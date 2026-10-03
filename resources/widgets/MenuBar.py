# -*- coding: utf-8 -*-
"""
MenuBar — Container da barra de menus do Aetheris ToolBox
===========================================================
Apenas exibe as abas (QMenu) construídas pelos MenuItems.
Cada aba é um BaseMenuItem que sabe construir seu próprio QMenu.

Não contém lógica de negócio — apenas recebe items prontos e os
adiciona ao QMenuBar.

Suporta widget à direita via add_widget_right().
"""

from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QMenuBar, QWidget

from core.menus.BaseMenuItem import BaseMenuItem
from resources.styles.AppStyles import AppStyles


class MenuBar(QWidget):
    """
    Container da barra de menus com suporte a widget à direita.

    Layout: [QMenuBar] [stretch] [right_widgets]

    Uso:
        menubar = MenuBar()
        menubar.add_menu_item(item_arquivo)
        menubar.add_menu_item(item_sistema)
        menubar.add_menu_item(item_ajuda)
        menubar.add_widget_right(monitor_widget)

    Sinais:
        action_triggered — repassa o sinal do BaseMenuItem que foi clicado
                           (data da ação)
    """

    action_triggered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("app_menu_bar_container")
        self.setStyleSheet(AppStyles.menu_bar_container_style())
        self._items: Dict[str, BaseMenuItem] = {}

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._menu_bar = QMenuBar()
        self._menu_bar.setObjectName("app_menu_bar")
        self._menu_bar.setStyleSheet(AppStyles.menu_bar_style())
        self._layout.addWidget(self._menu_bar)
        self._layout.addStretch(1)

        self._right_layout = QHBoxLayout()
        self._right_layout.setContentsMargins(0, 0, 8, 0)
        self._right_layout.setSpacing(4)
        self._layout.addLayout(self._right_layout)

        self.setFixedHeight(30)

    # ── API pública ────────────────────────────────────────────────

    def add_menu_item(self, item: BaseMenuItem) -> None:
        """
        Adiciona uma aba à barra de menus.

        O item já deve estar configurado com suas ações.
        O MenuBar cria o QMenu via item.build_menu() e o adiciona.
        """
        name = item.title
        self._items[name] = item

        menu = item.build_menu()
        self._menu_bar.addMenu(menu)

        # Repassa o sinal de clique do item para o container
        item.action_triggered.connect(self._on_item_triggered)

    def remove_menu_item(self, title: str) -> bool:
        """Remove uma aba pelo título. Retorna True se removeu."""
        if title not in self._items:
            return False

        # Remove o QMenu correspondente
        for action in self._menu_bar.actions():
            if action.text() == title and action.menu():
                self._menu_bar.removeAction(action)
                break

        del self._items[title]
        return True

    def get_menu_item(self, title: str) -> BaseMenuItem:
        """Retorna o BaseMenuItem pelo título."""
        return self._items.get(title)

    def refresh_all(self) -> None:
        """
        Reconstrói todos os QMenus a partir dos items atuais.
        Útil quando um item muda dinamicamente (ex: SystemMenuItem).
        """
        # Remove todos os menus atuais
        for action in self._menu_bar.actions():
            self._menu_bar.removeAction(action)

        # Reconstrói
        for name, item in self._items.items():
            menu = item.build_menu()
            self._menu_bar.addMenu(menu)

    def add_widget_right(self, widget: QWidget) -> None:
        """Adiciona um widget alinhado à direita da barra de menus."""
        self._right_layout.addWidget(widget)

    # ── Internos ───────────────────────────────────────────────────

    def _on_item_triggered(self, data: str):
        """Repassa o sinal do item para action_triggered do container."""
        self.action_triggered.emit(data)