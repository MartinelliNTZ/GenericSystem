# -*- coding: utf-8 -*-
"""
VeraDataStructureUtil — Estrutura da VERRA_DATA (informação PRIVADA)
====================================================================
Especificação da estrutura PRIVADA — a pasta de BACKUP GERAL da base — montada
sobre o engine compartilhado ``utils.FolderStructureUtil``: o MESMO sistema da
estrutura PÚBLICA ``utils.ProjectStructureUtil``, com estrutura DIFERENTE
(Contrato 7 — cada raiz tem a sua própria declaração).

Raiz: ``<BASE_DADOS>/VERRA_DATA``

    <BASE_DADOS>/VERRA_DATA/Consolidado/limites.shp           → completão de limites
    <BASE_DADOS>/VERRA_DATA/Consolidado/zonas_manejo.shp      → completão de zonas
    <BASE_DADOS>/VERRA_DATA/Consolidado/centroides.shp        → completão de centroides
    <BASE_DADOS>/VERRA_DATA/<OS>/Limites/<OS>_limites.shp     → limites da OS
    <BASE_DADOS>/VERRA_DATA/<OS>/ZM/<OS>_zonas_manejo.shp     → zonas de manejo da OS
    <BASE_DADOS>/VERRA_DATA/<OS>/Centroides/<OS>_centroides.shp → centroides da OS

A raiz é resolvida por ``root()``, nesta ordem:
    1. variável de ambiente ``AETHERIS_VERRA_DATA``;
    2. preferência ``ProjectStructure.verra_data_folder`` (Gerenciador de Estrutura);
    3. ``<pai da pasta-mãe>/BASE_DADOS/VERRA_DATA`` (derivada da pasta-mãe);
    4. ``DEFAULT_ROOT`` (caminho absoluto padrão da instalação).

Uso:
    from utils.VeraDataStructureUtil import VeraDataStructureUtil

    root = VeraDataStructureUtil.root()
    pasta = VeraDataStructureUtil.mode_folder(
        root, "220", VeraDataStructureUtil.LIMITES_FOLDER
    )
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from core.enum.ToolKey import ToolKey
from utils.FolderStructureUtil import FolderStructureUtil
from utils.Preferences import Preferences

_TOOL = ToolKey.PROJECT_STRUCTURE.value


class VeraDataStructureUtil(FolderStructureUtil):
    """FONTE ÚNICA da estrutura PRIVADA (``VERRA_DATA``) — backup geral da base.

    A estrutura de UMA pasta de OS é o ``STRUCTURE`` (``Limites`` + ``ZM`` +
    ``Centroides``); os
    completões de todos os modos ficam agrupados na pasta RESERVADA
    ``Consolidado`` (que não é uma pasta de OS).
    """

    # Identificação da raiz.
    ROOT_NAME = "VERRA_DATA"
    ROOT_FOLDER_NAME = "VERRA_DATA"
    DATA_ROOT_FOLDER = "BASE_DADOS"

    # Sobrescritas da raiz (ambiente/preferência).
    ENV_VAR = "AETHERIS_VERRA_DATA"
    PREF_KEY = "verra_data_folder"

    # Raiz padrão da instalação (último recurso do ``root()``).
    DEFAULT_ROOT = (
        r"C:\Users\MatheusMartinelli\OneDrive - Agrorobotica Fotonica Em Certificacoes "
        r"Agroambientais\BASE_DADOS\VERRA_DATA"
    )

    # Pastas da raiz que NÃO são pastas de OS.
    CONSOLIDATED_FOLDER = "Consolidado"

    # Pastas de dados DENTRO da pasta da OS (uma por modo da Base de Limites).
    LIMITES_FOLDER = "Limites"
    ZONAS_FOLDER = "ZM"
    CENTROIDES_FOLDER = "Centroides"

    # As pastas de OS são nomeadas apenas pela CHAVE (sem prefixo).
    KEY_PREFIX = ""
    RESERVED_FOLDERS = (CONSOLIDATED_FOLDER,)

    # ══════════════════════════════════════════════════════════════════
    # ESTRUTURA — FONTE ÚNICA do conteúdo de UMA pasta de OS
    # ══════════════════════════════════════════════════════════════════
    STRUCTURE: Dict[str, Any] = {
        LIMITES_FOLDER: None,
        ZONAS_FOLDER: None,
        CENTROIDES_FOLDER: None,
    }

    # ── Raiz ────────────────────────────────────────────────────────

    @classmethod
    def root(cls, tool_key: str = _TOOL) -> Path:
        """Raiz da VERRA_DATA (ordem de resolução no topo do módulo)."""
        env = os.environ.get(cls.ENV_VAR, "").strip()
        if env:
            return Path(env).expanduser()

        prefs = cls._prefs(tool_key)
        configured = str(prefs.get(cls.PREF_KEY, "") or "").strip()
        if configured:
            return Path(configured).expanduser()

        derived = cls._derived_root(prefs.get("mother_folder", ""))
        if derived is not None:
            return derived

        return Path(cls.DEFAULT_ROOT)

    @classmethod
    def root_str(cls, tool_key: str = _TOOL) -> str:
        """Raiz da VERRA_DATA como texto (para ``default_factory`` de configs)."""
        return str(cls.root(tool_key))

    @classmethod
    def _prefs(cls, tool_key: str) -> Dict[str, Any]:
        """Preferências do Gerenciador de Estrutura (pasta-mãe + raiz da VERRA_DATA)."""
        logger = cls._get_logger(tool_key, cls.__name__)
        try:
            return Preferences.load_tool_prefs(
                ToolKey.PROJECT_STRUCTURE,
                caller_tool_key=tool_key,
            )
        except Exception as e:
            logger.error(
                "Falha ao carregar as preferências de estrutura",
                code="VDS_PREFS_ERR",
                error=str(e),
            )
            return {}

    @classmethod
    def _derived_root(cls, mother: Any) -> Optional[Path]:
        """``<pai da pasta-mãe>/BASE_DADOS/VERRA_DATA`` — ``None`` sem pasta-mãe."""
        text = str(mother or "").strip()
        if not text:
            return None
        return (
            Path(text).expanduser().parent
            / cls.DATA_ROOT_FOLDER
            / cls.ROOT_FOLDER_NAME
        )

    # ── Caminhos da estrutura ───────────────────────────────────────

    @classmethod
    def consolidated_folder(cls, root: Optional[Path] = None) -> Path:
        """Pasta dos completões (``Consolidado``) — criada sob demanda."""
        return Path(root or cls.root()) / cls.CONSOLIDATED_FOLDER

    @classmethod
    def os_folder(cls, root: Optional[Path], os_key: str) -> Path:
        """Pasta de UMA OS dentro da raiz (nomeada apenas pela chave)."""
        return Path(root or cls.root()) / cls.normalize_key(os_key)

    @classmethod
    def mode_folder(
        cls,
        root: Optional[Path],
        os_key: str,
        folder_name: str,
    ) -> Path:
        """Pasta de um modo (``Limites`` | ``ZM``) dentro da pasta da OS."""
        return cls.os_folder(root, os_key) / folder_name

    # ── Materialização ──────────────────────────────────────────────

    @classmethod
    def ensure_root_folders(
        cls,
        root: Optional[Path] = None,
        tool_key: str = _TOOL,
    ) -> Path:
        """Garante a raiz e as pastas RESERVADAS (``Consolidado``) em disco."""
        base = Path(root or cls.root())
        cls.ensure_folder(base, tool_key=tool_key)
        cls.ensure_folder(base / cls.CONSOLIDATED_FOLDER, tool_key=tool_key)
        return base

    @classmethod
    def ensure_mode_folder(
        cls,
        root: Optional[Path],
        os_key: str,
        folder_name: str,
        tool_key: str = _TOOL,
    ) -> Path:
        """Garante a pasta de um modo (``Limites`` | ``ZM``) da OS em disco."""
        return cls.ensure_folder(
            cls.mode_folder(root, os_key, folder_name), tool_key=tool_key
        )


VeraDataStructureUtil.derive()

