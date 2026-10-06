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
| `SubOS` | Modelo de SubOS (subordem de serviço, ex.: A/B/C/D): nome de cliente, nome comercial, CNPJ e várias fazendas (Farm) |
| `WorkOrder` | Modelo de ordem de serviço (OS), com uma ou mais SubOS (SubOS) |

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
| `ProjectStructurePlugin` | Gerenciador de Estrutura de Projetos (herda de BasePlugin). Árvore de projetos/pastas, cards de resumo, filtro, atualização automática via QFileSystemWatcher e ações de pasta; as pastas de ano do `03_ENVIO_DE_DOCUMENTOS` são criadas por diálogo de checkboxes e as subpastas de template de uma pasta de topo (ex: `14_RELATORIO`) são validadas na árvore e criadas junto com a pasta; toda pasta com conteúdo em disco aparece expansível (subpastas/arquivos carregados sob demanda via `set_node_expandable`) |
| `ProjectStructureScanner` (módulo) | Descoberta de projetos, validação (recursiva, incluindo as pastas de ano, o template completo de documentos e o template de subpastas das pastas de topo via `scan_project_trees`) e estatísticas; `folder_has_items(path)` indica se uma pasta tem conteúdo (indicador de expansão); `StatisticsWorker` calcula em background |
| `FolderOperations` (módulo) | Criação, renomeação e mesclagem de pastas + templates (`create_template`, `create_document_year`, `create_project_folder`) + abertura no explorer; `RenameFolderWorker` |

### plugins/project_database_manager/
| Classe | Descrição |
|---|---|
| `ProjectDatabasePlugin` | Ferramenta CENTRAL do banco de dados: cards, árvore OS/Cliente/Pastas/Anos, ATUALIZAR DADOS (push para o Firestore) e SINCRONIZAR NUVEM (pull) |
| `ProjectDatabaseService` (módulo) | Monta os registros por OS + banco consolidado e o `ProjectDatabaseWorker` (varredura em background); preserva a chave `sub_os` já gravada |
| `ProjectDatabaseStore` (módulo) | Leitura/escrita atômica dos JSONs em `<pasta-mãe>/.BancoDados` (`load_consolidated`, `load_project`) |

### plugins/os_tracker/
| Classe | Descrição |
|---|---|
| `OsTrackerPlugin` | Ferramenta CENTRAL de Acompanhamento de OS: escolhe uma OS e exibe as SubOS (cliente, nome comercial e CNPJ) a partir do banco `.BancoDados` |
| `OsTrackerService` (módulo) | Lê os registros de OS do banco consolidado e monta os modelos `SubOS` (`load_orders`, `build_sub_os`, `order_label`) |

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
| `Preferences` | Gerenciador de preferências do usuário com persistência em `config/<APP_SLUG>_preferences.json` |
| `StringUtils` | Fonte única da identidade da aplicação (`APP_NAME`, `APP_SLUG`, `APP_ID`) e catálogo de extensões |

---

## main.py — Ponto de Entrada

| Função | Descrição |
|---|---|
| `main()` | Ponto de entrada da aplicação. Garante que a raiz do projeto está no sys.path e chama BootStrap().run() |