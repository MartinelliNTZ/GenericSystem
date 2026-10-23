# -*- coding: utf-8 -*-
"""
PanelZonas — Painel 2.3 · Zonas de manejo
=========================================
Mapa das zonas de manejo da propriedade, identificadas pela legenda, seguido do
resumo da base gravada na OS.

Entrega o GeoJSON (``FeatureCollection`` em EPSG:4326) da base
``zonas_manejo`` — propriedade ``zona`` — e o resumo da base (``base_zonas``:
feições, área, arquivo, origem e registro). Sem a base, o GeoJSON sai ``None``
e o template mostra "Aguardando o shape de zonas de manejo".
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelZonas(PanelBuilder):
    """Painel 2.3 — Zonas de manejo."""

    PANEL_ID = "2.3"
    PANEL_TITLE = "Zonas de manejo"
    ZONAS_KEY = "zonas_manejo"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """GeoJSON das zonas + resumo da base (``tem = False`` sem registro)."""
        return {
            "zonas": context.shape(cls.ZONAS_KEY),
            "base_zonas": cls.base_info(context, cls.ZONAS_KEY),
        }
