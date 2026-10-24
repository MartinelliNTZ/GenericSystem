# -*- coding: utf-8 -*-
"""
LocalidadeApi — Municipio, UF e pais de um ponto pelos servicos do IBGE
=======================================================================
API 2 do enriquecimento publico dos centroides da Base de Limites: devolve o
MUNICIPIO, a SIGLA da UF (2 letras) e o PAIS de cada ponto (longitude/latitude).

Fontes (publicas, oficiais e sem chave):

    municipio → servico ArcGIS do IBGE (Atlas dos Municipios)
                https://mapasinterativos.ibge.gov.br/arcgis/rest/services/atlas_mun/MapServer/0/query
    sigla UF  → API de Localidades do IBGE (codigo IBGE da UF → sigla)
                https://servicodados.ibge.gov.br/api/v1/localidades/estados

O servico cobre APENAS o Brasil: fora do territorio brasileiro o municipio, a
UF e o pais saem VAZIOS. Dentro do Brasil o pais e sempre ``BRASIL``. O mapa
``codigo da UF → sigla`` e carregado UMA vez por sessao e mantido em cache.

OTIMIZACAO: em vez de UMA consulta por ponto, os pontos sao agrupados em
celulas de ``CELL_DEGREES`` (0,5°) e cada celula faz UMA requisicao que devolve
os municipios que a intersectam; a atribuicao ponto → municipio e feita
LOCALMENTE (point-in-polygon). Pontos nao resolvidos localmente caem no
fallback de consulta por ponto. Numa base de ~1200 talhoes isso troca ~1200
requisicoes por algumas dezenas (minutos → segundos).

As consultas sao BEST-EFFORT: falhas de rede nao interrompem o fluxo do
chamador — os campos ficam vazios e o erro vai para o log.

Uso:
    from utils.LocalidadeApi import LocalidadeApi

    LocalidadeApi.lookup(-48.3336, -10.1840)
    # {"municipio": "PALMAS", "estado": "TO", "pais": "BRASIL"}

    LocalidadeApi.lookups([(-10.184, -48.3336), (-10.185, -48.3337)])
"""

from __future__ import annotations

import math
import re
import time
import unicodedata
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import requests
from shapely.geometry import Point, shape

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil

EMPTY: Dict[str, str] = {"municipio": "", "estado": "", "pais": ""}


class LocalidadeApi(BaseUtil):
    """Municipio, UF (sigla) e pais de um ponto pelos servicos do IBGE."""

    QUERY_URL = (
        "https://mapasinterativos.ibge.gov.br/arcgis/rest/services/"
        "atlas_mun/MapServer/0/query"
    )
    ESTADOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados"
    OUT_FIELDS = "NM_MUNICIP,CD_GEOCODM"
    UF_CODE_DIVISOR = 100000
    PAIS_BRASIL = "BRASIL"
    TIMEOUT_S = 30
    MIN_INTERVAL_S = 1.05
    RETRIES = 2

    # ── Otimizacao por celula ───────────────────────────────────────
    CELL_DEGREES = 0.5
    MAX_CELL_FEATURES = 200
    MAX_ALLOWABLE_OFFSET = 0.0005
    NOMINAL_REQUEST_S = 0.6

    _last_call_s = 0.0
    _uf_by_code: Dict[int, str] = {}

    # ── API publica ─────────────────────────────────────────────────

    @classmethod
    def lookups(
        cls,
        points: Iterable[Tuple[float, float]],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int, float], None]] = None,
    ) -> List[Dict[str, str]]:
        """
        Municipio/UF/pais de cada ponto, na MESMA ordem recebida.

        Agrupa os pontos por celula (``CELL_DEGREES``), faz UMA requisicao por
        celula (municipios que a intersectam) e resolve ponto → municipio
        LOCALMENTE; o que nao for resolvido cai no fallback por ponto.

        Args:
            points: Iteravel de ``(latitude, longitude)`` em EPSG:4326.
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total, eta_segundos)`` — o
                ``eta`` e o tempo RESTANTE projetado pela taxa medida.

        Returns:
            Lista de dicionarios ``{"municipio", "estado", "pais"}`` — campos
            vazios quando a consulta falha ou o ponto esta fora do Brasil.
        """
        logger = cls._get_logger(tool_key, "LocalidadeApi")
        coords = list(points)
        if not coords:
            return []

        logger.info(
            f"Consultando localidade de {len(coords)} ponto(s) (IBGE)",
            code="LOC_API_START",
        )

        started = time.monotonic()
        results: List[Optional[Dict[str, str]]] = [None] * len(coords)
        ufs = cls._uf_map(logger)
        cells = cls._cells(coords)
        by_polygon = 0

        for cell, indexes in cells.items():
            polygons = cls._cell_polygons(cell, logger)
            if polygons:
                by_polygon += cls._resolve(coords, indexes, polygons, results, ufs)
            cls._report(progress_cb, results, len(coords), started)

        pending = [index for index, item in enumerate(results) if item is None]
        logger.info(
            f"Localidade por celula: {by_polygon} ponto(s) resolvido(s) em "
            f"{len(cells)} celula(s)",
            code="LOC_API_CELLS",
            n_cells=len(cells),
            n_by_polygon=by_polygon,
            n_fallback=len(pending),
        )

        for index in pending:
            latitude, longitude = coords[index]
            results[index] = cls.lookup(longitude, latitude, tool_key)
            cls._report(progress_cb, results, len(coords), started)

        found = [item or dict(EMPTY) for item in results]
        logger.info(
            f"Localidade concluida: "
            f"{sum(1 for item in found if item['municipio'])}/{len(found)} ponto(s) "
            f"com municipio",
            code="LOC_API_DONE",
            elapsed_s=round(time.monotonic() - started, 2),
        )
        return found

    @classmethod
    def plan_seconds(cls, points: Iterable[Tuple[float, float]]) -> float:
        """Estimativa (segundos) da fase: 1 requisicao por celula + fallback nominal."""
        coords = list(points)
        if not coords:
            return 0.0
        return len(cls._cells(coords)) * cls.NOMINAL_REQUEST_S

    @classmethod
    def _cells(
        cls,
        coords: List[Tuple[float, float]],
    ) -> Dict[Tuple[int, int], List[int]]:
        """Agrupa os indices dos pontos por celula de ``CELL_DEGREES``."""
        cells: Dict[Tuple[int, int], List[int]] = {}
        for index, (latitude, longitude) in enumerate(coords):
            key = (
                int(math.floor(float(longitude) / cls.CELL_DEGREES)),
                int(math.floor(float(latitude) / cls.CELL_DEGREES)),
            )
            cells.setdefault(key, []).append(index)
        return cells

    @classmethod
    def _cell_polygons(
        cls,
        cell: Tuple[int, int],
        logger: Any,
    ) -> List[Tuple[Any, str, int]]:
        """Municipios que intersectam a celula (UMA requisicao) — ``[]`` em falha."""
        min_x = cell[0] * cls.CELL_DEGREES
        min_y = cell[1] * cls.CELL_DEGREES
        params = {
            "geometry": (
                f"{min_x:.6f},{min_y:.6f},"
                f"{min_x + cls.CELL_DEGREES:.6f},{min_y + cls.CELL_DEGREES:.6f}"
            ),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "outSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": cls.OUT_FIELDS,
            "returnGeometry": "true",
            "maxAllowableOffset": cls.MAX_ALLOWABLE_OFFSET,
            "resultRecordCount": cls.MAX_CELL_FEATURES,
            "f": "geojson",
        }

        for attempt in range(1, cls.RETRIES + 2):
            cls._throttle()
            try:
                response = requests.get(
                    cls.QUERY_URL, params=params, timeout=cls.TIMEOUT_S
                )
                response.raise_for_status()
                payload = response.json() or {}
                if payload.get("exceededTransferLimit"):
                    logger.warning(
                        "Celula com municipios demais — caindo na consulta por ponto",
                        code="LOC_API_CELL_LIMIT",
                        cell=str(cell),
                    )
                    return []
                return cls._polygons(payload.get("features") or [])
            except (requests.RequestException, ValueError) as e:
                logger.warning(
                    "Falha na consulta da celula",
                    code="LOC_API_CELL_RETRY",
                    cell=str(cell),
                    attempt=attempt,
                    error=str(e),
                )

        logger.error("Celula nao consultada", code="LOC_API_CELL_ERR", cell=str(cell))
        return []

    @classmethod
    def lookup(
        cls,
        longitude: float,
        latitude: float,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, str]:
        """
        Municipio, UF (sigla) e pais de UM ponto (EPSG:4326).

        Returns:
            ``{"municipio": ..., "estado": ..., "pais": ...}`` — vazio fora do
            Brasil ou quando a consulta falha.
        """
        logger = cls._get_logger(tool_key, "LocalidadeApi")
        municipio, uf_code = cls._query_municipio(longitude, latitude, logger)
        if not municipio:
            return dict(EMPTY)

        return {
            "municipio": municipio,
            "estado": cls._uf_map(logger).get(uf_code, ""),
            "pais": cls.PAIS_BRASIL,
        }

    @classmethod
    def _polygons(cls, features: List[Any]) -> List[Tuple[Any, str, int]]:
        """Converte as feicoes GeoJSON em ``(geometria, municipio, codigo da UF)``."""
        polygons: List[Tuple[Any, str, int]] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            geometry = feature.get("geometry")
            if not geometry:
                continue
            properties = feature.get("properties") or {}
            polygons.append(
                (
                    shape(geometry),
                    cls._clean(properties.get("NM_MUNICIP")),
                    cls._uf_code(properties.get("CD_GEOCODM")),
                )
            )
        return polygons

    @classmethod
    def _resolve(
        cls,
        coords: List[Tuple[float, float]],
        indexes: List[int],
        polygons: List[Tuple[Any, str, int]],
        results: List[Optional[Dict[str, str]]],
        ufs: Dict[int, str],
    ) -> int:
        """Atribui LOCALMENTE o municipio dos pontos da celula (point-in-polygon)."""
        resolved = 0
        for index in indexes:
            latitude, longitude = coords[index]
            point = Point(float(longitude), float(latitude))
            for geometry, municipio, uf_code in polygons:
                if not municipio or not geometry.contains(point):
                    continue
                results[index] = {
                    "municipio": municipio,
                    "estado": ufs.get(uf_code, ""),
                    "pais": cls.PAIS_BRASIL,
                }
                resolved += 1
                break
        return resolved

    @staticmethod
    def _report(
        progress_cb: Optional[Callable[[int, int, float], None]],
        results: List[Optional[Dict[str, str]]],
        total: int,
        started: float,
    ) -> None:
        """Emite ``(feitos, total, eta)`` projetando o restante pela taxa medida."""
        if progress_cb is None:
            return

        done = sum(1 for item in results if item is not None)
        elapsed = time.monotonic() - started
        eta = (elapsed / done) * (total - done) if done else 0.0
        progress_cb(done, total, eta)

    # ── Interno ─────────────────────────────────────────────────────

    @classmethod
    def _query_municipio(
        cls,
        longitude: float,
        latitude: float,
        logger: Any,
    ) -> Tuple[str, int]:
        """Consulta o municipio do ponto e devolve ``(nome, codigo da UF)``."""
        params = {
            "geometry": f"{float(longitude):.6f},{float(latitude):.6f}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": cls.OUT_FIELDS,
            "returnGeometry": "false",
            "f": "json",
        }

        for attempt in range(1, cls.RETRIES + 2):
            cls._throttle()
            try:
                response = requests.get(
                    cls.QUERY_URL, params=params, timeout=cls.TIMEOUT_S
                )
                response.raise_for_status()
                features = (response.json() or {}).get("features") or []
                if not features:
                    return "", 0

                attributes = features[0].get("attributes") or {}
                return cls._clean(attributes.get("NM_MUNICIP")), cls._uf_code(
                    attributes.get("CD_GEOCODM")
                )
            except (requests.RequestException, ValueError) as e:
                logger.warning(
                    "Falha na consulta de municipio",
                    code="LOC_API_RETRY",
                    latitude=latitude,
                    longitude=longitude,
                    attempt=attempt,
                    error=str(e),
                )

        logger.error(
            "Municipio nao consultado",
            code="LOC_API_ERR",
            latitude=latitude,
            longitude=longitude,
        )
        return "", 0

    @classmethod
    def _uf_map(cls, logger: Any) -> Dict[int, str]:
        """Mapa ``codigo da UF → sigla`` (carregado uma vez por sessao)."""
        if cls._uf_by_code:
            return cls._uf_by_code

        try:
            response = requests.get(cls.ESTADOS_URL, timeout=cls.TIMEOUT_S)
            response.raise_for_status()
            items = response.json() or []
        except (requests.RequestException, ValueError) as e:
            logger.error(
                "Falha ao carregar as UFs do IBGE",
                code="LOC_API_UF_ERR",
                error=str(e),
            )
            return {}

        for item in items:
            if not isinstance(item, dict):
                continue
            code = item.get("id")
            sigla = item.get("sigla")
            if isinstance(code, bool) or not isinstance(code, (int, float)):
                continue
            if sigla:
                cls._uf_by_code[int(code)] = str(sigla).strip().upper()

        logger.info(
            "UFs do IBGE carregadas",
            code="LOC_API_UF_OK",
            n_ufs=len(cls._uf_by_code),
        )
        return cls._uf_by_code

    @classmethod
    def _throttle(cls) -> None:
        """Mantem o intervalo minimo entre chamadas ao servico do IBGE."""
        wait = cls.MIN_INTERVAL_S - (time.monotonic() - cls._last_call_s)
        if wait > 0:
            time.sleep(wait)
        cls._last_call_s = time.monotonic()

    @classmethod
    def _uf_code(cls, value: Any) -> int:
        """Codigo da UF a partir do codigo IBGE do municipio (``1721000`` → ``17``)."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return 0
        return int(value) // cls.UF_CODE_DIVISOR

    @staticmethod
    def _clean(value: Any) -> str:
        """Normaliza o texto do IBGE (MAIUSCULAS, sem acento, espacos → ``_``)."""
        text = "" if value is None else str(value).strip()
        if not text:
            return ""

        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        return re.sub(r"\s+", "_", text).upper()



