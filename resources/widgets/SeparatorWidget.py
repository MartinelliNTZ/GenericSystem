# -*- coding: utf-8 -*-
"""
SeparatorWidget — Linha horizontal ou vertical estilizada
===========================================================
Substitui QFrame com HLine/VLine manual. Estilizado via QSS
global (BaseStyle), sem hardcoded colors.

Uso:
    from resources.widgets.SeparatorWidget import SeparatorWidget

    hline = SeparatorWidget(orientation="horizontal")
    vline = SeparatorWidget(orientation="vertical")
"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame


class SeparatorWidget(QFrame):
    """
    Linha separadora estilizada.

    orientation: "horizontal" (padrão) ou "vertical"
    """

    def __init__(
        self,
        orientation: str = "horizontal",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("separator")
        if orientation == "vertical":
            self.setFrameShape(QFrame.Shape.VLine)
            self.setFixedWidth(1)
        else:
            self.setFrameShape(QFrame.Shape.HLine)
            self.setFixedHeight(1)