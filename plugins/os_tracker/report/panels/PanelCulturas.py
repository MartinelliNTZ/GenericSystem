# -*- coding: utf-8 -*-
"""
PanelCulturas — Painel 2 · Culturas
===================================
Lista de todas as culturas da propriedade.

O banco ainda não fornece as culturas da OS, então o painel devolve a lista
VAZIA (o template exibe o próprio estado vazio). Nada é adaptado/inventado.
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelCulturas(PanelBuilder):
    """Painel 2 — Culturas."""

    PANEL_ID = "2"
    PANEL_TITLE = "Culturas"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Sem fonte no banco: lista vazia (o template mostra o estado vazio)."""
        return {"culturas": []}
