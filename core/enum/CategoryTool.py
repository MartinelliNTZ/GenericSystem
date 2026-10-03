# -*- coding: utf-8 -*-
"""
CategoryTool — Enum de categoria de ferramentas
=================================================
Define onde a ferramenta deve ser exibida:
- WORKSPACE: exibida como aba no Workspace (padrão)
- SIDE: exibida em painel lateral
"""

from __future__ import annotations

from enum import Enum


class CategoryTool(str, Enum):
    """Categoria de exibição da ferramenta."""

    CENTRAL = "central"
    SIDE = "side"            # mantido para compatibilidade — tratado como RIGHT_SIDE
    LEFT_SIDE = "left_side"
    RIGHT_SIDE = "right_side"
    BOTH = "both"
    INSTANT = "instant"
