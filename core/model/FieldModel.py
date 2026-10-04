# -*- coding: utf-8 -*-
"""
FieldModel — Modelo de talhão
=============================
Representa um talhão (field) pertencente a uma fazenda.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.model.BaseModel import BaseModel


@dataclass
class Field(BaseModel):
    """Representa um talhão de uma fazenda."""

    code: str = ""
    area: float = 0.0
    crop: str = ""
    soil_type: str = ""
    notes: str = ""
