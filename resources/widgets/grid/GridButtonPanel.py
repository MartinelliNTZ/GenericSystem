# -*- coding: utf-8 -*-
"""
GridButtonPanel — Grade de botões de ação configurável
======================================================
Widget 100% genérico que exibe N botões de ação em grid, configurados por
dicionário. Cada botão tem texto, tipo de estilo (``primary``, ``secondary``,
``danger``, ``ghost``) e tooltip; o clique é repassado pelo sinal
``clicked(key)``.

Uso:
    from resources.widgets.grid.GridButtonPanel import GridButtonPanel

    panel = GridButtonPanel({
        "columns": 2,
        "buttons": [
            {"key": "zm", "text": "LIMITE ZM", "description": "Abre a pasta ZM"},
            {"key": "docx", "text": "CHANGELOG (WORD)", "type": "primary"},
        ],
    })
    panel.clicked.connect(self._on_shortcut)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QWidget

from resources.widgets.simple.SimplePrimaryButton import SimplePrimaryButton


class GridButtonPanel(QWidget):
    """
    Grade de botões de ação configurados por dicionário.

    Parâmetros do config:
        columns: int (padrão 2) — número de botões por linha
        buttons: list[dict] — cada botão pode ter:
            key: str — identificador estável (chave do sinal ``clicked``)
            text: str — texto exibido
            type: str (opcional) — "primary", "secondary", "danger", "ghost"
            description: str (opcional) — tooltip do botão

    Sinais:
        clicked(key) — emitido com a chave do botão clicado
    """

    clicked = Signal(str)

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._buttons: Dict[str, SimplePrimaryButton] = {}
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(8)
        if config:
            self.build(config)

    # ── Construção ───────────────────────────────────────────────────

    def build(self, config: Dict[str, Any]) -> None:
        """Constrói (ou reconstrói) a grade de botões a partir do config."""
        self._clear()
        columns = max(1, int(config.get("columns", 2)))
        for index, item in enumerate(config.get("buttons", [])):
            key = str(item.get("key", ""))
            button = self._create_button(item)
            row, col = divmod(index, columns)
            self._grid.addWidget(button, row, col)
            self._buttons[key] = button
        for col in range(columns):
            self._grid.setColumnStretch(col, 1)

    def _create_button(self, item: Dict[str, Any]) -> SimplePrimaryButton:
        """Cria um botão estilizado a partir do item de config."""
        key = str(item.get("key", ""))
        button = SimplePrimaryButton(
            item.get("text", key),
            style_key=item.get("type", "secondary"),
            min_width=0,
            shadow_enabled=False,
        )
        description = item.get("description", "")
        if description:
            button.setToolTip(description)
        button.clicked.connect(lambda _=False, k=key: self.clicked.emit(k))
        return button

    def _clear(self) -> None:
        """Remove todos os botões da grade."""
        self._buttons.clear()
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()

    # ── API pública ──────────────────────────────────────────────────

    def button(self, key: str) -> Optional[SimplePrimaryButton]:
        """Retorna o botão da chave informada (ou ``None``)."""
        return self._buttons.get(key)

    def keys(self) -> List[str]:
        """Lista as chaves dos botões."""
        return list(self._buttons)

    def set_enabled(self, key: str, enabled: bool) -> None:
        """Habilita/desabilita um botão."""
        button = self._buttons.get(key)
        if button is not None:
            button.setEnabled(enabled)

    def set_visible(self, key: str, visible: bool) -> None:
        """Mostra/oculta um botão."""
        button = self._buttons.get(key)
        if button is not None:
            button.setVisible(visible)

    def set_text(self, key: str, text: str) -> None:
        """Define o texto exibido em um botão."""
        button = self._buttons.get(key)
        if button is not None:
            button.setText(text)
