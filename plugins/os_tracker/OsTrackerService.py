# -*- coding: utf-8 -*-
"""
OsTrackerService — Lógica do Acompanhamento de OS (OS → SubOS → pastas)
=======================================================================
Lógica pura (sem widgets Qt):

- ``load_orders`` lê os registros de OS da FONTE OFICIAL (Firebase) via a
  classe de banco ``CloudProjectDatabase`` (o plugin NUNCA toca no JSON).
- ``load_changes`` lê as alterações de UMA OS (changelog da estrutura) via
  ``CloudStructureDatabase.load_changes``.
- ``build_sub_os`` converte as entradas ``sub_os`` em modelos ``SubOS``.
- ``create_order`` / ``add_sub_os`` criam OS/SubOS na base (grava no Firebase).
- ``add_folders`` cria as pastas padrão selecionadas dentro da pasta da OS.

Uso:
    from plugins.os_tracker.OsTrackerService import OsTrackerService

    orders = OsTrackerService.load_orders()
    changes = OsTrackerService.load_changes("171")
    sub_os = OsTrackerService.build_sub_os(record)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.enum.ToolKey import ToolKey
from core.firebase.CloudProjectDatabase import CloudProjectDatabase
from core.firebase.CloudStructureDatabase import CloudStructureDatabase
from core.model.SubOSModel import SubOS
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureChangelog import ProjectStructureChangelog
from utils.ProjectStructureCreator import ProjectStructureCreator
from utils.ProjectStructureUtil import ProjectStructureUtil


class OsTrackerService(BaseUtil):
    """Lê e mantém os registros de OS/SubOS e as pastas associadas."""

    RECENT_CHANGES_LIMIT = 6
    # Pastas candidatas do "LIMITE ZM" dentro da pasta da SubOS (ordem de prioridade).
    ZM_CANDIDATES = ("00_ARCGIS/01_SHP/ZM", "00_ARCGIS/ZM", "ZM")
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
    def build_sub_os(cls, record: Dict[str, Any]) -> List[SubOS]:
        """Converte as entradas ``sub_os`` de um registro em modelos ``SubOS``."""
        models: List[SubOS] = []
        for entry in record.get("sub_os", []) or []:
            models.append(
                SubOS(
                    code=str(entry.get("sub_os", "")),
                    name=str(entry.get("client", "")),
                    commercial_name=str(entry.get("commercial_name", "")),
                    document=str(entry.get("cnpj", "")),
                )
            )
        return models

    @classmethod
    def record_summary(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Resume cliente/pastas/anos/caminho da OS a partir das suas SubOS."""
        return ProjectStructureUtil.aggregate_record(record)

    @classmethod
    def order_label(cls, record: Dict[str, Any]) -> str:
        """Rótulo exibido no seletor de OS (``OS <numero> — <cliente>``)."""
        number = str(record.get("os", "")).strip()
        client = cls.record_summary(record)["client"].strip()
        return f"OS {number} — {client}" if client else f"OS {number}"

    @classmethod
    def sub_os_codes(cls, record: Dict[str, Any]) -> List[str]:
        """Lista as letras de SubOS de um registro (ordenadas)."""
        codes = [
            str(entry.get("sub_os", ""))
            for entry in record.get("sub_os", []) or []
            if isinstance(entry, dict)
        ]
        return sorted(code for code in codes if code)

    @classmethod
    def sub_os_entry(
        cls, record: Dict[str, Any], code: str
    ) -> Optional[Dict[str, Any]]:
        """Retorna a entrada ``sub_os`` da letra informada (ou ``None``)."""
        for entry in record.get("sub_os", []) or []:
            if isinstance(entry, dict) and str(entry.get("sub_os", "")) == code:
                return entry
        return None

    @classmethod
    def next_sub_os_code(cls, record: Dict[str, Any]) -> str:
        """Próxima letra de SubOS livre (A, B, C, ...)."""
        used = set(cls.sub_os_codes(record))
        for index in range(26):
            letter = chr(ord("A") + index)
            if letter not in used:
                return letter
        return ""

    # ── Base de Limites/Zonas gravada na SubOS ──────────────────────

    @classmethod
    def asset_info(
        cls, entry: Optional[Dict[str, Any]], key: str
    ) -> Dict[str, Any]:
        """
        Resumo do asset ``limites``/``zonas_manejo`` gravado na SubOS pelo banco.

        Chaves: ``has``, ``features``, ``area_ha``, ``file``, ``source`` e
        ``inserted_at``.
        """
        data = (entry or {}).get(key)
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
        entry: Optional[Dict[str, Any]],
        key: str,
    ) -> str:
        """Caminho ABSOLUTO do arquivo do asset (o banco guarda o caminho relativo)."""
        rel = cls.asset_info(entry, key)["file"]
        if not rel:
            return ""
        if mother is None:
            return rel
        return str(ProjectStructureUtil.resolve_path(Path(mother), rel))

    # ── Atalhos (pastas/arquivos da SubOS) ──────────────────────────

    @classmethod
    def sub_os_folder(
        cls, mother: Optional[Path], entry: Optional[Dict[str, Any]]
    ) -> Optional[Path]:
        """Pasta física da SubOS (resolvida pela pasta-mãe), ou ``None``."""
        rel = str((entry or {}).get("path", "") or "")
        if not rel:
            return None
        base = Path(mother) if mother is not None else None
        return ProjectStructureUtil.resolve_path(base, rel)

    @classmethod
    def zm_folder(
        cls, mother: Optional[Path], entry: Optional[Dict[str, Any]]
    ) -> str:
        """Caminho da pasta LIMITE ZM da SubOS (``""`` sem pasta cadastrada)."""
        folder = cls.sub_os_folder(mother, entry)
        if folder is None:
            return ""
        for relative in cls.ZM_CANDIDATES:
            candidate = folder / relative
            if candidate.is_dir():
                return str(candidate)
        return str(folder / cls.ZM_CANDIDATES[0])

    @classmethod
    def changelog_path(
        cls, mother: Optional[Path], entry: Optional[Dict[str, Any]]
    ) -> str:
        """Caminho do changelog Word da OS (``""`` sem pasta cadastrada)."""
        folder = cls.sub_os_folder(mother, entry)
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
        os_number: str,
        name: str = "",
        client: str = "",
        commercial_name: str = "",
        cnpj: str = "",
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Dict[str, Any]:
        """Cria uma OS (numero obrigatório) com a SubOS ``A`` automática.

        Preserva uma OS já existente (mescla). Grava direto no Firebase.
        """
        number = ProjectStructureUtil.normalize_os(os_number)
        record = CloudProjectDatabase.get_order(number, tool_key=tool_key) or {}
        if not record:
            record = {"os": number, "name": "", "sub_os": []}
        record["os"] = number
        if name:
            record["name"] = name
        subs = {
            str(entry.get("sub_os", "")): entry
            for entry in record.get("sub_os", []) or []
            if isinstance(entry, dict)
        }
        entry = subs.get("A")
        if entry is None:
            entry = {"sub_os": "A"}
            subs["A"] = entry
        cls._fill_sub_os(entry, client, commercial_name, cnpj)
        record["sub_os"] = sorted(
            subs.values(), key=lambda item: str(item.get("sub_os", ""))
        )
        CloudProjectDatabase.save_order(
            record, mother=str(mother) if mother else "", tool_key=tool_key
        )
        return record

    @classmethod
    def add_sub_os(
        cls,
        mother: Optional[Path],
        record: Dict[str, Any],
        code: str = "",
        client: str = "",
        commercial_name: str = "",
        cnpj: str = "",
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Dict[str, Any]:
        """Adiciona uma SubOS à OS (letra automática quando vazia) e grava."""
        letter = (code or cls.next_sub_os_code(record)).strip().upper()
        subs = {
            str(entry.get("sub_os", "")): entry
            for entry in record.get("sub_os", []) or []
            if isinstance(entry, dict)
        }
        entry = subs.get(letter)
        if entry is None:
            entry = {"sub_os": letter}
            subs[letter] = entry
        cls._fill_sub_os(entry, client, commercial_name, cnpj)
        record["sub_os"] = sorted(
            subs.values(), key=lambda item: str(item.get("sub_os", ""))
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
        code: str,
        folder_names: List[str],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Dict[str, Any]:
        """Cria as pastas padrão selecionadas na pasta da SubOS e atualiza a base."""
        entry = cls.sub_os_entry(record, code)
        if entry is None:
            return {"created": 0, "path": ""}
        project = cls.ensure_sub_os_folder(mother, record, entry, tool_key=tool_key)
        created = ProjectStructureCreator.create_project_folders(
            project, folder_names, tool_key=tool_key
        )
        data = ProjectStructureUtil.collect_created_data(project, tool_key=tool_key)
        entry["folders"] = data["folders"]
        entry["years"] = data["years"]
        CloudProjectDatabase.save_order(
            record, mother=str(mother) if mother else "", tool_key=tool_key
        )
        return {"created": created, "path": str(project)}

    @classmethod
    def ensure_sub_os_folder(
        cls,
        mother: Optional[Path],
        record: Dict[str, Any],
        entry: Dict[str, Any],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Path:
        """Garante a pasta física da SubOS (cria ``OS_<numero>`` se não existir)."""
        mother_path = Path(mother) if mother else None
        rel = str(entry.get("path", "") or "")
        if rel:
            folder = ProjectStructureUtil.resolve_path(mother_path, rel)
            if folder.exists():
                return folder
        number = ProjectStructureUtil.normalize_os(str(record.get("os", "")))
        code = str(entry.get("sub_os", "") or "").upper()
        name = f"OS_{int(number):03d}" if number.isdigit() else f"OS_{number}"
        if code and code != "A":
            name = f"{name}_{code}"
        base = mother_path if mother_path is not None else Path(".")
        folder = base / name
        folder.mkdir(parents=True, exist_ok=True)
        entry["path"] = ProjectStructureUtil.to_relative_path(mother_path, folder)
        return folder

    @staticmethod
    def _fill_sub_os(
        entry: Dict[str, Any], client: str, commercial_name: str, cnpj: str
    ) -> None:
        """Preenche os campos da SubOS (sem apagar o que já existe)."""
        if client:
            entry["client"] = client
        if commercial_name:
            entry["commercial_name"] = commercial_name
        if cnpj:
            entry["cnpj"] = cnpj
        entry.setdefault("path", "")
        entry.setdefault("folders", [])
        entry.setdefault("years", [])
        entry.setdefault("client", "")
        entry.setdefault("commercial_name", "")
        entry.setdefault("cnpj", "")
