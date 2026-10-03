# -*- coding: utf-8 -*-
"""
MapInfos — Barra de informações horizontais para visualizadores geoespaciais
==============================================================================
Widget reutilizável que exibe informações lado a lado (coordenadas, zoom, CRS,
contagem de camadas) com separadores verticais.

Uso:
    infos = MapInfos()
    infos.set_coords(-15.78, -47.93)
    infos.set_zoom(12)
    infos.set_crs("EPSG:3857")
    infos.set_layer_count(3)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from resources.widgets.SeparatorWidget import SeparatorWidget


class MapInfos(QWidget):
    """
    Barra de informações horizontais para visualizadores geoespaciais.

    Exibe labels lado a lado no formato:
    [📍 Lat: -15.78  Lon: -47.93] | [🔍 Zoom: 12] | [🗺 EPSG:3857] | [📦 3 camadas]
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MapInfos")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(6)

        self._labels: dict[str, QLabel] = {}

        fields = [
            ("coords", "📍 Lat: —  Lon: —"),
            ("zoom", "🔍 Zoom: —"),
            ("crs", "🗺 EPSG:3857"),
            ("layers", "📦 0 camadas"),
        ]

        for i, (key, text) in enumerate(fields):
            if i > 0:
                sep = SeparatorWidget(orientation="vertical")
                sep.setFixedHeight(18)
                layout.addWidget(sep)

            label = QLabel(text)
            label.setStyleSheet("color: #aaa; font-size: 11px; background: transparent;")
            self._labels[key] = label
            layout.addWidget(label)

        layout.addStretch()

    # ── API Pública ────────────────────────────────────────────────

    def set_coords(self, lat: float, lon: float) -> None:
        """Atualiza as coordenadas exibidas."""
        self._labels["coords"].setText(f"📍 Lat: {lat:.4f}  Lon: {lon:.4f}")

    def set_zoom(self, zoom: int) -> None:
        """Atualiza o nível de zoom."""
        self._labels["zoom"].setText(f"🔍 Zoom: {zoom}")

    def set_crs(self, crs: str) -> None:
        """Atualiza o CRS exibido."""
        self._labels["crs"].setText(f"🗺 {crs}")

    def set_layer_count(self, count: int) -> None:
        """Atualiza a contagem de camadas."""
        self._labels["layers"].setText(f"📦 {count} camada(s)")

    def clear_coords(self) -> None:
        """Limpa as coordenadas."""
        self._labels["coords"].setText("📍 Lat: —  Lon: —")