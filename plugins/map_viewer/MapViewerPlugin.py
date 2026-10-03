# -*- coding: utf-8 -*-
"""
MapViewerPlugin — Visualizador geoespacial com basemap de satélite
====================================================================
Plugin que exibe um mapa navegável com tiles de satélite como fundo,
permitindo arrastar e soltar arquivos LAS/LAZ, SHP/GPKG e KML.
"""

from __future__ import annotations

from typing import Any

from plugins.BasePlugin import BasePlugin
from plugins.map_viewer.MapCanvasWidget import MapCanvasWidget
from resources.widgets.MapInfos import MapInfos


class MapViewerPlugin(BasePlugin):
    """
    Plugin visualizador de mapas com basemap de satélite.

    Sem ExecutionButtons pois é apenas visualizador (não executa nada).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(
            tool_key="MapViewer",
            parent=parent,
            title="Visualizador de Mapas",
            # Sem buttons_config — ferramenta apenas visualiza
        )

    def _build_ui(self) -> None:
        """Constrói a UI: canvas do mapa + barra de informações na parte inferior."""
        super()._build_ui()

        # Canvas do mapa (stretch=1 para ocupar todo espaço)
        self._canvas = MapCanvasWidget(tool_key=self.tool_key, parent=self)
        self.main_layout.addWidget(self._canvas, stretch=1)

        # Barra de informações na parte inferior
        self._map_infos = MapInfos(self)
        self.main_layout.addWidget(self._map_infos)

        # Conecta callback do canvas para atualizar MapInfos
        self._canvas.on_info_changed = self._on_canvas_info_changed

        # Conecta mudanças de camadas para atualizar contagem
        self._canvas.layer_manager.layers_changed.connect(self._on_layers_changed)

        # Estado inicial das infos
        self._on_canvas_info_changed(-15.8, -48.0, 5, "EPSG:3857")
        self._map_infos.set_layer_count(0)

        self.logger.info("UI do MapViewer construída", code="MV_UI_READY")

    def _on_canvas_info_changed(self, lat: float, lon: float, zoom: int, crs: str) -> None:
        """Atualiza a barra de informações com dados do canvas."""
        self._map_infos.set_coords(lat, lon)
        self._map_infos.set_zoom(zoom)
        self._map_infos.set_crs(crs)

    def _on_layers_changed(self) -> None:
        """Atualiza contagem de camadas na barra de informações."""
        count = self._canvas.layer_manager.count()
        self._map_infos.set_layer_count(count)

    # ── Preferências ─────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Restaura última posição e zoom do mapa."""
        state_str = self.preferences.get("map_state", None)
        if state_str and self._canvas:
            try:
                import json
                state = json.loads(state_str)
                self._canvas.restore_state(state)
                self.logger.info("Estado do mapa restaurado", code="MV_STATE_RESTORED")
            except Exception as e:
                self.logger.warning("Falha ao restaurar estado", code="MV_STATE_ERR", error=str(e))

    def save_prefs(self) -> None:
        """Salva posição e zoom atuais do mapa."""
        if self._canvas:
            try:
                import json
                state = self._canvas.save_state()
                self.preferences["map_state"] = json.dumps(state)
                self.logger.info("Estado do mapa salvo", code="MV_STATE_SAVED")
            except Exception as e:
                self.logger.warning("Falha ao salvar estado", code="MV_STATE_SAVE_ERR", error=str(e))

    # ── Cleanup ──────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """Garante que preferências são salvas ao fechar."""
        self.save_prefs()
        super().closeEvent(event)