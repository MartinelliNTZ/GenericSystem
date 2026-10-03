# -*- coding: utf-8 -*-
"""
ScrollWidget — Container rolável genérico
===========================================
Envolve qualquer widget em uma QScrollArea. Útil para conteúdos
que precisam de scroll mas não são listas.

Uso:
    from resources.widgets.ScrollWidget import ScrollWidget

    scroll = ScrollWidget(meu_widget_grande)
    parent_layout.addWidget(scroll)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea,
)


class ScrollWidget(QWidget):
    """
    Envolve um widget em QScrollArea com frameless.

    O widget interno expande horizontalmente (WidgetResizable=True).
    """

    def __init__(
        self,
        widget: QWidget | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        if widget is not None:
            self._scroll_area.setWidget(widget)

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)
        self._outer_layout.addWidget(self._scroll_area)

    def set_widget(self, widget: QWidget) -> None:
        """Define o widget interno (substitui widget anterior se houver)."""
        self._scroll_area.setWidget(widget)

    def scroll_to_top(self) -> None:
        """Rola para o topo."""
        self._scroll_area.verticalScrollBar().setValue(0)

    def scroll_to_bottom(self) -> None:
        """Rola para o final."""
        sb = self._scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())