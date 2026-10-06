# -*- coding: utf-8 -*-
"""
FieldModel — Modelo de talhão
=============================
Representa um talhão (field) pertencente a uma fazenda.
A área do talhão é definida nele. Culturas não alteram essa área.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.model.BaseModel import BaseModel
from core.model.CultureModel import Culture


@dataclass
class Field(BaseModel):
    """Representa um talhão de uma fazenda, com uma ou mais culturas."""

    code: str = ""
    area: float = 0.0
    soil_type: str = ""
    notes: str = ""
    cultures: list[Culture] = field(default_factory=list)

    def add_culture(self, new_culture: Culture) -> None:
        """Adiciona uma cultura ao talhão."""
        self.cultures.append(new_culture)
        self.touch()
