# -*- coding: utf-8 -*-
"""
ReportContext — Contexto entregue aos builders de painel
========================================================
Transporta, para os builders de painel, SOMENTE o que eles precisam: o
registro da OS, a pasta-mãe, a chave da ferramenta, a data de geração e as
SHAPES já convertidas em GeoJSON.

Os builders NÃO conhecem banco, disco, Qt nem ``OsTrackerService`` — eles
apenas leem o contexto e devolvem as chaves do template que lhes pertencem.

Uso:
    from plugins.os_tracker.report.ReportContext import ReportContext

    context = ReportContext(record=record, mother=mother, tool_key=tool_key,
                            generated_at="23/10/2026 15:10")
    context.value("os")            # campo do registro da OS
    context.shape("limites")       # FeatureCollection GeoJSON (ou None)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ReportContext:
    """Entrada imutável dos builders de painel do relatório."""

    record: Dict[str, Any]
    mother: Optional[Path]
    tool_key: str
    generated_at: str
    data_version: str = ""
    os_folder: str = ""
    asset_paths: Dict[str, str] = field(default_factory=dict)
    assets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    shapes: Dict[str, Optional[Dict[str, Any]]] = field(default_factory=dict)

    def value(self, key: str, default: Any = "") -> Any:
        """Valor de um campo do registro da OS (``default`` quando ausente)."""
        return (self.record or {}).get(key, default)

    def asset(self, key: str) -> Dict[str, Any]:
        """Info da base gravada na OS (``has``/``features``/``area_ha``/``file``…)."""
        return self.assets.get(key) or {}

    def shape(self, key: str) -> Optional[Dict[str, Any]]:
        """GeoJSON FeatureCollection da base informada (``None`` sem shape)."""
        return self.shapes.get(key)
