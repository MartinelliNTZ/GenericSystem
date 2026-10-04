# -*- coding: utf-8 -*-
"""
WorkOrderModel — Modelo de ordem de serviço
===========================================
Representa uma ordem de serviço, que pode envolver um ou mais clientes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from core.model.BaseModel import BaseModel
from core.model.ClientModel import Client


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
    """Representa uma ordem de serviço com um ou mais clientes."""

    number: str = ""
    status: str = WorkOrderStatus.OPEN
    priority: str = WorkOrderPriority.NORMAL
    responsible: str = ""
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    clients: list[Client] = field(default_factory=list)

    def add_client(self, new_client: Client) -> None:
        """Adiciona um cliente à ordem de serviço."""
        self.clients.append(new_client)
        self.touch()

    def finish(self, by: str = "") -> None:
        """Marca a ordem de serviço como concluída."""
        self.status = WorkOrderStatus.DONE
        self.completed_at = datetime.now()
        self.touch(by)
