# -*- coding: utf-8 -*-
"""
MenuCategory — Enum de categorias de menu para ferramentas
=============================================================
Define em qual menu suspenso a ferramenta deve aparecer.
Quando None (ou não definido), a ferramenta não vai para o menu.
"""

from __future__ import annotations

from enum import Enum


class MenuCategory(str, Enum):
    """Categorias de menu para exibição de ferramentas."""

    FILE = "Arquivo"
    SYSTEM = "Sistema"
    HELP = "Ajuda"

    @classmethod
    def display_names(cls) -> list[str]:
        """Retorna lista com os nomes de todos os menus."""
        return [item.value for item in cls]