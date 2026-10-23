# -*- coding: utf-8 -*-
"""
PanelFazendas — Painel 2.1 · Fazendas e talhões
==============================================
Resumo das fazendas e a lista de talhões de cada uma — primeiro pedaço do
painel **2 · Distribuição espacial**.

A fonte é o SHAPE de limites já convertido em GeoJSON (``FAZENDA``,
``TALHAO`` e ``AREA_HA``) — exatamente o mesmo dado do subpainel 2.2. Sem o
shape, a lista sai vazia (o template mostra o próprio estado vazio).
"""

from __future__ import annotations

from typing import Any, Dict, List

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelFazendas(PanelBuilder):
    """Painel 2.1 — Fazendas e talhões."""

    PANEL_ID = "2.1"
    PANEL_TITLE = "Fazendas e talhões"
    LIMITES_KEY = "limites"
    UNKNOWN_FARM = "—"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Agrupa os talhões do shape de limites por fazenda."""
        farms: Dict[str, List[Dict[str, Any]]] = {}
        for feature in cls._features(context):
            props = feature.get("properties") or {}
            name = str(props.get("fazenda") or "").strip() or cls.UNKNOWN_FARM
            farms.setdefault(name, []).append(
                {
                    "nome": str(props.get("talhao") or "").strip(),
                    "area_ha": props.get("area_ha"),
                }
            )
        return {
            "fazendas": [
                {
                    "nome": name,
                    "talhoes": sorted(items, key=lambda item: item["nome"]),
                }
                for name, items in sorted(farms.items())
            ]
        }

    @classmethod
    def _features(cls, context: ReportContext) -> List[Dict[str, Any]]:
        """Feições do shape de limites (lista vazia quando não houver shape)."""
        collection = context.shape(cls.LIMITES_KEY) or {}
        return list(collection.get("features") or [])
