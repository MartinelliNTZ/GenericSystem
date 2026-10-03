# -*- coding: utf-8 -*-
"""
Raster — Pacote de utilitarios para dados raster
==================================================
Fornece classes para manipulacao de camadas raster:
- RasterLayerSource: I/O, carregamento, basemaps Google
- RasterLayerMetrics: Estatisticas e calculos analiticos (percentis, min/max)
- RasterLayerProcessing: Processamento pixel a pixel (extrair bandas, mascaras)
- RasterLayerProjection: CRS, resolucao, alinhamento, reprojecao
- RasterLayerRendering: Simbologia, estilo QML, rampas de cor
- RasterVectorBridge: Conversao bidirecional raster <-> vetor
"""

from __future__ import annotations

from utils.raster.RasterLayerMetrics import RasterLayerMetrics
from utils.raster.RasterLayerProcessing import RasterLayerProcessing
from utils.raster.RasterLayerProjection import RasterLayerProjection
from utils.raster.RasterLayerRendering import RasterLayerRendering
from utils.raster.RasterLayerSource import RasterLayerSource
from utils.raster.RasterVectorBridge import RasterVectorBridge

__all__ = [
    "RasterLayerMetrics",
    "RasterLayerProcessing",
    "RasterLayerProjection",
    "RasterLayerRendering",
    "RasterLayerSource",
    "RasterVectorBridge",
]