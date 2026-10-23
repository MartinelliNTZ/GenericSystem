# -*- coding: utf-8 -*-
"""
PanelLimites — Painel 2.2 · Limites
===================================
Mapa dos limites dos talhões sobre imagem de satélite (uma cor por fazenda),
seguido do resumo da base gravada na OS.

Entrega o GeoJSON (``FeatureCollection`` em EPSG:4326) da base ``limites`` —
propriedades ``fazenda``, ``talhao`` e ``area_ha`` — e o resumo da base
(``base_limites``: feições, área, arquivo, origem e registro). Sem a base, o
GeoJSON sai ``None`` e o template mostra "Aguardando o shape de limites".
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelLimites(PanelBuilder):
    """Painel 2.2 — Limites."""

    PANEL_ID = "2.2"
    PANEL_TITLE = "Limites"
    LIMITES_KEY = "limites"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """GeoJSON dos limites + resumo da base (``tem = False`` sem registro)."""
        return {
            "limites": context.shape(cls.LIMITES_KEY),
            "base_limites": cls.base_info(context, cls.LIMITES_KEY),
        }
