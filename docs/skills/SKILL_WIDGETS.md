# Skill: Widgets Reutilizáveis (resources/widgets/)

Catálogo oficial de todos os widgets disponíveis em `resources/widgets/`. **Sempre consulte esta lista antes de criar UI nova.** Se o widget que você precisa não existe, crie-o em `resources/widgets/` e **adicione-o a esta lista** (Contrato 12).

> ⚠️ **Contrato 11**: NUNCA importe widgets brutos de `PySide6.QtWidgets` sem antes verificar se já existe um widget pronto aqui Mesmo verificando se nao existir vc deve criar um widget, nunca usar widgs padrao. Componentes compostos (label + campo + botão, etc.) DEVEM ser um único widget em `resources/widgets/`.

---

## 📋 Catálogo de Widgets

### `AppBar` — `app_bar.py`
Barra de título superior com:
- Ícone e título da janela
- Botões de minimizar, maximizar/restaurar, fechar (frameless)
- Suporte a arrasto da janela
- Área para toolbar de ações globais

```python
from resources.widgets.app_bar import AppBar
appbar = AppBar()
appbar.minimize_clicked.connect(self.showMinimized)
appbar.close_clicked.connect(self.close)
```

---

### `GroupPainel` — `GroupPainel.py`
⚠️ **NÃO INSTANCIÁVEL DIRETAMENTE** — Use `GridGroupPainel` de `resources/widgets/grid/GridGroupPainel.py` **mesmo para 1 único painel**.

```python
# ❌ NÃO USE — NÃO INSTANCIÁVEL
from resources.widgets.GroupPainel import GroupPainel
grupo = GroupPainel("Configurações")

# ✅ USE ISTO EM VEZ (sempre via GridGroupPainel)
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.GroupPainel import GroupPainel

grid = GridGroupPainel(GroupPainel("Configurações"))
main_layout.addWidget(grid)
```

> `GroupPainel` só deve ser instanciado **dentro de `GridGroupPainel`**. Para exibir labels, use `GridLabel` de `resources/widgets/grid/GridLabel.py`.

---

### `MenuBar` — `MenuBar.py`
Container da barra de menus. **Não contém lógica de negócio** — apenas exibe as abas (QMenu) construídas pelos MenuItems.

```python
from resources.widgets.MenuBar import MenuBar
from core.menus.FileMenuItem import FileMenuItem
from core.menus.SystemMenuItem import SystemMenuItem
from core.menus.HelpMenuItem import HelpMenuItem

bar = MenuBar()
bar.add_menu_item(FileMenuItem())
bar.add_menu_item(SystemMenuItem())
bar.add_menu_item(HelpMenuItem())
```

**Sinais:** `action_triggered(str)` — repassa o data da ação clicada.

> ⚠️ Consulte `docs/skills/menubar_skill.md` para a documentação completa do sistema de menus.

---


### `SelectorGrid` — `SelectorGrid.py` (DEPRECATED)
> ⚠️ **DEPRECATED** — Este widget está obsoleto. **Use `GridComplexSelector`** de `resources/widgets/complex/GridComplexSelector.py` em todas as novas ferramentas. O `GridComplexSelector` usa `ComplexSelector` internamente, que é mais flexível e suporta file/folder/files/folders com linking entre selectores, modo dinâmico (dynamic_parent) e output automático.

```python
# ❌ NÃO USE — DEPRECATED
from resources.widgets.SelectorGrid import SelectorGrid

# ✅ USE ISTO EM VEZ
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
```

---

### `GridSelector` — `grid/GridSelector.py` (DEPRECATED)
> ⚠️ **DEPRECATED** — Este widget está obsoleto. **Use `GridComplexSelector`** de `resources/widgets/complex/GridComplexSelector.py` em todas as novas ferramentas. 
>
> ```python
> # ❌ NÃO USE — DEPRECATED
> from resources.widgets.grid.GridSelector import GridSelector
> 
> # ✅ USE ISTO EM VEZ (via grid)
> from resources.widgets.complex.GridComplexSelector import GridComplexSelector
> ```

---



### `SimpleSelector` — `SimpleSelector.py` (DEPRECATED)
> ⚠️ **DEPRECATED** — Este widget está obsoleto. **Use `GridComplexSelector`** de `resources/widgets/complex/GridComplexSelector.py` em todas as novas ferramentas. `SimpleSelector` só deve ser usado internamente pelo grid — nunca diretamente por plugins.
>
> ```python
> # ❌ NÃO USE — DEPRECATED
> from resources.widgets.simple.SimpleSelector import SimpleSelector
> 
> # ✅ USE ISTO EM VEZ (via grid)
> from resources.widgets.complex.GridComplexSelector import GridComplexSelector
> ```

---

### `SimplePrimaryButton` — `SimplePrimaryButton.py`
Botão principal com gradiente ouro. Ações principais (executar pipeline, confirmar).

```python
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton
btn = SimplePrimaryButton("EXECUTAR")
btn.clicked.connect(self._on_executar)
```

---

### `SimpleSecondaryButton` — `SimpleSecondaryButton.py`
Botão secundário, fundo escuro e texto dourado. Ações auxiliares (salvar config, carregar).

```python
from resources.widgets.SimpleSecondaryButton import SimpleSecondaryButton
btn = SimpleSecondaryButton("Salvar Config")
```

---

### `SimpleLabel` — `SimpleLabel.py`
⚠️ **NÃO INSTANCIÁVEL DIRETAMENTE** — Use `GridLabel` de `resources/widgets/grid/GridLabel.py` para exibir qualquer label.

```python
# ❌ NÃO USE — NÃO INSTANCIÁVEL
from resources.widgets.SimpleLabel import SimpleLabel
label = SimpleLabel("Pressione ESC para cancelar")

# ✅ USE ISTO EM VEZ (sempre via GridLabel)
from resources.widgets.grid.GridLabel import GridLabel

grid = GridLabel({"hint": {"label": "Dica", "value": "Pressione ESC para cancelar"}})
```

> `SimpleLabel` só deve ser usado **internamente** por outros widgets.

---

### `SimpleDangerButton` — `SimpleDangerButton.py`
Botão de perigo (fundo vermelho). Ações destrutivas (cancelar, excluir).

```python
from resources.widgets.SimpleDangerButton import SimpleDangerButton
btn = SimpleDangerButton("CANCELAR")
```

---

### `SimpleGhostButton` — `SimpleGhostButton.py`
Botão ghost (invisível, aparece no hover). Ações sutis (adicionar item).

```python
from resources.widgets.SimpleGhostButton import SimpleGhostButton
btn = SimpleGhostButton("+ Adicionar")
```

---

### `SimpleRemoveButton` — `SimpleRemoveButton.py`
Botão de remover com hover vermelho. Remover linhas de tabela, itens de lista.

```python
from resources.widgets.SimpleRemoveButton import SimpleRemoveButton
btn = SimpleRemoveButton("Remover")
```

---

### `ToolbarButton` — `buttons/ToolbarButton.py`
Botão de ícone individual para a toolbar principal. Herda de `QToolButton` e configura automaticamente ícone, tooltip, tamanho e estilo a partir do objeto `Tool` e dos tokens visuais do tema ativo.

Cada `ToolbarButton` emite `tool_clicked(str)` com o nome da ferramenta ao ser clicado.

```python
from resources.widgets.buttons.ToolbarButton import ToolbarButton

btn = ToolbarButton(tool)
btn.tool_clicked.connect(self._on_tool_activated)
btn.tool        # objeto Tool
btn.tool_name   # tool.name
```

---

### `ToolGroup` — `ToolGroup.py`
Grupo horizontal de botões de ferramentas na toolbar principal. Cria instâncias de `ToolbarButton` para cada ferramenta de uma categoria.

```python
from resources.widgets.ToolGroup import ToolGroup
group = ToolGroup(tool_type=ToolType.RASTER, tools=lista_de_tools)
group.tool_clicked.connect(self._on_tool_activated)
```

---

### `ToolSeparator` — `ToolSeparator.py`
Separador decorativo com gradiente dourado. Separa grupos de ferramentas na toolbar.

```python
from resources.widgets.ToolSeparator import ToolSeparator
separator = ToolSeparator(orientation="vertical")  # ou "horizontal"
```

---

### `VerticalTab` — `VerticalTab.py`
Aba vertical estilo Civil 3D. Texto rotacionado 90°, usada no SideWorkspace.

```python
from resources.widgets.VerticalTab import VerticalTab
tab = VerticalTab(title="Ferramentas", tooltip="Painel lateral")
tab.clicked.connect(self._on_tab_clicked)
tab.selected = True
```

---

### `WorkspaceTab` — `WorkspaceTab.py`
Aba customizada para o CentralWorkspace (abas horizontais no topo). A estilização visual vem do QSS em `styles.py`.

```python
from resources.widgets.WorkspaceTab import WorkspaceTab
tab = WorkspaceTab(title="Console", tooltip="Console do sistema")
```

---

### `MouseButtonCapture` — `MouseButtonCapture.py`
Campo de captura de botão do mouse com label opcional encapsulado. Ao clicar, entra em modo de escuta e o próximo clique do mouse é capturado (Left, Right, Middle, X1, X2). Usa `pynput.mouse.Listener` internamente para capturar o clique fora do widget.

Se ``label`` for informado, cria automaticamente um QFormLayout com o label + campo — eliminando a necessidade de criar layouts externos no plugin.

```python
from resources.widgets.MouseButtonCapture import MouseButtonCapture

# Sem label
capture = MouseButtonCapture(default_button="left")
capture.buttonChanged.connect(self._on_button_changed)
captured = capture.captured_button()  # "left", "right", "middle", "x1", "x2"
capture.set_captured_button("right")  # define programaticamente

# Com label encapsulado (elimina QFormLayout no plugin)
capture = MouseButtonCapture(default_button="left", label="Botão do mouse:")
```

**Comportamento:**
- Exibe nome amigável (Left (Esquerdo), Right (Direito), Middle (Meio), X1 (Botão lateral), X2 (Botão lateral))
- Valor interno é compatível com `pyautogui.click(button=...)` e com o enum `MouseButton`
- Ao clicar, entra em modo de escuta
- Clique do mouse fora do widget → captura o botão
- Perde o foco → sai do modo escuta
- Tab → sai do modo escuta sem capturar

**Parâmetros:**
- `label: str | None` — se informado, encapsula o campo em um QFormLayout com o label

---

### `HotkeyCaptureLine` — `HotkeyCaptureLine.py`
Campo de captura de teclas com label opcional encapsulado. Ao clicar, entra em modo de escuta e a próxima tecla pressionada é capturada (F1, ESC, DEL, ENTER, etc.). Ideal para configuração de atalhos de teclado.

Se ``label`` for informado, cria automaticamente um QFormLayout com o label + campo — eliminando a necessidade de criar layouts externos no plugin.

```python
from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine

# Sem label (comportamento original)
capture = HotkeyCaptureLine(default_key="f")
capture.keyChanged.connect(self._on_key_changed)
captured = capture.captured_key()  # "f", "f1", "esc", "del", etc.
capture.set_captured_key("f1")     # define programaticamente

# Com label encapsulado (elimina QFormLayout no plugin)
capture = HotkeyCaptureLine(default_key="f", label="Tecla gatilho:")
```

**Comportamento:**
- Exibe nome amigável (F1, ESC, DEL, ↑, etc.)
- Valor interno é compatível com a biblioteca `keyboard`
- Perde o foco → sai do modo escuta
- Tab → sai do modo escuta sem capturar

**Parâmetros:**
- `label: str | None` — se informado, encapsula o campo em um QFormLayout com o label

---

### `GridCheckBox` — `GridCheckBox.py`
Grade rolável de checkboxes organizados em colunas configuráveis. Cada checkbox tem label e tooltip definidos por dicionário.

```python
from resources.widgets.GridCheckBox import GridCheckBox

config = {
    ".txt": {"label": ".txt", "description": "Texto puro", "default": True},
    ".py":  {"label": ".py",  "description": "Python", "default": False},
}

grid = GridCheckBox(config, num_columns=4)
checked = grid.checked      # { ".txt": True }
unchecked = grid.unchecked  # { ".py": False }
all_states = grid.all       # { ".txt": True, ".py": False }
grid.set_all(all_states)    # restaura estados
grid.changed.connect(self._on_ext_changed)
```

---

### `ExecutionButtons` — `ExecutionButtons.py`
Container horizontal de botões de ação com suporte a múltiplos botões secundários à esquerda e primários/de perigo à direita, com stretch automático entre os grupos.

Cada botão é configurado por um dicionário com chave única, permitindo acesso direto via `buttons["chave"]`.

```python
from resources.widgets.ExecutionButtons import ExecutionButtons

buttons = ExecutionButtons(self, {
    "salvar": {
        "text": "SALVAR CONFIG",
        "callback": self._on_salvar,
        "type": "secondary",
        "description": "Salva configuração em disco",
    },
    "preview": {
        "text": "PRÉ-VISUALIZAR",
        "callback": self._on_preview,
        "type": "secondary",
    },
    "executar": {
        "text": "EXECUTAR",
        "callback": self._on_executar,
        "type": "primary",
        "description": "Inicia o pipeline",
    },
    "cancelar": {
        "text": "CANCELAR",
        "callback": self._on_cancelar,
        "type": "danger",
    },
})

# Acessa botão pela chave do config
buttons["executar"].setEnabled(False)
buttons["executar"].setText("PARAR")

# Métodos auxiliares
buttons.set_callback("executar", self._on_parar)
buttons.set_visible("cancelar", True)
buttons.set_enabled("salvar", False)
buttons.set_all_enabled(False)
```

**Tipos suportados:** `primary`, `secondary`, `danger`, `ghost`

**Sinais/Conexões:**
- Cada botão tem `clicked.connect(callback)` automaticamente pelo config
- Callback pode ser alterado em runtime via `set_callback(key, callable)`

**Chaves disponíveis:**
- `buttons.keys()` — lista de chaves
- `"chave" in buttons` — verifica existência
- `buttons.get("chave")` — retorna botão ou None

---

### `GridDoubleSpinBox` — `GridDoubleSpinBox.py`
Grade rolável de campos numéricos (QDoubleSpinBox/QSpinBox) configurados por dicionário. Agrupa múltiplos campos em grid, com label, description, sufixo/prefixo.

```python
from resources.widgets.GridDoubleSpinBox import GridDoubleSpinBox

config = {
    "intervalo": {
        "label": "Intervalo (s)",
        "description": "Tempo entre execuções",
        "decimal": 1,
        "default": 1.0,
        "min": 0.0,
        "max": 999.0,
        "step": 0.1,
        "suffix": "s",
    },
    "repeticoes": {
        "label": "Repetições",
        "decimal": 0,       # 0 = inteiro (QSpinBox)
        "default": 3,
        "min": 1,
        "max": 9999,
    },
}

grid = GridDoubleSpinBox(config)
grid.values           # {"intervalo": 1.0, "repeticoes": 3}
grid.get("intervalo") # 1.0
grid.set("repeticoes", 5)
grid.set_values({"intervalo": 2.5})
grid.changed.connect(self._on_value_changed)
```

**Sinais:**
- `changed(key, value)` — emitido quando qualquer campo muda

**Decimais:**
- `decimal=0` → cria `QSpinBox` (inteiro)
- `decimal>0` → cria `QDoubleSpinBox` com N casas decimais

**Métodos:**
- `set_enabled(key, enabled)` — habilita/desabilita um campo específico

---

### `GridSlider` — `grid/GridSlider.py`
Grade de sliders horizontais genéricos com label e valor numérico. Widget reutilizável — qualquer plugin que precisar de um valor numérico ajustável via slider pode usá-lo.

Configuração via dicionário com suporte a label, default, min, max, step, suffix e description.

```python
from resources.widgets.grid.GridSlider import GridSlider

slider = GridSlider({
    "quality": {
        "label": "Qualidade:",
        "default": 95,
        "min": 1,
        "max": 100,
        "step": 1,
        "suffix": "%",
        "description": "Qualidade para formatos lossy",
    },
})
slider.values          # {"quality": 95}
slider.get("quality")  # 95
slider.set("quality", 80)
slider.set_on_changed("quality", self._on_quality_changed)
slider.set_enabled("quality", False)
```

**API pública (callbacks, não Signals):**
- `values` → dict com valores atuais
- `get(key)` → valor de um campo
- `set(key, value, block_callbacks=False)` → define valor programaticamente
- `set_on_changed(key, callback)` → callback recebe `(key, value)` quando o slider muda
- `set_enabled(key, enabled)` → habilita/desabilita
- `set_values(values, block_callbacks=True)` → define múltiplos valores

**Parâmetros do config:**
| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `label` | str | — | Texto do label |
| `default` | int | 50 | Valor inicial |
| `min` | int | 0 | Valor mínimo |
| `max` | int | 100 | Valor máximo |
| `step` | int | 1 | Incremento |
| `suffix` | str | "" | Sufixo (ex: "%", "px") |
| `description` | str | "" | Tooltip |

---

### `GridLabel` — `GridLabel.py`
Grade de labels informativos exibindo pares "label: valor" com estilo monospace. Suporta múltiplas colunas e valores clicáveis (links). Ideal para exibir metadados e propriedades.

⚠️ **Este é o widget PADRÃO para exibir qualquer label no sistema.** Use sempre este widget em vez de `SimpleLabel`.

```python
from resources.widgets.grid.GridLabel import GridLabel

config = {
    "name": {
        "label": "Nome",
        "value": "—",
        "description": "Nome do arquivo",      # opcional
    },
    "size": {
        "label": "Tamanho",
        "value": "—",
    },
    "path": {
        "label": "Caminho",
        "value": "—",
        "link": True,                           # link clicável
    },
}

grid = GridLabel(config, columns=1)
grid.values              # {"name": "—", "size": "—", "path": "—"}
grid.get("name")         # "—"
grid.set("name", "arquivo.txt")
grid.set("path", "arquivo.txt", url="c:/pasta/arquivo.txt")
grid.set_values({
    "name": "arquivo.txt",
    "size": "1.2 KB",
    "path": ("arquivo.txt", "c:/pasta/arquivo.txt"),  # (texto, url)
})
grid.link_clicked.connect(self._on_link_clicked)
```

**Sinais:**
- `link_clicked(key, value)` — emitido quando um link é clicado

**Parâmetros:**
- `config: Dict[str, Dict]` — cada chave tem: `label`, `value`, `description` (opcional), `link` (opcional, bool)
- `columns: int = 1` — número de colunas

---

### `GridLineEdit` — `GridLineEdit.py`
Grade rolável de campos de texto (QLineEdit) configurados por dicionário. Suporta placeholder, valor padrão, tooltip e callback.

```python
from resources.widgets.GridLineEdit import GridLineEdit

grid = GridLineEdit({
    "valor": {
        "label": "Valor",
        "description": "Texto a ser digitado",
        "default": "texto padrão",
        "placeholder": "Digite algo...",
    },
})
grid.values          # {"valor": "texto"}
grid.get("valor")    # "texto"
grid.set("valor", "novo texto")
grid.set_values({"valor": "outro"})
grid.changed.connect(self._on_value_changed)
```

---

### `HotkeySequenceCapture` — `HotkeySequenceCapture.py`
Captura uma sequência de teclas/atalhos. Cada tecla é adicionada a uma lista com botões de remover. Ideal para configurar macros de teclado multi-tecla.

```python
from resources.widgets.HotkeySequenceCapture import HotkeySequenceCapture

capture = HotkeySequenceCapture(title="Sequência de Teclas:")
capture.sequenceChanged.connect(self._on_seq_changed)
sequence = capture.captured_sequence()  # ["f1", "ctrl+c", "enter"]
capture.set_captured_sequence(["f", "enter", "del"])
capture.clear()
```

**Sinais:**
- `sequenceChanged(list)` — emitido quando a sequência é alterada

**Parâmetros:**
- `title: str | None` — label opcional exibido antes do campo de captura

---

### `ImagePreviewPanel` — `ImagePreviewPanel.py`
Widget standalone de pré-visualização de imagem com **zoom** (roda do mouse), **arrasto lateral** (botão esquerdo), **reset** (duplo clique ou tecla `7`). Usa PIL para carregar e redimensionar com KeepAspectRatio.

```python
from resources.widgets.ImagePreviewPanel import ImagePreviewPanel

preview = ImagePreviewPanel(fixed_size=(480, 360))
preview.show_preview("c:/foto.png")
preview.clear_preview()
```

**Interação do mouse:**
- **Roda do mouse** — zoom in/out (fator 1.15x, limite 0.1x a 10x)
- **Botão esquerdo arrastar** — pan lateral quando zoom > 1x
- **Duplo clique esquerdo** — reseta zoom para 1.0 e pan para (0, 0)
- **Tecla `7`** — reseta zoom para 1.0 e pan para (0, 0)

**Parâmetros:**
- `fixed_size: tuple[int, int] | None = (480, 360)` — tamanho fixo; `None` expande ao espaço disponível

**API:**
- `show_preview(path)` — carrega e exibe imagem
- `clear_preview()` — limpa e restaura placeholder

---

### `TextPreviewWidget` — `TextPreviewWidget.py`
Widget de pré-visualização e edição de texto com suporte a múltiplos encodings. Possui botões **Copiar** e **Salvar** na barra superior. Usa `QPlainTextEdit` com fonte monospace (Consolas 10pt) e sem quebra de linha.

```python
from resources.widgets.TextPreviewWidget import TextPreviewWidget

text_widget = TextPreviewWidget()
text_widget.load_file("c:/arquivo.txt")
text_widget.load_text("conteúdo manual")
text_widget.clear()
text_widget.text          # str — conteúdo atual
text_widget.is_dirty      # bool — modificado desde último salvamento
```

**Métodos:**
- `load_file(path)` — carrega arquivo com detecção automática de encoding
- `load_text(text)` — carrega texto sem arquivo associado
- `clear()` — limpa conteúdo e reseta estado

**Propriedades:**
- `text` — retorna o texto atual
- `is_dirty` — True se houver modificações não salvas

---

### `PreviewPanel` — `PreviewPanel.py`
Painel de pré-visualização genérico. Envolve o conteúdo em um **`GroupPainel`** com título e delega o preview interno para o widget apropriado conforme a extensão do arquivo:

- **Imagens** → `ImagePreviewPanel` (zoom/pan)
- **Texto** → `TextPreviewWidget` (editor com Copiar/Salvar)
- Novos tipos podem ser adicionados via `register_handler()`

```python
from resources.widgets.PreviewPanel import PreviewPanel
from resources.widgets.PreviewPanel import register_handler

# Uso padrão — auto-detecta tipo
preview = PreviewPanel(title="Pré-Visualização")
preview.show_preview("c:/foto.png")
preview.clear_preview()

# Registrar handler customizado
register_handler(frozenset({".xyz"}), factory_fn)
```

**Parâmetros:**
- `title: str = "Pré-Visualização"` — título do `GroupPainel` container

**API:**
- `show_preview(path)` — carrega preview detectando tipo automaticamente
- `clear_preview()` — limpa e restaura placeholder

**Registro de handlers:**
```python
register_handler(
    extensions: frozenset[str],
    factory: Callable[[str], QWidget],
)
```

---

### `FileListView` — `FileListView.py`
Widget de lista com thumbnails, reordenação e drag & drop. Encapsula botões internos (Adicionar Arquivos, Adicionar Pasta, Remover Selecionados, Limpar Tudo, Mover Cima/Baixo). Aceita filtro por extensões (DictManager-style). Conexão automática com PreviewPanel via parâmetro `preview_widget`.

```python
from resources.widgets.FileListView import FileListView
from resources.widgets.PreviewPanel import PreviewPanel
from utils.DictManager import DictManager

preview = PreviewPanel()
view = FileListView(
    file_filter=DictManager.IMAGE_EXTENSIONS,
    accept_dirs=True,
    preview_widget=preview,  # conexão automática
)

# API pública
view.add_files(["c:/foto.png", "c:/pasta_com_fotos/"])
paths = view.get_ordered_paths()
view.remove_selected()
view.clear()
view.move_up()
view.move_down()
count = view.count()
selected = view.selected_path()

# Sinais
view.files_changed.connect(self._on_files_changed)
view.selection_changed.connect(self._on_selection_changed)
```

**Sinais:** `files_changed(int)`, `selection_changed(str)`

---

### `PreferenceItemGrid` — `PreferenceItemGrid.py`
Grade rolável de itens de preferência editáveis. Cada linha contém: título | valor (checkbox para bool, spin para float/int, line edit para texto) | botão lixeira.

Configurado por dicionário com suporte a tipos `bool`, `float`, `int`, `text`.

```python
from resources.widgets.PreferenceItemGrid import PreferenceItemGrid

config = {
    "search_text": {
        "type": "text",
        "default": "",
        "label": "Texto de Busca",
    },
    "max_results": {
        "type": "int",
        "default": 50,
        "label": "Máx. Resultados",
        "min": 1,
        "max": 1000,
    },
}

grid = PreferenceItemGrid(config, section="MinhaFerramenta")
grid.load_values()     # carregar do disco
grid.save_values()     # salvar no disco
grid.reset_values()    # restaurar defaults
grid.clear_all()       # limpar tudo
```

---
### `ReadOnlyTextBrowser` — `ReadOnlyTextBrowser.py`
QTextBrowser pré-configurado como read-only com métodos auxiliares para exibição de logs e texto formatado. Substitui a configuração manual de QTextBrowser em consoles e visualizadores.

```python
from resources.widgets.ReadOnlyTextBrowser import ReadOnlyTextBrowser

browser = ReadOnlyTextBrowser(
    placeholder="Mensagens aparecem aqui...",
    open_links=True,
)
browser.append_html("<b>texto</b>")
browser.clear_content()
browser.select_all()
browser.copy_all()
browser.to_plain_text()
```

**Métodos auxiliares:**
- `append_html(html)` — adiciona HTML ao final
- `clear_content()` — limpa o conteúdo
- `select_all()` — seleciona todo o texto
- `copy_all()` — copia texto puro para área de transferência
- `to_plain_text()` — retorna conteúdo como string

**Parâmetros do construtor:**
- `placeholder: str = ""` — texto de placeholder
- `open_links: bool = False` — permite clicar em links internos
- `open_external_links: bool = False` — permite abrir links externos

---

### `SectionPanel` — `SectionPanel.py`
Container leve com QVBoxLayout de margem zero e spacing configurável. Ideal para agrupar widgets que precisam ser mostrados/escondidos juntos (seções alternáveis por modo/guia).

```python
from resources.widgets.SectionPanel import SectionPanel

panel = SectionPanel(object_name="stack_text")
panel.section_layout.addWidget(QLabel("conteúdo"))
panel.setVisible(True)  # mostrar/esconder o bloco

# Com spacing personalizado:
panel = SectionPanel(object_name="stack_hotkey", spacing=6)
```

**Atalho em relação a QWidget puro:** elimina a criação manual de QVBoxLayout + setContentsMargins + setObjectName.

**Parâmetros:**
- `object_name: str = ""` — setObjectName (opcional, útil para encontrar o widget via findChild)
- `spacing: int = 0` — espaçamento entre widgets filhos
- `parent` — widget pai

**Propriedades:**
- `section_layout` → QVBoxLayout interno (contentsMargins=0,0,0,0)

---

### `BasePage` — `BasePage.py`
Classe base para páginas com QVBoxLayout padronizado (margins 18, 10, 18, 10 e spacing 8). Serve como base para `PluginPage` e demais páginas do sistema.

```python
from resources.widgets.BasePage import BasePage

page = BasePage()
page.main_layout.addWidget(QLabel("conteúdo"))
page.add_widget(QLabel("atalho"))
page.add_widgets(QLabel("A"), QLabel("B"))
```

**Atributos:**
- `main_layout` — QVBoxLayout com margins e spacing padrão

**Métodos:**
- `add_widget(widget, stretch=0)` — adiciona widget ao main_layout
- `add_widgets(*widgets, stretch=0)` — adiciona múltiplos widgets

---

### `DialogPage` — `DialogPage.py`
Página de conteúdo para diálogos com abas. Herda de `BasePage` — é o **container** que exibe o conteúdo de cada aba quando selecionada.

A **dialog** que usa este widget gerencia as `HorizontalTab` por conta própria, empilhando `DialogPage`s via `QStackedWidget` e alternando a visibilidade conforme a aba clicada.

```python
from resources.widgets.DialogPage import DialogPage
from resources.widgets.HorizontalTab import HorizontalTab

# Dentro de uma QDialog:
self._tabs: list[HorizontalTab] = []
self._pages: list[DialogPage] = []

tab = HorizontalTab("Preview", closable=False)
tab.mousePressEvent = lambda e: self._on_tab_clicked(0)
tab_layout.addWidget(tab)

page = DialogPage(self)
page.add_widget(QLabel("conteúdo"))
stack.addWidget(page)
```

**Atributos herdados de BasePage:**
- `main_layout` — QVBoxLayout com margins e spacing padrão

---

### `PluginPage` — `PluginPage.py`
Container base padrão para todos os plugins. Fornece:
- QVBoxLayout com margins (18, 10, 18, 10) e spacing 8
- Header opcional (QLabel + QFrame separator) se `title` for informado
- **Badge de status encapsulado** — o plugin chama apenas:

      self.page.set_badge(self.page.PRONTA)
      self.page.set_badge(self.page.RUNNING)
      self.page.set_badge(self.page.ERROR)
      self.page.set_badge(self.page.CANCELED)
      self.page.set_badge(self.page.INFO)

  O estilo (cor de fundo, padding, font) é aplicado automaticamente.

- **ExecutionButtons integrado no header** — ordem: `Título → Badge → [stretch] → ExecutionButtons`
  - Se `buttons_config` for `None`, os botões ficam ocultos
  - Se `buttons_config` for um dict, `ExecutionButtons.setup()` é chamado automaticamente

Usado automaticamente pelo `BasePlugin._build_ui()`.

```python
from resources.widgets.PluginPage import PluginPage

# Uso direto (raro)
page = PluginPage(title="Meu Plugin")
page.main_layout.addWidget(QLabel("conteúdo"))
page.set_badge(page.PRONTA)

# Com buttons_config
page = PluginPage(
    title="Meu Plugin",
    buttons_config={
        "executar": {"text": "EXECUTAR", "callback": self._on_executar, "type": "primary"},
    },
)

# Uso via BasePlugin (padrão) — botões passados no super().__init__()
class MeuPlugin(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(
            tool_key="MinhaFerramenta",
            title="Minha Ferramenta",
            buttons_config={
                "executar": {
                    "text": "EXECUTAR",
                    "callback": self._on_executar,
                    "type": "primary",
                },
            },
        )

    def _build_ui(self):
        super()._build_ui()
        self.main_layout.addWidget(QLabel("meu widget"))
        self.page.set_badge(self.page.PRONTA)

    def _on_executar(self):
        self.page.buttons.set_enabled("executar", False)  # desabilita via header
        # ... execução ...
        self.page.buttons.set_enabled("executar", True)
```

**Parâmetros do construtor:**
- `title: str | None` — se informado, cria header com título, badge e execution buttons
- `buttons_config: dict | None` — config dos botões (mesmo formato do `ExecutionButtons.setup()`)

**Atributos públicos:**
- `self.buttons` → `ExecutionButtons | None` — instância dos botões no header
- `self.badge` → `Badge` — badge de status (sempre existe se title foi informado)

**Constantes do badge:** `page.PRONTA`, `page.RUNNING`, `page.ERROR`, `page.CANCELED`, `page.INFO`

---

### `GridGroupPainel` — `GridGroupPainel.py`
Container que distribui N instâncias de `GroupPainel` em colunas com stretch=1 igual para todas. Ideal para organizar painéis lado a lado.

⚠️ **Use sempre `GridGroupPainel` — mesmo para 1 único painel.** `GroupPainel` não pode ser instanciado diretamente.

```python
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.GroupPainel import GroupPainel

# Para 1 painel
painel = GroupPainel("Configurações")
painel.group_layout.addWidget(...)

grid = GridGroupPainel(painel)
main_layout.addWidget(grid)

# Para múltiplos painéis lado a lado
painel_a = GroupPainel("Painel A")
painel_b = GroupPainel("Painel B")

grid = GridGroupPainel(painel_a, painel_b)
main_layout.addWidget(grid)
```

**Propriedades:**
- `painels` → lista de GroupPainel

---

### `FileTreeWidget` — `FileTreeWidget.py`
Árvore de diretórios baseada em `QTreeView` + `QFileSystemModel`. Componente reutilizável para explorar, renomear, excluir, criar e mover arquivos via drag & drop.

```python
from resources.widgets.FileTreeWidget import FileTreeWidget

tree = FileTreeWidget()
tree.set_root_path("C:/meu_projeto")
tree.file_renamed.connect(self._on_renamed)
tree.file_deleted.connect(self._on_deleted)

# API pública
tree.selected_path()        # str | None
tree.selected_paths()       # list[str]
tree.delete_selected()      # bool
tree.rename_selected()      # bool
tree.create_text_file()     # bool
tree.refresh()              # None
```

**Sinais:** `file_renamed(old, new)`, `file_deleted(path)`, `file_created(path)`, `file_moved(src, dst)`, `selection_changed(path | None)`

**Funcionalidades:**
- Suporte a arrastar arquivos para QGIS/Explorer (drag externo com `QMimeData` + `urls`)
- Drop interno com `shutil.move()` e diálogo de conflito (Substituir/Manter ambos/Ignorar)
- Multi-seleção (ExtendedSelection = Ctrl+clique, Shift+clique, Ctrl+A)
- Context menu com Renomear (F2), Excluir (Del), Criar Arquivo (Ctrl+N), Atualizar (F5), Abrir Local no Explorer

---

### `ItemTable` — `ItemTable.py`
Tabela genérica configurável por especificação de colunas. Suporta colunas dos tipos: texto (QTableWidgetItem), spin (QSpinBox), line edit (QLineEdit) e botão remover (SimpleRemoveButton). Elimina formatação manual de QTableWidget.

```python
from resources.widgets.ItemTable import ItemTable

table = ItemTable(
    columns=[
        {"header": "Caminho", "type": "text", "stretch": True, "editable": False},
        {"header": "ID",      "type": "spin", "width": 55, "min": 0, "max": 999},
        {"header": "Legenda", "type": "line", "width": 90, "placeholder": "Legenda..."},
        {"header": "",        "type": "remove", "width": 65},
    ]
)
painel.group_layout.addWidget(table)

table.add_row("arquivo.shp", 1, "Mata")
table.get_row_data(0)       # {"col_0": "arquivo.shp", "col_1": 1, "col_2": "Mata"}
table.all_rows()             # lista de dicts
table.remove_row(0)
table.clear_rows()
```

**Specs de coluna:**
- `"type": "text"` — QTableWidgetItem. Opcional: `editable` (bool)
- `"type": "spin"` — QSpinBox. Opcional: `min`, `max` (int)
- `"type": "line"` — QLineEdit. Opcional: `placeholder` (str)
- `"type": "remove"` — SimpleRemoveButton. Opcional: `remove_text` (str)
- `"stretch": True` — coluna expande
- `"width": N` — largura fixa (se stretch=False)

---

### `CollapsibleParams` — `CollapsibleParams.py`
Container colapsável com header clicável estilo acordeão. Ao clicar no header, a seção expande/recolhe mostrando ou escondendo o conteúdo interno. Usa `AppStyles.theme_colors()` para estilização consistente com o tema.

```python
from resources.widgets.CollapsibleParams import CollapsibleParams

section = CollapsibleParams("Opções Avançadas", parent=self)
section.content_layout.addWidget(QLabel("conteúdo interno"))
main_layout.addWidget(section)

# Controlar programaticamente
section.collapsed = True   # recolher
section.collapsed = False  # expandir
```

**Atributos:**
- `header_label` — SimpleLabel do header (pode customizar texto/estilo)
- `content_layout` — QVBoxLayout interno para adicionar widgets filhos
- `collapsed` — property bool (True = recolhido, False = expandido)

**Parâmetros do construtor:**
- `title: str = "Parâmetros"` — texto do header
- `collapsed: bool = False` — estado inicial
- `parent: QWidget | None = None`

---

### `PropertyInfoWidget` — `PropertyInfoWidget.py`
Widget que exibe propriedades básicas de um arquivo. Internamente usa **`GridLabel`** para exibir pares label: valor. Mostra nome, tamanho formatado, tipo, caminho (clicável como link azul para abrir no Explorer), diretório, datas de criação e modificação.

Recebe dados via `load_data(data)` — o dicionário é tipicamente enriquecido via `BasicExtractor.enrich_json()` (fluxo JSON).

```python
from resources.widgets.PropertyInfoWidget import PropertyInfoWidget

widget = PropertyInfoWidget(parent=self)
widget.load_data({
    "name": "arquivo.txt",
    "size_formatted": "1.2 KB",
    "extension_name": "TXT",
    "path": "c:/pasta/arquivo.txt",
    "directory": "c:/pasta",
    "created": "01/06/2026 12:00:00",
    "modified": "01/06/2026 14:30:00",
})
```

**Métodos:**
- `load_data(data)` — recebe dict com chaves: name, size_formatted, extension_name, path, directory, created, modified

**Notas:**
- O caminho do arquivo é exibido como link azul sublinhado via GridLabel
- Ao clicar no link, abre o diretório pai no Windows Explorer via `QDesktopServices.openUrl`
- Layout sem margins (0,0,0,0) com spacing 8

---

### `SimpleComboBox` — `SimpleComboBox.py`
QComboBox genérico com label opcional. Aceita `Dict[str, str]` (recomendado) ou `List[str]`. Prefira **sempre** Dict — a chave é o valor interno estável, o texto é o display. Isso evita perda de índice e permite maior semântica.

```python
from resources.widgets.SimpleComboBox import SimpleComboBox

# Dict (recomendado) — valor_interno → texto_exibido
combo = SimpleComboBox(
    items={"console": "Console", "renamer": "Renomeador"},
    on_item_changed=self._on_item_changed,
    label="Ferramenta:",
)
combo.current_value   # "console"
combo.current_text    # "Console"
combo.current_value = "renamer"  # setter por valor
combo.select_first()
combo.set_items({"novo": "Novo"})

# List (menos recomendado) — texto = valor
combo = SimpleComboBox(items=["Opção A", "Opção B"])
```

---

### `GridFieldMapping` — `GridFieldMapping.py`
Grade rolável de mapeamento de campos com checkbox + label + lineedit + label + lineedit por linha. Widget genérico — não contém lógica de negócios.

Checkbox unchecked → linha inteira desabilitada visualmente.
Checkbox checked → campos editáveis.

Configurado por dicionário com suporte a `tooltip` que propaga para todos sub-widgets.

```python
from resources.widgets.GridFieldMapping import GridFieldMapping

config = {
    "altitude": {
        "from_label": "Campo Origem:",
        "from_placeholder": "Ex: AbsZ",
        "to_label": "Campo MRK:",
        "to_placeholder": "Ex: Ellh",
        "default_from": "AbsZ",
        "default_to": "Ellh",
        "default_enabled": True,
        "tooltip": "Mapeamento de altitude",
    },
}

grid = GridFieldMapping(config)
grid.values           # dict apenas itens ativos
grid.all              # dict completo (inclusive inativos)
grid.get("altitude")  # {"from": "AbsZ", "to": "Ellh", "enabled": True}
grid.set_values({"altitude": {"from": "Novo", "to": "Ellh", "enabled": False}})
grid.set_enabled("altitude", True)
grid.changed.connect(self._on_mapping_changed)
```

**Sinais:** `changed(key, values)` — emitido quando qualquer campo ou checkbox muda

**Parâmetros do config:**
- `from_label`: str — label do campo de origem
- `from_placeholder`: str — placeholder do lineedit de origem
- `to_label`: str — label do campo destino
- `to_placeholder`: str — placeholder do lineedit destino
- `default_from`: str — valor padrão do campo origem
- `default_to`: str — valor padrão do campo destino
- `default_enabled`: bool — checkbox inicia checked?
- `tooltip`: str — tooltip propagado para todos sub-widgets

---

### `RecentProjectsMenu` — `RecentProjectsMenu.py`
QMenu especializado em exibir lista de projetos recentes. Cada item representa um projeto com nome, tooltip (caminho completo) e estado active/inactive. Projetos com `active=False` (arquivo não encontrado em disco) aparecem desabilitados em itálico, não clicáveis. Usado como submenu do menu "Arquivo > Abrir Recente".

```python
from resources.widgets.RecentProjectsMenu import RecentProjectsMenu

recent_menu = RecentProjectsMenu()
recent_menu.rebuild(recents)  # recents = lista de dicts com path, name, active
recent_menu.project_clicked.connect(self._on_recent_clicked)
```

**Sinais:** `project_clicked(path: str)` — emitido ao clicar em um projeto ativo

---

### `GridPercentView` — `grid/GridPercentView.py`
Grade horizontal de indicadores percentuais generica. Exibe N indicadores lado a lado, cada um com label, valor percentual, barra de preenchimento e tooltip individual ao passar o mouse. Suporta callback por item.

Nao contem logica de negocios — o consumidor define os itens via config e atualiza via `set(key, value, tooltip)`.

```python
from resources.widgets.grid.GridPercentView import GridPercentView

view = GridPercentView({
    "cpu": {"label": "CPU", "value": 0.0, "tooltip": "Aguardando...",
            "callback": self._on_cpu_clicked},
    "ram": {"label": "RAM", "value": 0.0, "tooltip": "Aguardando..."},
})
view.set("cpu", 45.2, tooltip="CPU: 45.2% (8 cores fisicos, ...)")
view.set("ram", 72.8, tooltip="RAM: 72.8% (23.4 GB / 32.0 GB usados)")

view.values           # {"cpu": 45.2, "ram": 72.8}
view.get("cpu")       # 45.2
view.item_clicked.connect(self._on_item_clicked)
```

**Sinais:** `item_clicked(key, value)` — emitido ao clicar em item com callback

**Parâmetros do config:**
- `label`: str — texto do indicador
- `value`: float — valor inicial (0-100)
- `tooltip`: str — tooltip exibido ao passar mouse sobre o item
- `callback`: callable(key, value) | None — opcional, ativa clique

---

### `GridRadio` — `GridRadio.py`
Grade de radio buttons organizados em colunas configuráveis, similar a `GridCheckBox`. Cada radio button tem label, description e tooltip definidos por dicionário.

`num_columns=3` padrão. Se receber menos itens que colunas, distribui igualmente.

```python
from resources.widgets.GridRadio import GridRadio

config = {
    "single": {
        "label": "Arquivo Unico",
        "description": "Processa 1 arquivo",
        "default": True,
        "tooltip": "Modo de arquivo unico",
    },
    "batch": {
        "label": "Lote por Pasta",
        "description": "Processa varios",
        "default": False,
        "tooltip": "Modo de lote",
    },
}

grid = GridRadio(config, num_columns=3)
selected = grid.selected       # "single"
selected_text = grid.selected_text  # "Arquivo Unico"
grid.set_selected("batch")
grid.changed.connect(self._on_radio_changed)
```

**Sinais:** `changed(key)` — emitido quando a seleção muda

**Parâmetros do config:**
- `label`: str — texto do radio button
- `description`: str — descrição/tooltip (se `tooltip` não for informado)
- `default`: bool — se True, inicia selecionado
- `tooltip`: str — tooltip do radio button

---

### `ListFileDialog` — `dialogs/ListFileDialog.py`
Diálogo que exibe uma lista de arquivos do projeto ativo filtrados por extensões. Herda de `BaseDialog` com AppBar no topo. Suporta seleção única ou múltipla.

```python
from resources.widgets.dialogs.ListFileDialog import ListFileDialog

dialog = ListFileDialog(
    extensions=[".las", ".laz"],
    multi_select=True,
    parent=self,
)
if dialog.exec():
    selected = dialog.selected_paths  # list[str]
```

**Parâmetros do construtor:**
- `extensions: list[str]` — extensões para filtrar (ex: `[".las", ".laz"]`)
- `multi_select: bool = False` — True permite selecionar múltiplos arquivos

**Propriedades:**
- `selected_paths` → `list[str]` — caminhos selecionados após `exec()` retornar True

---


### `ComplexSelector` — `complex/ComplexSelector.py` (DEPRECATED)
> ⚠️ **DEPRECATED** — Este widget está obsoleto. **Use `GridComplexSelector`** de `resources/widgets/complex/GridComplexSelector.py` em todas as novas ferramentas. `ComplexSelector` só deve ser usado internamente pelo grid — nunca diretamente por plugins.
>
> ```python
> # ❌ NÃO USE — DEPRECATED
> from resources.widgets.complex.ComplexSelector import ComplexSelector
> 
> # ✅ USE ISTO EM VEZ (via grid)
> from resources.widgets.complex.GridComplexSelector import GridComplexSelector
> ```

---

### `GridComplexSelector` — `complex/GridComplexSelector.py`
Grade de `ComplexSelector`s configurados por dicionário, com suporte a **linking entre selectores** (parent/subfolder/fixed_name) e **dynamic_parent** (modo alterna conforme o tipo do parent). Botão "USAR ORIGEM" automático para outputs com parent.

**REGRAS DE ACOPLAMENTO:**
- O plugin **NUNCA** acessa atributos privados do widget (`_user_callbacks`, `edit`, `file_filter`)
- O plugin **NUNCA** sobrescreve `on_path_change` diretamente — usa `set_on_input_changed()` ou `set_on_changed()`
- Toda comunicação é via API pública
- Cada `ComplexSelector` com parent tem seu próprio botão 📥 nativo, eliminando o botão "USAR ORIGEM" externo do grid

```python
from resources.widgets.complex.GridComplexSelector import GridComplexSelector

grid = GridComplexSelector({
    "Entrada": {
        "file_filter": "LAS/LAZ (*.las *.laz)",
        "mode_type": "input",
        "allow_file": True,
        "allow_folder": True,
        "multiple": True,
        "show_project_button": True,
    },
    "Saída": {
        "mode_type": "output",
        "parent": "Entrada",
        "allow_file": True,       # Dynamic alterna entre file/folder
        "allow_folder": True,     # Ambos True para suportar alternância
        "multiple": False,
        "dynamic_parent": True,    # Ativa modo dinâmico
        "show_suggest_button": True,
        "subfolder": "lasvectorconverter",
        "fixed_name": "resultado",  # Sem extensão — set_output_extension adiciona
    },
}, title="Entrada e Saída")

# Acesso
grid["Entrada"].path()
grid["Entrada"].get_root_path()
grid["Entrada"].get_selected_list()
grid["Entrada"].path_type()

# Input/Output
grid.get_input()
grid.get_output()

# USAR ORIGEM (botão automático)
grid.use_origin("Saída")
grid.use_origin_all()
grid.refresh_links()
```

**API Pública para Callbacks (NÃO sobrescrever `on_path_change`):**
```python
# ✅ RECOMENDADO — para reagir a QUALQUER entrada:
grid.set_on_input_changed(self._on_input_changed)
# callback recebe (label: str, paths: list[str])

# ✅ Para reagir a um selector específico:
grid.set_on_changed("Entrada", self._on_entrada_changed)
# callback recebe (paths: list[str])

# ❌ NUNCA faça isso — quebra o chaining interno:
grid["Entrada"].on_path_change = callback  # PROIBIDO
```

**API Pública para Configuração (plugin não acessa sub-widgets):**
```python
# Substitui entrada.edit.setPlaceholderText(...)
grid.set_input_placeholder("Entrada", "Selecione o arquivo...")

# Substitui entrada.file_filter = value
grid.set_input_file_filter("Entrada", "LAS/LAZ (*.las *.laz)")

# Suspende/restaura callbacks para set_path sem re-avaliação
saved = grid.suspend_callbacks()
try:
    grid["Entrada"].set_path(saved_path)
finally:
    grid.resume_callbacks(saved)
```

**API Pública para Output Dinâmico:**
```python
# Atualiza extensão + sincroniza fixed_name no 📂
grid.set_output_extension("Saída", "shp")
# → fixed_name muda de "resultado.gpkg" para "resultado.shp"
# → 📂 agora gera "resultado.shp"

# Atualiza sufixo (ex: "_converted")
grid.set_output_suffix("Saída", "_converted")
```

**Parâmetros do spec (por chave):**
| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `label_text` | str | chave | Texto do label |
| `file_filter` | str | "Todos (*.*)" | Filtro |
| `mode_type` | str | "input" | "input" ou "output" |
| `parent` | str | "" | Chave do selector pai (só output) |
| `dynamic_parent` | bool | False | Modo dinâmico: filho alterna file/folder conforme parent |
| `allow_file` | bool | True | Mostra 🔍 (inicial, dynamic altera runtime) |
| `allow_folder` | bool | False | Mostra 📁 (inicial, dynamic altera runtime) |
| `multiple` | bool | False | Multi-seleção |
| `show_suggest_button` | bool | False | Mostra 📂 (só output) |
| `show_project_button` | bool | False | Mostra 📄 (só input) |
| `subfolder` | str | "" | Subpasta para output |
| `fixed_name` | str | "" | Nome fixo do arquivo de saída (pode ser sem extensão) |
| `suggested_path` | str | "" | Path relativo pro 📂 |
| `default_path` | str | "" | Path inicial |
| `tooltip` | str | "" | Tooltip |

**Regras do linking (parent) sem dynamic_parent:**
1. Output com `parent` definido → botão "USAR ORIGEM" automático
2. Ao clicar "USAR ORIGEM":
   - Parent modo `file`: output = `dirname(parent) / subfolder / fixed_name`
   - Parent modo `folder`: output = `parent / subfolder`
3. Linking reativo: output se atualiza quando parent muda (se vazio ou gerado pelo USAR ORIGEM)
4. 📂 no output usa `ProjectUtil.get_root_folder()` + `subfolder` + `fixed_name`
5. 📄 só aparece no input

**Regras do modo `dynamic_parent=True`:**
1. Parent seleciona **1 arquivo** (`path_type="file"`):
   - Filho vira **modo file** (🔍 visível, 📁 oculto)
   - Output gerado: `dirname(parent) / subfolder / fixed_name`
   - Placeholder: "Arquivo de saída"
   - **fixed_name é usado**
2. Parent seleciona **>1 arquivo, pasta ou pastas** (`path_type="folder"/"files"/"folders"`):
   - Filho vira **modo folder** (🔍 oculto, 📁 visível)
   - Output gerado: `parent_path / subfolder` (ou `converted` se subfolder vazio)
   - Placeholder: "Pasta de saída"
   - **fixed_name é ignorado**
3. Callback do plugin **NUNCA** sobrescreve `on_path_change` — use `set_on_input_changed()`
4. `allow_file=True` e `allow_folder=True` devem ser configurados no spec para suportar alternância

**Extensão Dinâmica:**
- `fixed_name` pode ser definido **sem extensão** (ex: `"lasvectorconverted"`)
- `set_output_extension("Saída", "gpkg")` adiciona a extensão: `"lasvectorconverted.gpkg"`
- O 📂 (suggest button) usa o `fixed_name` atualizado com a extensão correta
- `_generate_output()` também adiciona extensão se `fixed_name` não tiver

**Importante:** Ao usar `dynamic_parent`, configure o spec com `allow_file=True` e `allow_folder=True` para que o filho possa alternar entre os modos.

---

### `CrsSelectorWidget` — `crs/CrsSelectorWidget.py`
Widget de seleção de CRS/EPSG com label opcional + `SimpleComboBox` (EPSGs comuns do `CommonCrs` enum) + botão 🌎 (`SimpleSecondaryButton`) que abre a `CrsSearchDialog` para busca completa. Não persiste o EPSG selecionado em disco.

```python
from resources.widgets.crs.CrsSelectorWidget import CrsSelectorWidget

selector = CrsSelectorWidget(label="CRS:")
selector.crs_changed.connect(self._on_crs_changed)
selector.set_crs("EPSG:31983")
current = selector.get_crs()      # "EPSG:31983"
code = selector.crs_code          # 31983
label = selector.crs_label        # "EPSG:31983 - SIRGAS 2000 / UTM zone 23S"
```

**Sinais:** `crs_changed(str)` — emitido com o código EPSG completo (ex: `"EPSG:4326"`)

**API pública:**
- `set_crs(epsg_code)` — define programaticamente; EPSGs fora do enum são adicionados como temporários
- `get_crs()` — retorna o código EPSG completo selecionado
- `crs_code` (property) — código numérico (int)
- `crs_label` (property) — texto exibido no combo

**Parâmetros do construtor:**
- `label: str | None = "CRS:"` — texto do label à esquerda; `None` para omitir
- `parent: QWidget | None = None`

---

### `CrsSearchDialog` — `crs/CrsSearchDialog.py`
Diálogo de busca de CRS/EPSG com campo de filtro em tempo real e lista agrupada por categoria (Geográfico 2D/3D, Projetado, Geocêntrico, Composto). Usa `pyproj.database.query_crs_info` (cache lazy) como fonte de dados principal, com fallback para `CommonCrs` se pyproj não estiver disponível. Herda de `BaseDialog`.

```python
from resources.widgets.crs.CrsSearchDialog import CrsSearchDialog

dialog = CrsSearchDialog(parent=self)
dialog.crs_selected.connect(self._on_crs_selected)
if dialog.exec():
    epsg = dialog.selected_epsg  # "EPSG:31983"
```

**Sinais:** `crs_selected(str)` — emitido ao selecionar um CRS

**Propriedades:** `selected_epsg` → `str`

**Notas técnicas:**
- Consulta pyproj uma única vez (cache lazy na primeira abertura)
- Filtro é 100% em memória — NÃO reconsulta o banco a cada tecla
- Fallback offline: se pyproj não estiver instalado, exibe apenas os CRS do `CommonCrs` enum

---

## 🚫 Proibido: Import de PySide6/Qt no terminal

**Nunca** execute comandos como `python -c "from PySide6.QtWidgets import ..."` ou `python -c "from resources.widgets.X import Y"` no terminal para verificar código. O PySide6/Qt **trava** ao importar widgets fora de um `QApplication` — o terminal congela sem resposta.

**Sempre use `ast.parse` para verificação sintática:**
```powershell
python -c "import ast; ast.parse(open('arquivo.py', encoding='utf-8').read()); print('✓ OK')"
```

Para testes completos, execute o aplicativo real (`main.py`).

## 🎨 Regras de Estilo para Widgets

### Acesso ao tema

**Única forma permitida:** `AppStyles.current_theme`

```python
from resources.styles.AppStyles import AppStyles

class MeuWidget(QWidget):
    def paintEvent(self, event):
        current_theme = AppStyles.current_theme
        painter.fillRect(rect(), QColor(current_theme.SURFACE_1))
        painter.setPen(QColor(current_theme.ACCENT_TEXT))
        painter.drawText(rect(), "texto")
```

- **Nunca** importe `ThemeManager`, `BaseTheme`, `ct` ou temas concretos diretamente
- **Nunca** crie métodos-ponte no AppStyles como `hud_accent_color()` — use `current_theme.ACCENT_TEXT` diretamente
- **Nunca** use variáveis ambíguas como `t` ou `ct` — sempre `current_theme`

### QSS via AppStyles (recomendado)

Sempre que possível, use métodos de `AppStyles` que geram QSS completo:

```python
self.table.setStyleSheet(AppStyles.log_viewer_table_style())
btn.setStyleSheet(AppStyles.btn_primary_style())
badge.setStyleSheet(AppStyles.badge_success())
```

### O que evitar

- ❌ `AppStyles.theme_colors()` — gera acoplamento com dicionário. Use `current_theme.COR` diretamente.
- ❌ `P["GOLD"]` — GOLD não existe, é específico de tema. Use `current_theme.ACCENT`.
- ❌ Métodos no AppStyles para cores avulsas — não escala (ex: `hud_accent_color()`).

---

> 💡 **Consulte também:** `docs/skills/SKILL_HUD_PROGRESS.md` para documentação sobre o HUD Loader (`HudCircularRingsLoader`) e a ProgressBar central da MainWindow.

---

### `ListViewWidget` — `ListViewWidget.py`
Lista vertical genérica com scroll opcional. Similar a um RecyclerView. Container com QVBoxLayout que aceita adicionar/remover widgets dinamicamente.

Com `scroll=True` (padrão), envolve em QScrollArea frameless. Com `scroll=False`, vira um QVBoxLayout puro.

```python
from resources.widgets.ListViewWidget import ListViewWidget

# Com scroll (padrão):
view = ListViewWidget(spacing=6)
view.add_widget(QLabel("Item 1"))
view.add_widget(QLabel("Item 2"))
view.remove_all()
view.count()          # número de widgets
view.scroll_to_top()
view.scroll_to_bottom()

# Sem scroll (layout puro):
view = ListViewWidget(scroll=False)
view.add_widget(MeuWidget())
```

**Parâmetros do construtor:**
- `spacing: int = 8` — espaçamento entre widgets
- `margins: tuple = (0, 0, 0, 0)` — margens do conteúdo
- `scroll: bool = True` — True envolve em QScrollArea, False = layout puro

**API pública:**
- `add_widget(widget, stretch=0)` — adiciona ao final
- `insert_widget(index, widget)` — insere em posição específica
- `remove_widget(widget)` — remove um widget específico
- `remove_all()` — limpa todos os widgets
- `count()` — número de widgets
- `scroll_to_top()` / `scroll_to_bottom()` — rolagem programática (no-op se scroll=False)

---

### `ScrollWidget` — `ScrollWidget.py`
Container rolável genérico. Envolve qualquer widget em uma QScrollArea frameless. Útil para conteúdos grandes que precisam de scroll mas não são listas.

```python
from resources.widgets.ScrollWidget import ScrollWidget

scroll = ScrollWidget(meu_widget_grande)
parent_layout.addWidget(scroll)
```

**Parâmetros do construtor:**
- `widget: QWidget | None = None` — widget interno (opcional, pode ser definido depois via `set_widget()`)

**API pública:**
- `set_widget(widget)` — define/substitui o widget interno
- `scroll_to_top()` / `scroll_to_bottom()` — rolagem programática

---

### `SeparatorWidget` — `SeparatorWidget.py`
Linha horizontal ou vertical estilizada. Substitui QFrame com HLine/VLine manual. Estilizado via QSS global (`QFrame#separator`), sem hardcoded colors.

```python
from resources.widgets.SeparatorWidget import SeparatorWidget

hline = SeparatorWidget(orientation="horizontal")
vline = SeparatorWidget(orientation="vertical")
```

**Parâmetros do construtor:**
- `orientation: str = "horizontal"` — "horizontal" ou "vertical"

---

### `FootballMatchWidget` — `FootballMatchWidget.py`
Card individual de partida de futebol. Recebe um `Fixture` do `core.model.FootballModel` e exibe:

- **Linha 1:** Data/hora no horário de Brasília (esq) | Campeonato + rodada (dir)
- **Linha 2:** [Logo + nome do time casa] [placar/VS] [Logo + nome do time fora]
- **Linha 3:** Status (ex: "Match Finished") | Estádio, cidade

Os gols (fulltime ou penalty) aparecem abaixo do nome de cada time quando a partida já foi realizada. O status tem cores diferentes:
- Cinza escuro para partidas finalizadas
- Verde para partidas ao vivo
- Dourado para partidas decididas nos pênaltis

```python
from core.model.FootballModel import Fixture
from resources.widgets.FootballMatchWidget import FootballMatchWidget

widget = FootballMatchWidget(fixture)
```

**Parâmetros do construtor:**
- `fixture: Fixture` — modelo da partida (obrigatório)

**Propriedades:**
- `fixture` → `Fixture` — retorna a fixture associada

---

### `GridCardView` — `GridCardView.py`
Grade genérica de cards configuráveis por dicionário. Widget 100% genérico, sem lógica de negócio — reutilizável por qualquer plugin.

**Tipos de label:**
- `"simple"` — texto normal, cor secundária
- `"simple_accent"` — texto normal, cor de destaque (accent)
- `"great"` — texto grande (22px), cor secundária
- `"great_accent"` — texto grande (22px), cor de destaque (accent)

```python
from resources.widgets.GridCardView import GridCardView

config = {
    "items_per_row": 4,
    "cards": [
        {"logo": "path/to/icon.png", "labels": [
            {"type": "great_accent", "text": "32°C"},
            {"type": "simple", "text": "Temperatura"},
        ]},
        {"labels": [
            {"type": "great", "text": "15 km/h"},
            {"type": "simple_accent", "text": "Vento"},
        ]},
    ],
}
view = GridCardView(config)
parent_layout.addWidget(view)

# Atualizar dinamicamente
view.set_card_value(card_index=0, label_index=0, text="35°C")
```

**Parâmetros do config:**
- `items_per_row: int` (padrão 4) — cards por linha
- `cards: list[dict]` — cada card pode ter:
  - `logo: str` (opcional) — caminho/URL da imagem
  - `labels: list[dict]` — cada label tem:
    - `type: str` — "simple", "simple_accent", "great", "great_accent"
    - `text: str` — conteúdo
    - `tooltip: str` (opcional)

**API pública:**
- `build(config)` — reconstrói o grid
- `set_card_value(card_index, label_index, text)` — atualiza label dinamicamente

---

## 🆕 Como criar um Novo Widget

1. Crie o arquivo em `resources/widgets/MeuWidget.py`
2. A classe deve herdar de `QWidget` (ou `QPushButton`, `QLabel`, etc.)
3. Siga o padrão de nomenclatura: `PascalCase` para classe, `snake_case` para arquivo
4. Use `from __future__ import annotations` no topo
5. Adicione docstring explicando o propósito e uso
6. **ATUALIZE ESTA SKILL** — adicione o novo widget ao catálogo acima (Contrato 12)

## 🛠 Como modificar um Widget Existente

- **Mantenha compatibilidade retroativa**: não quebre a assinatura dos métodos existentes
- Se precisar adicionar parâmetros novos, use valores padrão (`=None`, `=False`)
- É preferível **estender** um widget existente a criar um novo similar
- Atualize esta skill se a interface pública mudar

---

### `ToastNotification` — `ToastNotification.py`
Notificação toast estilo Android. Exibe uma mensagem temporária que aparece, faz fade out e se auto-destrói, sem travar a UI (QTimer não-bloqueante + QPropertyAnimation).

```python
from resources.widgets.ToastNotification import ToastNotification

# Sucesso (padrão escuro)
ToastNotification.show("Configurações salvas com sucesso!")

# Erro (fundo vermelho)
ToastNotification.show("Falha ao processar", is_error=True)
```

**Métodos estáticos:**
- `show(text, is_error=False, parent=None)` — exibe o toast
- `dismiss()` — fecha o toast atual

**Comportamento:**
- 2.5s visível → 500ms fade out → auto-destrói (`WA_DeleteOnClose`)
- Reposiciona automaticamente ao redimensionar a janela pai
- Não bloqueia a UI (assíncrono)
- Fecha toast anterior se novo for chamado

---

### `MapInfos` — `MapInfos.py`
Barra de informações horizontais para visualizadores geoespaciais. Exibe labels lado a lado (coordenadas, zoom, CRS, contagem de camadas) com separadores verticais. Ideal para a parte inferior de visualizadores de mapa.

```python
from resources.widgets.MapInfos import MapInfos

infos = MapInfos()
infos.set_coords(-15.78, -47.93)
infos.set_zoom(12)
infos.set_crs("EPSG:3857")
infos.set_layer_count(3)
infos.clear_coords()
```

**API pública:**
- `set_coords(lat, lon)` — atualiza coordenadas
- `set_zoom(zoom)` — atualiza nível de zoom
- `set_crs(crs)` — atualiza CRS
- `set_layer_count(count)` — atualiza contagem de camadas
- `clear_coords()` — limpa coordenadas

---

## ✅ Checklist ao criar/alterar UI

- [ ] Consultei o catálogo acima antes de importar de `PySide6.QtWidgets`?
- [ ] O componente que preciso já existe como widget composto?
- [ ] Se não existe, criei em `resources/widgets/` e atualizei esta skill?
- [ ] Se modifiquei um existente, mantive compatibilidade retroativa?