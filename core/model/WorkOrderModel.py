# -*- coding: utf-8 -*-
"""
WorkOrderModel — Modelo de ordem de serviço
===========================================
Representa uma ordem de serviço (OS), que pode envolver uma ou mais
SubOS (subordens de serviço: A, B, C, D...). Cada SubOS carrega o
cliente, o nome comercial, o CNPJ e as fazendas.

Hierarquia de domínio:
    WorkOrder (OS) → SubOS → Farm (fazenda) → Field (talhão) → Culture
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from core.model.BaseModel import BaseModel
from core.model.SubOSModel import SubOS


class WorkOrderStatus(str, Enum):
    """Status possíveis de uma ordem de serviço."""

    OPEN = "aberta"
    IN_PROGRESS = "em_andamento"
    DONE = "concluida"
    CANCELED = "cancelada"


class WorkOrderPriority(str, Enum):
    """Prioridades possíveis de uma ordem de serviço."""

    LOW = "baixa"
    NORMAL = "normal"
    HIGH = "alta"
    URGENT = "urgente"


@dataclass
class WorkOrder(BaseModel):
    """Representa uma ordem de serviço com uma ou mais SubOS."""

    number: str = ""
    status: str = WorkOrderStatus.OPEN
    priority: str = WorkOrderPriority.NORMAL
    responsible: str = ""
    opened_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    contract_area: float = 0.0
    sub_os: list[SubOS] = field(default_factory=list)

    def open(self, contract_area: float = 0.0, by: str = "") -> None:
        """Abre a ordem de serviço, fixando a área de contrato na data de abertura."""
        self.opened_at = datetime.now()
        self.contract_area = contract_area
        self.touch(by)

    def add_sub_os(self, new_sub_os: SubOS) -> None:
        """Adiciona uma SubOS à ordem de serviço."""
        self.sub_os.append(new_sub_os)
        self.touch()

    def real_area(self) -> float:
        """Retorna a área real: soma da área de todas as SubOS (baseada nos talhões)."""
        return sum(new_sub_os.area() for new_sub_os in self.sub_os)

    def finish(self, by: str = "") -> None:
        """Marca a ordem de serviço como concluída."""
        self.status = WorkOrderStatus.DONE
        self.completed_at = datetime.now()
        self.touch(by)
