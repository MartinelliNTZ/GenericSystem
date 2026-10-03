# -*- coding: utf-8 -*-
"""
RasterLayerMetrics — Estatisticas e calculos analiticos de rasters
====================================================================
Responsavel por estatisticas e calculos analiticos (percentis, min/max).
NAO altera dados — apenas mede/calcula.

Uso:
    from utils.raster.RasterLayerMetrics import RasterLayerMetrics
    p_low, p_high = RasterLayerMetrics.get_band_percentiles("raster.tif", 1, tool_key=...)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RasterLayerMetrics(BaseUtil):
    """
    Metodos estaticos para calculos analiticos de rasters.
    Nao processa pixels — use RasterLayerProcessing para isso.
    Nao reprojeta — use RasterLayerProjection para isso.
    """

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def get_band_percentiles(
        raster_path: str,
        band_index: int,
        lower_pct: float = 2.0,
        upper_pct: float = 98.0,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Tuple[float, float]:
        """
        Calcula percentis de uma banda (usando numpy).

        Args:
            raster_path: Caminho do raster
            band_index: Indice da banda (1-based)
            lower_pct: Percentil inferior
            upper_pct: Percentil superior
            tool_key: Chave da ferramenta para logging

        Returns:
            (percentil_inferior, percentil_superior).
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerMetrics")
        logger.info("get_band_percentiles chamado — stub", code="RASTER_METRIC_STUB")
        return (0.0, 0.0)

    @staticmethod
    def get_global_min_max(
        values: List[Tuple[float, float]],
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Tuple[float, float]:
        """
        Min/max global a partir de lista de tuplas (min, max).

        Args:
            values: Lista de tuplas (min, max)
            tool_key: Chave da ferramenta para logging

        Returns:
            (global_min, global_max).
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerMetrics")
        if not values:
            return (0.0, 0.0)
        global_min = min(v[0] for v in values)
        global_max = max(v[1] for v in values)
        return (global_min, global_max)

    @staticmethod
    def get_global_min_max_from_rasters(
        raster_band_tuples: List[Tuple[str, int]],
        lower_pct: float = 2.0,
        upper_pct: float = 98.0,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Tuple[float, float]:
        """
        Min/max global de multiplos rasters.

        Args:
            raster_band_tuples: Lista de (raster_path, band_index)
            lower_pct: Percentil inferior
            upper_pct: Percentil superior
            tool_key: Chave da ferramenta para logging

        Returns:
            (global_min, global_max).
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerMetrics")
        logger.info("get_global_min_max_from_rasters chamado — stub", code="RASTER_METRIC_STUB")
        return (0.0, 0.0)

    @staticmethod
    def get_raster_statistics(
        raster_path: str,
        band_index: int = 1,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, float]:
        """
        Obtem estatisticas basicas de uma banda (min, max, mean, std).

        Args:
            raster_path: Caminho do raster
            band_index: Indice da banda (1-based)
            tool_key: Chave da ferramenta para logging

        Returns:
            Dict com min, max, mean, std.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerMetrics")
        logger.info("get_raster_statistics chamado — stub", code="RASTER_METRIC_STUB")
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}