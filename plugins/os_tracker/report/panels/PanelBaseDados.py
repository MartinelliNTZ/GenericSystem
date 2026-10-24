# -*- coding: utf-8 -*-
"""
PanelBaseDados — Painel 4 · Base de Dados
=========================================
O que já existe na base da OS — subpainel **4.1 Pasta** (nome da pasta + o
caminho completo resolvido), subpainel **4.2 Pastas criadas** (contagem +
lista) e subpainel **4.3 Anos com dados** (contagem + lista).

Os dados vêm do próprio registro da OS (``path``/``folders``/``years``, gravados
pela ferramenta ao criar as pastas do projeto) e a pasta resolvida
(``context.os_folder``). Sem registro, as listas saem vazias e o template mostra
o estado vazio.
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelBaseDados(PanelBuilder):
    """Painel 4 — Base de Dados (pasta, pastas criadas e anos com dados)."""

    PANEL_ID = "4"
    PANEL_TITLE = "Base de Dados"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Pasta (4.1), pastas criadas (4.2) e anos com dados (4.3) da OS."""
        folders = [str(name) for name in (context.value("folders") or [])]
        years = [str(year) for year in (context.value("years") or [])]
        return {
            "pasta": str(context.value("path", "") or ""),
            "pasta_completa": context.os_folder,
            "pastas_criadas": len(folders),
            "lista_pastas": folders,
            "anos_criados": years,
        }
