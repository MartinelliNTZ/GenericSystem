# -*- coding: utf-8 -*-
"""
SimpleGhostButton — Botão ghost (invisível, aparece no hover).
Uso: Adicionar Shapefile, ações sutis.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from resources.styles.AppStyles import AppStyles
from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey


class SimpleGhostButton(QPushButton):
    """
    Botão ghost (invisível, aparece no hover).
    """

    def __init__(self, text: str = "Ação", parent=None):
        super().__init__(text, parent)
        self._logger = LogUtils(tool=ToolKey.UNTRACEABLE.value, class_name="SimpleGhostButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(32)
        self.setStyleSheet(AppStyles.btn_ghost_style())
        self._logger.info(f"SimpleGhostButton criado", code="BTN_CREATED", text=text)
        self._logger.debug(f"Estilo ghost aplicado: background transparent, texto ACCENT_TEXT")
