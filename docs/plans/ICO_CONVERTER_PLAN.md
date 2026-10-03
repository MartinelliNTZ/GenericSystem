# 🧾 Plano de Implementação — Conversor ICO

## 📋 Análise do App Original (pyd6_ico_conv_v1)

O app original possui:
- **ReorderableListWidget**: Lista com thumbnails, drag & drop de arquivos/pastas, reordenação interna, mover cima/baixo, remover selecionados
- **Preview**: Visualização da imagem selecionada
- **Checkboxes de tamanhos**: 16, 32, 48, 64, 128, 256 pixels
- **Botão "Converter para ICO"**: Gera um .ICO por imagem
- **Seleção de pasta de saída**: SimpleSelector

**O que NÃO vamos replicar** (já existente no sistema):
- ❌ ProgressBar local → usar `SignalManager.progress_update` (ui_main já tem)
- ❌ Log em arquivo → usar `self.logger` + `SignalManager.console_message`
- ❌ Toolbar → usar `ExecutionButtons`

---

## 🔧 Novos Widgets Necessários (resources/widgets/)

### 1. `FileListView` — `FileListView.py`
**Widget de lista com thumbnails, reordenação, drag & drop E botões internos**

**Responsabilidades:**
- Exibir lista de arquivos com miniaturas (120x80)
- Drag & drop interno para reordenação (InternalMove)
- Drag & drop externo de arquivos/pastas do sistema
- **Botões internos**: Adicionar Arquivos, Adicionar Pasta, Remover Selecionados, Limpar Tudo, Mover p/ Cima, Mover p/ Baixo
- Método público `add_files(paths)` para receber arquivos programaticamente (ex: pasta do projeto ao abrir)
- Filtro por extensões via `DictManager`-style dict
- **Conexão opcional com PreviewPanel**: se passado como parâmetro `preview_widget`, o FileListView se conecta automaticamente ao PreviewPanel (atualiza preview ao selecionar item)
- Sinal `files_changed(count)` — para o plugin saber quantos arquivos estão na lista
- Sinal `selection_changed(path | None)`

```python
from resources.widgets.FileListView import FileListView
from resources.widgets.PreviewPanel import PreviewPanel
from utils.DictManager import DictManager

preview = PreviewPanel()

# FileListView com PreviewPanel conectado automaticamente
view = FileListView(
    file_filter=DictManager.IMAGE_EXTENSIONS,
    accept_dirs=True,
    preview_widget=preview,  # conexão automática
)

# Plugin pode passar pasta do projeto ao abrir
view.add_files(["c:/projeto/imagens/"])

# API pública
paths = view.get_ordered_paths()
view.add_files(["c:/foto.png"])
view.remove_selected()
view.clear()

# Sinais
view.files_changed.connect(self._on_files_changed)
view.selection_changed.connect(self._on_selection_changed)
```

---

### 2. `PreviewPanel` — `PreviewPanel.py`
**Widget de pré-visualização genérico**

**Responsabilidades:**
- Exibe preview da imagem selecionada (PIL → QImage → QPixmap, redimensionada KeepAspectRatio)
- Label "Nenhuma imagem selecionada" quando vazio
- Método `show_preview(path)` para carregar e exibir
- Método `clear_preview()` para limpar
- **Genérico**: parâmetro `preview_type: str = "image"` para futura extensão (vetores, etc.)
- Tamanho configurável via `fixed_size` (padrão 480x360)

```python
from resources.widgets.PreviewPanel import PreviewPanel

preview = PreviewPanel(
    fixed_size=(480, 360),
    preview_type="image",
)
preview.show_preview("c:/foto.png")
preview.clear_preview()
```

---

### 3. `SelectorGrid` — Modificação no existente
**Adicionar suporte a "suggestion paths"**

Adicionar parâmetro opcional `suggested_paths: Dict[str, str]`:
- Cada `SimpleSelector` ganha um botão "→" visível abaixo do QLineEdit
- O botão só aparece se o caminho sugerido não for vazio
- Ao clicar, insere o caminho no QLineEdit
- Quem passa: `ExplorerUtils.get_default_path("ico", root_folder)`

---

## 🔧 Modificações em Módulos Existentes

### `utils/ExplorerUtils.py` — Adicionar `get_default_path()`
```python
@staticmethod
def get_default_path(category: str, root_folder: str = "") -> str:
    """
    Retorna caminho padrão para uma categoria.
    Categorias: "vector", "raster", "ico", "image", "documents"
    Se root_folder vazio, retorna "" (botão não aparece).
    """
    paths = {
        "vector":    "vector",
        "raster":    "raster", 
        "ico":       "ico",
        "image":     "image",
        "documents": "documents",
    }
    sub = paths.get(category, "")
    if not sub or not root_folder:
        return ""
    return os.path.join(root_folder, sub)
```

### `plugins/BasePlugin.py` — Adicionar `show_project_path`
```python
def __init__(
    self,
    *,
    tool_key: str,
    parent: QWidget | None = None,
    sys_prefs: bool = False,
    title: str | None = None,
    show_project_path: bool = False,  # NOVO
) -> None:
```
Quando `True`, exibe o caminho do projeto (via `ProjectUtil`) ao lado do título, alinhado à direita. Se `False`, não exibe nada.

### `requirements.txt` — Adicionar `Pillow`
```txt
numpy pandas geopandas rasterio scikit-learn tensorflow matplotlib seaborn opencv-python shapely PySide6 psutil pynput Pillow
```

### `docs/ia/contracts.md` — Adicionar Contrato 20 (ProgressBar + Console)
**Novo Contrato 20 — Progress Bar e Console**
```
Plugins DEVEM usar SignalManager para progresso e mensagens ao usuário:
- SignalManager.progress_update(float) — atualiza barra da MainWindow
- SignalManager.console_message(str) — exibe mensagem no ConsolePlugin

Nunca crie QProgressBar ou QTextBrowser para logs no plugin.
```

---

## 🏗 Estrutura do Plugin ICO Converter

### Arquivo: `plugins/ico_converter/IcoConverterPlugin.py`

**Herda de:** `BasePlugin`

**Parâmetros:**
- `tool_key = ToolKey.ICO_CONVERTER.value`
- `title = "Conversor ICO"`
- `show_project_path = True`

**Layout (Contrato 18 — Título → Separator → ExecutionButtons → conteúdo):**

```
┌─ PluginPage (title="Conversor ICO") ─────────────────────────┐
│ Header: [Conversor ICO]        [caminho projeto]     [badge] │
│ Separator                                                     │
│ ┌─ ExecutionButtons ─────────────────────────────────────────┐│
│ │ [nenhum botão interno — tudo no FileListView]  │ CONVERTER ││
│ └────────────────────────────────────────────────────────────┘│
│ ┌─ GridGroupPainel ──────────────────────────────────────────┐│
│ │ ┌─ GroupPainel "Arquivos" ─────┐ ┌─ GroupP. "Pré-Visual..┐││
│ │ │ FileListView (completo,      │ │ PreviewPanel          │││
│ │ │  com seus botões internos)   │ │ (conectado auto via   │││
│ │ │                              │ │  FileListView)        │││
│ │ └──────────────────────────────┘ └───────────────────────┘││
│ ├─ GroupPainel "Tamanhos do Ícone" ──────────────────────────┤│
│ │ GridCheckBox com ICO_SIZES (6 itens, 3 colunas)            ││
│ ├─ SimpleLabel: "Profundidade: 32 bits (RGBA com alpha)"     ││
│ ├─ SelectorGrid "Pasta de Saída" ────────────────────────────┤│
│ │ SimpleSelector (directory) + botão sugestão (se existir)   ││
│ ├─ GridCheckBox "Opções" ────────────────────────────────────┤│
│ │ [x] Vasculhar subpastas  [ ] Salvar ICOs na origem        ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Botões do ExecutionButtons:
| Chave | Texto | Tipo | Descrição |
|-------|-------|------|-----------|
| `convert` | "CONVERTER" | `primary` | Executa a conversão |

### Fluxo de Comunicação:

```
IcoConverterPlugin
├── FileListView (encapsula: add_files, add_folder, remove, clear, move, preview)
│   ├── add_files(["c:/projeto/imagens/"])  ← plugin chama no init se houver pasta
│   └── preview_widget=preview (conexão automática)
├── SignalManager.progress_update(float)    ← durante conversão
├── SignalManager.console_message(str)      ← mensagens para o usuário
└── self.logger.info(...)                   ← logs para o desenvolvedor
```

### Métodos Principais:

| Método | Descrição |
|--------|-----------|
| `_build_ui()` | Monta UI: ExecutionButtons + GridGroupPainel + FileListView+Preview + GridCheckBox + SelectorGrid |
| `load_prefs()` | Carrega: output_dir, sizes, subfolders, save_in_origin |
| `save_prefs()` | Salva preferências |
| `_on_convert()` | Inicia conversão (thread-safe? usar QTimer) |
| `_get_selected_sizes()` | Lista de tamanhos checados |
| `_generate_icos()` | Itera arquivos, chama PIL, emite progresso e console |

### Conversão (PIL):
```python
def _generate_ico(self, image_path: str, sizes: list[int], output_dir: str) -> str:
    img = Image.open(image_path).convert("RGBA")
    sizes_tuples = [(s, s) for s in sorted(sizes)]
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(output_dir, f"{base_name}.ico")
    img.save(out_path, format='ICO', sizes=sizes_tuples)
    return out_path
```

### Logs Obrigatórios (dev) + Console (user):

| Momento | Log (LogUtils) | Console (SignalManager) |
|---------|----------------|------------------------|
| Init | `"ICO_READY"` | — |
| Add files | `"ICO_FILES_ADDED: {n}"` | — |
| Converter start | `"ICO_CONVERT_START: {n} files, sizes={s}"` | `"Iniciando conversão de {n} imagens..."` |
| Each ICO | `"ICO_GENERATED: {path}"` | — |
| Error | `"ICO_CONVERT_ERR: {path}: {e}"` | `"Erro ao processar {path}"` |
| Done | `"ICO_CONVERT_DONE: {ok} ok, {err} err"` | `"Conversão finalizada! {ok} ícones gerados."` |
| Cancelled | `"ICO_CONVERT_CANCELLED"` | `"Conversão cancelada."` |

### Progresso (via SignalManager):
```python
SignalManager.instance().progress_update.emit(progress_percent)
```

### Preferências Salvas:
```python
self.preferences = {
    "sizes": {"16": True, "32": True, "48": True, "64": True, "128": True, "256": False},
    "output_dir": "",
    "subfolders": False,
    "save_in_origin": False,
}
```

### ICO_SIZES (no plugin, não no DictManager):
```python
ICO_SIZES = {
    "16":   {"label": "16 pixels",   "description": "16x16", "default": True},
    "32":   {"label": "32 pixels",   "description": "32x32", "default": True},
    "48":   {"label": "48 pixels",   "description": "48x48", "default": True},
    "64":   {"label": "64 pixels",   "description": "64x64", "default": True},
    "128":  {"label": "128 pixels",  "description": "128x128", "default": True},
    "256":  {"label": "256 pixels",  "description": "256x256", "default": False},
}
```
*(Permanece no plugin por ser específico do ICO Converter, não reutilizável)*

---

## ✅ Passos da Implementação (Checklist Final)

### Passo 1: Modificações em módulos existentes
- [ ] Adicionar `get_default_path()` no `ExplorerUtils`
- [ ] Adicionar `show_project_path` no `BasePlugin.__init__`
- [ ] Adicionar `Pillow` no `requirements.txt`
- [ ] Adicionar Contrato 20 no `docs/ia/contracts.md`

### Passo 2: Criar novos widgets
- [ ] Criar `PreviewPanel` em `resources/widgets/PreviewPanel.py`
  - [ ] Preview de imagem (PIL → QImage)
  - [ ] Label placeholder
  - [ ] Métodos show_preview/clear_preview
  - [ ] Parâmetro preview_type e fixed_size
  - [ ] Atualizar `docs/skills/widgets_skill.md`

- [ ] Criar `FileListView` em `resources/widgets/FileListView.py`
  - [ ] QListWidget com thumbnails 120x80
  - [ ] Drag & drop interno + externo
  - [ ] Filtro por extensões (DictManager-style)
  - [ ] Botões internos: add_files, add_folder, remove_selected, clear
  - [ ] Botões internos: move_up, move_down
  - [ ] Parâmetro `preview_widget` para conectar ao PreviewPanel
  - [ ] Sinais: files_changed, selection_changed
  - [ ] Método público add_files(paths)
  - [ ] Atualizar `docs/skills/widgets_skill.md`

- [ ] Modificar `SelectorGrid` para sugestão de caminho
  - [ ] Parâmetro `suggested_paths` opcional
  - [ ] Botão "→" que insere caminho no QLineEdit
  - [ ] Atualizar `docs/skills/widgets_skill.md`

### Passo 3: Criar o plugin
- [ ] Criar `plugins/ico_converter/__init__.py`
- [ ] Criar `plugins/ico_converter/IcoConverterPlugin.py`
  - [ ] Herdar de BasePlugin com show_project_path=True
  - [ ] `_build_ui()` com layout completo
  - [ ] `load_prefs()` / `save_prefs()`
  - [ ] `_on_convert()` com PIL + SignalManager.progress_update
  - [ ] Console messages via SignalManager.console_message
  - [ ] Logs em pontos críticos (LogUtils)
  - [ ] Badge de status (PRONTA, RUNNING, ERROR)

### Passo 4: Registrar no sistema
- [ ] Adicionar `ICO_CONVERTER` no `ToolKey`
- [ ] Registrar no `ToolRegistry._TOOLS`
  - `tool_type=ToolType.IMAGE`
  - `category=CategoryTool.CENTRAL`
  - `show_in_toolbar=True`

### Passo 5: Verificações finais
- [ ] Compilar com `py_compile`
- [ ] Verificar contratos (Contrato 1-20)
- [ ] Verificar imports mortos
- [ ] Atualizar `docs/skills/widgets_skill.md` com FileListView e PreviewPanel
- [ ] Nenhum QProgressBar ou QTextBrowser criado no plugin