# -*- coding: utf-8 -*-
"""
HelpMenuItem — Aba "Ajuda" da barra de menus
==============================================
Itens: Sobre
Herda de BaseMenuItem e expõe sinal sobre_clicked.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from core.menus.BaseMenuItem import BaseMenuItem


class HelpMenuItem(BaseMenuItem):
    """
    Menu "Ajuda" — ações de ajuda/sobre.

    Sinais:
        sobre_clicked — emitido quando o usuário clica em "Sobre"
    """

    sobre_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Ajuda", parent)
        self._build_actions()

    def _build_actions(self):
        """Constrói a lista de ações do menu Ajuda."""
        self.add_action(
            text="Sobre",
            callback=self._on_sobre,
            data="sobre",
        )

    def _on_sobre(self):
        """Propaga o clique em Sobre."""
        self.sobre_clicked.emit()