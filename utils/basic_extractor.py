# -*- coding: utf-8 -*-
"""
BasicExtractor — Extrai metadados básicos de arquivos e enriquece JSONs
========================================================================
Fornece dados como nome, tamanho formatado, caminho, diretório,
extensão, datas de criação e modificação.

O fluxo principal é:
    1. Dialog cria JSON temporário via JsonUtil
    2. Dialog chama enrich_json(json_path, file_path)
    3. Extractor lê o JSON, extrai metadados do arquivo, enriquece e salva
    4. Dialog lê o JSON enriquecido e extrai os campos que precisa

Uso:
    from utils.basic_extractor import BasicExtractor

    # Modo direto (retorna dict)
    props = BasicExtractor.extract("c:/arquivo.txt")

    # Modo JSON (enriquece um JSON temporário)
    data = BasicExtractor.enrich_json("c:/temp/123.json", "c:/arquivo.txt")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.FormatUtils import FormatUtils
from utils.JsonUtil import JsonUtil


class BasicExtractor(BaseUtil):
    """Extrai metadados básicos de arquivos do sistema."""

    @staticmethod
    def extract(
        file_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Extrai metadados de um arquivo ou diretório.

        Args:
            file_path: Caminho completo do arquivo.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Dicionário com chaves: name, size, size_formatted, path, directory,
            extension, extension_name, created, modified, is_file, is_dir.
            Retorna dict vazio se o caminho não existir.
        """
        logger = BaseUtil._get_logger(tool_key, "BasicExtractor")
        path = Path(file_path)
        if not path.exists():
            logger.warning("Arquivo nao encontrado", code="EXTRACT_NOT_FOUND", path=file_path)
            return {}

        stat = path.stat()
        result = {
            "name": path.name,
            "size": stat.st_size,
            "size_formatted": FormatUtils.format_size(stat.st_size),
            "path": str(path.resolve()),
            "directory": str(path.parent.resolve()),
            "extension": path.suffix,
            "extension_name": (
                path.suffix[1:].upper() if path.suffix else "(sem extensão)"
            ),
            "created": FormatUtils.format_date(stat.st_ctime),
            "modified": FormatUtils.format_date(stat.st_mtime),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
        }
        logger.info("Metadados extraidos", code="EXTRACT_OK", path=file_path)
        return result

    @staticmethod
    def enrich_json(
        json_path: str,
        file_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Lê um JSON, extrai metadados do arquivo, enriquece e salva.

        Args:
            json_path: Caminho do arquivo JSON (criado via JsonUtil).
            file_path: Caminho do arquivo a extrair metadados.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Dicionário completo com os dados enriquecidos.
            Retorna dict vazio se o arquivo não existir.
        """
        logger = BaseUtil._get_logger(tool_key, "BasicExtractor")
        metadata = BasicExtractor.extract(file_path, tool_key=tool_key)
        if not metadata:
            logger.warning("Nada a enriquecer", code="ENRICH_EMPTY", path=file_path)
            return {}

        result = JsonUtil.update_json(json_path, metadata)
        logger.info("JSON enriquecido com metadados", code="ENRICH_OK", path=file_path)
        return result