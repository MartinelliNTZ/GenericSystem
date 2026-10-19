# -*- coding: utf-8 -*-
"""
StructureSyncService — Snapshot da estrutura + changelog (background)
=====================================================================
Lógica pura (sem widgets Qt) executada quando o Gerenciador de Estrutura abre:

1. lê a estrutura atual em disco (pastas + arquivos de cada OS, com tamanho
   e data de modificação);
2. carrega o snapshot anterior da fonte oficial (Firestore);
3. classifica as alterações com o componente ISOLADO
   ``ProjectStructureChangeDetector`` (criados/removidos, renomeados, movidos
   e modificados — inclusive renomeação/movimentação de pastas por árvore);
4. grava o changelog em Word dentro de cada OS
   (``11_AGROROBOTICA/OS_<numero>_CHANGELOG.DOCX``);
5. grava as alterações e o novo snapshot no banco.

Na primeira execução (banco vazio) apenas a linha de base é salva — nenhuma
alteração é reportada e nenhum documento Word é criado.

O ``StructureSyncWorker`` (QRunnable) executa tudo em background para não
bloquear a interface (rede + varredura de disco).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import QObject, QRunnable, Signal

from core.enum.ToolKey import ToolKey
from core.firebase.CloudStructureDatabase import CloudStructureDatabase
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureChangeDetector import ProjectStructureChangeDetector
from utils.ProjectStructureChangelog import ProjectStructureChangelog
from utils.ProjectStructureSnapshot import ProjectStructureSnapshot

_TOOL_KEY = ToolKey.PROJECT_STRUCTURE.value


class StructureSyncService(BaseUtil):
    """Compara a estrutura em disco com o snapshot salvo e registra mudanças."""

    _DETAIL_LABELS = (
        ("Pasta renomeada", "folder_renames"),
        ("Pasta movida", "folder_moves"),
        ("Pasta criada", "added_folders"),
        ("Pasta removida", "removed_folders"),
        ("Arquivo renomeado", "renamed_files"),
        ("Arquivo movido", "moved_files"),
        ("Arquivo criado", "added_files"),
        ("Arquivo removido", "removed_files"),
        ("Arquivo modificado", "modified_files"),
    )
    _MAX_SUMMARY_OS = 10
    _MAX_DETAIL_LINES = 120

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
            else ProjectStructureChangeDetector.detect(previous, current)
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

    # ── Relatório (apresentação) ────────────────────────────────────

    @classmethod
    def summary(cls, changes: List[Dict[str, Any]]) -> str:
        """Resumo curto exibido no corpo do modal."""
        total = sum(
            len(change.get(key, []) or [])
            for change in changes
            for _, key in cls._DETAIL_LABELS
        )
        listed = [
            f"• OS {change.get('os', '')} — {change.get('scope', '')}"
            for change in changes[: cls._MAX_SUMMARY_OS]
        ]
        if len(changes) > cls._MAX_SUMMARY_OS:
            listed.append(f"... e mais {len(changes) - cls._MAX_SUMMARY_OS} OS.")
        return (
            f"{len(changes)} OS com alterações ({total} mudança(s)):\n\n"
            + "\n".join(listed)
            + "\n\nO registro foi salvo no banco de dados e no changelog Word "
            "de cada OS."
        )

    @classmethod
    def detail(cls, changes: List[Dict[str, Any]]) -> str:
        """Detalhamento (colapsável) das alterações, por OS."""
        lines: List[str] = []
        for change in changes:
            lines.append(f"OS {change.get('os', '')} — {change.get('scope', '')}")
            for label, key in cls._DETAIL_LABELS:
                for item in change.get(key, []) or []:
                    lines.append(f"  {label}: {cls._item_text(item)}")
            lines.append("")
        if len(lines) > cls._MAX_DETAIL_LINES:
            remaining = len(lines) - cls._MAX_DETAIL_LINES
            lines = lines[: cls._MAX_DETAIL_LINES]
            lines.append(f"... e mais {remaining} linha(s).")
        return "\n".join(lines)

    @classmethod
    def _item_text(cls, item: Any) -> str:
        """Formata um item (nome, renomeado/movido ou modificado com data)."""
        if not isinstance(item, dict):
            return str(item)
        if "old_path" in item and "new_path" in item:
            return f"{item['old_path']} → {item['new_path']}"
        path = str(item.get("path", ""))
        date = str(item.get("modified_at", ""))
        if not date:
            return path
        try:
            date = datetime.fromisoformat(date).strftime("%d/%m/%Y %H:%M:%S")
        except ValueError as e:
            cls._get_logger(_TOOL_KEY, "StructureSyncService").warning(
                "Data de modificação inválida",
                code="SSYNC_DATE_ERR",
                error=str(e),
                value=date,
            )
        return f"{path} ({date})"

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
