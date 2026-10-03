# -*- coding: utf-8 -*-
"""
IconManager — Gerenciador central de ícones do Aetheris ToolBox
=================================================================
Fornece QIcons a partir de nomes de arquivo na pasta resources/icons/.
Como atualmente só existe Aetheris.ico, todas as ferramentas usam
esse mesmo ícone por enquanto.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtGui import QIcon


class IconManager:
    """
    Gerenciador central de ícones.

    Cada ferramenta tem seu ícone em resources/icons/ com o mesmo
    nome do ToolKey (ex: LogViewer.ico, Console.ico).
    Se o arquivo não existir, usa o ícone default.

    Uso:
        icon = IconManager.get_tool_icon("LogViewer")
        icon = IconManager.get("LogViewer.ico")
    """

    BASE_PATH = os.path.join(os.path.dirname(__file__), "icons")

    # ── Ícone default (fallback) ──────────────────────────────────────
    DEFAULT = "Aetheris2.ico"

    # ── Métodos ───────────────────────────────────────────────────────

    @classmethod
    def get_tool_icon(cls, tool_name: str) -> QIcon:
        """
        Retorna o QIcon de uma ferramenta pelo seu nome (ToolKey).
        O nome do arquivo é {tool_name}.ico em resources/icons/.
        Ex: get_tool_icon("LogViewer") → resources/icons/LogViewer.ico

        Se o arquivo não existir, retorna o ícone default.
        """
        filename = f"{tool_name}.ico"
        return cls.get(filename)

    @classmethod
    def get(cls, name: str) -> QIcon:
        """
        Retorna um QIcon a partir do nome do arquivo de ícone.
        Se o arquivo não existir, retorna o ícone default (nunca quebra).
        """
        path = cls.path(name)
        return QIcon(path)

    @classmethod
    def path(cls, name: str) -> str:
        """Retorna o caminho completo do arquivo de ícone."""
        full = os.path.join(cls.BASE_PATH, name)
        if os.path.isfile(full):
            return full
        # Fallback para o ícone default
        fallback = os.path.join(cls.BASE_PATH, cls.DEFAULT)
        return fallback if os.path.isfile(fallback) else ""

    @classmethod
    def default_icon(cls) -> QIcon:
        """Retorna o ícone default do sistema."""
        return cls.get(cls.DEFAULT)
