# -*- coding: utf-8 -*-
"""AboutDialog — Dialog simples com informações do sistema, estilizado com Palette."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from core.dialogs.BaseDialog import BaseDialog
from resources.styles.AppStyles import AppStyles


class AboutDialog(BaseDialog):
    """Dialog simples exibindo informações do Aetheris ToolBox."""

    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            title="Sobre o Aetheris ToolBox",
            object_name="about_dialog",
            fixed_size=(380, 240),
            modal=True,
        )
        self.setStyleSheet(AppStyles.about_dialog_stylesheet())

    def _build_ui(self):
        self._add_title(
            "Aetheris ToolBox", object_name="about_title"
        )
        self._add_centered_text(
            "Versão 1.0.0", object_name="about_version"
        )
        self.main_layout.addSpacing(8)
        self._add_centered_text(
            "Ferramentas para automação de processos\n"
            "de classificação raster e análise de dados.",
            object_name="about_desc",
            word_wrap=True,
        )
        self.main_layout.addSpacing(4)
        self._add_centered_text(
            "© 2026 Aetheris ToolBox", object_name="about_copyright"
        )

        self.main_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(80)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(AppStyles.btn_secondary_style())
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)