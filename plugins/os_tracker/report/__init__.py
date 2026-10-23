# -*- coding: utf-8 -*-
"""
Relatório Geral do Projeto (HTML) — submódulo do Acompanhamento de OS
=====================================================================
Gera o relatório HTML da OS a partir do template
``core/template/relatorio_geral_projeto.html`` (editável — é a fonte do
layout) preenchido com os dados do banco e com os SHAPES das bases
(``limites`` e ``zonas_manejo``) convertidos para GeoJSON (EPSG:4326).

O template é dividido em PAINÉIS numerados (``Painel 1`` … ``Painel 5``) e um
painel pode ser dividido em VÁRIOS pedaços (``Painel 3.1``, ``3.2`` …). Cada
painel é preenchido por um BUILDER desacoplado (``panels/``) e o resultado
final é o objeto ``window.DADOS_PROJETO`` do template.

| Classe | Papel |
|---|---|
| ``OsReportHtmlService`` | Fachada: monta os dados e gera o arquivo |
| ``ReportSource`` | Resolve a pasta/arquivos da OS (único ponto que fala com ``OsTrackerService``) |
| ``ReportDataBuilder`` | Junta o schema do template com os builders de painel |
| ``ReportContext`` | Contexto imutável entregue aos builders |
| ``ShapeGeoJsonReader`` | Vetor da base → GeoJSON EPSG:4326 |
| ``OsReportHtmlGenerator`` | Template + dados → ``.HTML`` |
| ``panels.PanelBuilder`` | Contrato dos builders de painel |

Uso:
    from plugins.os_tracker.report.OsReportHtmlService import OsReportHtmlService

    path = OsReportHtmlService.generate(
        mother, record, tool_key=ToolKey.OS_TRACKER.value
    )
"""
