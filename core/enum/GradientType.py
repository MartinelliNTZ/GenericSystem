# -*- coding: utf-8 -*-
"""
GradientType — Tipos de gradiente suportados pelo sistema de temas
===================================================================
Cada tema pode definir um tipo de gradiente diferente para seus
elementos visuais (botões, progress bars, etc.).

Suporta:
    LINEAR  — Gradiente linear entre dois pontos (padrão, compatibilidade total)
    RADIAL  — Gradiente radial a partir de um ponto central
    CONICAL — Gradiente cônico em torno de um ponto central (Qt >= 5.12)

Uso nos temas:
    from core.enum.GradientType import GradientType
    GRADIENT_ACCENT_TYPE = GradientType.RADIAL

Uso no QSS:
    LINEAR  → qlineargradient(x1:,y1:,x2:,y2:, stop:...)
    RADIAL  → qradialgradient(cx:,cy:,radius:, fx:,fy:, stop:...)
    CONICAL → qconicalgradient(cx:,cy:,angle:, stop:...)
"""

from __future__ import annotations

from enum import Enum


class GradientType(Enum):
    """
    Tipos de gradiente disponíveis para uso nos temas.
    """

    LINEAR = "linear"
    """Gradiente linear entre dois pontos (x1,y1 → x2,y2). Padrão do sistema."""

    RADIAL = "radial"
    """Gradiente radial partindo de um ponto focal (fx,fy) com raio definido."""

    CONICAL = "conical"
    """Gradiente cônico em torno de um ponto central (cx,cy) com ângulo inicial."""