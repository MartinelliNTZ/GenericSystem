# -*- coding: utf-8 -*-
"""
OsReportHtmlGenerator — Template HTML + dados → relatório
=========================================================
Preenche o TEMPLATE HTML do relatório geral do projeto com os dados da OS e
salva o arquivo na pasta da OS.

O template (``core/template/relatorio_geral_projeto.html``) é a FONTE do layout
e vive SEPARADO dos seus assets — a folha de estilo
(``relatorio_geral_projeto.css``) e o comportamento
(``relatorio_geral_projeto.js``). Quem UNE os três num só documento é o
``OsReportAssets``: ele embute o CSS e o JS no HTML, de modo que o ``.HTML``
gerado é autossuficiente (só depende das CDNs do Leaflet).

O template fica com o token ``<!--{{DADOS_PROJETO}}-->`` e o gerador troca esse
token por um ``<script>`` que define ``window.DADOS_PROJETO``. Para mudar o
relatório (textos, ordem, painéis), basta editar os arquivos do template —
nenhuma alteração de código é necessária.

O DESTINO é o mesmo do relatório da OS (``OsReportGenerator``):
``<pasta da OS>/14_RELATORIOS/<TIPO>/OS_<chave>_<TIPO>_<AAAAMMDDHHMMSS>.HTML``

Uso:
    from plugins.os_tracker.report.OsReportHtmlGenerator import OsReportHtmlGenerator

    path = OsReportHtmlGenerator.generate(
        data, os_folder="C:/.../OS_220", os_key="220", tool_key=ToolKey.OS_TRACKER.value
    )
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.enum.ToolKey import ToolKey
from utils.OsReportGenerator import OsReportGenerator

from plugins.os_tracker.report.OsReportAssets import OsReportAssets


class OsReportHtmlGenerator(OsReportGenerator):
    """Gera o relatório geral do projeto em HTML a partir do template."""

    # Extensão do relatório (mesma pasta/tipo do relatório Word).
    OUTPUT_SUFFIX = ".HTML"
    # Token do template que recebe o script com os dados do projeto.
    TOKEN = "<!--{{DADOS_PROJETO}}-->"
    SCRIPT_TEMPLATE = "<script>window.DADOS_PROJETO = {data};</script>"
    # Escape de fim de tag dentro da string JSON (segurança no HTML).
    _SCRIPT_END = "</"

    # ── API pública ─────────────────────────────────────────────────

    @classmethod
    def generate(
        cls,
        data: Dict[str, Any],
        os_folder: str | Path = "",
        os_key: str = "",
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> str:
        """Preenche o template e salva o relatório na pasta da OS.

        Args:
            data: Objeto ``DADOS_PROJETO`` do template.
            os_folder: Pasta da OS (destino: ``14_RELATORIOS/<TIPO>``).
            os_key: Chave da OS (entra no nome do arquivo).
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho absoluto do ``.HTML`` gerado.

        Raises:
            FileNotFoundError: se o template não existir.
            ValueError: se o template não tiver o token de dados.
        """
        logger = cls._get_logger(tool_key, "OsReportHtmlGenerator")
        html = OsReportAssets.html(tool_key)
        if cls.TOKEN not in html:
            logger.error(
                "Token de dados ausente no template HTML",
                code="OSREP_HTML_TOKEN_MISSING",
                token=cls.TOKEN,
            )
            raise ValueError(f"Template sem o token de dados: {cls.TOKEN}")

        target = cls.report_path(os_folder, os_key, tool_key)
        target.write_text(cls._render(html, data), encoding="utf-8")
        logger.info(
            "Relatório HTML da OS gerado",
            code="OSREP_HTML_GENERATED",
            path=str(target),
        )
        return str(target)

    # ── Render ──────────────────────────────────────────────────────

    @classmethod
    def _render(cls, html: str, data: Dict[str, Any]) -> str:
        """Troca o token de dados pelo script com o objeto do projeto."""
        payload = json.dumps(data or {}, ensure_ascii=False).replace(
            cls._SCRIPT_END, "<\\/"
        )
        return html.replace(cls.TOKEN, cls.SCRIPT_TEMPLATE.format(data=payload))
