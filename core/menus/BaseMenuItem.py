# -*- coding: utf-8 -*-
"""
BaseMenuItem — Classe base para abas da barra de menus
========================================================
Fornece métodos comuns: add_action, clear, build_menu, title.
Cada aba (FileMenuItem, SystemMenuItem, HelpMenuItem) herda daqui.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QWidget

from resources.styles.AppStyles import AppStyles


class BaseMenuItem(QObject):
    """
    Classe base para uma aba da barra de menus.

    Cada instância representa UMA aba (ex: "Arquivo", "Sistema", "Ajuda")
    e gerencia a lista de ações que aparecem no dropdown.

    Sinais:
        action_triggered — emitido quando o usuário clica em uma ação
                           O argumento é o 'data' associado à ação.
    """

    action_triggered = Signal(str)  # data da ação clicada

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._actions: List[Dict[str, Any]] = []

    # ── API pública ────────────────────────────────────────────────

    @property
    def title(self) -> str:
        """Nome da aba (ex: "Arquivo", "Sistema", "Ajuda")."""
        return self._title

    def add_action(
        self,
        text: str,
        callback: Callable[[], None],
        data: str = "",
        icon: Optional[QIcon] = None,
        enabled: bool = True,
    ) -> None:
        """
        Adiciona uma ação à lista do menu.

        Args:
            text: Texto exibido no menu.
            callback: Função chamada quando a ação é clicada.
            data: Identificador da ação (enviado via action_triggered).
            icon: Ícone opcional.
            enabled: Se False, a ação aparece desabilitada.
        """
        self._actions.append({
            "text": text,
            "callback": callback,
            "data": data or text,
            "icon": icon,
            "enabled": enabled,
        })

    def add_submenu(self, text: str, menu: QMenu) -> None:
        """
        Adiciona um submenu à lista de ações.

        Args:
            text: Texto exibido no menu pai (item que abre o submenu).
            menu: QMenu a ser exibido como submenu.
        """
        self._actions.append({
            "submenu": True,
            "text": text,
            "menu": menu,
        })

    def add_separator(self) -> None:
        """Adiciona um separador visual à lista."""
        self._actions.append({"separator": True})

    def clear(self) -> None:
        """Remove todas as ações."""
        self._actions.clear()

    @staticmethod
    def _menu_style() -> str:
        """Estilo QSS para o QMenu (dropdown) — delegado ao AppStyles."""
        return AppStyles.menu_dropdown_style()

    def build_menu(self) -> QMenu:
        """
        Constrói e retorna um QMenu populado com as ações registradas.

        O QMenu é recriado a cada chamada — chame novamente se as ações
        mudarem dinamicamente (ex: SystemMenuItem com tools).
        O estilo QSS do dropdown é aplicado diretamente no QMenu
        (necessário porque QMenu é um popup independente, não herda
        stylesheet do QMenuBar pai).
        """
        menu = QMenu(self._title, self.parent())
        menu.setStyleSheet(self._menu_style())
        for action_cfg in self._actions:
            # Submenu
            if action_cfg.get("submenu"):
                submenu = action_cfg["menu"]
                menu.addMenu(submenu)
                continue

            # Separador
            if action_cfg.get("separator"):
                menu.addSeparator()
                continue

            # Ação normal
            text = action_cfg["text"]
            callback = action_cfg["callback"]
            data = action_cfg["data"]
            icon = action_cfg.get("icon")
            enabled = action_cfg.get("enabled", True)

            qaction = QAction(text, menu)
            if icon:
                qaction.setIcon(icon)
            qaction.setEnabled(enabled)
            qaction.setData(data)
            qaction.triggered.connect(callback)
            qaction.triggered.connect(lambda checked, d=data: self.action_triggered.emit(d))
            menu.addAction(qaction)

        return menu

    def __len__(self) -> int:
        return len(self._actions)