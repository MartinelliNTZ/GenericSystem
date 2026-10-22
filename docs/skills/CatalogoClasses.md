# Catálogo de Classes — Aetheris ToolBox

## core/ — Núcleo do Sistema

### core/config/
| Classe | Descrição |
|---|---|
| `BootStrap` | Singleton que orquestra toda a inicialização da aplicação (ambiente, logging, QApplication, registro de ferramentas, MainWindow) |
| `LogUtils` | Logger que escreve eventos JSON por **canal**: o canal padrão (`main`) vai para `log/` e canais nomeados (ex: `database`) vão para subpastas próprias — ver SKILL_DATABASE.md |
| `LogCleanup` | Limpeza de logs antigos por canal, mantendo os N arquivos mais recentes (`run(max_files, channel)`) |
| `LogFilter` | Filtro customizado para o sistema de logging (formatação, nível, etc.) |
| `MenuManager` | Gerencia a construção da toolbar com grupos de ferramentas (ToolGroup) e emite sinais ao clicar em um botão |
| `ToolRegistry` | Registry singleton que armazena e gerencia todas as definições de ferramentas (Tool) do sistema |

### core/enum/
| Classe | Descrição |
|---|---|
| `ToolKey` | Enum com chaves padronizadas das ferramentas (HOME, CONSOLE, LOGVIEWER, FILE_MANAGER, ...) |
| `ToolType` | Enum com categorias visuais das ferramentas (SYSTEM, LAYOUTS, FOLDER, VECTOR, AGRICULTURE, RASTER, IMAGE, POINTS) |

### core/manager/
| Classe | Descrição |
|---|---|
| `SignalCatalog` | Catálogo que define todos os sinais do sistema como atributos de uma classe QObject |
| `SignalManager` | Singleton orquestrador de sinais, gerencia emissão e conexão de eventos globais entre componentes |

### core/model/
| Classe | Descrição |
|---|---|
| `BasePlugin` | Classe base para todos os plugins/ferramentas. Fornece logger automático, métodos load/save de preferências e emite sinais de tool_opened/tool_closed |
| `Tool` | Modelo de ferramenta com lazy loading: só instancia o widget QWidget sob demanda via factory |
| `BaseModel` | Modelo base do sistema, pai de todos os models (id, nome, descrição e auditoria de criação/modificação) |
| `Culture` | Modelo de cultura plantada em um talhão (ciclo, safra, área plantada e colheita) |
| `Field` | Modelo de talhão de uma fazenda, que possui várias culturas (Culture); a área do talhão permanece definida nele |
| `Farm` | Modelo de fazenda, que possui vários talhões (Field) |
| `SubOS` (REMOVIDO) | O sistema de SubOS foi eliminado: a OS é TEXTO e pode conter LETRA (ex.: `169A`), que é o que diferencia as OS de um mesmo projeto |
| `WorkOrder` | Modelo de ordem de serviço (OS): a OS é texto e pode conter letra; cliente/nome comercial/CNPJ ficam na própria OS |

### core/ui/
| Classe | Descrição |
|---|---|
| `MainWindow` | Janela principal do sistema (QMainWindow frameless). Contém AppBar, toolbar com ToolGroups, Workspace e ProgressBar global |
| `Workspace` | Área de trabalho com QTabBar + QStackedWidget. Gerencia abas (abrir, fechar, arrastar) com lazy loading por ferramenta |
| `hud_loader` | Utilitário para exibir HUD loading overlay durante operações longas |
| `HudCircularRingsLoader` | Widget de loading visual com anéis circulares animados |

### core/dialogs/
| Classe | Descrição |
|---|---|
| `LogDetailDialog` | Diálogo de detalhes de log, exibe informações completas de uma entrada de log |

### core/firebase/
| Classe | Descrição |
|---|---|
| `FirebaseConfig` | Leitura de credenciais/parâmetros do Firebase via Preferences ou variáveis de ambiente |
| `FirebaseAuthService` | Autenticação (login/logout/refresh de token) via REST do Firebase Auth |
| `FirebaseServiceAccountAuth` | Token OAuth2 via conta de serviço (Admin SDK) — dispensa Web API Key e login de usuário; cache + renovação automática |
| `FirebaseTokenProvider` | Resolve o token Bearer (conta de serviço primeiro; senão sessão de usuário) |
| `FirestoreService` | Operações REST no Cloud Firestore (`get_document`, `save_document`, `save_documents`, `list_documents`, `delete_document`) com conversão automática de tipos |
| `CloudDatabaseSync` | Espelha um diretório de JSONs (`.BancoDados`) ↔ coleção Firestore (`push`/`pull`) com metadados em `.cloud/meta.json` |
| `FirebaseStorageService` | Upload/download de arquivos no Firebase Storage |
| `FirebaseWorker` | Executor assíncrono (QThread) de operações Firebase |
| `FirebaseCredentialManager` | Persistência criptografada de credenciais (`config/.firebase_auth.enc`) |

---

## plugins/ — Ferramentas (Plugins)

### plugins/home/
| Classe | Descrição |
|---|---|
| `HomeTool` | Página inicial exibida ao abrir o software. Herda de BasePlugin, exibe boas-vindas e resumo das ferramentas |

### plugins/console/
| Classe | Descrição |
|---|---|
| `ConsoleTool` | Console interativo para execução de comandos e scripts |

### plugins/log_viewer/
| Classe | Descrição |
|---|---|
| `LogViewerTool` | Visualizador de logs do sistema com filtros e busca |

### plugins/project_structure_manager/
| Classe | Descrição |
|---|---|
| `ProjectStructurePlugin` | Gerenciador de Estrutura de Projetos (herda de BasePlugin). Árvore de projetos/pastas, cards de resumo, filtro, atualização automática via QFileSystemWatcher e ações de pasta; as pastas de ano do `03_ENVIO_DE_DOCUMENTOS` são criadas por diálogo de checkboxes e as subpastas de template de uma pasta de topo (ex: `14_RELATORIOS`) são validadas na árvore e criadas junto com a pasta; toda pasta com conteúdo em disco aparece expansível (subpastas/arquivos carregados sob demanda via `set_node_expandable`) |
| `ProjectStructureScanner` (módulo) | Descoberta de projetos, validação (recursiva, incluindo as pastas de ano, o template completo de documentos e o template de subpastas das pastas de topo via `scan_project_trees`) e estatísticas; `folder_has_items(path)` indica se uma pasta tem conteúdo (indicador de expansão); `StatisticsWorker` calcula em background |
| `FolderOperations` (módulo) | Renomeação e mesclagem de pastas + abertura no explorer; re-exporta a criação (delegada a `utils/ProjectStructureCreator`); `RenameFolderWorker` |
| `StructureSyncService` (módulo) | Conferência da estrutura ao abrir a ferramenta: scan + diff + changelog Word + gravação no banco; `StructureSyncWorker` executa em background |

### plugins/project_database_manager/
| Classe | Descrição |
|---|---|
| `ProjectDatabasePlugin` | Ferramenta CENTRAL do banco de dados: cards, árvore OS/Cliente/Pastas/Anos; ATUALIZAR DADOS (consulta Firebase + re-escaneia as OS existentes) e SINCRONIZAR NUVEM (pull) |
| `ProjectDatabaseService` (módulo) | **NÃO cria OS**: re-escaneia as pastas das OS existentes e atualiza `folders`/`years`; + `ProjectDatabaseWorker` |
| `CloudProjectDatabase` (core/firebase) | **CLASSE DE BANCO (Contrato 28)**: única porta de entrada dos registros de OS (Firestore: `load_orders`/`get_order`/`save_order`/`rebuild_consolidated`) + geração dos backups JSON |
| `ProjectDatabaseStore` (core/database) | Leitura/escrita atômica dos backups JSON em `<pasta-mãe>/.BancoDados` (`load_consolidated`, `load_project`) — usada só pela `CloudProjectDatabase` |
| `CloudStructureDatabase` (core/firebase) | Classe de banco dos snapshots da estrutura (`estrutura_projetos`, com `blob` gzip+base64) e do histórico de alterações (`estrutura_changelog`) no Firestore; `load_snapshots`, `save_snapshots`, `save_changes(changes, operator=...)` — grava também `detected_by`/`detected_by_email`/`machine`; `load_changes(limit, os_number="")` — últimas alterações (filtradas por OS quando informado) |

### plugins/os_tracker/
| Classe | Descrição |
|---|---|
| `OsTrackerPlugin` | Ferramenta CENTRAL de Acompanhamento de OS: seleciona a OS; os painéis são **Origem**, **Seleção**, **Dados Gerais**, **Atalhos** e **Últimas alterações da OS**; o painel **Dados Gerais** exibe TODOS os dados em um único `GridLabel` de **2 colunas**, na mesma formatação — OS, cliente, pastas criadas, anos criados e as infos de cada base do banco (**Feições/Área — Limites** e **Feições/Área — Zonas de manejo**); o painel **Atalhos** (`GridButtonPanel`) abre a **pasta da OS**, **um botão por link registrado** (`LIMITES`/`ZONAS DE MANEJO` — escondido quando a OS não tem o registro, abrindo a PASTA do arquivo) e o **changelog Word** da OS (`11_AGROROBOTICA/OS_<chave>_CHANGELOG.DOCX`); o painel **Últimas alterações da OS** traz o changelog da estrutura filtrado pela chave da OS, vindo do BANCO — não do Word; cria OS (chave obrigatória — TEXTO, pode conter letra) e adiciona pastas (checklist) — tudo via `CloudProjectDatabase`/`CloudStructureDatabase` |
| `OsTrackerService` (módulo) | Lê a base (Firebase) e as alterações de UMA OS (`load_changes(os_number)`, com `change_summary`/`change_when`); lê os dados de **`limites`/`zonas_manejo`** do registro da OS (`asset_info` e `asset_file_path` — caminho absoluto resolvido em cascata: **absoluto → relativo à pasta-mãe → relativo à pasta da OS**, cobrindo registros antigos/fora da pasta-mãe) e formata timestamps ISO (`format_when`, reusado por `change_when`); resolve os atalhos da OS (`project_folder` e `changelog_path` — `.DOCX` via `ProjectStructureChangelog.document_path`); cria OS (`create_order`) e adiciona pastas (`add_folders`, `ensure_project_folder`) |

### plugins/limites_db/
| Classe | Descrição |
|---|---|
| `LimitesPlugin` | Ferramenta CENTRAL com **dois modos**: **Limites** e **Zonas de Manejo** (GridRadio). Seleciona um vetor (SHP/GPKG/KML/KMZ/GeoJSON), mapeia os campos do modo ativo (talhão *no modo limites* / **zona** e **campo de manejo** *no modo zonas*, fazenda, OS, cliente, área informada; talhão e campo são opcionais nas zonas); preenche a **OS manual** pelo padrão do caminho de origem (`OS_<chave>` na pasta ou `P<chave>` no arquivo) quando identificado — valor digitado pelo usuário é preservado; VALIDAR (não grava), IMPORTAR (calcula a área e grava) e **ATUALIZAR** (procura os shapes que já existem nas pastas, pergunta se devem ser substituídos e troca as feições das OS do vetor); preferências são carregadas ao INICIAR (modo, vetor e valores manuais) — ao TROCAR o vetor o auto-preenchimento da OS pelo caminho manda sobre o valor das prefs (só o valor digitado é preservado) e o **mapeamento de campos nunca é persistido** (é recalculado a partir do vetor) |
| `LimitesService` (módulo) | Regras de negócio por modo (`MODE_SETTINGS`): normalização (`TALHÃO`/`ZONA`/`CAMPO`/`FAZENDA` em maiúsculas) e da **OS em TEXTO** (zeros e letra preservados — `039`, `169A`); área calculada em hectares (`AREA_HA`) + área informada (`AREA_INF`), divergência por tolerância (%), bloqueio de duplicidade pela `KEY` apenas no modo limites (`OS-FAZENDA-TALHÃO`, ex.: `169A-FAZ_X-P3`); no modo zonas o **CAMPO de manejo** é OPCIONAL (`FIELD_CAMPO`, campo mapeado ou valor manual) e, quando indicado, consta em todos os shapes gerados; **validação do vetor** (`validate_vector`/`vector_problems`) antes de qualquer gravação — shapefile completo (`.shp`/`.shx`/`.dbf`), CRS obrigatoriamente `EPSG:4326` (`DEFAULT_EPSG`), somente polígonos (`POLYGON_TYPES`), sem geometrias nulas/vazias e com `is_valid`, e vetor com pelo menos 1 feição; grava `limites.shp`/`<OS>_limites.shp` e `zonas_manejo.shp`/`<OS>_zonas_manejo.shp` (atômico), copia para `<pasta da OS>/08_LIMITES/TALHOES` ou `<pasta da OS>/13_ZONAS_DE_MANEJO` e registra `limites`/`zonas_manejo` no **registro da OS** via `CloudProjectDatabase` (o `file` gravado é **relativo à pasta-mãe** e vira **absoluto** quando o arquivo está fora dela — `_stored_file_path`); **`find_existing`** lista os shapes já existentes (completão, arquivo da OS na base e cópia no projeto) e, com `LimitesImportConfig.update=True`, a gravação **substitui** as feições das OS do lote (`_replace_and_write`, sem checagem de duplicidade) preservando as demais OS; workers `LimitesInspectWorker`, `LimitesImportWorker` e `LimitesExistingWorker` (QRunnable) |

---

## resources/ — Recursos Visuais

### resources/styles/
| Classe | Descrição |
|---|---|
| `Palette` | Paleta de cores com 6 níveis de profundidade (BG_DEEPEST → BG_SURFACE) + cores de acento ouro, sucesso, warning, perigo |
| `AppStyles` | Estilos QSS centralizados de todos os componentes, com métodos estáticos para botões, badges e logs HTML |
| `DarkCharcoalStyle` | Classe de compatibilidade legada com constantes e stylesheet global |

### resources/widgets/
| Classe | Descrição |
|---|---|
| `AppBar` | Barra superior com título da janela, toolbar de ações e botões de minimizar/maximizar/fechar (suporte a frameless) |
| `GroupDiv` | Container com título dourado e fundo escuro, suporta QVBoxLayout e QGridLayout |
| `SelectorGrid` | Grade de SimpleSelectors configurados por dicionário, suporta múltiplas colunas |
| `SimpleSelector` | Linha com label + QLineEdit + botão "..." para selecionar arquivo/pasta |
| `SimplePrimaryButton` | Botão primário com gradiente ouro (ações principais) |
| `SimpleSecondaryButton` | Botão secundário com fundo escuro e texto dourado |
| `SimpleDangerButton` | Botão de perigo com fundo vermelho escuro |
| `SimpleGhostButton` | Botão ghost (invisível, aparece no hover) |
| `SimpleRemoveButton` | Botão de remover com hover vermelho |
| `ToolGroup` | Grupo horizontal de ferramentas na toolbar, com botões de ícone + separador |
| `ToolSeparator` | Separador decorativo slim com fade dourado entre ToolGroups |
| `GridTree` | Árvore multicoluna genérica (indexada por chave) com cores por célula e widgets de ação por linha |
| `GridActionCell` | Container horizontal genérico para widgets de ação em uma célula de tabela/árvore |
| `GridButtonPanel` | Grade genérica de botões de ação configurados por dicionário (texto, estilo e tooltip) com sinal `clicked(key)` |
| `SimpleMenuButton` | Botão com popup de menu (dropdown) configurável por Dict |
| `CheckBoxSelectDialog` | Diálogo genérico de seleção múltipla por checkboxes (usa GridCheckBox), com `selected_keys` |
| `WorkspaceTab` | Aba customizada com fundo preto, canto superior direito arredondado e texto dourado centralizado |

### resources/
| Classe | Descrição |
|---|---|
| `IconManager` | Gerenciador de ícones do sistema; ícones default/por ferramenta (`get`, `get_tool_icon`), nativos do SO (`system_icon`) e tingidos (`folder_icon`/`colorized`) |

---

## utils/ — Utilitários

| Classe | Descrição |
|---|---|
| `ColorProvider` | Provedor de cores utilitário: níveis de log, tools, classes e pastas de estrutura (`folder_color`, `shade`) + paletas dinâmicas |
| `Preferences` | Gerenciador de preferências do usuário com persistência em `config/<APP_SLUG>_preferences.json` (`load_tool_prefs`, `save_tool_prefs` — merge —, `remove_tool_prefs` — remove chaves antigas —, `all_data`, `save_all`) |
| `StringUtils` | Fonte única da identidade da aplicação (`APP_NAME`, `APP_SLUG`, `APP_ID`) e catálogo de extensões |
| `ProjectStructureUtil` | **Fonte única da estrutura dos projetos (OS)**: o dicionário `PROJECT_STRUCTURE` descreve TODA a estrutura (pastas aninhadas, a pasta de anos e futuros arquivos base) — tipos de nó `None` / `{...}` / `"arquivo"` / `BaseFile(...)` / `Years(...)`. Os acessores `DEFAULT_PROJECT_FOLDERS`, `PROJECT_FOLDER_TEMPLATES`, `DOCUMENT_YEARS_FOLDER`, `DEFAULT_YEARS` e `DOCUMENT_TEMPLATE` são derivados dele. Reúne também a descoberta da chave da OS (`discover_projects`, `is_year_folder`, `extract_os`, `normalize_os`, `project_folder`, `collect_created_data`) |
| `ProjectStructureSnapshot` | Scanner recursivo (pastas + arquivos) das pastas `OS_*`; grava tamanho (`sizes`) e data de última modificação (`modified`) por arquivo; ignora `~$*`, o próprio changelog e pastas/arquivos internos (`.git`, `__pycache__`, `.venv`, `node_modules`, `desktop.ini`…). `encode`/`decode` compactam o snapshot para o documento Firestore (gzip+base64) |
| `ProjectStructureChangeDetector` | **Detecção isolada**: compara snapshots e classifica criados/removidos/modificados, `renamed_files`, `moved_files`, `folder_renames` e `folder_moves` (validação por árvore + tamanho; pares não ambíguos) |
| `ProjectStructureChangelog` | Cria/atualiza `<pasta da OS>/11_AGROROBOTICA/OS_<numero>_CHANGELOG.DOCX` (python-docx) com um bloco por execução contendo as pastas/arquivos criados, removidos e modificados + a linha `Conferido por:` (operador recebido em `operator`); na primeira detecção da OS grava só "Primeira inicialização" (`first_run`); blocos em ordem decrescente (mais recente no topo) |
| `ProjectStructureSnapshot` (ignore) | Fora do snapshot: temporários `~$*` e qualquer `11_AGROROBOTICA/*_CHANGELOG.DOCX` — o próprio documento nunca conta como criado/removido/modificado |

---

## main.py — Ponto de Entrada

| Função | Descrição |
|---|---|
| `main()` | Ponto de entrada da aplicação. Garante que a raiz do projeto está no sys.path e chama BootStrap().run() |