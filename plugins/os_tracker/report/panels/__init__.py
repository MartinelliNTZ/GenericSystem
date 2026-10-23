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
| 1 | ``PanelVisaoGeral`` | OS e nome comercial (contratuais ainda sem fonte) |
| 2 | ``PanelCulturas`` | Culturas (ainda sem fonte no banco) |
| 3 | ``PanelFazendas`` | Fazendas e talhões (derivados do shape de limites) |
| 4 | ``PanelLimites`` | GeoJSON dos limites (mapa) |
| 5 | ``PanelZonas`` | GeoJSON das zonas de manejo (mapa) |
"""
