# -*- coding: utf-8 -*-
"""
VectorLayerRenderer — Renderizador de vetores SHP/GPKG
=========================================================
Lê arquivos vetoriais (.shp, .gpkg) via geopandas, converte
geometrias para EPSG:3857 e desenha no canvas do mapa.
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPolygonF

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class VectorLayerRenderer:
    """
    Renderizador de camadas vetoriais (SHP, GPKG).
    Métodos estáticos — sem estado.
    """

    @staticmethod
    def read(path: str, tool_key: str = ToolKey.UNTRACEABLE.value) -> dict[str, Any] | None:
        """
        Lê um arquivo vetorial via geopandas.

        Returns:
            Dict com geometries, bounds, count ou None se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerRenderer")

        try:
            import geopandas as gpd
            gdf = gpd.read_file(path)

            if gdf.empty:
                logger.warning("Shapefile vazio", code="VEC_EMPTY", path=path)
                return None

            # Converte para EPSG:3857 se tiver CRS
            if gdf.crs and gdf.crs.to_string() not in ("EPSG:3857", ""):
                try:
                    gdf = gdf.to_crs("EPSG:3857")
                except Exception as e:
                    logger.warning("Falha ao reprojetar, usando CRS original", code="VEC_REPROJ_FAIL", error=str(e))

            bounds = (
                float(gdf.total_bounds[0]),
                float(gdf.total_bounds[1]),
                float(gdf.total_bounds[2]),
                float(gdf.total_bounds[3]),
            )

            geometries = []
            for geom in gdf.geometry:
                if geom is not None and not geom.is_empty:
                    geometries.append(geom)

            logger.info(
                "Vetor carregado",
                code="VEC_LOADED",
                path=path,
                features=len(geometries),
            )
            return {
                "geometries": geometries,
                "bounds": bounds,
                "count": len(geometries),
            }

        except ImportError:
            logger.error("geopandas não instalado", code="VEC_NO_LIB")
            return None
        except Exception as e:
            logger.error("Erro ao ler vetor", code="VEC_READ_ERR", error=str(e), path=path)
            return None

    @staticmethod
    def render(
        painter: QPainter,
        data: dict[str, Any],
        world_to_pixel: Callable[[float, float], QPointF],
        zoom: float,
    ) -> None:
        """
        Desenha geometrias vetoriais no canvas.

        Suporta Point, LineString, Polygon (shapely geometries).
        """
        geometries = data.get("geometries", [])
        if not geometries:
            return

        # Cores por tipo de geometria
        colors = {
            "Polygon": (QColor(255, 255, 0, 200), QColor(255, 255, 0, 40)),
            "MultiPolygon": (QColor(255, 255, 0, 200), QColor(255, 255, 0, 40)),
            "LineString": (QColor(0, 255, 255, 220), QColor(0, 255, 255, 0)),
            "MultiLineString": (QColor(0, 255, 255, 220), QColor(0, 255, 255, 0)),
            "Point": (QColor(255, 0, 255, 220), QColor(255, 0, 255, 100)),
            "MultiPoint": (QColor(255, 0, 255, 220), QColor(255, 0, 255, 100)),
        }

        for geom in geometries:
            geom_type = getattr(geom, 'geom_type', 'Unknown')
            stroke, fill = colors.get(geom_type, (QColor(255, 255, 0, 200), QColor(255, 255, 0, 40)))

            if geom_type == 'Point':
                coords = list(geom.coords)
                if coords:
                    pt = world_to_pixel(coords[0][0], coords[0][1])
                    painter.setPen(stroke)
                    painter.setBrush(fill)
                    painter.drawEllipse(pt, 5, 5)
                    painter.setBrush(Qt.BrushStyle.NoBrush)

            elif 'Polygon' in geom_type:
                if geom_type == 'MultiPolygon':
                    polys = geom.geoms
                else:
                    polys = [geom]

                for poly in polys:
                    exterior = poly.exterior
                    if exterior and len(exterior.coords) >= 3:
                        pts = QPolygonF([world_to_pixel(x, y) for x, y in exterior.coords])
                        painter.setPen(stroke)
                        painter.setBrush(fill)
                        painter.drawPolygon(pts)
                        painter.setBrush(Qt.BrushStyle.NoBrush)

            elif 'LineString' in geom_type:
                if geom_type == 'MultiLineString':
                    lines = geom.geoms
                else:
                    lines = [geom]

                for line in lines:
                    coords = list(line.coords)
                    if len(coords) >= 2:
                        pts = QPolygonF([world_to_pixel(x, y) for x, y in coords])
                        painter.setPen(stroke)
                        painter.drawPolyline(pts)

            elif geom_type == 'Point':
                coords = list(geom.coords)
                if coords:
                    pt = world_to_pixel(coords[0][0], coords[0][1])
                    painter.setPen(stroke)
                    painter.setBrush(fill)
                    painter.drawEllipse(pt, 5, 5)
                    painter.setBrush(Qt.BrushStyle.NoBrush)

            elif 'MultiPoint' in geom_type:
                for point in geom.geoms:
                    coords = list(point.coords)
                    if coords:
                        pt = world_to_pixel(coords[0][0], coords[0][1])
                        painter.setPen(stroke)
                        painter.setBrush(fill)
                        painter.drawEllipse(pt, 5, 5)
                        painter.setBrush(Qt.BrushStyle.NoBrush)