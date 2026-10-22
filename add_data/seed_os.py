# -*- coding: utf-8 -*-
"""
seed_os.py — Script de DEV: cria/atualiza a BASE de OS existente no Firestore
============================================================================
Cria, DIRETO no Firebase (Cloud Firestore, coleção ``banco_dados``), a base de OS
já existente: um registro por OS com o cliente, o nome comercial, o CNPJ e a
PASTA associada (caminho RELATIVO à pasta-mãe — portável entre computadores).

A OS é **TEXTO** e pode conter **LETRA** (ex.: ``169A``, ``181C``): a letra é o
que diferencia as OS de um mesmo projeto, então cada OS tem o seu próprio
registro, a sua própria pasta e o seu próprio arquivo de limites.

O Firestore é a fonte oficial; os backups JSON são gerados pela classe de banco
``CloudProjectDatabase``. O resto da operação (criar NOVAS OS) é responsabilidade
do sistema, via a ferramenta Acompanhamento de OS.

Este script é SOMENTE PARA DESENVOLVIMENTO (seed inicial da base).

USO:
    python add_data/seed_os.py                      # usa a pasta-mãe da preferência
    python add_data/seed_os.py --mother "C:/pasta"  # pasta-mãe explícita
    python add_data/seed_os.py --dry-run            # só mostra o resumo, não envia

Como a pasta-mãe é resolvida (nesta ordem):
    1. Argumento --mother
    2. Variável de ambiente AETHERIS_MOTHER_FOLDER
    3. Preferência ProjectStructure.mother_folder (config/<APP_SLUG>_preferences.json)

O que é gravado (no Firestore, via CloudProjectDatabase):
    - ``<os>``            (um documento por OS)
    - ``banco_dados``     (documento consolidado)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Garante a raiz do projeto no sys.path (permite importar core.model).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# O console do Windows pode estar em cp1252: força a saída UTF-8 para o script
# poder imprimir acentos (o HomePlugin captura a saída como UTF-8).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.enum.ToolKey import ToolKey  # noqa: E402
from core.firebase.FirebaseTokenProvider import FirebaseTokenProvider  # noqa: E402
from core.firebase.CloudProjectDatabase import CloudProjectDatabase  # noqa: E402
from utils.ProjectStructureUtil import ProjectStructureUtil  # noqa: E402


# Coleção do Firestore (o Firestore é a fonte oficial do banco).
COLLECTION = "banco_dados"
_TOOL_KEY = ToolKey.PROJECT_DATABASE.value


# ── Dados de entrada: (OS, Cliente, Nome comercial, CNPJ) ─────────────
# A OS é a CHAVE do registro e é a MESMA chave do nome da pasta
# (``OS_<chave>_...``) — com a letra quando o projeto tem mais de uma.
RAW_ROWS: List[Tuple[str, str, str, str]] = [
    ("039", "Cornélio Adriano Sanders", "GRUPO PROGRESSO", ""),
    ("050", "SEMENTES TROPICAL", "OCP FERTILIZANTES LTDA", "18.105.959/0001-57"),
    ("053", "OCP FERTILIZANTES LTDA", "OCP FERTILIZANTES LTDA", "18.105.959/0001-57"),
    ("059", "Fazenda Dourada e Fazenda Pedra Dourada", "DOURADA COMERCIAL E AGROPECUARIA S.A", "05.027.654/0002-03"),
    ("068", "Agropecuária Rio da Areia Ltda. / Fazenda Santo Antônio do Paraíso", "AGROPECUARIA RIO DA AREIA LTDA", "02.149.159/0001-06"),
    ("119", "Elisa Agro Sustentável Ltda.", "MITRE AGRO", ""),
    ("131", "Usinas Itamarati S.A. / UISA", "UISA", ""),
    ("132", "FSL ANGUS", "", ""),
    ("133", "ZILOR", "", ""),
    ("140", "Caetano Polato / Fazenda Gravataí", "GRAVATAÍ AGRO", ""),
    ("141", "Marfrig Global Foods S.A.", "MARFIG (FAZ MARCO MOLINA)", ""),
    ("154", "Fetz Agropecuária Ltda.", "Fetz Agropecuária Ltda.", ""),
    ("160", "Itaquere", "Participações E Empreendimentos Rio Suia Ltda", "19.083.038/0001-01"),
    ("167", "GGF FAZENDAS LTDA", "GGF FAZENDAS LTDA", ""),

    # OS 169 é subdividida em 3 pastas no disco (169A/169B/169C).
    ("169A", "Agua Viva.", "AGUA VIVA", ""),
    ("169B", "Darro.", "DARRO", ""),
    ("169C", "Fazenda Pioneira Empreendimentos Agrícolas S.A.", "SLC AGRÍCOLA SA", ""),

    ("171", "Lida Agrícola Ltda. / Grupo Lida", "GRUPO LIDA", ""),
    ("179", "Guilherme Borges de Freitas", "Guilherme Borges de Freitas", ""),

    # OS 181 é subdividida em 3 pastas no disco (181A/181B/181C).
    ("181A", "Capricornio Renner", "GRUPO JCN", ""),
    ("181B", "Grupo Falavinha - Faz Almanaras", "GRUPO JCN", ""),
    ("181C", "Grupo Salazar - Faz Rio Alegre", "GRUPO JCN", ""),

    ("182", "SPM Holding e Administradora de Bens Ltda.", "Stradiotti", ""),
    ("183", "FADEL", "", ""),
    ("184", "AGROMANTOVA", "AGROMANTOVA", ""),
    ("186", "LAR COOPERATIVA", "LAR", ""),
    ("187", "José Carlos Costa Vidotti", "JOSÉ CARLOS COSTA VIDOTTI", ""),
    ("189", "Agropecuária Jatobá Ltda.", "THIAGO FABRIS", ""),
    ("190", "Egon Otto Rehn e outros / Grupo ER", "GRUPO ER", ""),
    ("191", "Marco Tulio Paolinelli Ltda.", "Marco Tulio Paolinelli Ltda.", ""),
    ("192", "Energética Santa Helena S.A.", "Energética Santa Helena S.A.", ""),
    ("196", "F L G AGRO E INVESTIMENTO LTDA", "F L G AGRO E INVESTIMENTO LTDA", ""),
    ("200", "Celso José Minozzo e Flavia Gabriela Minozzo", "Celso José Minozzo e Flavia Gabriela Minozzo", ""),
    ("201", "Flávia Bifon e Lúcia Helena Teixeira Bifon", "Flávia Bifon e Lúcia Helena Teixeira Bifon", ""),
    ("210", "Eduardo Zago Machado e outro", "Eduardo Zago Machado e outro", ""),
    ("211", "José Ricardo de Albuquerque Arruda Silva e Sílvia Morsoletto Tozetto", "José Ricardo de Albuquerque Arruda Silva e Sílvia Morsoletto Tozetto", ""),
    ("214", "Manoel Benedito Rosa Filho", "Manoel Benedito Rosa Filho", ""),
    ("215", "Agrigel Agropecuária Ltda.", "DIERBERGER  CITROS", ""),
    ("220", "Wanda Inês Riedi e Ivo Ilário Riedi", "Wanda Inês Riedi e Ivo Ilário Riedi", ""),
    ("221", "Sidnei Elvis Willms", "Sidnei Elvis Willms", ""),
    ("222", "Agropecuária Terras do Guaporé Ltda.", "Agropecuária Terras do Guaporé Ltda.", ""),
    ("225", "Hosana Luiz de Faria e Gisele Pereira Silva de Faria", "Hosana Luiz de Faria e Gisele Pereira Silva de Faria", ""),
    ("229", "Agropecuária Gado Bravo Ltda.", "GADO BRAVO", ""),
    ("230", "Agrícola Wehrmann Ltda", "Agrícola Wehrmann Ltda", "35.563.152/0001-87"),
    ("231", "Adriano Kitagawa; Alexandre Kitagawa; Marcelo Kitagawa", "Adriano Kitagawa; Alexandre Kitagawa; Marcelo Kitagawa", ""),
    ("232", "Santa Vitória Açúcar e Álcool Ltda. / Jalles", "USINA SANTA VITÓRIA", ""),

    # OS que existem em disco mas ainda NÃO têm cliente cadastrado — preencha
    # depois no Acompanhamento de OS (CRIAR OS com a MESMA chave mescla os dados).
    ("069", "", "", ""),
    ("127", "", "", ""),
    ("144", "", "", ""),
    ("302", "", "", ""),
    ("315", "", "", ""),
    ("393", "", "", ""),
]


# ── Utilitários (sem Qt) ──────────────────────────────────────────────

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


def _build_entries() -> Dict[str, Dict[str, str]]:
    """Monta ``{os: {client, commercial_name, cnpj}}`` a partir de ``RAW_ROWS``."""
    entries: Dict[str, Dict[str, str]] = {}
    for os_key, cliente, comercial, cnpj in RAW_ROWS:
        entries[ProjectStructureUtil.normalize_os(os_key)] = {
            "client": cliente,
            "commercial_name": comercial,
            "cnpj": cnpj,
        }
    return entries


def _find_record(
    projects: List[Dict[str, Any]], os_key: str
) -> Dict[str, Any] | None:
    """Encontra o registro da OS pela chave (comparação normalizada)."""
    key = ProjectStructureUtil.normalize_os(os_key)
    for record in projects:
        if ProjectStructureUtil.normalize_os(str(record.get("os", ""))) == key:
            return record
    return None


def _scan_folders(mother: Path) -> Dict[str, Dict[str, Any]]:
    """Varre a pasta-mãe: ``{os: {path, folders, years}}`` (uma pasta = uma OS)."""
    result: Dict[str, Dict[str, Any]] = {}
    for path in ProjectStructureUtil.discover_projects(mother):
        os_key = ProjectStructureUtil.extract_os(path.name)
        if not os_key:
            continue
        data = ProjectStructureUtil.collect_created_data(path)
        result[os_key] = {
            "path": ProjectStructureUtil.to_relative_path(mother, path),
            "folders": data["folders"],
            "years": data["years"],
        }
    return result


def _load_cloud_projects() -> List[Dict[str, Any]]:
    """Lê os registros de OS já existentes na fonte oficial (Firebase).

    O consolidado é ignorado (é apenas um snapshot). A leitura passa pela
    classe de banco CloudProjectDatabase (nunca pelo JSON local).
    """
    return CloudProjectDatabase.load_orders(tool_key=_TOOL_KEY)


def _write_to_cloud(
    mother: Path, touched: List[Dict[str, Any]], projects: List[Dict[str, Any]]
) -> None:
    """Grava cada OS + o consolidado via classe de banco (Firestore + JSON backup)."""
    saved = 0
    failed = 0
    for record in touched:
        ok = CloudProjectDatabase.save_order(
            record, mother=str(mother), tool_key=_TOOL_KEY
        )
        if ok:
            saved += 1
        else:
            failed += 1
    CloudProjectDatabase.rebuild_consolidated(
        projects, mother=str(mother), tool_key=_TOOL_KEY
    )
    print(f"Firebase  : {saved} documento(s) enviado(s), {failed} falha(s)")


def _merge_record(
    record: Dict[str, Any],
    categoria: Dict[str, str],
    scan: Dict[str, Any],
    now: str,
) -> None:
    """Mescla cliente/nome comercial/CNPJ e os dados da pasta no registro da OS.

    O que não foi semeado é PRESERVADO (o registro é atualizado, não recriado) e o
    caminho/pastas/anos só são sobrescritos quando a pasta existe em disco.
    """
    record.setdefault("name", "")
    record.setdefault("path", "")
    record.setdefault("folders", [])
    record.setdefault("years", [])
    record["client"] = categoria["client"] or record.get("client", "")
    record["commercial_name"] = (
        categoria["commercial_name"] or record.get("commercial_name", "")
    )
    record["cnpj"] = categoria["cnpj"] or record.get("cnpj", "")
    if scan:
        record["path"] = scan["path"]
        record["folders"] = scan["folders"]
        record["years"] = scan["years"]
    record["updated_at"] = now


def _apply(mother: Path, dry_run: bool) -> None:
    """Cria/atualiza a base de OS existente (OS + cliente + pasta) no Firestore."""
    entries = _build_entries()
    scan = _scan_folders(mother)
    now = datetime.now().isoformat(timespec="seconds")

    projects = [] if dry_run else _load_cloud_projects()
    created = 0
    updated = 0
    without_folder: List[str] = []
    touched: List[Dict[str, Any]] = []

    for os_key in sorted(entries):
        categoria = entries[os_key]
        record = _find_record(projects, os_key)
        if record is None:
            record = {
                "os": os_key,
                "name": "",
                "path": "",
                "folders": [],
                "years": [],
                "updated_at": now,
            }
            projects.append(record)
            created += 1
        else:
            updated += 1
        folder = scan.get(os_key)
        if folder is None:
            without_folder.append(os_key)
        _merge_record(record, categoria, folder or {}, now)
        touched.append(record)

    print(f"Pasta-mãe : {mother}")
    print(f"Firestore : {COLLECTION}")
    print(f"OS        : {len(entries)} ({created} criada(s), {updated} atualizada(s))")
    if without_folder:
        print(f"Sem pasta : {', '.join(without_folder)}")

    if dry_run:
        print("[dry-run] Nada foi enviado ao Firebase.")
        return

    _write_to_cloud(mother, touched, projects)


def main() -> None:
    """Ponto de entrada do script de seed."""
    parser = argparse.ArgumentParser(
        description="DEV: semeia a base de OS direto no Firestore.",
    )
    parser.add_argument(
        "--mother", default="", help="Pasta-mãe (varredura das pastas de OS).",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Não envia; apenas mostra o resumo.",
    )
    args = parser.parse_args()

    mother = _resolve_mother(args.mother)
    if not mother.exists():
        raise SystemExit(f"Pasta-mãe inexistente: {mother}")
    if not args.dry_run and not FirebaseTokenProvider.has_credentials():
        raise SystemExit(
            "Sem credenciais Firebase (conta de serviço ou login). "
            "Este script envia direto ao Firestore."
        )
    _apply(mother, args.dry_run)


if __name__ == "__main__":
    main()
