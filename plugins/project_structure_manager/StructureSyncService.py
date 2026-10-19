# -*- coding: utf-8 -*-
"""
StructureSyncService — Snapshot da estrutura + changelog (background)
=====================================================================
Lógica pura (sem widgets Qt) executada quando o Gerenciador de Estrutura abre:

1. lê a estrutura atual em disco (pastas + arquivos de cada OS);
2. carrega o snapshot anterior da fonte oficial (Firestore);
3. compara e monta a lista de alterações (pastas/arquivos criados/removidos);
4. grava o changelog em Word dentro de cada OS
   (``11_AGROROBOTICA/OS_<numero>_CHANGELOG.DOCX``);
5. grava as alterações e o novo snapshot no banco.

Na primeira execução (banco vazio) apenas a linha de base é salva — nenhuma
alteração é reportada e nenhum documento Word é criado.

O ``StructureSyncWorker`` (QRunnable) executa tudo em background para não
bloquear a interface (rede + varredura de disco).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QObject, QRunnable, Signal

from core.enum.ToolKey import ToolKey
from core.firebase.CloudStructureDatabase import CloudStructureDatabase
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureChangelog import ProjectStructureChangelog
from utils.ProjectStructureSnapshot import ProjectStructureSnapshot

_TOOL_KEY = ToolKey.PROJECT_STRUCTURE.value


class StructureSyncService(BaseUtil):
    """Compara a estrutura em disco com o snapshot salvo e registra mudanças."""

    @classmethod
    def sync(
        cls,
        mother: Path,
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Executa a conferência completa e persiste o resultado."""
        logger = cls._get_logger(tool_key, "StructureSyncService")
        current = ProjectStructureSnapshot.scan(mother, tool_key=tool_key)
        saved_docs = CloudStructureDatabase.load_snapshots(tool_key=tool_key)
        previous = cls._previous_by_scope(saved_docs)
        baseline = not previous
        changes = (
            [] if baseline
            else ProjectStructureSnapshot.diff(previous, current)
        )

        written = cls._write_changelogs(mother, changes, current, tool_key)
        changes_saved = (
            CloudStructureDatabase.save_changes(changes, tool_key=tool_key)
            if changes else 0
        )
        snapshots_saved = CloudStructureDatabase.save_snapshots(
            current,
            existing_doc_ids=list(saved_docs.keys()),
            previous=previous,
            tool_key=tool_key,
        )
        logger.info(
            "Conferência da estrutura concluída",
            code="SSYNC_DONE",
            baseline=baseline,
            scopes=len(current),
            changed_scopes=len(changes),
            changelogs=written,
            changes_saved=changes_saved,
            snapshots_saved=snapshots_saved,
        )
        return {
            "baseline": baseline,
            "scopes": len(current),
            "changes": changes,
            "changelogs_written": written,
            "changes_saved": changes_saved,
            "snapshots_saved": snapshots_saved,
        }

    @staticmethod
    def _previous_by_scope(
        documents: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Converte ``{doc_id: dados}`` em ``{scope: dados}``."""
        previous: Dict[str, Dict[str, Any]] = {}
        for doc_id, data in documents.items():
            if not isinstance(data, dict):
                continue
            previous[str(data.get("scope") or doc_id)] = data
        return previous

    @classmethod
    def _write_changelogs(
        cls,
        mother: Path,
        changes: List[Dict[str, Any]],
        current: Dict[str, Dict[str, Any]],
        tool_key: str,
    ) -> int:
        """Grava o Word de cada OS alterada e registra a pasta do changelog."""
        written = 0
        for change in changes:
            scope = str(change.get("scope", ""))
            folder = Path(mother) / scope
            if not scope or not folder.is_dir():
                continue
            result = ProjectStructureChangelog.append_changes(
                folder, change, tool_key=tool_key
            )
            if not result["written"]:
                continue
            written += 1
            if result["created_folder"]:
                cls._register_changelog_folder(current, scope)
        return written

    @staticmethod
    def _register_changelog_folder(
        current: Dict[str, Dict[str, Any]], scope: str
    ) -> None:
        """Inclui a pasta criada pelo changelog no snapshot atual.

        Evita que a pasta ``11_AGROROBOTICA`` (criada junto com o documento)
        seja reportada como "pasta adicionada" na próxima execução.
        """
        entry = current.get(scope)
        if entry is None:
            return
        folders = entry.setdefault("folders", [])
        if ProjectStructureChangelog.FOLDER_NAME not in folders:
            folders.append(ProjectStructureChangelog.FOLDER_NAME)
            folders.sort(key=str.lower)


class _StructureSyncSignals(QObject):
    """Sinais do worker de conferência da estrutura."""

    finished = Signal(int, object)   # (generation, resultado)
    failed = Signal(int, str)        # (generation, mensagem)


class StructureSyncWorker(QRunnable):
    """Executa a conferência da estrutura em background (sem widgets)."""

    def __init__(
        self,
        generation: int,
        mother: str,
        tool_key: str = _TOOL_KEY,
    ) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.mother = mother
        self.tool_key = tool_key
        self.signals = _StructureSyncSignals()

    def run(self) -> None:
        """Executa a conferência e emite o resultado."""
        try:
            result = StructureSyncService.sync(
                Path(self.mother), tool_key=self.tool_key
            )
            self.signals.finished.emit(self.generation, result)
        except Exception as e:
            StructureSyncService._get_logger(
                self.tool_key, "StructureSyncWorker"
            ).error(
                "Falha na conferência da estrutura",
                code="SSYNC_WORKER_ERR",
                error=str(e),
                path=self.mother,
            )
            self.signals.failed.emit(self.generation, str(e))
