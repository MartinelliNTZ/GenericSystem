# -*- coding: utf-8 -*-
"""
PanelAtividades — Painel 3 · Atividades
=======================================
Atividades da propriedade (era o painel "Culturas").

O banco ainda não fornece as atividades da OS, então o painel devolve a lista
VAZIA (o template exibe o próprio estado vazio). Nada é adaptado/inventado.
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelAtividades(PanelBuilder):
    """Painel 3 — Atividades."""

    PANEL_ID = "3"
    PANEL_TITLE = "Atividades"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Sem fonte no banco: lista vazia (o template mostra o estado vazio)."""
        return {"atividades": []}
