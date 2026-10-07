# -*- coding: utf-8 -*-
"""
ProjectStructureUtil — Estrutura padrão dos projetos (OS) compartilhada
======================================================================
FONTE ÚNICA (single source of truth) da estrutura de pastas dos projetos (OS).

Toda a estrutura — pastas, futuros ARQUIVOS BASE e a pasta de anos — é descrita
por UM único dicionário: ``ProjectStructureUtil.PROJECT_STRUCTURE``. Alimente e
edite apenas ele; os valores derivados (``DEFAULT_PROJECT_FOLDERS``,
``PROJECT_FOLDER_TEMPLATES``, ``DOCUMENT_YEARS_FOLDER``, ``DEFAULT_YEARS`` e
``DOCUMENT_TEMPLATE``) são calculados a partir dele e consumidos pelo
Gerenciador de Estrutura, pelo Banco de Dados e pelas cores das pastas.

Tipos de nó do dicionário (recursivo):
    None            → pasta vazia (folha)
    { ... }         → pasta contendo os itens do dicionário
    "arquivo.ext"   → ARQUIVO BASE copiado de ``BASE_FILES_DIR``
    BaseFile(...)   → ARQUIVO BASE com opções (origem/conteúdo/sobrescrever)
    Years(...)      → pasta que se expande em uma subpasta por ano

Uso:
    from utils.ProjectStructureUtil import ProjectStructureUtil

    projects = ProjectStructureUtil.discover_projects(mother)
    data = ProjectStructureUtil.collect_created_data(project)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


# ── Tipos de nó do PROJECT_STRUCTURE ────────────────────────────────
# Cada item do dicionário é um NOME mapeado para um NÓ:
#   None          → pasta vazia (folha)
#   { ... }       → pasta com itens filhos (recursivo)
#   "arquivo.ext" → ARQUIVO BASE copiado de ProjectStructureUtil.BASE_FILES_DIR
#   BaseFile(...) → ARQUIVO BASE com opções (origem/conteúdo/sobrescrever)
#   Years(...)    → pasta que se expande em uma subpasta por ano


@dataclass(frozen=True)
class BaseFile:
    """Arquivo base criado dentro da estrutura do projeto.

    ``source``: caminho relativo dentro de ``BASE_FILES_DIR`` (copiado de lá);
    ``content``: conteúdo inline (usado quando ``source`` está vazio);
    ``overwrite``: se ``False``, não sobrescreve um arquivo já existente.
    """

    source: str = ""
    content: str = ""
    overwrite: bool = True


@dataclass
class Years:
    """Pasta especial que se expande em uma subpasta por ano selecionado.

    ``years``: anos oferecidos por padrão (diálogo de criação);
    ``template``: estrutura criada (e validada) DENTRO de cada ano.
    """

    years: List[int] = field(default_factory=list)
    template: Dict[str, Any] = field(default_factory=dict)


def is_file_node(node: Any) -> bool:
    """Indica se ``node`` representa um ARQUIVO base (``str`` ou ``BaseFile``)."""
    return isinstance(node, (str, BaseFile))


def is_years_node(node: Any) -> bool:
    """Indica se ``node`` é a pasta especial de ANOS (``Years``)."""
    return isinstance(node, Years)


def file_spec(node: Any) -> BaseFile:
    """Normaliza um nó de arquivo (``str`` | ``BaseFile``) em ``BaseFile``."""
    if isinstance(node, BaseFile):
        return node
    return BaseFile(source=str(node))


class ProjectStructureUtil(BaseUtil):
    """FONTE ÚNICA da estrutura de pastas padrão dos projetos (OS).

    Toda a estrutura — pastas, arquivos base e a pasta de anos — é descrita
    pelo dicionário ``PROJECT_STRUCTURE``. Alimente/edite apenas ele: os valores
    derivados (``DEFAULT_PROJECT_FOLDERS``, ``PROJECT_FOLDER_TEMPLATES``,
    ``DOCUMENT_YEARS_FOLDER``, ``DEFAULT_YEARS`` e ``DOCUMENT_TEMPLATE``) são
    calculados a partir dele e consumidos pelo Gerenciador de Estrutura, pelo
    Banco de Dados e pelas cores das pastas.
    """

    # Prefixo das pastas de projeto dentro da pasta-mãe.
    PROJECT_PREFIX = "OS_"

    # ══════════════════════════════════════════════════════════════════
    # ESTRUTURA — FONTE ÚNICA (alimente apenas este dicionário)
    # ══════════════════════════════════════════════════════════════════
    #
    # Cada chave é um item criado na raiz da pasta do projeto (OS). O valor
    # define o CONTEÚDO do item (ver tipos de nó no topo do módulo):
    #   None | { ... } | "arquivo.ext" | BaseFile(...) | Years(...)
    #
    PROJECT_STRUCTURE: Dict[str, Any] = {
        "01_Acessos_Plataforma_IA_AGLIBS": None,
        "02_Acompanhamento_de_Projeto_Reuniões": None,
        "03_ENVIO_DE_DOCUMENTOS": Years(
            years=list(range(2019, 2028)),
            template={
                "01_DADOS_OPERACIONAIS": {
                    "COMBUSTIVEL": None,
                    "DEFENSIVOS": {"ALGODAO": None, "MILHO": None, "SOJA": None},
                    "FERTILIZANTES": {"ALGODAO": None, "MILHO": None, "SOJA": None},
                    "PRODUTIVIDADE": None,
                },
                "02_ANALISES_SOLO": None,
                "03_NOTAS_FISCAIS": {
                    "NF_ANIMAIS": {"FICHA_VACINACAO": None, "GTA_ANIMAL": None},
                    "NF_COMBUSTIVEL": None,
                    "NF_DEFENSIVOS": None,
                    "NF_ENERGIA": None,
                    "NF_FERTILIZANTE": {"CALCARIO": None, "KCL": None, "MAP": None},
                    "NF_RACOES": None,
                    "NF_SEMENTES": None,
                },
                "04_TICKETS_PESSAGEM_BALANCA": None,
                "05_ANEXOS_TREINAMENTOS": None,
            },
        ),
        "04_ATIVIDADES_ATRIBUIDAS": None,
        "05_ASA": None,
        "06_CAR": None,
        "07_MATRICULA": None,
        "08_LIMITES": None,
        "09_HISTORICO_COBERTURA_SOLO": None,
        "10_VERRA": None,
        "11_AGROROBOTICA": None,
        "12_FOTOS_INICIO_PROJETO": None,
        "13_ZONAS_DE_MANEJO": None,
        "14_RELATORIOS": {
            "Laudos Analises de Solo": {
                "Fertilidade": {
                    "Excel": None,
                    "PDF": None,
                    "Recomendacao_Agronomica": None,
                },
                "Sustentabilidade": {
                    "Relatório": None,
                },
            },
            "Relatorios Evolucao Operacional": None,
            "Uso e Ocupacao do Solo": None,
        },
    }

    # Origem dos ARQUIVOS BASE (``BaseFile.source`` é relativo a esta pasta).
    BASE_FILES_DIR: Path = (
        Path(__file__).resolve().parent.parent
        / "resources"
        / "project_templates"
    )


    # ── Descoberta ──────────────────────────────────────────────────

    @classmethod
    def discover_projects(
        cls,
        mother: Path,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> List[Path]:
        """Retorna as pastas de projeto (prefixo ``OS_``) ordenadas por nome."""
        logger = cls._get_logger(tool_key, "ProjectStructureUtil")
        try:
            projects = [
                path
                for path in mother.iterdir()
                if path.is_dir() and path.name.upper().startswith(cls.PROJECT_PREFIX)
            ]
        except (PermissionError, FileNotFoundError, OSError) as e:
            logger.error(
                "Falha ao ler a pasta-mãe",
                code="PSU_DISCOVER_ERR",
                error=str(e),
                path=str(mother),
            )
            return []
        projects.sort(key=lambda path: path.name.lower())
        return projects

    @staticmethod
    def is_year_folder(name: str) -> bool:
        """Indica se ``name`` é uma pasta de ano (4 dígitos numéricos)."""
        return name.isdigit() and len(name) == 4

    # ── Chave da OS ─────────────────────────────────────────────────

    @classmethod
    def _strip_prefix(cls, name: str) -> str:
        """Remove o prefixo ``OS_`` do nome da pasta (se presente)."""
        if name.upper().startswith(cls.PROJECT_PREFIX.upper()):
            return name[len(cls.PROJECT_PREFIX):]
        return name

    @classmethod
    def extract_os_number(cls, name: str) -> str:
        """Extrai o NÚMERO da OS — o primeiro campo após o prefixo ``OS_``.

            "OS_234_Cliente"                      → "234"
            "OS_181_RENNER_A_Grupo JCN - Faz X"   → "181"
            "OS_234"                              → "234"
        """
        core = cls._strip_prefix(name)
        parts = core.split("_")
        return parts[0] if parts else core

    @classmethod
    def extract_sub_os(cls, name: str) -> str:
        """Extrai a SUBOS do nome da pasta — a letra única após o número.

            "OS_181_RENNER_A_Grupo JCN - Faz X"   → "A"
            "OS_189_Thiago_Fabris"                 → ""
            "OS_169_SLC"                           → ""
        """
        core = cls._strip_prefix(name)
        parts = core.split("_")
        for token in parts[1:]:
            if len(token) == 1 and token.isascii() and token.isalpha():
                return token.upper()
        return ""

    @classmethod
    def assign_sub_os_letters(cls, project_paths: List[Path]) -> Dict[Path, str]:
        """Atribui uma letra de SubOS a cada pasta de uma OS.

        - Se TODAS as pastas tiverem uma letra no nome (ex.: ``OS_181_RENNER_A_...``),
          usa a letra do próprio nome.
        - Caso contrário, subdivide por ORDEM: 1ª pasta → ``A``, 2ª → ``B``, ...
          (uma pasta única fica sempre em ``A``).

        Returns:
            ``{Path: "A", ...}``.
        """
        ordered = sorted(project_paths, key=lambda path: path.name.lower())
        letters = [cls.extract_sub_os(path.name) for path in ordered]
        if all(letters) and len(set(letters)) == len(letters):
            return {path: letter for path, letter in zip(ordered, letters)}
        return {path: chr(ord("A") + index) for index, path in enumerate(ordered)}

    @classmethod
    def group_projects_by_os(cls, projects: List[Path]) -> Dict[str, List[Path]]:
        """Agrupa as pastas de projeto pelo NÚMERO da OS (normalizado).

        Uma OS dividida em várias pastas (uma por SubOS) vira UMA entrada:

            {"181": [OS_181_RENNER_A..., OS_181_RENNER_B..., OS_181_RENNER_C...]}
        """
        groups: Dict[str, List[Path]] = {}
        for path in projects:
            number = cls.normalize_os(cls.extract_os_number(path.name))
            groups.setdefault(number, []).append(path)
        return groups

    @staticmethod
    def normalize_os(number: str) -> str:
        """Normaliza o número da OS — remove zeros à esquerda (``"039"`` → ``"39"``)."""
        text = str(number).strip()
        return str(int(text)) if text.isdigit() else text

    # ── Caminhos (relativo à pasta-mãe — portável entre computadores) ──

    @classmethod
    def to_relative_path(
        cls, mother: Optional[Path], path: str | Path
    ) -> str:
        """Converte ``path`` em caminho RELATIVO à pasta-mãe (portável).

        Grava sempre com separador ``/`` para funcionar em qualquer computador.
        Se ``path`` não estiver sob ``mother`` (ou ``mother`` for vazio),
        retorna apenas o nome final da pasta/arquivo.
        """
        target = Path(path)
        if mother is not None:
            try:
                return target.relative_to(Path(mother)).as_posix()
            except ValueError:
                pass
        return target.name

    @classmethod
    def resolve_path(cls, mother: Optional[Path], rel_path: str | Path) -> Path:
        """Resolve um caminho RELATIVO à pasta-mãe (ou devolve o absoluto).

        Caminhos absolutos são retornados como estão (compatibilidade com o
        legado). Caminhos relativos são combinados com ``mother``.
        """
        raw = str(rel_path or "").replace("\\", "/").strip()
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate
        base = Path(mother) if mother is not None else Path("")
        return (base / raw) if raw else base

    # ── Dados já criados (adaptador para o Banco de Dados) ──────────

    @classmethod
    def collect_created_data(
        cls,
        project: Path,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, List[str]]:
        """Retorna o que já existe em disco dentro de uma OS.

        Apenas as pastas **padrão** (``DEFAULT_PROJECT_FOLDERS``) presentes em
        disco entram em ``folders`` (equivalentes ao status ``CORRETA``);
        pastas fora de padrão são ignoradas. Em ``years`` entram somente as
        pastas de ano (4 dígitos) presentes dentro de
        ``03_ENVIO_DE_DOCUMENTOS``.
        """
        logger = cls._get_logger(tool_key, "ProjectStructureUtil")
        folders: List[str] = []
        years: List[str] = []
        try:
            existing = {
                path.name for path in project.iterdir() if path.is_dir()
            }
        except (PermissionError, FileNotFoundError, OSError) as e:
            logger.error(
                "Falha ao ler projeto",
                code="PSU_COLLECT_ERR",
                error=str(e),
                path=str(project),
            )
            return {"folders": folders, "years": years}

        folders = [
            name for name in cls.DEFAULT_PROJECT_FOLDERS if name in existing
        ]

        envio = project / cls.DOCUMENT_YEARS_FOLDER
        if envio.is_dir():
            try:
                years = sorted(
                    path.name
                    for path in envio.iterdir()
                    if path.is_dir() and cls.is_year_folder(path.name)
                )
            except (PermissionError, FileNotFoundError, OSError) as e:
                logger.error(
                    "Falha ao listar pastas de ano",
                    code="PSU_YEARS_ERR",
                    error=str(e),
                    path=str(envio),
                )

        return {"folders": folders, "years": years}

    # ── Agregação (Regra: pastas e anos pertencem à SubOS) ──────────

    @classmethod
    def aggregate_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Deriva cliente/pastas/anos/caminho a partir das SubOS do registro.

        As pastas e os anos **pertencem à SubOS** — não à OS. Este helper apenas
        agrega esses dados para telas que resumem a OS; a fonte continua sendo
        cada entrada de ``sub_os``.
        """
        folders: List[str] = []
        years: List[str] = []
        paths: List[str] = []
        clients: List[str] = []
        for entry in record.get("sub_os", []) or []:
            if not isinstance(entry, dict):
                continue
            cls._extend_unique(folders, entry.get("folders", []) or [])
            cls._extend_unique(years, entry.get("years", []) or [])
            path = str(entry.get("path", "") or "")
            if path and path not in paths:
                paths.append(path)
            client = str(entry.get("client", "") or "").strip()
            if client and client not in clients:
                clients.append(client)
        ordered_folders = [
            name for name in cls.DEFAULT_PROJECT_FOLDERS if name in folders
        ]
        return {
            "client": " / ".join(clients),
            "folders": ordered_folders or folders,
            "years": sorted(years),
            "path": paths[0] if paths else "",
            "paths": paths,
        }

    @staticmethod
    def _extend_unique(target: List[str], values: List[str]) -> None:
        """Adiciona a ``target`` os itens de ``values`` que ainda não existem."""
        for value in values:
            if value not in target:
                target.append(value)


# ── Derivados de PROJECT_STRUCTURE (NÃO edite — calculados a partir dele) ──
def _derive_from_structure() -> None:
    """Calcula os acessores derivados a partir de ``PROJECT_STRUCTURE``."""
    structure = ProjectStructureUtil.PROJECT_STRUCTURE
    years_name = next(
        (name for name, node in structure.items() if is_years_node(node)), ""
    )
    years_node = structure.get(years_name) if years_name else None
    ProjectStructureUtil.DEFAULT_PROJECT_FOLDERS = list(structure)
    ProjectStructureUtil.DOCUMENT_YEARS_FOLDER = years_name
    ProjectStructureUtil.DEFAULT_YEARS = (
        list(years_node.years) if years_node else []
    )
    ProjectStructureUtil.DOCUMENT_TEMPLATE = (
        dict(years_node.template) if years_node else {}
    )
    ProjectStructureUtil.PROJECT_FOLDER_TEMPLATES = {
        name: node for name, node in structure.items() if isinstance(node, dict)
    }


_derive_from_structure()


# ── Atalhos de módulo (apontam para a classe — fonte única) ─────────
PROJECT_STRUCTURE = ProjectStructureUtil.PROJECT_STRUCTURE
PROJECT_PREFIX = ProjectStructureUtil.PROJECT_PREFIX
DEFAULT_PROJECT_FOLDERS = ProjectStructureUtil.DEFAULT_PROJECT_FOLDERS
DOCUMENT_YEARS_FOLDER = ProjectStructureUtil.DOCUMENT_YEARS_FOLDER
DEFAULT_YEARS = ProjectStructureUtil.DEFAULT_YEARS
PROJECT_FOLDER_TEMPLATES = ProjectStructureUtil.PROJECT_FOLDER_TEMPLATES
DOCUMENT_TEMPLATE = ProjectStructureUtil.DOCUMENT_TEMPLATE


# ── Funções de módulo (re-exportáveis por outras ferramentas) ───────

def discover_projects(
    mother: Path,
    tool_key: str = ToolKey.UNTRACEABLE.value,
) -> List[Path]:
    """Atalho de módulo para ``ProjectStructureUtil.discover_projects``."""
    return ProjectStructureUtil.discover_projects(mother, tool_key=tool_key)


def is_year_folder(name: str) -> bool:
    """Atalho de módulo para ``ProjectStructureUtil.is_year_folder``."""
    return ProjectStructureUtil.is_year_folder(name)


def collect_created_data(
    project: Path,
    tool_key: str = ToolKey.UNTRACEABLE.value,
) -> Dict[str, List[str]]:
    """Atalho de módulo para ``ProjectStructureUtil.collect_created_data``."""
    return ProjectStructureUtil.collect_created_data(project, tool_key=tool_key)
