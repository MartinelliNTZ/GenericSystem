# -*- coding: utf-8 -*-
"""
BasePage — Classe base para páginas com layout padrão
======================================================
Fornece um QWidget com QVBoxLayout (margins 18, 10, 18, 10 e spacing 8)
que serve como base para PluginPage e demais páginas do sistema.

Uso:
    class MinhaPage(BasePage):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.main_layout.addWidget(QLabel("conteúdo"))
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout


class BasePage(QWidget):
    """
    Container base com QVBoxLayout padronizado.

    Atributos:
        main_layout : QVBoxLayout — layout principal para adicionar widgets filhos.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 10, 18, 10)
        self.main_layout.setSpacing(8)

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        """Atalho para adicionar widget ao main_layout."""
        self.main_layout.addWidget(widget, stretch)

    def add_widgets(self, *widgets: QWidget, stretch: int = 0) -> None:
        """
        Adiciona múltiplos widgets ao main_layout de uma só vez.

        Args:
            *widgets: Widgets a serem adicionados (ordem sequencial)
            stretch: Fator de esticamento aplicado a todos
        """
        for widget in widgets:
            self.main_layout.addWidget(widget, stretch)