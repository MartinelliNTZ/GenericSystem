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
from typing import Dict, List

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
]

# Pasta do projeto que agrupa as pastas de ano.
DOCUMENT_YEARS_FOLDER = "03_ENVIO_DE_DOCUMENTOS"

# Anos oferecidos por padrão (usados pelo diálogo de criação de anos).
DEFAULT_YEARS: List[int] = list(range(2019, 2028))


class ProjectStructureUtil(BaseUtil):
    """Constantes e descoberta da estrutura padrão dos projetos (OS)."""

    # Mesmas constantes expostas via classe (ProjectStructureUtil.X).
    PROJECT_PREFIX = PROJECT_PREFIX
    DEFAULT_PROJECT_FOLDERS = DEFAULT_PROJECT_FOLDERS
    DOCUMENT_YEARS_FOLDER = DOCUMENT_YEARS_FOLDER
    DEFAULT_YEARS = DEFAULT_YEARS


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
    def extract_client_name(cls, name: str) -> str:
        """Extrai o nome do cliente — o ÚLTIMO campo (pode conter espaços).

            "OS_234_Cliente"                      → "Cliente"
            "OS_181_RENNER_A_Grupo JCN - Faz X"   → "Grupo JCN - Faz X"
            "OS_234"                              → ""
        """
        core = cls._strip_prefix(name)
        parts = core.split("_")
        return parts[-1] if len(parts) > 1 else ""

    @classmethod
    def extract_os_identifier(cls, name: str) -> str:
        """Identificador completo da OS (nome sem o prefixo e sem o cliente).

        Usado para desambiguar arquivos quando o NÚMERO da OS se repete:

            "OS_181_RENNER_A_Grupo JCN - Faz X"   → "181_RENNER_A"
            "OS_068_SANTO_ANTONIO"                → "068_SANTO"
        """
        core = cls._strip_prefix(name)
        parts = core.split("_")
        if len(parts) <= 1:
            return core
        return "_".join(parts[:-1])

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
