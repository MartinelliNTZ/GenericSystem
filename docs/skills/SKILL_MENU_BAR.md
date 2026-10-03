# Skill: Sistema de Menus (MenuBar)

Estrutura completa do sistema de barra de menus do **Aetheris ToolBox**, com arquitetura baseada em itens de menu separados por responsabilidade.

> ⚠️ **Contratos aplicáveis:**
> - **Contrato 14** — `MenuManager` encapsula `MenuBar` + toolbar. A `MainWindow` nunca importa `MenuBar` diretamente.
> - **Contrato 15** — `MenuCategory` define em qual menu suspenso cada ferramenta aparece.
> - **Contrato 12** — Documentação reflexiva: toda modificação funcional deve atualizar esta skill.

---

## 🧱 Arquitetura

```
MenuManager (orquestrador — core/config/MenuManager.py)
  ├── MenuBar (container puro — resources/widgets/MenuBar.py)
  │     ├── FileMenuItem  → "Arquivo"   → [Sair]
  │     ├── SystemMenuItem → "Sistema"   → [tools dinâmicas do ToolRegistry]
  │     └── HelpMenuItem  → "Ajuda"     → [Sobre]
  └── Toolbar (ToolGroups) — toolbar de ícones

BaseMenuItem (pai — core/menus/BaseMenuItem.py)
  ├── FileMenuItem   (core/menus/FileMenuItem.py)
  ├── SystemMenuItem (core/menus/SystemMenuItem.py)
  └── HelpMenuItem   (core/menus/HelpMenuItem.py)
```

**Princípio:** cada aba da barra de menus é um `BaseMenuItem` que sabe quais ações exibe e o que fazer quando clicado. A `MenuBar` é apenas o container que as recebe.

---

## 📁 `core/menus/BaseMenuItem.py`

Classe base para todas as abas. Fornece:

| Método | Descrição |
|---|---|
| `add_action(text, callback, data, icon, enabled)` | Adiciona uma ação ao dropdown |
| `add_submenu(text, menu)` | Adiciona um submenu (`QMenu`) como item do dropdown |
| `add_separator()` | Adiciona separador visual |
| `clear()` | Remove todas as ações |
| `build_menu()` | Constrói e retorna um `QMenu` com estilo aplicado |
| `title` (property) | Nome da aba (ex: "Arquivo") |

**Sinais:**
- `action_triggered(str)` — emitido quando qualquer ação é clicada (argumento = `data`)

```python
from core.menus.BaseMenuItem import BaseMenuItem

class MeuMenuItem(BaseMenuItem):
    def __init__(self, parent=None):
        super().__init__("MinhaAba", parent)
        self._build_actions()

    def _build_actions(self):
        self.add_action("Abrir", self._on_abrir, data="abrir")
        self.add_action("Fechar", self._on_fechar, data="fechar")

    def _on_abrir(self):
        print("abriu")

    def _on_fechar(self):
        print("fechou")
```

---

## 📁 `core/menus/FileMenuItem.py`

Aba "Arquivo". Itens fixos e submenu dinâmico:

| Item | Sinal emitido | Data |
|---|---|---|
| Novo | `novo_clicked` | `"novo"` |
| Abrir | `abrir_clicked` | `"abrir"` |
| Salvar como | `salvar_como_clicked` | `"salvar_como"` |
| Abrir Recente | `recente_clicked(str)` (submenu dinâmico) | path do .mtl |
| Sair | `sair_clicked` | `"sair"` |

O submenu "Abrir Recente" é um `RecentProjectsMenu` (QMenu) que exibe a lista de projetos recentes salvos em `config/recent_projects.json`. Projetos cujo arquivo .mtl não existe mais em disco aparecem desabilitados (active=False, itálico).

**Métodos públicos:**
- `refresh_recentes()` — reconstrói o submenu com dados atualizados do disco

```python
from core.menus.FileMenuItem import FileMenuItem

item = FileMenuItem()
item.novo_clicked.connect(self._on_novo)
item.abrir_clicked.connect(self._on_abrir)
item.salvar_como_clicked.connect(self._on_salvar_como)
item.recente_clicked.connect(self._on_recente)
item.sair_clicked.connect(self.close)
```

---

## 📁 `core/menus/SystemMenuItem.py`

Aba "Sistema". Populada dinamicamente com ferramentas do `ToolRegistry` cujo `menu_category == MenuCategory.SYSTEM`.

| Item | Sinal emitido | Data |
|---|---|---|
| Cada tool do ToolRegistry | `tool_clicked(str)` | `tool.name` |

```python
from core.menus.SystemMenuItem import SystemMenuItem

item = SystemMenuItem()
item.refresh_tools()  # recarrega do ToolRegistry
item.tool_clicked.connect(self._on_tool_activated)
```

**Métodos:**
- `refresh_tools()` — limpa e recria as ações baseadas no `ToolRegistry`

---

## 📁 `core/menus/HelpMenuItem.py`

Aba "Ajuda". Itens fixos:

| Item | Sinal emitido | Data |
|---|---|---|
| Sobre | `sobre_clicked` | `"sobre"` |

```python
from core.menus.HelpMenuItem import HelpMenuItem

item = HelpMenuItem()
item.sobre_clicked.connect(self._show_about)
```

---

## 📦 `resources/widgets/MenuBar.py`

Container puro da barra de menus. **Não contém lógica de negócio.**

| Método | Descrição |
|---|---|
| `add_menu_item(item: BaseMenuItem)` | Adiciona uma aba à barra |
| `remove_menu_item(title: str) -> bool` | Remove uma aba pelo título |
| `get_menu_item(title: str) -> BaseMenuItem` | Obtém um item pelo título |
| `refresh_all()` | Reconstrói todos os QMenus (útil após mudanças dinâmicas) |

**Sinais:**
- `action_triggered(str)` — repassa o data da ação clicada em qualquer aba

```python
from resources.widgets.MenuBar import MenuBar
from core.menus.FileMenuItem import FileMenuItem
from core.menus.SystemMenuItem import SystemMenuItem
from core.menus.HelpMenuItem import HelpMenuItem

bar = MenuBar()
bar.add_menu_item(FileMenuItem())
bar.add_menu_item(SystemMenuItem())
bar.add_menu_item(HelpMenuItem())
bar.action_triggered.connect(self._on_menu_action)
```

---

## ⚙️ `core/config/MenuManager.py`

Orquestrador principal. Instancia a `MenuBar`, cria os três `MenuItem`s, conecta sinais e monta a toolbar (`ToolGroup`s).

| Propriedade | Tipo | Descrição |
|---|---|---|
| `menu_bar` | `MenuBar` | Barra de menus pronta para layout |
| `toolbar_widget` | `QWidget` | Toolbar pronta para layout |
| `tool_groups` | `list[ToolGroup]` | Grupos de ferramentas criados |

**Sinais (conectados pela MainWindow):**
- `tool_activated(str)` — emitido ao clicar em qualquer ferramenta (toolbar ou menu)
- `sair_clicked()` — emitido ao clicar em Arquivo > Sair
- `sobre_clicked()` — emitido ao clicar em Ajuda > Sobre

```python
# Uso na MainWindow:
from core.config.MenuManager import MenuManager

manager = MenuManager()
manager.build()
manager.tool_activated.connect(self._on_tool_activated)
manager.sair_clicked.connect(self.close)
manager.sobre_clicked.connect(self._show_about)

root_layout.addWidget(manager.menu_bar)
root_layout.addWidget(manager.toolbar_widget)
```

---

## 🎨 Estilos

O estilo visual do dropdown (QMenu) está centralizado em `resources/styles/AppStyles.py`:

| Método | Descrição |
|---|---|
| `AppStyles.menu_bar_style()` | Estilo da `QMenuBar` (tabs + barra) |
| `AppStyles.menu_dropdown_style()` | Estilo do `QMenu` (dropdown suspenso) com hover dourado |
| `AppStyles.toolbar_icon_size()` | Tamanho do ícone na toolbar (px) — obtido do tema via `TOOLBAR_ICON_SIZE` |
| `AppStyles.toolbar_btn_size()` | Tamanho do botão na toolbar (px) — obtido do tema via `TOOLBAR_BTN_SIZE` |
| `AppStyles.toolbar_btn_border_radius()` | Border-radius do botão da toolbar (px) — obtido do tema via `BORDER_RADIUS_TOOLBAR_BTN` |

O `menu_dropdown_style()` é aplicado **diretamente em cada QMenu** via `BaseMenuItem.build_menu()` porque o QMenu é um popup independente que não herda stylesheet do pai.

Os tamanhos de ícone e botão da toolbar (`AppStyles.toolbar_icon_size()` e `AppStyles.toolbar_btn_size()`) são lidos dos tokens semânticos do tema ativo, garantindo que cada tema possa definir seu próprio tamanho de toolbar. Atualmente:
- **DarkCharcoalTheme**: ícone 20px, botão 32px
- **ZeroGrausTheme**: ícone 20px, botão 32px
- **BlueTheme**: ícone 22px, botão 36px

---

## ➕ Criando uma Nova Aba

1. Crie um arquivo em `core/menus/NomeMenuItem.py`
2. Herde de `BaseMenuItem`
3. Implemente `_build_actions()` definindo os itens com `add_action()`
4. Crie sinais específicos para ações importantes (ex: `sair_clicked`)
5. No `MenuManager.build()`, instancie e registre com `menu_bar.add_menu_item()`
6. **ATUALIZE ESTA SKILL** (Contrato 12)

```python
# core/menus/MinhaAbaMenuItem.py
from PySide6.QtCore import Signal
from core.menus.BaseMenuItem import BaseMenuItem

class MinhaAbaMenuItem(BaseMenuItem):
    acao_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__("MinhaAba", parent)
        self._build_actions()

    def _build_actions(self):
        self.add_action("Opção 1", self._on_opt1, data="opt1")
        self.add_action("Opção 2", self._on_opt2, data="opt2")

    def _on_opt1(self):
        self.acao_clicked.emit("opt1")

    def _on_opt2(self):
        self.acao_clicked.emit("opt2")
```

---

## ✅ Checklist

- [ ] A nova aba herda de `BaseMenuItem`?
- [ ] Os itens usam `add_action()` com `data` único?
- [ ] Sinais específicos foram criados para ações importantes?
- [ ] O item foi registrado no `MenuManager.build()`?
- [ ] A `MainWindow` NÃO importa `MenuBar` diretamente (Contrato 14)?
- [ ] Esta skill foi atualizada se houver mudança funcional (Contrato 12)?