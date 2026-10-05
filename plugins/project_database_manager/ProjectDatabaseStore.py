# -*- coding: utf-8 -*-
"""
ProjectDatabaseStore — Persistência do Banco de Dados de Projetos
================================================================
Leitura/escrita dos JSONs em ``<pasta-mãe>/.BancoDados``:

- Um JSON por OS (``<numero_os>.json``) — fonte por projeto.
- Um JSON consolidado (``banco_dados.json``) — agregação de todas as OS.

A gravação é atômica (``<arquivo>.tmp`` + ``os.replace``) para evitar JSON
corrompido em caso de queda. Não decide regras de negócio (isso é do
``ProjectDatabaseService``).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils
from utils.JsonUtil import JsonUtil


class ProjectDatabaseStore(BaseUtil):
    """Grava/lê os JSONs do banco de dados em ``<pasta-mãe>/.BancoDados``."""

    DB_FOLDER = ".BancoDados"
    CONSOLIDATED_FILENAME = "banco_dados.json"
    DB_SCHEMA = 1

    # ── Caminhos ────────────────────────────────────────────────────

    @classmethod
    def db_dir(cls, mother_folder: str | Path) -> Path:
        """Retorna o caminho da pasta ``.BancoDados`` (sem criá-la)."""
        return Path(mother_folder) / cls.DB_FOLDER

    @classmethod
    def ensure_db_dir(
        cls,
        mother_folder: str | Path,
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> Path:
        """Garante a existência da pasta ``.BancoDados`` e a retorna."""
        path = cls.db_dir(mother_folder)
        ExplorerUtils.ensure_directory(str(path), tool_key=tool_key)
        return path

    # ── Escrita ─────────────────────────────────────────────────────

    @classmethod
    def save_project(
        cls,
        mother_folder: str | Path,
        record: Dict[str, Any],
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> None:
        """Grava o JSON individual de uma OS (``<numero_os>.json``)."""
        db = cls.ensure_db_dir(mother_folder, tool_key=tool_key)
        os_number = str(record.get("os") or record.get("name") or "os")
        filename = cls._safe_filename(os_number) + ".json"
        cls._write_json_atomic(db / filename, record, tool_key=tool_key)

    @classmethod
    def save_consolidated(
        cls,
        mother_folder: str | Path,
        data: Dict[str, Any],
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> None:
        """Grava o JSON consolidado (``banco_dados.json``)."""
        db = cls.ensure_db_dir(mother_folder, tool_key=tool_key)
        cls._write_json_atomic(
            db / cls.CONSOLIDATED_FILENAME, data, tool_key=tool_key
        )

    # ── Leitura ─────────────────────────────────────────────────────

    @classmethod
    def load_consolidated(
        cls,
        mother_folder: str | Path,
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> Dict[str, Any]:
        """Lê o JSON consolidado. Retorna ``{}`` se não existir."""
        path = cls.db_dir(mother_folder) / cls.CONSOLIDATED_FILENAME
        return JsonUtil.read_json(str(path), tool_key=tool_key)

    @classmethod
    def prune_projects(
        cls,
        mother_folder: str | Path,
        keep_keys: Iterable[str],
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> None:
        """Remove JSONs de OS que não estão mais no banco (nunca o consolidado).

        Mantém apenas ``<keep_keys>.json`` + ``banco_dados.json``; remove os
        demais ``*.json`` (ex.: chaves antigas de uma regra de nome anterior).
        """
        db = cls.db_dir(mother_folder)
        if not db.is_dir():
            return
        logger = cls._get_logger(tool_key, "ProjectDatabaseStore")
        keep = {cls._safe_filename(key) + ".json" for key in keep_keys}
        keep.add(cls.CONSOLIDATED_FILENAME)
        for path in db.glob("*.json"):
            if path.name in keep:
                continue
            try:
                path.unlink()
                logger.info(
                    "JSON de OS obsoleto removido",
                    code="PDB_PRUNE_OK",
                    path=str(path),
                )
            except OSError as e:
                logger.error(
                    "Falha ao remover JSON obsoleto",
                    code="PDB_PRUNE_ERR",
                    error=str(e),
                    path=str(path),
                )

    # ── Internos ────────────────────────────────────────────────────

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Sanitiza ``name`` para uso como nome de arquivo no Windows."""
        return re.sub(r'[<>:"/\\|?*]', "_", str(name)).strip() or "os"

    @classmethod
    def _write_json_atomic(
        cls,
        path: Path,
        data: Dict[str, Any],
        tool_key: str,
    ) -> None:
        """Escreve ``data`` em ``path`` de forma atômica (tmp + replace)."""
        logger = cls._get_logger(tool_key, "ProjectDatabaseStore")
        tmp = path.with_name(path.name + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
            logger.debug(
                "JSON gravado (atômico)",
                code="PDB_STORE_OK",
                path=str(path),
            )
        except OSError as e:
            logger.error(
                "Falha ao gravar JSON",
                code="PDB_STORE_ERR",
                error=str(e),
                path=str(path),
            )
