# -*- coding: utf-8 -*-
"""
ProjectStructureSnapshot — Snapshot da estrutura de pastas das OS
================================================================
Scanner ISOLADO da estrutura (sem widgets, sem banco e sem regra de negócio):

- ``scan`` percorre a pasta-mãe e devolve, para cada pasta de OS, a lista
  COMPLETA (recursiva) de pastas e arquivos, com caminhos RELATIVOS à pasta
  da OS e separador ``/`` (portável entre computadores).
- Para cada arquivo são gravados o TAMANHO (``sizes``) e a data da ÚLTIMA
  MODIFICAÇÃO (``modified``).

A comparação/classificação das alterações (renomeações, movimentações etc.)
fica em ``utils.ProjectStructureChangeDetector`` — este módulo apenas LÊ o
disco.

O changelog gerado pela ferramenta (``11_AGROROBOTICA/
OS_<numero>_CHANGELOG.DOCX``) e os temporários do Office (``~$*``) são
ignorados — assim a própria gravação do documento não vira "alteração" na
próxima execução.

Uso:
    from utils.ProjectStructureSnapshot import ProjectStructureSnapshot

    snapshot = ProjectStructureSnapshot.scan(mother)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureChangelog import ProjectStructureChangelog
from utils.ProjectStructureUtil import ProjectStructureUtil


class ProjectStructureSnapshot(BaseUtil):
    """Lê a estrutura das OS em disco (pastas, arquivos, tamanho e data)."""

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
            "modified": {},
            "sizes": {},
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
                info = cls._file_info(current_path / name, logger)
                entry["sizes"][relative] = info["size"]
                entry["modified"][relative] = info["modified_at"]

    @classmethod
    def _file_info(cls, path: Path, logger: Any) -> Dict[str, Any]:
        """Tamanho (bytes) e data da última modificação (ISO) do arquivo.

        Em caso de falha de ``stat`` o tamanho fica ``-1`` (desconhecido) e a
        data fica vazia; a detecção ignora tamanhos desconhecidos.
        """
        try:
            stat = path.stat()
        except OSError as e:
            logger.warning(
                "Falha ao ler tamanho/data do arquivo",
                code="PSS_STAT_ERR",
                error=str(e),
                path=str(path),
            )
            return {"size": -1, "modified_at": ""}
        return {
            "size": int(stat.st_size),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(
                timespec="seconds"
            ),
        }

    @classmethod
    def _ignored_files(cls, root: Path) -> set[str]:
        """Caminhos (relativos, minúsculos) que não entram no snapshot."""
        changelog = ProjectStructureChangelog.relative_document_path(root)
        return {changelog.lower()}

    @staticmethod
    def _is_ignored(name: str, relative: str, ignored: set[str]) -> bool:
        """Indica se o arquivo é temporário do Office ou o próprio changelog."""
        return name.startswith("~$") or relative.lower() in ignored

