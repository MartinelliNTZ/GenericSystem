# -*- coding: utf-8 -*-
"""
ProjectDatabaseService — Lógica do Banco de Dados de Projetos (OS)
=================================================================
Lógica pura (sem widgets Qt) da NOVA regra de negócio:

- O Banco de Dados **não cria mais OS**. Ele consulta a fonte oficial
  (Firebase) as OS já existentes e, para cada SubOS com pasta associada,
  **re-escaneia a pasta em disco** e atualiza ``folders``/``years``.
- Os caminhos são gravados RELATIVOS à pasta-mãe (portável).
- ``ProjectDatabaseWorker`` (QRunnable) executa a varredura em background,
  emitindo progresso por OS (Contrato 20).

A gravação (Firestore + backup JSON) é responsabilidade da CLASSE DE BANCO
(``core.firebase.CloudProjectDatabase``) — esta camada apenas monta o resultado.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, QRunnable, Signal

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureUtil import ProjectStructureUtil

_TOOL_KEY = ToolKey.PROJECT_DATABASE.value


class ProjectDatabaseService(BaseUtil):
    """Atualiza (re-escaneia) as OS JÁ EXISTENTES — nunca cria OS."""

    @classmethod
    def refresh_order(
        cls,
        mother: Path,
        record: Dict[str, Any],
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Re-escaneia as pastas de UMA OS e atualiza ``folders``/``years``.

        O caminho de cada SubOS é normalizado para RELATIVO à pasta-mãe. SubOS
        cuja pasta não existe em disco é reportada em ``missing``. Retorna o
        resumo das mudanças (para o modal de resumo).
        """
        os_number = str(record.get("os", ""))
        summary: Dict[str, Any] = {
            "os": os_number,
            "updated": False,
            "folders_added": 0,
            "years_added": 0,
            "missing": [],
        }
        for entry in record.get("sub_os", []) or []:
            if not isinstance(entry, dict):
                continue
            code = str(entry.get("sub_os", ""))
            rel = str(entry.get("path", "") or "")
            if not rel:
                summary["missing"].append(f"OS {os_number} · SubOS {code or '?'}")
                continue
            folder = ProjectStructureUtil.resolve_path(mother, rel)
            entry["path"] = ProjectStructureUtil.to_relative_path(mother, folder)
            if not folder.exists():
                summary["missing"].append(f"OS {os_number} · SubOS {code or '?'}")
                continue
            data = ProjectStructureUtil.collect_created_data(
                folder, tool_key=tool_key
            )
            before = (
                list(entry.get("folders") or []),
                list(entry.get("years") or []),
            )
            entry["folders"] = data["folders"]
            entry["years"] = data["years"]
            if (data["folders"], data["years"]) != before:
                summary["updated"] = True
            summary["folders_added"] += sum(
                1 for name in data["folders"] if name not in before[0]
            )
            summary["years_added"] += sum(
                1 for year in data["years"] if year not in before[1]
            )
        return summary

    @classmethod
    def refresh_orders(
        cls,
        mother: Path,
        orders: List[Dict[str, Any]],
        progress_cb: Optional[Callable[[int, int], None]] = None,
        tool_key: str = _TOOL_KEY,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Atualiza TODAS as OS existentes e retorna ``(orders, resumo_geral)``."""
        total = max(len(orders), 1)
        summaries: List[Dict[str, Any]] = []
        for index, record in enumerate(orders, start=1):
            summaries.append(cls.refresh_order(mother, record, tool_key=tool_key))
            if progress_cb is not None:
                progress_cb(index, total)
        aggregate: Dict[str, Any] = {
            "total_orders": len(orders),
            "updated_orders": sum(1 for s in summaries if s.get("updated")),
            "folders_added": sum(s["folders_added"] for s in summaries),
            "years_added": sum(s["years_added"] for s in summaries),
            "missing": [item for s in summaries for item in s["missing"]],
        }
        return orders, aggregate


class _ProjectDatabaseSignals(QObject):
    """Sinais do worker do banco de dados."""

    progress = Signal(int, int, int)          # (generation, done, total)
    finished = Signal(int, object, object)    # (generation, orders, summary)
    failed = Signal(int, str)                 # (generation, mensagem)


class ProjectDatabaseWorker(QRunnable):
    """Re-escaneia as OS existentes em background (não toca em widgets Qt)."""

    def __init__(
        self, generation: int, mother: str, orders: List[Dict[str, Any]]
    ) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.mother = mother
        self.orders = copy.deepcopy(orders)
        self.signals = _ProjectDatabaseSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """Solicita o cancelamento cooperativo da varredura."""
        self._cancelled = True

    def run(self) -> None:
        """Executa a atualização e emite o resultado."""
        try:
            def _progress(done: int, total: int) -> None:
                self.signals.progress.emit(self.generation, done, total)

            orders, summary = ProjectDatabaseService.refresh_orders(
                Path(self.mother),
                self.orders,
                progress_cb=_progress,
                tool_key=_TOOL_KEY,
            )
            if self._cancelled:
                return
            self.signals.finished.emit(self.generation, orders, summary)
        except Exception as e:
            ProjectDatabaseService._get_logger(
                _TOOL_KEY, "ProjectDatabaseWorker"
            ).error(
                "Falha na atualização do banco de dados",
                code="PDB_WORKER_ERR",
                error=str(e),
                path=self.mother,
            )
            self.signals.failed.emit(self.generation, str(e))
