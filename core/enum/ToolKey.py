# -*- coding: utf-8 -*-
"""
ToolKey — Enum de chaves das ferramentas do sistema
=====================================================
Centraliza os nomes das ferramentas em um Enum para evitar
strings soltas no código e facilitar manutenção.

"""

from __future__ import annotations

from enum import Enum


class ToolKey(str, Enum):
    """Enum com as chaves de todas as ferramentas registradas."""

    HOME = "Home"
    CONSOLE = "Console"
    LOGVIEWER = "LogViewer"
    HOTKEY_PLUGIN = "HotkeyPlugin"
    PREFERENCES = "Preferences"
    RENAMER = "Renamer"
    CONFIGURATION = "Configuration"
    SYSTEM = "System"
    SAVE_PROJECT = "SaveProject"
    FILE_MANAGER = "FileManager"
    UNTRACEABLE = "Untraceable"
    ICO_CONVERTER = "IcoConverter"
    IMAGE_CONVERTER = "ImageConverter"
    DOCLING = "Docling"
    STATISTICS = "Statistics"
    SYSTEM_MONITOR = "SystemMonitor"
    FOOTBALL_FETCH = "FootballFetch"
    WEATHER_FETCH = "WeatherFetch"
    MAP_VIEWER = "MapViewer"
    PROJECT_STRUCTURE = "ProjectStructure"
    PROJECT_DATABASE = "ProjectDatabase"
    OS_TRACKER = "OsTracker"
    FIREBASE = "Firebase"

    PYTHON_LIBRARY_MANAGER = "PythonLibraryManager"  # Ainda não implementado

    # ── Método utilitário ──────────────────────────────────────────────

    @classmethod
    def display_names(cls) -> list[str]:
        """Retorna lista com os nomes de todas as ferramentas."""
        return [item.value for item in cls]

    @classmethod
    def from_name(cls, name: str) -> "ToolKey":
        """
        Retorna o enum correspondente ao nome, ou levanta ValueError.

        Exemplo:
            ToolKey.from_name("Console")  # ToolKey.CONSOLE
        """
        try:
            return cls(name)
        except ValueError:
            raise ValueError(
                f"'{name}' não é uma ToolKey válida. "
                f"Opções: {', '.join(cls.display_names())}"
            )