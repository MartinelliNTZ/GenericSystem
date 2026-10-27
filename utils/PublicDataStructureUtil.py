# -*- coding: utf-8 -*-
"""
PublicDataStructureUtil — Estrutura da BASE PÚBLICA (BASE_DADOS/PUBLICOS)
========================================================================
FONTE ÚNICA da pasta das BASES PÚBLICAS — as malhas OFICIAIS de referência
(shapefiles de domínio público) usadas pelas ferramentas OFFLINE do Aetheris
ToolBox. Hoje ela hospeda as MALHAS do IBGE lidas pelos enriquecimentos dos
centroides da Base de Limites: a MALHA MUNICIPAL (``IBGE_BR_Municipios_<ano>``,
por ``utils.LocalidadeApi``) e a MALHA DE BIOMAS (``IBGE_BIOMAS``, por
``utils.BiomaApi``).

Raiz: ``<BASE_DADOS>/PUBLICOS``

    <BASE_DADOS>/PUBLICOS/IBGE_BR_Municipios_2025/BR_Municipios_2025.shp
    <BASE_DADOS>/PUBLICOS/IBGE_BIOMAS/lml_bioma_e250k_v20250911_A.shp

A raiz é resolvida por ``root()``, nesta ordem:
    1. variável de ambiente ``AETHERIS_PUBLIC_DATA``;
    2. preferência ``ProjectStructure.public_data_folder`` (Gerenciador de Estrutura);
    3. ``<pai da pasta-mãe>/BASE_DADOS/PUBLICOS`` (derivada da pasta-mãe);
    4. ``DEFAULT_ROOT`` (caminho absoluto padrão da instalação).

ATUALIZAR A BASE PÚBLICA é só trocar os arquivos em disco: a versão MAIS NOVA é
descoberta automaticamente — pasta do ANO mais recente (``IBGE_BR_Municipios_2026``
> ``..._2025``) e shape mais novo da pasta (``lml_bioma_e250k_v<AAAAMMDD>_A.shp``)
— sem reconfigurar nada.

Uso:
    from utils.PublicDataStructureUtil import PublicDataStructureUtil

    PublicDataStructureUtil.municipios_shape()   # .../IBGE_BR_Municipios_2025/BR_Municipios_2025.shp
    PublicDataStructureUtil.biomas_shape()       # .../IBGE_BIOMAS/lml_bioma_e250k_v20250911_A.shp
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.Preferences import Preferences

_TOOL = ToolKey.PROJECT_STRUCTURE.value


class PublicDataStructureUtil(BaseUtil):
    """FONTE ÚNICA da pasta das BASES PÚBLICAS (``<BASE_DADOS>/PUBLICOS``)."""

    # Identificação da raiz.
    ROOT_FOLDER_NAME = "PUBLICOS"
    DATA_ROOT_FOLDER = "BASE_DADOS"

    # Sobrescritas da raiz (ambiente/preferência).
    ENV_VAR = "AETHERIS_PUBLIC_DATA"
    PREF_KEY = "public_data_folder"

    # Raiz padrão da instalação (último recurso do ``root()``).
    DEFAULT_ROOT = (
        r"C:\Users\MatheusMartinelli\OneDrive - Agrorobotica Fotonica Em Certificacoes "
        r"Agroambientais\BASE_DADOS\PUBLICOS"
    )

    # Malha municipal do IBGE (pasta por ANO + shape interno).
    MUNICIPIOS_FOLDER_PREFIX = "IBGE_BR_Municipios"
    MUNICIPIOS_STEM_PREFIX = "BR_Municipios"
    MUNICIPIOS_SHAPE_ENV = "AETHERIS_IBGE_MUNICIPIOS"

    # Malha de biomas do IBGE (pasta unica + shape por versao).
    BIOMAS_FOLDER_PREFIX = "IBGE_BIOMAS"
    BIOMAS_STEM_PREFIX = "lml_bioma"
    BIOMAS_SHAPE_ENV = "AETHERIS_IBGE_BIOMAS"

    # ── Raiz ────────────────────────────────────────────────────────

    @classmethod
    def root(cls, tool_key: str = _TOOL) -> Path:
        """Raiz da BASE PÚBLICA (ambiente → preferência → derivada → padrão)."""
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
        """Raiz da BASE PÚBLICA como texto."""
        return str(cls.root(tool_key))

    @classmethod
    def _prefs(cls, tool_key: str) -> Dict[str, Any]:
        """Preferências do Gerenciador de Estrutura (pasta-mãe + raiz pública)."""
        logger = cls._get_logger(tool_key, cls.__name__)
        try:
            return Preferences.load_tool_prefs(
                ToolKey.PROJECT_STRUCTURE,
                caller_tool_key=tool_key,
            )
        except Exception as e:
            logger.error(
                "Falha ao carregar as preferências de estrutura",
                code="PDS_PREFS_ERR",
                error=str(e),
            )
            return {}

    @classmethod
    def _derived_root(cls, mother: Any) -> Optional[Path]:
        """``<pai da pasta-mãe>/BASE_DADOS/PUBLICOS`` — ``None`` sem pasta-mãe."""
        text = str(mother or "").strip()
        if not text:
            return None
        return (
            Path(text).expanduser().parent
            / cls.DATA_ROOT_FOLDER
            / cls.ROOT_FOLDER_NAME
        )

    # ── Malhas do IBGE ──────────────────────────────────────────────

    @classmethod
    def municipios_shape(
        cls,
        root: Optional[Path] = None,
        tool_key: str = _TOOL,
    ) -> Optional[Path]:
        """Shape da malha municipal MAIS NOVA — ``None`` quando nao existe.

        A variavel de ambiente ``AETHERIS_IBGE_MUNICIPIOS`` (arquivo) tem
        prioridade; sem ela, procura ``IBGE_BR_Municipios_*`` dentro da raiz e
        escolhe a pasta do ANO mais recente (``2026`` > ``2025``).
        """
        return cls._find_shape(
            cls.MUNICIPIOS_FOLDER_PREFIX,
            cls.MUNICIPIOS_STEM_PREFIX,
            cls.MUNICIPIOS_SHAPE_ENV,
            root,
        )

    @classmethod
    def biomas_shape(
        cls,
        root: Optional[Path] = None,
        tool_key: str = _TOOL,
    ) -> Optional[Path]:
        """Shape da malha de BIOMAS — ``None`` quando nao existe.

        A variavel de ambiente ``AETHERIS_IBGE_BIOMAS`` (arquivo) tem
        prioridade; sem ela, procura ``IBGE_BIOMAS*`` dentro da raiz e usa o
        shape mais NOVO da pasta (``lml_bioma_e250k_v<AAAAMMDD>_A.shp``).
        """
        return cls._find_shape(
            cls.BIOMAS_FOLDER_PREFIX,
            cls.BIOMAS_STEM_PREFIX,
            cls.BIOMAS_SHAPE_ENV,
            root,
        )

    @classmethod
    def _find_shape(
        cls,
        folder_prefix: str,
        stem_prefix: str,
        env_var: str,
        root: Optional[Path] = None,
    ) -> Optional[Path]:
        """Shape de uma malha: arquivo forcado por ambiente ou o MAIS NOVO da raiz."""
        forced = os.environ.get(env_var, "").strip()
        if forced:
            candidate = Path(forced).expanduser()
            return candidate if candidate.is_file() else None

        for folder in cls.malha_folders(folder_prefix, root):
            shape = cls._shape_in(folder, stem_prefix)
            if shape is not None:
                return shape

        return None

    @classmethod
    def municipios_folders(cls, root: Optional[Path] = None) -> List[Path]:
        """Pastas da malha municipal (``IBGE_BR_Municipios_*``), da MAIS NOVA."""
        return cls.malha_folders(cls.MUNICIPIOS_FOLDER_PREFIX, root)

    @classmethod
    def biomas_folders(cls, root: Optional[Path] = None) -> List[Path]:
        """Pastas da malha de biomas (``IBGE_BIOMAS*``), da MAIS NOVA."""
        return cls.malha_folders(cls.BIOMAS_FOLDER_PREFIX, root)

    @classmethod
    def malha_folders(cls, prefix: str, root: Optional[Path] = None) -> List[Path]:
        """Pastas de uma malha (``prefix*``) dentro da base publica, da MAIS NOVA."""
        base = Path(root or cls.root())
        if not base.is_dir():
            return []

        folders = [
            entry
            for entry in base.iterdir()
            if entry.is_dir() and entry.name.startswith(prefix)
        ]
        return sorted(folders, key=cls._folder_rank, reverse=True)

    @staticmethod
    def _folder_rank(folder: Path) -> Tuple[int, float, str]:
        """Ordena as pastas pelo ANO do nome (sem ano, pela data de modificacao)."""
        match = re.search(r"(\d{4})", folder.name)
        if match:
            return int(match.group(1)), folder.stat().st_mtime, folder.name
        return 0, folder.stat().st_mtime, folder.name

    @classmethod
    def _shape_in(cls, folder: Path, stem_prefix: str) -> Optional[Path]:
        """Shape MAIS NOVO de uma pasta (``stem_prefix*`` preferido)."""
        preferred = sorted(folder.glob(f"{stem_prefix}*.shp"))
        if preferred:
            return preferred[-1]

        found = sorted(folder.glob("*.shp"))
        return found[-1] if len(found) == 1 else None
