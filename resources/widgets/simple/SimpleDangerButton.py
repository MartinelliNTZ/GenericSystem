# -*- coding: utf-8 -*-
"""
SimpleDangerButton — Botão de perigo (vermelho).
Uso: Cancelar, ações destrutivas.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from resources.styles.AppStyles import AppStyles


class SimpleDangerButton(QPushButton):
    """
    Botão de perigo com fundo vermelho escuro.
    """

    def __init__(self, text: str = "CANCELAR", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_danger_style())
        self.setMinimumHeight(32)
        self.setMinimumWidth(100)