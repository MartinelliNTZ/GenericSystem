# -*- coding: utf-8 -*-
"""
ProjectDatabaseService — Lógica do Banco de Dados de Projetos (OS)
=================================================================
Lógica pura (sem widgets Qt):

- ``build_project_record`` monta o registro de uma OS (número, cliente,
  pastas padrão criadas e anos criados).
- ``build_database`` percorre a pasta-mãe e monta o banco consolidado.
- ``ProjectDatabaseWorker`` (QRunnable) executa a varredura em background,
  emitindo progresso por OS (Contrato 20).
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QObject, QRunnable, Signal

from core.enum.ToolKey import ToolKey
from plugins.project_database_manager.ProjectDatabaseStore import ProjectDatabaseStore
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureUtil import ProjectStructureUtil

_TOOL_KEY = ToolKey.PROJECT_DATABASE.value


class ProjectDatabaseService(BaseUtil):
    """Monta os registros do banco de dados a partir do disco."""

    @classmethod
    def build_project_record(
        cls,
        project: Path,
        os_key: str,
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Monta o registro de uma OS (pastas padrão + anos criados)."""
        data = ProjectStructureUtil.collect_created_data(project, tool_key=tool_key)
        return {
            "os": os_key,
            "name": project.name,
            "client": ProjectStructureUtil.extract_client_name(project.name),
            "path": str(project),
            "folders": data["folders"],
            "years": data["years"],
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }

    @classmethod
    def resolve_os_key(cls, project: Path, number_counts: Dict[str, int]) -> str:
        """Define a chave da OS (nome do arquivo em ``.BancoDados``).

        - Número único → apenas o número (ex.: ``068``).
        - Número repetido → número + resto do nome (ex.: ``181_RENNER_A``).
        """
        number = ProjectStructureUtil.extract_os_number(project.name)
        if number_counts.get(number, 0) > 1:
            return ProjectStructureUtil.extract_os_identifier(project.name)
        return number

    @classmethod
    def build_database(
        cls,
        mother: Path,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Percorre a pasta-mãe e monta o banco consolidado."""
        projects = ProjectStructureUtil.discover_projects(mother, tool_key=tool_key)
        total = len(projects)
        numbers = [
            ProjectStructureUtil.extract_os_number(p.name) for p in projects
        ]
        counts = dict(Counter(numbers))
        records = []
        for index, project in enumerate(projects, start=1):
            os_key = cls.resolve_os_key(project, counts)
            records.append(
                cls.build_project_record(project, os_key, tool_key=tool_key)
            )
            if progress_cb is not None:
                progress_cb(index, total)
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "mother_folder": str(mother),
            "db_schema": ProjectDatabaseStore.DB_SCHEMA,
            "total_projects": total,
            "projects": records,
        }


class _ProjectDatabaseSignals(QObject):
    """Sinais do worker do banco de dados."""

    progress = Signal(int, int, int)   # (generation, done, total)
    finished = Signal(int, object)     # (generation, database dict)
    failed = Signal(int, str)          # (generation, mensagem)


class ProjectDatabaseWorker(QRunnable):
    """Varre a pasta-mãe em background (não toca em widgets Qt)."""

    def __init__(self, generation: int, mother: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.mother = mother
        self.signals = _ProjectDatabaseSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """Solicita o cancelamento cooperativo da varredura."""
        self._cancelled = True

    def run(self) -> None:
        """Executa a varredura e emite o resultado."""
        try:
            def _progress(done: int, total: int) -> None:
                self.signals.progress.emit(self.generation, done, total)

            database = ProjectDatabaseService.build_database(
                Path(self.mother), progress_cb=_progress, tool_key=_TOOL_KEY
            )
            if self._cancelled:
                return
            self.signals.finished.emit(self.generation, database)
        except Exception as e:
            ProjectDatabaseService._get_logger(
                _TOOL_KEY, "ProjectDatabaseWorker"
            ).error(
                "Falha na varredura do banco de dados",
                code="PDB_WORKER_ERR",
                error=str(e),
                path=self.mother,
            )
            self.signals.failed.emit(self.generation, str(e))
