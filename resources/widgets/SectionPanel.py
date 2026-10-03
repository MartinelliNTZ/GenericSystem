# -*- coding: utf-8 -*-
"""
SectionPanel — Container leve com QVBoxLayout de margem zero.
Uso: agrupar widgets que precisam ser mostrados/escondidos juntos,
     como seções alternáveis por modo/guia.

Fornece ``section_layout`` (QVBoxLayout) para adicionar filhos.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout


class SectionPanel(QWidget):
    """
    Container com QVBoxLayout de margens zero e spacing configurável.

    Uso:
        panel = SectionPanel(spacing=6)
        panel.section_layout.addWidget(QLabel("conteúdo"))
        parent_layout.addWidget(panel)
        panel.setVisible(True)  # mostrar/esconder o bloco inteiro
    """

    def __init__(self, object_name: str = "", spacing: int = 0, parent=None):
        super().__init__(parent)
        if object_name:
            self.setObjectName(object_name)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(spacing)

    @property
    def section_layout(self) -> QVBoxLayout:
        """Layout interno para adicionar widgets filhos."""
        return self._layout