# -*- coding: utf-8 -*-
"""
LimitesService — Regras de negócio da Base de Limites
=====================================================
Importa vetores (SHP, GPKG, KML, KMZ, GeoJSON) para a base de limites:

    <BASE_DADOS>/limites/limites.shp                       → completão (todas as OS)
    <BASE_DADOS>/limites/<OS>/<OS>_limites.shp             → um arquivo por OS
    <pasta da SubOS>/08_LIMITES/TALHOES/<OS>_limites.shp   → cópia no projeto

Regras de negócio:
- TALHÃO é obrigatório (sempre vem de um campo do vetor).
- FAZENDA e OS são obrigatórios (campo mapeado OU valor manual).
- SUB_OS é ``A`` por padrão; aceita campo mapeado ou valor manual (letra única).
- AREA_HA é CALCULADA em hectares; AREA_INF guarda a área informada (opcional).
- A chave ``OS-FAZENDA-TALHÃO`` é única; quando a SubOS NÃO é ``A`` ela recebe o
  sufixo ``-<SubOS>`` (ex.: ``39-FAZ_X-P3-B``), permitindo o mesmo talhão em
  SubOS diferentes. Duplicidade BLOQUEIA a importação.
- Divergência entre área informada e calculada apenas ALERTA (tolerância em %).
- Depois de gravar, cada OS/SubOS ganha a cópia no projeto e o registro
  ``limites`` na SubOS do banco (via ``CloudProjectDatabase`` — Contrato 28).

A leitura/escrita vetorial é delegada para ``utils.vector`` (Contrato 25).
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
from PySide6.QtCore import QObject, QRunnable, Signal

from core.enum.ToolKey import ToolKey
from core.firebase.CloudProjectDatabase import CloudProjectDatabase
from utils.BaseUtil import BaseUtil
from utils.Preferences import Preferences
from utils.ProjectStructureUtil import ProjectStructureUtil
from utils.vector.VectorLayerMetrics import VectorLayerMetrics
from utils.vector.VectorLayerSource import VectorLayerSource

_TOOL_KEY = ToolKey.LIMITES_DB.value

BASE_ROOT = (
    r"C:\Users\MatheusMartinelli\OneDrive - Agrorobotica Fotonica Em Certificacoes "
    r"Agroambientais\BASE_DADOS\limites"
)
CONSOLIDATED_FILENAME = "limites.shp"
OS_FILE_SUFFIX = "_limites"
DEFAULT_SUB_OS = "A"
DEFAULT_TOLERANCE_PCT = 1.0

# Estrutura Verra: <projeto da SubOS>/08_LIMITES/TALHOES/<OS>_limites.shp
LIMITES_FOLDER = "08_LIMITES"
TALHOES_FOLDER = "TALHOES"

FIELD_TALHAO = "TALHAO"
FIELD_FAZENDA = "FAZENDA"
FIELD_OS = "OS"
FIELD_SUB_OS = "SUB_OS"
FIELD_CLIENTE = "CLIENTE"
FIELD_KEY = "KEY"
FIELD_AREA_CALC = "AREA_HA"
FIELD_AREA_INF = "AREA_INF"

OUTPUT_FIELDS = [
    FIELD_TALHAO,
    FIELD_FAZENDA,
    FIELD_OS,
    FIELD_SUB_OS,
    FIELD_CLIENTE,
    FIELD_KEY,
    FIELD_AREA_CALC,
    FIELD_AREA_INF,
]

PREPARE_FIELDS = [field for field in OUTPUT_FIELDS if field != FIELD_AREA_CALC]

SEMANTIC_KEYS = ("talhao", "fazenda", "os", "subos", "cliente", "area")

GUESS_TOKENS = {
    "talhao": ("TALHAO", "TALH"),
    "fazenda": ("FAZENDA", "PROPRIEDADE"),
    "os": ("OS", "ORDEM"),
    "subos": ("SUBOS", "SUB_OS", "SUB"),
    "cliente": ("CLIENTE",),
    "area": ("AREA",),
}


@dataclass
class LimitesImportConfig:
    """Configuração de uma importação da Base de Limites."""

    vector_path: str
    field_map: Dict[str, str] = field(default_factory=dict)
    manual: Dict[str, str] = field(default_factory=dict)
    tolerance_pct: float = DEFAULT_TOLERANCE_PCT
    output_root: str = BASE_ROOT


class LimitesValidationError(Exception):
    """Importação bloqueada por problemas de validação."""

    def __init__(self, problems: List[str]) -> None:
        self.problems = problems
        super().__init__(f"{len(problems)} problema(s) de validação")


class LimitesService(BaseUtil):
    """Regras de negócio, validação e escrita da base de limites."""

    # ── Inspeção ─────────────────────────────────────────────────────

    @classmethod
    def inspect(cls, path: str) -> Dict[str, Any]:
        """Lê o vetor e devolve campos, CRS, contagem e tipos de geometria."""
        logger = cls._get_logger(_TOOL_KEY, "LimitesService")

        gdf = VectorLayerSource.read_geodataframe(path, tool_key=_TOOL_KEY)
        geom_types = sorted({str(item) for item in gdf.geom_type.dropna().unique()})

        payload: Dict[str, Any] = {
            "path": path,
            "count": int(len(gdf)),
            "crs": str(gdf.crs) if gdf.crs is not None else "",
            "geometry": ", ".join(geom_types),
            "fields": VectorLayerSource.list_fields(gdf),
        }

        logger.info(
            "Vetor inspecionado",
            code="LIM_INSPECT",
            path=path,
            n_features=payload["count"],
        )
        return payload

    # ── Normalização ────────────────────────────────────────────────

    @staticmethod
    def normalize_text(value: Any) -> str:
        """Remove acentos, troca espaços por ``_`` e devolve em MAIÚSCULAS."""
        text = "" if value is None else str(value)
        if text.strip().lower() in ("", "nan", "none", "<na>", "nat"):
            return ""

        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        text = re.sub(r"\s+", "_", text.strip())
        return text.upper().strip("_")

    @staticmethod
    def normalize_os(value: Any) -> Optional[int]:
        """Converte o valor da OS em inteiro (aceita ``039``, ``OS 39`` e ``39.0``)."""
        text = "" if value is None else str(value).strip()
        if text.lower() in ("", "nan", "none", "<na>"):
            return None

        if re.fullmatch(r"\d+\.0+", text):
            text = text.split(".")[0]

        digits = re.sub(r"\D", "", text)
        return int(digits) if digits else None

    @staticmethod
    def normalize_sub_os(value: Any) -> str:
        """Normaliza a SubOS; devolve ``A`` quando o valor está vazio."""
        text = LimitesService.normalize_text(value)
        return text or DEFAULT_SUB_OS

    @staticmethod
    def parse_float(value: Any) -> Optional[float]:
        """Converte área em float, aceitando vírgula decimal."""
        text = "" if value is None else str(value).strip()
        if text.lower() in ("", "nan", "none", "<na>"):
            return None

        if "," in text:
            text = text.replace(".", "").replace(",", ".")

        try:
            return float(text)
        except ValueError:
            return None

    @classmethod
    def guess_field(cls, fields: List[str], key: str) -> str:
        """
        Sugere o campo do vetor para uma chave semântica (heurística simples).

        Usada apenas para pré-selecionar os combos da UI — o usuário confirma.
        """
        tokens = GUESS_TOKENS.get(key, ())

        for field in fields:
            normalized = cls.normalize_text(field)
            parts = re.split(r"[^A-Z0-9]+", normalized)

            for token in tokens:
                if token == "OS":
                    if "OS" in parts or normalized.endswith("_OS"):
                        return field
                elif token in normalized:
                    return field

            if key == "fazenda" and normalized.startswith("FAZ"):
                return field

        return ""

    @staticmethod
    def guess_os_from_path(path: str) -> str:
        """
        Identifica o número da OS no caminho de origem (vazio quando não há padrão).

        Prioridade:
          1. pasta ``OS_<numero>...`` mais próxima do arquivo
             (ex.: ``OS_210_EDUARDO_ZAGO_BB``);
          2. prefixo do arquivo ``P<numero>`` (ex.: ``P210_001_01_FAZ_...``);
          3. token ``OS_<numero>`` no nome do arquivo.
        """
        if not path:
            return ""

        candidate = Path(path)

        for folder in candidate.parents:
            match = re.search(
                r"(?:^|[_\-\s])OS[_\-\s]?(\d{1,6})(?=\D|$)",
                folder.name,
                re.IGNORECASE,
            )
            if match:
                return ProjectStructureUtil.normalize_os(match.group(1))

        stem = candidate.stem
        match = re.match(r"^P(\d{1,6})(?=\D|$)", stem, re.IGNORECASE)
        if match:
            return ProjectStructureUtil.normalize_os(match.group(1))

        match = re.search(
            r"(?:^|[_\-\s])OS[_\-\s]?(\d{1,6})(?=\D|$)",
            stem,
            re.IGNORECASE,
        )
        if match:
            return ProjectStructureUtil.normalize_os(match.group(1))

        return ""

    # ── Importação ──────────────────────────────────────────────────

    @classmethod
    def import_file(
        cls,
        config: LimitesImportConfig,
        dry_run: bool = False,
        progress_cb: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Valida e (quando ``dry_run=False``) grava o vetor na base de limites.

        Args:
            config: Configuração da importação.
            dry_run: True apenas valida (nada é gravado).
            progress_cb: Callback ``(pct, mensagem)`` de progresso.

        Returns:
            Dicionário com o resumo da operação.

        Raises:
            LimitesValidationError: Problemas que bloqueiam a importação.
            ValueError: Falhas de leitura/área (CRS ausente, geometria inválida).
        """
        logger = cls._get_logger(_TOOL_KEY, "LimitesService")
        cls._notify(progress_cb, 5, "Lendo vetor...")

        gdf = VectorLayerSource.read_geodataframe(config.vector_path, tool_key=_TOOL_KEY)
        if gdf.crs is None:
            raise LimitesValidationError(
                ["O vetor não possui CRS definido. Defina a projeção do arquivo antes de importar."]
            )

        cls._notify(progress_cb, 25, "Validando atributos...")
        prepared = cls._prepare(gdf, config)
        warnings: List[str] = []

        cls._notify(progress_cb, 55, "Calculando área...")
        prepared = VectorLayerMetrics.calculate_area_hectares(
            prepared, FIELD_AREA_CALC, 4, _TOOL_KEY
        )
        prepared = prepared[OUTPUT_FIELDS + [prepared.geometry.name]]
        warnings.extend(cls._area_warnings(prepared, config.tolerance_pct))

        cls._notify(progress_cb, 70, "Verificando duplicidades...")
        consolidated = os.path.join(config.output_root, CONSOLIDATED_FILENAME)
        cls._check_duplicates(prepared, consolidated)

        payload: Dict[str, Any] = {
            "dry_run": dry_run,
            "n_features": int(len(prepared)),
            "crs": str(prepared.crs),
            "total_ha": round(float(prepared[FIELD_AREA_CALC].sum()), 4),
            "os_numbers": sorted({int(value) for value in prepared[FIELD_OS]}),
            "sub_os": {
                str(key): int(value)
                for key, value in prepared[FIELD_SUB_OS].value_counts().items()
            },
            "consolidated": consolidated,
            "os_files": [],
            "copies": [],
            "db_updated": 0,
            "warnings": warnings,
        }

        if dry_run:
            warnings.extend(cls._structure_warnings(prepared))
            cls._notify(progress_cb, 100, "Validação concluída.")
            logger.info(
                "Validação da importação concluída",
                code="LIM_VALIDATE_OK",
                n_features=payload["n_features"],
                n_warnings=len(warnings),
            )
            return payload

        cls._notify(progress_cb, 85, "Gravando base...")
        cls._append_and_write(consolidated, prepared)

        os_files: List[str] = []
        for os_number, group in prepared.groupby(FIELD_OS, sort=True):
            os_dir = os.path.join(config.output_root, str(int(os_number)))
            target = os.path.join(os_dir, f"{int(os_number)}{OS_FILE_SUFFIX}.shp")
            cls._append_and_write(target, group)
            os_files.append(target)

        payload["os_files"] = os_files

        cls._notify(progress_cb, 92, "Copiando para os projetos...")
        cls._publish_to_projects(prepared, config, payload, logger)

        cls._notify(progress_cb, 100, "Importação concluída.")

        logger.info(
            "Importação concluída",
            code="LIM_IMPORT_DONE",
            n_features=payload["n_features"],
            n_os=len(os_files),
            n_copies=len(payload["copies"]),
            n_db_updated=payload["db_updated"],
            total_ha=payload["total_ha"],
            n_warnings=len(warnings),
            root=config.output_root,
        )
        return payload

    @classmethod
    def _prepare(
        cls,
        gdf: Any,
        config: LimitesImportConfig,
    ) -> Any:
        """Resolve os valores de cada feição e devolve o GeoDataFrame canônico."""
        columns = {key: cls._resolve_series(gdf, config, key) for key in SEMANTIC_KEYS}

        talhoes: List[str] = []
        fazendas: List[str] = []
        os_numbers: List[int] = []
        sub_os_list: List[str] = []
        clientes: List[str] = []
        areas: List[Optional[float]] = []
        keys: List[str] = []
        problems: List[str] = []

        for index in range(len(gdf)):
            label = f"Feição {index + 1}"

            talhao = cls.normalize_text(columns["talhao"][index])
            if not talhao:
                problems.append(f"{label}: TALHÃO vazio (obrigatório).")

            fazenda = cls.normalize_text(columns["fazenda"][index])
            if not fazenda:
                problems.append(f"{label}: FAZENDA vazia (obrigatória).")

            os_number = cls.normalize_os(columns["os"][index])
            if os_number is None:
                problems.append(f"{label}: OS vazia ou inválida (obrigatória).")

            sub_os = cls.normalize_sub_os(columns["subos"][index])
            if not re.fullmatch(r"[A-Z]", sub_os):
                problems.append(
                    f"{label}: SubOS '{sub_os}' inválida — informe uma única letra (ex.: A)."
                )

            area = cls.parse_float(columns["area"][index])
            if area is not None and area <= 0:
                area = None
            areas.append(area)
            talhoes.append(talhao)
            fazendas.append(fazenda)
            sub_os_list.append(sub_os)
            clientes.append(cls.normalize_text(columns["cliente"][index]))

            if os_number is None or not talhao or not fazenda:
                os_numbers.append(0)
                keys.append("")
                continue

            os_numbers.append(int(os_number))
            key = f"{int(os_number)}-{fazenda}-{talhao}"
            if sub_os != DEFAULT_SUB_OS:
                key = f"{key}-{sub_os}"
            keys.append(key)

        if problems:
            raise LimitesValidationError(cls._limit_problems(problems))

        prepared = gdf.copy()
        prepared[FIELD_TALHAO] = talhoes
        prepared[FIELD_FAZENDA] = fazendas
        prepared[FIELD_OS] = os_numbers
        prepared[FIELD_SUB_OS] = sub_os_list
        prepared[FIELD_CLIENTE] = clientes
        prepared[FIELD_AREA_INF] = pd.Series(areas, index=prepared.index, dtype="float64")
        prepared[FIELD_KEY] = keys
        return prepared[PREPARE_FIELDS + [prepared.geometry.name]]

    @staticmethod
    def _resolve_series(gdf: Any, config: LimitesImportConfig, key: str) -> List[Any]:
        """Valores de uma chave semântica: campo mapeado (prioridade) ou valor manual."""
        field_name = (config.field_map.get(key) or "").strip()
        if field_name and field_name in gdf.columns:
            return list(gdf[field_name])

        manual = (config.manual.get(key) or "").strip()
        return [manual] * len(gdf)

    # ── Verificações ────────────────────────────────────────────────

    @staticmethod
    def _area_warnings(gdf: Any, tolerance_pct: float) -> List[str]:
        """Compara a área informada com a calculada e devolve os avisos de divergência."""
        warnings: List[str] = []

        for _, row in gdf.iterrows():
            informed = row[FIELD_AREA_INF]
            if informed is None or pd.isna(informed):
                continue

            informed = float(informed)
            if informed <= 0:
                continue

            calculated = float(row[FIELD_AREA_CALC])
            key = str(row[FIELD_KEY])

            diff_pct = abs(calculated - informed) / informed * 100.0
            if diff_pct > tolerance_pct:
                warnings.append(
                    f"{key}: informada {informed:.2f} ha × calculada {calculated:.2f} ha "
                    f"(diferença {diff_pct:.1f}%)."
                )

        return warnings

    @classmethod
    def _check_duplicates(cls, gdf: Any, consolidated_path: str) -> None:
        """Bloqueia chaves repetidas no próprio arquivo ou já existentes na base."""
        existing = cls._load_keys(consolidated_path)
        problems: List[str] = []
        seen: set = set()

        sub_values = (
            gdf[FIELD_SUB_OS] if FIELD_SUB_OS in gdf.columns
            else [""] * len(gdf)
        )

        for key, sub_os in zip(gdf[FIELD_KEY], sub_values):
            key = str(key).strip()
            if not key:
                continue
            if key in seen:
                problems.append(f"{key}: duplicado dentro do próprio arquivo.")
                continue

            seen.add(key)
            if key in existing:
                problems.append(f"{key}: já existe na base (SubOS {existing[key]}).")

        if problems:
            raise LimitesValidationError(cls._limit_problems(problems))

    @classmethod
    def _load_keys(cls, consolidated_path: str) -> Dict[str, str]:
        """Lê as chaves já existentes no completão (vazio quando o arquivo não existe)."""
        if not os.path.exists(consolidated_path):
            return {}

        gdf = VectorLayerSource.read_geodataframe(consolidated_path, tool_key=_TOOL_KEY)
        if FIELD_KEY not in gdf.columns:
            return {}

        sub_values = (
            gdf[FIELD_SUB_OS] if FIELD_SUB_OS in gdf.columns
            else [""] * len(gdf)
        )

        keys: Dict[str, str] = {}
        for key, sub_os in zip(gdf[FIELD_KEY], sub_values):
            text = str(key).strip()
            if text:
                keys[text] = str(sub_os).strip()
        return keys

    # ── Escrita ─────────────────────────────────────────────────────

    @classmethod
    def _append_and_write(cls, target: str, new_gdf: Any) -> None:
        """Anexa o lote ao arquivo de destino (quando existe) e grava de forma atômica."""
        if os.path.exists(target):
            existing = VectorLayerSource.read_geodataframe(target, tool_key=_TOOL_KEY).copy()
            defaults = {
                FIELD_OS: 0,
                FIELD_AREA_CALC: 0.0,
                FIELD_AREA_INF: float("nan"),
            }
            for column in OUTPUT_FIELDS:
                if column not in existing.columns:
                    existing[column] = defaults.get(column, "")
            existing = existing[OUTPUT_FIELDS + [existing.geometry.name]]
            merged = VectorLayerSource.concat_geodataframes(existing, new_gdf, tool_key=_TOOL_KEY)
            merged = merged[OUTPUT_FIELDS + [merged.geometry.name]]
        else:
            merged = new_gdf

        VectorLayerSource.write_geodataframe_atomic(merged, target, tool_key=_TOOL_KEY)

    # ── Estrutura do projeto (Verra) + banco ────────────────────────

    @classmethod
    def _publish_to_projects(
        cls,
        prepared: Any,
        config: LimitesImportConfig,
        payload: Dict[str, Any],
        logger: Any,
    ) -> None:
        """Copia os limites para ``<projeto da SubOS>/08_LIMITES/TALHOES`` e registra no banco."""
        warnings: List[str] = payload["warnings"]

        mother = cls._load_mother_folder()
        if mother is None:
            warnings.append(
                "Pasta-mãe não configurada no Gerenciador de Estrutura — a cópia em "
                f"{LIMITES_FOLDER}/{TALHOES_FOLDER} não foi gerada."
            )
            return

        projects_by_os = ProjectStructureUtil.group_projects_by_os(
            ProjectStructureUtil.discover_projects(mother, tool_key=_TOOL_KEY)
        )
        records: Dict[str, Optional[Dict[str, Any]]] = {}

        for (os_number, sub_os), group in prepared.groupby(
            [FIELD_OS, FIELD_SUB_OS], sort=True
        ):
            number = str(int(os_number))
            letter = str(sub_os)

            if number not in records:
                records[number] = cls._load_order(number, logger)
            record = records[number]

            folder, reason = cls._find_sub_os_folder(
                mother, record, number, letter, projects_by_os
            )
            if folder is None:
                warnings.append(
                    f"OS {number} · SubOS {letter}: {reason} — cópia no projeto não gerada."
                )
                continue

            try:
                copy_path = cls._write_project_copy(folder, number, group)
            except Exception as e:
                logger.error(
                    "Falha ao gravar a copia no projeto",
                    code="LIM_COPY_ERR",
                    path=str(folder),
                    error=str(e),
                )
                warnings.append(
                    f"OS {number} · SubOS {letter}: falha ao gravar a cópia no projeto ({e})."
                )
                continue

            payload["copies"].append(str(copy_path))

            if record is None:
                warnings.append(
                    f"OS {number} · SubOS {letter}: OS não encontrada no banco — "
                    "o limite não foi registrado."
                )
                continue

            if cls._register_limits(mother, record, letter, copy_path, group, config):
                payload["db_updated"] += 1
            else:
                warnings.append(
                    f"OS {number} · SubOS {letter}: falha ao registrar o limite no banco."
                )

    @classmethod
    def _structure_warnings(cls, prepared: Any) -> List[str]:
        """Antes de gravar, avisa sobre projetos/SubOS que não receberão a cópia."""
        mother = cls._load_mother_folder()
        if mother is None:
            return [
                "Pasta-mãe não configurada no Gerenciador de Estrutura — a cópia em "
                f"{LIMITES_FOLDER}/{TALHOES_FOLDER} não será gerada."
            ]

        projects_by_os = ProjectStructureUtil.group_projects_by_os(
            ProjectStructureUtil.discover_projects(mother, tool_key=_TOOL_KEY)
        )
        warnings: List[str] = []
        pairs = prepared[[FIELD_OS, FIELD_SUB_OS]].drop_duplicates()

        for os_number, sub_os in pairs.itertuples(index=False, name=None):
            number = str(int(os_number))
            letter = str(sub_os)
            folder, reason = cls._find_sub_os_folder(
                mother, None, number, letter, projects_by_os
            )
            if folder is None:
                warnings.append(f"OS {number} · SubOS {letter}: {reason}.")

        return warnings

    @classmethod
    def _find_sub_os_folder(
        cls,
        mother: Path,
        record: Optional[Dict[str, Any]],
        os_number: str,
        sub_os: str,
        projects_by_os: Dict[str, List[Path]],
    ) -> Tuple[Optional[Path], str]:
        """Localiza a pasta do projeto da SubOS (banco primeiro, disco como fallback)."""
        if record:
            for entry in record.get("sub_os", []) or []:
                if not isinstance(entry, dict):
                    continue
                if str(entry.get("sub_os", "")) != sub_os:
                    continue
                rel = str(entry.get("path", "") or "")
                if rel:
                    folder = ProjectStructureUtil.resolve_path(mother, rel)
                    if folder.is_dir():
                        return folder, ""
                break

        candidates = projects_by_os.get(
            ProjectStructureUtil.normalize_os(os_number), []
        )

        for folder in candidates:
            if ProjectStructureUtil.extract_sub_os(folder.name) == sub_os:
                return folder, ""

        if sub_os == DEFAULT_SUB_OS:
            without_letter = [
                folder for folder in candidates
                if not ProjectStructureUtil.extract_sub_os(folder.name)
            ]
            if len(without_letter) == 1:
                return without_letter[0], ""

        letters = ProjectStructureUtil.assign_sub_os_letters(candidates)
        for folder, letter in letters.items():
            if letter == sub_os:
                return folder, ""

        return None, f"pasta da SubOS {sub_os} não encontrada em {mother}"

    @classmethod
    def _write_project_copy(cls, project_folder: Path, os_number: str, group: Any) -> Path:
        """Grava a cópia do limite em ``<projeto>/08_LIMITES/TALHOES/<OS>_limites.shp``."""
        target = (
            project_folder / LIMITES_FOLDER / TALHOES_FOLDER
            / f"{os_number}{OS_FILE_SUFFIX}.shp"
        )
        cls._append_and_write(str(target), group)
        return target

    @classmethod
    def _register_limits(
        cls,
        mother: Path,
        record: Dict[str, Any],
        sub_os: str,
        file_path: Path,
        group: Any,
        config: LimitesImportConfig,
    ) -> bool:
        """Marca na SubOS do banco que o limite foi inserido (Firestore + backup JSON)."""
        entries = [
            entry for entry in record.get("sub_os", []) or []
            if isinstance(entry, dict)
        ]
        entry = next(
            (item for item in entries if str(item.get("sub_os", "")) == sub_os),
            None,
        )
        if entry is None:
            entry = {"sub_os": sub_os}
            entries.append(entry)
            entries.sort(key=lambda item: str(item.get("sub_os", "")))
            record["sub_os"] = entries

        entry["limites"] = {
            "inserted_at": datetime.now().isoformat(timespec="seconds"),
            "file": ProjectStructureUtil.to_relative_path(mother, file_path),
            "source": os.path.basename(config.vector_path),
            "features": int(len(group)),
            "area_ha": round(float(group[FIELD_AREA_CALC].sum()), 4),
        }

        try:
            return CloudProjectDatabase.save_order(
                record, mother=str(mother), tool_key=_TOOL_KEY
            )
        except Exception as e:
            cls._get_logger(_TOOL_KEY, "LimitesService").error(
                "Falha ao registrar o limite no banco",
                code="LIM_DB_SAVE_ERR",
                os_number=str(record.get("os", "")),
                sub_os=sub_os,
                error=str(e),
            )
            return False

    @staticmethod
    def _load_order(number: str, logger: Any) -> Optional[Dict[str, Any]]:
        """Lê o registro da OS no banco oficial (``None`` quando não existe/offline)."""
        try:
            return CloudProjectDatabase.get_order(number, tool_key=_TOOL_KEY)
        except Exception as e:
            logger.warning(
                "Falha ao consultar a OS no banco",
                code="LIM_DB_READ_ERR",
                os_number=number,
                error=str(e),
            )
            return None

    @staticmethod
    def _load_mother_folder() -> Optional[Path]:
        """Pasta-mãe dos projetos (configurada no Gerenciador de Estrutura)."""
        prefs = Preferences.load_tool_prefs(
            ToolKey.PROJECT_STRUCTURE,
            caller_tool_key=_TOOL_KEY,
        )
        raw = str(prefs.get("mother_folder", "") or "").strip()
        if not raw:
            return None

        path = Path(raw)
        return path if path.is_dir() else None

    # ── Utilidades ──────────────────────────────────────────────────

    @staticmethod
    def _notify(
        progress_cb: Optional[Callable[[int, str], None]],
        pct: int,
        message: str,
    ) -> None:
        """Repassa o progresso quando existe callback."""
        if progress_cb is not None:
            progress_cb(pct, message)

    @staticmethod
    def _limit_problems(problems: List[str], limit: int = 12) -> List[str]:
        """Limita a lista de problemas exibida ao usuário."""
        if len(problems) <= limit:
            return problems
        return problems[:limit] + [f"... e mais {len(problems) - limit} problema(s)."]


class _LimitesSignals(QObject):
    """Sinais compartilhados pelos workers da Base de Limites."""

    progress = Signal(int, int, str)   # (generation, pct, mensagem)
    finished = Signal(int, object)     # (generation, payload)
    invalid = Signal(int, list)        # (generation, problemas)
    failed = Signal(int, str)          # (generation, erro)


class LimitesInspectWorker(QRunnable):
    """Lê o vetor e devolve campos/CRS/contagem em background (sem tocar em widgets)."""

    def __init__(self, generation: int, path: str) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.path = path
        self.signals = _LimitesSignals()

    def run(self) -> None:
        """Executa a inspeção e emite o resultado."""
        try:
            payload = LimitesService.inspect(self.path)
            self.signals.finished.emit(self.generation, payload)
        except Exception as e:
            LimitesService._get_logger(_TOOL_KEY, "LimitesInspectWorker").error(
                "Falha ao inspecionar vetor",
                code="LIM_INSPECT_ERR",
                path=self.path,
                error=str(e),
            )
            self.signals.failed.emit(self.generation, str(e))


class LimitesImportWorker(QRunnable):
    """Executa a validação/importação em background (sem tocar em widgets)."""

    def __init__(
        self,
        generation: int,
        config: LimitesImportConfig,
        dry_run: bool = False,
    ) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.config = config
        self.dry_run = dry_run
        self.signals = _LimitesSignals()

    def run(self) -> None:
        """Executa a importação e emite progresso/resultado."""
        try:
            def _progress(pct: int, message: str) -> None:
                self.signals.progress.emit(self.generation, int(pct), message)

            payload = LimitesService.import_file(
                self.config,
                dry_run=self.dry_run,
                progress_cb=_progress,
            )
            self.signals.finished.emit(self.generation, payload)
        except LimitesValidationError as e:
            self.signals.invalid.emit(self.generation, e.problems)
        except Exception as e:
            LimitesService._get_logger(_TOOL_KEY, "LimitesImportWorker").error(
                "Falha na importação de limites",
                code="LIM_IMPORT_ERR",
                path=self.config.vector_path,
                error=str(e),
            )
            self.signals.failed.emit(self.generation, str(e))

