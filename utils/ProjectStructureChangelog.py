# -*- coding: utf-8 -*-
"""
ProjectStructureChangelog — Documento Word de changelog por OS
=============================================================
Grava/atualiza o changelog da estrutura de uma OS em
``<pasta da OS>/11_AGROROBOTICA/OS_<numero>_CHANGELOG.DOCX``.

O documento é criado sob demanda (na primeira alteração detectada) e, nas
próximas execuções, recebe um novo bloco com data/hora e a lista de pastas e
arquivos criados/removidos. Os blocos ficam em ordem DECRESCENTE (o mais
recente no topo, logo abaixo do cabeçalho). O arquivo é EXCLUÍDO do snapshot
da estrutura — sem isso, a própria atualização do documento apareceria como
alteração.

Uso:
    from utils.ProjectStructureChangelog import ProjectStructureChangelog

    result = ProjectStructureChangelog.append_changes(os_folder, change)
    # result -> {"written": bool, "created_folder": bool, "path": str}
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureUtil import ProjectStructureUtil


class ProjectStructureChangelog(BaseUtil):
    """Cria e atualiza o documento Word de changelog de cada OS."""

    FOLDER_NAME = "11_AGROROBOTICA"
    DOCUMENT_SUFFIX = "_CHANGELOG.DOCX"
    # Quantidade de parágrafos do cabeçalho criado por _new_document.
    HEADER_PARAGRAPHS = 3

    _CHANGE_LABELS = (
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

    # ── Caminho do documento ────────────────────────────────────────

    @classmethod
    def document_path(cls, os_folder: str | Path) -> Path:
        """Retorna o caminho do changelog dentro da pasta da OS."""
        folder = Path(os_folder)
        name = cls._document_name(folder)
        return folder / cls.FOLDER_NAME / f"{name}{cls.DOCUMENT_SUFFIX}"

    @classmethod
    def relative_document_path(cls, os_folder: str | Path) -> str:
        """Caminho do changelog RELATIVO à pasta da OS (posix)."""
        folder = Path(os_folder)
        return cls.document_path(folder).relative_to(folder).as_posix()

    @classmethod
    def _document_name(cls, os_folder: Path) -> str:
        """Nome base do documento (``OS_039``) a partir da pasta da OS."""
        raw = ProjectStructureUtil.extract_os_number(os_folder.name)
        number = ProjectStructureUtil.normalize_os(raw)
        if not number:
            return os_folder.name
        if number.isdigit():
            return f"OS_{int(number):03d}"
        return f"OS_{number}"

    # ── Gravação ────────────────────────────────────────────────────

    @classmethod
    def append_changes(
        cls,
        os_folder: str | Path,
        change: Dict[str, Any],
        tool_key: str = ToolKey.PROJECT_STRUCTURE.value,
    ) -> Dict[str, Any]:
        """Acrescenta um bloco de alterações ao changelog da OS.

        Returns:
            ``{"written", "created_folder", "path"}`` — ``written`` é ``False``
            quando não foi possível gravar (ex.: documento aberto no Word).
        """
        logger = cls._get_logger(tool_key, "ProjectStructureChangelog")
        path = cls.document_path(os_folder)
        created_folder = not path.parent.exists()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            document = cls._load_document(path, os_folder, logger)
            cls._append_event(document, change, tool_key)
            document.save(str(path))
        except (OSError, ValueError) as e:
            logger.error(
                "Falha ao gravar o changelog da OS",
                code="PSCH_SAVE_ERR",
                error=str(e),
                path=str(path),
            )
            return {"written": False, "created_folder": False, "path": str(path)}
        logger.info("Changelog atualizado", code="PSCH_SAVE_OK", path=str(path))
        return {"written": True, "created_folder": created_folder, "path": str(path)}

    @classmethod
    def _load_document(cls, path: Path, os_folder: str | Path, logger: Any) -> Document:
        """Abre o documento existente ou cria um novo quando ausente/corrompido."""
        if not path.exists():
            return cls._new_document(os_folder)
        try:
            return Document(str(path))
        except (PackageNotFoundError, ValueError) as e:
            logger.warning(
                "Changelog inválido — recriando o documento",
                code="PSCH_CORRUPT",
                error=str(e),
                path=str(path),
            )
            return cls._new_document(os_folder)

    @staticmethod
    def _new_document(os_folder: str | Path) -> Document:
        """Cria o documento com o cabeçalho padrão do changelog."""
        document = Document()
        document.add_heading("CHANGELOG — Estrutura da OS", level=1)
        document.add_paragraph(f"OS: {Path(os_folder).name}")
        document.add_paragraph(
            "Documento gerado automaticamente pelo Aetheris ToolBox. Cada bloco "
            "registra as pastas e os arquivos criados ou removidos na estrutura."
        )
        return document

    @classmethod
    def _append_event(
        cls,
        document: Document,
        change: Dict[str, Any],
        tool_key: str,
    ) -> None:
        """Insere o bloco de alterações logo após o cabeçalho.

        A ordem é DECRESCENTE: o bloco mais recente fica no topo (logo abaixo do
        cabeçalho) e os blocos anteriores são empurrados para baixo.
        """
        existing = len(document.paragraphs)
        created = [
            document.add_heading(
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"), level=2
            )
        ]
        registered = False
        for label, key in cls._CHANGE_LABELS:
            for item in change.get(key, []) or []:
                text = cls._item_text(item, tool_key)
                created.append(
                    document.add_paragraph(f"{label}: {text}", style="List Bullet")
                )
                registered = True
        if not registered:
            created.append(document.add_paragraph("Sem alterações registradas."))
        if existing > cls.HEADER_PARAGRAPHS:
            anchor = document.paragraphs[cls.HEADER_PARAGRAPHS]._p
            for paragraph in created:
                anchor.addprevious(paragraph._p)

    @classmethod
    def _item_text(cls, item: Any, tool_key: str) -> str:
        """Formata uma alteração (texto, renomeado/movido ou data)."""
        if not isinstance(item, dict):
            return str(item)
        if "old_path" in item and "new_path" in item:
            text = f"{item['old_path']} → {item['new_path']}"
            count = item.get("file_count")
            if isinstance(count, int):
                text += f" ({count} arquivo(s))"
            return text
        path = str(item.get("path", ""))
        date = cls._format_date(str(item.get("modified_at", "")), tool_key)
        return f"{path} (modificado em {date})" if date else path

    @classmethod
    def _format_date(cls, value: str, tool_key: str) -> str:
        """Converte ISO (``2026-10-19T15:42:10``) em ``19/10/2026 15:42:10``."""
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).strftime("%d/%m/%Y %H:%M:%S")
        except ValueError as e:
            cls._get_logger(tool_key, "ProjectStructureChangelog").warning(
                "Data de modificação inválida",
                code="PSCH_DATE_ERR",
                error=str(e),
                value=value,
            )
            return value
