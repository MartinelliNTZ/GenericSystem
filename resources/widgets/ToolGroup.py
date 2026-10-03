# -*- coding: utf-8 -*-
"""
ToolGroup — Grupo horizontal de ferramentas na toolbar principal.
==================================================================
Cada ToolGroup representa uma categoria (System, Raster, Vector, etc.)
com botões de ícone para cada ferramenta da cattegoria.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QHBoxLayout

from core.enum.ToolType import ToolType
from core.model.Tool import Tool
from resources.styles.AppStyles import AppStyles
from resources.widgets.ToolSeparator import ToolSeparator
from resources.widgets.buttons.ToolbarButton import ToolbarButton


class ToolGroup(QWidget):
    """
    Grupo de ferramentas na toolbar horizontal.

    Layout vertical com título no topo e botões de ícone abaixo,
    seguido de um separador decorativo.
    """

    tool_clicked = Signal(str)  # nome da ferramenta

    def __init__(
        self,
        tool_type: ToolType,
        tools: list[Tool],
        parent=None,
    ):
        super().__init__(parent)
        self._tool_type = tool_type

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        # ── Título do grupo (acima dos botões) ──
        lbl = QLabel(tool_type.value)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(AppStyles.tool_group_label_style())
        layout.addWidget(lbl)

        # ── Linha horizontal com botões ──
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        for tool in tools:
            btn = ToolbarButton(tool)
            btn.tool_clicked.connect(self.tool_clicked.emit)
            row.addWidget(btn)
        row.addWidget(ToolSeparator())
        layout.addLayout(row)

    @property
    def tool_type(self) -> ToolType:
        return self._tool_type