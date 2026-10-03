# -*- coding: utf-8 -*-
"""
ListViewWidget — Lista vertical genérica com scroll opcional
==============================================================
Similar a um RecyclerView. Container com QVBoxLayout que aceita
adicionar/remover widgets dinamicamente. Com scroll=True (padrão),
envolve em QScrollArea. Com scroll=False, vira um QVBoxLayout puro.

Uso:
    from resources.widgets.ListViewWidget import ListViewWidget

    # Com scroll (padrão):
    view = ListViewWidget()
    view.add_widget(MeuWidget())

    # Sem scroll (layout puro):
    view = ListViewWidget(scroll=False)
    view.add_widget(OutroWidget())
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea,
)


class ListViewWidget(QWidget):
    """
    Lista vertical genérica com scroll opcional.

    scroll=True (padrão): QScrollArea com frameless, sem scroll horizontal.
    scroll=False: QVBoxLayout puro.

    O `content_layout` (QVBoxLayout) é exposto para manipulação direta.
    spacing default = 8.
    """

    def __init__(
        self,
        spacing: int = 8,
        margins: tuple[int, int, int, int] = (0, 0, 0, 0),
        scroll: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("list_view_widget")
        self.setStyleSheet("QWidget#list_view_widget { background: transparent; }")
        self._scroll = scroll
        self._scroll_area: Optional[QScrollArea] = None

        if scroll:
            # ── Com scroll ─────────────────────────────────────────
            self._scroll_area = QScrollArea()
            self._scroll_area.setWidgetResizable(True)
            self._scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
            self._scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
            self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
            self._scroll_area.setStyleSheet("QScrollArea { background: transparent; }")

            self._content = QWidget()
            self._content.setStyleSheet("background: transparent;")
            self._content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.content_layout = QVBoxLayout(self._content)
            self.content_layout.setSpacing(spacing)
            self.content_layout.setContentsMargins(*margins)
            self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            self._scroll_area.setWidget(self._content)

            self._outer_layout = QVBoxLayout(self)
            self._outer_layout.setContentsMargins(0, 0, 0, 0)
            self._outer_layout.setSpacing(0)
            self._outer_layout.addWidget(self._scroll_area)
        else:
            # ── Sem scroll — layout puro ───────────────────────────
            self.content_layout = QVBoxLayout(self)
            self.content_layout.setSpacing(spacing)
            self.content_layout.setContentsMargins(*margins)
            self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    # ── Public API ─────────────────────────────────────────────────

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        """Adiciona um widget ao final da lista."""
        self.content_layout.addWidget(widget, stretch)

    def insert_widget(self, index: int, widget: QWidget) -> None:
        """Insere um widget em uma posição específica."""
        self.content_layout.insertWidget(index, widget)

    def remove_widget(self, widget: QWidget) -> None:
        """Remove um widget específico da lista."""
        self.content_layout.removeWidget(widget)
        widget.setParent(None)

    def remove_all(self) -> None:
        """Remove todos os widgets da lista."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

    def count(self) -> int:
        """Retorna o número de widgets na lista."""
        return self.content_layout.count()

    def scroll_to_top(self) -> None:
        """Rola a lista para o topo (no-op se scroll=False)."""
        if self._scroll_area:
            self._scroll_area.verticalScrollBar().setValue(0)

    def scroll_to_bottom(self) -> None:
        """Rola a lista para o final (no-op se scroll=False)."""
        if self._scroll_area:
            sb = self._scroll_area.verticalScrollBar()
            sb.setValue(sb.maximum())