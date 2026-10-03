# -*- coding: utf-8 -*-
"""
ToolSeparator — Separador decorativo entre ToolGroups.
======================================================
Suporta orientação vertical e horizontal.
Gradiente dourado suave com fade nas extremidades.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QBrush
from PySide6.QtCore import Qt, QPointF, QRectF

from resources.styles.AppStyles import AppStyles


class ToolSeparator(QWidget):
    """
    Separador slim com fade usando ACCENT como cor base.

    Args:
        orientation: "vertical" (padrão) ou "horizontal"
    """

    def __init__(self, parent=None, orientation: str = "vertical"):
        super().__init__(parent)
        self._orientation = orientation.lower()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._apply_size_policy()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _apply_size_policy(self) -> None:
        if self._orientation == "horizontal":
            self.setFixedHeight(1)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        else:
            self.setFixedWidth(1.2)
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # Busca ACCENT do tema via AppStyles
        P = AppStyles.theme_colors()
        accent_hex = P.get("ACCENT", "#C9A84C")
        c = QColor(accent_hex)
        r, g, b = c.red(), c.green(), c.blue()

        # Gradiente ao longo do eixo principal
        if self._orientation == "horizontal":
            start = QPointF(0.0, 0.0)
            end   = QPointF(w,   0.0)
        else:
            start = QPointF(0.0, 0.0)
            end   = QPointF(0.0, h)

        grad = QLinearGradient(start, end)
        grad.setColorAt(0.00, QColor(r, g, b,   0))
        grad.setColorAt(0.12, QColor(r, g, b,  18))
        grad.setColorAt(0.30, QColor(r, g, b,  90))
        grad.setColorAt(0.50, QColor(r, g, b, 185))
        grad.setColorAt(0.70, QColor(r, g, b,  90))
        grad.setColorAt(0.88, QColor(r, g, b,  18))
        grad.setColorAt(1.00, QColor(r, g, b,   0))

        painter.fillRect(QRectF(0.0, 0.0, w, h), QBrush(grad))