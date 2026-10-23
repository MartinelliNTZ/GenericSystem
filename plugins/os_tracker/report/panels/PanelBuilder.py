# -*- coding: utf-8 -*-
"""
PanelBuilder — Contrato dos builders de painel do relatório
===========================================================
Cada painel do template tem um NÚMERO (``PANEL_ID``) e um TÍTULO
(``PANEL_TITLE``). Um painel pode ser dividido em vários pedaços: cada pedaço
é um builder próprio com subnúmero (ex.: ``"3.1"``, ``"3.2"``) e devolve as
chaves do template que preenche.

O builder NÃO lê disco, banco nem Qt: recebe o ``ReportContext`` pronto.

Uso:
    class PanelExemplo(PanelBuilder):
        PANEL_ID = "3.1"
        PANEL_TITLE = "Resumo das fazendas"

        @classmethod
        def build(cls, context):
            return {"fazendas": []}
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from utils.BaseUtil import BaseUtil

from plugins.os_tracker.report.ReportContext import ReportContext


class PanelBuilder(BaseUtil, ABC):
    """Contrato dos builders de painel do relatório."""

    PANEL_ID = ""
    PANEL_TITLE = ""

    @classmethod
    @abstractmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Chaves do template preenchidas por este painel."""

    @classmethod
    def label(cls) -> str:
        """Identificação do painel (ex.: ``Painel 3 · Fazendas e talhões``)."""
        return f"Painel {cls.PANEL_ID} · {cls.PANEL_TITLE}"
