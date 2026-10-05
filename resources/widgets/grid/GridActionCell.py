# -*- coding: utf-8 -*-
"""
GridActionCell — Linha horizontal genérica de widgets de ação
=============================================================
Container para empacotar widgets de ação (botões, menu buttons) em uma
única célula de tabela/árvore, evitando QHBoxLayout solto nos plugins.

Uso:
    from resources.widgets.grid.GridActionCell import GridActionCell

    cell = GridActionCell(btn_abrir, menu_button)
    tree.set_cell_widget(key, col, cell)
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QWidget


class GridActionCell(QWidget):
    """Container horizontal com os widgets de ação alinhados à esquerda."""

    def __init__(self, *widgets: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(4)
        for widget in widgets:
            self._layout.addWidget(widget)
        self._layout.addStretch()

    def add_widget(self, widget: QWidget) -> None:
        """Adiciona um widget de ação ao final (antes do stretch)."""
        self._layout.insertWidget(self._layout.count() - 1, widget)
