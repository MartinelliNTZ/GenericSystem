# -*- coding: utf-8 -*-
"""
FarmModel — Modelo de fazenda
=============================
Representa uma fazenda, que pode conter vários talhões (Field).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.model.BaseModel import BaseModel
from core.model.FieldModel import Field


@dataclass
class Farm(BaseModel):
    """Representa uma fazenda, proprietária de vários talhões."""

    city: str = ""
    state: str = ""
    country: str = ""
    registration: str = ""
    fields: list[Field] = field(default_factory=list)

    def add_field(self, new_field: Field) -> None:
        """Adiciona um talhão à fazenda."""
        self.fields.append(new_field)
        self.touch()

    def area(self) -> float:
        """Retorna a área da fazenda: soma da área de todos os talhões."""
        return sum(new_field.area for new_field in self.fields)
