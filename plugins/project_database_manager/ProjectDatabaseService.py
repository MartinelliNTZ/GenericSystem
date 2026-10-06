# -*- coding: utf-8 -*-
"""
ProjectDatabaseService — Lógica do Banco de Dados de Projetos (OS)
=================================================================
Lógica pura (sem widgets Qt):

- ``build_os_record`` monta o registro de UMA OS a partir das suas pastas:
  cada pasta em disco vira UMA SubOS (a letra vem do nome da pasta) e as
  pastas/anos pertencem à SubOS; o cliente/nome comercial/CNPJ são associados
  pelo seed via a chave ``sub_os``.
- ``build_database`` percorre a pasta-mãe, agrupa as pastas pelo NÚMERO de OS
  e monta o banco consolidado.
- ``ProjectDatabaseWorker`` (QRunnable) executa a varredura em background,
  emitindo progresso por OS (Contrato 20).
"""

from __future__ import annotations

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
    """Monta os registros do banco de dados a partir do disco.

    Uma OS pode ter VÁRIAS pastas (uma por SubOS). Todas as pastas com o mesmo
    NÚMERO de OS são agrupadas em UM único registro e a SubOS de cada pasta é
    lida do próprio nome da pasta (``ProjectStructureUtil.extract_sub_os``).
    """

    @classmethod
    def build_os_record(
        cls,
        mother: Path,
        os_number: str,
        project_paths: list,
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Monta o registro de UMA OS a partir das suas pastas (uma por SubOS).

        Cada pasta em disco vira UMA SubOS (a letra vem do nome da pasta) e é a
        SubOS que possui ``path``/``folders``/``years`` — pastas pertencem à
        SubOS, não à OS. SubOS sem pasta **não** entram no registro. A
        categorização (cliente/nome comercial/CNPJ) já gravada é preservada.
        """
        previous = cls._load_existing_record(mother, os_number, tool_key=tool_key)
        previous_sub = {
            str(entry.get("sub_os", "")): entry
            for entry in previous.get("sub_os", [])
            if isinstance(entry, dict)
        }

        letters = ProjectStructureUtil.assign_sub_os_letters(project_paths)
        sub_os_entries: list = []
        for project in project_paths:
            data = ProjectStructureUtil.collect_created_data(
                project, tool_key=tool_key
            )
            letter = letters.get(project, "")
            prev = previous_sub.get(letter, {})
            sub_os_entries.append({
                "sub_os": letter,
                "path": str(project),
                "folders": data["folders"],
                "years": data["years"],
                "client": prev.get("client", ""),
                "commercial_name": prev.get("commercial_name", ""),
                "cnpj": prev.get("cnpj", ""),
            })

        sub_os_entries.sort(key=lambda entry: str(entry.get("sub_os", "")))
        return {
            "os": os_number,
            "name": "",
            "sub_os": sub_os_entries,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }

    @classmethod
    def _load_existing_record(
        cls,
        mother: Optional[Path],
        os_number: str,
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Lê o JSON individual de uma OS (``<numero>.json``). ``{}`` se não houver."""
        if mother is None:
            return {}
        return ProjectDatabaseStore.load_project(mother, os_number, tool_key=tool_key)

    @classmethod
    def build_database(
        cls,
        mother: Path,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Percorre a pasta-mãe e monta o banco consolidado (agrupado por OS)."""
        projects = ProjectStructureUtil.discover_projects(mother, tool_key=tool_key)
        groups = ProjectStructureUtil.group_projects_by_os(projects)
        total = len(groups)
        ordered_numbers = sorted(
            groups,
            key=lambda key: (not key.isdigit(), int(key) if key.isdigit() else key),
        )
        records = []
        for index, number in enumerate(ordered_numbers, start=1):
            records.append(
                cls.build_os_record(
                    mother, number, groups[number], tool_key=tool_key
                )
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
