# -*- coding: utf-8 -*-
"""
MapLayer — DTO de camada sobreposta no mapa
=============================================
Armazena dados de uma camada carregada (LAS, SHP, KML) para renderização.
"""

from __future__ import annotations

from typing import Any


class MapLayer:
    """
    Representa uma camada carregada no visualizador de mapas.

    Attributes:
        path: Caminho do arquivo de origem.
        layer_type: Tipo da camada ("las", "vector", "kml").
        crs: CRS original da camada (ex: "EPSG:31983").
        data: Dados processados pelo renderizador (dict).
        bounds: Bounding box (min_x, min_y, max_x, max_y) em EPSG:3857.
        visible: Se a camada está visível.
        name: Nome amigável (nome do arquivo sem extensão).
    """

    def __init__(
        self,
        path: str,
        layer_type: str,
        data: dict[str, Any],
        bounds: tuple[float, float, float, float],
        crs: str = "",
        name: str = "",
    ) -> None:
        self.path = path
        self.layer_type = layer_type
        self.crs = crs
        self.data = data
        self.bounds = bounds
        self.visible = True
        self.name = name or path.split("/")[-1].split("\\")[-1]