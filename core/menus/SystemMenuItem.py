# -*- coding: utf-8 -*-
"""
SystemMenuItem — Aba "Sistema" da barra de menus
==================================================
Gerencia dinamicamente as ferramentas registradas via ToolRegistry.
Cada tool com menu_category=SYSTEM vira uma ação no dropdown.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from core.config.ToolRegistry import ToolRegistry
from core.enum.MenuCategory import MenuCategory
from core.menus.BaseMenuItem import BaseMenuItem


class SystemMenuItem(BaseMenuItem):
    """
    Menu "Sistema" — lista dinâmica de ferramentas registradas.

    Sinais:
        tool_clicked — emitido quando o usuário clica em uma tool
                       (tool_name)
    """

    tool_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Sistema", parent)
        # Não popula no __init__ — o MenuManager chama refresh_tools()
        # após construir o item, para evitar construir vazio.

    def refresh_tools(self) -> None:
        """
        Lê o ToolRegistry e adiciona ações de ferramentas
        cujo menu_category == SYSTEM.
        Substitui qualquer conteúdo anterior.
        """
        self.clear()
        registry = ToolRegistry()
        tools = registry.get_all()

        added = 0
        for tool in tools:
            if tool.menu_category != MenuCategory.SYSTEM:
                continue

            self.add_action(
                text=tool.title,
                callback=lambda name=tool.name: self._on_tool_clicked(name),
                data=tool.name,
            )
            added += 1

        if added == 0:
            self.add_action(
                text="(vazio)",
                callback=lambda: None,
                data="",
                enabled=False,
            )

    def _on_tool_clicked(self, tool_name: str):
        """Propaga o clique na ferramenta."""
        self.tool_clicked.emit(tool_name)