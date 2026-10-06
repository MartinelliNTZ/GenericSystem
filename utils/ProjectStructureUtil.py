# -*- coding: utf-8 -*-
"""
ProjectStructureUtil — Estrutura padrão dos projetos (OS) compartilhada
======================================================================
Centraliza as constantes e a descoberta da estrutura de pastas dos
projetos (OS) para reuso por mais de uma ferramenta (Contrato 7 — nenhum
plugin importa outro). Foi promovido de
``plugins/project_structure_manager/ProjectStructureScanner`` para
``utils/``; o scanner passa a importar daqui e re-exporta os nomes.

Uso:
    from utils.ProjectStructureUtil import ProjectStructureUtil

    projects = ProjectStructureUtil.discover_projects(mother)
    data = ProjectStructureUtil.collect_created_data(project)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


# ── Constantes (nível de módulo — importáveis por outras ferramentas) ──

# Prefixo das pastas de projeto dentro da pasta-mãe.
PROJECT_PREFIX = "OS_"

# Pastas esperadas na raiz de cada projeto.
DEFAULT_PROJECT_FOLDERS: List[str] = [
    "01_Acessos_Plataforma_IA_AGLIBS",
    "02_Acompanhamento_de_Projeto_Reuniões",
    "03_ENVIO_DE_DOCUMENTOS",
    "04_ATIVIDADES_ATRIBUIDAS",
    "05_ASA",
    "06_CAR",
    "07_MATRICULA",
    "08_LIMITES",
    "09_HISTORICO_COBERTURA_SOLO",
    "10_VERRA",
    "11_AGROROBOTICA",
    "12_FOTOS_INICIO_PROJETO",
    "13_ZONAS_DE_MANEJO",
    "14_RELATORIO",
]

# Pasta do projeto que agrupa as pastas de ano.
DOCUMENT_YEARS_FOLDER = "03_ENVIO_DE_DOCUMENTOS"

# Anos oferecidos por padrão (usados pelo diálogo de criação de anos).
DEFAULT_YEARS: List[int] = list(range(2019, 2028))

# Templates de subpastas para pastas de topo específicas do projeto.
# ``None`` = folha (sem subpastas); ``dict`` = subpastas esperadas (validadas
# na árvore e criadas junto com a pasta de topo).
PROJECT_FOLDER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "14_RELATORIO": {
        "Uso e Ocupacao do Solo": None,
        "Laudos Analises de Solo": None,
    },
}


class ProjectStructureUtil(BaseUtil):
    """Constantes e descoberta da estrutura padrão dos projetos (OS)."""

    # Mesmas constantes expostas via classe (ProjectStructureUtil.X).
    PROJECT_PREFIX = PROJECT_PREFIX
    DEFAULT_PROJECT_FOLDERS = DEFAULT_PROJECT_FOLDERS
    DOCUMENT_YEARS_FOLDER = DOCUMENT_YEARS_FOLDER
    DEFAULT_YEARS = DEFAULT_YEARS
    PROJECT_FOLDER_TEMPLATES = PROJECT_FOLDER_TEMPLATES


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
