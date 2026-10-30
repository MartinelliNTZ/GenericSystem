# -*- coding: utf-8 -*-
"""
ProjectStructureUtil — Estrutura PADRÃO dos projetos (VERRA_Farmer) — PÚBLICA
=============================================================================
Especificação da estrutura PÚBLICA (pasta-mãe ``VERRA_Farmer``), montada sobre o
engine compartilhado ``utils.FolderStructureUtil`` — o MESMO sistema usado pela
estrutura PRIVADA ``utils.VeraDataStructureUtil`` (Contrato 7).

FONTE ÚNICA (single source of truth): ``ProjectStructureUtil.PROJECT_STRUCTURE``
(o ``STRUCTURE`` do engine). Alimente e edite apenas ele; os valores derivados
(``DEFAULT_PROJECT_FOLDERS``, ``PROJECT_FOLDER_TEMPLATES``,
``DOCUMENT_YEARS_FOLDER``, ``DEFAULT_YEARS`` e ``DOCUMENT_TEMPLATE``) são
calculados a partir dele e consumidos pelo Gerenciador de Estrutura, pelo Banco
de Dados e pelas cores das pastas.

Tipos de nó do dicionário (ver ``utils.FolderStructureUtil``):
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

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.enum.ToolKey import ToolKey
from utils.FolderStructureUtil import (
    BaseFile,
    FolderStructureUtil,
    Years,
    file_spec,
    is_file_node,
    is_years_node,
)


class ProjectStructureUtil(FolderStructureUtil):
    """FONTE ÚNICA da estrutura PÚBLICA dos projetos (pasta-mãe ``VERRA_Farmer``).

    Toda a estrutura é descrita por ``PROJECT_STRUCTURE``. Alimente/edite apenas
    ele: os valores derivados (``DEFAULT_PROJECT_FOLDERS``,
    ``PROJECT_FOLDER_TEMPLATES``, ``DOCUMENT_YEARS_FOLDER``, ``DEFAULT_YEARS`` e
    ``DOCUMENT_TEMPLATE``) são calculados a partir dele e consumidos pelo
    Gerenciador de Estrutura, pelo Banco de Dados e pelas cores das pastas.
    """

    # Pasta raiz desta estrutura (informação PÚBLICA).
    ROOT_NAME = "VERRA_Farmer"

    # Prefixo das pastas-chave (projetos) dentro da pasta-mãe.
    KEY_PREFIX = "OS_"

    # Compatibilidade: a API histórica usa o nome PROJECT_PREFIX.
    PROJECT_PREFIX = KEY_PREFIX

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
        "08_LIMITES": {
            "TALHOES": None,
            "AREAS_DE_CONTROLE": None,
        },
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

    # A estrutura consumida pelo engine é o próprio PROJECT_STRUCTURE.
    STRUCTURE = PROJECT_STRUCTURE

    # ── API pública histórica (delega para o engine) ────────────────

    @classmethod
    def discover_projects(
        cls,
        mother: Path,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> List[Path]:
        """Retorna as pastas de projeto (prefixo ``OS_``) ordenadas por nome."""
        return cls.discover(mother, tool_key=tool_key)

    @staticmethod
    def is_year_folder(name: str) -> bool:
        """Indica se ``name`` é uma pasta de ano (4 dígitos numéricos)."""
        return FolderStructureUtil.is_special_entry(name)

    @classmethod
    def extract_os(cls, name: str) -> str:
        """Extrai a CHAVE da OS — o primeiro campo após o prefixo ``OS_``.

        A OS é **TEXTO** (nunca inteiro) e a diferenciação é feita pela LETRA:
        ``OS_169A_AGUA_VIVA`` → ``169A``. Os zeros à esquerda são PRESERVADOS
        (``OS_039_Bunge`` → ``039``).

            "OS_234_Cliente"    → "234"
            "OS_039_Bunge"      → "039"
            "OS_169A_AGUA_VIVA" → "169A"
            "OS_181C_RENNER..." → "181C"
        """
        return cls.extract_key(name)

    @staticmethod
    def normalize_os(os_key: str) -> str:
        """Normaliza a CHAVE da OS (texto em MAIÚSCULAS, zeros preservados).

        ``"039"`` continua ``"039"`` (a OS é texto — nunca inteiro) e ``"169a"``
        vira ``"169A"``.
        """
        return FolderStructureUtil.normalize_key(os_key)

    @classmethod
    def same_os(cls, first: str, second: str) -> bool:
        """Indica se DUAS chaves são a MESMA OS (zeros à esquerda NÃO diferenciam).

        A chave oficial continua sendo a que está na pasta/banco (``050``), mas a
        comparação aceita a forma sem os zeros à esquerda (``50`` ≡ ``050``) — a
        LETRA continua diferenciando (``169`` ≠ ``169A``). Chaves fora do padrão
        numérico só casam exatamente.
        """
        return cls.keys_match(first, second)

    @classmethod
    def project_folder(
        cls,
        mother: Optional[Path],
        os_key: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[Path]:
        """Pasta do projeto (OS) na pasta-mãe — ``None`` quando não existe.

        Localiza a pasta ``OS_<chave>...`` cuja chave bate com ``os_key``
        (ex.: ``169A`` → ``OS_169A_AGUA_VIVA``); sem par exato, aceita a chave
        sem os zeros à esquerda (``50`` → ``OS_050_Sementes Tropical``) — ver
        ``same_os``.
        """
        return cls.folder(mother, os_key, tool_key=tool_key)

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
        data = cls.collect_created(project, tool_key=tool_key)
        return {"folders": data["folders"], "years": data["entries"]}


# ── Derivados de PROJECT_STRUCTURE (NÃO edite — calculados a partir dele) ──
ProjectStructureUtil.derive()

# Compatibilidade: os nomes históricos apontam para os derivados do engine.
ProjectStructureUtil.DEFAULT_PROJECT_FOLDERS = ProjectStructureUtil.FOLDER_NAMES
ProjectStructureUtil.PROJECT_FOLDER_TEMPLATES = ProjectStructureUtil.FOLDER_TEMPLATES
ProjectStructureUtil.DOCUMENT_YEARS_FOLDER = ProjectStructureUtil.SPECIAL_FOLDER
ProjectStructureUtil.DEFAULT_YEARS = ProjectStructureUtil.SPECIAL_ENTRIES
ProjectStructureUtil.DOCUMENT_TEMPLATE = ProjectStructureUtil.SPECIAL_TEMPLATE


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


