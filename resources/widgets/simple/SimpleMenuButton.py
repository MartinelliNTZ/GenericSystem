# -*- coding: utf-8 -*-
"""
SimpleMenuButton — Botão com menu suspenso (dropdown) configurável
==================================================================
Encapsula um QToolButton com popup de menu, evitando QToolButton/QMenu
brutos espalhados pelos plugins.

O consumidor informa os itens via Dict {valor_interno: texto_exibido} e
recebe a escolha pelo sinal ``item_selected(key)``.

Sinais:
    item_selected(key: str) — emitido quando um item do menu é acionado

Uso:
    from resources.widgets.simple.SimpleMenuButton import SimpleMenuButton

    btn = SimpleMenuButton(
        items={"05_ASA": "05_ASA", "06_CAR": "06_CAR"},
        text="Padronizar",
        parent=self,
    )
    btn.item_selected.connect(self._on_padronizar)
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMenu, QToolButton, QWidget

from resources.styles.AppStyles import AppStyles


class SimpleMenuButton(QToolButton):
    """Botão com popup de menu cujos itens vêm de um Dict configurável."""

    item_selected = Signal(str)

    def __init__(
        self,
        items: Dict[str, str],
        text: str = "Ações",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        theme = AppStyles.current_theme

        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(text)

        self._menu = QMenu(self)
        for key, label in items.items():
            action = self._menu.addAction(str(label))
            action.triggered.connect(
                lambda checked=False, k=key: self.item_selected.emit(k)
            )
        self.setMenu(self._menu)

        self.setStyleSheet(
            f"QToolButton {{"
            f"  background-color: {theme.SURFACE_3};"
            f"  color: {theme.TEXT_MEDIUM};"
            f"  border: 1px solid {theme.BORDER_DEFAULT};"
            f"  border-radius: {theme.BORDER_RADIUS_BUTTON};"
            f"  font-size: {theme.FONT_SIZE_SMALL};"
            f"  padding: 2px 10px;"
            f"}}"
            f"QToolButton:hover {{"
            f"  border-color: {theme.ACCENT};"
            f"  color: {theme.ACCENT_BRIGHT};"
            f"}}"
            f"QToolButton::menu-indicator {{ image: none; }}"
        )
