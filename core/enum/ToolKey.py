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
    CLASSIFIER = "Classifier"
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
    MRK_SUBSTITUTOR = "MrkSubstitutor"
    LAS_BLACK_FILTER = "LasBlackFilter"
    LAS_CHECK = "LasCheck"
    STATISTICS = "Statistics"
    POINT_BOUNDARY = "PointBoundary"
    IDW_INTERPOLATOR = "IdwInterpolator"
    LAS_TILER = "LasTiler"
    SYSTEM_MONITOR = "SystemMonitor"
    LAS_VECTOR_CONVERTER = "LasVectorConverter"
    LAS_REPROJECTION = "LasReprojection"
    FOOTBALL_FETCH = "FootballFetch"
    WEATHER_FETCH = "WeatherFetch"
    SCAN_ANGLE_FILTER = "ScanAngleFilter"
    MAP_VIEWER = "MapViewer"

    CUT_BY_TRAJECTORY = "CutByTrajectory"  # Ainda não implementado
    IBGE_HNOR_ORGANIZER = "IBGEHnorOrganizer"  # Ainda não implementado
    IBGE_PPP_CONVERTER = "IBGEPPPConverter"  # Ainda não implementado
    JOHN_DEERE_ORGANIZER = "JohnDeereOrganizer"  # Ainda não implementado
    LAS_LAZ_CONVERT = "LasLazConvert"  # Ainda não implementado
    LAS_MERGE = "LasMerge"  # Ainda não implementado
    PYTHON_LIBRARY_MANAGER = "PythonLibraryManager"  # Ainda não implementado
    RASTER_CHECK = "RasterCheck"  # Ainda não implementado
    RASTER_FREE = "RasterFree"  # Ainda não implementado
    RASTER_FREE_2 = "RasterFree (2)"  # Ainda não implementado
    RASTER_MERGE = "RasterMerge"  # Ainda não implementado
    RASTER_MERGE_2 = "RasterMerge2"  # Ainda não implementado
    RASTER_TO_LAS = "RasterToLas"  # Ainda não implementado
    RASTER_TO_LAS_2 = "RasterToLas2"  # Ainda não implementado
    RASTER_VISION_CLASSIFIER = "RasterVisionClassifier"  # Ainda não implementado

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