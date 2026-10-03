# -*- coding: utf-8 -*-
"""
KmlLayerRenderer — Renderizador de arquivos KML
==================================================
Lê arquivos KML, extrai geometrias (Point, LineString, Polygon),
converte para EPSG:3857 e desenha no canvas do mapa.
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPolygonF

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class KmlLayerRenderer:
    """
    Renderizador de arquivos KML.
    Métodos estáticos — sem estado.
    """

    @staticmethod
    def read(path: str, tool_key: str = ToolKey.UNTRACEABLE.value) -> dict[str, Any] | None:
        """
        Lê um arquivo KML e extrai geometrias.

        Tenta usar fastkml primeiro, depois lxml parsing manual como fallback.

        Returns:
            Dict com geometries, names, bounds, count ou None se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "KmlLayerRenderer")

        # Tenta fastkml
        try:
            from fastkml import kml as fastkml_kml

            with open(path, "rb") as f:
                doc = fastkml_kml.KML()
                doc.from_string(f.read())

            geometries = []
            names = []
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')

            def extract_features(feature):
                if hasattr(feature, 'features'):
                    for f in feature.features:
                        extract_features(f)
                if hasattr(feature, 'geometry') and feature.geometry is not None:
                    geometries.append(feature.geometry)
                    names.append(getattr(feature, 'name', '') or '')
                    # Estima bounds
                    try:
                        bounds_obj = feature.geometry.bounds
                        min_x = min(min_x, bounds_obj[0])
                        min_y = min(min_y, bounds_obj[1])
                        max_x = max(max_x, bounds_obj[2])
                        max_y = max(max_y, bounds_obj[3])
                    except Exception:
                        pass

            if hasattr(doc, 'features'):
                for f in doc.features():
                    extract_features(f)

            if geometries:
                bounds = (min_x, min_y, max_x, max_y)
            else:
                bounds = (0, 0, 0, 0)

            logger.info("KML carregado (fastkml)", code="KML_LOADED", path=path, features=len(geometries))
            return {
                "geometries": geometries,
                "names": names,
                "bounds": bounds,
                "count": len(geometries),
            }

        except ImportError:
            pass
        except Exception as e:
            logger.warning("fastkml falhou, tentando fallback", code="KML_FASTKML_FAIL", error=str(e))

        # Fallback: lxml parsing manual
        try:
            from lxml import etree
            tree = etree.parse(path)
            ns = {"kml": "http://www.opengis.net/kml/2.2"}

            geometries = []
            names = []
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')

            for placemark in tree.findall(".//kml:Placemark", ns):
                name_elem = placemark.find("kml:name", ns)
                name = name_elem.text if name_elem is not None else ""

                for coord_elem in placemark.findall(".//kml:coordinates", ns):
                    text = coord_elem.text or ""
                    coords = []
                    for part in text.strip().split():
                        parts = part.split(",")
                        if len(parts) >= 2:
                            lon, lat = float(parts[0]), float(parts[1])
                            coords.append((lon, lat))
                            min_x = min(min_x, lon)
                            min_y = min(min_y, lat)
                            max_x = max(max_x, lon)
                            max_y = max(max_y, lat)

                    if coords:
                        parent = coord_elem.getparent()
                        parent_tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
                        geometries.append({
                            "type": parent_tag,
                            "coordinates": coords,
                        })
                        names.append(name)

            bounds = (min_x, min_y, max_x, max_y) if geometries else (0, 0, 0, 0)
            logger.info("KML carregado (fallback)", code="KML_LOADED_FB", path=path, features=len(geometries))
            return {
                "geometries": geometries,
                "names": names,
                "bounds": bounds,
                "count": len(geometries),
            }

        except Exception as e:
            logger.error("Erro ao ler KML", code="KML_READ_ERR", error=str(e), path=path)
            return None

    @staticmethod
    def render(
        painter: QPainter,
        data: dict[str, Any],
        world_to_pixel: Callable[[float, float], QPointF],
        zoom: float,
    ) -> None:
        """
        Desenha geometrias KML no canvas.

        Suporta Point, LineString, LinearRing, Polygon.
        """
        geometries = data.get("geometries", [])
        if not geometries:
            return

        painter.setPen(QColor(0, 255, 255, 200))  # Ciano para KML

        for geom in geometries:
            # fastkml geometries têm .geom_type; fallback dict tem "type"
            if isinstance(geom, dict):
                geom_type = geom.get("type", "Unknown")
                coords = geom.get("coordinates", [])
            else:
                geom_type = getattr(geom, 'geom_type', 'Unknown')
                coords = list(geom.coords) if hasattr(geom, 'coords') else []

            if not coords:
                continue

            if 'Point' in geom_type:
                pt = world_to_pixel(coords[0][0] if isinstance(coords[0], (list, tuple)) else coords[0][0],
                                    coords[0][1] if isinstance(coords[0], (list, tuple)) else coords[0][1])
                painter.setBrush(QColor(0, 255, 255, 100))
                painter.drawEllipse(pt, 6, 6)
                painter.setBrush(Qt.BrushStyle.NoBrush)

            elif 'LineString' in geom_type or 'LinearRing' in geom_type:
                pts = [world_to_pixel(c[0], c[1]) for c in coords]
                if len(pts) >= 2:
                    poly = QPolygonF(pts)
                    painter.drawPolyline(poly)

            elif 'Polygon' in geom_type:
                exterior = geom.exterior if hasattr(geom, 'exterior') else (
                    coords[0] if isinstance(coords[0], list) else coords
                )
                if exterior and len(exterior) >= 3:
                    if isinstance(exterior, (list, tuple)):
                        pts = [world_to_pixel(c[0], c[1]) for c in exterior]
                    else:
                        pts = [world_to_pixel(c[0], c[1]) for c in exterior.coords]
                    if len(pts) >= 3:
                        poly = QPolygonF(pts)
                        painter.setBrush(QColor(0, 255, 255, 40))
                        painter.drawPolygon(poly)
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.setPen(QColor(0, 255, 255, 200))