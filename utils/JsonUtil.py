# -*- coding: utf-8 -*-
"""
JsonUtil — Criação e manipulação de JSONs temporários
=======================================================
Centraliza operações de criar, ler, escrever e manipular
arquivos JSON em diretório temporário gerenciado pelo sistema.

Uso:
    from utils.JsonUtil import JsonUtil

    path = JsonUtil.create_temp_json({"key": "value"})
    data = JsonUtil.read_json(path)
    JsonUtil.write_json(path, data)
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils


_TEMP_DIR = "file_preview"


class JsonUtil(BaseUtil):
    """Utilitário para criar e manipular JSONs em pasta temporária."""

    @staticmethod
    def _get_temp_dir(
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Retorna e garante a existência do diretório temporário de JSONs.

        Args:
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "JsonUtil")
        config_dir = ExplorerUtils.get_plugin_config_dir(_TEMP_DIR, tool_key=tool_key)
        temp_dir = str(config_dir / "temp")
        os.makedirs(temp_dir, exist_ok=True)
        logger.debug("Diretorio temp JSON garantido", code="JSON_TEMP_DIR", path=temp_dir)
        return temp_dir

    @staticmethod
    def create_temp_json(
        data: Optional[Dict[str, Any]] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Cria um arquivo JSON temporário com dados iniciais.

        Args:
            data: Dicionário inicial (vazio se None).
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho absoluto do arquivo JSON criado.
        """
        logger = BaseUtil._get_logger(tool_key, "JsonUtil")
        if data is None:
            data = {}

        temp_dir = JsonUtil._get_temp_dir(tool_key=tool_key)
        file_name = f"preview_{uuid.uuid4().hex}.json"
        file_path = os.path.join(temp_dir, file_name)

        JsonUtil.write_json(file_path, data, tool_key=tool_key)
        logger.info("JSON temporario criado", code="JSON_CREATE", path=file_path)
        return file_path

    @staticmethod
    def read_json(
        file_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Lê e retorna o conteúdo de um arquivo JSON.

        Args:
            file_path: Caminho do arquivo JSON.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Dicionário com os dados, ou dict vazio se não existir.
        """
        logger = BaseUtil._get_logger(tool_key, "JsonUtil")
        if not os.path.exists(file_path):
            logger.warning("Arquivo JSON nao encontrado", code="JSON_READ_NOT_FOUND", path=file_path)
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = dict(json.load(f))
            logger.debug("JSON lido com sucesso", code="JSON_READ_OK", path=file_path)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Erro ao ler JSON", code="JSON_READ_ERR", path=file_path, error=str(e))
            return {}

    @staticmethod
    def write_json(
        file_path: str,
        data: Dict[str, Any],
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """
        Escreve dados em um arquivo JSON (sobrescreve).

        Args:
            file_path: Caminho do arquivo JSON.
            data: Dicionário a ser salvo.
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "JsonUtil")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("JSON escrito com sucesso", code="JSON_WRITE_OK", path=file_path)
        except OSError as e:
            logger.error("Erro ao escrever JSON", code="JSON_WRITE_ERR", path=file_path, error=str(e))

    @staticmethod
    def update_json(
        file_path: str,
        updates: Dict[str, Any],
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Lê um JSON, aplica atualizações e salva de volta.

        Args:
            file_path: Caminho do arquivo JSON.
            updates: Dicionário com campos a atualizar/inserir.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Dicionário completo após atualização.
        """
        logger = BaseUtil._get_logger(tool_key, "JsonUtil")
        data = JsonUtil.read_json(file_path, tool_key=tool_key)
        data.update(updates)
        JsonUtil.write_json(file_path, data, tool_key=tool_key)
        logger.debug("JSON atualizado", code="JSON_UPDATE_OK", path=file_path, keys=list(updates.keys()))
        return data

    @staticmethod
    def cleanup_temp_json(
        file_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """
        Remove um arquivo JSON temporário.

        Args:
            file_path: Caminho do arquivo a remover.
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "JsonUtil")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("JSON temporario removido", code="JSON_CLEANUP_OK", path=file_path)
            else:
                logger.debug("JSON temporario ja nao existe", code="JSON_CLEANUP_GONE", path=file_path)
        except OSError as e:
            logger.error("Erro ao remover JSON temporario", code="JSON_CLEANUP_ERR", path=file_path, error=str(e))