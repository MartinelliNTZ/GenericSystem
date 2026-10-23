---
name: os-report-html
description: >-
  Relatório geral do projeto (HTML) do Acompanhamento de OS —
  `plugins/os_tracker/report/` (`OsReportHtmlService`, `ReportSource`,
  `ReportDataBuilder`, `ReportContext`, `ShapeGeoJsonReader`, `OsReportAssets`,
  `OsReportHtmlGenerator` e `panels/`) + o modelo visual em TRÊS arquivos
  (`core/template/relatorio_geral_projeto.html` + `.css` + `.js`). Carrega-se
  quando a tarefa for gerar ou alterar o relatório HTML da OS: painéis 1–4
  (visão geral, distribuição espacial 2.1/2.2/2.3, atividades e base de dados),
  os mapas Leaflet dos shapes de limites/zonas, o rodapé (aviso + tempo de
  processamento + data de geração + VERSÃO do relatório) e a versão do
  relatório. A ferramenta, o banco e os atalhos do Acompanhamento de OS estão em
  `docs/skills/SKILL_PROJECT.md`.
---

# os-report-html · Relatório geral do projeto (HTML)

## 1. Identidade

| Item | Valor |
|---|---|
| Responsabilidade | Montar e gravar o relatório HTML de **UMA OS** a partir do registro do banco + os SHAPES das bases (limites e zonas de manejo) |
| Entrada | `record` (registro da OS) + `mother` (pasta-mãe dos projetos) |
| Saída | `<pasta da OS>/14_RELATORIOS/Relatorio Geral Projeto/OS_<chave>_Relatorio Geral Projeto_<AAAAMMDDHHMMSS>.HTML` (arquivo AUTOSSUFICIENTE) |
| Entry point | `OsReportHtmlService.generate(mother, record, tool_key=ToolKey.OS_TRACKER.value)` → caminho do `.HTML` |
| Quem chama | `OsTrackerPlugin._on_generate_html_report` — atalho **RELATÓRIO HTML** do painel Atalhos (gera e abre a pasta) |
| Modelo visual | **TRIO com o mesmo nome-base** em `core/template/`: `relatorio_geral_projeto.html` (estrutura) + `.css` (estilos) + `.js` (comportamento) |
| União dos arquivos | `OsReportAssets.html(tool_key)` — embute o CSS e o JS no HTML (o `.HTML` gerado não depende de arquivos ao lado) |
| Versão do relatório | `ReportDataBuilder.REPORT_VERSION` + `REPORT_VERSION_DATE` → `versao_relatorio` no RODAPÉ (§11) |
| Teste sem Qt | o submódulo é lógico (sem widgets): `OsReportHtmlService.generate(...)` roda em script Python (§10) |

## 2. Fluxo (`OsReportHtmlService.generate`)

1. `ReportSource.context(mother, record, tool_key)` → `ReportContext` com o
   registro, a pasta da OS resolvida, o caminho de cada base, o resumo de cada
   base (`OsTrackerService.asset_info`), a data de geração
   (`dd/mm/aaaa hh:mm`) e os SHAPES já em GeoJSON.
2. `ShapeGeoJsonReader.read(path, key, tool_key)` → `FeatureCollection`
   (EPSG:4326) por base; base ausente/ilegível → `None` + `warning`
   (`OSREP_SHAPE_MISSING`/`OSREP_SHAPE_EMPTY`/`OSREP_SHAPE_ERR`) e o relatório
   sai com o aviso no mapa (nunca quebra).
3. `ReportDataBuilder.build(context)` → `window.DADOS_PROJETO`: parte do
   `SCHEMA` (todas as chaves com valor neutro) e aplica, na ORDEM do template,
   cada builder de `PANELS`; preenche `gerado_em`, `versao_data` e
   `versao_relatorio`.
4. `OsReportHtmlGenerator.generate(data, os_folder, os_key, tool_key)`:
   `OsReportAssets.html(tool_key)` une o TRIO → troca o token
   `<!--{{DADOS_PROJETO}}-->` pelo `<script>` com os dados → grava o `.HTML`
   no destino do relatório da OS (mesma pasta por TIPO, mesma regra do
   `OsReportGenerator`).
5. Logs: `OSREP_ASSETS_DONE` (assets embutidos), `OSREP_HTML_GENERATED` e
   `OSREP_SERVICE_DONE` (fim).

## 3. Arquivos (quem faz o quê)

| Arquivo | Papel |
|---|---|
| `plugins/os_tracker/report/OsReportHtmlService.py` | **Fachada** do submódulo: resolve a fonte, monta os dados e gera o arquivo — o plugin conhece SÓ esta classe |
| `plugins/os_tracker/report/ReportSource.py` | **ÚNICA** classe que fala com `OsTrackerService`: pasta da OS, arquivo de cada base (`ASSET_KEYS`), versão dos dados e o `ReportContext` |
| `plugins/os_tracker/report/ReportDataBuilder.py` | Schema do template + builders de painel na ordem (`PANELS`) e a **versão do relatório** (`REPORT_VERSION`/`REPORT_VERSION_DATE`/`version_label`) |
| `plugins/os_tracker/report/ReportContext.py` | Contexto IMUTÁVEL entregue aos builders (`record`, `mother`, `tool_key`, `generated_at`, `data_version`, `os_folder`, `asset_paths`, `assets`, `shapes`) com `value()`, `asset()` e `shape()` |
| `plugins/os_tracker/report/ShapeGeoJsonReader.py` | Vetor da base → GeoJSON EPSG:4326, só com as propriedades do template (`SHAPE_FIELDS`) |
| `plugins/os_tracker/report/OsReportAssets.py` | **Une HTML + CSS + JS** num só documento (embute o CSS e o JS); erro próprio por asset ausente |
| `plugins/os_tracker/report/OsReportHtmlGenerator.py` | Documento + dados → `.HTML` (troca o token pelo script com `window.DADOS_PROJETO`) |
| `plugins/os_tracker/report/panels/PanelBuilder.py` | Contrato dos builders (`PANEL_ID`/`PANEL_TITLE`/`build`) + o helper `base_info(context, key)` |
| `plugins/os_tracker/report/panels/PanelVisaoGeral.py` | Painel **1** — projeto + dados da OS |
| `plugins/os_tracker/report/panels/PanelFazendas.py` | Painel **2.1** — fazendas e talhões (derivados do shape de limites) |
| `plugins/os_tracker/report/panels/PanelLimites.py` | Painel **2.2** — GeoJSON dos limites + resumo da base |
| `plugins/os_tracker/report/panels/PanelZonas.py` | Painel **2.3** — GeoJSON das zonas + resumo da base |
| `plugins/os_tracker/report/panels/PanelAtividades.py` | Painel **3** — atividades (ainda sem fonte no banco) |
| `plugins/os_tracker/report/panels/PanelBaseDados.py` | Painel **4** — pastas criadas (4.1) e anos com dados (4.2) |
| `core/template/relatorio_geral_projeto.html` | ESTRUTURA: markup dos 4 painéis, do menu lateral e do rodapé + o token `<!--{{DADOS_PROJETO}}-->` e as tags `<link>`/`<script src>` dos irmãos |
| `core/template/relatorio_geral_projeto.css` | ESTILOS: tema escuro azul, painéis por módulo, cartões, chips, tabelas, mapas, tooltips e o rodapé em 4 colunas |
| `core/template/relatorio_geral_projeto.js` | COMPORTAMENTO: helpers, pintura dos painéis, mapas Leaflet, menu lateral, tooltips, expandir/recolher e o objeto PADRÃO de `DADOS_PROJETO` |
| `utils/OsReportGenerator.py` | DESTINO do relatório (`REPORTS_FOLDER`/`REPORT_TYPE`/`report_path`) herdado pelo gerador HTML |
| `utils/vector/VectorLayerSource.py` | Leitura do vetor (`.shp`/`.gpkg`/`.kml`/`.kmz`/`.geojson`) usada pelo leitor de shapes |

## 4. Contrato de entrada (o registro da OS)

| Chave | Uso |
|---|---|
| `os` | Chave da OS (entra no título, no nome do arquivo e na resolução da pasta) |
| `name` / `client` / `commercial_name` / `cnpj` | Cards do painel 1 (`nome`, `cliente`, `nome comercial`, `CNPJ`); o `commercial_name` também é o subtítulo do cabeçalho |
| `path` | Caminho RELATIVO da pasta da OS (resolvido em cascata: gravado → `OS_<chave>...` na pasta-mãe) |
| `updated_at` | `versao_data` (data da versão dos dados do relatório) |
| `folders` / `years` | Painel 4 — pastas criadas (4.1) e anos com dados (4.2) |
| `limites` / `zonas_manejo` | Bloco do banco com `features`, `area_ha`, `file`, `source`, `inserted_at` — vira o **resumo da base** (2.2/2.3) e o caminho do vetor lido pelo `ShapeGeoJsonReader` |

**Campos que o banco AINDA não fornece** (`tipos_manejo`, `area_contratada_ha`,
`n_cars`, `data_inicio`, `ano_cenario_base` e `atividades`) permanecem
**VAZIOS** — o template já exibe o estado vazio e nada é inventado.

## 5. Contrato de saída (o `.HTML`)

| Item | Valor |
|---|---|
| Destino | `<pasta da OS>/14_RELATORIOS/<TIPO>/` — o TIPO vem do `OsReportGenerator` (`Relatorio Geral Projeto`) e a pasta é criada se não existir |
| Nome | `OS_<chave>_<TIPO>_<AAAAMMDDHHMMSS>.HTML` — **com data/hora** (cada geração é um arquivo novo) |
| Arquivo autocontido | o CSS e o JS entram EMBUTIDOS (`OsReportAssets`); só o Leaflet vem de CDN |
| Dados | um `<script>` com `window.DADOS_PROJETO = {…};` no lugar do token; o JSON escapa `</` para `<\/` |
| Mapas | Leaflet + satélite Esri (World Imagery) e as camadas de referência; a legenda flutua SOBRE o mapa (2.2 com o checkbox "Mostrar nome dos talhões") |
| Rodapé | `.rodape-grade` (marca + Links + Contato + Redes sociais), `.rodape-info` (11px: aviso de geração automática, `Tempo de processamento:` **só quando o dado existe** e `Gerado em:`) e `.rodape-fim` (© + "Desenvolvido por Matheus Martinelli" + **a versão do relatório**) |
| Menu lateral | NÃO mostra versão nem data (o antigo bloco `.side-info` saiu) e o CABEÇALHO não mostra "Gerado em" — a data fica SÓ no rodapé |

## 6. Painéis exibidos

| # | Painel | O que alimenta |
|---|---|---|
| 1 | **Visão geral** | `PanelVisaoGeral` — cartões (OS, nome, cliente, nome comercial, CNPJ, pasta, área contratada, CARs, data de início, cenário base e última atualização), os tipos de manejo e a pasta completa |
| 2.1 | **Fazendas e talhões** | `PanelFazendas` — agrupa o shape de limites por fazenda (`fazenda`/`talhao`/`area_ha`) e soma a área por fazenda + total |
| 2.2 | **Limites** | `PanelLimites` — mapa (uma cor por fazenda, rótulo do talhão e popup) + resumo da base (contagem "Talhões", Área (ha), Arquivo, Origem e Registrado em) |
| 2.3 | **Zonas de manejo** | `PanelZonas` — mapa das zonas (legenda pelas zonas presentes) + resumo da base (contagem "Zonas", …) |
| 3 | **Atividades** | `PanelAtividades` — lista de atividades (sem fonte no banco: estado vazio) |
| 4.1 | **Pastas criadas** | `PanelBaseDados` — `folders` do registro |
| 4.2 | **Anos com dados** | `PanelBaseDados` — `years` do registro |

Cada painel é preenchido por UM builder desacoplado em
`plugins/os_tracker/report/panels/`, registrado em `ReportDataBuilder.PANELS`
na ORDEM do template — para dividir um painel, basta registrar outro builder com
subnúmero (ex.: `PANEL_ID = "2.4"`).

## 7. Regras intocáveis

1. **Um só arquivo de saída**: o relatório é AUTOSSUFICIENTE — CSS e JS vão
   embutidos pelo `OsReportAssets`; nada de `<link>`/`<script src>` locais.
2. **O modelo visual é um TRIO com o mesmo nome-base**: trocar só o `.html`
   deixa o CSS/JS órfãos (o `OsReportAssets` levanta `ValueError` se as tags
   sumirem).
3. **O builder não lê disco, banco nem Qt**: recebe o `ReportContext` pronto e
   devolve só as chaves do template que lhe pertencem.
4. **Nada é inventado**: chave que o banco não fornece permanece vazia e o
   template mostra o estado vazio.
5. **A base ausente não quebra o relatório**: shape ilegível → `None` +
   `warning` + o aviso no mapa ("Aguardando o shape …").
6. **A versão do relatório vive no CÓDIGO** (`ReportDataBuilder`), não no
   modelo, e é exibida **só no rodapé** (§11).
7. **Nunca `except:` sem `as e` e logger**: falha de shape/base é logada e o
   lote continua.
8. **1 classe = 1 responsabilidade**: a fachada orquestra, a fonte resolve,
   os builders preenchem, o gerador grava.
9. **Alinhamento com o sistema**: tema escuro azul, painéis numerados
   (`01`, `02`, `2.1`), descrição em tooltip (o "i" do cabeçalho do painel),
   chevron de expandir/recolher e o rodapé em 4 colunas.

## 8. Onde mexer

| Preciso… | Onde |
|---|---|
| Mudar um valor do painel 1 | `panels/PanelVisaoGeral.py` |
| Mudar o agrupamento de fazendas/talhões | `panels/PanelFazendas.py` |
| Mudar o mapa/resumo de limites ou zonas | `panels/PanelLimites.py` / `panels/PanelZonas.py` |
| Painel novo ou subpainel novo | novo builder em `panels/` + registro em `ReportDataBuilder.PANELS` (na ordem do template) |
| Chave nova em `DADOS_PROJETO` | `ReportDataBuilder.SCHEMA` + o builder que a preenche |
| Estilo, cor, layout, rodapé | `core/template/relatorio_geral_projeto.css` |
| Cálculo, pintura do painel, mapa, menu, tooltip | `core/template/relatorio_geral_projeto.js` |
| Markup, texto fixo, tooltip, estrutura do rodapé | `core/template/relatorio_geral_projeto.html` |
| Propriedades lidas do vetor (campos do shape) | `ShapeGeoJsonReader.SHAPE_FIELDS`/`NUMERIC_FIELDS` |
| Bases que entram no relatório | `ReportSource.ASSET_KEYS` |
| Destino, TIPO e nome do arquivo | `utils/OsReportGenerator.py` (`REPORTS_FOLDER`/`REPORT_TYPE`/`report_path`) |
| Como os assets são unidos | `OsReportAssets` (tags/molde do CSS e do JS) |
| **Subir a versão do relatório** | `ReportDataBuilder.REPORT_VERSION` + `REPORT_VERSION_DATE` (§11) |
| A pasta/arquivos de uma base | `OsTrackerService.project_folder`/`asset_file_path` (domínio — `SKILL_PROJECT.md`) |

## 9. Armadilhas

- **O trio é indivisível**: renomear/apagar o `.css` ou o `.js` de
  `core/template/` faz o `OsReportAssets` levantar `FileNotFoundError`
  (`OSREP_ASSET_MISSING`) — e editar o `<link>`/`<script src>` do HTML derruba o
  embutimento (`OSREP_ASSET_TAG_MISSING`).
- **Sem timestamp? Não**: aqui o nome TEM data/hora
  (`…_<AAAAMMDDHHMMSS>.HTML`), então cada geração cria um arquivo novo — o
  relatório do Word (`OsReportGenerator`) segue a mesma regra.
- **A versão do relatório não vai para o menu lateral nem para o cabeçalho**: o
  antigo bloco `.side-info` (versão + data) foi removido e o cabeçalho não mostra
  mais "Gerado em" — quem mostra data e versão é SÓ o rodapé
  (`.rodape-info`/`.rodape-fim`).
- **O tempo de processamento é OPCIONAL**: sem `processamento` em
  `DADOS_PROJETO` a linha sai de cena (`hidden`) — não se inventa duração.
- **Os mapas precisam do Leaflet da CDN**: sem internet o JS mostra o aviso no
  lugar do mapa (não é falha) e a legenda continua listando as fazendas/zonas.
- **Ao reabrir um painel recolhido** os mapas ficam com o tamanho errado: o JS
  chama `invalidateSize()` na instância guardada no elemento
  (`el.__mapaLeaflet`) — mexer nessa marca quebra o mapa.
- **A logo é externa** (CDN do Google): sem rede a caixa mostra a sigla "AR"
  (o `ligarLogos` marca `.sem-img`).
- **`DADOS_PROJETO` é a única ponte Python → página**: o Python não monta HTML
  de painel (só o markup fixo do template); quem pinta os painéis é o JS.
- **Campos sem fonte no banco** (`tipos_manejo`, `atividades`, …) saem com os
  EXEMPLOS em tom fantasma no painel 1 — é a única "amostra" da página e está
  marcada como tal; não transforme isso em dado.
- **O `report_path` é herdado**: mudar a pasta/nome do relatório HTML sem olhar
  o `OsReportGenerator` afeta os DOIS relatórios da OS (Word e HTML).

## 10. Execução e validação

Pelo aplicativo (caminho normal): ferramenta **Acompanhamento de OS** → escolher
a OS → painel Atalhos → **RELATÓRIO HTML** (gera e abre a pasta).

Pelo Python (o submódulo não tem Qt — roda em script):

```python
from pathlib import Path

from core.enum.ToolKey import ToolKey
from plugins.os_tracker.report.OsReportHtmlService import OsReportHtmlService

record = {"os": "220", "name": "OS 220", "client": "Cliente", "path": "OS_220_Cliente"}
caminho = OsReportHtmlService.generate(Path("C:/Projetos"), record, tool_key=ToolKey.OS_TRACKER.value)
print(caminho)   # .../OS_220_Cliente/14_RELATORIOS/Relatorio Geral Projeto/OS_220_...HTML
```

Verificação de sintaxe dos módulos (sem renderizar):

```powershell
python -m py_compile plugins\os_tracker\report\OsReportAssets.py plugins\os_tracker\report\OsReportHtmlGenerator.py plugins\os_tracker\report\ReportDataBuilder.py plugins\os_tracker\report\ReportSource.py plugins\os_tracker\report\panels\PanelBuilder.py
```

O `.HTML` gerado deve sair com o CSS e o JS EMBUTIDOS e sem as tags locais:

```powershell
Select-String -Path 'C:\...\OS_220_...HTML' -Pattern 'relatorio_geral_projeto\.(css|js)|rodape-info|rodape-fim|DADOS_PROJETO'
```

Esperado: **nenhum** `<link href="relatorio_geral_projeto.css">` nem
`<script src="relatorio_geral_projeto.js">` (foram embutidos), o
`window.DADOS_PROJETO` presente e as classes do rodapé (`rodape-info`,
`rodape-fim`) no arquivo.

## 11. Versão do relatório (regra de numeração)

O relatório tem **versão própria** — a do software é outra (`ToolRegistry`) — e
ela aparece em UM lugar: o **RODAPÉ**
(`Desenvolvido por Matheus Martinelli · V1.0.0 · 23/10/2026`). O menu lateral
não mostra versão nem data e o cabeçalho não mostra a data de geração.

**Sempre que o relatório for modificado, suba a versão E atualize a data.** As
duas constantes vivem em `plugins/os_tracker/report/ReportDataBuilder.py`:

| Constante | Papel |
|---|---|
| `REPORT_VERSION` | a versão (`"1.0.0"`), no formato `MAJOR.MINOR.PATCH` |
| `REPORT_VERSION_DATE` | a data da ÚLTIMA mudança (`"23/10/2026"`) |

`ReportDataBuilder.version_label()` monta o texto exibido
(`V1.0.0 · 23/10/2026`) e ele viaja no `DADOS_PROJETO` como `versao_relatorio` —
o `<span id="versaoRelatorio">` do `.rodape-fim` é o **único** ponto de exibição.

**Qual nível subir:**

| Nível | De → para | Quando |
|---|---|---|
| **PATCH** | `1.0.0 → 1.0.1` | alteração PEQUENA: texto, rótulo, estilo, correção de um painel, ajuste de coluna |
| **MINOR** | `1.0.1 → 1.1.0` | sub-painel, campo ou coluna NOVA dentro de um painel que já existe (ex.: um `2.4`, um `4.3`) |
| **MAJOR** | `1.1.0 → 2.0.0` | componente GRANDE novo: painel novo, dashboard novo, mudança estrutural da página |

Ao subir um nível, os de baixo **zeram** (`1.0.1 → 1.1.0` e `1.1.0 → 2.0.0`).

Regras da casa:

1. **Toda** mudança no relatório (painel, campo, CSS, JS, modelo, rodapé) sobe a
   versão e atualiza a data — o nome do arquivo tem data/hora, mas é a versão do
   rodapé que diz ao leitor QUAL relatório ele está vendo;
2. a mudança entra também no `docs/data/changelog.txt`, com o de-para
   (`V1.0.0 → V1.1.0`, por exemplo) e o nível (PATCH/MINOR/MAJOR);
3. mexer na versão do relatório **não** é mexer na versão do SOFTWARE
   (`ToolRegistry`) nem em chave alguma do banco;
4. a data é a do DIA da mudança (`dd/mm/aaaa`), não a da execução — quem mostra a
   data da execução é o `Gerado em:` do rodapé (`generated_at`).

Histórico: **`V1.0.0 · 23/10/2026`** — adoção da regra de numeração junto com a
separação do modelo visual em três arquivos (HTML + CSS + JS) e o rodapé novo.



