# 📋 Plano de Ação — SystemMonitorWidget (Monitor de CPU/RAM)

## 🎯 Objetivo

Criar um widget persistente na barra de menus que exiba em tempo real as porcentagens de uso de **CPU** e **RAM** do sistema, utilizando `psutil` (já presente em `requirements.txt`). O widget deve ser acoplado ao `MenuManager` e posicionado à direita da barra de menus, após os itens "Arquivo | Sistema | Ajuda".

**Layout final da barra superior:**
```
[Arquivo] [Sistema] [Ajuda]  ······················  [CPU: 45%] [RAM: 72%]
```

---

## 🔍 Diagnóstico — Onde e como integrar

| Componente | Papel atual | Impacto |
|---|---|---|
| `MenuManager` (`core/config/MenuManager.py`) | Orquestra MenuBar + Toolbar | Deve adicionar o `GridPercentView` à direita da MenuBar |
| `MenuBar` (`resources/widgets/MenuBar.py`) | Container das abas de menu | Precisa de um layout que suporte widget à direita |
| `ToolBar` (`resources/widgets/ToolBar.py`) | Toolbar de ícones | Alternativa de posicionamento (menos indicada) |
| `SystemMenuItem` (`core/menus/SystemMenuItem.py`) | Aba "Sistema" do menu | Pode conter ação de config do monitor |
| `SignalCatalog` (`core/manager/SignalCatalog.py`) | Sinais do sistema | Pode receber novos sinais de stats update |

### Decisão Arquitetural

O `GridPercentView` será inserido **dentro do `MenuBar`**, no canto direito, usando um `QHBoxLayout` com `addStretch()` entre os menus e o monitor. Isso mantém o monitor visualmente integrado à barra superior sem ocupar espaço da toolbar.

```
MenuBar (QWidget horizontal)
├── [FileMenuItem] [SystemMenuItem] [HelpMenuItem]  ← QMenuBar nativa
├── stretch (addStretch)
└── GridPercentView (CPU | RAM)                      ← widget customizado
```

---

## 🧱 Arquitetura Proposta

```
resources/widgets/grid/
├── GridPercentView.py          ← ✨ NOVO — Widget de exibição de percentuais

core/monitor/
├── __init__.py                 ← ✨ NOVO — Pacote de serviços de monitoramento
└── SystemMonitorService.py     ← ✨ NOVO — Serviço de polling com QTimer + psutil

core/config/
└── MenuManager.py              ← 🔧 MODIFICAR — Adicionar GridPercentView à direita

core/enum/
└── ToolKey.py                  ← 🔧 MODIFICAR — Adicionar SYSTEM_MONITOR

docs/skills/
└── SKILL_WIDGETS.md            ← 📝 ATUALIZAR — Documentar GridPercentView
```

---

## 📦 Componente Detalhado

### 1. `GridPercentView` — `resources/widgets/grid/GridPercentView.py`

Widget que exibe uma grade horizontal de indicadores percentuais. Cada indicador mostra:
- Nome do recurso (ex: "CPU", "RAM")
- Valor percentual (ex: "45%")
- Tooltip ao passar o mouse (ex: "CPU: 45.2% (8 cores, 32% por core)")
- Callback opcional ao clicar

```python
class GridPercentView(QWidget):
    """
    Grade horizontal de indicadores percentuais.

    Configuração via dicionário:
        {
            "cpu": {
                "label": "CPU",
                "value": 0.0,
                "tooltip": "Uso da CPU",
                "callback": self._on_cpu_clicked,   # opcional
            },
            "ram": {
                "label": "RAM",
                "value": 0.0,
                "tooltip": "Uso da RAM",
            },
        }

    Uso:
        view = GridPercentView(config)
        view.set("cpu", 45.2)
        view.set("ram", 72.8)
        view.values  # {"cpu": 45.2, "ram": 72.8}
        view.item_clicked.connect(self._on_item_clicked)
    """

    item_clicked = Signal(str, float)  # key, value
#sinais sao obrigatorio no Sinal Catalog, ler a skill de comunication 
    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        parent: Optional[QWidget] = None,
    ):
        ...

    def set(self, key: str, value: float, tooltip: Optional[str] = None):
        """Atualiza o valor de um indicador."""

    def get(self, key: str) -> float:
        """Retorna o valor atual de um indicador."""

    @property
    def values(self) -> Dict[str, float]:
        """Retorna dict com todos os valores atuais."""
```

**Design visual:**
- Fundo escuro translúcido (mesmo estilo da MenuBar)
- Texto monospace, cor clara (#A1A1AA) para label, cor destaque (#F5B041) para valor
- toda estilizacao deve ser feita com Styles/themes ler skill
de styles
- Tooltip com informações detalhadas
- Cursor pointer nos itens com callback
- Padding horizontal entre itens: 12px
- Altura compatível com a MenuBar (~32px)

**Comportamento:**
- `set(key, value)` atualiza o display e tooltip
- Clique em item com callback → emite `item_clicked(key, value)`
- Tooltip dinâmico: se não fornecido, gera automaticamente "CPU: 45.2%"

---

### 2. `SystemMonitorService` — `core/monitor/SystemMonitorService.py`

Serviço singleton que polla CPU e RAM via `psutil` em intervalo configurável (padrão: 2s).

```python
class SystemMonitorService(QObject):
    """
    Serviço de monitoramento do sistema via psutil.

    Uso:
        monitor = SystemMonitorService(interval_ms=2000)
        monitor.stats_updated.connect(self._on_stats)
        monitor.start()
        # ...
        monitor.stop()

    Sinais:
        stats_updated(dict) — emitido a cada ciclo:
            {
                "cpu": 45.2,
                "ram": 72.8,
                "cpu_tooltip": "CPU: 45.2% (8 cores, uso por core: ...)",
                "ram_tooltip": "RAM: 72.8% (23.4 GB / 32.0 GB)",
            }
    """

    stats_updated = Signal(dict)

    def __init__(self, interval_ms: int = 2000, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._interval = interval_ms

    def start(self):
        self._poll()  # primeira execução imediata
        self._timer.start(self._interval)

    def stop(self):
        self._timer.stop()

    def _poll(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        # ... monta dict com tooltips ...
        self.stats_updated.emit(data)
```

**API Pública:**

| Método | Descrição |
|---|---|
| `start()` | Inicia o polling periódico |
| `stop()` | Para o polling |
| `poll_once()` | Executa uma leitura manual (retorna dict) |
| `is_running` | Property bool — True se o timer está ativo |

**Comportamento:**
- `psutil.cpu_percent(interval=None)` — retorna uso desde última chamada (non-blocking)
- `psutil.virtual_memory()` — retorna uso de RAM (percent + used + total)
- Tooltip de CPU: `"CPU: 45.2% (8 cores físicos, 16 lógicos)"`
- Tooltip de RAM: `"RAM: 72.8% (23.4 GB / 32.0 GB)"`
- Usa `FormatUtils.format_size()` para bytes (Contrato 22)

---

### 3. Integração no `MenuManager`

No método `MenuManager.build()`, após criar a MenuBar e os itens, adicionar:

```python
# ── 7. Adicionar SystemMonitorService + GridPercentView ──
from core.monitor.SystemMonitorService import SystemMonitorService
from resources.widgets.grid.GridPercentView import GridPercentView

self._monitor_service = SystemMonitorService(interval_ms=2000)
self._monitor_view = GridPercentView({
    "cpu": {"label": "CPU", "value": 0.0, "tooltip": "Aguardando...",
            "callback": self._on_cpu_clicked},
    "ram": {"label": "RAM", "value": 0.0, "tooltip": "Aguardando..."},
})

self._monitor_service.stats_updated.connect(self._on_stats_updated)
self._monitor_service.start()

# Adiciona à direita da MenuBar
self._menu_bar.add_widget_right(self._monitor_view)
```

**Métodos adicionados ao MenuManager:**

```python
def _on_stats_updated(self, data: dict):
    """Atualiza o GridPercentView com novos valores."""
    self._monitor_view.set("cpu", data["cpu"], tooltip=data.get("cpu_tooltip"))
    self._monitor_view.set("ram", data["ram"], tooltip=data.get("ram_tooltip"))

def _on_cpu_clicked(self, key: str, value: float):
    """Callback ao clicar em CPU — pode abrir detalhes."""
    self._logger.info(
        "CPU monitor clicked", code="MONITOR_CPU_CLICK",
        value=value,
    )
```

**Método `add_widget_right()` no MenuBar:**

Adicionar à classe `MenuBar` um método que insere um widget à direita:

```python
def add_widget_right(self, widget: QWidget):
    """Adiciona um widget alinhado à direita da barra de menus."""
    self._right_layout.addWidget(widget)
```

O layout do MenuBar passará a ser:
```python
# Layout atual (QHBoxLayout):
# [QMenuBar (menus)] [stretch] [right_container (QHBoxLayout)]
```

---

## 🔧 Arquivos a Modificar — Detalhamento

### 1. ✨ CRIAR — `resources/widgets/grid/GridPercentView.py`

**Ação:** Criar o widget conforme especificação acima.

**Responsabilidades:**
- Exibir indicadores percentuais lado a lado
- Tooltip dinâmico ao passar o mouse
- Suporte a callback por clique
- Atualização via `set(key, value)`

---

### 2. ✨ CRIAR — `core/monitor/__init__.py`

**Ação:** Criar pacote vazio com docstring.

```python
# -*- coding: utf-8 -*-
"""
core/monitor — Serviços de monitoramento do sistema.
"""
```

---

### 3. ✨ CRIAR — `core/monitor/SystemMonitorService.py`

**Ação:** Criar o serviço de polling conforme especificação acima.

---

### 4. 🔧 MODIFICAR — `resources/widgets/MenuBar.py`

**Ação:** Adicionar suporte a widget à direita.

**Antes:**
```python
# Layout: [QMenuBar]
```

**Depois:**
```python
# Layout: [QMenuBar] [stretch] [right_widgets]
```

Adicionar:
- `_right_layout: QHBoxLayout` — layout interno para widgets à direita
- `add_widget_right(widget)` — método público
- `remove_widget_right(widget)` — método público opcional

---

### 5. 🔧 MODIFICAR — `core/config/MenuManager.py`

**Ação:** Adicionar `SystemMonitorService` + `GridPercentView` no `build()`.

**Mudanças:**
- Importar `SystemMonitorService` e `GridPercentView`
- Criar instâncias no `build()`
- Conectar `stats_updated` → atualização do view
- Iniciar o serviço
- Adicionar view à direita da MenuBar
- Parar o serviço no destructor ou via método `shutdown()`

**No `__init__`:**
```python
self._monitor_service: Optional[SystemMonitorService] = None
self._monitor_view: Optional[GridPercentView] = None
```

**No `build()`, após criar MenuBar:**
```python
# ── 7. System Monitor ──
self._setup_system_monitor()
```

**Novo método:**
```python
def _setup_system_monitor(self):
    """Configura o monitor de CPU/RAM na barra de menus."""
    from core.monitor.SystemMonitorService import SystemMonitorService
    from resources.widgets.grid.GridPercentView import GridPercentView

    self._monitor_view = GridPercentView({
        "cpu": {
            "label": "CPU",
            "value": 0.0,
            "tooltip": "Aguardando...",
            "callback": self._on_cpu_clicked,
        },
        "ram": {
            "label": "RAM",
            "value": 0.0,
            "tooltip": "Aguardando...",
        },
    })

    self._monitor_service = SystemMonitorService(interval_ms=2000)
    self._monitor_service.stats_updated.connect(self._on_stats_updated)
    self._monitor_service.start()

    self._menu_bar.add_widget_right(self._monitor_view)
```

**Callbacks:**
```python
def _on_stats_updated(self, data: dict):
    self._monitor_view.set("cpu", data["cpu"], tooltip=data.get("cpu_tooltip"))
    self._monitor_view.set("ram", data["ram"], tooltip=data.get("ram_tooltip"))

def _on_cpu_clicked(self, key: str, value: float):
    self._logger.info(
        "CPU monitor clicked", code="MONITOR_CPU_CLICK",
        value=value,
    )
```

**Shutdown (no `__del__` ou método dedicado):**
```python
def shutdown(self):
    """Para serviços em background."""
    if self._monitor_service:
        self._monitor_service.stop()
        self._monitor_service = None
```

---

### 6. 🔧 MODIFICAR — `core/enum/ToolKey.py`

**Ação:** Adicionar `SYSTEM_MONITOR = "SystemMonitor"` ao enum.

```python
class ToolKey(str, Enum):
    ...
    SYSTEM_MONITOR = "SystemMonitor"
```

---

### 7. 📝 ATUALIZAR — `docs/skills/SKILL_WIDGETS.md`

**Ação:** Adicionar `GridPercentView` ao catálogo de widgets.

---

## 📊 Mapeamento Completo das Alterações

| Arquivo | Tipo | O quê muda |
|---|---|---|
| `resources/widgets/grid/GridPercentView.py` | ✨ NOVO | Widget de indicadores percentuais |
| `core/monitor/__init__.py` | ✨ NOVO | Pacote de monitoramento |
| `core/monitor/SystemMonitorService.py` | ✨ NOVO | Serviço de polling psutil |
| `resources/widgets/MenuBar.py` | 🔧 MODIFICAR | Adicionar `add_widget_right()` |
| `core/config/MenuManager.py` | 🔧 MODIFICAR | Integrar monitor no build() |
| `core/enum/ToolKey.py` | 🔧 MODIFICAR | Adicionar `SYSTEM_MONITOR` |
| `docs/skills/SKILL_WIDGETS.md` | 📝 ATUALIZAR | Documentar GridPercentView |

---

## ✅ Checklist de Verificação de Contratos

| Contrato | Verificação |
|---|---|
| **C1** (QMessageBox) | Nenhum `QMessageBox` usado. ✅ |
| **C2** (except as e) | Todo `except` terá `as e` e logger. ✅ |
| **C3** (Logger) | `SystemMonitorService` usa `LogUtils`. ✅ |
| **C4** (Preferences) | `SystemMonitorService` não usa Preferences. ✅ |
| **C5** (BasePlugin) | Nenhum dos novos componentes é plugin. ✅ |
| **C6** (closeEvent) | Não aplicável. ✅ |
| **C7** (Sinais) | `SystemMonitorService` usa `Signal` próprio (não SignalManager). ✅ |
| **C8** (Dependências) | `psutil` já está em `requirements.txt`. ✅ |
| **C9** (Código morto) | Sem imports mortos. ✅ |
| **C10** (Categorias) | Não é tool. ✅ |
| **C11** (Widgets) | `GridPercentView` criado em `resources/widgets/grid/`. ✅ |
| **C12** (Doc reflexiva) | Este plano + atualização de SKILL_WIDGETS.md. ✅ |
| **C13** (ToolRegistry) | Não modifica tools. ✅ |
| **C14** (MenuManager) | MenuManager gerencia o monitor via `add_widget_right()`. ✅ |
| **C15** (MenuCategory) | Não aplicável. ✅ |
| **C16** (WorkspaceManager) | Não mexe em workspace. ✅ |
| **C17** (ExplorerUtils) | Não usa QFileDialog. ✅ |
| **C18** (ExecutionButtons) | Não tem botões de ação. ✅ |
| **C19** (Estilos) | Usa `AppStyles` para cores consistentes. ✅ |
| **C20** (Progress/HUD) | Não interage com HUD. ✅ |
| **C21** (JsonUtil) | Não cria JSONs. ✅ |
| **C22** (FormatUtils) | Usa `FormatUtils.format_size()` para tooltip de RAM. ✅ |
| **C23** (Utils compartilhados) | Usa `FormatUtils`. ✅ |
| **C24** (SignalManager) | `SystemMonitorService` usa `Signal` próprio, não SignalManager. ✅ |
| **C25** (I/O vetorial/raster) | Não lê dados geoespaciais. ✅ |
| **C26** (ToolKey) | Usa `ToolKey.SYSTEM_MONITOR.value` para logger. ✅ |

### Conclusão: **Nenhum contrato precisa ser quebrado.**

---

## 📝 Checklist de Implementação

- [ ] Criar `resources/widgets/grid/GridPercentView.py` com classe `GridPercentView`
- [ ] Criar `core/monitor/__init__.py` (pacote vazio)
- [ ] Criar `core/monitor/SystemMonitorService.py` com classe `SystemMonitorService`
- [ ] Modificar `resources/widgets/MenuBar.py` — adicionar `add_widget_right()`
- [ ] Modificar `core/config/MenuManager.py` — integrar monitor no `build()`
- [ ] Modificar `core/enum/ToolKey.py` — adicionar `SYSTEM_MONITOR`
- [ ] Atualizar `docs/skills/SKILL_WIDGETS.md` — documentar `GridPercentView`
- [ ] `py_compile` em todos os arquivos modificados/criados
- [ ] Verificar que o monitor para quando a aplicação fecha (shutdown)

---

## 🧪 Teste de Verificação

```python
# Teste do SystemMonitorService
monitor = SystemMonitorService(interval_ms=500)
results = []

def on_stats(data):
    results.append(data)
    assert "cpu" in data
    assert "ram" in data
    assert 0 <= data["cpu"] <= 100
    assert 0 <= data["ram"] <= 100
    monitor.stop()

monitor.stats_updated.connect(on_stats)
monitor.start()

# Teste do GridPercentView
view = GridPercentView({
    "cpu": {"label": "CPU", "value": 0.0},
    "ram": {"label": "RAM", "value": 0.0},
})
view.set("cpu", 45.2)
view.set("ram", 72.8)
assert view.get("cpu") == 45.2
assert view.get("ram") == 72.8
assert view.values == {"cpu": 45.2, "ram": 72.8}
```

---

## 🎨 Design Visual (GridPercentView)

```
┌─────────────────────────────────────────────────────┐
│  CPU: 45%    RAM: 72%                               │
│  ↑ tooltip: "CPU: 45.2% (8 cores)"                  │
│  ↑ clickable (se callback definido)                  │
└─────────────────────────────────────────────────────┘
```

**Estilo:**
- Background: transparente (herda da MenuBar)
- Label: `#A1A1AA`, Consolas 11px
- Valor: `#F5B041` (dourado), Consolas 11px bold
- Padding: 4px 8px entre itens
- Cursor: `PointingHandCursor` em itens com callback
- Tooltip: informações detalhadas formatadas

**Exemplo de tooltip:**
- CPU: `"CPU: 45.2% — 8 cores físicos, 16 lógicos"`
- RAM: `"RAM: 72.8% — 23.4 GB / 32.0 GB usados"`