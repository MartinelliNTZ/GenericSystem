# -*- coding: utf-8 -*-
"""
LocalidadeApi — Municipio, UF, regiao e pais de um ponto pela MALHA DO IBGE (OFFLINE)
=====================================================================================
API 2 do enriquecimento publico dos centroides da Base de Limites: devolve o
MUNICIPIO, a SIGLA da UF (2 letras), a REGIAO (Norte/Nordeste/Centro-Oeste/
Sudeste/Sul) e o PAIS de cada ponto (latitude/longitude).

Fonte LOCAL (sem rede — funciona OFFLINE):

    malha municipal do IBGE -> <BASE_DADOS>/PUBLICOS/IBGE_BR_Municipios_<ano>/
                               BR_Municipios_<ano>.shp

O caminho e resolvido por ``utils.PublicDataStructureUtil`` (a versao MAIS NOVA
da pasta e usada automaticamente) e os campos lidos do shape sao ``NM_MUN``
(municipio), ``SIGLA_UF`` (sigla da UF) e ``NM_REGIAO`` (regiao). O shape cobre
APENAS o Brasil: fora do territorio brasileiro o municipio, a UF, a regiao e o
pais saem VAZIOS; dentro dele o pais e sempre ``BRASIL``.

OTIMIZACAO: os pontos sao agrupados em celulas de ``CELL_DEGREES`` (0,5°) e cada
celula faz UMA leitura ESPACIAL do shape (``bbox`` — so os municipios que a
intersectam entram na memoria); a atribuicao ponto → municipio e feita
LOCALMENTE (point-in-polygon com shapely). Numa base de ~1200 talhoes isso da
algumas dezenas de leituras (segundos), sem NENHUMA requisicao de rede.

As consultas sao BEST-EFFORT: malha ausente/ilegivel nao interrompe o fluxo do
chamador — os campos ficam vazios e o erro vai para o log.

Uso:
    from utils.LocalidadeApi import LocalidadeApi

    LocalidadeApi.lookup(-48.3336, -10.1840)
    # {"municipio": "PALMAS", "estado": "TO", "regiao": "NORTE", "pais": "BRASIL"}

    LocalidadeApi.lookups([(-10.184, -48.3336), (-10.185, -48.3337)])
"""

from __future__ import annotations

import math
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import fiona
from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError
from shapely.geometry import Point

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.PublicDataStructureUtil import PublicDataStructureUtil
from utils.vector.VectorLayerSource import VectorLayerSource

EMPTY: Dict[str, str] = {"municipio": "", "estado": "", "regiao": "", "pais": ""}


class LocalidadeApi(BaseUtil):
    """Municipio, UF (sigla), regiao e pais de um ponto pela malha do IBGE."""

    # Campos da malha municipal do IBGE (Malha Municipal Digital).
    FIELD_MUNICIPIO = "NM_MUN"
    FIELD_ESTADO = "SIGLA_UF"
    FIELD_REGIAO = "NM_REGIAO"

    PAIS_BRASIL = "BRASIL"

    # ── Otimizacao por celula ───────────────────────────────────────
    CELL_DEGREES = 0.5
    CELL_PAD_DEGREES = 0.002
    NOMINAL_CELL_S = 0.3

    _info: Optional[Dict[str, Any]] = None
    _info_ready = False

    # ── API publica ─────────────────────────────────────────────────

    @classmethod
    def lookups(
        cls,
        points: Iterable[Tuple[float, float]],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int, float], None]] = None,
    ) -> List[Dict[str, str]]:
        """
        Municipio/UF/regiao/pais de cada ponto, na MESMA ordem recebida.

        Args:
            points: Iteravel de ``(latitude, longitude)`` (EPSG:4326).
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total, eta_segundos)``.

        Returns:
            Lista de dicionarios — vazios fora do Brasil ou quando a malha nao
            esta disponivel.
        """
        logger = cls._get_logger(tool_key, "LocalidadeApi")
        coords = list(points)
        if not coords:
            return []

        info = cls._load_info(tool_key, logger)
        if info is None:
            return [dict(EMPTY) for _ in coords]

        cells = cls._cells(coords)
        results = [dict(EMPTY) for _ in coords]
        total = len(coords)
        done = 0
        started = time.monotonic()

        logger.info(
            f"Consultando localidade de {total} ponto(s) (malha municipal do IBGE)",
            code="LOC_API_START",
            n_points=total,
            n_cells=len(cells),
            shape=str(info["path"]),
        )

        for cell in sorted(cells):
            indexes = cells[cell]
            for index in indexes:
                latitude, longitude = coords[index]
                results[index] = cls._resolve(
                    info, latitude, longitude, cell, tool_key, logger
                )
            done += len(indexes)
            cls._report(progress_cb, done, total, started)

        logger.info(
            "Localidade consultada",
            code="LOC_API_DONE",
            n_points=total,
            n_cells=len(cells),
            n_found=sum(1 for item in results if item["municipio"]),
        )
        return results

    @classmethod
    def lookup(
        cls,
        longitude: float,
        latitude: float,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, str]:
        """
        Municipio, UF (sigla), regiao e pais de UM ponto (EPSG:4326).

        Returns:
            ``{"municipio": ..., "estado": ..., "regiao": ..., "pais": ...}`` —
            vazio fora do Brasil ou quando a malha nao esta disponivel.
        """
        logger = cls._get_logger(tool_key, "LocalidadeApi")
        info = cls._load_info(tool_key, logger)
        if info is None:
            return dict(EMPTY)

        latitude = float(latitude)
        longitude = float(longitude)
        return cls._resolve(
            info,
            latitude,
            longitude,
            cls._cell_key(latitude, longitude),
            tool_key,
            logger,
        )

    @classmethod
    def plan_seconds(cls, points: Iterable[Tuple[float, float]]) -> float:
        """Estimativa (segundos) da fase: 1 leitura espacial por celula."""
        return len(cls._cells(list(points))) * cls.NOMINAL_CELL_S

    @classmethod
    def shape_path(cls, tool_key: str = ToolKey.UNTRACEABLE.value) -> str:
        """Caminho da malha municipal em uso (``""`` quando nao encontrada)."""
        shape = PublicDataStructureUtil.municipios_shape(tool_key=tool_key)
        return str(shape) if shape is not None else ""

    # ── Malha municipal (cabecalho e cache) ─────────────────────────

    @classmethod
    def _load_info(cls, tool_key: str, logger: Any) -> Optional[Dict[str, Any]]:
        """Cabecalho da malha (caminho, CRS, transformador e celulas) em cache."""
        if not cls._info_ready:
            cls._info_ready = True
            cls._info = cls._read_info(tool_key, logger)
        return cls._info

    @classmethod
    def _read_info(cls, tool_key: str, logger: Any) -> Optional[Dict[str, Any]]:
        """Le o cabecalho do shape (CRS) SEM carregar a geometria."""
        path = PublicDataStructureUtil.municipios_shape(tool_key=tool_key)
        if path is None:
            logger.error(
                "Malha municipal do IBGE nao encontrada — os campos de "
                "localidade ficarao vazios",
                code="LOC_API_SHAPE_MISSING",
                root=PublicDataStructureUtil.root_str(tool_key),
            )
            return None

        try:
            with fiona.open(str(path)) as source:
                crs = cls._source_crs(source, logger)
                missing = cls._missing_fields(source)
        except Exception as e:
            logger.error(
                "Falha ao ler o cabecalho da malha municipal",
                code="LOC_API_SHAPE_ERR",
                path=str(path),
                error=str(e),
            )
            return None

        if missing:
            logger.error(
                "Malha municipal sem os campos esperados — os campos de "
                "localidade ficarao vazios",
                code="LOC_API_FIELDS_ERR",
                path=str(path),
                missing=missing,
            )
            return None

        transformer = None
        if crs is not None and not crs.is_geographic:
            transformer = Transformer.from_crs(
                CRS.from_epsg(4326), crs, always_xy=True
            )

        logger.info(
            "Malha municipal pronta",
            code="LOC_API_SHAPE_OK",
            path=str(path),
            crs=crs.to_string() if crs is not None else "N/A",
        )
        return {"path": Path(path), "cells": {}, "transformer": transformer}

    @classmethod
    def _missing_fields(cls, source: Any) -> List[str]:
        """Campos da malha que faltam no shape (vazio quando esta no padrao)."""
        schema = getattr(source, "schema", None) or {}
        fields = set((schema.get("properties") or {}).keys())
        expected = (cls.FIELD_MUNICIPIO, cls.FIELD_ESTADO, cls.FIELD_REGIAO)
        return [name for name in expected if name not in fields]

    @staticmethod
    def _source_crs(source: Any, logger: Any) -> Optional[CRS]:
        """CRS declarado no shape (``.prj``) — ``None`` quando ausente/ilegivel."""
        wkt = str(getattr(source, "crs_wkt", "") or "").strip()
        if not wkt:
            logger.warning(
                "Malha municipal sem CRS declarado — assumindo graus (EPSG:4326)",
                code="LOC_API_CRS_MISSING",
            )
            return None

        try:
            return CRS.from_user_input(wkt)
        except CRSError as e:
            logger.warning(
                "CRS da malha municipal ilegivel — assumindo graus (EPSG:4326)",
                code="LOC_API_CRS_WARN",
                error=str(e),
            )
            return None

    # ── Celulas (agrupamento dos pontos) ────────────────────────────

    @classmethod
    def _cells(
        cls, coords: List[Tuple[float, float]]
    ) -> Dict[Tuple[int, int], List[int]]:
        """Agrupa os indices dos pontos por celula (``(latitude, longitude)``)."""
        cells: Dict[Tuple[int, int], List[int]] = {}
        for index, (latitude, longitude) in enumerate(coords):
            cells.setdefault(cls._cell_key(latitude, longitude), []).append(index)
        return cells

    @classmethod
    def _cell_key(cls, latitude: float, longitude: float) -> Tuple[int, int]:
        """Celula (indices inteiros) de um ponto."""
        return (
            math.floor(float(latitude) / cls.CELL_DEGREES),
            math.floor(float(longitude) / cls.CELL_DEGREES),
        )

    @classmethod
    def _cell_bbox(
        cls, info: Dict[str, Any], cell: Tuple[int, int]
    ) -> Tuple[float, float, float, float]:
        """Caixa da celula (com folga) no CRS da malha."""
        min_lon = cell[1] * cls.CELL_DEGREES - cls.CELL_PAD_DEGREES
        min_lat = cell[0] * cls.CELL_DEGREES - cls.CELL_PAD_DEGREES
        max_lon = (cell[1] + 1) * cls.CELL_DEGREES + cls.CELL_PAD_DEGREES
        max_lat = (cell[0] + 1) * cls.CELL_DEGREES + cls.CELL_PAD_DEGREES

        transformer = info["transformer"]
        if transformer is None:
            return min_lon, min_lat, max_lon, max_lat

        corners = [
            transformer.transform(x, y)
            for x, y in (
                (min_lon, min_lat),
                (max_lon, min_lat),
                (min_lon, max_lat),
                (max_lon, max_lat),
            )
        ]
        xs = [corner[0] for corner in corners]
        ys = [corner[1] for corner in corners]
        return min(xs), min(ys), max(xs), max(ys)

    @classmethod
    def _cell_polygons(
        cls,
        info: Dict[str, Any],
        cell: Tuple[int, int],
        tool_key: str,
        logger: Any,
    ) -> List[Tuple[Any, str, str, str]]:
        """Municipios que intersectam a celula — ``(geometria, municipio, UF, regiao)``.

        Faz UMA leitura espacial (``bbox``) por celula e memoriza o resultado.
        """
        cached = info["cells"].get(cell)
        if cached is not None:
            return cached

        polygons: List[Tuple[Any, str, str, str]] = []
        try:
            gdf = VectorLayerSource.read_geodataframe(
                str(info["path"]),
                tool_key=tool_key,
                bbox=cls._cell_bbox(info, cell),
            )
            geom_name = gdf.geometry.name
            for _, row in gdf.iterrows():
                municipio = cls._clean(row.get(cls.FIELD_MUNICIPIO))
                if not municipio:
                    continue
                geometry = row[geom_name]
                if geometry is None or geometry.is_empty:
                    continue
                polygons.append(
                    (
                        geometry,
                        municipio,
                        cls._clean(row.get(cls.FIELD_ESTADO)),
                        cls._clean(row.get(cls.FIELD_REGIAO)),
                    )
                )
        except Exception as e:
            logger.error(
                "Falha ao ler a malha municipal da celula",
                code="LOC_API_CELL_ERR",
                cell=str(cell),
                error=str(e),
            )

        info["cells"][cell] = polygons
        return polygons

    # ── Resolucao ponto → municipio ─────────────────────────────────

    @classmethod
    def _resolve(
        cls,
        info: Dict[str, Any],
        latitude: float,
        longitude: float,
        cell: Tuple[int, int],
        tool_key: str,
        logger: Any,
    ) -> Dict[str, str]:
        """Municipio/UF/regiao/pais de UM ponto (point-in-polygon na celula)."""
        point = cls._point(info, latitude, longitude)
        for geometry, municipio, estado, regiao in cls._cell_polygons(
            info, cell, tool_key, logger
        ):
            if geometry.covers(point):
                return {
                    "municipio": municipio,
                    "estado": estado,
                    "regiao": regiao,
                    "pais": cls.PAIS_BRASIL,
                }

        return dict(EMPTY)

    @classmethod
    def _point(cls, info: Dict[str, Any], latitude: float, longitude: float) -> Point:
        """Ponto no CRS da malha (identidade quando a malha ja e geografica)."""
        longitude = float(longitude)
        latitude = float(latitude)
        transformer = info["transformer"]
        if transformer is None:
            return Point(longitude, latitude)

        x, y = transformer.transform(longitude, latitude)
        return Point(x, y)

    @staticmethod
    def _report(
        progress_cb: Optional[Callable[[int, int, float], None]],
        done: int,
        total: int,
        started: float,
    ) -> None:
        """Reporta ``(processados, total, eta_segundos)`` pela taxa medida."""
        if progress_cb is None:
            return

        elapsed = time.monotonic() - started
        eta = (elapsed / done * (total - done)) if done else 0.0
        progress_cb(done, total, eta)

    @staticmethod
    def _clean(value: Any) -> str:
        """Normaliza o texto da malha (MAIUSCULAS, sem acento, espacos → ``_``)."""
        text = "" if value is None else str(value).strip()
        if not text:
            return ""

        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        return re.sub(r"\s+", "_", text).upper()
