# -*- coding: utf-8 -*-
"""
MalhaLookup — Ponto → polígono em MALHAS PÚBLICAS, 100% OFFLINE
===============================================================
Motor compartilhado do enriquecimento público dos centroides: dado um conjunto
de pontos ``(latitude, longitude)`` e o shape de uma MALHA oficial (malha
municipal, biomas...), devolve os ATRIBUTOS do polígono que CONTÉM cada ponto —
sem NENHUMA requisição de rede.

    utils.LocalidadeApi → malha municipal do IBGE (município/UF/região)
    utils.BiomaApi      → malha de biomas do IBGE (bioma)

OTIMIZACAO por celula: os pontos sao agrupados em celulas de ``CELL_DEGREES``
(0,5°) e cada celula faz UMA leitura ESPACIAL do shape (``bbox`` — so os
poligonos que a intersectam entram na memoria); o point-in-polygon e feito
LOCALMENTE (shapely ``covers``) e o resultado da celula fica em cache na sessao
(chave: caminho do shape + campos pedidos).

O CRS da malha e lido do ``.prj``: malha geografica usa as coordenadas como
estao; malha projetada tem o bbox e os pontos transformados (``pyproj``).

As consultas sao BEST-EFFORT: malha ausente/ilegivel nao interrompe o fluxo do
chamador — os campos saem VAZIOS e o erro vai para o log.

Uso:
    from utils.MalhaLookup import MalhaLookup

    MalhaLookup.lookup("biomas.shp", -48.3336, -10.1840, ("NM_BIOMA",))
    # {"NM_BIOMA": "CERRADO"}

    MalhaLookup.lookups(shape, [(-10.184, -48.3336)], ("NM_BIOMA",))
"""

from __future__ import annotations

import math
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import fiona
from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError
from shapely.geometry import Point

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.vector.VectorLayerSource import VectorLayerSource


class MalhaLookup(BaseUtil):
    """Atributos do poligono de uma MALHA publica que contem cada ponto (offline)."""

    # ── Otimizacao por celula ───────────────────────────────────────
    CELL_DEGREES = 0.5
    CELL_PAD_DEGREES = 0.002
    NOMINAL_CELL_S = 0.3

    # Cache de sessao: ``"caminho|campo1,campo2"`` → info (cells inclusas).
    _infos: Dict[str, Optional[Dict[str, Any]]] = {}

    # ── API publica ─────────────────────────────────────────────────

    @classmethod
    def lookups(
        cls,
        shape: Any,
        points: Iterable[Tuple[float, float]],
        fields: Sequence[str],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        progress_cb: Optional[Callable[[int, int, float], None]] = None,
        source_label: str = "malha publica",
    ) -> List[Dict[str, str]]:
        """
        Atributos de cada ponto, na MESMA ordem recebida.

        Args:
            shape: Caminho do shape da malha (``None`` quando nao encontrada).
            points: Iteravel de ``(latitude, longitude)`` (EPSG:4326).
            fields: Campos da malha a devolver por ponto.
            tool_key: Chave da ferramenta para logging.
            progress_cb: Callback ``(processados, total, eta_segundos)``.
            source_label: Nome da fonte para as mensagens de log.

        Returns:
            Lista de dicionarios (um por ponto) — valores vazios fora da malha
            ou quando o shape nao esta disponivel.
        """
        logger = cls._get_logger(tool_key, "MalhaLookup")
        coords = list(points)
        if not coords:
            return []

        info = cls._load_info(shape, fields, tool_key, logger, source_label)
        if info is None:
            return [cls._empty(fields) for _ in coords]

        cells = cls._cells(coords)
        results = [cls._empty(fields) for _ in coords]
        total = len(coords)
        done = 0
        started = time.monotonic()

        logger.info(
            f"Consultando {source_label} de {total} ponto(s)",
            code="MALHA_LOOKUP_START",
            n_points=total,
            n_cells=len(cells),
            fields=list(fields),
            shape=str(info["path"]),
        )

        for cell in sorted(cells):
            indexes = cells[cell]
            for index in indexes:
                latitude, longitude = coords[index]
                results[index] = cls._resolve(
                    info, latitude, longitude, cell, tool_key, logger, source_label
                )
            done += len(indexes)
            cls._report(progress_cb, done, total, started)

        logger.info(
            f"{source_label} consultada",
            code="MALHA_LOOKUP_DONE",
            n_points=total,
            n_cells=len(cells),
            n_found=sum(1 for item in results if any(item.values())),
        )
        return results

    @classmethod
    def lookup(
        cls,
        shape: Any,
        longitude: float,
        latitude: float,
        fields: Sequence[str],
        tool_key: str = ToolKey.UNTRACEABLE.value,
        source_label: str = "malha publica",
    ) -> Dict[str, str]:
        """Atributos de UM ponto (EPSG:4326) — vazios fora da malha."""
        logger = cls._get_logger(tool_key, "MalhaLookup")
        info = cls._load_info(shape, fields, tool_key, logger, source_label)
        if info is None:
            return cls._empty(fields)

        latitude = float(latitude)
        longitude = float(longitude)
        return cls._resolve(
            info,
            latitude,
            longitude,
            cls._cell_key(latitude, longitude),
            tool_key,
            logger,
            source_label,
        )

    @classmethod
    def plan_seconds(
        cls, shape: Any, points: Iterable[Tuple[float, float]]
    ) -> float:
        """Estimativa (segundos) da fase: 1 leitura espacial por celula."""
        return len(cls._cells(list(points))) * cls.NOMINAL_CELL_S

    # ── Normalizacao do texto ───────────────────────────────────────

    @staticmethod
    def clean_text(value: Any) -> str:
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

    # ── Malha (cabecalho e cache) ───────────────────────────────────

    @classmethod
    def _empty(cls, fields: Sequence[str]) -> Dict[str, str]:
        """Dicionario com TODOS os campos vazios."""
        return {name: "" for name in fields}

    @classmethod
    def _load_info(
        cls,
        shape: Any,
        fields: Sequence[str],
        tool_key: str,
        logger: Any,
        source_label: str,
    ) -> Optional[Dict[str, Any]]:
        """Cabecalho da malha (caminho, CRS, transformador e celulas) em cache."""
        key = cls._cache_key(shape, fields)
        if key in cls._infos:
            return cls._infos[key]

        info = cls._read_info(shape, fields, tool_key, logger, source_label)
        cls._infos[key] = info
        return info

    @staticmethod
    def _cache_key(shape: Any, fields: Sequence[str]) -> str:
        """Chave do cache: caminho do shape + campos pedidos."""
        return f"{shape}|{','.join(fields)}"

    @classmethod
    def _read_info(
        cls,
        shape: Any,
        fields: Sequence[str],
        tool_key: str,
        logger: Any,
        source_label: str,
    ) -> Optional[Dict[str, Any]]:
        """Le o cabecalho do shape (CRS e campos) SEM carregar a geometria."""
        path = Path(str(shape)) if shape else None
        if path is None or not path.is_file():
            logger.error(
                f"{source_label} nao encontrada — os campos ficarao vazios",
                code="MALHA_SHAPE_MISSING",
                source=source_label,
                shape=str(shape or ""),
            )
            return None

        try:
            with fiona.open(str(path)) as source:
                crs = cls._source_crs(source, logger, source_label)
                missing = cls._missing_fields(source, fields)
        except Exception as e:
            logger.error(
                f"Falha ao ler o cabecalho da {source_label}",
                code="MALHA_SHAPE_ERR",
                source=source_label,
                path=str(path),
                error=str(e),
            )
            return None

        if missing:
            logger.error(
                f"{source_label} sem os campos esperados — os campos ficarao vazios",
                code="MALHA_FIELDS_ERR",
                source=source_label,
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
            f"{source_label} pronta",
            code="MALHA_SHAPE_OK",
            source=source_label,
            path=str(path),
            crs=crs.to_string() if crs is not None else "N/A",
            fields=list(fields),
        )
        return {"path": path, "fields": tuple(fields), "cells": {}, "transformer": transformer}

    @classmethod
    def _missing_fields(cls, source: Any, fields: Sequence[str]) -> List[str]:
        """Campos pedidos que faltam no shape (vazio quando esta no padrao)."""
        schema = getattr(source, "schema", None) or {}
        available = set((schema.get("properties") or {}).keys())
        return [name for name in fields if name not in available]

    @staticmethod
    def _source_crs(source: Any, logger: Any, source_label: str) -> Optional[CRS]:
        """CRS declarado no shape (``.prj``) — ``None`` quando ausente/ilegivel."""
        wkt = str(getattr(source, "crs_wkt", "") or "").strip()
        if not wkt:
            logger.warning(
                f"{source_label} sem CRS declarado — assumindo graus (EPSG:4326)",
                code="MALHA_CRS_MISSING",
                source=source_label,
            )
            return None

        try:
            return CRS.from_user_input(wkt)
        except CRSError as e:
            logger.warning(
                f"CRS da {source_label} ilegivel — assumindo graus (EPSG:4326)",
                code="MALHA_CRS_WARN",
                source=source_label,
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
        source_label: str,
    ) -> List[Tuple[Any, Dict[str, str]]]:
        """Poligonos que intersectam a celula — ``(geometria, atributos)``.

        Faz UMA leitura espacial (``bbox``) por celula e memoriza o resultado.
        """
        cached = info["cells"].get(cell)
        if cached is not None:
            return cached

        fields: Tuple[str, ...] = info["fields"]
        polygons: List[Tuple[Any, Dict[str, str]]] = []
        try:
            gdf = VectorLayerSource.read_geodataframe(
                str(info["path"]),
                tool_key=tool_key,
                bbox=cls._cell_bbox(info, cell),
            )
            geom_name = gdf.geometry.name
            for _, row in gdf.iterrows():
                attributes = {
                    name: cls.clean_text(row.get(name)) for name in fields
                }
                if not any(attributes.values()):
                    continue
                geometry = row[geom_name]
                if geometry is None or geometry.is_empty:
                    continue
                polygons.append((geometry, attributes))
        except Exception as e:
            logger.error(
                f"Falha ao ler a {source_label} da celula",
                code="MALHA_CELL_ERR",
                source=source_label,
                cell=str(cell),
                error=str(e),
            )

        info["cells"][cell] = polygons
        return polygons

    # ── Resolucao ponto → poligono ──────────────────────────────────

    @classmethod
    def _resolve(
        cls,
        info: Dict[str, Any],
        latitude: float,
        longitude: float,
        cell: Tuple[int, int],
        tool_key: str,
        logger: Any,
        source_label: str,
    ) -> Dict[str, str]:
        """Atributos do poligono que contem UM ponto (point-in-polygon na celula)."""
        point = cls._point(info, latitude, longitude)
        for geometry, attributes in cls._cell_polygons(
            info, cell, tool_key, logger, source_label
        ):
            if geometry.covers(point):
                return dict(attributes)

        return cls._empty(info["fields"])

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
