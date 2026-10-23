# -*- coding: utf-8 -*-
"""
PanelLimites — Painel 4 · Limites
=================================
Mapa dos limites dos talhões sobre imagem de satélite (uma cor por fazenda).

Entrega o GeoJSON (``FeatureCollection`` em EPSG:4326) da base ``limites``
gravada na OS — as propriedades são ``fazenda``, ``talhao`` e ``area_ha``.
Sem a base, entrega ``None`` e o template mostra "Aguardando o shape de
limites".
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelLimites(PanelBuilder):
    """Painel 4 — Limites."""

    PANEL_ID = "4"
    PANEL_TITLE = "Limites"
    LIMITES_KEY = "limites"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """GeoJSON dos limites (``None`` quando a OS não tem a base)."""
        return {"limites": context.shape(cls.LIMITES_KEY)}
