# -*- coding: utf-8 -*-
"""
RasterLayerProjection — CRS, resolucao, alinhamento e extent de rasters
========================================================================
Responsavel por CRS, resolucao, alinhamento, extent e reprojecao de rasters.

Uso:
    from utils.raster.RasterLayerProjection import RasterLayerProjection
    output = RasterLayerProjection.reproject_raster_to_crs(
        "raster.tif", "EPSG:31983", external_tool_key=...
    )
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RasterLayerProjection(BaseUtil):
    """
    Metodos estaticos para CRS, resolucao e reprojecao de rasters.
    Nao altera valores de pixels — use RasterLayerProcessing para isso.
    Nao carrega/salva — use RasterLayerSource para isso.
    """

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def get_raster_crs(
        raster: Any,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Obtem CRS do raster (QgsRasterLayer ou caminho string).

        Args:
            raster: QgsRasterLayer ou caminho string
            external_tool_key: Chave da ferramenta para logging

        Returns:
            QgsCoordinateReferenceSystem ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerProjection")
        logger.info("get_raster_crs chamado — stub", code="RASTER_PROJ_STUB")
        return None

    @staticmethod
    def reproject_raster_to_crs(
        raster_path: str,
        target_crs: Any,
        resampling_method: Any = None,
        nodata_value: Optional[float] = None,
        target_resolution: Optional[float] = None,
        output_path: Optional[str] = None,
        multithreading: bool = False,
        creation_options: str = "",
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Reprojeta/reamostra raster via gdal:warpreproject.

        Args:
            raster_path: Caminho do raster de entrada
            target_crs: CRS de destino (str ou QgsCRS)
            resampling_method: Metodo de reamostragem (ResamplingMethod enum)
            nodata_value: Valor NoData (herdado se None)
            target_resolution: Resolucao de destino (pula reamostragem se None)
            output_path: Caminho de saida (temp se None)
            multithreading: Processamento multi-thread
            creation_options: Opcoes GDAL extras
            external_tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do raster reprojetado.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerProjection")
        logger.info("reproject_raster_to_crs chamado — stub", code="RASTER_PROJ_STUB")
        return output_path or ""

    @staticmethod
    def align_rasters(
        raster_paths: list,
        target_crs: Any = None,
        target_resolution: Optional[float] = None,
        resampling_method: Any = None,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> list:
        """
        Alinha multiplos rasters para mesmo CRS e resolucao.

        Args:
            raster_paths: Lista de caminhos de rasters
            target_crs: CRS de destino (usa do primeiro se None)
            target_resolution: Resolucao de destino
            resampling_method: Metodo de reamostragem
            external_tool_key: Chave da ferramenta para logging

        Returns:
            Lista de caminhos dos rasters alinhados.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerProjection")
        logger.info("align_rasters chamado — stub", code="RASTER_PROJ_STUB")
        return raster_paths

    @staticmethod
    def get_raster_extent(
        raster_path: str,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[Dict[str, float]]:
        """
        Obtem extent de um raster.

        Args:
            raster_path: Caminho do raster
            external_tool_key: Chave da ferramenta para logging

        Returns:
            Dict com xmin, ymin, xmax, ymax ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerProjection")
        logger.info("get_raster_extent chamado — stub", code="RASTER_PROJ_STUB")
        return None
