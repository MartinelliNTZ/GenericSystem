# -*- coding: utf-8 -*-
"""
FormatUtils — Utilitários de formatação de dados
===================================================
Fornece formatação de tamanho de arquivo e datas de forma
centralizada para todo o sistema.

Uso:
    from utils.FormatUtils import FormatUtils

    size_str = FormatUtils.format_size(1024)
    date_str = FormatUtils.format_date(1234567890.0)
    brasilia = FormatUtils.format_brasilia_date("2026-07-07T00:00:00+00:00")
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class FormatUtils(BaseUtil):
    """Utilitários de formatação de dados."""

    _BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")

    @staticmethod
    def format_size(
        size_bytes: int,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Formata bytes para string legível (B, KB, MB, GB).

        Args:
            size_bytes: Tamanho em bytes.
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "FormatUtils")
        if size_bytes < 1024:
            result = f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            result = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            result = f"{size_bytes / 1024 ** 2:.1f} MB"
        else:
            result = f"{size_bytes / 1024 ** 3:.2f} GB"
        logger.debug("Tamanho formatado", code="FMT_SIZE", bytes=size_bytes, result=result)
        return result

    @staticmethod
    def format_date(
        timestamp: float,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Formata timestamp Unix para string de data dd/mm/AAAA HH:MM:SS.

        Args:
            timestamp: Timestamp Unix.
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "FormatUtils")
        result = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
        logger.debug("Data formatada", code="FMT_DATE", timestamp=timestamp, result=result)
        return result

    @staticmethod
    def format_brasilia_date(
        iso_datetime: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Converte data ISO (UTC) para horário de Brasília.

        Exemplo:
            "2026-07-07T00:00:00+00:00" → "06/07/2026 21:00"
            "2026-07-07T16:00:00+00:00" → "07/07/2026 13:00"

        Args:
            iso_datetime: String ISO 8601 com timezone (ex: "2026-07-07T00:00:00+00:00").
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "FormatUtils")
        try:
            dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
            brasilia_dt = dt.astimezone(FormatUtils._BRASILIA_TZ)
            result = brasilia_dt.strftime("%d/%m/%Y %H:%M")
            logger.debug(
                "Data convertida para Brasília",
                code="FMT_BRASILIA",
                original=iso_datetime,
                result=result,
            )
            return result
        except Exception as e:
            logger.error(
                "Falha ao converter data para Brasília",
                code="FMT_BRASILIA_ERR",
                error=str(e),
            )
            return iso_datetime[:19] if iso_datetime else ""