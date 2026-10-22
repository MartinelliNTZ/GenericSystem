# -*- coding: utf-8 -*-
"""
migrate_os_keys.py — Script de DEV: migra a base de OS para o esquema SEM SubOS
==============================================================================
Migra os registros do Firestore (coleção ``banco_dados``) do esquema ANTIGO
(``os`` sem zeros + lista ``sub_os``) para o esquema NOVO:

- a OS é **TEXTO** e pode conter **LETRA** (``169`` + SubOS ``B`` → ``169B``);
- **cada pasta em disco é UMA OS**: cliente, nome comercial, CNPJ, caminho,
  pastas/anos e as bases (``limites``/``zonas_manejo``) passam para o PRÓPRIO
  registro (a chave ``sub_os`` deixa de existir);
- os zeros à esquerda são PRESERVADOS (``39`` → ``039``).

A chave nova de cada registro vem do NOME DA PASTA em disco
(``OS_169B_DARRO`` → ``169B``): o disco é a fonte da verdade, porque as pastas
das OS que ganharam letra foram renomeadas.

USO:
    python add_data/migrate_os_keys.py --dry-run   # só mostra o plano (nada grava)
    python add_data/migrate_os_keys.py             # migra (Firestore + backups JSON)

Antes de gravar, o script copia ``<pasta-mãe>/.BancoDados`` para
``<pasta-mãe>/.BancoDados_backup_<AAAAMMDDHHMMSS>``.

Este script é SOMENTE PARA DESENVOLVIMENTO (migração única do esquema).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# O console do Windows pode estar em cp1252: força a saída UTF-8 para o script
# poder imprimir acentos/setas (o HomePlugin captura a saída como UTF-8).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.enum.ToolKey import ToolKey  # noqa: E402
from core.firebase.FirebaseTokenProvider import FirebaseTokenProvider  # noqa: E402
from core.firebase.CloudProjectDatabase import CloudProjectDatabase  # noqa: E402
from core.database.ProjectDatabaseStore import ProjectDatabaseStore  # noqa: E402
from utils.ProjectStructureUtil import ProjectStructureUtil  # noqa: E402

_TOOL_KEY = ToolKey.PROJECT_DATABASE.value

# Bases gravadas na OS pelo banco (chaves que saem da SubOS para o registro).
ASSET_KEYS = ("limites", "zonas_manejo")


# ── Pasta-mãe ─────────────────────────────────────────────────────────

def _read_prefs_mother() -> str:
    """Lê ``ProjectStructure.mother_folder`` do arquivo de preferências (sem Qt)."""
    for path in (ROOT / "config").glob("*_preferences.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        mother = (data.get("ProjectStructure") or {}).get("mother_folder", "")
        if mother:
            return str(mother)
    return ""


def _resolve_mother(cli_value: str) -> Path:
    """Resolve a pasta-mãe: --mother → env var → preferência do ProjectStructure."""
    if cli_value:
        return Path(cli_value).expanduser()
    env_value = os.environ.get("AETHERIS_MOTHER_FOLDER", "").strip()
    if env_value:
        return Path(env_value).expanduser()
    return Path(_read_prefs_mother()).expanduser()


def _scan_keys(mother: Path) -> Dict[str, Path]:
    """Mapa ``{chave_da_os: pasta}`` a partir das pastas ``OS_*`` em disco."""
    folders: Dict[str, Path] = {}
    for project in ProjectStructureUtil.discover_projects(mother):
        key = ProjectStructureUtil.extract_os(project.name)
        if key:
            folders[key] = project
    return folders


# ── Nova chave de cada registro ───────────────────────────────────────

def _resolve_key(
    old_key: str,
    letter: str,
    rel_path: str,
    folders: Dict[str, Path],
    forced: str = "",
) -> str:
    """Decide a chave NOVA de uma OS (o disco manda; o banco é o fallback).

    Ordem: chave forçada por ``--rename`` → chave da pasta gravada no banco →
    ``<os antiga><letra>`` (ex.: ``169`` + ``A`` → ``169A``) → a própria ``os``
    antiga → o que veio do banco.
    """
    if forced:
        return forced
    stored = ProjectStructureUtil.extract_os(Path(rel_path).name) if rel_path else ""
    if stored and stored in folders:
        return stored
    if letter and f"{old_key}{letter}" in folders:
        return f"{old_key}{letter}"
    if old_key in folders:
        return old_key
    if stored:
        return stored
    return f"{old_key}{letter}" if letter and letter != "A" else old_key


def _repair_asset_file(
    mother: Path, folder: Path | None, data: Any
) -> Any:
    """Reaponta o arquivo do asset para a pasta ATUAL da OS (pasta renomeada).

    O nome do arquivo é preservado; o prefixo (pasta antiga) é reescrito para o
    caminho RELATIVO à pasta-mãe do arquivo encontrado dentro da pasta da OS.
    """
    if not isinstance(data, dict) or not data or folder is None:
        return data
    raw = str(data.get("file", "") or "")
    if not raw:
        return data

    name = Path(raw).name
    found = next((path for path in folder.rglob(name)), None)
    if found is None:
        return data

    repaired = dict(data)
    repaired["file"] = ProjectStructureUtil.to_relative_path(mother, found)
    return repaired


def _build_record(
    source: Dict[str, Any],
    entry: Dict[str, Any],
    key: str,
    rel_path: str,
    mother: Path,
) -> Dict[str, Any]:
    """Monta o registro NOVO de UMA OS (sem ``sub_os``) com a chave informada."""
    record: Dict[str, Any] = {
        "os": key,
        "name": str(source.get("name", "") or ""),
        "path": rel_path,
        "folders": list(entry.get("folders") or []),
        "years": list(entry.get("years") or []),
        "client": str(entry.get("client", "") or source.get("client", "") or ""),
        "commercial_name": str(
            entry.get("commercial_name", "") or source.get("commercial_name", "") or ""
        ),
        "cnpj": str(entry.get("cnpj", "") or source.get("cnpj", "") or ""),
        "updated_at": str(source.get("updated_at", "") or ""),
    }

    folder = folders_path(mother, key)
    for asset in ASSET_KEYS:
        data = entry.get(asset, source.get(asset))
        if isinstance(data, dict) and data:
            record[asset] = _repair_asset_file(mother, folder, data)

    if folder is not None:
        data = ProjectStructureUtil.collect_created_data(folder)
        record["path"] = ProjectStructureUtil.to_relative_path(mother, folder)
        record["folders"] = data["folders"]
        record["years"] = data["years"]
    return record


def folders_path(mother: Path, key: str) -> Path | None:
    """Pasta da OS na pasta-mãe (``None`` quando não existe)."""
    return ProjectStructureUtil.project_folder(mother, key, tool_key=_TOOL_KEY)


# ── Plano da migração ─────────────────────────────────────────────────

def _dedupe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mantém UM registro por chave (preferindo o que tem pasta em disco)."""
    merged: Dict[str, Dict[str, Any]] = {}
    for record in records:
        key = str(record.get("os", ""))
        current = merged.get(key)
        if current is None or (not current.get("path") and record.get("path")):
            merged[key] = record
    return list(merged.values())


def _plan(
    orders: List[Dict[str, Any]],
    mother: Path,
    folders: Dict[str, Path],
    aliases: Dict[str, str] | None = None,
) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
    """Converte os registros antigos: ``(registros_novos, [(antiga, nova)])``.

    ``aliases`` força a chave de uma OS (``--rename`` — ex.: ``377`` → ``393``
    quando a OS foi renumerada e a pasta mudou de nome).
    """
    aliases = aliases or {}
    records: List[Dict[str, Any]] = []
    mapping: List[Tuple[str, str]] = []

    for source in orders:
        old_key = ProjectStructureUtil.normalize_os(str(source.get("os", "")))
        forced = aliases.get(old_key, "")
        entries = [
            entry for entry in source.get("sub_os", []) or []
            if isinstance(entry, dict)
        ]
        if not entries:
            rel = str(source.get("path", "") or "")
            key = _resolve_key(old_key, "", rel, folders, forced)
            records.append(_build_record(source, source, key, rel, mother))
            mapping.append((old_key, key))
            continue

        for entry in entries:
            letter = ProjectStructureUtil.normalize_os(str(entry.get("sub_os", "")))
            rel = str(entry.get("path", "") or "")
            key = _resolve_key(old_key, letter, rel, folders, forced)
            records.append(_build_record(source, entry, key, rel, mother))
            mapping.append((old_key, key))

    return _dedupe(records), mapping


# ── Gravação ──────────────────────────────────────────────────────────

def _backup_database(mother: Path) -> str:
    """Copia ``.BancoDados`` para uma pasta datada antes de sobrescrever."""
    source = ProjectDatabaseStore.db_dir(mother)
    if not source.is_dir():
        return ""
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    target = source.parent / f"{ProjectDatabaseStore.DB_FOLDER}_backup_{stamp}"
    shutil.copytree(source, target)
    return str(target)


def _parse_aliases(items: List[str]) -> Dict[str, str]:
    """Converte ``["377=393"]`` em ``{"377": "393"}`` (chaves normalizadas)."""
    aliases: Dict[str, str] = {}
    for item in items:
        old, _, new = str(item).partition("=")
        old = ProjectStructureUtil.normalize_os(old)
        new = ProjectStructureUtil.normalize_os(new)
        if not old or not new:
            raise SystemExit(f"--rename inválido: '{item}' (use ANTIGA=NOVA).")
        aliases[old] = new
    return aliases


def _apply(
    mother: Path, dry_run: bool, aliases: Dict[str, str] | None = None
) -> None:
    """Migra a base de OS (Firestore + backups JSON) para o esquema sem SubOS."""
    aliases = aliases or {}
    orders = CloudProjectDatabase.load_orders(tool_key=_TOOL_KEY)
    folders = _scan_keys(mother)
    records, mapping = _plan(orders, mother, folders, aliases)

    new_keys = {str(record.get("os", "")) for record in records}
    obsolete = sorted({
        ProjectStructureUtil.normalize_os(str(record.get("os", "")))
        for record in orders
        if ProjectStructureUtil.normalize_os(str(record.get("os", ""))) not in new_keys
    })

    print(f"Pasta-mãe : {mother}")
    print(f"Registros : {len(orders)} antigo(s) -> {len(records)} novo(s)")
    for old_key, new_key in mapping:
        if old_key != new_key:
            print(f"  {old_key} -> {new_key}")
    for old_key, new_key in sorted(aliases.items()):
        mark = "" if new_key in folders else "  [sem pasta em disco]"
        print(f"Renomeado : {old_key} -> {new_key}{mark}")
    if obsolete:
        print(f"Obsoletos : {', '.join(obsolete)}")

    if dry_run:
        print("[dry-run] Nada foi gravado (nem Firestore nem backups JSON).")
        return

    backup = _backup_database(mother)
    if backup:
        print(f"Backup    : {backup}")

    saved = CloudProjectDatabase.save_orders(
        records, mother=str(mother), tool_key=_TOOL_KEY
    )
    print(f"Firestore : {saved} documento(s) gravado(s)")

    removed = 0
    for key in obsolete:
        if CloudProjectDatabase.delete_order(key, tool_key=_TOOL_KEY):
            removed += 1
    print(f"Removidos : {removed} documento(s) antigo(s)")


def main() -> None:
    """Ponto de entrada do script de migração."""
    parser = argparse.ArgumentParser(
        description="DEV: migra a base de OS para o esquema sem SubOS (chave texto).",
    )
    parser.add_argument("--mother", default="", help="Pasta-mãe das OS.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Não grava nada (só mostra o plano).",
    )
    parser.add_argument(
        "--rename",
        action="append",
        default=[],
        metavar="ANTIGA=NOVA",
        help="Renumera a chave de uma OS (ex.: --rename 377=393). Repetível.",
    )
    args = parser.parse_args()

    mother = _resolve_mother(args.mother)
    if not mother.is_dir():
        raise SystemExit(f"Pasta-mãe inexistente: {mother}")
    if not FirebaseTokenProvider.has_credentials():
        raise SystemExit(
            "Sem credenciais Firebase (conta de serviço ou login). "
            "A migração lê e grava direto no Firestore."
        )
    _apply(mother, args.dry_run, _parse_aliases(args.rename))


if __name__ == "__main__":
    main()
