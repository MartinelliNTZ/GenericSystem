# -*- coding: utf-8 -*-
"""
LasLayerRenderer — Renderizador de nuvens LAS/LAZ
====================================================
Lê arquivos LAS/LAZ com laspy, converte coordenadas para EPSG:3857
e desenha pontos coloridos no canvas do mapa.
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils


class LasLayerRenderer:
    """
    Renderizador de nuvens de pontos LAS/LAZ.
    Métodos estáticos — sem estado.
    """

    @staticmethod
    def read(path: str, tool_key: str = ToolKey.UNTRACEABLE.value) -> dict[str, Any] | None:
        """
        Lê um arquivo LAS/LAZ e retorna dados processados.

        Returns:
            Dict com points, colors, bounds, count ou None se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasLayerRenderer")
        try:
            import laspy
        except ImportError:
            logger.error("laspy não instalado", code="LAS_NO_LIB")
            return None

        try:
            las = laspy.read(path)
            x = las.x.copy()
            y = las.y.copy()

            # Se tiver RGB, converte para 0-255
            has_color = bool(hasattr(las, 'red') and las.red.max() > 0)
            colors: np.ndarray | None = None
            if has_color:
                colors = np.column_stack([
                    np.clip(las.red // 256, 0, 255).astype(np.uint8),
                    np.clip(las.green // 256, 0, 255).astype(np.uint8),
                    np.clip(las.blue // 256, 0, 255).astype(np.uint8),
                    np.full(len(las), 255, dtype=np.uint8),
                ])

            # Bounds originais (valores nativos Python)
            bounds = (float(x.min()), float(y.min()), float(x.max()), float(y.max()))

            # Converte points para listas de floats nativos (evita numpy no log)
            points_list = np.column_stack([x, y]).astype(np.float64)

            logger.info(
                "LAS carregado",
                code="LAS_LOADED",
                path=path,
                points=int(len(las)),
                has_color=has_color,
            )
            return {
                "points": points_list,
                "colors": colors,
                "bounds": bounds,
                "count": int(len(las)),
            }

        except Exception as e:
            logger.error("Erro ao ler LAS", code="LAS_READ_ERR", error=str(e), path=path)
            return None

    @staticmethod
    def render(
        painter: QPainter,
        data: dict[str, Any],
        world_to_pixel: Callable[[float, float], QPointF],
        zoom: float,
    ) -> None:
        """
        Desenha os pontos da nuvem no canvas.

        Args:
            painter: QPainter do canvas.
            data: Dict retornado por read().
            world_to_pixel: Função de transformação coordenada → pixel.
            zoom: Nível de zoom atual.
        """
        points: np.ndarray = data["points"]
        colors: np.ndarray | None = data.get("colors")

        if points.size == 0:
            return

        # Subsampling adaptativo baseado no zoom
        n_points = len(points)
        step = 1
        if zoom < 10 and n_points > 50000:
            step = max(1, n_points // 50000)
        elif zoom < 14 and n_points > 200000:
            step = max(1, n_points // 200000)
        elif n_points > 500000:
            step = max(1, n_points // 500000)

        painter.setPen(QColor(255, 255, 255))  # Fallback white
        for i in range(0, n_points, step):
            pt = world_to_pixel(points[i][0], points[i][1])
            px, py = pt.x(), pt.y()
            w = painter.device().width()
            h = painter.device().height()
            if 0 <= px < w and 0 <= py < h:
                if colors is not None:
                    c = colors[i]
                    painter.setPen(QColor(int(c[0]), int(c[1]), int(c[2])))
                painter.drawPoint(QPointF(px, py))