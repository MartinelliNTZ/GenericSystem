# -*- coding: utf-8 -*-
"""
OsTrackerService — Lógica de leitura do Acompanhamento de OS
============================================================
Lógica pura (sem widgets Qt): lê o banco consolidado (``.BancoDados``) e
converte cada registro de OS em entidades de domínio (``SubOS``).

Uso:
    from plugins.os_tracker.OsTrackerService import OsTrackerService

    orders = OsTrackerService.load_orders(mother)
    sub_os = OsTrackerService.build_sub_os(record)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from core.database.ProjectDatabaseStore import ProjectDatabaseStore
from core.enum.ToolKey import ToolKey
from core.model.SubOSModel import SubOS
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureUtil import ProjectStructureUtil


class OsTrackerService(BaseUtil):
    """Carrega os registros de OS do banco e monta as SubOS de domínio."""

    @classmethod
    def load_orders(
        cls,
        mother: Path,
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> List[Dict[str, Any]]:
        """Lê os registros de OS do banco consolidado (lista vazia se não houver)."""
        data = ProjectDatabaseStore.load_consolidated(mother, tool_key=tool_key)
        orders = data.get("projects", [])
        return orders if isinstance(orders, list) else []

    @classmethod
    def build_sub_os(cls, record: Dict[str, Any]) -> List[SubOS]:
        """Converte as entradas ``sub_os`` de um registro em modelos ``SubOS``."""
        models: List[SubOS] = []
        for entry in record.get("sub_os", []) or []:
            models.append(
                SubOS(
                    code=str(entry.get("sub_os", "")),
                    name=str(entry.get("client", "")),
                    commercial_name=str(entry.get("commercial_name", "")),
                    document=str(entry.get("cnpj", "")),
                )
            )
        return models

    @classmethod
    def record_summary(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Resume cliente/pastas/anos/caminho da OS a partir das suas SubOS."""
        return ProjectStructureUtil.aggregate_record(record)

    @classmethod
    def order_label(cls, record: Dict[str, Any]) -> str:
        """Rótulo exibido no seletor de OS (``OS <numero> — <cliente>``)."""
        number = str(record.get("os", "")).strip()
        client = cls.record_summary(record)["client"].strip()
        return f"OS {number} — {client}" if client else f"OS {number}"
