# -*- coding: utf-8 -*-
"""
BaseModel — Modelo base do sistema
==================================
Pai de todos os models do Aetheris ToolBox. Reúne os dados de sistema
comuns a qualquer entidade: identificação, nome e auditoria de
criação/modificação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


def _to_serializable(value: Any) -> Any:
    """Converte valores do model para tipos serializáveis."""
    if isinstance(value, BaseModel):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_to_serializable(item) for item in value]
    return value


@dataclass
class BaseModel:
    """Modelo base com os dados de sistema compartilhados por todos os models."""

    id: Optional[str] = None
    name: str = ""
    description: str = ""
    active: bool = True

    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: str = ""

    def touch(self, by: str = "") -> None:
        """Marca o model como modificado, atualizando a auditoria."""
        self.updated_at = datetime.now()
        if by:
            self.updated_by = by

    def to_dict(self) -> dict:
        """Serializa o model, incluindo models aninhados, para dicionário."""
        return {key: _to_serializable(value) for key, value in self.__dict__.items()}

    def __str__(self) -> str:
        return self.name or self.__class__.__name__
