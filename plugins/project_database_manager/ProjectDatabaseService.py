# -*- coding: utf-8 -*-
"""
ProjectDatabaseService — Lógica do Banco de Dados de Projetos (OS)
=================================================================
Lógica pura (sem widgets Qt):

- ``build_os_record`` monta o registro de UMA OS, agrupando todas as suas
  pastas (uma por SubOS; o cliente/nome comercial/CNPJ são associados pelo
  seed via a chave ``sub_os``).
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
        """Monta o registro de UMA OS, agrupando todas as suas pastas (SubOS).

        Preserva a categorização (cliente/nome comercial/CNPJ) já gravada em
        disco para cada SubOS, para que uma nova varredura não a apague.
        """
        previous = cls._load_existing_record(mother, os_number, tool_key=tool_key)
        previous_sub = {
            str(entry.get("sub_os", "")): entry
            for entry in previous.get("sub_os", [])
            if isinstance(entry, dict)
        }

        all_folders: list = []
        all_years: list = []
        sub_os_entries: list = []
        used_letters: set = set()

        letters = ProjectStructureUtil.assign_sub_os_letters(project_paths)
        for project in project_paths:
            data = ProjectStructureUtil.collect_created_data(
                project, tool_key=tool_key
            )
            cls._extend_unique(all_folders, data["folders"])
            cls._extend_unique(all_years, data["years"])
            letter = letters.get(project, "")
            used_letters.add(letter)
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

        # Mantém SubOS que existem no banco mas não têm pasta criada.
        for letter, prev in previous_sub.items():
            if letter not in used_letters:
                sub_os_entries.append(prev)

        sub_os_entries.sort(key=lambda entry: str(entry.get("sub_os", "")))
        ordered_folders = [
            name for name in ProjectStructureUtil.DEFAULT_PROJECT_FOLDERS
            if name in all_folders
        ]
        ordered_paths = [
            str(path) for path in
            sorted(project_paths, key=lambda path: path.name.lower())
        ]
        return {
            "os": os_number,
            "name": "",
            "client": "",
            "path": ordered_paths[0] if ordered_paths else "",
            "paths": ordered_paths,
            "folders": ordered_folders,
            "years": all_years,
            "sub_os": sub_os_entries,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }

    @staticmethod
    def _extend_unique(target: list, values) -> None:
        """Adiciona a ``target`` os itens de ``values`` que ainda não existem."""
        for value in values:
            if value not in target:
                target.append(value)

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
