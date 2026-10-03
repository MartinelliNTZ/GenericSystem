# -*- coding: utf-8 -*-
"""
ToolBar — Barra de ferramentas horizontal independente
======================================================
Agrupa ToolGroups em um container estilizado via AppStyles.
Nenhum hardcoded — todas as cores vêm do tema via AppStyles.

Uso:
    toolbar = ToolBar(groups=[...])
    root_layout.addWidget(toolbar)
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout

from resources.styles.AppStyles import AppStyles
from resources.widgets.ToolGroup import ToolGroup


class ToolBar(QWidget):
    """
    Container horizontal que agrupa ToolGroups.
    Estilo aplicado via AppStyles — zero valores hardcoded.
    """

    tool_clicked = Signal(str)

    def __init__(self, groups: List[ToolGroup] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("toolbar_panel")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(0)

        if groups:
            self.set_groups(groups)

        self._apply_style()

    def set_groups(self, groups: List[ToolGroup]) -> None:
        """Define os grupos da toolbar e conecta sinais."""
        for group in groups:
            group.tool_clicked.connect(self._on_tool_clicked)
            self._layout.addWidget(group)
        self._layout.addStretch()

    def _on_tool_clicked(self, tool_name: str) -> None:
        """Propaga o clique para o sinal tool_clicked."""
        self.tool_clicked.emit(tool_name)

    def _apply_style(self) -> None:
        """Aplica o stylesheet usando AppStyles (via BaseStyle)."""
        self.setStyleSheet(f"""
            QWidget#toolbar_panel {{
                background-color: {AppStyles.theme_colors()["BG_DEEPEST"]};
                border-bottom: 1px solid {AppStyles.theme_colors()["BORDER"]};
            }}
        """)