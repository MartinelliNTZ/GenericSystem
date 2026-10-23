# Skill: Sistema de Projetos (.mtl)

Esta skill descreve o sistema de gerenciamento de projetos do Aetheris ToolBox, incluindo criação, abertura, salvamento, projetos recentes e exibição do status na AppBar.

## Visão Geral

O sistema de projetos usa arquivos `.mtl` (formato JSON) para armazenar metadados do projeto. Cada projeto contém:

```json
{
    "project_name": "MeuProjeto",
    "path": "C:/caminho/para/pasta",
    "created_at": "2026-05-14T20:30:00",
    "last_modified": "2026-05-14T20:30:00",
    "file_path": "C:/caminho/para/pasta/MeuProjeto.mtl"
}
```

## Componentes do Sistema

| Componente | Arquivo | Função |
|---|---|---|
| `ProjectUtil` | `utils/ProjectUtil.py` | Utilitário estático para criar, ler, atualizar arquivos .mtl |
| `SaveProjectPlugin` | `plugins/project_manager/SaveProjectPlugin.py` | Plugin INSTANT para salvar/criar projetos |
| `MenuManager` | `core/config/MenuManager.py` | Lógica de Novo, Abrir, Salvar como, Abrir Recente no menu Arquivo |
| `FileMenuItem` | `core/menus/FileMenuItem.py` | Aba "Arquivo" da barra de menus com ações de projeto |
| `RecentProjectsManager` | `utils/RecentProjectsManager.py` | Gerencia lista de projetos recentes |
| `AppBar` | `resources/widgets/app_bar.py` | Exibe status do projeto ativo na barra de título |
| `Preferences` | `utils/Preferences.py` | Persiste `current_project` e `root_folder` na seção `ToolKey.SYSTEM` |

## Fluxo de Dados

```
Usuário clica "Salvar como" (menu ou plugin)
    → ExplorerUtils.save_file() (diálogo nativo)
    → ProjectUtil.create_project_safe() (cria .mtl com validação)
    → Preferences.save_tool_prefs(ToolKey.SYSTEM, {current_project, root_folder})
    → SignalManager.instance().project_changed.emit()
    → MainWindow._update_appbar_project_status() (atualiza AppBar)
    → FileManager recarrega com nova raiz
```

## ProjectUtil — Utilitário de Projeto

`utils/ProjectUtil.py` fornece métodos estáticos:

### Criar projeto
```python
from utils.ProjectUtil import ProjectUtil

# Cria .mtl (sobrescreve sem perguntar)
result = ProjectUtil.create_project("C:/pasta", "MeuProjeto")

# Cria .mtl com validação (pergunta se já existe)
result = ProjectUtil.create_project_safe("C:/pasta", "MeuProjeto")
# Retorna dict com dados ou None se falhar/cancelar
```

### Ler projeto
```python
data = ProjectUtil.load_project("C:/pasta/MeuProjeto.mtl")
# Retorna dict ou None
```

### Atualizar
```python
# Atualiza last_modified para data/hora atual
result = ProjectUtil.update_last_modified("C:/pasta/MeuProjeto.mtl")

# Atualiza campo específico
result = ProjectUtil.update_field("C:/pasta/MeuProjeto.mtl", "project_name", "NovoNome")
```

### Utilitários
```python
# Obtém root_folder do projeto ativo (das preferências)
root = ProjectUtil.get_root_folder()

# Lista arquivos por extensões na pasta do projeto
files = ProjectUtil.get_files_by_extensions([".las", ".laz"])
# Retorna {nome_arquivo: caminho_completo}
```

## SaveProjectPlugin — Plugin Instantâneo

`plugins/project_manager/SaveProjectPlugin.py` é uma ferramenta do tipo **INSTANT** (não abre aba, executa ação imediata e se auto-destrói).

### Fluxo:
1. Carrega `current_project` das preferências do sistema
2. Se existe e arquivo está no disco → `_handle_save_existing()` (atualiza last_modified)
3. Se não existe → `_handle_create_new()` (abre diálogo "Salvar como")
4. Emite `project_changed` e exibe MessageBox de confirmação
5. Chama `_self_destruct()` (remove o widget)

### Registro no ToolRegistry:
```python
Tool(
    key=ToolKey.SAVE_PROJECT,
    name="Salvar Projeto",
    tool_type=ToolType.PROJECT,
    plugin_class=SaveProjectPlugin,
    show_in_toolbar=True,
    show_in_menu=True,
)
```

## MenuManager — Lógica de Projeto no Menu Arquivo

O `MenuManager` em `core/config/MenuManager.py` gerencia as ações de projeto do menu Arquivo:

### Novo Projeto (`_on_novo`)
```python
# Zera current_project e root_folder nas preferências
Preferences.save_tool_prefs(ToolKey.SYSTEM, {
    "current_project": "",
    "root_folder": "",
})
SignalManager.instance().project_changed.emit()
```

### Abrir Projeto (`_on_abrir`)
```python
# 1. Diálogo nativo para selecionar .mtl
file_path = ExplorerUtils.open_file(title="Abrir projeto", file_filter="Projeto Aetheris (*.mtl)")

# 2. Valida com ProjectUtil.load_project()
project_data = ProjectUtil.load_project(file_path)

# 3. Salva nas preferências
sys_prefs["current_project"] = file_path
sys_prefs["root_folder"] = os.path.dirname(file_path)
Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

# 4. Atualiza last_modified
ProjectUtil.update_last_modified(file_path)

# 5. Adiciona aos recentes
self._recent_manager.add_recent(file_path)

# 6. Emite sinais
SignalManager.instance().recent_projects_changed.emit(self._recent_manager.get_validated())
SignalManager.instance().project_changed.emit()
```

### Salvar como (`_on_salvar_como`)
```python
# 1. Diálogo nativo "Salvar como"
file_path = ExplorerUtils.save_file(title="Salvar projeto como", file_filter="Projeto Aetheris (*.mtl)")

# 2. ProjectUtil.create_project_safe() (valida substituição)
result = ProjectUtil.create_project_safe(folder, project_name)

# 3. Salva nas preferências + recentes + emite sinais
Preferences.save_tool_prefs(ToolKey.SYSTEM, {current_project, root_folder})
self._recent_manager.add_recent(result["file_path"])
SignalManager.instance().recent_projects_changed.emit(...)
SignalManager.instance().project_changed.emit()
```

### Abrir Recente (`_on_recente_abrir`)
```python
# 1. Valida se arquivo existe (os.path.isfile)
# 2. Carrega com ProjectUtil.load_project()
# 3. Salva nas preferências
# 4. Atualiza last_modified
# 5. Move ao topo dos recentes (add_recent)
# 6. Emite sinais
```

## FileMenuItem — Aba "Arquivo" da MenuBar

`core/menus/FileMenuItem.py` constrói o menu Arquivo com:

```
Arquivo
├── Novo              → novo_clicked Signal
├── Abrir             → abrir_clicked Signal
├── Salvar como       → salvar_como_clicked Signal
├── ─────────
├── Abrir Recente     → submenu RecentProjectsMenu
│   ├── Projeto1.mtl  (active)
│   ├── Projeto2.mtl  (active)
│   └── Projeto3.mtl  (inactive — cinza)
├── ─────────
└── Sair              → sair_clicked Signal
```

### Sinais emitidos:
- `novo_clicked` → `MenuManager._on_novo()`
- `abrir_clicked` → `MenuManager._on_abrir()`
- `salvar_como_clicked` → `MenuManager._on_salvar_como()`
- `recente_clicked(str path)` → `MenuManager._on_recente_abrir(path)`
- `sair_clicked` → `MenuManager._on_sair()`

### Atualização em tempo real:
O `recent_projects_changed` signal reconstrói o submenu de recentes sem ler do disco:
```python
SignalManager.instance().recent_projects_changed.connect(
    self._file_item.rebuild_recentes_from_signal
)
```

## AppBar — Status do Projeto

A `AppBar` em `resources/widgets/app_bar.py` exibe o projeto ativo ao lado do título da janela.

### Formato de exibição:
- **Com projeto ativo:** `Aetheris ToolBox  -  [project_name] - C:/caminho/para/pasta`
- **Sem projeto:** `Aetheris ToolBox  -  [Não salvo]`

### Métodos:
```python
# Define status com nome e caminho
appbar.set_project_status("MeuProjeto", "C:/pasta/MeuProjeto.mtl")

# Limpa status (exibe [Não salvo])
appbar.clear_project_status()
```

### Atualização automática:
A `MainWindow` conecta-se ao sinal `project_changed` e atualiza a AppBar:
```python
SignalManager.instance().project_changed.connect(self._update_appbar_project_status)
```

O método `_update_appbar_project_status()` lê `current_project` das preferências do sistema, carrega o `.mtl` com `ProjectUtil.load_project()` e chama `appbar.set_project_status()` ou `appbar.clear_project_status()`.

Na inicialização, o status é carregado em `_open_home_on_startup()`:
```python
self._update_appbar_project_status()
```

## Sinal project_changed

O sinal `project_changed` (definido em `SignalCatalog`) é o ponto central de notificação. **Sempre que o projeto ativo mudar**, emita este sinal.

### Quem emite:
- `SaveProjectPlugin._handle_save_existing()` — após salvar
- `SaveProjectPlugin._handle_create_new()` — após criar
- `MenuManager._on_novo()` — após limpar
- `MenuManager._on_abrir()` — após abrir
- `MenuManager._on_salvar_como()` — após salvar como
- `MenuManager._on_recente_abrir()` — após abrir recente

### Quem escuta:
- `MainWindow._update_appbar_project_status()` — atualiza AppBar
- `FileManager` (via WorkspaceManager) — recarrega árvore de arquivos

## Sinal recent_projects_changed

O sinal `recent_projects_changed` (definido em `SignalCatalog`) atualiza o submenu "Abrir Recente" em tempo real.

### Payload:
```python
# Lista de dicts
[
    {"path": "C:/proj/Proj1.mtl", "name": "Proj1", "active": True},
    {"path": "C:/proj/Proj2.mtl", "name": "Proj2", "active": False},  # arquivo não existe mais
]
```

### Quem emite:
- `MenuManager._on_abrir()` — após abrir
- `MenuManager._on_salvar_como()` — após salvar como
- `MenuManager._on_recente_abrir()` — após abrir recente

### Quem escuta:
- `FileMenuItem.rebuild_recentes_from_signal()` — reconstrói submenu

## Regras e Boas Práticas

1. **Sempre use `ExplorerUtils`** para diálogos de arquivo — nunca `QFileDialog` diretamente (Contrato 17).
2. **Sempre use `ProjectUtil`** para manipular arquivos .mtl — não crie JSON manualmente.
3. **Sempre emita `project_changed`** após qualquer alteração no projeto ativo.
4. **Sempre emita `recent_projects_changed`** após adicionar/remover recentes.
5. **Use `RecentProjectsManager`** para gerenciar a lista de recentes — não manipule o JSON diretamente.
6. **O `SaveProjectPlugin` é INSTANT** — não cria aba, executa e se auto-destrói.
7. **A lógica de projeto no menu Arquivo** vive no `MenuManager`, não no `FileMenuItem`.
8. **O status visual do projeto** na AppBar é atualizado via `project_changed` — não atualize manualmente.
9. **Ao criar novo projeto**, sempre zere `current_project` e `root_folder` nas preferências.
10. **Ao abrir/salvar**, sempre atualize `last_modified` via `ProjectUtil.update_last_modified()`.

## Banco de Dados de Projetos (`ProjectDatabase`)

Ferramenta **CENTRAL** (`ToolKey.PROJECT_DATABASE`) que mantém um **banco de
dados local em JSON** com o estado das pastas dos projetos (OS) de uma
pasta-mãe, além de um **backup diário** desse banco. **Não substitui** a
varredura do Gerenciador de Estrutura: persiste um retrato dos dados para
consulta rápida.

### Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `plugins/project_database_manager/ProjectDatabasePlugin.py` | UI (cards, árvore, seletores), botão ATUALIZAR DADOS (consulta Firebase + re-escaneia), prefs, backup e varredura assíncrona |
| `plugins/project_database_manager/ProjectDatabaseService.py` | Lógica pura: **NÃO cria OS** — re-escaneia as pastas das OS existentes e atualiza `folders`/`years`; + `ProjectDatabaseWorker` |
| `core/firebase/CloudProjectDatabase.py` | **CLASSE DE BANCO (Contrato 28)**: única porta de entrada dos registros de OS (Firestore) + geração dos backups JSON |
| `core/database/ProjectDatabaseStore.py` | Leitura/escrita atômica dos backups JSON em `.BancoDados` (usada só pela `CloudProjectDatabase`) |
| `utils/ProjectStructureUtil.py` | **FONTE ÚNICA** — dicionário `PROJECT_STRUCTURE` descrevendo toda a estrutura (pastas, anos e futuros arquivos base); os acessores `DEFAULT_PROJECT_FOLDERS`, `PROJECT_FOLDER_TEMPLATES`, `DOCUMENT_YEARS_FOLDER`, `DEFAULT_YEARS` e `DOCUMENT_TEMPLATE` são **derivados** dele. Também: descoberta compartilhada (`discover_projects`, `is_year_folder`, `extract_os`, `normalize_os`, `project_folder`, `collect_created_data`) e tipos de nó (`BaseFile`, `Years`) |
| `utils/ProjectDatabaseBackup.py` | `ensure_daily_backup(...)` — ZIP diário do `.BancoDados` |

### Estrutura em disco

```
<pasta-mãe>/.BancoDados/
├── banco_dados.json          ← consolidado (todas as OS)
└── <numero_os>.json           ← um JSON independente por OS
```

### Chave da OS e estrutura

O nome da pasta segue `OS_<chave>_<resto...>` (ex.: `OS_039_Bunge`,
`OS_169A_AGUA_VIVA`, `OS_181C_RENNER_Grupo Salazar - Faz Rio Alegre`). A **chave**
é o primeiro campo após `OS_`, é **TEXTO** e PODE CONTER **LETRA** — a letra é o
que diferencia as OS de um mesmo projeto. Os **zeros à esquerda são preservados**
(`OS_039_Bunge` → `039`), assim como a letra (`OS_169B_DARRO` → `169B`).

**Uma pasta = UMA OS.** A chave (`os`) — que também dá nome ao arquivo — é a chave
da pasta (`039` → `039.json`, `169A` → `169A.json`) e o registro guarda TUDO no
próprio nível (cliente, nome comercial, CNPJ, caminho, pastas/anos e as bases):

```json
{
  "os": "181C",
  "name": "",
  "path": "OS_181C_RENNER_Grupo Salazar - Faz Rio Alegre",
  "folders": ["01_Acessos_Plataforma_IA_AGLIBS", "03_ENVIO_DE_DOCUMENTOS"],
  "years": ["2023", "2024"],
  "client": "Grupo Salazar - Faz Rio Alegre",
  "commercial_name": "GRUPO JCN",
  "cnpj": "",
  "updated_at": "2026-10-05T17:15:36"
}
```

- Não existe mais o campo/list `sub_os` (o sistema de SubOS foi eliminado).
- `folders`: **apenas** as pastas **padrão** presentes em disco (nunca as fora
  de padrão).
- `years`: **apenas** as pastas de ano presentes em `03_ENVIO_DE_DOCUMENTOS`.
- Ao clicar em ATUALIZAR DADOS, JSONs órfãos (de chaves antigas) são removidos
  automaticamente, mantendo o `.BancoDados` enxuto.

### Regras

1. **Abrir a ferramenta NÃO recalcula nem grava** — apenas lê a base (Firebase).
2. **ATUALIZAR DADOS não cria OS**: consulta o Firestore as OS já existentes,
   **re-escaneia** as pastas associadas (caminhos RELATIVOS à pasta-mãe) e
   atualiza `folders`/`years` (varredura em background + gravação no Firebase),
   exibindo um modal de resumo. A gravação dos backups JSON é da
   `CloudProjectDatabase` (Contrato 28 — plugins com ZERO contato com o JSON).
3. A **pasta-mãe** é a mesma do Gerenciador de Estrutura (fonte única — seção
   `ProjectStructure`), exibida **somente leitura**.
4. O **backup diário** é `zipfile` (stdlib), gravado em
   `<backup_dir>/<YYYYMMDDHHMMSS>.BancoDados.zip` (default
   `~/Documents/Backups/VerraData`), no máximo **1x/dia**, disparado ao iniciar
   **esta ferramenta** (`ProjectDatabaseBackup.ensure_daily_backup`).
5. Código compartilhado vive em `utils/` (Contrato 7) — nenhum plugin importa
   outro plugin.

## Snapshot e changelog da estrutura (Gerenciador de Estrutura)

Ao abrir o **Gerenciador de Estrutura** (`ToolKey.PROJECT_STRUCTURE`), a
ferramenta agenda em background a conferência da estrutura:

1. `ProjectStructureSnapshot.scan` percorre cada pasta `OS_*` e lista **todas**
   as pastas e arquivos (recursivo, caminhos relativos à OS), guardando o
   **tamanho** e a **data da última modificação** de cada arquivo (mapas
   `sizes` e `modified`). Ficam FORA do scan as pastas internas (`.git`,
   `.svn`, `.hg`, `__pycache__`, `.venv`, `venv`, `node_modules`) e arquivos de
   sistema (`desktop.ini`, `Thumbs.db`).
2. `CloudStructureDatabase.load_snapshots` lê o snapshot anterior do Firestore
   (**com paginação** — `list_documents` percorre `nextPageToken`) e
   descompacta o `blob` (gzip+base64).
3. `ProjectStructureChangeDetector.detect` (componente ISOLADO, sem Qt/banco/UI)
   classifica as alterações: criados/removidos, modificados, **renomeados**,
   **movidos** e **renomeação/movimentação de pastas** (validação por árvore).
4. `ProjectStructureChangelog.append_changes` grava/atualiza
   `<pasta da OS>/11_AGROROBOTICA/OS_<numero>_CHANGELOG.DOCX` (blocos em ordem
   decrescente — o mais recente fica no topo), carimbando **quem executou a
   conferência** na linha `Conferido por: Nome (email) — MAQUINA`.
5. `CloudStructureDatabase.save_changes` grava o histórico em
   `estrutura_changelog` e `save_snapshots` atualiza `estrutura_projetos`
   (snapshot compactado; poda OS que não existem mais em disco). O
   `StructureSyncWorker` emite o andamento no **Console**
   (`SignalManager.console_message`): início, resumo final e falhas.

Na primeira execução (banco vazio) só a **linha de base** é salva — nenhuma
alteração é reportada e nenhum Word é criado. Cada OS vista pela **primeira
vez** (sem snapshot anterior, ou com snapshot vazio) é compactada em um único
evento `first_run`: o Word ganha só o bloco **"Primeira inicialização"** em vez
de listar milhares de pastas/arquivos criados (`StructureSyncService.
_compact_first_runs`). Nas execuções seguintes, se houver mudanças, um
**modal** (`MessageBox.show_info`, com detalhes colapsáveis) lista as OS
alteradas.

### Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `utils/ProjectStructureSnapshot.py` | Scanner recursivo (pastas, arquivos, tamanho e data) — sem detecção |
| `utils/ProjectStructureChangeDetector.py` | **Detecção ISOLADA**: classifica criados/removidos/modificados/renomeados/movidos e renomeação/movimentação de pastas |
| `utils/ProjectStructureChangelog.py` | Documento Word `11_AGROROBOTICA/OS_<numero>_CHANGELOG.DOCX` |
| `core/firebase/CloudStructureDatabase.py` | Classe de banco (Firestore): snapshots + histórico |
| `plugins/project_structure_manager/StructureSyncService.py` | Orquestração + `StructureSyncWorker` (background) |
| `plugins/project_structure_manager/ProjectStructurePlugin.py` | Dispara na abertura/refresh e exibe o modal |

### Observações

- O próprio `.DOCX` do changelog e os temporários do Office (`~$*`) são
  ignorados no snapshot — evita "alteração" causada pela escrita do documento.
  A regra é por **padrão**: qualquer `11_AGROROBOTICA/*_CHANGELOG.DOCX`
  (case-insensitive) fica fora do snapshot, então o documento nunca aparece
  como criado, removido nem **modificado**, mesmo se a pasta da OS for
  renomeada.
- Os mapas `sizes` e `modified` guardam, por arquivo, o tamanho (bytes) e a
  data da última modificação (ISO). Eles alimentam a classificação de
  renomeação/movimentação (mesmo tamanho) e de arquivos modificados (data
  diferente). Snapshots antigos sem esses mapas **não** geram falsos positivos.
- A renomeação/movimentação só é declarada quando o par é **inequívoco**
  (1 antigo × 1 novo). Em caso de ambiguidade, o arquivo aparece como
  criado + removido — nunca é "chutado".
- A pasta `11_AGROROBOTICA`, quando criada junto com o documento, é incluída
  no snapshot atual para não aparecer como pasta adicionada na próxima execução.
- A conferência roda no máximo 1 vez a cada **5 minutos** por ferramenta
  (`_SYNC_INTERVAL`), além do gatilho do botão ATUALIZAR.
- **Snapshot no Firestore**: o documento de `estrutura_projetos` guarda o
  snapshot COMPACTADO (`blob` gzip+base64 + `scope`, `os`, `folders_count`,
  `files_count`, `updated_at`). Sem isso, OS grandes passavam de **1 MiB**
  (limite por documento), a gravação falhava (`CSDB_SAVE_PARTIAL`) e a OS
  voltava eternamente como "primeira inicialização". `load_snapshots` também
  pagina a leitura (`nextPageToken`) — antes só a 1ª página era lida e as OS
  restantes pareciam novas a cada abertura.
- **Filtro por nome** (`Pesquisa`) usa **debounce de 350 ms**
  (`_FILTER_DELAY_MS`): a busca só é aplicada depois da última tecla, evitando
  expandir/ler dezenas de projetos a cada caractere digitado.
- **Autoria**: cada bloco do `.DOCX` e cada documento de `estrutura_changelog`
  registram o **operador que executou a conferência**
  (`StructureSyncService._operator`: nome/e-mail da sessão Firebase, fallback
  para o nome salvo nas credenciais + `COMPUTERNAME`). O filesystem **não**
  guarda quem criou/renomeou/removeu cada arquivo — apenas a data da última
  modificação (`modified`); não existe autoria por arquivo.
- O **Acompanhamento de OS** (`OsTrackerPlugin`) exibe, no painel **"Últimas
  alterações da OS"**, apenas as entradas da **OS selecionada**
  (`CloudStructureDatabase.load_changes(limit, os_number=...)` — igualdade em
  `os`, sem índice composto, ordenada em memória por `detected_at`).
- Os painéis do **Acompanhamento de OS** são: **Origem**, **Seleção**, **Dados
  Gerais**, **Atalhos** e **Últimas alterações da OS**.
- O painel **"Dados Gerais"** exibe TODOS os dados em um único `GridLabel` de
  **2 colunas**, na mesma formatação: OS, cliente, pastas criadas, anos criados e
  as infos de cada base do banco — **Feições/Área de Limites** e **Feições/Área de
  Zonas de manejo** (`OsTrackerService.asset_info`; o tooltip traz a origem e a
  data de registro).
- O painel **"Atalhos"** (`GridButtonPanel`) abre, com um clique, a **pasta da
  OS** (`OsTrackerService.project_folder`), a **pasta do arquivo de cada base
  obtida** (`LIMITES`/`ZONAS DE MANEJO` — um botão por link registrado, escondido
  quando a OS não tem o registro), o **changelog Word** da OS
  (`OsTrackerService.changelog_path` → `ProjectStructureChangelog.document_path`),
  aberto no aplicativo padrão, e **BAIXAR RELATÓRIO**, que gera o **relatório da
  OS** pelo template Word (`utils.OsReportGenerator` + `OsTrackerService.report_data`)
  dentro de `<pasta da OS>/14_RELATORIOS/<TIPO>/` e **abre a pasta do relatório**
  no gerenciador de arquivos (não imprime). **Não** há link para o shapefile — a
  abertura da pasta é feita pelos botões de atalho. O caminho do arquivo de
  limites/zonas (`asset_file_path`) é resolvido em cascata — **absoluto →
  relativo à pasta-mãe → relativo à pasta da OS** — cobrindo registros antigos ou
  gravados fora da pasta-mãe. O painel **"Últimas alterações da OS"** continua
  vindo do **banco** (`estrutura_changelog`), nunca do Word.
- O **relatório** da OS usa o TEMPLATE Word
  `core/template/MODELO_RELATORIO_OS.docx` como fonte do layout: o corpo já vem
  pré-preenchido com os campos `{{chave}}` (Dados Gerais, Base de Limites e Base
  de Zonas de Manejo) e o cabeçalho/rodapé da Agrorobótica é preservado. Para
  mudar o relatório, **edite o template** — nenhuma alteração de código é
  necessária. As **últimas alterações NÃO entram** no relatório (é um retrato dos
  dados atuais do banco).
- O **destino** do relatório é a pasta de relatórios da própria OS — uma pasta
  por TIPO, criada se não existir — com data/hora no nome:
  `14_RELATORIOS/<TIPO>/OS_<chave>_<TIPO>_<AAAAMMDDHHMMSS>.DOCX` (ex.:
  `14_RELATORIOS/Relatorio Geral Projeto/OS_220_Relatorio Geral Projeto_20261023134420.DOCX`).
  O TIPO é `OsReportGenerator.REPORT_TYPE` (`"Relatorio Geral Projeto"`) e a pasta
  raiz é `OsReportGenerator.REPORTS_FOLDER` (`"14_RELATORIOS"`).
- O **relatório geral do projeto (HTML)** é o SEGUNDO relatório da OS e tem
  submódulo próprio — `plugins/os_tracker/report/` — com classes desacopladas:
  `OsReportHtmlService` (fachada), `ReportSource` (única que fala com
  `OsTrackerService`), `ReportDataBuilder` (schema + painéis), `ReportContext`,
  `ShapeGeoJsonReader` (vetor da base → GeoJSON EPSG:4326), `OsReportAssets`
  (une HTML + CSS + JS num só documento) e `OsReportHtmlGenerator` (documento +
  dados → `.HTML`). O atalho **RELATÓRIO HTML** (painel Atalhos) gera o arquivo
  e **abre a pasta** do relatório.
- O relatório HTML tem **4 painéis numerados** e um painel pode ser dividido em
  **subpainéis** (o template marca cada pedaço com `Painel N.M`):

  | Painel | Conteúdo |
  |---|---|
  | **1 · Visão geral** | projeto + dados contratuais **+ dados da OS** (nome, cliente, CNPJ, pasta, pasta completa, última atualização) |
  | **2 · Distribuição espacial** | **2.1** fazendas e talhões · **2.2** limites (mapa + resumo da base) · **2.3** zonas de manejo (mapa + resumo da base) |
  | **3 · Atividades** | atividades da propriedade (ainda sem fonte no banco) |
  | **4 · Base de Dados** | **4.1** pastas criadas · **4.2** anos com dados |

  Cada painel/subpainel é preenchido por um builder desacoplado em
  `plugins/os_tracker/report/panels/` (`PanelBuilder` + um arquivo por painel),
  registrado em `ReportDataBuilder.PANELS` na ORDEM do template — para dividir um
  painel, basta registrar outro builder com subnúmero (ex.: `PANEL_ID = "2.4"`).
- **TODAS as infos do relatório emitido em PDF/Word entram no HTML**: os painéis
  **1** (o "Dados Gerais" do template Word: nome, cliente, nome comercial, CNPJ,
  pasta e última atualização), **2.2**/**2.3** (seções "Base de Limites" e "Base
  de Zonas de Manejo": feições, área em ha, arquivo, origem e data de registro) e
  **4** (pastas criadas e anos) replicam os campos de
  `OsTrackerService.report_data` usados no `MODELO_RELATORIO_OS.docx`.
- O **template** do relatório HTML vive em TRÊS arquivos separados, os três em
  `core/template/` (editáveis — são a fonte do layout): a **estrutura**
  (`relatorio_geral_projeto.html`), a **folha de estilo**
  (`relatorio_geral_projeto.css`) e o **comportamento**
  (`relatorio_geral_projeto.js`). O HTML aponta para os irmãos por `<link>` e
  `<script src>` (abrir o template direto no navegador mostra o layout) e o
  `OsReportAssets` **embute** o CSS e o JS no documento, de modo que o `.HTML`
  gerado é autossuficiente (só depende das CDNs do Leaflet). O HTML traz o token
  `<!--{{DADOS_PROJETO}}-->`, que o `OsReportHtmlGenerator` troca por um
  `<script>` com `window.DADOS_PROJETO`; o objeto PADRÃO de
  `DADOS_PROJETO` (campos vazios) fica no topo do `.js` — abrir o template direto
  mostra o layout com os campos vazios.
- O layout segue o **padrão visual do sistema** (tema escuro azul): menu lateral
  com a marca da Agrorobótica (sem versão nem data), cabeçalho fixo com a marca,
  painéis numerados (`01`, `02`, `2.1` …) tingidos pela cor do módulo, cartões,
  chips/pills, tabelas, **descrição em tooltip** (o "i" do cabeçalho do painel,
  movido para a área de ações pelo próprio JS) e o botão de **expandir/recolher**
  de cada painel. No celular o menu vira gaveta, a legenda dos mapas encolhe e
  aparece o botão "voltar ao topo".
- O **rodapé** fecha a página em QUATRO colunas (marca + Links + Contato + Redes
  sociais) e duas faixas: `.rodape-info` (fonte pequena — 11px — com o aviso de
  geração automática, o **tempo de processamento** quando o dado existe e a
  **data de geração**) e `.rodape-fim` (© e a **versão do relatório**,
  `Desenvolvido por Matheus Martinelli · V1.0.0 · 23/10/2026`). A data de geração
  **NÃO** aparece no cabeçalho e a versão/data **NÃO** aparecem no menu lateral —
  quem mostra é só o rodapé. A versão do relatório vive no CÓDIGO
  (`ReportDataBuilder.REPORT_VERSION`/`REPORT_VERSION_DATE` → `versao_relatorio`)
  e tem regra de numeração própria: ver `docs/skills/SKILL_OS_REPORT.md` §11.
- O **passo a passo** do submódulo (classes, contrato de entrada/saída, painéis,
  regras intocáveis, onde mexer, armadilhas e a versão do relatório) está na skill
  dedicada `docs/skills/SKILL_OS_REPORT.md`.
- Os **shapes** entram nos subpainéis **2.2** (`limites`) e **2.3**
  (`zonas_manejo`) como `FeatureCollection` GeoJSON (EPSG:4326), lidos do arquivo
  gravado na OS pelo `ShapeGeoJsonReader` (campos `FAZENDA`/`TALHAO`/`AREA_HA` →
  `fazenda`/`talhao`/`area_ha`; `ZONA` → `zona`) e desenhados no navegador pelo
  Leaflet. A **legenda fica SOBRE o mapa** (canto superior direito, translúcida,
  com rolagem própria e o checkbox "Mostrar nome dos talhões") — não ao lado. O
  subpainel **2.1** (fazendas e talhões) é derivado do MESMO shape de limites.
- Abaixo de cada mapa (2.2 e 2.3) vem o **resumo da base** (`base_limites` /
  `base_zonas`, via `PanelBuilder.base_info`): dois cartões — a **contagem** com
  rótulo coerente (**Talhões** no 2.2 e **Zonas** no 2.3; chave neutra
  `contagem`, no lugar do antigo `feicoes`) e a **Área (ha)** — e uma linha com
  **Arquivo**, **Origem** e **Registrado em**. Base sem registro mostra "Base não
  registrada nesta OS.".
- Chaves que o banco **ainda não fornece** (tipos de manejo, atividades, área
  contratada, CARs, data de início e cenário base) permanecem **vazias** — nada é
  adaptado/inventado; o template já sabe exibir o estado vazio.
- O destino do HTML é o MESMO do relatório Word (mesma pasta por TIPO), mudando
  só a extensão: `14_RELATORIOS/<TIPO>/OS_<chave>_<TIPO>_<AAAAMMDDHHMMSS>.HTML`.
- O botão **EDITAR OS** (ExecutionButtons) abre um formulário
  (`FormLineEditDialog`) pré-preenchido com os campos EDITÁVEIS do registro —
  **nome, cliente, nome comercial e CNPJ** (`OsTrackerService.EDITABLE_FIELDS`) —
  e grava a alteração na fonte oficial via `OsTrackerService.update_order` →
  `CloudProjectDatabase.save_order`. A chave da OS, a pasta e as bases
  (limites/zonas) são derivadas e **não** entram na edição.
- `python-docx` é dependência declarada em `requirements.txt`.

