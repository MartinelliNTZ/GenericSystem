# -*- coding: utf-8 -*-
"""
OsTrackerService — Lógica do Acompanhamento de OS (OS → pastas)
===============================================================
Lógica pura (sem widgets Qt):

- ``load_orders`` lê os registros de OS da FONTE OFICIAL (Firebase) via a
  classe de banco ``CloudProjectDatabase`` (o plugin NUNCA toca no JSON).
- ``load_changes`` lê as alterações de UMA OS (changelog da estrutura) via
  ``CloudStructureDatabase.load_changes``.
- ``create_order`` cria a OS na base (grava no Firebase).
- ``add_folders`` cria as pastas padrão selecionadas dentro da pasta da OS.

A OS é **TEXTO** e pode conter **LETRA** (ex.: ``169A``, ``181B``): a letra é o
que diferencia as OS de um mesmo projeto. Cada OS tem UMA pasta em disco
(``OS_<chave>_...``) e guarda no próprio registro o cliente, o nome comercial, o
CNPJ, o caminho e as pastas/anos criados.

Uso:
    from plugins.os_tracker.OsTrackerService import OsTrackerService

    orders = OsTrackerService.load_orders()
    changes = OsTrackerService.load_changes("169A")
    folder = OsTrackerService.project_folder(mother, record)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.enum.ToolKey import ToolKey
from core.firebase.CloudProjectDatabase import CloudProjectDatabase
from core.firebase.CloudStructureDatabase import CloudStructureDatabase
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureChangelog import ProjectStructureChangelog
from utils.ProjectStructureCreator import ProjectStructureCreator
from utils.ProjectStructureUtil import ProjectStructureUtil


class OsTrackerService(BaseUtil):
    """Lê e mantém os registros de OS e as pastas associadas."""

    RECENT_CHANGES_LIMIT = 6
    _CHANGE_SUMMARY_LABELS = (
        ("pasta(s) criada(s)", "added_folders"),
        ("pasta(s) removida(s)", "removed_folders"),
        ("pasta(s) renomeada(s)", "folder_renames"),
        ("pasta(s) movida(s)", "folder_moves"),
        ("arquivo(s) criado(s)", "added_files"),
        ("arquivo(s) removido(s)", "removed_files"),
        ("arquivo(s) renomeado(s)", "renamed_files"),
        ("arquivo(s) movido(s)", "moved_files"),
        ("arquivo(s) modificado(s)", "modified_files"),
    )

    # ── Leitura ─────────────────────────────────────────────────────

    @classmethod
    def load_orders(
        cls, tool_key: str = ToolKey.OS_TRACKER.value
    ) -> List[Dict[str, Any]]:
        """Lê os registros de OS da fonte oficial (Firebase — nunca do JSON)."""
        return CloudProjectDatabase.load_orders(tool_key=tool_key)

    @classmethod
    def load_changes(
        cls,
        os_number: str,
        limit: int = RECENT_CHANGES_LIMIT,
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> List[Dict[str, Any]]:
        """Alterações registradas para UMA OS (mais recentes primeiro)."""
        number = ProjectStructureUtil.normalize_os(str(os_number or ""))
        if not number:
            return []
        return CloudStructureDatabase.load_changes(
            limit=limit, os_number=number, tool_key=tool_key
        )

    # ── Apresentação das alterações ─────────────────────────────────

    @classmethod
    def change_summary(cls, change: Dict[str, Any]) -> str:
        """Resumo curto de uma alteração (ex.: ``2 pasta(s) criada(s)``)."""
        if change.get("first_run"):
            return "Primeira inicialização"
        parts = [
            f"{len(change.get(key) or [])} {label}"
            for label, key in cls._CHANGE_SUMMARY_LABELS
            if change.get(key)
        ]
        if not parts:
            return "Sem itens registrados"
        return " · ".join(parts[:3] + (["…"] if len(parts) > 3 else []))

    @staticmethod
    def format_when(
        value: str,
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> str:
        """Formata um timestamp ISO em ``dd/mm/aaaa hh:mm`` (ou devolve o original)."""
        text = str(value or "")
        if not text:
            return ""
        try:
            return datetime.fromisoformat(text).strftime("%d/%m/%Y %H:%M")
        except ValueError as e:
            BaseUtil._get_logger(tool_key, "OsTrackerService").warning(
                "Data inválida",
                code="OST_DATE_ERR",
                error=str(e),
                value=text,
            )
            return text

    @classmethod
    def change_when(
        cls,
        change: Dict[str, Any],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> str:
        """Data/hora da alteração (``dd/mm/aaaa hh:mm``) ou o texto original."""
        return cls.format_when(str(change.get("detected_at", "") or ""), tool_key)

    @classmethod
    def record_summary(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Resume cliente/pastas/anos/caminho do registro da OS."""
        return {
            "client": str(record.get("client", "") or ""),
            "folders": list(record.get("folders") or []),
            "years": list(record.get("years") or []),
            "path": str(record.get("path", "") or ""),
        }

    @classmethod
    def order_label(cls, record: Dict[str, Any]) -> str:
        """Rótulo exibido no seletor de OS (``OS <chave> — <cliente>``)."""
        os_key = str(record.get("os", "")).strip()
        client = cls.record_summary(record)["client"].strip()
        return f"OS {os_key} — {client}" if client else f"OS {os_key}"

    # ── Base de Limites/Zonas gravada na OS ─────────────────────────

    @classmethod
    def asset_info(
        cls, record: Optional[Dict[str, Any]], key: str
    ) -> Dict[str, Any]:
        """
        Resumo do asset ``limites``/``zonas_manejo`` gravado na OS pelo banco.

        Chaves: ``has``, ``features``, ``area_ha``, ``file``, ``source`` e
        ``inserted_at``.
        """
        data = (record or {}).get(key)
        if not isinstance(data, dict) or not data:
            return {
                "has": False,
                "features": 0,
                "area_ha": 0.0,
                "file": "",
                "source": "",
                "inserted_at": "",
            }

        return {
            "has": True,
            "features": cls._as_int(data.get("features")),
            "area_ha": cls._as_float(data.get("area_ha")),
            "file": str(data.get("file", "") or ""),
            "source": str(data.get("source", "") or ""),
            "inserted_at": str(data.get("inserted_at", "") or ""),
        }

    @classmethod
    def asset_file_path(
        cls,
        mother: Optional[Path],
        record: Optional[Dict[str, Any]],
        key: str,
    ) -> str:
        """Caminho ABSOLUTO do arquivo do asset gravado na OS.

        O banco guarda o caminho RELATIVO à pasta-mãe; registros antigos podem ter
        caminho absoluto ou apenas o nome do arquivo. A resolução tenta, na ordem:
        caminho absoluto → relativo à pasta-mãe → relativo à pasta da OS.
        """
        rel = cls.asset_info(record, key)["file"]
        if not rel:
            return ""

        candidate = Path(rel)
        if candidate.is_absolute():
            return str(candidate)

        mother_path = Path(mother) if mother is not None else None
        folder = cls.project_folder(mother_path, record)
        for base in (mother_path, folder):
            if base is None:
                continue
            resolved = ProjectStructureUtil.resolve_path(base, rel)
            if resolved.exists():
                return str(resolved)

        base = mother_path or folder
        return str(ProjectStructureUtil.resolve_path(base, rel)) if base else rel

    # ── Atalhos (pasta/arquivo da OS) ───────────────────────────────

    @classmethod
    def project_folder(
        cls, mother: Optional[Path], record: Optional[Dict[str, Any]]
    ) -> Optional[Path]:
        """Pasta física da OS (resolvida pela pasta-mãe), ou ``None``.

        Usa o caminho gravado no registro; quando ele não existe em disco, procura
        a pasta ``OS_<chave>...`` na pasta-mãe.
        """
        rel = str((record or {}).get("path", "") or "")
        base = Path(mother) if mother is not None else None
        if rel:
            folder = ProjectStructureUtil.resolve_path(base, rel)
            if folder.is_dir():
                return folder
        return ProjectStructureUtil.project_folder(
            base, str((record or {}).get("os", "") or "")
        )

    @classmethod
    def changelog_path(
        cls, mother: Optional[Path], record: Optional[Dict[str, Any]]
    ) -> str:
        """Caminho do changelog Word da OS (``""`` sem pasta cadastrada)."""
        folder = cls.project_folder(mother, record)
        if folder is None:
            return ""
        return str(ProjectStructureChangelog.document_path(folder))

    @staticmethod
    def _as_int(value: Any) -> int:
        """Converte um valor do banco em inteiro (fallback ``0``)."""
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _as_float(value: Any) -> float:
        """Converte um valor do banco em float (fallback ``0.0``)."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    # ── Escrita (grava no Firebase via classe de banco) ──────────────

    @classmethod
    def create_order(
        cls,
        mother: Optional[Path],
        os_key: str,
        name: str = "",
        client: str = "",
        commercial_name: str = "",
        cnpj: str = "",
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Dict[str, Any]:
        """Cria uma OS (chave obrigatória — pode conter letra, ex.: ``169A``).

        Preserva uma OS já existente (mescla) e garante a pasta ``OS_<chave>`` em
        disco. Grava direto no Firebase.
        """
        key = ProjectStructureUtil.normalize_os(os_key)
        record = CloudProjectDatabase.get_order(key, tool_key=tool_key) or {}
        record["os"] = key
        if name:
            record["name"] = name
        cls._fill_order(record, client, commercial_name, cnpj)
        if mother:
            folder = cls.ensure_project_folder(mother, record, tool_key=tool_key)
            record["path"] = ProjectStructureUtil.to_relative_path(
                Path(mother), folder
            )
        CloudProjectDatabase.save_order(
            record, mother=str(mother) if mother else "", tool_key=tool_key
        )
        return record

    @classmethod
    def add_folders(
        cls,
        mother: Optional[Path],
        record: Dict[str, Any],
        folder_names: List[str],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Dict[str, Any]:
        """Cria as pastas padrão selecionadas na pasta da OS e atualiza a base."""
        project = cls.ensure_project_folder(mother, record, tool_key=tool_key)
        created = ProjectStructureCreator.create_project_folders(
            project, folder_names, tool_key=tool_key
        )
        data = ProjectStructureUtil.collect_created_data(project, tool_key=tool_key)
        record["path"] = ProjectStructureUtil.to_relative_path(mother, project)
        record["folders"] = data["folders"]
        record["years"] = data["years"]
        CloudProjectDatabase.save_order(
            record, mother=str(mother) if mother else "", tool_key=tool_key
        )
        return {"created": created, "path": str(project)}

    @classmethod
    def ensure_project_folder(
        cls,
        mother: Optional[Path],
        record: Dict[str, Any],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Path:
        """Garante a pasta física da OS (cria ``OS_<chave>`` se não existir)."""
        mother_path = Path(mother) if mother else None
        rel = str(record.get("path", "") or "")
        if rel:
            folder = ProjectStructureUtil.resolve_path(mother_path, rel)
            if folder.exists():
                return folder
        key = ProjectStructureUtil.normalize_os(str(record.get("os", "")))
        base = mother_path if mother_path is not None else Path(".")
        folder = base / f"{ProjectStructureUtil.PROJECT_PREFIX}{key}"
        folder.mkdir(parents=True, exist_ok=True)
        record["path"] = ProjectStructureUtil.to_relative_path(mother_path, folder)
        return folder

    @staticmethod
    def _fill_order(
        record: Dict[str, Any], client: str, commercial_name: str, cnpj: str
    ) -> None:
        """Preenche os campos da OS (sem apagar o que já existe)."""
        if client:
            record["client"] = client
        if commercial_name:
            record["commercial_name"] = commercial_name
        if cnpj:
            record["cnpj"] = cnpj
        record.setdefault("path", "")
        record.setdefault("folders", [])
        record.setdefault("years", [])
        record.setdefault("client", "")
        record.setdefault("commercial_name", "")
        record.setdefault("cnpj", "")
