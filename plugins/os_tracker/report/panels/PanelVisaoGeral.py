# -*- coding: utf-8 -*-
"""
PanelVisaoGeral — Painel 1 · Visão geral
========================================
Identificação do projeto e os dados da OS (o antigo painel "Dados da OS" foi
SOMADO a este): OS, nome, cliente, nome comercial, CNPJ e última atualização. A
PASTA saiu daqui — vive no painel 4 (Base de Dados) — e os TIPOS DE MANEJO no
painel 3 (Atividades).

Os campos contratuais do template (``area_contratada_ha``, ``n_cars``,
``data_inicio`` e ``ano_cenario_base``) permanecem VAZIOS — o banco ainda não os
fornece e nada é adaptado/inventado (o template já traz o estado vazio).
"""

from __future__ import annotations

from typing import Any, Dict

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder


class PanelVisaoGeral(PanelBuilder):
    """Painel 1 — Visão geral (projeto + dados da OS)."""

    PANEL_ID = "1"
    PANEL_TITLE = "Visão geral"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Projeto + dados cadastrais da OS (o restante o template traz vazio)."""
        return {
            "os": str(context.value("os", "") or ""),
            "nome": str(context.value("name", "") or ""),
            "cliente": str(context.value("client", "") or ""),
            "nome_comercial": str(context.value("commercial_name", "") or ""),
            "cnpj": str(context.value("cnpj", "") or ""),
            "atualizado_em": str(context.value("updated_at", "") or ""),
        }
