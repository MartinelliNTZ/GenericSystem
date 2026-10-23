# -*- coding: utf-8 -*-
"""
PanelVisaoGeral — Painel 1 · Visão geral
========================================
Identificação do projeto e dados contratuais.

Preenche ``os`` e ``nome_comercial`` com o registro da OS. Os campos
contratuais do template (``tipos_manejo``, ``area_contratada_ha``, ``n_cars``,
``data_inicio`` e ``ano_cenario_base``) permanecem VAZIOS — o banco ainda não
os fornece e nada é adaptado/inventado (o template já traz o estado vazio).
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelVisaoGeral(PanelBuilder):
    """Painel 1 — Visão geral."""

    PANEL_ID = "1"
    PANEL_TITLE = "Visão geral"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """OS e nome comercial do registro (o restante o template traz vazio)."""
        return {
            "os": str(context.value("os", "") or ""),
            "nome_comercial": str(context.value("commercial_name", "") or ""),
        }
