# -*- coding: utf-8 -*-
"""
PanelDadosOs — Painel 6 · Dados da OS
=====================================
Identificação do registro e da pasta da OS — as MESMAS infos que o relatório
emitido em PDF (template Word) traz em "Dados Gerais": nome, cliente, CNPJ,
pasta, pastas criadas (com a lista), anos criados e a última atualização.

A data vai em ISO (``updated_at``) e o template a formata no navegador; campo
sem valor sai vazio e o template exibe o próprio estado vazio.
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelDadosOs(PanelBuilder):
    """Painel 6 — Dados da OS."""

    PANEL_ID = "6"
    PANEL_TITLE = "Dados da OS"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Campos cadastrais do registro da OS e as pastas/anos criados."""
        folders = [str(name) for name in (context.value("folders") or [])]
        years = [str(year) for year in (context.value("years") or [])]
        return {
            "nome": str(context.value("name", "") or ""),
            "cliente": str(context.value("client", "") or ""),
            "cnpj": str(context.value("cnpj", "") or ""),
            "pasta": str(context.value("path", "") or ""),
            "pasta_completa": context.os_folder,
            "pastas_criadas": len(folders),
            "lista_pastas": folders,
            "anos_criados": years,
            "atualizado_em": str(context.value("updated_at", "") or ""),
        }
