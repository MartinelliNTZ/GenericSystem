# -*- coding: utf-8 -*-
"""
FolderStructureUtil — Engine reutilizável de estruturas de pastas padronizadas
==============================================================================
Camada COMPARTILHADA (``utils/`` — Contrato 7) que descreve, valida e materializa
estruturas de pastas em disco. O MESMO sistema serve para as DUAS raízes do
projeto — cada uma com a SUA estrutura declarada em uma subclasse:

    utils.ProjectStructureUtil   → VERRA_Farmer (informação PÚBLICA, pasta-mãe)
    utils.VeraDataStructureUtil  → VERRA_DATA   (informação PRIVADA, backup geral)

Tipos de nó do ``STRUCTURE`` (recursivo):
    None            → pasta vazia (folha)
    { ... }         → pasta contendo os itens do dicionário
    "arquivo.ext"   → ARQUIVO BASE copiado de ``BASE_FILES_DIR``
    BaseFile(...)   → ARQUIVO BASE com opções (origem/conteúdo/sobrescrever)
    Years(...)      → pasta que se expande em uma subpasta por ano

Cada subclasse declara APENAS a sua estrutura:

    ROOT_NAME        — nome da pasta raiz (documentação/log);
    STRUCTURE        — FONTE ÚNICA do conteúdo de UMA pasta-chave;
    KEY_PREFIX       — prefixo das pastas-chave dentro da raiz (ex.: ``OS_``);
    RESERVED_FOLDERS — pastas da raiz que NÃO são pastas-chave;
    BASE_FILES_DIR   — origem dos ARQUIVOS BASE.

Uso:
    from utils.VeraDataStructureUtil import VeraDataStructureUtil

    root = VeraDataStructureUtil.root()
    VeraDataStructureUtil.ensure_mode_folder(root, "220", "Limites")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


# ── Tipos de nó do STRUCTURE ────────────────────────────────────────


@dataclass(frozen=True)
class BaseFile:
    """Arquivo base criado dentro da estrutura.

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


class FolderStructureUtil(BaseUtil):
    """Engine de estruturas de pastas — a estrutura vem SEMPRE da subclasse.

    Toda a estrutura é descrita pelo dicionário ``STRUCTURE``. Alimente/edite
    apenas ele: os valores derivados (``FOLDER_NAMES``, ``FOLDER_TEMPLATES``,
    ``SPECIAL_FOLDER``, ``SPECIAL_ENTRIES`` e ``SPECIAL_TEMPLATE``) são
    calculados por ``derive()`` e consumidos pelos gerenciadores.
    """

    # Nome da pasta raiz (documentação/log).
    ROOT_NAME = ""

    # ══════════════════════════════════════════════════════════════════
    # ESTRUTURA — FONTE ÚNICA (a subclasse alimenta este dicionário)
    # ══════════════════════════════════════════════════════════════════
    STRUCTURE: Dict[str, Any] = {}

    # Prefixo das pastas-chave dentro da raiz (``""`` = sem prefixo).
    KEY_PREFIX = ""

    # Pastas da raiz que NÃO são pastas-chave (ficam de fora da descoberta).
    RESERVED_FOLDERS: Tuple[str, ...] = ()

    # Origem dos ARQUIVOS BASE (``BaseFile.source`` é relativo a esta pasta).
    BASE_FILES_DIR: Path = (
        Path(__file__).resolve().parent.parent / "resources" / "project_templates"
    )

    # ── Derivados de STRUCTURE (calculados por derive()) ────────────
    FOLDER_NAMES: List[str] = []
    FOLDER_TEMPLATES: Dict[str, Any] = {}
    SPECIAL_FOLDER: str = ""
    SPECIAL_ENTRIES: List[int] = []
    SPECIAL_TEMPLATE: Dict[str, Any] = {}

    @classmethod
    def derive(cls) -> None:
        """Calcula os acessores derivados a partir de ``STRUCTURE``."""
        structure = cls.STRUCTURE
        special = next(
            (name for name, node in structure.items() if is_years_node(node)), ""
        )
        special_node = structure.get(special) if special else None

        cls.FOLDER_NAMES = list(structure)
        cls.FOLDER_TEMPLATES = {
            name: node for name, node in structure.items() if isinstance(node, dict)
        }
        cls.SPECIAL_FOLDER = special
        cls.SPECIAL_ENTRIES = list(special_node.years) if special_node else []
        cls.SPECIAL_TEMPLATE = dict(special_node.template) if special_node else {}

    # ── Descoberta ──────────────────────────────────────────────────

    @classmethod
    def is_reserved(cls, name: str) -> bool:
        """Indica se ``name`` é uma pasta RESERVADA da raiz (não é pasta-chave)."""
        reserved = {item.upper() for item in cls.RESERVED_FOLDERS}
        return name.strip().upper() in reserved

    @classmethod
    def discover(
        cls,
        root: Path,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> List[Path]:
        """Retorna as pastas-CHAVE da raiz, ordenadas por nome.

        Pastas reservadas (``RESERVED_FOLDERS``) ficam de fora; quando há
        ``KEY_PREFIX``, apenas as pastas que começam com ele entram.
        """
        logger = cls._get_logger(tool_key, cls.__name__)
        prefix = cls.KEY_PREFIX.upper()
        try:
            folders = [
                path
                for path in Path(root).iterdir()
                if path.is_dir()
                and not cls.is_reserved(path.name)
                and (not prefix or path.name.upper().startswith(prefix))
            ]
        except (PermissionError, FileNotFoundError, OSError) as e:
            logger.error(
                "Falha ao ler a pasta raiz",
                code="FSU_DISCOVER_ERR",
                error=str(e),
                path=str(root),
            )
            return []
        folders.sort(key=lambda path: path.name.lower())
        return folders

    @staticmethod
    def is_special_entry(name: str) -> bool:
        """Indica se ``name`` é uma entrada da pasta especial (ano de 4 dígitos)."""
        return name.isdigit() and len(name) == 4

    # ── Chave da pasta ──────────────────────────────────────────────

    @classmethod
    def _strip_prefix(cls, name: str) -> str:
        """Remove o ``KEY_PREFIX`` do nome da pasta (se presente)."""
        if cls.KEY_PREFIX and name.upper().startswith(cls.KEY_PREFIX.upper()):
            return name[len(cls.KEY_PREFIX):]
        return name

    @classmethod
    def extract_key(cls, name: str) -> str:
        """Extrai a CHAVE de uma pasta-chave — primeiro campo após o prefixo."""
        core = cls._strip_prefix(name)
        parts = core.split("_")
        return cls.normalize_key(parts[0] if parts else core)

    @staticmethod
    def normalize_key(key: str) -> str:
        """Normaliza a CHAVE (texto em MAIÚSCULAS, zeros preservados)."""
        return str(key).strip().upper()

    @staticmethod
    def _key_parts(key: str) -> Optional[Tuple[int, str]]:
        """``(número, letra)`` de uma chave numérica — ``None`` fora desse padrão.

        ``"050"`` → ``(50, "")``; ``"169a"`` → ``(169, "A")``; ``"X1"`` → ``None``.
        """
        match = re.fullmatch(r"(\d+)([A-Z]*)", key)
        if match is None:
            return None
        return (int(match.group(1)), match.group(2))

    @classmethod
    def keys_match(cls, first: str, second: str) -> bool:
        """Indica se DUAS chaves apontam para a MESMA pasta-chave.

        A comparação é EXATA na chave normalizada; quando as duas são numéricas
        (com letra opcional), os **zeros à esquerda não diferenciam** a chave
        (``"50"`` ≡ ``"050"``) — apenas a LETRA diferencia (``"169"`` ≠ ``"169A"``).
        Chaves fora do padrão numérico só casam exatamente.
        """
        left = cls.normalize_key(first)
        right = cls.normalize_key(second)
        if not left or not right:
            return False
        if left == right:
            return True

        parts = cls._key_parts(left)
        return parts is not None and parts == cls._key_parts(right)

    @classmethod
    def folder(
        cls,
        root: Optional[Path],
        key: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[Path]:
        """Pasta-chave da raiz — ``None`` quando não existe.

        A busca é primeiro EXATA pela chave e, sem par exato, TOLERANTE aos zeros
        à esquerda (``"50"`` encontra ``OS_050_...``) — ver ``keys_match``.
        """
        if root is None:
            return None
        target = cls.normalize_key(key)
        if not target:
            return None

        candidates = cls.discover(Path(root), tool_key=tool_key)
        for candidate in candidates:
            if cls.extract_key(candidate.name) == target:
                return candidate

        for candidate in candidates:
            if cls.keys_match(cls.extract_key(candidate.name), target):
                return candidate
        return None

    # ── Caminhos (relativo à raiz — portável entre computadores) ────

    @classmethod
    def to_relative_path(cls, root: Optional[Path], path: str | Path) -> str:
        """Converte ``path`` em caminho RELATIVO à raiz (portável).

        Grava sempre com separador ``/`` para funcionar em qualquer computador.
        Se ``path`` não estiver sob ``root`` (ou ``root`` for vazio), retorna
        apenas o nome final da pasta/arquivo.
        """
        target = Path(path)
        if root is not None:
            try:
                return target.relative_to(Path(root)).as_posix()
            except ValueError:
                pass
        return target.name

    @classmethod
    def resolve_path(cls, root: Optional[Path], rel_path: str | Path) -> Path:
        """Resolve um caminho RELATIVO à raiz (ou devolve o absoluto).

        Caminhos absolutos são retornados como estão (compatibilidade com o
        legado). Caminhos relativos são combinados com ``root``.
        """
        raw = str(rel_path or "").replace("\\", "/").strip()
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate
        base = Path(root) if root is not None else Path("")
        return (base / raw) if raw else base

    # ── Dados já criados (adaptador para o Banco de Dados) ──────────

    @classmethod
    def collect_created(
        cls,
        folder: Path,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, List[str]]:
        """Retorna o que já existe em disco dentro de uma pasta-chave.

        ``folders``: pastas PADRÃO (``FOLDER_NAMES``) presentes em disco;
        ``entries``: subpastas da pasta ESPECIAL (``SPECIAL_FOLDER``) que casam
        com ``is_special_entry`` (ex.: anos de 4 dígitos).
        """
        logger = cls._get_logger(tool_key, cls.__name__)
        folders: List[str] = []
        entries: List[str] = []
        try:
            existing = {
                path.name for path in Path(folder).iterdir() if path.is_dir()
            }
        except (PermissionError, FileNotFoundError, OSError) as e:
            logger.error(
                "Falha ao ler a pasta",
                code="FSU_COLLECT_ERR",
                error=str(e),
                path=str(folder),
            )
            return {"folders": folders, "entries": entries}

        folders = [name for name in cls.FOLDER_NAMES if name in existing]
        if not cls.SPECIAL_FOLDER:
            return {"folders": folders, "entries": entries}

        special = Path(folder) / cls.SPECIAL_FOLDER
        if not special.is_dir():
            return {"folders": folders, "entries": entries}

        try:
            entries = sorted(
                path.name
                for path in special.iterdir()
                if path.is_dir() and cls.is_special_entry(path.name)
            )
        except (PermissionError, FileNotFoundError, OSError) as e:
            logger.error(
                "Falha ao listar as entradas da pasta especial",
                code="FSU_ENTRIES_ERR",
                error=str(e),
                path=str(special),
            )
        return {"folders": folders, "entries": entries}

    # ── Materialização ──────────────────────────────────────────────

    @classmethod
    def ensure_folder(
        cls,
        folder: Path,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Path:
        """Garante que ``folder`` existe em disco (idempotente).

        Levanta OSError em falha de filesystem.
        """
        logger = cls._get_logger(tool_key, cls.__name__)
        target = Path(folder)
        if target.is_dir():
            return target
        target.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Pasta garantida: {target}",
            code="FSU_FOLDER_OK",
            root_name=cls.ROOT_NAME,
            path=str(target),
        )
        return target



