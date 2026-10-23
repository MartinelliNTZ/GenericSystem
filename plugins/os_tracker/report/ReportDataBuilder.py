# -*- coding: utf-8 -*-
"""
ReportDataBuilder — Schema do template + builders de painel
==========================================================
Monta o objeto ``window.DADOS_PROJETO`` do template: parte do SCHEMA (todas as
chaves com valor neutro — o mesmo estado vazio do template) e aplica, na
ORDEM do template, o resultado de cada builder de painel.

Chave que nenhum painel preenche permanece vazia — nada é adaptado/inventado.

Uso:
    from plugins.os_tracker.report.ReportDataBuilder import ReportDataBuilder

    data = ReportDataBuilder.build(context)
"""

from __future__ import annotations

from typing import Any, Dict, Tuple, Type

from utils.BaseUtil import BaseUtil

from plugins.os_tracker.report.ReportContext import ReportContext
from plugins.os_tracker.report.panels.PanelAtividades import PanelAtividades
from plugins.os_tracker.report.panels.PanelBaseDados import PanelBaseDados
from plugins.os_tracker.report.panels.PanelBuilder import PanelBuilder
from plugins.os_tracker.report.panels.PanelFazendas import PanelFazendas
from plugins.os_tracker.report.panels.PanelLimites import PanelLimites
from plugins.os_tracker.report.panels.PanelVisaoGeral import PanelVisaoGeral
from plugins.os_tracker.report.panels.PanelZonas import PanelZonas


class ReportDataBuilder(BaseUtil):
    """Junta o schema do template com os builders de painel."""

    # ── Versão do relatório ─────────────────────────────────────────
    # O relatório tem versão PRÓPRIA (a do software é outra, no ToolRegistry) e
    # ela aparece em UM lugar: o RODAPÉ (`Desenvolvido por … · V1.0.0 · dd/mm/aaaa`).
    # TODA mudança no relatório (painel, campo, CSS, JS, modelo) sobe a versão e
    # atualiza a data — ver `docs/skills/SKILL_OS_REPORT.md` §11.
    REPORT_VERSION = "1.0.0"
    REPORT_VERSION_DATE = "23/10/2026"

    # Schema do template (chave → valor neutro). O que não for preenchido por
    # um painel continua exatamente assim — o template já sabe exibir o vazio.
    SCHEMA: Dict[str, Any] = {
        "os": "",
        "nome_comercial": "",
        "tipos_manejo": [],
        "area_contratada_ha": None,
        "n_cars": None,
        "data_inicio": "",
        "ano_cenario_base": None,
        "gerado_em": "",
        "versao_data": "",
        # Rodapé (aviso + tempo de processamento + data de geração + versão).
        "versao_relatorio": "",
        "processamento": "",
        # Painel 1 — dados da OS (as mesmas infos do relatório emitido em PDF).
        "nome": "",
        "cliente": "",
        "cnpj": "",
        "pasta": "",
        "pasta_completa": "",
        "atualizado_em": "",
        # Painel 2 — distribuição espacial.
        "fazendas": [],
        "limites": None,
        "zonas": None,
        "base_limites": None,
        "base_zonas": None,
        # Painel 3 — atividades.
        "atividades": [],
        # Painel 4 — base de dados.
        "pastas_criadas": None,
        "lista_pastas": [],
        "anos_criados": [],
    }
    # Painéis na ORDEM do template (um painel pode ter vários builders).
    PANELS: Tuple[Type[PanelBuilder], ...] = (
        PanelVisaoGeral,
        PanelFazendas,
        PanelLimites,
        PanelZonas,
        PanelAtividades,
        PanelBaseDados,
    )

    @classmethod
    def version_label(cls) -> str:
        """Texto da versão exibido no RODAPÉ (ex.: ``V1.0.0 · 23/10/2026``)."""
        return f"V{cls.REPORT_VERSION} · {cls.REPORT_VERSION_DATE}"

    @classmethod
    def build(cls, context: ReportContext) -> Dict[str, Any]:
        """Dados completos do relatório (schema + todos os painéis)."""
        logger = cls._get_logger(context.tool_key, "ReportDataBuilder")
        data = dict(cls.SCHEMA)
        data["gerado_em"] = context.generated_at
        data["versao_data"] = context.data_version or cls.SCHEMA["versao_data"]
        data["versao_relatorio"] = cls.version_label()
        for panel in cls.PANELS:
            data.update(panel.build(context))
            logger.info("Painel do relatório preenchido", code="OSREP_PANEL", panel=panel.label())
        logger.info(
            "Dados do relatório montados",
            code="OSREP_DATA_DONE",
            panels=len(cls.PANELS),
            versao=cls.REPORT_VERSION,
        )
        return data
