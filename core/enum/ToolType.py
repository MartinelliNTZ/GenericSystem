# -*- coding: utf-8 -*-
"""
ToolType — Categorias de ferramentas do Aetheris ToolBox
=========================================================
Define os grupos visuais que organizam as ferramentas na toolbar.
"""

from __future__ import annotations

from enum import Enum


class ToolType(str, Enum):
    """Categorias que agrupam as ferramentas na toolbar principal."""

    SYSTEM = "System"
    LAYOUTS = "Layouts"
    FOLDER = "Folder"
    VECTOR = "Vector"
    AGRICULTURE = "Agriculture"
    RASTER = "Raster"
    IMAGE = "Image"
    POINTS = "Points"