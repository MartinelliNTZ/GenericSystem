# -*- coding: utf-8 -*-
"""
SimpleRemoveButton — Botão de remover (hover vermelho).
Uso: remover linhas de tabela.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from resources.styles.AppStyles import AppStyles


class SimpleRemoveButton(QPushButton):
    """
    Botão de remover (hover vermelho).
    """

    def __init__(self, text: str = "Remover", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_remove_style())