# -*- coding: utf-8 -*-
"""
PanelBases — Painel 7 · Bases gravadas
======================================
Resumo de cada base do banco registrada na OS — as MESMAS infos que o relatório
emitido em PDF (template Word) traz em "Base de Limites" e "Base de Zonas de
Manejo": feições, área (ha), arquivo, origem e a data de registro.

Os números vão CRUS (o template formata em pt-BR) e a data vai em ISO (o
template a formata no navegador). Base não registrada sai com ``tem = False`` e
o template exibe o estado vazio.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelBases(PanelBuilder):
    """Painel 7 — Bases gravadas na OS."""

    PANEL_ID = "7"
    PANEL_TITLE = "Bases gravadas"
    # Bases do banco na ordem do relatório: (chave, título).
    BASES: Tuple[Tuple[str, str], ...] = (
        ("limites", "Base de Limites"),
        ("zonas_manejo", "Base de Zonas de Manejo"),
    )

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Uma entrada por base do banco, na ordem de ``BASES``."""
        return {
            "bases": [cls._base(context, key, title) for key, title in cls.BASES]
        }

    @classmethod
    def _base(
        cls,
        context: ReportContext,
        key: str,
        title: str,
    ) -> Dict[str, Any]:
        """Resumo de UMA base registrada na OS."""
        info = context.asset(key)
        return {
            "chave": key,
            "titulo": title,
            "tem": bool(info.get("has")),
            "feicoes": info.get("features", 0),
            "area_ha": info.get("area_ha", 0.0),
            "arquivo": str(info.get("file", "") or ""),
            "origem": str(info.get("source", "") or ""),
            "registrado": str(info.get("inserted_at", "") or ""),
        }
