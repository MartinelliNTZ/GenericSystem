# -*- coding: utf-8 -*-
"""
RasterLayerSource — I/O de camadas raster
===========================================
Responsavel pelo carregamento, salvamento e criacao de camadas raster:
carregamento de arquivos GeoTIFF, carregamento de URLs remotas (XYZ/WMS),
adicao de basemaps Google (hybrid/satellite/road).

Uso:
    from utils.raster.RasterLayerSource import RasterLayerSource
    raster = RasterLayerSource().load_raster_from_file("mosaico.tif", external_tool_key=...)
    basemap = RasterLayerSource().add_google_basemap(project, "satellite", external_tool_key=...)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RasterLayerSource(BaseUtil):
    """
    Metodos de instancia para I/O de camadas raster.
    Nao reprojeta — use RasterLayerProjection para isso.
    Nao processa pixels — use RasterLayerProcessing para isso.
    """

    GOOGLE_BASEMAP_VARIANTS = {
        "hybrid": {"lyrs": "y", "label": "Google Hybrid"},
        "satellite": {"lyrs": "s", "label": "Google Satellite"},
        "road": {"lyrs": "m", "label": "Google Road"},
    }

    # ── API Publica — Carregamento ───────────────────────────────────

    def load_raster_from_file(
        self,
        file_path: str,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Carrega raster de arquivo (GeoTIFF, IMG, etc).

        Args:
            file_path: Caminho do arquivo
            external_tool_key: Chave da ferramenta para logging

        Returns:
            QgsRasterLayer ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerSource")
        logger.info("load_raster_from_file chamado — stub", code="RASTER_LOAD_STUB")
        return None

    def load_raster_from_url(
        self,
        url: str,
        cache_directory: Optional[str] = None,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
        layer_name: Optional[str] = None,
        provider_key: Optional[str] = None,
    ) -> Any:
        """
        Carrega raster remoto (XYZ/WMS).

        Args:
            url: URL do servico
            cache_directory: Diretorio de cache (opcional)
            external_tool_key: Chave da ferramenta para logging
            layer_name: Nome da camada (opcional)
            provider_key: Chave do provider (opcional)

        Returns:
            QgsRasterLayer ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerSource")
        logger.info("load_raster_from_url chamado — stub", code="RASTER_LOAD_STUB")
        return None

    def add_google_basemap(
        self,
        project: Any,
        basemap_style: str = "satellite",
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
        layer_name: Optional[str] = None,
    ) -> Any:
        """
        Adiciona camada base Google (hybrid/satellite/road) evitando duplicidade.

        Args:
            project: QgsProject instance
            basemap_style: Estilo do basemap ("hybrid", "satellite", "road")
            external_tool_key: Chave da ferramenta para logging
            layer_name: Nome personalizado (opcional)

        Returns:
            QgsRasterLayer ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerSource")
        logger.info("add_google_basemap chamado — stub", code="RASTER_LOAD_STUB")
        return None

    # ── API Publica — Utilitarios ────────────────────────────────────

    def get_raster_info(
        self,
        file_path: str,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Obtem informacoes basicas de um raster.

        Args:
            file_path: Caminho do arquivo
            external_tool_key: Chave da ferramenta para logging

        Returns:
            Dict com informacoes do raster.
        """
        logger = BaseUtil._get_logger(external_tool_key, "RasterLayerSource")
        logger.info("get_raster_info chamado — stub", code="RASTER_UTIL_STUB")
        return {
            "width": 0,
            "height": 0,
            "band_count": 0,
            "crs": None,
            "dtype": None,
        }