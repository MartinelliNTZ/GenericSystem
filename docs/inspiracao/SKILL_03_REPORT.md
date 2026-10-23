---
name: api-03-reports
description: >-
  API 3 do ObterDados — relatório: JSON de `saida/` → HTML. Carrega-se quando a
  tarefa for executar ou alterar a API 3 (`apis/03ApiReports/`): `ValidadorDados`
  (métricas), `ReportRendering` (painéis 01–09), `FileManager` e o modelo visual
  (`template_02.html` + `.css` + `.js`), `LaudoAttachment` (laudo anexado no
  9.4), blocos `validacao`/`conformidades`/`laudos` lidos dos NÓS DAS OS da
  árvore `dados_gerais`, o **cliente da OS** (`dados_gerais.<OS>.cliente`,
  API 7) no painel 1 e os nomes dos `.html` de `saida/`. Alerta e conformidade
  são da API 5; laudo, da API 4.
---

# api-03-reports · Relatório (JSON → HTML)

## 1. Identidade

| Item | Valor |
|---|---|
| Responsabilidade | Calcular as MÉTRICAS do JSON e EXIBIR os relatórios HTML (painéis 01–09) |
| Entrada | JSON normalizado de `saida/` na árvore `dados_gerais → OS → fazenda → registros` + os blocos que as outras APIs publicam NOS NÓS DAS OS: `cliente` (API 7), `validacao` (alertas) e `conformidades` (alertas justificados) e `laudos` (API 5/4) + o bloco `statistics` do SISTEMA (LIDO só para o tempo de processamento do rodapé) |
| Saída (artefatos da API) | `saida/OS_<número>/OS_<número>_report.html` (um por OS, na pasta da OS) + `saida/Consolidado.html` |
| Entry point | `apis/03ApiReports/ApiReports.py` → `ApiReports.run(json_path, individual=True, consolidated=True)`: devolve `ReportsResult` ou `None` |
| Rodapé (fechamento) | `ApiReports.atualizar_rodape(json_path, report_paths=None)` — chamado pela Pipeline no FIM da execução (o bloco `statistics` do JSON só existe aí): reescreve a linha do TEMPO DE PROCESSAMENTO no rodapé dos `.html` já gravados e devolve os caminhos atualizados |
| Escopo | O SISTEMA (API 00) chama com `consolidated=False` na FASE POR OS (só o HTML da OS) e com `individual=False` na fase consolidada (só o `Consolidado.html`) — ver `SKILL_00_SYSTEM.md` §3 |
| CLI isolada | `python -m apis.03ApiReports.ApiReports --json saida/dados_<ts>.json` |
| CLI só de métricas | `python -m apis.03ApiReports.validador --json saida/dados_<ts>.json [--saida out.json]` |

A API 3 **não decide nada**: ela lê o JSON, calcula métricas e exibe. Todo alerta
nasce na API 5 e todo laudo, na API 4 — o único vínculo entre as APIs é o arquivo
JSON (`CONTRACT.MD` §9 e §10).

## 2. Fluxo (`ApiReports.run`)

1. `_load_json()` — JSON ilegível → `logger.error` e `None`.
2. `JsonHierarchy.records(data)` → `filter_lines(registros)` — todos os talhões
   da árvore, descartando o que **não é linha** (log com a quantidade
   descartada).
3. `ValidadorDados.validar(line_records)` → resumos por planilha;
   `consolidar(resumos, gerado_em)` → `RelatorioConsolidado` (recebe também
   `arquivos_com_erro` da raiz do JSON).
4. `resumir_por_os(line_records)` → **um** `ResumoArquivo` por OS, com as
   planilhas daquela OS já fundidas.
5. `_bloco("validacao")`, `_bloco("conformidades")` e `_bloco("laudos")` — no
   contrato novo leem os blocos de CADA nó de OS e os reúnem com
   `JsonHierarchy.merged_block`; ausentes só geram `warning`;
   `LaudoAttachmentBuilder.build(laudos)` embute os laudos em base64.
6. `_clientes_por_os(data)` — lê `dados_gerais.<OS>.cliente` (API 7) e
   entrega o mapa `chave da OS → {nome, logotipo}` ao `gerar_todos(clientes=…)`;
   cada relatório de OS passa o seu `client` ao `corpo_os` (card “Cliente” no
   painel 1) e ao `renderizar` (logo antes do título + nome na linha do título).
7. `ReportRendering.gerar_todos(...)` → lista de `.html`; nenhum gravado → `None`.
8. Devolve `ReportsResult(json_path, report_paths, total_files, total_os,
   total_records, laudo_paths)`.

**O RODAPÉ** de cada `.html` fecha a página — em **fonte pequena** — com o aviso
de geração automática (“alguns dados podem sofrer alteração”), o **tempo de
processamento** (SÓ a duração: `Tempo de processamento: 1 min 32 s` — o `início` e
o `fim` da janela ficam no JSON, NÃO na página) e a **data de geração**
(`gerado_em`, que saiu do cabeçalho para cá). No `run`, a janela é lida do bloco
`statistics` quando ele já existe no JSON (`janela_processamento`) e, sem o
bloco, é MEDIDA (início de `run` → gravação de cada HTML); a Pipeline manda
reescrevê-la no fim da execução (`atualizar_rodape`), quando o bloco passa a
existir.

## 3. Arquivos (quem faz o quê)

| Arquivo | Papel |
|---|---|
| `apis/03ApiReports/ApiReports.py` | Entry point + CLI: orquestra métricas, blocos e renderização; `ReportsResult`; o RODAPÉ (`janela_processamento` lê a janela da API 3 no bloco `statistics` e `atualizar_rodape` a publica nos `.html` no fim da execução). |
| `apis/03ApiReports/validador.py` | `ValidadorDados` — **só MÉTRICAS** (`validar`, `consolidar`, `resumir_por_os`), identidade da OS (`chave_os`, `rotulo_os`, `extrair_numero_os`), `is_line`/`filter_lines` e as dataclasses `ResumoTalhao`, `ResumoOS`, `ResumoArquivo`, `RelatorioConsolidado`. Tem CLI própria (`--json [--saida]`) que imprime o consolidado. |
| `apis/03ApiReports/ReportRendering.py` | Costura o modelo visual (`renderizar`) e monta o corpo e os painéis (`gerar_todos`, `gerar_os`, `gerar_consolidado`, `corpo_os`, `corpo_consolidado`, `painel_geral`, `painel_area`, `painel_produtividade`, `painel_pecuaria`, `painel_fertilizantes`, `painel_nutrientes`, `painel_combustivel`, `painel_praticas`, `painel_alertas`, `painel_conformidades`, `painel_laudos`); o RODAPÉ (`texto_processamento`, `texto_duracao`, `texto_gerado_em`, `atualizar_rodape`) e a VERSÃO do relatório (`RELATORIO_VERSAO`, `RELATORIO_VERSAO_DATA`, `texto_versao` — §11). |
| `apis/03ApiReports/FileManager.py` | Único ponto que lê o modelo visual: `REPORT_TEMPLATE_FILENAME` (hoje `template_02.html`) + `stylesheet_path`/`script_path` (mesmo nome-base) + `read_template`/`read_stylesheet`/`read_script`. |
| `apis/03ApiReports/LaudoAttachment.py` | `LaudoAttachmentBuilder.build(bloco)` lê o `.docx` e o PDF do bloco `laudos` e embute em base64; `LaudoAttachment.as_payload()` é o que o JS do 9.4 consome. |
| `apis/03ApiReports/LogoResolver.py` | Resolve o logo do cliente (URL/`data:`/arquivo local → `data:` base64) e aplica o fallback do logo da AgroRobótica (`logo_agrorobotica.jpg` na pasta da API 3); o logo é RECURSO da API 3. |
| `apis/03ApiReports/template_02.html` | ESTRUTURA: markup + placeholders `$TITULO_JANELA`, `$TITULO_PAGINA`, `$SUBTITULO`, `$GERADO_EM` (só no RODAPÉ), `$PROCESSAMENTO` (linha do tempo no rodapé), `$VERSAO_RELATORIO` (a versão do relatório, no rodapé), `$LOGO_CLIENTE`, `$LOGO_FALLBACK`, `$ESTILOS`, `$SCRIPTS`, `$PAINEL_GERAL`, `$PAINEL_AREA`, `$PAINEL_PRODUTIVIDADE`, `$PAINEL_PECUARIA`, `$PAINEL_FERTILIZANTES`, `$PAINEL_NUTRIENTES`, `$PAINEL_COMBUSTIVEL`, `$PAINEL_PRATICAS`, `$PAINEL_ALERTAS`. |
| `apis/03ApiReports/template_02.css` | ESTILIZAÇÃO (só CSS) — preenche `$ESTILOS`; se não existir, o placeholder fica vazio. |
| `apis/03ApiReports/template_02.js` | COMPORTAMENTO (só JS) — preenche `$SCRIPTS`: cálculos em tempo real, filtros, botões e montagem dos painéis a partir dos payloads `dados*`. |
| `core/util/DataMetrics.py`, `JsonRecord.py`, `OsKey.py`, `Slug.py`, `OutputLayout.py`, `JsonHierarchy.py` | Utils neutros: fatos do registro e as CHAVES do JSON; leitura do registro AGRUPADO; identidade da OS; nome de arquivo/pasta seguro; pasta/nome da OS na saída (`saida/OS_131/`) e `Old/`; árvore `dados_gerais` (registros e blocos por OS). |
| `core/config.py` | Constantes de exibição: `LIMITE_LAUDO_ANEXO_MB`, `FATORES_PRODUTIVIDADE_T_HA`, `CAMPO_FERTILIZANTES`, `PRATICAS_*`/`CAMPO_PRATICA_SOLO`, `TALHAO_NAMES_WITHOUT_AREA`. |
| `core/catalog/CultivationCatalog.py`, `core/catalog/FertilizerCatalog.py` | **Catálogos do SISTEMA**: as culturas (`CULTIVATIONS`: classe e formas de produção) e os insumos (teores) que o painel 3.2/05 usa (`config.CULTIVATIONS`/`config.FERTILIZERS` são as views). |

## 4. Contrato de entrada (o JSON)

| Chave | Uso |
|---|---|
| `dados_gerais` | A árvore `dados_gerais → OS → fazendas → registros`; `JsonHierarchy.records` achata os talhões e `merged_block` reúne os blocos das OS. |
| `cliente` (bloco da API 7, DENTRO de cada OS) | `{nome, site, logotipo, documento}`. O painel 1 do relatório da OS mostra o card **“Cliente”** com `nome` quando ele existe; sem nome/cliente, o card NÃO aparece. O CABEÇALHO mostra o logo de `logotipo` (URL/`data:`/arquivo local) antes do título e o NOME na própria linha do título (`Relatório … -- NOME`, sem o rótulo “Cliente”); sem logo, usa o logo da AgroRobótica. |
| `gerado_em` | Data/hora de GERAÇÃO, exibida no RODAPÉ (`$GERADO_EM`, em `dd/mm/aaaa às hh:mm:ss` — o ISO do JSON não vai para a página); ausente → usa a hora atual. |
| `statistics` (bloco do SISTEMA, na raiz) | SÓ LEITURA: a janela da API 3 (`apis` com `code` = "3": o primeiro `started_at` e o último `finished_at`) vira o TEMPO DE PROCESSAMENTO do rodapé (`janela_processamento`). Ausente (o HTML gerado pela pipeline, que grava o bloco no fim) → a janela é MEDIDA na gravação e a Pipeline a reescreve depois (`atualizar_rodape`). A API 3 nunca grava esse bloco. |
| `arquivos_com_erro` | Planilhas com falha; aparecem no consolidado. |
| `alertas` (raiz) | Avisos de conversão do JSON; o painel 09 exibe o que vem do bloco `validacao`. |
| `validacao` (bloco da API 5, DENTRO de cada OS) | Alertas **já decididos**: o painel 09 só os apresenta. Ausente → 9.1/9.2 saem sem alertas (com `warning` no log, não é falha). |
| `conformidades` (bloco da API 5, DENTRO de cada OS) | Conformidades — alertas **já justificados** (o valor registrado está correto). Cada item traz `code`, `class_key`/`class_short`/`class_description`, `title`, `statement`, `report_description`, `source_file`, `os_number`, `farm`, `field_name`, `excel_rows` e `evidence`. Ausente → não sai o **9.3** (com `warning`); lista vazia → o 9.3 sai com “Nenhuma conformidade identificada”. |
| `laudos` (bloco da API 4, DENTRO de cada OS) | `os_number`, `docx`, `pdf` — os caminhos são **RELATIVOS a `saida/`** (`LaudoAttachment` resolve contra `config.SAIDA_DIR`). Ausente → o **9.4** sai sem laudo. |
| `nutrients` (chave do REGISTRO, API 6) | Massa de macro/micronutrientes vinda da adubação, por nutriente: `{sintetico, organico, total}`. O painel 06 achata o N em `n_total`/`n_sintetico`/`n_organico` e os demais só pelo `total`. Ausente → o painel 06 sai vazio (JSON sem a 3ª etapa, a API 6). |

## 5. Contrato de saída (HTML)

| Item | Valor |
|---|---|
| Relatório por OS | `saida/OS_<número>/OS_<número>_report.html` — a pasta e o nome saem de `OutputLayout` (o NÚMERO da OS manda: `OS 131 - UISA` e `131` caem em `saida/OS_131/`); as planilhas da mesma OS vão juntas e o laudo da OS fica na MESMA pasta. |
| Consolidado | `saida/Consolidado.html` — todas as OS (e os laudos de todas). |
| Nome | **Sem timestamp**: rodar de novo **sobrescreve** os anteriores. |
| Arquivo autocontido | CSS e JS entram embutidos (`$ESTILOS`/`$SCRIPTS`); o laudo entra em **base64** no payload `#dadosLaudos` (o base64 infla ~33%). |
| Teto do laudo | Arquivo ilegível ou maior que `config.LIMITE_LAUDO_ANEXO_MB` (12 MB) fica **fora** do anexo (o laudo continua em `saida/`), com erro no log; sem PDF, o anexo sai só com o `.docx`. |
| Rodapé | `.rodape-info` (FONTE PEQUENA — 11px) com o aviso de geração automática, `Tempo de processamento: <duração>` (SÓ o tempo: sem `início`/`fim`) e `Gerado em: <dd/mm/aaaa às hh:mm:ss>` (a data SAIU do cabeçalho). O tempo é reescrito no fim da execução (`atualizar_rodape`). No `.rodape-fim` sai a **VERSÃO do relatório** (`V3.0.1 · 23/10/2026`, `$VERSAO_RELATORIO`) — e só ali: a barra lateral não mostra mais versão nem data. |

## 6. Painéis exibidos

| # | Painel | O que alimenta |
|---|---|---|
| 01 | Visão geral | cartões e anos do resumo/consolidado |
| 02 | Estrutura territorial | talhões, área física e área por ano (`ResumoOS`/`ResumoTalhao`) |
| 03 | Produção agrícola — 3.1 a 3.8 | payload `dadosProdutividade` (uma linha por forma de produção: cultura, unidade, produtividade, área, `fator_t_ha`, variedade) |
| 04 | Produção animal — 4.1/4.2 | payload `dadosPecuaria` (tabela por OS · Fazenda · Talhão · ano e gráfico em três escalas) |
| 05 | Insumos e adubação — 5.1 a 5.5 | payload `dadosFertilizantes` (produto do mapa `fertilizers` com quantidade > 0) |
| 06 | Nutrientes da adubação — 6.1 a 6.5 | payload `dadosNutrientes` (chave `nutrients` da API 6: N total/sintético/orgânico e os demais macro/micro pelo total) |
| 07 | Combustíveis e energia — 7.1 a 7.8 | payload `dadosCombustivel` (combustíveis em L e energia em kWh) |
| 08 | Práticas de solo — 8.1 a 8.3 | payload `dadosPraticas` (práticas data-driven de `CAMPO_PRATICA_SOLO` + listas da V3) |
| 09 | Qualidade dos dados — 9.1/9.2/9.3/9.4 | bloco `validacao` (chips 9.1 + grupos 9.2), bloco `conformidades` (9.3: chips + grupos verdes) e bloco `laudos` (9.4), montados no Python |
| — | Filtros | globais, aplicados no navegador pelo `template_02.js`: **OS e Fazenda são GRADES de checkboxes** (`ObterDados.filtros.os`/`.fazenda` = LISTA de valores marcados; vazio = inativo) com o botão "Selecionar todos"/"Desmarcar todos"; os demais são selects de valor único. Marcar a grade **RECONSTRÓI o relatório**: a cascata (`atualizarCascata`) refaz as listas dos demais filtros a partir do recorte de OS + Fazenda — opção sem dado no recorte sai da lista (ex.: ano que não existe na OS marcada) e a escolha que sumiu volta para "todos" — e as colunas de ano do 3.2 saem do recorte exibido (`anosDaListaArea`) |

## 7. Regras intocáveis

1. **Só EXIBE**: alerta e conformidade são decididos na API 5 e laudo é escrito
   na API 4. Duplicar uma dessas regras aqui é violação de fronteira
   (`CONTRACT.MD` §10.2).
2. **Só leitura do JSON**: a API 3 não regrava JSON/CSV nem toca em `data/`.
3. **Área física**: cada talhão conta **1×**, pela **MAIOR** área registrada
   entre as safras; no consolidado, talhões coincidentes (fazenda + talhão)
   fundem-se com a maior área, a menor mínima, a maior área por ano e os
   registros somados.
4. **Variação de área**: 0% sem alerta; `≤5%` verde; `≤20%` amarelo; `>20%`
   vermelho — só amarelo/vermelho aparecem no painel de alertas, e a faixa de
   cor é **apresentação**.
5. **O que é uma LINHA**: o registro conta quando **ao menos 1** dos 5 campos
   (`OS`, `NomeDaFazenda`, `NomeDoTalhao`, `AreaDoTalhaoHa` e ano) tem valor;
   senão fica fora de totais, métricas e validações (`filter_lines`).
6. **Talhões agregados** (`config.TALHAO_NAMES_WITHOUT_AREA`: `TODOS`, `RATEIO`)
   são linhas de total/prorrateo **sem área própria** — não contam como
   "registro sem área".
7. **Produtividade `null` ou `≤ 0` = talhão não colhido**: não é medição e fica
   fora dos cards 3.1 e das colunas do 3.4.
8. **Fertilizante é o NOME** (`config.CAMPO_FERTILIZANTES`): o painel 05 exibe o
   mapa que já vem do JSON (identidade, soma e grafia decididas na API 1) — a
   API 3 não monta rótulo, não agrupa por nome e não une produtos.
9. **Nunca `except: pass`**: `except Exception as exc` + `logger.error(...)` e o
   lote continua; um arquivo com problema não derruba os outros.
10. **1 classe = 1 responsabilidade**, cada método público = 1 passo.
    Identificadores em inglês; docstring, comentário e mensagem em pt-BR
    (`CONTRACT.MD` §2).
11. **A VERSÃO do relatório sobe a CADA mudança** (§11): `RELATORIO_VERSAO` e
    `RELATORIO_VERSAO_DATA` em `ReportRendering.py`, exibidas **só no rodapé**
    (`$VERSAO_RELATORIO`). PATCH para ajuste pequeno, MINOR para sub-painel/campo
    novo e MAJOR para painel ou componente grande novo — e a data acompanha.

## 8. Onde mexer

| Preciso… | Onde |
|---|---|
| Nova métrica | `apis/03ApiReports/validador.py` → `ValidadorDados` (`_resumir_arquivo` / `_resumir_os`) |
| Novo painel ou mudar o conteúdo do corpo | `apis/03ApiReports/ReportRendering.py` (`corpo_os`/`corpo_consolidado` + os `painel_*`) |
| Estilo, cor, layout | `apis/03ApiReports/template_02.css` |
| Cálculo, filtro ou botão no navegador | `apis/03ApiReports/template_02.js` |
| Grade de checkboxes (OS/Fazenda), cascata dos demais filtros | `apis/03ApiReports/template_02.js` (bloco das GRADES + `casaFiltro`/`valoresFiltro`/`atualizarCascata`) + o markup da grade em `template_02.html` + `.filtro-checks`/`.btn-todos-checks` no `template_02.css` |
| Markup, texto fixo, tooltip ou placeholder | `apis/03ApiReports/template_02.html` |
| Aviso, tempo de processamento ou data no rodapé | `ReportRendering.texto_processamento`/`texto_duracao`/`texto_gerado_em` + o bloco `.rodape-info` do `template_02.html` + o CSS `.rodape-info`/`.rodape-aviso`/`.rodape-processamento`/`.rodape-gerado` (fonte pequena: 11px) |
| De onde sai o TEMPO DE PROCESSAMENTO | `ApiReports.janela_processamento` (bloco `statistics` do JSON — só o TEMPO vai para a página, via `texto_duracao`) + `ReportRendering.atualizar_rodape` (a reescrita pedida pela Pipeline no fim da execução) |
| Subir a VERSÃO do relatório | `ReportRendering.RELATORIO_VERSAO` + `RELATORIO_VERSAO_DATA` (a data vai junto) — a regra de numeração está no §11; quem exibe é o `$VERSAO_RELATORIO` do rodapé |
| Trocar o modelo visual inteiro | `FileManager.REPORT_TEMPLATE_FILENAME` + as três peças com o mesmo nome-base em `apis/03ApiReports/` |
| Agrupamento/nome dos relatórios por OS | `validador.py` → `chave_os`/`rotulo_os`; `ReportRendering._slug` monta o nome |
| Conformidades do 9.3 (chips, grupos, cores, textos) | `ReportRendering.painel_conformidades`/`_classes_de_conformidades`/`_grupos_de_conformidades`/`_grupo_conformidade_html` + o JS de filtro (`_script_filtro(PANEL_CONFORMITIES)`) + CSS `.nivel-conformidade`/`.conformidade-*` |
| Botões de download do laudo (9.4) | `ReportRendering.painel_laudos`/`_script_laudos` + `configurarLaudos` (lista `TIPOS`) no `template_02.js` + CSS `.laudo-*` |
| Anexar outro formato de laudo | `LaudoAttachment.as_payload`/`_build_one` + a lista `TIPOS` do JS |
| Teto do anexo | `core/config.py` → `LIMITE_LAUDO_ANEXO_MB` |
| Mudar alerta, motivo, limiar ou texto do painel 09 | **API 5** (`apis/05ApiAlerts/`) — não aqui |
| Mudar o laudo, o PDF ou o modelo `.docx` | **API 4** (`apis/04ApiLaudos/`) — não aqui |
| Diagnosticar "falta o HTML de uma OS" | linhas sem OS não formam OS e planilha sem registros não gera resumo — revisar o JSON de entrada e o log |

## 9. Armadilhas

- **Sem timestamp no nome**: nova execução sobrescreve os `.html`; o consolidado
  com os laudos em base64 pode ficar grande (o base64 infla ~33%).
- **Sem o bloco `validacao`** o painel 09 sai sem alertas, **sem o bloco
  `conformidades`** sai sem o 9.3 e **sem o bloco `laudos`** sai sem o 9.4 — em
  todos os casos com `warning` no log; **não** é falha da API 3. Bloco
  `conformidades` presente e vazio (a OS não teve alerta justificado) → o 9.3
  sai com “Nenhuma conformidade identificada”.
- **O 9.2 e o 9.3 dividem o MESMO mecanismo de chips + grupos**, separados pelo
  `data-painel` (`alertas` × `conformidades`): o filtro de um painel não esconde
  os grupos do outro. Ao criar um terceiro painel desse tipo, reuse
  `_painel_classes`/`_script_filtro` com um `data-painel` novo — não copie o
  JS.
- **Linhas sem OS** não formam OS: não geram relatório por OS (entram no
  consolidado). Planilha sem registros não gera resumo. Por isso o
  `total_arquivos` do consolidado pode diferir do `total_archivos` do JSON.
- **O painel 09 vem PRONTO do Python** (grupos e detalhes já no DOM; o
  `<details>` só esconde o que está fechado). Os painéis 03–08 montam no
  **navegador**, a partir dos payloads `dadosProdutividade`, `dadosPecuaria`,
  `dadosFertilizantes`, `dadosNutrientes`, `dadosCombustivel` e `dadosPraticas`.
- **Filtro de OS/Fazenda é LISTA**: `ObterDados.filtros.os`/`.fazenda` guardam um
  ARRAY de valores marcados (vazio = filtro inativo) — nenhum código compara o
  valor do registro à mão: sempre `casaFiltro(valor, filtro)` (entende lista e
  valor único) e `temFiltroAtivo`/`resumoFiltros` para contar os ativos. A
  **cascata** é disparada só pelas grades (`aoMudarGrade` → `atualizarCascata`):
  os selects (Talhão, Ano, Cenário, Cultura, Fertilizante, Combustível/Energia e
  Prática de solo) são refeitos do recorte de OS + Fazenda e a escolha que saiu
  do recorte volta para "todos" — a grade de OS e a de Fazenda **não** se
  estreitam uma à outra (a lista das duas é a base inteira).
- **Fila cinza (ano faltante) é apresentação**: talhão sem área em algum ano
  exibido **e** sem variação (0%) — não gera alerta. No consolidado e no 3.5 a
  régua é o período inteiro exibido, então talhão que só existe parte do período
  sai cinza (dado incompleto, não erro). No 3.2 a régua é `anosDaListaArea` — os
  anos do RECORTE exibido (não os do payload inteiro).
- **3.5 × 3.7 usam escalas de cor diferentes**: no 3.5 a faixa é **por linha**
  (leitura temporal); no 3.7 é **única por cultura**, sobre todas as células
  (mostra em quais talhões estão os piores resultados).
- **3.5 não usa `fator_t_ha`**: a Média sai na unidade da cultura e é ponderada
  pela área **com produtividade** — produção `0` conta, não colhido (`null`) não.
  No 3.3 só convertem para t/ha as unidades com equivalência de **massa**
  (`config.FATORES_PRODUTIVIDADE_T_HA`); `m³/ha` fica fora. Na área (3.2),
  eucalipto e aroeira contam como **uma só** cultura.
- **Rótulo da cultura pode já trazer a unidade**: nas formas de produção que NÃO
  medem a área (`Aroeira (m³/ha)`, `Eucalipto (m³/ha)`) a API 3 grava a unidade
  no próprio `cultura` do payload. Por isso os painéis 3.2/3.4/3.5/3.7 nunca
  anexam a unidade de novo: usam `unidadeDoRotulo(cultura, unidade)`, que devolve
  `''` quando o rótulo já termina em `(unidade)`. Sem isso o cabeçalho do 3.4
  saía `Aroeira (m³/ha) (m³/ha)` e, com vários anos, o rótulo repetido caía na
  linha de baixo (encavalado).
- **8.3 alinha as colunas de ano pela borda da grade**: o recuo OS → fazenda →
  talhão é aplicado só no TEXTO do `.cel-nome` (`#pratTabelaWrap .cons-body`
  com `padding-left: 0` + `padding-left` no nome). O `padding` horizontal do
  `.cons-body` (8px) mais a borda do `<details>` (1px) deslocavam a grade 9px
  por nível — a coluna do ano no talhão caía 18px à direita do cabeçalho e, com
  vários anos, os valores pareciam encavalados (ao rolar, sobrava só o fim do
  texto, ex.: “cional”).
- **O anexo do laudo casa pela CHAVE da OS** (`chave_os`), o mesmo critério dos
  relatórios por OS; o laudo «(sem OS)» só aparece no consolidado. Sem PDF
  (nenhum conversor) o anexo sai só com o `.docx` e o botão do PDF não é montado.
- **O modelo visual é um TRIO com o mesmo nome-base**: trocar só o `.html` deixa
  o CSS/JS órfãos; os caminhos saem de `FileManager`.
- **Anexo lê caminho RELATIVO a `saida/`**: é o contrato do bloco `laudos`
  (`LaudoAttachment._resolve`); caminho absoluto no bloco quebra o anexo.
- **O bloco `statistics` só existe no FIM da execução**: o HTML nasce com a
  janela MEDIDA (início de `run` → gravação) e é a Pipeline que pede a reescrita
  (`atualizar_rodape`) depois de gravar o bloco. Rodar a API 3 pela CLI num JSON
  que já tem o bloco mostra a janela REGISTRADA nele (a da execução anterior),
  não o tempo do HTML novo. A linha é achada pelo `id="rodapeProcessamento"`:
  mexer nesse `id`/na classe `rodape-processamento` sem atualizar a marca deixa o
  rodapé com o tempo medido (com `warning` no log) — a API 3 não grava o bloco
  `statistics`, só o lê.
- **A versão do relatório vive no CÓDIGO, não no modelo**: `RELATORIO_VERSAO`/
  `RELATORIO_VERSAO_DATA` (`ReportRendering.py`) → `$VERSAO_RELATORIO` no rodapé
  (o `V` e o `·` são montados por `texto_versao()`). Escrever `V3.0.0` à mão no
  `template_02.html` cria uma segunda fonte de verdade. A barra lateral **não**
  mostra versão nem data (o antigo `.side-info` saiu): quem mostra é o rodapé, e
  só ele — com o aviso de geração automática, o tempo de processamento e a data
  de geração.

## 10. Execução e validação

```powershell
# esta API isolada: JSON de saida/ → HTML de saida/
python -m apis.03ApiReports.ApiReports --json saida\dados_20261013_082752.json

# só as métricas (imprime o consolidado; não gera HTML)
python -m apis.03ApiReports.validador --json saida\dados_20261013_082752.json --saida saida\out.json

# verificação de sintaxe (sem renderizar)
python -m py_compile apis\03ApiReports\ApiReports.py apis\03ApiReports\validador.py apis\03ApiReports\ReportRendering.py apis\03ApiReports\FileManager.py apis\03ApiReports\LaudoAttachment.py

# o RODAPÉ do HTML gerado (aviso + tempo de processamento + data de geração + versão)
Select-String -Path 'saida\Consolidado.html' -Pattern 'rodape-info|rodape-processamento|rodape-gerado|V3\.0\.0'

# a versão NÃO pode sobrar na barra lateral (o bloco `.side-info` foi removido)
Select-String -Path 'saida\Consolidado.html' -Pattern 'side-info'
```

Programaticamente — a pasta da API começa com dígito, então
`from apis.03ApiReports… import …` é `SyntaxError`:

```python
from importlib import import_module

ApiReports = import_module("apis.03ApiReports.ApiReports").ApiReports
result = ApiReports().run("saida/dados_20261013_082752.json")
if result is not None:
    print(result.report_paths, result.total_files,
          result.total_os, result.total_records)
```

Esperado: uma pasta `saida/OS_<número>/` por OS (com o `<OS>_report.html` dentro)
+ `saida/Consolidado.html`, com `Relatório gravado: …` no log; sem os blocos
`validacao`/`laudos`, apenas os `warning` correspondentes.

## 11. Versão do relatório (regra de numeração)

O relatório tem **versão própria** — a do SOFTWARE é outra
(`config.ROTULO_APLICACAO`, do SISTEMA) — e ela aparece em UM lugar: o **RODAPÉ**
(`Desenvolvido por Matheus Martinelli · V3.0.0 · 23/10/2026`). A barra lateral não
mostra mais versão nem data (o antigo bloco `.side-info` saiu do
`template_02.html`).

**Sempre que o relatório for modificado, suba a versão E atualize a data.** As
duas constantes vivem em `apis/03ApiReports/ReportRendering.py`:

| Constante | Papel |
|---|---|
| `RELATORIO_VERSAO` | a versão (`"3.0.0"`), no formato `MAJOR.MINOR.PATCH` |
| `RELATORIO_VERSAO_DATA` | a data da ÚLTIMA mudança (`"23/10/2026"`) |

`ReportRendering.texto_versao()` monta o texto exibido (`V3.0.0 · 23/10/2026`) e o
`$VERSAO_RELATORIO` do `template_02.html` é o **único** ponto de exibição.

**Qual nível subir:**

| Nível | De → para | Quando |
|---|---|---|
| **PATCH** | `3.0.0 → 3.0.1` | alteração PEQUENA: texto, rótulo, estilo, correção de um painel, ajuste de coluna |
| **MINOR** | `3.0.1 → 3.1.0` | sub-painel, campo ou coluna NOVA dentro de um painel que já existe (ex.: um `3.1`, um `5.2`) |
| **MAJOR** | `3.1.0 → 4.0.0` | componente GRANDE novo: painel novo, dashboard novo, mudança estrutural da página |

Ao subir um nível, os de baixo **zeram** (`3.0.1 → 3.1.0` e `3.1.0 → 4.0.0`).

Regras da casa:

1. **Toda** mudança no relatório (painel, métrica, CSS, JS, modelo, rodapé) sobe
   a versão e atualiza a data — o nome do `.html` não tem data/hora, então a
   versão do rodapé é o que diz ao leitor QUAL relatório ele está vendo;
2. a mudança entra também no `docs/data/changelog.txt`, com o de-para
   (`V2 → V3.0.0`, por exemplo) e o nível (PATCH/MINOR/MAJOR);
3. mexer na versão do relatório **não** é mexer no `$ROTULO_APLICACAO` (marca do
   SOFTWARE, do SISTEMA) nem em chave alguma do JSON;
4. a data é a do DIA da mudança (`dd/mm/aaaa`), não a da execução — quem mostra a
   data da execução é o `Gerado em:` (que vem do `gerado_em` do JSON).

Histórico: `V2 · 07/10/2026` (última versão antes da regra) → **`V3.0.0 ·
23/10/2026`** (adoção da regra de numeração) → **`V3.0.1 · 23/10/2026`** (PATCH: o
rodapé mostra só o TEMPO, sem `início`/`fim`, em fonte pequena).
