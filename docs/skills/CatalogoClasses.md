# Catálogo de Classes — Aetheris ToolBox

## core/ — Núcleo do Sistema

### core/config/
| Classe | Descrição |
|---|---|
| `BootStrap` | Singleton que orquestra toda a inicialização da aplicação (ambiente, logging, QApplication, registro de ferramentas, MainWindow) |
| `LogUtils` | Logger responsável por escrever mensagens JSON de execução e debug do software |
| `LogCleanup` | Gerencia limpeza de arquivos de log antigos, mantendo apenas os N mais recentes |
| `LogFilter` | Filtro customizado para o sistema de logging (formatação, nível, etc.) |
| `MenuManager` | Gerencia a construção da toolbar com grupos de ferramentas (ToolGroup) e emite sinais ao clicar em um botão |
| `ToolRegistry` | Registry singleton que armazena e gerencia todas as definições de ferramentas (Tool) do sistema |

### core/enum/
| Classe | Descrição |
|---|---|
| `ToolKey` | Enum com chaves padronizadas das ferramentas (HOME, CONSOLE, LOG_VIEWER, TENSORFLOW_CLASSIFIER) |
| `ToolType` | Enum com categorias visuais das ferramentas (SYSTEM, RASTER, VECTOR, CLASSIFIER) |

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

### plugins/tensorflow_classifier/
| Classe | Descrição |
|---|---|
| `ClassificationTool` | Ferramenta principal de classificação de imagens com TensorFlow |
| `ClassifierPipeline` | Pipeline completo de classificação (pré-processamento → extração → treino → avaliação → predição) |
| `DatasetSplitter` | Utilitário para divisão de datasets em treino/validação/teste |
| `Evaluator` | Avaliador de modelos treinados (métricas, matriz de confusão, relatórios) |
| `FeatureExtractor` | Extrator de características de imagens/raster para treinamento |
| `HardwareManager` | Gerenciador de detecção de hardware disponível (CPU/GPU) |
| `MainController` | Controlador principal que orquestra a lógica de negócio da classificação |
| `ModelFactory` | Fábrica de criação de modelos TensorFlow/Keras |
| `PipelineConfig` | Configuração e parâmetros do pipeline de classificação |
| `RasterPredictor` | Preditor para arquivos raster completos (GeoTIFF) |
| `RasterSource` | Fonte de dados raster para leitura e processamento de GeoTIFF |
| `ShapefileDataset` | Dataset a partir de shapefiles para classificação |
| `Trainer` | Treinador de modelos com callbacks e logging |
| `UIFieldSpecs` | Especificações dos campos da interface do classificador |

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
| `WorkspaceTab` | Aba customizada com fundo preto, canto superior direito arredondado e texto dourado centralizado |

### resources/
| Classe | Descrição |
|---|---|
| `IconManager` | Gerenciador de ícones do sistema, fornece ícones default e por ferramenta |

---

## utils/ — Utilitários

| Classe | Descrição |
|---|---|
| `ColorProvider` | Provedor de cores utilitário para geração de cores em gradientes e paletas dinâmicas |
| `Preferences` | Gerenciador de preferências do usuário com persistência em arquivo JSON |

---

## main.py — Ponto de Entrada

| Função | Descrição |
|---|---|
| `main()` | Ponto de entrada da aplicação. Garante que a raiz do projeto está no sys.path e chama BootStrap().run() |