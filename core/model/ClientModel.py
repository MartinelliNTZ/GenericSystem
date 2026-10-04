# -*- coding: utf-8 -*-
"""
ClientModel — Modelo de cliente
===============================
Representa um cliente, que pode possuir várias fazendas (Farm).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.model.BaseModel import BaseModel
from core.model.FarmModel import Farm


@dataclass
class Client(BaseModel):
    """Representa um cliente, proprietário de várias fazendas."""

    document: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    contact: str = ""
    farms: list[Farm] = field(default_factory=list)

    def add_farm(self, new_farm: Farm) -> None:
        """Adiciona uma fazenda ao cliente."""
        self.farms.append(new_farm)
        self.touch()
