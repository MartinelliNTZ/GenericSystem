# -*- coding: utf-8 -*-
"""
PanelZonas — Painel 5 · Zonas de manejo
=======================================
Mapa das zonas de manejo da propriedade, identificadas pela legenda.

Entrega o GeoJSON (``FeatureCollection`` em EPSG:4326) da base
``zonas_manejo`` gravada na OS — a propriedade usada é ``zona``. Sem a base,
entrega ``None`` e o template mostra "Aguardando o shape de zonas de manejo".
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelZonas(PanelBuilder):
    """Painel 5 — Zonas de manejo."""

    PANEL_ID = "5"
    PANEL_TITLE = "Zonas de manejo"
    ZONAS_KEY = "zonas_manejo"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """GeoJSON das zonas (``None`` quando a OS não tem a base)."""
        return {"zonas": context.shape(cls.ZONAS_KEY)}
