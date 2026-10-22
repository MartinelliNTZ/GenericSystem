# -*- coding: utf-8 -*-
"""
WorkOrderModel — Modelo de ordem de serviço
===========================================
Representa uma ordem de serviço (OS). A OS é identificada por TEXTO (``number``)
e PODE CONTER LETRA (ex.: ``169A``, ``181B``): a letra é o que diferencia as OS
de um mesmo projeto. O cliente, o nome comercial e o CNPJ ficam na própria OS.

Hierarquia de domínio:
    WorkOrder (OS) → Farm (fazenda) → Field (talhão) → Culture
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from core.model.BaseModel import BaseModel


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
    """Representa uma ordem de serviço (a OS é texto e pode conter letra)."""

    number: str = ""
    status: str = WorkOrderStatus.OPEN
    priority: str = WorkOrderPriority.NORMAL
    responsible: str = ""
    opened_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    contract_area: float = 0.0
    document: str = ""          # CNPJ
    commercial_name: str = ""   # Nome comercial

    def open(self, contract_area: float = 0.0, by: str = "") -> None:
        """Abre a ordem de serviço, fixando a área de contrato na data de abertura."""
        self.opened_at = datetime.now()
        self.contract_area = contract_area
        self.touch(by)

    def finish(self, by: str = "") -> None:
        """Marca a ordem de serviço como concluída."""
        self.status = WorkOrderStatus.DONE
        self.completed_at = datetime.now()
        self.touch(by)
