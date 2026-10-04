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
    total_area: float = 0.0
    registration: str = ""
    fields: list[Field] = field(default_factory=list)

    def add_field(self, new_field: Field) -> None:
        """Adiciona um talhão à fazenda."""
        self.fields.append(new_field)
        self.touch()

    def fields_area(self) -> float:
        """Retorna a soma da área de todos os talhões da fazenda."""
        return sum(talhao.area for talhao in self.fields)
