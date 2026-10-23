# -*- coding: utf-8 -*-
"""
PanelBaseDados — Painel 4 · Base de Dados
=========================================
O que já existe na base da OS — subpainel **4.1 Pastas criadas** (contagem +
lista) e subpainel **4.2 Anos com dados** (contagem + lista).

Os dados vêm do próprio registro da OS (``folders``/``years``, gravados pela
ferramenta ao criar as pastas do projeto). Sem registro, as listas saem vazias
e o template mostra o estado vazio.
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelBaseDados(PanelBuilder):
    """Painel 4 — Base de Dados (pastas criadas e anos com dados)."""

    PANEL_ID = "4"
    PANEL_TITLE = "Base de Dados"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Pastas criadas (4.1) e anos com dados (4.2) do registro da OS."""
        folders = [str(name) for name in (context.value("folders") or [])]
        years = [str(year) for year in (context.value("years") or [])]
        return {
            "pastas_criadas": len(folders),
            "lista_pastas": folders,
            "anos_criados": years,
        }
