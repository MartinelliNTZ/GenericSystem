# -*- coding: utf-8 -*-
"""
CultureModel — Modelo de cultura
================================
Representa a cultura plantada em um talhão (Field).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from core.model.BaseModel import BaseModel


class CultureStatus(str, Enum):
    """Status possíveis de uma cultura."""

    PLANNED = "planejada"
    PLANTED = "plantada"
    HARVESTED = "colhida"


class CultureCycle(str, Enum):
    """Ciclo da cultura dentro do ano agrícola."""

    MAIN = "safra"
    OFF_SEASON = "safrinha"
    WINTER = "inverno"
    PERENNIAL = "perene"


@dataclass
class Culture(BaseModel):
    """Representa a cultura plantada em um talhão."""

    code: str = ""
    variety: str = ""
    cycle: str = CultureCycle.MAIN
    season: str = ""
    status: str = CultureStatus.PLANNED
    area: float = 0.0
    planted_at: Optional[datetime] = None
    harvested_at: Optional[datetime] = None

    def plant(self, area: float = 0.0, by: str = "") -> None:
        """Registra o plantio, fixando a área plantada e a data."""
        self.planted_at = datetime.now()
        self.status = CultureStatus.PLANTED
        if area:
            self.area = area
        self.touch(by)

    def harvest(self, by: str = "") -> None:
        """Marca a cultura como colhida."""
        self.harvested_at = datetime.now()
        self.status = CultureStatus.HARVESTED
        self.touch(by)
