# -*- coding: utf-8 -*-
"""
Builders de painel do Relatório Geral do Projeto
================================================
Cada PAINEL do template é preenchido por UM builder desacoplado, que só
conhece o ``ReportContext`` e devolve as chaves do template que lhe
pertencem. Um painel pode ser dividido em VÁRIOS pedaços registrando builders
com subnúmero (ex.: ``PANEL_ID = "3.1"`` / ``"3.2"``).

Painéis atuais:

| Painel | Builder | Conteúdo |
|---|---|---|
| 1 | ``PanelVisaoGeral`` | Visão geral: projeto + dados da OS (o antigo painel "Dados da OS" foi somado aqui) |
| 2.1 | ``PanelFazendas`` | Fazendas e talhões (derivados do shape de limites) |
| 2.2 | ``PanelLimites`` | GeoJSON dos limites (mapa) + resumo da base |
| 2.3 | ``PanelZonas`` | GeoJSON das zonas de manejo (mapa) + resumo da base |
| 3 | ``PanelAtividades`` | Atividades: 3.1 tipos de manejo e 3.2 culturas (ainda sem fonte no banco) |
| 4 | ``PanelBaseDados`` | Base de Dados: 4.1 pasta, 4.2 pastas criadas e 4.3 anos com dados |

Os painéis **1**, **2.2**, **2.3** e **4** trazem as MESMAS infos que o relatório
emitido em PDF (template Word ``MODELO_RELATORIO_OS.docx``) em "Dados Gerais",
"Base de Limites", "Base de Zonas de Manejo" e a pasta/pastas/anos da OS.
"""
