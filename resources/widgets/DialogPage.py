# -*- coding: utf-8 -*-
"""
DialogPage — Página de conteúdo para diálogos com abas
=========================================================
Widget que representa uma página de conteúdo dentro de um diálogo com abas.
Herda de BasePage — nunca deve ser instanciado manualmente, é o container
que exibe o conteúdo de cada aba quando selecionada.

A dialog que usa este widget deve gerenciar as HorizontalTab por conta
própria, empilhando DialogPages e mostrando/escondendo conforme a aba clicada.

Uso (dentro de uma dialog):
    self._pages: list[DialogPage] = []

    def _add_tab(self, title: str, closable: bool = True) -> DialogPage:
        tab = HorizontalTab(title, closable=closable, parent=self)
        self.tab_layout.addWidget(tab)

        page = DialogPage(self)
        self.stack_layout.addWidget(page)
        page.setVisible(False)

        self._tabs.append(tab)
        self._pages.append(page)
        return page
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from resources.widgets.BasePage import BasePage


class DialogPage(BasePage):
    """
    Página de conteúdo de um diálogo com abas.
    Herda de BasePage para manter o layout padronizado do sistema.

    Attributes:
        main_layout : QVBoxLayout — layout herdado de BasePage.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)