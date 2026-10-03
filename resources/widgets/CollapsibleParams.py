# -*- coding: utf-8 -*-
"""
CollapsibleParams — Container colapsável com header clicável
=============================================================
Widget que agrupa outros widgets em uma seção que pode ser
recolhida ou expandida ao clicar no header.

Uso:
    from resources.widgets.CollapsibleParams import CollapsibleParams

    section = CollapsibleParams("Informações Avançadas", parent=self)
    section.content_layout.addWidget(QLabel("conteúdo"))
    main_layout.addWidget(section)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from resources.styles.AppStyles import AppStyles
from resources.widgets.simple.SimpleLabel import SimpleLabel


class CollapsibleParams(QWidget):
    """
    Container com header clicável que expande/recolhe o conteúdo.

    Attributes:
        header_label: SimpleLabel usado como header clicável.
        content_layout: QVBoxLayout onde os widgets filhos são adicionados.
        collapsed: Estado atual (True = recolhido).
    """

    def __init__(
        self,
        title: str = "Parâmetros",
        collapsed: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._collapsed = collapsed

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # ── Header clicável (altura fixa via AppStyles) ─────────
        self.header_label = SimpleLabel(self._format_title(title), self)
        self.header_label.setObjectName("collapsible_header")
        self.header_label.setStyleSheet(AppStyles.collapsible_header_style())
        self.header_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_label.setFixedHeight(int(AppStyles.collapsible_header_height()))
        self.header_label.mousePressEvent = self._on_header_clicked  # type: ignore[assignment]

        self._layout.addWidget(self.header_label)

        # ── Container de conteúdo (expande livremente) ──────────
        self._content_widget = QWidget()
        self._content_widget.setObjectName("collapsible_content")
        self._content_widget.setStyleSheet(AppStyles.collapsible_content_style())
        self.content_layout = QVBoxLayout(self._content_widget)
        self.content_layout.setContentsMargins(12, 6, 12, 6)
        self.content_layout.setSpacing(4)

        self._layout.addWidget(self._content_widget, 1)

        if collapsed:
            self._content_widget.setVisible(False)

    # ── Propriedades ────────────────────────────────────────────

    @property
    def collapsed(self) -> bool:
        """True se a seção está recolhida."""
        return self._collapsed

    @collapsed.setter
    def collapsed(self, value: bool) -> None:
        """Define estado recolhido/expandido."""
        self._collapsed = value
        self._content_widget.setVisible(not value)
        self.header_label.setText(self._format_title(
            self.header_label.text().lstrip("▶ ▼ ").strip()
        ))

    # ── Handlers ────────────────────────────────────────────────

    def _on_header_clicked(self, event) -> None:
        """Alterna entre recolhido e expandido."""
        self._collapsed = not self._collapsed
        self._content_widget.setVisible(not self._collapsed)
        # Extrai o título sem o ícone atual
        raw_title = self.header_label.text()
        for prefix in ("▶ ", "▼ "):
            if raw_title.startswith(prefix):
                raw_title = raw_title[len(prefix):]
                break
        self.header_label.setText(self._format_title(raw_title.strip()))

    # ── Helpers ─────────────────────────────────────────────────

    def _format_title(self, title: str) -> str:
        """Retorna título com ícone de estado."""
        icon = "▶" if self._collapsed else "▼"
        return f"{icon}  {title}"
