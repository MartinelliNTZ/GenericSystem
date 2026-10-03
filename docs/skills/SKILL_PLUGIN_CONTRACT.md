# 📜 Contratos do Sistema — Aetheris ToolBox

Contratos são regras imutáveis. Todo código produzido para o Aetheris ToolBox DEVE respeitar estas regras. Violações causam reject automático.

---

## 🔴 Contrato 1 — Mensagens ao Usuário

```
QMessageBox é PROIBIDO. Use MessageBox de utils.MessageBox.
```

`from PySide6.QtWidgets import QMessageBox` — proibido em todo o projeto.
Única exceção: `utils/MessageBox.py` (a própria implementação).

## 🔴 Contrato 2 — Tratamento de Exceções

```
Todo except DEVE capturar a exceção com 'as e' E logar.
```

```python
# ✅ Correto
except ValueError as e:
    logger.error("valor invalido", code="VAL_ERR", error=str(e))
```

```python
# ❌ Proibido
except:
    pass

# ❌ Proibido
except Exception:
    print("deu erro")
```

## 🔴 Contrato 3 — Logger

```
Use LogUtils (logger via BasePlugin ou LogUtils direto). Não use print().
```

Única exceção: fallbacks em `ExceptionHandler._python_excepthook` e `main.py` quando o sistema de log não está disponível (pré-startup).

## 🔴 Contrato 4 — Preferências

```
Não instancie Preferences manualmente. Use self.preferences.
```

O `BasePlugin` já fornece `self.preferences`. Ferramentas que não herdam de BasePlugin podem instanciar `Preferences` normalmente (como feito nos controllers).

## 🔴 Contrato 5 — Importação de Ferramentas

```
Sempre use ToolRegistry. Nunca importe plugins diretamente no core.
```

O carregamento dinâmico (Lazy Loading) é obrigatório. Plugins são registrados no `ToolRegistry` com caminho de módulo, não importados estaticamente.

## 🔴 Contrato 6 — Estrutura de Plugins

```
Plugin herda de BasePlugin, implementa load_prefs() e save_prefs().
```

Métodos `on_open()` e `on_close()` são opcionais. `load_prefs()` deve ser chamado no `__init__` após montar a UI.

## 🔴 Contrato 7 — Sinais

```
Use SignalManager para comunicação entre componentes. Não acople plugins diretamente.
```

Nunca um plugin deve conhecer ou importar outro plugin. Comunicação é via sinais do `SignalManager`.

## 🔴 Contrato 8 — Dependências Externas

```
Não adicione dependências novas sem registrar em requirements.txt.
```

Qualquer novo pip install DEVE ter o nome e versão adicionados ao `requirements.txt`.

## 🔴 Contrato 9 — Código Morto

```
Nenhum import, classe, função ou variável não utilizado.
```

Remove imports mortos antes de finalizar. Não deixe `print()`, comentários de debug ou código comentado.

## 🔴 Contrato 10 — Categorias de Ferramentas

```
CENTRAL    → abas no topo (CentralWorkspace)
LEFT_SIDE  → painel lateral esquerdo fixo
RIGHT_SIDE → painel lateral direito fixo
SIDE       → compatibilidade: tratado como RIGHT_SIDE
BOTH       → pode ir para CENTRAL ou qualquer SIDE
INSTANT    → auto-destrutiva (não fica em workspace)
```

Definido em `CategoryTool` e no registro do `ToolRegistry`. Siga o padrão das ferramentas existentes.
- `FileManager` = `LEFT_SIDE` (fixo na esquerda)
- `Console` = `RIGHT_SIDE` (fixo na direita)
- Demais ferramentas de painel lateral usam `LEFT_SIDE` ou `RIGHT_SIDE` conforme necessidade
- `BOTH` registra no right side por padrão, mas pode ser movido para o central ou left side

## 🔴 Contrato 11 — Widgets Reutilizáveis (Composição Obrigatória)

```
NUNCA importe de PySide6.QtWidgets diretamente.
Sempre verifique em resources/widgets/ se já existe um widget pronto.
Se não existir, CRIE o widget em resources/widgets/.
```

**Regras:**
- **Abstraia componentes compostos** — se você precisa de um label + caixa de texto + botão, provavelmente isso é UM widget composto, não 3 widgets isolados. Crie uma classe em `resources/widgets/` que empacote os 3.
- **Modifique widgets existentes** para adicionar funcionalidades, desde que mantenha compatibilidade retroativa. É preferível estender um widget existente a criar um novo similar.
- **Nunca** use `QHBoxLayout` / `QVBoxLayout` solto com widgets brutos do Qt para criar o mesmo padrão que já existe em `resources/widgets/`.
- **Prefira Dict a List** para dados de widgets (combos, grids, configs). Dict tem chave fixa e estável, permite semântica clara (chave = valor interno, texto = exibição) e é mais manutenível que List que perde significado do índice.
  ```python
  # ✅ Correto — Dict
  combo = SimpleComboBox(items={"console": "Console", "renamer": "Renomeador"})

  # ⚠️ Aceitável — List (perde semântica do valor interno)
  combo = SimpleComboBox(items=["Opção A", "Opção B"])
  ```

```python
# ✅ Correto — usa widget existente
from resources.widgets.SimpleSelector import SimpleSelector
selector = SimpleSelector("Imagem:", file_filter="*.tif")

# ✅ Correto — cria widget composto novo em resources/widgets/
# resources/widgets/MeuWidgetComposto.py
class MeuWidgetComposto(QWidget):
    def __init__(self, ...):
        # label + lineedit + botão encapsulados aqui
        ...

# ❌ Proibido — widget bruto do Qt sem verificar se já existe
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton
# montando manualmente toda vez que precisar

# ❌ Proibido — criar widget dentro do plugin sem abstrair
class MeuPlugin(BasePlugin):
    def _build_ui(self):
        layout = QVBoxLayout(self)
        row = QHBoxLayout()  # Isso deveria ser um SimpleSelector!
        row.addWidget(QLabel("Caminho:"))
        row.addWidget(QLineEdit())
        row.addWidget(QPushButton("..."))
```

## 🔴 Contrato 12 — Documentação Reflexiva

```
Toda modificação que altere funcionalidade ou exija novo contrato
DEVE atualizar a documentação correspondente.
```

**Regras:**
- Ao criar um novo widget em `resources/widgets/`, adicione-o à skill `docs/skills/widgets_skill.md`.
- Ao criar um novo contrato, adicione-o neste arquivo e referencie no `docs/ia/agent.md`.
- Ao modificar comportamento existente, verifique se as skills e contratos ainda refletem a realidade.
- Documentação desatualizada é considerada bug.

## 🔴 Contrato 13 — ToolRegistry é a Única Fonte de Configuração de Tools

```
ToolRegistry centraliza TODAS as ferramentas.
Nenhum outro módulo cria, configura ou modifica objetos Tool.
```

**Regras:**
- `ToolRegistry._TOOLS` contém a definição completa de cada ferramenta: nome, título, factory, tool_type, category, show_in_toolbar, menu_category, etc.
- A `MainWindow` recebe a tool list PRONTA de `ToolRegistry.get_all()` — não altera nem filtra.
- O `MenuManager` recebe a tool list de `ToolRegistry.get_all()` e filtra internamente quem vai para toolbar e quem vai para menu.
- Nenhum outro módulo pode instanciar `Tool()` diretamente ou modificar propriedades de uma tool registrada.

```python
# ✅ Correto — ToolRegistry define tudo
_TOOLS = {
    "Preferences": Tool(
        name="Preferences",
        widget_factory=_make_factory(...),
        show_in_toolbar=False,
        menu_category=MenuCategory.SYSTEM,
    ),
}

# ❌ Proibido — configurar tool fora do ToolRegistry
tool.show_in_toolbar = False  # em qualquer outro lugar
```

## 🔴 Contrato 14 — MenuManager Encapsula MenuBar + Toolbar

```
MenuManager é o ÚNICO responsável por instanciar e configurar
a MenuBar e a toolbar. A MainWindow apenas POSICIONA os widgets.
```

**Regras:**
- `MenuManager.build()` constrói tanto a `MenuBar` quanto a `toolbar_widget`.
- A `MainWindow` acessa `manager.menu_bar` e `manager.toolbar_widget` como propriedades prontas.
- Sinais de clique (toolbar e menu) convergem para um único sinal: `MenuManager.tool_activated`.
- Sinais de `sair_clicked` e `sobre_clicked` são propagados pelo `MenuManager`.
- A `MainWindow` NÃO importa `MenuBar` diretamente — só se comunica via `MenuManager`.

```python
# ✅ Correto — MainWindow usa MenuManager como caixa preta
manager = MenuManager()
manager.build()
manager.tool_activated.connect(self._on_tool_activated)
manager.sair_clicked.connect(self.close)
root_layout.addWidget(manager.menu_bar)
root_layout.addWidget(manager.toolbar_widget)

# ❌ Proibido — MainWindow manipular MenuBar ou toolbar diretamente
from resources.widgets.MenuBar import MenuBar  # não deve existir no ui_main
menu_bar = MenuBar()
menu_bar.add_menu_items(...)  # isso é responsabilidade do MenuManager
```

## 🔴 Contrato 15 — MenuCategory para Ferramentas de Menu

```
Ferramentas com menu_category definido aparecem no menu suspenso.
Ferramentas SEM menu_category não vão para o menu.
```

**Regras:**
- `menu_category` é definido no `ToolRegistry._TOOLS`, não em runtime.
- `MenuCategory.SYSTEM` → menu "Sistema"
- `MenuCategory.FILE` → menu "Arquivo" (futuro)
- `MenuCategory.HELP` → menu "Ajuda" (futuro)
- Ferramentas com `show_in_toolbar=False` + `menu_category=MenuCategory.SYSTEM` só aparecem no menu, nunca na toolbar.

## 🔴 Contrato 16 — WorkspaceManager Encapsula 3 Workspaces (Left | Central | Right)

```
WorkspaceManager é o ÚNICO responsável por gerenciar os workspaces.
A MainWindow não conhece CentralWorkspace nem SideWorkspace diretamente.
```

**Regras:**
- `WorkspaceManager` instancia o `QSplitter` com 3 painéis: `LeftSide | CentralWorkspace | RightSide`.
- `WorkspaceManager` registra cada tool no workspace correto:
  - `LEFT_SIDE` → left (ex: FileManager)
  - `RIGHT_SIDE` / `SIDE` (legado) → right (ex: Console)
  - `CENTRAL` → central (ex: Home, Renamer)
  - `BOTH` → registra no right por padrão, pode ser movido
- `WorkspaceManager` gerencia todo o redimensionamento e persistência dos SideWorkspaces (largura salva em sys_prefs).
- `WorkspaceManager` gerencia a movimentação de tools BOTH entre workspaces.
- A `MainWindow` expõe `left_workspace`, `central_workspace`, `right_workspace` (e `side_workspace` por compatibilidade).

```python
# ✅ Correto
self._workspace_manager = WorkspaceManager(tools)
root_layout.addWidget(self._workspace_manager, 1)

# ❌ Proibido — MainWindow importar ou manipular workspaces
from core.ui.CentralWorkspace import CentralWorkspace
self.central_workspace = CentralWorkspace()
self.central_workspace.register_tool(tool)
```

## 🔴 Contrato 17 — ExplorerUtils para Seleção de Arquivos/Pastas

```
ExplorerUtils é a ÚNICA classe que pode chamar QFileDialog.
Nenhum outro módulo pode importar ou usar QFileDialog.
```

**Regras:**
- Todas as operações de "abrir arquivo", "salvar arquivo", "selecionar pasta" DEVEM passar por `ExplorerUtils`.
- `ExplorerUtils` exporta: `open_file()`, `open_files()`, `save_file()`, `select_directory()`, `select_directories()`, `resolve_initial_dir()`.
- A exceção é o próprio `utils/ExplorerUtils.py` (implementação da classe).

```python
# ✅ Correto
from utils.ExplorerUtils import ExplorerUtils
path = ExplorerUtils.open_file("Abrir", filter="*.json", parent=self)

# ❌ Proibido — em qualquer lugar fora de ExplorerUtils
from PySide6.QtWidgets import QFileDialog
path, _ = QFileDialog.getOpenFileName(self, "Abrir", "", "*.json")
```

## 🔴 Contrato 18 — Padrão de UI: Título → ExecutionButtons

```
Todo plugin DEVE seguir a estrutura:

  Título → Separator → ExecutionButtons → (conteúdo do plugin)
```

NUNCA use `QHBoxLayout`, `QPushButton` bruto, `SimplePrimaryButton`/`SimpleSecondaryButton`/`SimpleDangerButton` individuais montados manualmente na seção de botões de ação. Use SEMPRE `ExecutionButtons` de `resources/widgets/ExecutionButtons.py`.

**Regras:**
- O `ExecutionButtons` já padroniza altura, font-size, padding e cursor para todos os botões.
- Botões do tipo `primary` recebem destaque extra (altura +4px, font-size 13px vs 11px).
- Botões do tipo `secondary`, `danger` e `ghost` têm altura e fonte uniformes (30px, 11px).
- `ExecutionButtons` gerencia automaticamente o stretch entre grupos (secundários à esquerda, primary/danger à direita).
- Nunca adicione `addStretch()` manual — o widget já faz isso.
- Use `buttons["chave"]` para acessar botões individualmente (mudar texto, habilitar/desabilitar).

```python
# ✅ Correto — ExecutionButtons gerencia tudo
from resources.widgets.ExecutionButtons import ExecutionButtons

self._btns = ExecutionButtons(self)
self._btns.setup({
    "salvar": {"text": "SALVAR", "callback": self._on_salvar, "type": "secondary"},
    "executar": {"text": "EXECUTAR", "callback": self._on_executar, "type": "primary"},
})
layout.addWidget(self._btns)

# ❌ Proibido — botões manuais com QHBoxLayout
from PySide6.QtWidgets import QHBoxLayout
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton
from resources.widgets.SimpleSecondaryButton import SimpleSecondaryButton

row = QHBoxLayout()
btn_sec = SimpleSecondaryButton("SALVAR")
btn_pri = SimplePrimaryButton("EXECUTAR")
row.addWidget(btn_sec)
row.addStretch()
row.addWidget(btn_pri)
layout.addLayout(row)
```

```python
# ✅ Correto — acessar botão por chave
self._btns["executar"].setText("PARAR")
self._btns.set_enabled("salvar", False)
self._btns.set_callback("executar", self._on_parar)

## 🔴 Contrato 19 — Importação de Estilos

```
Fora de resources/styles/, importe APENAS AppStyles.
Nunca importe BaseTheme, ThemeManager, temas concretos ou ct diretamente.
```

Widgets que precisam de cores para `paintEvent()` devem usar os métodos específicos
do AppStyles (ex: `AppStyles.vertical_tab_colors()`, `AppStyles.theme_colors()`).
Nunca importe `ct` ou `BaseTheme` fora de `resources/styles/`.

## 🔴 Contrato 20 — Progress Bar, HUD e Console

```
Plugins DEVEM usar SignalManager para progresso e mensagens ao usuário:
- `SignalManager.progress_update(float)` — atualiza a ProgressBar da `MainWindow` (0.0–100.0)
- `SignalManager.console_message(str)` — exibe mensagem no `ConsolePlugin`
```

Regras obrigatórias:
- **Nenhuma ferramenta deve criar uma barra de progresso interna** (`QProgressBar`) ou um visualizador de logs próprio; use os componentes centrais via sinais.
- Use `SignalManager.instance().progress_update.emit(valor)` para progresso e `SignalManager.instance().console_message.emit(texto)` para mensagens ao usuário.
- Use `self.logger.info/warning/error(...)` para logs estruturados (LogUtils).
- A `ProgressBar` existe na `MainWindow` e é a única barra oficial para percentuais.

HUDLoader:
- O `HUDLoader` é recomendado para operações longas e mais visíveis; controle-o via sinais (`hud_show`, `hud_update`, `hud_hide`).
- Diferentemente da ProgressBar, o uso do HUD é opcional quando apropriado, mas prefira o HUD central em vez de implementar indicadores locais.
- Consulte `docs/skills/SKILL_HUD_PROGRESS.md` para o fluxo completo de progresso (HUD + ProgressBar + QThread).

```python
# ✅ Correto
SignalManager.instance().progress_update.emit(50.0)
SignalManager.instance().console_message.emit("Processando arquivo X...")

# ❌ Proibido — criar ProgressBar no plugin
self.progress = QProgressBar()
self.main_layout.addWidget(self.progress)
```

## 🔴 Contrato 21 — JsonUtil para Criação de JSONs Temporários

```
Todo JSON temporário DEVE ser criado via JsonUtil.
Nunca crie arquivos JSON temporários manualmente com open()/json.dump().
```

**Regras:**
- `JsonUtil._get_temp_dir()` usa `ExplorerUtils.get_plugin_config_dir()` para diretório padronizado em `config/data/file_preview/temp/`
- `JsonUtil.create_temp_json(data)` → cria JSON com UUID único, retorna path
- `JsonUtil.read_json(path)` → lê JSON com tratamento de erros
- `JsonUtil.write_json(path, data)` → escreve JSON com indent=2
- `JsonUtil.update_json(path, updates)` → lê, mescla, salva
- `JsonUtil.cleanup_temp_json(path)` → remove arquivo com segurança

**Fluxo padrão:**
```python
json_path = JsonUtil.create_temp_json()
enriched = BasicExtractor.enrich_json(json_path, file_path)
# extrair campos de 'enriched'...
JsonUtil.cleanup_temp_json(json_path)
```

## 🔴 Contrato 22 — FormatUtils para Formatação de Dados

```
Toda formatação de data e tamanho DEVE usar FormatUtils.
Nunca formate datas ou tamanhos manualmente com strftime() ou aritmética.
```

**Regras:**
- `FormatUtils.format_size(bytes)` → string legível (B, KB, MB, GB)
- `FormatUtils.format_date(timestamp)` → `dd/mm/AAAA HH:MM:SS`
- BasicExtractor delega formatação para FormatUtils

## 🔴 Contrato 23 — Utilitários Compartilhados

```
Use as classes do pacote utils/ para funcionalidades transversais.
Não duplique lógica de diálogos, seleção de arquivos, JSON temporários, paths ou formatação em plugins.
```

**Regras:**
- `ExplorerUtils` é a única fonte de `QFileDialog`.
- `MessageBox` é a única fonte de `QMessageBox`.
- `JsonUtil` gerencia JSONs temporários; não use `open()`/`json.dump()` manualmente para esse propósito.
- `FormatUtils` formata datas e tamanhos; não crie utilitários de formatação separados.
- `ProjectUtil` gerencia arquivos `.mtl` e metadata de projeto.
- `DictManager` fornece catálogos padronizados de extensões e valores.
- `ColorProvider` fornece cores consistentes por nível, ferramenta e classe.
- Se precisar de nova funcionalidade compartilhada, crie o utilitário em `utils/` e documente a nova API.

## 🔴 Contrato 24 — SignalManager Exclusivo para Comunicação Entre Componentes

```
SignalManager é EXCLUSIVO para comunicação entre plugins, ferramentas e componentes do sistema.
NUNCA use SignalManager para mudanças internas de widgets (ex: checkbox state, line edit text).
```

**Regras:**
- Widgets reutilizáveis em `resources/widgets/` DEVEM usar `QObject.Signal` (PySide6 Signals) para notificar mudanças internas.
- `SignalManager` é para eventos de sistema: tool_opened, tool_closed, progress_update, console_message, app_startup, etc.
- Um widget não deve conhecer `SignalManager` — ele emite seus próprios `Signal()` e o plugin/ferramenta que o consome conecta ao `SignalManager` se necessário.
- Violação: widget que importa `SignalManager` para emitir mudanças locais.

```python
# ✅ Correto — widget usa Signal próprio
class MeuWidget(QWidget):
    changed = Signal(str)  # Signal PySide6, não SignalManager
    def _on_internal_change(self):
        self.changed.emit("novo valor")

# ❌ Proibido — widget usando SignalManager
from core.manager.SignalManager import SignalManager
class MeuWidget(QWidget):
    def _on_internal_change(self):
        SignalManager.instance().console_message.emit("mudou")  # errado aqui
```

## 🔴 Contrato 25 — I/O Vetorial/Raster via Utils Especializados

```
Toda leitura de dados vetoriais (.shp, .gpkg, .csv) DEVE usar VectorLayerSource.
Toda leitura de dados raster (.tif, .tiff) DEVE usar RasterLayerSource.
NUNCA implemente leitura de shapefile/geopackage/csv diretamente no plugin.
```

**Regras:**
- `utils/vector/VectorLayerSource` é a única classe que lê vetores.
- `utils/raster/RasterLayerSource` é a única classe que lê rasters.
- Ambas usam `LogUtils` e aceitam `tool_key: str = ToolKey.UNTRACEABLE.value`.
- Ambas convertem tipos numpy para tipos nativos Python.
- Plugins delegam a leitura para estas classes, nunca importam `geopandas` ou `rasterio` diretamente.

```python
# ✅ Correto
from utils.vector.VectorLayerSource import VectorLayerSource
data = VectorLayerSource.read(path, tool_key=self.tool_key)

# ❌ Proibido
import geopandas as gpd
gdf = gpd.read_file(path)
```

## 🔴 Contrato 26 — ToolKey no lugar de Strings Soltas para Logger

```
Ao passar tool_key para LogUtils ou classes de I/O, SEMPRE use ToolKey.XXX.value.
NUNCA use strings literais em logs.
```

```python
# ✅ Correto
VectorLayerSource.read(path, tool_key=ToolKey.MRK_SUBSTITUTOR.value)

# ❌ Proibido
VectorLayerSource.read(path, tool_key="MrkSubstitutor")
VectorLayerSource.read(path, tool_key="Untraceable")

## 🔴 Contrato 27 — Verificação de Código com PySide6

```
NUNCA execute python -c "from PySide6.QtWidgets import ..." ou
"from resources.widgets.X import Y" no terminal para verificar código.
O PySide6/Qt TRAVA ao importar widgets fora de um QApplication.
```

**O problema:** ao executar `python -c "from PySide6.QtWidgets import QTabBar"` ou qualquer import que dependa de widgets Qt, o Python tenta inicializar o **Qt platform plugin** (subsistema gráfico do Windows). Como o terminal não tem um `QApplication` rodando, o Qt entra em espera infinita e o terminal congela.

**Solução — Use `ast.parse` para verificação sintática:**
```powershell
python -c "import ast; ast.parse(open('arquivo.py', encoding='utf-8').read()); print('✓ OK')"
```

Isso lê o arquivo como texto e analisa a estrutura sintática sem executar nada. Para testes completos, execute o aplicativo real (`main.py`).

**Regras:**
- ✅ `ast.parse()` — seguro, rápido, não executa código
- ❌ `python -c "from resources.widgets.X import Y"` — **TRAVA** o terminal
- ❌ `python -c "from PySide6.QtWidgets import ..."` — **TRAVA** o terminal
- Apenas execute imports de widgets Qt dentro de uma aplicação rodando (`main.py`)
