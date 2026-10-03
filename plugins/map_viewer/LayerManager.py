# -*- coding: utf-8 -*-
"""
LayerManager — Gerenciamento de camadas sobrepostas no mapa
=============================================================
Mantém a lista de camadas carregadas (LAS, SHP, KML) e fornece
métodos para adicionar, remover e consultar.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Signal

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from plugins.map_viewer.model.MapLayer import MapLayer


class LayerManager(QObject):
    """
    Gerencia a lista de camadas sobrepostas no canvas do mapa.

    Sinais:
        layers_changed() — emitido quando a lista de camadas é alterada.
    """

    layers_changed = Signal()

    def __init__(self, tool_key: str = ToolKey.UNTRACEABLE.value) -> None:
        super().__init__()
        self._tool_key = tool_key
        self._logger = BaseUtil._get_logger(tool_key, "LayerManager")
        self._layers: list[MapLayer] = []
        self._max_layers = 10

    # ── API Pública ────────────────────────────────────────────────

    def add_layer(self, layer: MapLayer) -> bool:
        """
        Adiciona uma camada. Se atingir o limite, remove a mais antiga.

        Returns:
            True se adicionou, False se a camada já existe.
        """
        # Evita duplicatas por path
        if any(l.path == layer.path for l in self._layers):
            self._logger.warning(
                "Camada já existe, ignorando",
                code="LAYER_DUP",
                path=layer.path,
            )
            return False

        # Remove a mais antiga se atingir limite
        if len(self._layers) >= self._max_layers:
            removed = self._layers.pop(0)
            self._logger.info(
                "Limite de camadas atingido, removendo mais antiga",
                code="LAYER_LIMIT",
                removed=removed.name,
            )

        self._layers.append(layer)
        self._logger.info(
            "Camada adicionada",
            code="LAYER_ADDED",
            name=layer.name,
            type=layer.layer_type,
        )
        self.layers_changed.emit()
        return True

    def remove_layer(self, index: int) -> bool:
        """Remove uma camada pelo índice."""
        if 0 <= index < len(self._layers):
            removed = self._layers.pop(index)
            self._logger.info(
                "Camada removida",
                code="LAYER_REMOVED",
                name=removed.name,
            )
            self.layers_changed.emit()
            return True
        return False

    def remove_all(self) -> None:
        """Remove todas as camadas."""
        self._layers.clear()
        self._logger.info("Todas as camadas removidas", code="LAYER_CLEARED")
        self.layers_changed.emit()

    def get_layers(self) -> list[MapLayer]:
        """Retorna a lista de camadas."""
        return list(self._layers)

    def get_visible_layers(self) -> list[MapLayer]:
        """Retorna apenas camadas visíveis."""
        return [l for l in self._layers if l.visible]

    def set_visible(self, index: int, visible: bool) -> None:
        """Altera a visibilidade de uma camada."""
        if 0 <= index < len(self._layers):
            self._layers[index].visible = visible
            self.layers_changed.emit()

    def count(self) -> int:
        """Número de camadas."""
        return len(self._layers)

    def get_layer(self, index: int) -> MapLayer | None:
        """Retorna uma camada pelo índice."""
        if 0 <= index < len(self._layers):
            return self._layers[index]
        return None