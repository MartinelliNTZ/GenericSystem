# -*- coding: utf-8 -*-
"""
SubOSModel — Modelo de subordem de serviço
==========================================
Representa uma SubOS (subordem de serviço, ex.: "A", "B", "C", "D"): a
unidade comercial/cliente dentro de uma ordem de serviço (OS). Possui
nome de cliente, nome comercial, CNPJ e uma ou mais fazendas (Farm).

Hierarquia de domínio:
    WorkOrder (OS) → SubOS → Farm (fazenda) → Field (talhão) → Culture
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.model.BaseModel import BaseModel
from core.model.FarmModel import Farm


@dataclass
class SubOS(BaseModel):
    """Representa uma SubOS, proprietária de várias fazendas."""

    code: str = ""              # Identificador da subordem dentro da OS (A, B, C, D)
    document: str = ""          # CNPJ
    commercial_name: str = ""   # Nome comercial
    email: str = ""
    phone: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    contact: str = ""
    farms: list[Farm] = field(default_factory=list)

    def add_farm(self, new_farm: Farm) -> None:
        """Adiciona uma fazenda à SubOS."""
        self.farms.append(new_farm)
        self.touch()

    def area(self) -> float:
        """Retorna a área da SubOS: soma da área de todas as fazendas."""
        return sum(new_farm.area() for new_farm in self.farms)
