# -*- coding: utf-8 -*-
"""
seed_sub_os.py — Script de DEV: popula o banco com a categorização OS → SubOS
=============================================================================
Insere, no espelho offline do banco de dados (``<pasta-mãe>/.BancoDados``),
a lista de SubOS de cada OS (cliente, nome comercial e CNPJ).

Este script é SOMENTE PARA DESENVOLVIMENTO (seed inicial da base).

USO:
    python add_data/seed_sub_os.py                      # usa a pasta-mãe da preferência
    python add_data/seed_sub_os.py --mother "C:/pasta"  # pasta-mãe explícita
    python add_data/seed_sub_os.py --dry-run            # só mostra o resumo, não grava
    python add_data/seed_sub_os.py --push               # grava e espelha no Firestore

Como a pasta-mãe é resolvida (nesta ordem):
    1. Argumento --mother
    2. Variável de ambiente AETHERIS_MOTHER_FOLDER
    3. Preferência ProjectStructure.mother_folder (config/<APP_SLUG>_preferences.json)

O que é gravado:
    - ``<os>.json``        (um por OS, com a chave ``sub_os``)
    - ``banco_dados.json`` (consolidado)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Garante a raiz do projeto no sys.path (permite importar core.model).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.model.SubOSModel import SubOS  # noqa: E402
from utils.ProjectStructureUtil import ProjectStructureUtil  # noqa: E402

DB_FOLDER = ".BancoDados"
CONSOLIDATED_FILENAME = "banco_dados.json"

# ── Dados de entrada: (OS, SubOS, Cliente, Nome comercial, CNPJ) ──────
# ── Dados de entrada: (OS, SubOS, Cliente, Nome comercial, CNPJ) ──────
RAW_ROWS: List[tuple] = [
    ("39", "A", "Cornélio Adriano Sanders", "GRUPO PROGRESSO", ""),
    ("50", "A", "SEMENTES TROPICAL", "OCP FERTILIZANTES LTDA", "18.105.959/0001-57"),
    ("53", "A", "OCP FERTILIZANTES LTDA", "OCP FERTILIZANTES LTDA", "18.105.959/0001-57"),
    ("59", "A", "Fazenda Dourada e Fazenda Pedra Dourada", "DOURADA COMERCIAL E AGROPECUARIA S.A", "05.027.654/0002-03"),
    ("68", "A", "Agropecuária Rio da Areia Ltda. / Fazenda Santo Antônio do Paraíso", "AGROPECUARIA RIO DA AREIA LTDA", "02.149.159/0001-06"),
    ("119", "A", "Elisa Agro Sustentável Ltda.", "MITRE AGRO", ""),
    ("131", "A", "Usinas Itamarati S.A. / UISA", "UISA", ""),
    ("132", "A", "FSL ANGUS", "", ""),
    ("133", "A", "ZILOR", "", ""),
    ("140", "A", "Caetano Polato / Fazenda Gravataí", "GRAVATAÍ AGRO", ""),
    ("141", "A", "Marfrig Global Foods S.A.", "MARFIG (FAZ MARCO MOLINA)", ""),
    ("154", "A", "Fetz Agropecuária Ltda.", "Fetz Agropecuária Ltda.", ""),
    ("160", "A", "Itaquere", "Participações E Empreendimentos Rio Suia Ltda", "19.083.038/0001-01"),
    ("167", "A", "GGF FAZENDAS LTDA", "GGF FAZENDAS LTDA", ""),

    # OS 169 é a única que mantém múltiplas SubOS.
    ("169", "A", "Agropecuária Água Viva Ltda.", "AGROPENIDO", ""),
    ("169", "B", "Agropecuária Darro Ltda.", "AGROPENIDO", ""),
    ("169", "C", "Fazenda Pioneira Empreendimentos Agrícolas S.A.", "SLC AGRÍCOLA SA", ""),

    ("171", "A", "Lida Agrícola Ltda. / Grupo Lida", "GRUPO LIDA", ""),
    ("179", "A", "Guilherme Borges de Freitas", "Guilherme Borges de Freitas", ""),
    ("181", "A", "Capricornio Renner", "GRUPO JCN", ""),
    ("182", "A", "SPM Holding e Administradora de Bens Ltda.", "Stradiotti", ""),
    ("183", "A", "FADEL", "", ""),
    ("184", "A", "AGROMANTOVA", "AGROMANTOVA", ""),
    ("186", "A", "LAR COOPERATIVA", "LAR", ""),
    ("187", "A", "José Carlos Costa Vidotti", "JOSÉ CARLOS COSTA VIDOTTI", ""),
    ("189", "A", "Agropecuária Jatobá Ltda.", "THIAGO FABRIS", ""),
    ("190", "A", "Egon Otto Rehn e outros / Grupo ER", "GRUPO ER", ""),
    ("191", "A", "Marco Tulio Paolinelli Ltda.", "Marco Tulio Paolinelli Ltda.", ""),
    ("192", "A", "Energética Santa Helena S.A.", "Energética Santa Helena S.A.", ""),
    ("196", "A", "F L G AGRO E INVESTIMENTO LTDA", "F L G AGRO E INVESTIMENTO LTDA", ""),
    ("200", "A", "Celso José Minozzo e Flavia Gabriela Minozzo", "Celso José Minozzo e Flavia Gabriela Minozzo", ""),
    ("201", "A", "Flávia Bifon e Lúcia Helena Teixeira Bifon", "Flávia Bifon e Lúcia Helena Teixeira Bifon", ""),
    ("210", "A", "Eduardo Zago Machado e outro", "Eduardo Zago Machado e outro", ""),
    ("211", "A", "José Ricardo de Albuquerque Arruda Silva e Sílvia Morsoletto Tozetto", "José Ricardo de Albuquerque Arruda Silva e Sílvia Morsoletto Tozetto", ""),
    ("214", "A", "Manoel Benedito Rosa Filho", "Manoel Benedito Rosa Filho", ""),
    ("215", "A", "Agrigel Agropecuária Ltda.", "DIERBERGER  CITROS", ""),
    ("220", "A", "Wanda Inês Riedi e Ivo Ilário Riedi", "Wanda Inês Riedi e Ivo Ilário Riedi", ""),
    ("221", "A", "Sidnei Elvis Willms", "Sidnei Elvis Willms", ""),
    ("222", "A", "Agropecuária Terras do Guaporé Ltda.", "Agropecuária Terras do Guaporé Ltda.", ""),
    ("225", "A", "Hosana Luiz de Faria e Gisele Pereira Silva de Faria", "Hosana Luiz de Faria e Gisele Pereira Silva de Faria", ""),
    ("229", "A", "Agropecuária Gado Bravo Ltda.", "GADO BRAVO", ""),
    ("230", "A", "Agrícola Wehrmann Ltda", "Agrícola Wehrmann Ltda", "35.563.152/0001-87"),
    ("231", "A", "Adriano Kitagawa; Alexandre Kitagawa; Marcelo Kitagawa", "Adriano Kitagawa; Alexandre Kitagawa; Marcelo Kitagawa", ""),
    ("232", "A", "Santa Vitória Açúcar e Álcool Ltda. / Jalles", "USINA SANTA VITÓRIA", ""),
]

# ── Utilitários (sem Qt) ──────────────────────────────────────────────

def _safe_filename(name: str) -> str:
    """Sanitiza ``name`` para uso como nome de arquivo (mesma regra do Store)."""
    return re.sub(r'[<>:"/\\|?*]', "_", str(name)).strip() or "os"


def _write_json(path: Path, data: Any) -> None:
    """Grava ``data`` em ``path`` de forma atômica (tmp + replace)."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.replace(tmp, path)


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
    pref = _read_prefs_mother()
    if pref:
        return Path(pref)
    raise SystemExit(
        "Pasta-mãe não informada. Use --mother <pasta> ou defina a pasta-mãe "
        "no Gerenciador de Estrutura."
    )


# ── Lógica de seed ────────────────────────────────────────────────────

def _build_entries() -> Dict[str, List[Dict[str, str]]]:
    """Agrupa as linhas por OS, montando as SubOS via modelo de domínio."""
    by_os: Dict[str, List[Dict[str, str]]] = {}
    for os_number, sub_code, cliente, comercial, cnpj in RAW_ROWS:
        sub_os = SubOS(
            code=sub_code,
            name=cliente,
            commercial_name=comercial,
            document=cnpj,
        )
        by_os.setdefault(os_number, []).append({
            "sub_os": sub_os.code,
            "client": sub_os.name,
            "commercial_name": sub_os.commercial_name,
            "cnpj": sub_os.document,
        })
    return by_os


def _find_record(projects: List[Dict[str, Any]], os_number: str) -> Dict[str, Any] | None:
    """Encontra o registro da OS (número normalizado — exata ou prefixo)."""
    for record in projects:
        if ProjectStructureUtil.normalize_os(str(record.get("os", ""))) == os_number:
            return record
    for record in projects:
        key = ProjectStructureUtil.normalize_os(str(record.get("os", "")))
        if key.startswith(f"{os_number}_"):
            return record
    return None


def _merge_sub_os(
    record: Dict[str, Any],
    categorias: List[Dict[str, str]],
    folders: Dict[str, Dict[str, Any]],
    now: str,
) -> None:
    """Mescla cliente/nome comercial/CNPJ e os dados de pasta em cada SubOS.

    Preserva ``path``/``folders``/``years`` já gravados pela varredura e aplica
    os dados de pasta encontrados em disco quando a letra da SubOS bate.
    """
    existing = {
        str(entry.get("sub_os", "")): entry
        for entry in record.get("sub_os", []) if isinstance(entry, dict)
    }
    merged: List[Dict[str, Any]] = []
    seen: set = set()
    for categoria in categorias:
        letter = categoria["sub_os"]
        prev = existing.get(letter, {})
        scan = folders.get(letter, {})
        merged.append({
            "sub_os": letter,
            "path": scan.get("path", prev.get("path", "")),
            "folders": scan.get("folders", prev.get("folders", [])),
            "years": scan.get("years", prev.get("years", [])),
            "client": categoria["client"],
            "commercial_name": categoria["commercial_name"],
            "cnpj": categoria["cnpj"],
        })
        seen.add(letter)
    for letter, scan in folders.items():
        if letter in seen:
            continue
        merged.append({
            "sub_os": letter,
            "path": scan.get("path", ""),
            "folders": scan.get("folders", []),
            "years": scan.get("years", []),
            "client": "",
            "commercial_name": "",
            "cnpj": "",
        })
        seen.add(letter)
    for letter, prev in existing.items():
        if letter not in seen:
            merged.append(prev)

    merged.sort(key=lambda entry: str(entry.get("sub_os", "")))
    record["sub_os"] = merged
    record["client"] = ""

    all_paths: List[str] = []
    all_folders: List[str] = []
    all_years: List[str] = []
    for data in folders.values():
        path = str(data.get("path", ""))
        if path and path not in all_paths:
            all_paths.append(path)
        for name in data.get("folders", []):
            if name not in all_folders:
                all_folders.append(name)
        for year in data.get("years", []):
            if year not in all_years:
                all_years.append(year)
    if all_paths:
        record["paths"] = all_paths
        record["path"] = all_paths[0]
    else:
        record.setdefault("paths", [])
    if all_folders:
        record["folders"] = [
            name for name in ProjectStructureUtil.DEFAULT_PROJECT_FOLDERS
            if name in all_folders
        ]
    if all_years:
        record["years"] = all_years
    record["updated_at"] = now


def _scan_folders(mother: Path) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Varre a pasta-mãe: ``{numero_os: {subos: {path, folders, years}}}``."""
    result: Dict[str, Dict[str, Dict[str, Any]]] = {}
    by_os = ProjectStructureUtil.group_projects_by_os(
        ProjectStructureUtil.discover_projects(mother)
    )
    for number, paths in by_os.items():
        letters = ProjectStructureUtil.assign_sub_os_letters(paths)
        for path in paths:
            letter = letters.get(path, "")
            data = ProjectStructureUtil.collect_created_data(path)
            result.setdefault(number, {})[letter] = {
                "path": str(path),
                "folders": data["folders"],
                "years": data["years"],
            }
    return result


def _apply(mother: Path, dry_run: bool) -> None:
    """Aplica a categorização ao banco (``.BancoDados``)."""
    entries = _build_entries()
    scan = _scan_folders(mother)
    db_dir = mother / DB_FOLDER
    consolidated_path = db_dir / CONSOLIDATED_FILENAME

    consolidated: Dict[str, Any] = {}
    if consolidated_path.is_file():
        consolidated = json.loads(consolidated_path.read_text(encoding="utf-8"))
    projects = consolidated.get("projects", [])
    if not isinstance(projects, list):
        projects = []

    now = datetime.now().isoformat(timespec="seconds")
    created = 0
    updated = 0
    touched: List[Dict[str, Any]] = []

    for os_number in sorted(entries, key=int):
        categorias = entries[os_number]
        record = _find_record(projects, os_number)
        if record is None:
            record = {
                "os": os_number,
                "name": "",
                "client": "",
                "path": "",
                "paths": [],
                "folders": [],
                "years": [],
                "sub_os": [],
                "updated_at": now,
            }
            projects.append(record)
            created += 1
        else:
            updated += 1
        _merge_sub_os(record, categorias, scan.get(os_number, {}), now)
        touched.append(record)

    consolidated["projects"] = projects
    consolidated.setdefault("db_schema", 1)
    consolidated["mother_folder"] = str(mother)
    consolidated["total_projects"] = len(projects)
    consolidated["generated_at"] = now

    total_sub_os = sum(len(value) for value in entries.values())
    print(f"Pasta-mãe : {mother}")
    print(f"Banco     : {db_dir}")
    print(f"OS        : {len(entries)} ({created} criada(s), {updated} atualizada(s))")
    print(f"SubOS     : {total_sub_os}")

    if dry_run:
        print("[dry-run] Nada foi gravado.")
        return

    db_dir.mkdir(parents=True, exist_ok=True)
    for record in touched:
        filename = _safe_filename(str(record.get("os", "os"))) + ".json"
        _write_json(db_dir / filename, record)
    _write_json(consolidated_path, consolidated)
    print("Gravado com sucesso.")


def _push_to_cloud(mother: Path) -> None:
    """Espelha o ``.BancoDados`` no Firestore (coleção ``banco_dados``)."""
    from core.enum.ToolKey import ToolKey
    from core.firebase.CloudDatabaseSync import CloudDatabaseSync
    from core.firebase.FirebaseTokenProvider import FirebaseTokenProvider

    if not FirebaseTokenProvider.has_credentials():
        print(
            "Push ignorado: sem credenciais Firebase (conta de serviço ou login)."
        )
        return

    db_dir = mother / DB_FOLDER
    result = CloudDatabaseSync.push(
        str(db_dir), "banco_dados", tool_key=ToolKey.PROJECT_DATABASE.value
    )
    pushed = result.get("pushed", 0)
    failed = result.get("failed", 0)
    print(f"Firebase  : {pushed} documento(s) enviado(s), {failed} falha(s)")


def main() -> None:
    """Ponto de entrada do script de seed."""
    parser = argparse.ArgumentParser(
        description="DEV: popula o banco com a categorização OS/SubOS.",
    )
    parser.add_argument(
        "--mother", default="", help="Pasta-mãe (contém a pasta .BancoDados).",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Não grava; apenas mostra o resumo.",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Após gravar, espelha o .BancoDados no Firestore (banco_dados).",
    )
    args = parser.parse_args()

    mother = _resolve_mother(args.mother)
    if not mother.exists():
        raise SystemExit(f"Pasta-mãe inexistente: {mother}")
    _apply(mother, args.dry_run)
    if args.push and not args.dry_run:
        _push_to_cloud(mother)


if __name__ == "__main__":
    main()

