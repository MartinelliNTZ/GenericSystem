# -*- coding: utf-8 -*-
"""
OsReportAssets — Une HTML + CSS + JS do relatório num só documento
==================================================================
Lê o TEMPLATE do relatório (``core/template/relatorio_geral_projeto.html``) e os
seus dois assets — a folha de estilo (``.css``) e o comportamento (``.js``) — e
devolve o documento com os dois EMBUTIDOS, pronto para virar um ``.HTML``
autossuficiente (sem depender de arquivos ao lado).

Os três arquivos vivem separados porque cada um tem o seu papel:

| Arquivo | Papel |
|---|---|
| ``relatorio_geral_projeto.html`` | Estrutura (painéis, tokens de dados/estilos/scripts) |
| ``relatorio_geral_projeto.css`` | Estilos do relatório |
| ``relatorio_geral_projeto.js`` | Comportamento (painéis, mapas, menu, descrições) |

O template aponta para os irmãos por ``<link>``/``<script src>`` — abrir o
template direto no navegador continua mostrando o layout — e esta classe troca
essas duas tags pelo conteúdo embutido. O token ``<!--{{DADOS_PROJETO}}-->``
NÃO é tratado aqui: quem o substitui é o ``OsReportHtmlGenerator``.

Uso:
    from plugins.os_tracker.report.OsReportAssets import OsReportAssets

    html = OsReportAssets.html(tool_key=ToolKey.OS_TRACKER.value)
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class OsReportAssets(BaseUtil):
    """Une o template HTML e os seus assets (CSS/JS) num só documento."""

    # Pasta dos templates do sistema (a mesma do template Word da OS).
    FOLDER: Path = Path(__file__).resolve().parents[3] / "core" / "template"
    HTML_FILE = "relatorio_geral_projeto.html"
    CSS_FILE = "relatorio_geral_projeto.css"
    JS_FILE = "relatorio_geral_projeto.js"

    # Tags do template trocadas pelo conteúdo embutido (e o molde de cada uma).
    CSS_TAG = f'<link rel="stylesheet" href="{CSS_FILE}">'
    JS_TAG = f'<script src="{JS_FILE}"></script>'
    CSS_TEMPLATE = "<style>\n{css}\n</style>"
    JS_TEMPLATE = "<script>\n{js}\n</script>"

    # ── API pública ─────────────────────────────────────────────────

    @classmethod
    def html(cls, tool_key: str = ToolKey.OS_TRACKER.value) -> str:
        """Documento do relatório com o CSS e o JS embutidos.

        Args:
            tool_key: Chave da ferramenta para logging.

        Returns:
            HTML do template com os dois assets embutidos (o token de dados
            permanece, para o ``OsReportHtmlGenerator`` substituí-lo).

        Raises:
            FileNotFoundError: se algum dos três arquivos não existir.
            ValueError: se o template não tiver as tags dos assets.
        """
        logger = cls._get_logger(tool_key, "OsReportAssets")
        template, css, js = cls._read_all(tool_key)
        cls._exigir_tag(template, cls.CSS_TAG, tool_key)
        cls._exigir_tag(template, cls.JS_TAG, tool_key)

        document = template.replace(cls.CSS_TAG, cls.CSS_TEMPLATE.format(css=css))
        document = document.replace(cls.JS_TAG, cls.JS_TEMPLATE.format(js=js))
        logger.info(
            "Assets do relatório embutidos no HTML",
            code="OSREP_ASSETS_DONE",
            folder=str(cls.FOLDER),
        )
        return document

    # ── Leitura dos assets ──────────────────────────────────────────

    @classmethod
    def _read_all(cls, tool_key: str) -> Tuple[str, str, str]:
        """Conteúdo do template, do CSS e do JS (na ordem de uso)."""
        return (
            cls._read(cls.HTML_FILE, tool_key),
            cls._read(cls.CSS_FILE, tool_key),
            cls._read(cls.JS_FILE, tool_key),
        )

    @classmethod
    def _read(cls, name: str, tool_key: str) -> str:
        """Conteúdo de um arquivo do relatório.

        Raises:
            FileNotFoundError: se o arquivo não existir na pasta dos templates.
        """
        logger = cls._get_logger(tool_key, "OsReportAssets")
        path = cls.FOLDER / name
        if not path.exists():
            logger.error(
                "Arquivo do relatório não encontrado",
                code="OSREP_ASSET_MISSING",
                path=str(path),
            )
            raise FileNotFoundError(f"Arquivo do relatório não encontrado: {path}")
        return path.read_text(encoding="utf-8")

    @classmethod
    def _exigir_tag(cls, template: str, tag: str, tool_key: str) -> None:
        """Garante que o template tem a tag que será trocada pelo asset.

        Raises:
            ValueError: se a tag não existir no template.
        """
        if tag in template:
            return
        cls._get_logger(tool_key, "OsReportAssets").error(
            "Tag de asset ausente no template do relatório",
            code="OSREP_ASSET_TAG_MISSING",
            tag=tag,
        )
        raise ValueError(f"Template sem a tag de asset: {tag}")
