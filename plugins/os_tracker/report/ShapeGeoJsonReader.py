# -*- coding: utf-8 -*-
"""
ShapeGeoJsonReader — Vetor da base → GeoJSON (EPSG:4326)
=======================================================
Lê o arquivo vetorial gravado pela Base de Limites (``.shp``, ``.gpkg``,
``.kml``, ``.kmz``, ``.geojson``) e devolve uma ``FeatureCollection`` GeoJSON
pronta para os mapas (Leaflet) do template, mantendo APENAS as propriedades
que o template usa.

O mapa de campos fica em ``SHAPE_FIELDS`` (chave da base no banco →
propriedade do template → candidatos de campo no vetor, sem diferenciar
maiúsculas/minúsculas). Campo ausente sai vazio — o relatório nunca quebra
por causa do vetor.

Uso:
    from plugins.os_tracker.report.ShapeGeoJsonReader import ShapeGeoJsonReader

    fc = ShapeGeoJsonReader.read(".../220_limites.shp", "limites", tool_key=...)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.vector.VectorLayerSource import VectorLayerSource


class ShapeGeoJsonReader(BaseUtil):
    """Converte o vetor de uma base da OS em GeoJSON para o relatório."""

    # Propriedades do template por base do banco: nome → candidatos no vetor.
    SHAPE_FIELDS: Dict[str, Dict[str, Tuple[str, ...]]] = {
        "limites": {
            "fazenda": ("FAZENDA", "PROPRIEDADE"),
            "talhao": ("TALHAO", "TALH"),
            "area_ha": ("AREA_HA", "AREA_INF", "AREA"),
        },
        "zonas_manejo": {
            "zona": ("ZONA", "ZONE"),
        },
    }
    # Propriedades numéricas (as demais saem como texto).
    NUMERIC_FIELDS = frozenset({"area_ha"})
    CRS_WGS84 = "EPSG:4326"

    # ── API pública ─────────────────────────────────────────────────

    @classmethod
    def read(
        cls,
        path: str,
        key: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[Dict[str, Any]]:
        """GeoJSON da base ``key`` gravada em ``path`` (``None`` quando falha).

        Args:
            path: Caminho absoluto do vetor da base.
            key: Chave da base no banco (``limites`` | ``zonas_manejo``).
            tool_key: Chave da ferramenta para logging.
        """
        logger = cls._get_logger(tool_key, "ShapeGeoJsonReader")
        field_map = cls.SHAPE_FIELDS.get(key)
        target = Path(str(path or ""))
        if not field_map or not str(path or ""):
            return None
        if not target.exists():
            logger.warning(
                "Vetor da base não encontrado",
                code="OSREP_SHAPE_MISSING",
                base=key,
                path=str(target),
            )
            return None

        try:
            frame = cls._frame(
                VectorLayerSource.read_geodataframe(str(target), tool_key=tool_key),
                field_map,
                tool_key,
            )
            if frame.empty:
                logger.warning(
                    "Vetor da base sem feições válidas",
                    code="OSREP_SHAPE_EMPTY",
                    base=key,
                    path=str(target),
                )
                return None
            collection = json.loads(frame.to_json())
        except Exception as e:
            logger.error(
                "Falha ao converter o vetor da base em GeoJSON",
                code="OSREP_SHAPE_ERR",
                base=key,
                path=str(target),
                error=str(e),
            )
            return None

        logger.info(
            "Vetor da base convertido em GeoJSON",
            code="OSREP_SHAPE_DONE",
            base=key,
            features=len(frame),
        )
        return collection

    # ── Recorte e reprojeção ────────────────────────────────────────

    @classmethod
    def _frame(
        cls,
        gdf: Any,
        field_map: Dict[str, Tuple[str, ...]],
        tool_key: str,
    ) -> Any:
        """Recorta o GeoDataFrame nas propriedades do template, em EPSG:4326."""
        logger = cls._get_logger(tool_key, "ShapeGeoJsonReader")
        frame = gdf.copy()
        if frame.crs is None:
            logger.warning(
                "Vetor da base sem CRS — assumindo EPSG:4326",
                code="OSREP_SHAPE_NO_CRS",
            )
        elif str(frame.crs) != cls.CRS_WGS84:
            frame = frame.to_crs(cls.CRS_WGS84)

        frame = frame[frame.geometry.notna()].copy()
        for name, candidates in field_map.items():
            frame[name] = cls._column(frame, name, candidates)

        geometry = frame.geometry.name
        return frame[[*field_map, geometry]].copy().set_geometry(geometry)

    @classmethod
    def _column(cls, frame: Any, name: str, candidates: Tuple[str, ...]) -> Any:
        """Série da propriedade ``name`` (vazia quando o campo não existe)."""
        source = cls._find_column(frame, candidates)
        if source is None:
            return None if name in cls.NUMERIC_FIELDS else ""
        if name in cls.NUMERIC_FIELDS:
            return frame[source].map(cls._number)
        return frame[source].map(cls._text)

    @staticmethod
    def _find_column(frame: Any, candidates: Tuple[str, ...]) -> Optional[str]:
        """Nome real do primeiro campo candidato presente no vetor."""
        lookup = {str(column).strip().upper(): str(column) for column in frame.columns}
        for candidate in candidates:
            found = lookup.get(candidate.upper())
            if found:
                return found
        return None

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        """Número com 4 casas (``None`` para vazio/NaN/não numérico)."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return None if number != number else round(number, 4)

    @staticmethod
    def _text(value: Any) -> str:
        """Texto do atributo (``""`` para vazio/NaN)."""
        if value is None:
            return ""
        try:
            if value != value:
                return ""
        except (TypeError, ValueError):
            return str(value).strip()
        return str(value).strip()
