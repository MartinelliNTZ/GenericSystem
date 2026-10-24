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

As consultas sao BEST-EFFORT: falhas de rede nao interrompem o fluxo do
chamador — os campos ficam vazios e o erro vai para o log.

Uso:
    from utils.LocalidadeApi import LocalidadeApi

    LocalidadeApi.lookup(-48.3336, -10.1840)
    # {"municipio": "PALMAS", "estado": "TO", "pais": "BRASIL"}
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import requests

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

    _last_call_s = 0.0
    _uf_by_code: Dict[int, str] = {}

    # ── API publica ─────────────────────────────────────────────────

    @classmethod
    def lookups(
        cls,
        points: Iterable[Tuple[float, float]],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, str]]:
        """
        Municipio/UF/pais de cada ponto, na MESMA ordem recebida.

        Args:
            points: Iteravel de ``(latitude, longitude)`` em EPSG:4326.
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total)`` opcional.

        Returns:
            Lista de dicionarios ``{"municipio", "estado", "pais"}`` — campos
            vazios quando a consulta falha ou o ponto esta fora do Brasil.
        """
        logger = cls._get_logger(tool_key, "LocalidadeApi")
        coords = list(points)
        if not coords:
            return []

        logger.info(
            "Consultando municipio/UF/pais (IBGE)",
            code="LOC_API_START",
            n_points=len(coords),
        )

        found: List[Dict[str, str]] = []
        for latitude, longitude in coords:
            found.append(cls.lookup(longitude, latitude, tool_key))
            if progress_cb:
                progress_cb(len(found), len(coords))

        logger.info(
            "Localidade concluida",
            code="LOC_API_DONE",
            n_points=len(coords),
            n_found=sum(1 for item in found if item["municipio"]),
        )
        return found

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



