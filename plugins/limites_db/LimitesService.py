# -*- coding: utf-8 -*-
"""
LimitesService — Regras de negócio da Base de Limites e das Zonas de Manejo
==========================================================================
Importa vetores (SHP, GPKG, KML, KMZ, GeoJSON) em dois modos:

**Limites** (``MODE_LIMITES``):
    <BASE_DADOS>/limites/limites.shp                       → completão (todas as OS)
    <BASE_DADOS>/limites/<OS>/<OS>_limites.shp             → um arquivo por OS
    <pasta da OS>/08_LIMITES/TALHOES/<OS>_limites.shp      → cópia no projeto

**Zonas de Manejo** (``MODE_ZONAS``):
    <BASE_DADOS>/limites/zonas_manejo.shp                  → completão de zonas
    <BASE_DADOS>/limites/<OS>/<OS>_zonas_manejo.shp        → um arquivo por OS
    <pasta da OS>/13_ZONAS_DE_MANEJO/<OS>_zonas_manejo.shp

A OS é **TEXTO** e pode conter **LETRA** (ex.: ``169A``, ``181B``): a letra já
diferencia as OS de um mesmo projeto, então cada OS tem o seu próprio arquivo e a
sua própria pasta.

Regras de negócio (limites):
- TALHÃO é obrigatório (sempre vem de um campo do vetor).
- FAZENDA e OS são obrigatórios (campo mapeado OU valor manual).
- AREA_HA é CALCULADA em hectares; AREA_INF guarda a área informada (opcional).
- A chave ``OS-FAZENDA-TALHÃO`` é única (ex.: ``169A-FAZ_X-P3``); duplicidade
  BLOQUEIA a importação.
- Divergência entre área informada e calculada apenas ALERTA (tolerância em %).
- Depois de gravar, cada OS ganha a cópia no projeto e o registro ``limites`` na
  própria OS do banco (via ``CloudProjectDatabase`` — Contrato 28).

Regras de negócio (zonas de manejo):
- ZONA é obrigatória; FAZENDA e OS também (campo mapeado ou valor manual).
- TALHÃO é OPCIONAL e NÃO há regra de duplicidade.
- CAMPO (campo de manejo) é OPCIONAL: quando indicado — campo mapeado ou valor
  manual — ele CONSTA em todos os shapes gerados (completão, arquivo da OS na
  base e cópia no projeto); sem indicação a coluna existe, porém vazia.
- AREA_HA continua sendo CALCULADA em hectares.
- O registro vai para a chave ``zonas_manejo`` da OS.

Atualização (``ATUALIZAR``):
- Antes de gravar, a ferramenta procura os shapes que já existem (completão,
  arquivo da OS na base e cópia no projeto) e pergunta se devem ser substituídos.
- Na atualização, as feições das OS do vetor são REMOVIDAS dos arquivos de
  destino e trocadas pelo lote novo — as demais OS do arquivo ficam intactas — e
  a checagem de duplicidade é ignorada.

Validações do vetor (bloqueiam a operação — nada é gravado):
- **Shapefile completo**: exige ``.shp``, ``.shx`` e ``.dbf`` no mesmo diretório;
- **EPSG**: o padrão é ``EPSG:4326`` — qualquer outro CRS (ou sem ``.prj``) é
  bloqueado com orientação para reprojetar;
- **Somente polígonos**: geometrias ``Polygon``/``MultiPolygon`` — ponto, linha
  ou tipos mistos são bloqueados;
- **Geometria válida**: sem geometrias vazias/nulas, com anel fechado e sem
  auto-interseção (``is_valid``);
- **Feições**: o vetor não pode estar vazio.

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
DEFAULT_TOLERANCE_PCT = 1.0

# Padrões de entrada aceitos (validados antes de qualquer gravação)
DEFAULT_EPSG = 4326
POLYGON_TYPES = ("Polygon", "MultiPolygon")
SHP_SIDECARS = (".shp", ".shx", ".dbf")

MODE_LIMITES = "limites"
MODE_ZONAS = "zonas"

# Estrutura Verra:
#   <projeto>/08_LIMITES/TALHOES/<OS>_limites.shp
#   <projeto>/13_ZONAS_DE_MANEJO/<OS>_zonas_manejo.shp
LIMITES_FOLDER = "08_LIMITES"
TALHOES_FOLDER = "TALHOES"
ZONAS_FOLDER = "13_ZONAS_DE_MANEJO"

FIELD_TALHAO = "TALHAO"
FIELD_ZONA = "ZONA"
FIELD_CAMPO = "CAMPO"
FIELD_FAZENDA = "FAZENDA"
FIELD_OS = "OS"
FIELD_CLIENTE = "CLIENTE"
FIELD_KEY = "KEY"
FIELD_AREA_CALC = "AREA_HA"
FIELD_AREA_INF = "AREA_INF"

LIMITES_FIELDS = [
    FIELD_TALHAO,
    FIELD_FAZENDA,
    FIELD_OS,
    FIELD_CLIENTE,
    FIELD_KEY,
    FIELD_AREA_CALC,
    FIELD_AREA_INF,
]

ZONAS_FIELDS = [
    FIELD_ZONA,
    FIELD_CAMPO,
    FIELD_FAZENDA,
    FIELD_OS,
    FIELD_TALHAO,
    FIELD_CLIENTE,
    FIELD_AREA_CALC,
    FIELD_AREA_INF,
]

MODE_SETTINGS: Dict[str, Dict[str, Any]] = {
    MODE_LIMITES: {
        "label": "Limites",
        "consolidated": CONSOLIDATED_FILENAME,
        "os_suffix": OS_FILE_SUFFIX,
        "project_folder": LIMITES_FOLDER,
        "project_subfolder": TALHOES_FOLDER,
        "db_key": "limites",
        "fields": LIMITES_FIELDS,
        "semantic": ("talhao", "fazenda", "os", "cliente", "area"),
        "unique": True,
    },
    MODE_ZONAS: {
        "label": "Zonas de Manejo",
        "consolidated": "zonas_manejo.shp",
        "os_suffix": "_zonas_manejo",
        "project_folder": ZONAS_FOLDER,
        "project_subfolder": "",
        "db_key": "zonas_manejo",
        "fields": ZONAS_FIELDS,
        "semantic": ("zona", "campo", "fazenda", "os", "talhao", "cliente", "area"),
        "unique": False,
    },
}

GUESS_TOKENS = {
    "talhao": ("TALHAO", "TALH"),
    "zona": ("ZONA", "ZONE"),
    "campo": ("CAMPO",),
    "fazenda": ("FAZENDA", "PROPRIEDADE"),
    "os": ("OS", "ORDEM"),
    "cliente": ("CLIENTE",),
    "area": ("AREA",),
}


@dataclass
class LimitesImportConfig:
    """Configuração de uma importação (limites ou zonas de manejo)."""

    vector_path: str
    field_map: Dict[str, str] = field(default_factory=dict)
    manual: Dict[str, str] = field(default_factory=dict)
    tolerance_pct: float = DEFAULT_TOLERANCE_PCT
    output_root: str = BASE_ROOT
    mode: str = MODE_LIMITES
    update: bool = False


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
        """Lê o vetor e devolve campos, CRS, contagem, geometrias e problemas."""
        logger = cls._get_logger(_TOOL_KEY, "LimitesService")

        gdf = VectorLayerSource.read_geodataframe(path, tool_key=_TOOL_KEY)
        geom_types = sorted({str(item) for item in gdf.geom_type.dropna().unique()})

        payload: Dict[str, Any] = {
            "path": path,
            "count": int(len(gdf)),
            "crs": str(gdf.crs) if gdf.crs is not None else "",
            "geometry": ", ".join(geom_types),
            "fields": VectorLayerSource.list_fields(gdf),
            "problems": cls.vector_problems(path, gdf),
        }

        logger.info(
            "Vetor inspecionado",
            code="LIM_INSPECT",
            path=path,
            n_features=payload["count"],
            n_problems=len(payload["problems"]),
        )
        return payload

    # ── Validação do vetor ──────────────────────────────────────────

    @classmethod
    def vector_problems(cls, path: str, gdf: Any) -> List[str]:
        """Problemas do vetor que impedem a operação (shape, CRS e geometria)."""
        return cls._sidecar_problems(path) + cls._geometry_problems(gdf)

    @classmethod
    def validate_vector(cls, path: str, gdf: Any) -> None:
        """
        Bloqueia vetores fora do padrão antes de qualquer gravação.

        Regras: shapefile completo (``.shp``/``.shx``/``.dbf``), CRS
        ``EPSG:4326`` (padrão), apenas polígonos, geometrias válidas e vetor
        com pelo menos uma feição.

        Raises:
            LimitesValidationError: Vetor fora do padrão.
        """
        problems = cls.vector_problems(path, gdf)
        if problems:
            raise LimitesValidationError(cls._limit_problems(problems))

        cls._get_logger(_TOOL_KEY, "LimitesService").info(
            "Vetor validado (EPSG + polígonos + geometrias)",
            code="LIM_VECTOR_OK",
            path=path,
            n_features=int(len(gdf)),
            crs=str(gdf.crs),
        )

    @staticmethod
    def _sidecar_problems(path: str) -> List[str]:
        """Confere os arquivos obrigatórios do conjunto shapefile."""
        candidate = Path(path)
        if candidate.suffix.lower() != ".shp":
            return []

        stem = candidate.with_suffix("")
        missing = [
            ext for ext in SHP_SIDECARS if not Path(f"{stem}{ext}").is_file()
        ]
        if not missing:
            return []

        return [
            "Shapefile incompleto — faltando: "
            + ", ".join(missing)
            + ". Copie o conjunto inteiro (.shp, .shx, .dbf e .prj)."
        ]

    @staticmethod
    def _geometry_problems(gdf: Any) -> List[str]:
        """Confere CRS (padrão EPSG:4326), tipo de geometria e validade das feições."""
        problems: List[str] = []

        if len(gdf) == 0:
            return ["O vetor não possui feições (0 registros)."]

        crs = gdf.crs
        if crs is None:
            problems.append(
                f"Vetor sem CRS definido (sem .prj) — o padrão é EPSG:{DEFAULT_EPSG}."
            )
        elif crs.to_epsg() != DEFAULT_EPSG:
            name = getattr(crs, "name", "") or str(crs)
            problems.append(
                f"CRS atual: EPSG:{crs.to_epsg() or '?'} ({name}) — o padrão é "
                f"EPSG:{DEFAULT_EPSG}. Reprojete o vetor antes de importar."
            )

        for index, geometry in enumerate(gdf.geometry):
            label = f"Feição {index + 1}"

            if geometry is None or not hasattr(geometry, "geom_type"):
                problems.append(f"{label}: geometria ausente (vazia ou nula).")
                continue

            if geometry.is_empty:
                problems.append(f"{label}: geometria vazia.")
                continue

            if geometry.geom_type not in POLYGON_TYPES:
                problems.append(
                    f"{label}: geometria {geometry.geom_type} — só polígonos "
                    "(Polygon/MultiPolygon) podem ser importados."
                )
                continue

            if not geometry.is_valid:
                problems.append(
                    f"{label}: geometria inválida (auto-interseção ou anel não "
                    "fechado) — corrija no SIG antes de importar."
                )

        return problems

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
    def normalize_os(value: Any) -> Optional[str]:
        """Normaliza a CHAVE da OS em TEXTO (aceita ``039``, ``OS 169A``, ``169.0``).

        A OS é **TEXTO** e pode conter **LETRA** (ex.: ``169A``): a letra é o que
        diferencia as OS de um mesmo projeto. Os zeros à esquerda são PRESERVADOS
        (``039`` continua ``039``).
        """
        text = "" if value is None else str(value).strip().upper()
        if text.lower() in ("", "nan", "none", "<na>"):
            return None

        if re.fullmatch(r"\d+\.0+", text):
            text = text.split(".")[0]

        text = re.sub(r"[^0-9A-Z]", "", text)
        text = re.sub(r"^OS(?=\d)", "", text)
        return text or None

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
        Identifica a OS no caminho de origem (vazio quando não há padrão).

        A OS pode conter LETRA (ex.: ``OS_169A_...`` → ``169A``). Prioridade:
          1. pasta ``OS_<chave>...`` mais próxima do arquivo
             (ex.: ``OS_169A_AGUA_VIVA``);
          2. prefixo do arquivo ``P<chave>`` (ex.: ``P210_001_01_FAZ_...``);
          3. token ``OS_<chave>`` no nome do arquivo.
        """
        if not path:
            return ""

        candidate = Path(path)

        for folder in candidate.parents:
            match = re.search(
                r"(?:^|[_\-\s])OS[_\-\s]?(\d{1,6}[A-Za-z]?)(?=\D|$)",
                folder.name,
                re.IGNORECASE,
            )
            if match:
                return ProjectStructureUtil.normalize_os(match.group(1))

        stem = candidate.stem
        match = re.match(r"^P(\d{1,6}[A-Za-z]?)(?=\D|$)", stem, re.IGNORECASE)
        if match:
            return ProjectStructureUtil.normalize_os(match.group(1))

        match = re.search(
            r"(?:^|[_\-\s])OS[_\-\s]?(\d{1,6}[A-Za-z]?)(?=\D|$)",
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
        settings = cls.settings(config.mode)
        fields = settings["fields"]

        cls._notify(progress_cb, 5, "Lendo vetor...")

        gdf = VectorLayerSource.read_geodataframe(config.vector_path, tool_key=_TOOL_KEY)
        cls.validate_vector(config.vector_path, gdf)

        cls._notify(progress_cb, 25, "Validando atributos...")
        prepared = cls._prepare(gdf, config)

        cls._notify(progress_cb, 55, "Calculando área...")
        prepared = VectorLayerMetrics.calculate_area_hectares(
            prepared, FIELD_AREA_CALC, 4, _TOOL_KEY
        )
        prepared = prepared[fields + [prepared.geometry.name]]
        warnings: List[str] = cls._area_warnings(prepared, config)

        consolidated = cls._consolidated_path(config)
        if settings["unique"] and not config.update:
            cls._notify(progress_cb, 70, "Verificando duplicidades...")
            cls._check_duplicates(prepared, consolidated)

        payload: Dict[str, Any] = {
            "mode": config.mode,
            "dry_run": dry_run,
            "n_features": int(len(prepared)),
            "crs": str(prepared.crs),
            "total_ha": round(float(prepared[FIELD_AREA_CALC].sum()), 4),
            "os_keys": sorted({str(value) for value in prepared[FIELD_OS]}),
            "consolidated": consolidated,
            "os_files": [],
            "copies": [],
            "db_updated": 0,
            "update": bool(config.update),
            "replaced": 0,
            "warnings": warnings,
        }

        if dry_run:
            warnings.extend(cls._structure_warnings(prepared, config))
            cls._notify(progress_cb, 100, "Validação concluída.")
            logger.info(
                "Validação da importação concluída",
                code="LIM_VALIDATE_OK",
                n_features=payload["n_features"],
                n_warnings=len(warnings),
            )
            return payload

        cls._notify(
            progress_cb,
            85,
            "Atualizando base..." if config.update else "Gravando base...",
        )
        replaced = cls._write_target(consolidated, prepared, fields, config.update)

        os_files: List[str] = []
        for os_key, group in prepared.groupby(FIELD_OS, sort=True):
            target = cls._os_file_path(config, str(os_key))
            replaced += cls._write_target(target, group, fields, config.update)
            os_files.append(target)

        payload["os_files"] = os_files
        payload["replaced"] = replaced

        cls._notify(progress_cb, 92, "Copiando para os projetos...")
        cls._publish_to_projects(prepared, config, payload, logger)

        cls._notify(
            progress_cb,
            100,
            "Atualização concluída." if config.update else "Importação concluída.",
        )

        logger.info(
            f"Importação concluída ({settings['label']})",
            code="LIM_IMPORT_DONE",
            mode=config.mode,
            update=config.update,
            n_features=payload["n_features"],
            n_os=len(os_files),
            n_copies=len(payload["copies"]),
            n_db_updated=payload["db_updated"],
            n_replaced=payload["replaced"],
            total_ha=payload["total_ha"],
            n_warnings=len(warnings),
            root=config.output_root,
        )
        return payload

    @classmethod
    def settings(cls, mode: str) -> Dict[str, Any]:
        """Configuração do modo (``limites`` ou ``zonas``)."""
        return MODE_SETTINGS.get(mode, MODE_SETTINGS[MODE_LIMITES])

    # ── Destinos ────────────────────────────────────────────────────

    @classmethod
    def _consolidated_path(cls, config: LimitesImportConfig) -> str:
        """Caminho do completão do modo (arquivo com todas as OS)."""
        return os.path.join(
            config.output_root, cls.settings(config.mode)["consolidated"]
        )

    @classmethod
    def _os_file_path(cls, config: LimitesImportConfig, os_key: str) -> str:
        """Caminho do arquivo do modo dentro da pasta da OS na base."""
        settings = cls.settings(config.mode)
        return os.path.join(
            config.output_root, os_key, f"{os_key}{settings['os_suffix']}.shp"
        )

    @classmethod
    def _project_copy_path(
        cls,
        project_folder: Path,
        os_key: str,
        mode: str,
    ) -> Path:
        """Caminho da cópia do modo dentro da pasta do projeto da OS."""
        settings = cls.settings(mode)
        target_dir = project_folder / settings["project_folder"]
        if settings["project_subfolder"]:
            target_dir = target_dir / settings["project_subfolder"]

        return target_dir / f"{os_key}{settings['os_suffix']}.shp"

    # ── Verificação de shapes existentes ────────────────────────────

    @classmethod
    def find_existing(cls, config: LimitesImportConfig) -> Dict[str, Any]:
        """
        Localiza os shapes do vetor que JÁ existem na base e nos projetos.

        Lê e valida o vetor (mesmas regras da importação) para descobrir as OS
        e devolve os arquivos que uma atualização substituiria.

        Raises:
            LimitesValidationError: Problemas que impedem a leitura/validação.
        """
        logger = cls._get_logger(_TOOL_KEY, "LimitesService")

        gdf = VectorLayerSource.read_geodataframe(config.vector_path, tool_key=_TOOL_KEY)
        cls.validate_vector(config.vector_path, gdf)

        prepared = cls._prepare(gdf, config)
        os_keys = sorted({str(value) for value in prepared[FIELD_OS]})

        targets: List[str] = []
        consolidated = cls._consolidated_path(config)
        if os.path.exists(consolidated):
            targets.append(consolidated)

        for os_key in os_keys:
            path = cls._os_file_path(config, os_key)
            if os.path.exists(path):
                targets.append(path)

        targets.extend(cls._existing_project_copies(prepared, config))

        logger.info(
            "Shapes existentes verificados",
            code="LIM_EXISTING",
            mode=config.mode,
            n_os=len(os_keys),
            n_targets=len(targets),
        )
        return {
            "mode": config.mode,
            "n_features": int(len(prepared)),
            "os_keys": os_keys,
            "targets": targets,
        }

    @classmethod
    def _existing_project_copies(
        cls,
        prepared: Any,
        config: LimitesImportConfig,
    ) -> List[str]:
        """Caminhos das cópias no projeto que já existem para as OS do lote."""
        mother = cls._load_mother_folder()
        if mother is None:
            return []

        logger = cls._get_logger(_TOOL_KEY, "LimitesService")
        records: Dict[str, Optional[Dict[str, Any]]] = {}
        found: List[str] = []

        for os_key in prepared[FIELD_OS].drop_duplicates():
            key = str(os_key)
            if key not in records:
                records[key] = cls._load_order(key, logger)

            folder, _ = cls._find_project_folder(mother, records[key], key)
            if folder is None:
                continue

            target = cls._project_copy_path(folder, key, config.mode)
            if target.is_file():
                found.append(str(target))

        return found

    @classmethod
    def _prepare(
        cls,
        gdf: Any,
        config: LimitesImportConfig,
    ) -> Any:
        """Resolve os valores de cada feição e devolve o GeoDataFrame canônico."""
        settings = cls.settings(config.mode)
        semantic = settings["semantic"]
        is_zonas = config.mode == MODE_ZONAS

        columns = {key: cls._resolve_series(gdf, config, key) for key in semantic}
        empty = [""] * len(gdf)

        talhoes: List[str] = []
        zonas: List[str] = []
        campos: List[str] = []
        fazendas: List[str] = []
        os_keys: List[str] = []
        clientes: List[str] = []
        areas: List[Optional[float]] = []
        keys: List[str] = []
        problems: List[str] = []

        for index in range(len(gdf)):
            label = f"Feição {index + 1}"

            talhao = cls.normalize_text(columns.get("talhao", empty)[index])
            if not talhao and not is_zonas:
                problems.append(f"{label}: TALHÃO vazio (obrigatório).")

            zona = cls.normalize_text(columns.get("zona", empty)[index])
            if is_zonas and not zona:
                problems.append(f"{label}: ZONA vazia (obrigatória).")

            # CAMPO de manejo é OPCIONAL — quando informado vai para todos os shapes
            campo = cls.normalize_text(columns.get("campo", empty)[index])

            fazenda = cls.normalize_text(columns["fazenda"][index])
            if not fazenda:
                problems.append(f"{label}: FAZENDA vazia (obrigatória).")

            os_key = cls.normalize_os(columns["os"][index])
            if os_key is None:
                problems.append(f"{label}: OS vazia ou inválida (obrigatória).")

            area = cls.parse_float(columns["area"][index])
            if area is not None and area <= 0:
                area = None
            areas.append(area)
            talhoes.append(talhao)
            zonas.append(zona)
            campos.append(campo)
            fazendas.append(fazenda)
            clientes.append(cls.normalize_text(columns["cliente"][index]))

            if os_key is None or not fazenda:
                os_keys.append("")
                keys.append("")
                continue

            os_keys.append(os_key)

            if is_zonas:
                keys.append("")
                continue

            if not talhao:
                keys.append("")
                continue

            keys.append(f"{os_key}-{fazenda}-{talhao}")

        if problems:
            raise LimitesValidationError(cls._limit_problems(problems))

        prepared = gdf.copy()
        if is_zonas:
            prepared[FIELD_ZONA] = zonas
            prepared[FIELD_CAMPO] = campos
        prepared[FIELD_TALHAO] = talhoes
        prepared[FIELD_FAZENDA] = fazendas
        prepared[FIELD_OS] = os_keys
        prepared[FIELD_CLIENTE] = clientes
        prepared[FIELD_AREA_INF] = pd.Series(areas, index=prepared.index, dtype="float64")
        if not is_zonas:
            prepared[FIELD_KEY] = keys

        prepare_fields = [f for f in settings["fields"] if f != FIELD_AREA_CALC]
        return prepared[prepare_fields + [prepared.geometry.name]]

    @staticmethod
    def _resolve_series(gdf: Any, config: LimitesImportConfig, key: str) -> List[Any]:
        """Valores de uma chave semântica: campo mapeado (prioridade) ou valor manual."""
        field_name = (config.field_map.get(key) or "").strip()
        if field_name and field_name in gdf.columns:
            return list(gdf[field_name])

        manual = (config.manual.get(key) or "").strip()
        return [manual] * len(gdf)

    # ── Verificações ────────────────────────────────────────────────

    @classmethod
    def _area_warnings(cls, gdf: Any, config: LimitesImportConfig) -> List[str]:
        """Compara a área informada com a calculada e devolve os avisos de divergência."""
        warnings: List[str] = []
        is_zonas = config.mode == MODE_ZONAS

        for _, row in gdf.iterrows():
            informed = row[FIELD_AREA_INF]
            if informed is None or pd.isna(informed):
                continue

            informed = float(informed)
            if informed <= 0:
                continue

            calculated = float(row[FIELD_AREA_CALC])
            if is_zonas:
                key = f"{row[FIELD_OS]}-{row[FIELD_FAZENDA]}-{row[FIELD_ZONA]}"
            else:
                key = str(row[FIELD_KEY])

            diff_pct = abs(calculated - informed) / informed * 100.0
            if diff_pct > config.tolerance_pct:
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

        for key in gdf[FIELD_KEY]:
            key = str(key).strip()
            if not key:
                continue
            if key in seen:
                problems.append(f"{key}: duplicado dentro do próprio arquivo.")
                continue

            seen.add(key)
            if key in existing:
                problems.append(f"{key}: já existe na base.")

        if problems:
            raise LimitesValidationError(cls._limit_problems(problems))

    @classmethod
    def _load_keys(cls, consolidated_path: str) -> set:
        """Lê as chaves já existentes no completão (vazio quando o arquivo não existe)."""
        if not os.path.exists(consolidated_path):
            return set()

        gdf = VectorLayerSource.read_geodataframe(consolidated_path, tool_key=_TOOL_KEY)
        if FIELD_KEY not in gdf.columns:
            return set()

        return {str(key).strip() for key in gdf[FIELD_KEY] if str(key).strip()}

    # ── Escrita ─────────────────────────────────────────────────────

    @classmethod
    def _write_target(
        cls,
        target: str,
        new_gdf: Any,
        fields: List[str],
        replace: bool,
    ) -> int:
        """
        Anexa ou SUBSTITUI o lote no arquivo de destino.

        Returns:
            Número de feições removidas do destino (0 quando apenas anexa).
        """
        if not replace:
            cls._append_and_write(target, new_gdf, fields)
            return 0

        return cls._replace_and_write(target, new_gdf, fields)

    @classmethod
    def _append_and_write(cls, target: str, new_gdf: Any, fields: List[str]) -> None:
        """Anexa o lote ao arquivo de destino (quando existe) e grava de forma atômica."""
        if not os.path.exists(target):
            VectorLayerSource.write_geodataframe_atomic(
                new_gdf, target, tool_key=_TOOL_KEY
            )
            return

        existing = cls._read_existing(target, fields)
        merged = VectorLayerSource.concat_geodataframes(
            existing, new_gdf, tool_key=_TOOL_KEY
        )
        cls._write_canonical(merged, target, fields)

    @classmethod
    def _replace_and_write(cls, target: str, new_gdf: Any, fields: List[str]) -> int:
        """Substitui as feições das OS do lote no destino e grava de forma atômica."""
        if not os.path.exists(target):
            VectorLayerSource.write_geodataframe_atomic(
                new_gdf, target, tool_key=_TOOL_KEY
            )
            return 0

        existing = cls._read_existing(target, fields)
        kept = cls._drop_batch_os(existing, new_gdf)
        removed = len(existing) - len(kept)

        if len(kept) == 0:
            merged = new_gdf
        else:
            merged = VectorLayerSource.concat_geodataframes(
                kept, new_gdf, tool_key=_TOOL_KEY
            )

        cls._write_canonical(merged, target, fields)
        return removed

    @classmethod
    def _read_existing(cls, target: str, fields: List[str]) -> Any:
        """Lê o destino garantindo as colunas canônicas do modo antes de mesclar."""
        existing = VectorLayerSource.read_geodataframe(target, tool_key=_TOOL_KEY).copy()
        defaults = {
            FIELD_OS: "",
            FIELD_AREA_CALC: 0.0,
            FIELD_AREA_INF: float("nan"),
        }
        for column in fields:
            if column not in existing.columns:
                existing[column] = defaults.get(column, "")

        return existing[fields + [existing.geometry.name]]

    @staticmethod
    def _drop_batch_os(existing: Any, batch: Any) -> Any:
        """Remove do arquivo existente as feições das OS presentes no lote."""
        keys = {str(value).strip() for value in batch[FIELD_OS]}
        keep = [str(value).strip() not in keys for value in existing[FIELD_OS]]
        return existing[keep]

    @staticmethod
    def _write_canonical(gdf: Any, target: str, fields: List[str]) -> None:
        """Grava o GeoDataFrame com as colunas do modo, de forma atômica."""
        VectorLayerSource.write_geodataframe_atomic(
            gdf[fields + [gdf.geometry.name]], target, tool_key=_TOOL_KEY
        )

    # ── Estrutura do projeto (Verra) + banco ────────────────────────

    @classmethod
    def _publish_to_projects(
        cls,
        prepared: Any,
        config: LimitesImportConfig,
        payload: Dict[str, Any],
        logger: Any,
    ) -> None:
        """Copia o resultado para a pasta do projeto da OS e registra no banco."""
        settings = cls.settings(config.mode)
        warnings: List[str] = payload["warnings"]

        mother = cls._load_mother_folder()
        if mother is None:
            warnings.append(
                "Pasta-mãe não configurada no Gerenciador de Estrutura — a cópia em "
                f"{settings['project_folder']} não foi gerada."
            )
            return

        records: Dict[str, Optional[Dict[str, Any]]] = {}

        for os_key, group in prepared.groupby(FIELD_OS, sort=True):
            key = str(os_key)

            if key not in records:
                records[key] = cls._load_order(key, logger)
            record = records[key]

            folder, reason = cls._find_project_folder(mother, record, key)
            if folder is None:
                warnings.append(f"OS {key}: {reason} — cópia no projeto não gerada.")
                continue

            try:
                copy_path, removed = cls._write_project_copy(
                    folder, key, group, config.mode, config.update
                )
            except Exception as e:
                logger.error(
                    "Falha ao gravar a copia no projeto",
                    code="LIM_COPY_ERR",
                    path=str(folder),
                    error=str(e),
                )
                warnings.append(
                    f"OS {key}: falha ao gravar a cópia no projeto ({e})."
                )
                continue

            payload["copies"].append(str(copy_path))
            payload["replaced"] += removed

            if record is None:
                warnings.append(
                    f"OS {key}: OS não encontrada no banco — "
                    "o resultado não foi registrado."
                )
                continue

            if cls._register_limits(mother, record, copy_path, group, config):
                payload["db_updated"] += 1
            else:
                warnings.append(f"OS {key}: falha ao registrar no banco.")

    @classmethod
    def _structure_warnings(cls, prepared: Any, config: LimitesImportConfig) -> List[str]:
        """Antes de gravar, avisa sobre projetos que não receberão a cópia."""
        settings = cls.settings(config.mode)
        mother = cls._load_mother_folder()
        if mother is None:
            return [
                "Pasta-mãe não configurada no Gerenciador de Estrutura — a cópia em "
                f"{settings['project_folder']} não será gerada."
            ]

        warnings: List[str] = []
        for os_key in prepared[FIELD_OS].drop_duplicates():
            key = str(os_key)
            folder, reason = cls._find_project_folder(mother, None, key)
            if folder is None:
                warnings.append(f"OS {key}: {reason}.")

        return warnings

    @classmethod
    def _find_project_folder(
        cls,
        mother: Path,
        record: Optional[Dict[str, Any]],
        os_key: str,
    ) -> Tuple[Optional[Path], str]:
        """Localiza a pasta do projeto da OS (banco primeiro, disco como fallback)."""
        if record:
            rel = str(record.get("path", "") or "")
            if rel:
                folder = ProjectStructureUtil.resolve_path(mother, rel)
                if folder.is_dir():
                    return folder, ""

        folder = ProjectStructureUtil.project_folder(
            mother, os_key, tool_key=_TOOL_KEY
        )
        if folder is not None:
            return folder, ""

        return None, f"pasta da OS {os_key} não encontrada em {mother}"

    @classmethod
    def _write_project_copy(
        cls,
        project_folder: Path,
        os_key: str,
        group: Any,
        mode: str,
        replace: bool = False,
    ) -> Tuple[Path, int]:
        """Grava (ou substitui) a cópia na pasta do projeto e devolve o caminho."""
        settings = cls.settings(mode)
        target = cls._project_copy_path(project_folder, os_key, mode)
        removed = cls._write_target(str(target), group, settings["fields"], replace)
        return target, removed

    @staticmethod
    def _stored_file_path(mother: Path, file_path: Path) -> str:
        """Caminho do arquivo gravado no banco: relativo à pasta-mãe (ou absoluto).

        ``to_relative_path`` devolve apenas o NOME quando o arquivo está FORA da
        pasta-mãe — nesse caso grava o caminho ABSOLUTO para o registro continuar
        abrindo no Explorer.
        """
        target = Path(file_path)
        relative = ProjectStructureUtil.to_relative_path(mother, target)
        if relative == target.name:
            return str(target)
        return relative

    @classmethod
    def _register_limits(
        cls,
        mother: Path,
        record: Dict[str, Any],
        file_path: Path,
        group: Any,
        config: LimitesImportConfig,
    ) -> bool:
        """Marca na OS do banco que o limite foi inserido (Firestore + backup JSON)."""
        settings = cls.settings(config.mode)
        db_key = settings["db_key"]

        record[db_key] = {
            "inserted_at": datetime.now().isoformat(timespec="seconds"),
            "file": cls._stored_file_path(mother, file_path),
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
                "Falha ao registrar no banco",
                code="LIM_DB_SAVE_ERR",
                os_key=str(record.get("os", "")),
                db_key=db_key,
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


class LimitesExistingWorker(QRunnable):
    """Procura, em background, os shapes do vetor que já existem nas pastas."""

    def __init__(self, generation: int, config: LimitesImportConfig) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.generation = generation
        self.config = config
        self.signals = _LimitesSignals()

    def run(self) -> None:
        """Executa a verificação e emite o resultado."""
        try:
            payload = LimitesService.find_existing(self.config)
            self.signals.finished.emit(self.generation, payload)
        except LimitesValidationError as e:
            self.signals.invalid.emit(self.generation, e.problems)
        except Exception as e:
            LimitesService._get_logger(_TOOL_KEY, "LimitesExistingWorker").error(
                "Falha ao verificar shapes existentes",
                code="LIM_EXISTING_ERR",
                path=self.config.vector_path,
                error=str(e),
            )
            self.signals.failed.emit(self.generation, str(e))

