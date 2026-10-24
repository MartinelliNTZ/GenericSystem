# -*- coding: utf-8 -*-
"""
PanelAtividades — Painel 3 · Atividades
=======================================
Atividades da propriedade (era o painel "Culturas"): **3.1 Tipos de manejo** e
**3.2 Culturas**.

O banco ainda não fornece as duas listas, então o painel devolve as chaves
VAZIAS (o template exibe o próprio estado vazio e, no 3.1, os exemplos em tom
fantasma). Nada é adaptado/inventado.
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
        """Sem fonte no banco: listas vazias (o template mostra o estado vazio)."""
        return {"tipos_manejo": [], "culturas": []}
