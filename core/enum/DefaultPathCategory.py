# -*- coding: utf-8 -*-
"""
DefaultPathCategory — Categorias de caminhos padrão do sistema
===============================================================
Usado por ExplorerUtils.get_default_path() para evitar strings soltas.

Uso:
    from core.enum.DefaultPathCategory import DefaultPathCategory
    path = ExplorerUtils.get_default_path(DefaultPathCategory.ICO, root)
"""

from __future__ import annotations

from enum import Enum


class DefaultPathCategory(str, Enum):
    """Categorias de diretórios padrão no root_folder do projeto."""

    VECTOR = "vector"
    RASTER = "raster"
    ICO = "ico"
    IMAGE = "image"
    DOCUMENTS = "documents"