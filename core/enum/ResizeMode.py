# -*- coding: utf-8 -*-
"""Modos de redimensionamento da janela frameless do Aetheris ToolBox."""

from __future__ import annotations

from enum import Enum


class ResizeMode(Enum):
    """Modos de redimensionamento da janela frameless."""
    NONE = "none"       # Sem resize (comportamento atual)
    NATIVE = "native"   # WM_NCHITTEST via nativeEvent (Windows)
    CURSOR = "cursor"   # Mouse tracking manual (cross-platform)