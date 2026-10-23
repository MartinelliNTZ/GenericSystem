# -*- coding: utf-8 -*-
"""
OsReportHtmlService — Fachada do Relatório Geral do Projeto (HTML)
=================================================================
Ponto ÚNICO de entrada do submódulo: resolve a fonte (pasta/arquivos da OS),
monta os dados do template (schema + painéis) e gera o arquivo HTML.

O plugin do Acompanhamento de OS conhece apenas esta classe — os painéis, o
leitor de shapes e o gerador ficam encapsulados aqui.

Uso:
    from plugins.os_tracker.report.OsReportHtmlService import OsReportHtmlService

    path = OsReportHtmlService.generate(mother, record, tool_key=ToolKey.OS_TRACKER.value)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil

from plugins.os_tracker.report.OsReportHtmlGenerator import OsReportHtmlGenerator
from plugins.os_tracker.report.ReportDataBuilder import ReportDataBuilder
from plugins.os_tracker.report.ReportSource import ReportSource


class OsReportHtmlService(BaseUtil):
    """Gera o relatório geral do projeto (HTML) de uma OS."""

    @classmethod
    def generate(
        cls,
        mother: Optional[Path],
        record: Optional[Dict[str, Any]],
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> str:
        """Gera o relatório HTML da OS e devolve o caminho do arquivo.

        Args:
            mother: Pasta-mãe dos projetos (resolve os caminhos da OS).
            record: Registro da OS vindo do banco.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho absoluto do ``.HTML`` gerado.
        """
        logger = cls._get_logger(tool_key, "OsReportHtmlService")
        os_key = str((record or {}).get("os", "") or "")
        context = ReportSource.context(mother, record, tool_key)
        data = ReportDataBuilder.build(context)
        path = OsReportHtmlGenerator.generate(
            data,
            os_folder=ReportSource.os_folder(mother, record),
            os_key=os_key,
            tool_key=tool_key,
        )
        logger.info(
            "Relatório geral do projeto (HTML) gerado",
            code="OSREP_SERVICE_DONE",
            os_key=os_key,
            path=path,
        )
        return path
