# -*- coding: utf-8 -*-
"""
ProjectStructureSnapshot — Snapshot e diff da estrutura de pastas das OS
=======================================================================
Lógica pura (sem widgets e sem banco) usada pelo Gerenciador de Estrutura:

- ``scan`` percorre a pasta-mãe e devolve, para cada pasta de OS, a lista
  COMPLETA (recursiva) de pastas e arquivos, com caminhos RELATIVOS à pasta
  da OS e separador ``/`` (portável entre computadores).
- ``diff`` compara o snapshot salvo no banco com o snapshot atual e devolve
  apenas as OS que mudaram (pastas/arquivos criados e removidos).

O changelog gerado pela ferramenta (``11_AGROROBOTICA/
OS_<numero>_CHANGELOG.DOCX``) e os temporários do Office (``~$*``) são
ignorados — assim a própria gravação do documento não vira "alteração" na
próxima execução.

Uso:
    from utils.ProjectStructureSnapshot import ProjectStructureSnapshot

    snapshot = ProjectStructureSnapshot.scan(mother)
    changes = ProjectStructureSnapshot.diff(previous, snapshot)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureChangelog import ProjectStructureChangelog
from utils.ProjectStructureUtil import ProjectStructureUtil


class ProjectStructureSnapshot(BaseUtil):
    """Lê a estrutura das OS em disco e compara snapshots."""

    _CHANGE_KEYS = (
        "added_folders",
        "removed_folders",
        "added_files",
        "removed_files",
    )

    # ── Leitura ─────────────────────────────────────────────────────

    @classmethod
    def scan(
        cls,
        mother: str | Path,
        tool_key: str = ToolKey.PROJECT_STRUCTURE.value,
    ) -> Dict[str, Dict[str, Any]]:
        """Retorna ``{nome_da_pasta_da_OS: snapshot}`` para a pasta-mãe."""
        logger = cls._get_logger(tool_key, "ProjectStructureSnapshot")
        projects = ProjectStructureUtil.discover_projects(
            Path(mother), tool_key=tool_key
        )
        snapshot: Dict[str, Dict[str, Any]] = {}
        for project in projects:
            entry = cls._new_entry(project)
            cls._walk(project, entry, logger)
            snapshot[project.name] = entry
        return snapshot

    @classmethod
    def _new_entry(cls, project: Path) -> Dict[str, Any]:
        """Cria o registro vazio de uma pasta de OS."""
        number = ProjectStructureUtil.normalize_os(
            ProjectStructureUtil.extract_os_number(project.name)
        )
        return {
            "scope": project.name,
            "os": number,
            "folders": [],
            "files": [],
        }

    @classmethod
    def _walk(
        cls,
        root: Path,
        entry: Dict[str, Any],
        logger: Any,
    ) -> None:
        """Percorre recursivamente a pasta da OS preenchendo ``entry``."""
        ignored = cls._ignored_files(root)

        def on_error(error: OSError) -> None:
            logger.error(
                "Falha ao ler a estrutura da OS",
                code="PSS_WALK_ERR",
                error=str(error),
                path=str(root),
            )

        for current, dirs, files in os.walk(root, onerror=on_error):
            dirs.sort(key=str.lower)
            files.sort(key=str.lower)
            current_path = Path(current)
            for name in dirs:
                entry["folders"].append(
                    (current_path / name).relative_to(root).as_posix()
                )
            for name in files:
                relative = (current_path / name).relative_to(root).as_posix()
                if cls._is_ignored(name, relative, ignored):
                    continue
                entry["files"].append(relative)

    @classmethod
    def _ignored_files(cls, root: Path) -> set[str]:
        """Caminhos (relativos, minúsculos) que não entram no snapshot."""
        changelog = ProjectStructureChangelog.relative_document_path(root)
        return {changelog.lower()}

    @staticmethod
    def _is_ignored(name: str, relative: str, ignored: set[str]) -> bool:
        """Indica se o arquivo é temporário do Office ou o próprio changelog."""
        return name.startswith("~$") or relative.lower() in ignored

    # ── Comparação ──────────────────────────────────────────────────

    @classmethod
    def diff(
        cls,
        previous: Dict[str, Dict[str, Any]],
        current: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Compara dois snapshots e devolve apenas as OS com alterações.

        Args:
            previous: snapshot salvo no banco (``{scope: registro}``).
            current: snapshot atual gerado por ``scan``.

        Returns:
            Lista de registros com ``scope``, ``os`` e as quatro listas de
            mudanças (pastas/arquivos criados e removidos).
        """
        changes: List[Dict[str, Any]] = []
        for scope in sorted(set(previous) | set(current), key=str.lower):
            before = previous.get(scope) or {}
            after = current.get(scope) or {}
            change = {
                "scope": str(after.get("scope") or before.get("scope") or scope),
                "os": str(after.get("os") or before.get("os") or ""),
                "added_folders": cls._difference(after, before, "folders"),
                "removed_folders": cls._difference(before, after, "folders"),
                "added_files": cls._difference(after, before, "files"),
                "removed_files": cls._difference(before, after, "files"),
            }
            if any(change[key] for key in cls._CHANGE_KEYS):
                changes.append(change)
        return changes

    @staticmethod
    def _difference(
        source: Dict[str, Any],
        reference: Dict[str, Any],
        key: str,
    ) -> List[str]:
        """Itens de ``source[key]`` que não existem em ``reference[key]``."""
        current = set(source.get(key, []) or [])
        previous = set(reference.get(key, []) or [])
        return sorted(current - previous, key=str.lower)
