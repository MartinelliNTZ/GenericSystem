# Plano de Ação: Banco de Dados de Projetos (`ProjectDatabase`)

> **Ferramenta:** Banco de Dados de Projetos (OS) — ferramenta CENTRAL
> **Baseada em:** `plugins/project_manager/SaveProjectPlugin.py`,
> `plugins/project_structure_manager/ProjectStructurePlugin.py`,
> `plugins/project_structure_manager/ProjectStructureScanner.py`,
> `utils/ProjectUtil.py`
> **Categoria:** `CategoryTool.CENTRAL` · **ToolKey:** `PROJECT_DATABASE = "ProjectDatabase"`
> **Prioridade:** Alta
> **Status:** Planejamento (sem código implementado ainda)

---

## 1. Visão Geral

Criar uma ferramenta que mantenha um **banco de dados local em JSON** com o
estado das pastas dos projetos (OS) de uma pasta-mãe, além de uma rotina de
**backup diário** desse banco.

O banco **não substitui** a varredura do Gerenciador de Estrutura: ele
**persiste um retrato** do que já existe em disco para consulta rápida,
relatórios e automações futuras. Os dados só são recalculados/gravados quando o
usuário clica em **ATUALIZAR DADOS**.

A ferramenta fica **fortemente ligada** ao `SaveProjectPlugin` e ao
`ProjectStructurePlugin` (mesma pasta-mãe, mesmas regras de estrutura) e deve
**reutilizar ao máximo** o código existente, adaptando-o onde necessário — sem
criar um segundo framework.

## 2. Escopo Inicial (v1)

1. **Json por OS + Json consolidado** gravados em `<pasta-mãe>/.BancoDados/`.
2. Cada OS tem **seu próprio JSON independente** + **um JSON consolidado**.
3. O banco inicialmente mostra, por OS:
   - quais **pastas padrão do projeto** já estão criadas (somente as do padrão,
     **não** as fora de padrão);
   - quais **pastas de ano** já estão criadas (dentro de
     `03_ENVIO_DE_DOCUMENTOS`).
4. **Atualização do JSON apenas** quando o usuário clica em **ATUALIZAR DADOS**
   (abrir a ferramenta não reescreve nada — apenas lê o consolidado existente).
5. **Backup diário** do `.BancoDados` em pasta configurável (default
   `%USERPROFILE%\Documents\Backups\VerraData`), no formato
   `<YYYYMMDDHHMMSS>.BancoDados.zip`, no máximo **1 vez por dia**.
6. O backup é disparado **ao iniciar** esta ferramenta **OU** ao iniciar o
   Gerenciador de Estrutura (código de backup **compartilhado**).
7. Estrutura **modular** com espaço para evolução (arquivos prontos, relatórios,
   integrações), **sem exageros**.

### Fora do escopo da v1 (evolução futura)
- Arquivos/documentos prontos por OS.
- Leitura/edição dos dados de negócio (faturamento, talhões, etc.).
- Sincronização em nuvem / banco externo (SQLite etc.).
- Restauração de backup (apenas geração nesta versão).

## 3. Decisões de Design (confirmar antes de codar)

| # | Decisão | Recomendação (default) | Alternativa |
|---|---------|------------------------|-------------|
| D1 | **Formato do backup** | **ZIP** via `zipfile` (stdlib, zero dependência) | RAR exigiria WinRAR/`unrar` + lib extra (`rarfile`) — **evitar** (Contrato 8) |
| D2 | **Pasta-mãe** | **Fonte única = preferência do `ProjectStructure`** (`mother_folder`). A ferramenta lê e exibe **somente leitura** (é "a mesma pasta-mãe do outro plugin") | Ter `mother_folder` própria, inicializada a partir da do ProjectStructure |
| D3 | **Pasta de backup** | Preferência própria na seção `ProjectDatabase` (`backup_dir`); default = `Path.home()/"Documents"/"Backups"/"VerraData"` (portátil, sem usuário embutido) | Guardar em `ToolKey.SYSTEM` |
| D4 | **BaseUtil vs módulo** | Utils compartilhadas como **classe herdando `BaseUtil`** (SKILL_UTILS), com `tool_key` nos métodos públicos | Funções de módulo (como o scanner atual) |
| D5 | **Backup ao atualizar** | Manter conforme spec: **somente ao iniciar** as ferramentas | Também disparar após "Atualizar dados" |

> ⚠️ Se D1–D5 não forem confirmados, seguir as recomendações.

---

## 4. Arquitetura & Estrutura de Arquivos

A ferramenta é dividida em **3 camadas**: UI (plugin), lógica (service) e
persistência (store). O que é **compartilhado** entre ferramentas vai para
`utils/` (Contrato 7 — um plugin nunca importa outro plugin).

```
utils/
├── ProjectStructureUtil.py      ← NOVO  (constantes + descoberta compartilhada)
└── ProjectDatabaseBackup.py     ← NOVO  (backup diário ZIP, reutilizável)

plugins/project_database_manager/            ← NOVO pacote (CATEGORIA CENTRAL)
├── __init__.py
├── ProjectDatabasePlugin.py     ← UI (herda BasePlugin) + cards + árvore
├── ProjectDatabaseService.py    ← lógica pura: varre pasta-mãe e monta os dados
└── ProjectDatabaseStore.py      ← leitura/escrita dos JSONs em .BancoDados

plugins/project_structure_manager/
├── ProjectStructureScanner.py   ← ALTERADO (passa a usar utils.ProjectStructureUtil)
├── ProjectStructurePlugin.py     ← ALTERADO (dispara backup no início)
└── FolderOperations.py          ← (sem mudança nesta v1)

core/enum/ToolKey.py             ← ALTERADO (+ PROJECT_DATABASE)
core/config/ToolRegistry.py      ← ALTERADO (+ registro da ferramenta)
docs/skills/SKILL_PROJECT.md     ← ALTERADO (documenta a nova ferramenta)  (Contrato 12)
docs/data/changelog.txt          ← ALTERADO (entrada da versão)
```

### Responsabilidades

| Módulo | Responsabilidade | Não faz |
|--------|------------------|---------|
| `ProjectDatabasePlugin.py` | UI (cards, árvore, seletores), botão ATUALIZAR DADOS, load/save prefs, disparo do backup e da varredura assíncrona | Não fala com filesystem/JSON diretamente |
| `ProjectDatabaseService.py` | Descobrir OS, calcular pastas padrão criadas + anos criados, montar estruturas | Não toca em widgets Qt |
| `ProjectDatabaseStore.py` | Gravar/ler JSON por OS e consolidado, criar `.BancoDados` | Não decide regras de negócio |
| `utils/ProjectStructureUtil.py` | Constantes da estrutura (`DEFAULT_PROJECT_FOLDERS`, `DOCUMENT_YEARS_FOLDER`, `DEFAULT_YEARS`, `PROJECT_PREFIX`) + `discover_projects`, `is_year_folder`, `collect_created_data` | Sem UI |
| `utils/ProjectDatabaseBackup.py` | `ensure_daily_backup(...)` — cria `<ts>.BancoDados.zip` se ainda não houver backup do dia | Sem UI |

## 5. Reutilização de Código (mapa de dependências)

> Objetivo: **zero duplicação**. O que já existe é reutilizado; o que está em
> pacote de outro plugin é **promovido para `utils/`** antes de ser usado.

| Necessidade | Reutilizar de | Observação |
|-------------|---------------|------------|
| Base do plugin (logger, prefs, página, sinais de ciclo) | `plugins/BasePlugin.py` (`BasePlugin`) | `tool_key`, `title`, `buttons_config` |
| Botão **ATUALIZAR DADOS** no header | `buttons_config` do `BasePlugin` (Contrato 18) | Acesso via `self.page.buttons.set_enabled(...)` |
| Badge de status | `self.page.set_badge(self.page.RUNNING/PRONTA/ERROR/INFO)` | PluginPage |
| Cards de resumo | `resources/widgets/grid/GridCardView.py` | `set_card_value(i, j, texto)` |
| Árvore multicoluna | `resources/widgets/grid/GridTree.py` | `add_node`, `set_cell_text`, `clear_nodes` |
| Grupos/containers | `resources/widgets/GroupPainel.py`, `resources/widgets/grid/GridGroupPainel.py` | Idêntico ao ProjectStructure |
| Seletor de pasta | `resources/widgets/simple/SimpleSelector.py` | `browse_mode="directory"` |
| Diálogo de pasta | `utils/ExplorerUtils.py` (`select_directory`, `ensure_directory`) | Contrato 17 |
| Mensagens | `utils/MessageBox.py` (`show_info/warning/error/toast`) | Contrato 1 |
| Persistência JSON | `utils/JsonUtil.py` (`read_json/write_json`) | Formato indentado, `ensure_ascii=False` |
| Constantes/descoberta de projetos | `ProjectStructureScanner.discover_projects`, `DEFAULT_PROJECT_FOLDERS`, `DOCUMENT_YEARS_FOLDER`, `is_year_folder` | **Promovidos** para `utils/ProjectStructureUtil.py` |
| Padrão de worker assíncrono | `ProjectStructureScanner.ScanWorker` (`QRunnable` + `Signal`) | Mesmo padrão (barra central via `progress_update`) |
| Progresso central | `SignalManager.instance().progress_update` / `progress_reset` | Contrato 20 |
| Formatação datas/tamanho | `utils/FormatUtils.py` | Contrato 22 |
| Preferências | `self.preferences` (própria) + `Preferences.load_tool_prefs(ToolKey.PROJECT_STRUCTURE)` (pasta-mãe) | Contrato 4 |
| Projeto ativo (.mtl) | `utils/ProjectUtil.py` | Opcional: mostrar projeto atual |
| Logging | `self.logger` (LogUtils) / `BaseUtil._get_logger` | Contrato 3 |
| Chave de ferramenta em logs | `ToolKey.PROJECT_DATABASE.value` | Contrato 26 |

### 5.1 Passo de refatoração (adaptação obrigatória)

Para o Banco de Dados reutilizar a descoberta/estrutura **sem importar outro
plugin** (Contrato 7), extrair de `ProjectStructureScanner.py` para
`utils/ProjectStructureUtil.py`:

```
PROJECT_PREFIX, DEFAULT_PROJECT_FOLDERS, DOCUMENT_YEARS_FOLDER, DEFAULT_YEARS
discover_projects(mother)
is_year_folder(name)
collect_created_data(project)   ← NOVO adaptador para o banco
```

`ProjectStructureScanner.py` passa a **importar** desses símbolos
(`from utils.ProjectStructureUtil import ...`), mantendo a API pública
(re-exportando os nomes para não quebrar `ProjectStructurePlugin.py`).
Nenhuma mudança de comportamento.

---

## 6. Esquema dos JSONs (`.BancoDados`)

Pasta na raiz da pasta-mãe: `<pasta-mãe>/.BancoDados/`

### 6.1 JSON por OS — `.BancoDados/<nome_da_os>.json`

```json
{
  "os": "OS_2024_001_Cliente",
  "path": "C:/Users/.../VERRA_Farmer/OS_2024_001_Cliente",
  "folders": [
    "01_Acessos_Plataforma_IA_AGLIBS",
    "03_ENVIO_DE_DOCUMENTOS",
    "05_ASA",
    "10_VERRA"
  ],
  "years": ["2023", "2024"],
  "updated_at": "2026-10-05T17:15:36"
}
```

- `folders`: **apenas** as pastas padrão (`DEFAULT_PROJECT_FOLDERS`) que existem
  em disco (equivalentes ao status `CORRETA`). **Nunca** inclui pastas fora de
  padrão.
- `years`: **apenas** as pastas de ano (4 dígitos) existentes dentro de
  `03_ENVIO_DE_DOCUMENTOS`.
- `updated_at`: timestamp ISO local gerado no momento da atualização.

### 6.2 JSON consolidado — `.BancoDados/banco_dados.json`

```json
{
  "generated_at": "2026-10-05T17:15:36",
  "mother_folder": "C:/Users/.../VERRA_Farmer",
  "db_schema": 1,
  "total_projects": 12,
  "projects": [
    { "os": "OS_2024_001_Cliente", "path": "...", "folders": ["..."], "years": ["2024"], "updated_at": "..." }
  ]
}
```

- `db_schema`: versão do esquema (facilita evolução sem quebrar leitores).
- `projects[]`: os mesmos registros dos JSONs individuais (o consolidado é a
  agregação; o por-OS é a fonte por projeto).

> **Gravação atômica:** escrever em `<arquivo>.tmp` e depois `os.replace()` para
> evitar JSON corrompido em caso de queda. (Adaptar `JsonUtil` ou fazer no
> `ProjectDatabaseStore`.)

## 7. Estrutura de Backup Diário

### 7.1 Regra
- Pasta de destino: `<backup_dir>` (preferência própria; default
  `Path.home()/"Documents"/"Backups"/"VerraData"`).
- Origem: `<pasta-mãe>/.BancoDados`.
- Nome do arquivo: `<YYYYMMDDHHMMSS>.BancoDados.zip`
  (ex.: `20261005171536.BancoDados.zip`).
- **1 backup por dia**: se já existir `glob("<YYYYMMDD>*.BancoDados.zip")` na
  pasta de destino, **não** gerar de novo.
- Se a origem `.BancoDados` não existir, **não** fazer nada (log info).

### 7.2 API compartilhada — `utils/ProjectDatabaseBackup.py`

```python
class ProjectDatabaseBackup(BaseUtil):
    DB_FOLDER = ".BancoDados"
    DEFAULT_BACKUP_DIR = str(Path.home() / "Documents" / "Backups" / "VerraData")

    @staticmethod
    def ensure_daily_backup(
        mother_folder: str,
        backup_dir: str = "",
        label: str = "BancoDados",
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> Optional[str]:
        """Cria <backup>/<YYYYMMDDHHMMSS>.<label>.zip a partir de
        <mother>/.BancoDados. Retorna o caminho criado, ou None se já
        havia backup do dia / origem inexistente / falha."""
```

- Implementação com `zipfile.ZipFile(..., ZIP_DEFLATED)`, percorrendo
  `os.walk` da origem (guardando caminhos relativos).
- `backup_dir` vazio → usa `DEFAULT_BACKUP_DIR`; garante existência via
  `ExplorerUtils.ensure_directory`.
- A escolha por **ZIP** (D1) elimina dependências externas (Contrato 8).

### 7.3 Disparo do backup

```
ProjectDatabasePlugin._init_runtime()   → QTimer.singleShot(0, self._maybe_backup)
ProjectStructurePlugin._init_runtime()  → QTimer.singleShot(0, self._maybe_backup)
        │
        └─► utils.ProjectDatabaseBackup.ensure_daily_backup(
                mother_folder = <pasta-mãe resolvida>,
                backup_dir    = <preferência ProjectDatabase.backup_dir>,
                tool_key      = ToolKey.<TOOL>.value,
            )
```

> O `ProjectStructurePlugin` resolve a pasta-mãe da própria preferência
> (`mother_folder`) e o `backup_dir` da seção `ProjectDatabase`. Assim o
> backup é **compartilhado** sem que um plugin importe o outro (Contrato 7).

---

## 8. Fluxo de Dados

### 8.1 Ao abrir a ferramenta
```
abrir aba → load_prefs (backup_dir) + resolve pasta-mãe (ProjectStructure)
          → lê <pasta-mãe>/.BancoDados/banco_dados.json (se existir)  [SOMENTE LEITURA]
          → popula cards + árvore com os dados salvos
          → QTimer.singleShot(0, _maybe_backup)   ← backup diário
```
> Abrir a ferramenta **não** recalcula nem reescreve JSONs (requisito).

### 8.2 Ao clicar em ATUALIZAR DADOS
```
_on_refresh_clicked()
  → valida pasta-mãe (existe?)
  → badge RUNNING + botão desabilitado + progress_update(0)
  → worker (QRunnable) varre a pasta-mãe:
        discover_projects(mother)
        para cada OS: collect_created_data(project)  → folders[] + years[]
        progress_update por OS
  → ProjectDatabaseStore.grava:
        .BancoDados/<os>.json  (um por OS, independente)
        .BancoDados/banco_dados.json (consolidado)
  → atualiza cards (GridCardView) + árvore (GridTree)
  → badge PRONTA + botão habilitado + progress_reset
  → SignalManager.console_message + MessageBox.show_toast
  → save_prefs
```

## 9. UI (Ferramenta CENTRAL)

- **Título:** `Banco de Dados`
- **Botão (header via `buttons_config`):** `atualizar` → `ATUALIZAR DADOS`
  (type `primary`), desabilitado durante a varredura
  (`self.page.buttons.set_enabled("atualizar", False/True)`).
- **Grupo "Configurações"** (`GroupPainel`):
  - `Pasta-mãe:` → `SimpleSelector` **somente leitura** (valor vindo do
    ProjectStructure) — mostra o caminho atual (D2).
  - `Pasta de backup:` → `SimpleSelector` (`browse_mode="directory"`) —
    editável; persiste em `ProjectDatabase.backup_dir`.
- **Cards** (`GridCardView`, 4 por linha):
  - `Projetos` · `Pastas criadas` · `Anos criados` · `Última atualização`.
- **Árvore** (`GridTree`) — colunas:
  - `OS` (stretch) · `Pastas criadas` · `Anos` · `Caminho`.
  - Alternativa: raiz = OS, filhos = pastas/anos (agrupador "Anos").
- **Legenda/estado vazio:** se não houver `banco_dados.json`, mostrar INFO +
  mensagem "Sem dados. Clique em ATUALIZAR DADOS."

## 10. Fases de Implementação

### Fase 0 — Reuso/preparação
- [ ] Criar `utils/ProjectStructureUtil.py` (constantes + `discover_projects`,
      `is_year_folder`, `collect_created_data`), herdando `BaseUtil`.
- [ ] Refatorar `ProjectStructureScanner.py` para importar de
      `utils.ProjectStructureUtil` (re-exportar nomes públicos).
- [ ] Validar que `ProjectStructurePlugin` continua funcionando sem regressão.

### Fase 1 — Backup compartilhado
- [ ] Criar `utils/ProjectDatabaseBackup.py` (`ensure_daily_backup`, ZIP, 1x/dia).
- [ ] Ligar o backup no `ProjectStructurePlugin._init_runtime()` (via
      `QTimer.singleShot(0, ...)`), lendo `backup_dir` da seção `ProjectDatabase`.
- [ ] Logar: já existe backup do dia / backup criado / origem ausente.

### Fase 2 — Persistência (store)
- [ ] Criar `ProjectDatabaseStore.py`: `db_dir(mother)`, `save_os(data)`,
      `save_consolidated(data)`, `load_consolidated()`, gravação atômica.
- [ ] Usar `JsonUtil` para leitura/escrita; garantir `.BancoDados` via
      `ExplorerUtils.ensure_directory`.

### Fase 3 — Lógica (service + worker)
- [ ] Criar `ProjectDatabaseService.py`:
  - `build_project_db(project) -> dict` (≈ `collect_created_data`);
  - `build_database(mother, progress_cb) -> dict` (percorre todas as OS);
  - `ProjectDatabaseWorker(QRunnable)` com sinais `progress/finished/failed`
    (mesmo padrão do `ScanWorker`).

### Fase 4 — Plugin (UI)
- [ ] Criar `plugins/project_database_manager/__init__.py`.
- [ ] Criar `ProjectDatabasePlugin.py` (`BasePlugin`, CENTRAL, `buttons_config`).
- [ ] `_build_ui()`: grupos + cards + árvore.
- [ ] `load_prefs()`: resolve pasta-mãe (ProjectStructure) + `backup_dir`.
- [ ] `save_prefs()`: persiste `backup_dir`.
- [ ] `_on_refresh_clicked()`: varredura assíncrona + gravação + refresh UI.
- [ ] `_maybe_backup()`: chama `ProjectDatabaseBackup.ensure_daily_backup`.
- [ ] `closeEvent()`: encerrar worker/pool.

### Fase 5 — Registro e docs
- [ ] `core/enum/ToolKey.py`: `PROJECT_DATABASE = "ProjectDatabase"`.
- [ ] `core/config/ToolRegistry.py`: registrar `Tool` (lazy, CENTRAL, toolbar).
- [ ] Atualizar `docs/skills/SKILL_PROJECT.md` (nova ferramenta + backup).
- [ ] Atualizar `docs/data/changelog.txt`.

### Fase 6 — Validação
- [ ] `py_compile`/`ast.parse` em todos os arquivos novos/alterados.
- [ ] Executar o app real (`main.py`) e testar os cenários abaixo.

### Registro no `ToolRegistry` (Fase 5)

```python
ToolKey.PROJECT_DATABASE.value: Tool(
    name=ToolKey.PROJECT_DATABASE.value,
    title="Banco de Dados",
    widget_factory=_make_factory(
        "plugins.project_database_manager.ProjectDatabasePlugin",
        "ProjectDatabasePlugin",
    ),
    tooltip="Banco de dados (JSON) das pastas e anos criados por OS",
    tool_type=ToolType.FOLDER,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

---

## 11. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Varredura lenta com muitas OS | Worker assíncrono (`QRunnable`) + `progress_update`; nunca travar a UI |
| JSON corrompido em queda | Gravação atômica (`<arquivo>.tmp` + `os.replace`) |
| Backup repetido no mesmo dia | Checagem por `glob("<YYYYMMDD>*.BancoDados.zip")` antes de gerar |
| `.BancoDados` inexistente no 1º start | Backup apenas loga info e não falha; é criado no primeiro ATUALIZAR |
| Dependência externa para RAR | Usar **ZIP** (stdlib) — sem `rarfile`/WinRAR (Contrato 8) |
| Acoplamento entre plugins | Código compartilhado em `utils/` (Contratos 7 e 11); leitura de preferências via `Preferences`, nunca import de plugin |
| Preferência de pasta-mãe divergente | Fonte única = seção `ProjectStructure` (D2) |
| `_load_prefs` antes da UI existir | Usar `QTimer.singleShot(0, ...)` para carregar após o `__init__` do `BasePlugin` (padrão do `SaveProjectPlugin`) |
| Pasta-mãe não configurada | Badge INFO + mensagem orientando configurar no Gerenciador de Estrutura |

## 12. Conformidade com Contratos (checklist)

- [ ] **Contrato 1** — só `utils.MessageBox` (nada de `QMessageBox`).
- [ ] **Contrato 2** — todo `except` captura `as e` e loga.
- [ ] **Contrato 3** — logs via `LogUtils`/`BaseUtil._get_logger` (sem `print`).
- [ ] **Contrato 4** — `self.preferences` do `BasePlugin`; `load_prefs`/`save_prefs`.
- [ ] **Contrato 5** — registro lazy no `ToolRegistry` (sem import estático).
- [ ] **Contrato 6** — herda `BasePlugin`, implementa `load_prefs`/`save_prefs`.
- [ ] **Contrato 7** — **nenhum import entre plugins** (compartilhado em `utils/`).
- [ ] **Contrato 8** — nenhuma dependência nova (ZIP é stdlib).
- [ ] **Contratos 11/18** — widgets de `resources/widgets/` + `buttons_config`.
- [ ] **Contrato 17** — diálogos via `ExplorerUtils`.
- [ ] **Contrato 20** — progresso na ProgressBar central.
- [ ] **Contrato 22** — formatação via `FormatUtils`.
- [ ] **Contrato 25** — sem I/O vetorial/raster nesta v1.
- [ ] **Contrato 26** — `ToolKey.*.value` em logs.
- [ ] **Contrato 27** — validar com `ast.parse`/`py_compile`, nunca import de Qt no terminal.

## 13. Critérios de Conclusão (v1)

- A ferramenta abre como aba CENTRAL e exibe os dados salvos.
- **ATUALIZAR DADOS** grava corretamente `<pasta-mãe>/.BancoDados/<os>.json`
  (um por OS) + `banco_dados.json` (consolidado).
- O banco lista **apenas** as pastas **padrão** presentes e os **anos** presentes
  (nunca pastas fora de padrão).
- Abrir a ferramenta **não** reescreve JSONs.
- Backup diário é criado **no máximo 1x/dia** em `<backup_dir>`, com o nome
  `<YYYYMMDDHHMMSS>.BancoDados.zip`, disparado ao iniciar **esta ferramenta ou**
  o Gerenciador de Estrutura.
- `ProjectStructurePlugin` continua funcionando sem regressão após a refatoração.
- Docs (`SKILL_PROJECT.md`) e `changelog.txt` atualizados.
- Verificação de execução na aplicação real passa.

## 14. Evolução Futura (base preparada)

- **Arquivos prontos** por OS (templates armazenados em `.BancoDados/ready/`).
- Indicadores/relatórios por OS (aderência à estrutura, pendências).
- `db_schema` para migrações de formato.
- Restauração/exportação de backup.
- Integração com o projeto ativo (`.mtl` / `ProjectUtil`) e filtros avançados.

> A separação **UI / service / store** e o `db_schema` versionado garantem que
> novas capacidades sejam adicionadas sem reescrever a v1.

---

> **Plano gerado em:** 05/10/2026
> **Referências:** `SKILL_AGENT.md`, `SKILL_CREATE_TOOL.md`, `SKILL_PLUGIN_CONTRACT.md`,
> `SKILL_UTILS.md`, `SKILL_PREFERENCES.md`, `SKILL_PROJECT.md`,
> `docs/plans/PLAN_POINT_BOUNDARY_VALIDATOR.md`,
> `plugins/project_manager/SaveProjectPlugin.py`,
> `plugins/project_structure_manager/ProjectStructureScanner.py`,
> `plugins/project_structure_manager/ProjectStructurePlugin.py`,
> `utils/ProjectUtil.py`.




