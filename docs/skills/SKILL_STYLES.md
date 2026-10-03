# Skill: Sistema de Estilos e Temas (Styles)

Esta skill documenta o sistema de estilos e temas do **Aetheris ToolBox**, descrevendo sua arquitetura baseada em tokens semânticos, como criar novos temas, e como usar estilos em widgets e plugins.

---

## 📋 Visão Geral

O sistema implementa uma **arquitetura de temas baseada em tokens semânticos** com 18+ grupos de tokens organizados por categoria (ACCENT, SURFACE, TEXT, BORDER, RADIUS, SPACE, etc.). Cada tema concreto herda de `BaseTheme` e sobrescreve todos os tokens com valores específicos.

```
BaseTheme (abstrato) ← DarkCharcoalTheme, ZeroGrausTheme, BlueTheme, GoldPremiumTheme
       ↑
ThemeManager (singleton) — carrega o tema ativo das preferências
       ↑
BaseStyle (estilos globais QSS + helpers de gradiente) ← AppStyles (botões, badges, menus, logs, toolbar)
       ↑
AnimationManager (animações via QPropertyAnimation — hover grow, bounce)
```

**Novidades:**
- **`GradientType` enum** (`core/enum/GradientType.py`) — Tipos de gradiente: `LINEAR`, `RADIAL`, `CONICAL`
- **Gradiente multi-stop com tipo configurável** — Cada tema define o tipo de gradiente para botões primários (`GRADIENT_ACCENT_TYPE`), secundários (`GRADIENT_BUTTON_TYPE`) e tabs (`GRADIENT_TAB_TYPE`)
- **Glow controlado por tema** — `GLOW_BUTTON_ENABLED` e `GLOW_TAB_ENABLED` ativam glow via `QGraphicsDropShadowEffect` em botões e tabs
- **`AnimationManager`** — Gerenciador central de animações Qt (hover grow, bounce)

**Princípios:**
- **Zero valores hardcoded** — todo QSS usa tokens do tema via `ct.theme.ATRIBUTO`
- **Tema ativo lido das preferências** — salvo em `System > "theme"` no `preferences.json`
- **Lazy loading de temas** — só importa o módulo do tema ativo no startup
- **Compatibilidade retroativa** — aliases antigos (BG_DARK, GOLD, etc.) mapeiam para tokens semânticos
- **Fallback automático** — temas que não definem `GRADIENT_*_STOPS` continuam usando gradientes 2-stop clássicos

---

## 🧱 Arquitetura

```
resources/styles/
├── __init__.py               — Exporta classes públicas (AnimationManager, AppStyles, BaseStyle, BaseTheme, DarkCharcoalTheme, ThemeManager, ct)
├── BaseTheme.py              — Classe base abstrata com TODOS os tokens semânticos (18 grupos)
├── DarkCharcoalTheme.py      — Tema concreto: Dark Charcoal + Gold (padrão)
├── ZeroGrausTheme.py         — Tema concreto: Ice Glass / Frozen Crystal
├── BlueTheme.py              — Tema concreto: Modern Dashboard (azul elétrico)
├── BaseStyle.py              — Gera QSS global usando o tema ativo
├── AppStyles.py              — Herda BaseStyle + estilos de botões, badges, logs, menus, tabs, toolbar
├── AnimationManager.py       — Gerenciador central de animações Qt (hover grow, bounce, QPropertyAnimation)
└── ThemeManager.py           — Singleton que mantém o tema ativo e gerencia troca de temas
```

---

## 📦 Componentes

### `BaseTheme` — `resources/styles/BaseTheme.py`

Classe base abstrata que define **todos os tokens semânticos** do sistema. Cada tema concreto deve sobrescrever todos os atributos.

**18 grupos de tokens:**

| # | Grupo | Prefixo | Descrição | Exemplo |
|---|-------|---------|-----------|---------|
| 1 | **ACCENT** | `ACCENT_*` | Cores de destaque principal | `ACCENT`, `ACCENT_HOVER`, `ACCENT_GRADIENT` |
| 2 | **SURFACE** | `SURFACE_*` | Níveis de profundidade (0=fundo…5=topo) | `SURFACE_0` a `SURFACE_5`, `TITLE_BAR` |
| 3 | **TEXT** | `TEXT_*` | Hierarquia tipográfica | `TEXT_HIGH`, `TEXT_MEDIUM`, `TEXT_LOW`, `TEXT_DISABLED` |
| 4 | **BORDER** | `BORDER_*` | Hierarquia de bordas | `BORDER_SUBTLE`, `BORDER_DEFAULT`, `BORDER_STRONG` |
| 5 | **SHADOW** | `SHADOW_*` | Sombras por tamanho | `SHADOW_SM`, `SHADOW_MD`, `SHADOW_LG`, `SHADOW_XL` |
| 6 | **RADIUS** | `RADIUS_*` | Escala global de cantos arredondados (int) | `RADIUS_XS`(2) a `RADIUS_XL`(16), `RADIUS_FULL` |
| 7 | **SPACE** | `SPACE_*` | Escala global de espaçamento (int) | `SPACE_XXS`(2) a `SPACE_3XL`(48) |
| 8 | **ICON** | `ICON_*` | Tamanhos de ícone | `ICON_XS`(12) a `ICON_XL`(32), `TOOLBAR_ICON_SIZE`(20) |
| 9 | **ANIMATION** | `ANIMATION_*` | Durações de animação (ms) | `ANIMATION_FAST`(120), `ANIMATION_SLOW`(260) |
| 10 | **OPACITY** | `OPACITY_*` | Níveis de opacidade | `OPACITY_DISABLED`(0.35), `OPACITY_ACTIVE`(1.0) |
| 11 | **LAYOUT** | `*` | Layout global | `PAGE_PADDING`, `SECTION_GAP`, `GRID_GAP` |
| 12 | **ELEVATION** | `ELEVATION_*` | Níveis de elevação (z-index) | `ELEVATION_FLAT` a `ELEVATION_HIGH` |
| 13 | **OVERLAY** | `OVERLAY_*` | Sobreposições / glass effect | `OVERLAY_BG`, `BACKDROP_BLUR` |
| 14 | **FOCUS_RING** | `FOCUS_RING_*` | Anel de foco visual | `FOCUS_RING_COLOR`, `FOCUS_RING_WIDTH` |
| 15 | **STATUS** | `COLOR_*` | Cores de estado semântico | `COLOR_SUCCESS`, `COLOR_WARNING`, `COLOR_DANGER`, `COLOR_INFO` |
| 16 | **FONT** | `FONT_*` | Tipografia | `FONT_FAMILY_DEFAULT`, `FONT_SIZE_NORMAL`, `FONT_WEIGHT_BOLD` |
| 17 | **DIMENSIONS** | `*` | Alturas e tamanhos de widgets | `INPUT_HEIGHT`(int), `BUTTON_HEIGHT`(int), `SCROLLBAR_WIDTH`(str c/px), `TOOLBAR_BTN_SIZE`(int) |
| 18 | **SPECIFICS** | `BORDER_RADIUS_*`, `*_PADDING`, etc. | Tokens específicos de implementação | `BORDER_RADIUS_CARD`(str c/px), `BADGE_PADDING_V`(str c/px), `MENU_PADDING`(str c/px) |

**Aliases de compatibilidade retroativa** (mapeiam nomes antigos → tokens semânticos):

| Alias Antigo | Token Semântico |
|-------------|-----------------|
| `BG_DEEPEST` | `SURFACE_0` |
| `BG_DARK` | `SURFACE_1` |
| `BG_PANEL` | `SURFACE_2` |
| `BG_CARD` | `SURFACE_3` |
| `BG_ELEVATED` | `SURFACE_4` |
| `BG_SURFACE` | `SURFACE_5` |
| `ACCENT_COLOR` | `ACCENT` |
| ~~`GOLD`~~ | *(renomeado para `ACCENT_COLOR`)* |
| `ACCENT_COLOR_HOVER` | `ACCENT_HOVER` |
| ~~`GOLD_HOVER`~~ | *(renomeado para `ACCENT_COLOR_HOVER`)* |
| `ACCENT_COLOR_ACTIVE` | `ACCENT_ACTIVE` |
| ~~`GOLD_ACTIVE`~~ | *(renomeado para `ACCENT_COLOR_ACTIVE`)* |
| `ACCENT_COLOR_DIM` | `ACCENT_DIM` |
| ~~`GOLD_DIM`~~ | *(renomeado para `ACCENT_COLOR_DIM`)* |
| `ACCENT_COLOR_LIGHT` | `ACCENT_LIGHT` |
| ~~`GOLD_LIGHT`~~ | *(renomeado para `ACCENT_COLOR_LIGHT`)* |
| `ACCENT_COLOR_GRADIENT` | `ACCENT_GRADIENT` |
| ~~`GOLD_GRADIENT`~~ | *(renomeado para `ACCENT_COLOR_GRADIENT`)* |
| `TEXT_BRIGHT` | `TEXT_HIGH` |
| `TEXT_PRIMARY` | `TEXT_MEDIUM` |
| `TEXT_SECONDARY` | `TEXT_LOW` |
| `TEXT_MUTED` | `TEXT_DISABLED` |
| `TEXT_ACCENT` | `ACCENT_TEXT` |
| ~~`TEXT_GOLD`~~ | *(renomeado para `TEXT_ACCENT`)* |
| `TEXT_ACCENT_BRIGHT` | `ACCENT_BRIGHT` |
| ~~`TEXT_GOLD_BRIGHT`~~ | *(renomeado para `TEXT_ACCENT_BRIGHT`)* |
| `BORDER` | `BORDER_DEFAULT` |
| `BORDER_HOVER` | `BORDER_ACCENT` |
| `SUCCESS` | `COLOR_SUCCESS` |
| `WARNING` | `COLOR_WARNING` |
| `DANGER` | `COLOR_DANGER` |

---

### `ThemeManager` — `resources/styles/ThemeManager.py`

Singleton que mantém a instância do tema ativo. Gerencia carregamento dinâmico e troca de temas.

```python
from resources.styles.ThemeManager import ct

# Acessar tokens do tema atual
cor_fundo = ct.theme.SURFACE_1
cor_texto = ct.theme.TEXT_MEDIUM
fonte = ct.theme.FONT_FAMILY_DEFAULT

# Metadados do tema ativo
chave = ct.current_key          # "dark_charcoal"
info = ct.current_info          # {"module": ..., "label": ..., "description": ...}

# Listar temas disponíveis
temas = ThemeManager.available_themes()
for key, meta in temas.items():
    print(f"{meta['label']}: {meta['description']}")

# Recarregar tema (após alterar preferência)
ct.reload_theme()
```

**Propriedades e métodos:**

| Método/Propriedade | Retorno | Descrição |
|-------------------|---------|-----------|
| `ct.theme` | `BaseTheme` | Instância do tema atual |
| `ct.current_key` | `str` | Chave do tema ativo (lida das preferências) |
| `ct.current_info` | `dict` | Metadados completos do tema ativo |
| `ThemeManager.available_themes()` | `dict[str, dict]` | Todos os temas registrados |
| `ct.reload_theme()` | `None` | Recria a instância do tema |

**Temas registrados no dicionário `THEMES`:**

| Chave | Classe | Label | Descrição |
|-------|--------|-------|-----------|
| `"dark_charcoal"` | `DarkCharcoalTheme` | Dark Charcoal | Tema escuro minimalista com detalhes em dourado |
| `"zero_graus"` | `ZeroGrausTheme` | Zero Graus | Tema cristalino Ice Glass, tons azulados profundos |
| `"blue_theme"` | `BlueTheme` | Blue Theme | Tema inspirado em Modern Dashboard UI, azul elétrico |

**Tema ativo é lido das preferências do sistema:**

```python
# Salvo em config/preferences.json na seção System
# Chave: "theme" → valor: "dark_charcoal" | "zero_graus" | "blue_theme"
sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
tema_atual = sys_prefs.get("theme", "dark_charcoal")  # padrão: dark_charcoal
```

---

### `BaseStyle` — `resources/styles/BaseStyle.py`

Gera o **stylesheet global** do Qt usando o tema ativo. Cobre todos os widgets base do sistema.

```python
from resources.styles.AppStyles import AppStyles

# Aplicar stylesheet global na aplicação
app.setStyleSheet(AppStyles.global_stylesheet())
```

**Componentes cobertos pelo QSS global:**

| Seção | Widgets |
|-------|---------|
| **ScrollBar** | `QScrollBar:vertical`, `QScrollBar::handle:vertical` |
| **GroupBox** | `QGroupBox`, `QGroupBox::title` |
| **Label** | `QLabel`, `QLabel#header_title`, `QLabel#header_subtitle`, `QLabel#section_badge` |
| **Title Bar** | `QWidget#title_bar`, `QLabel#window_title`, `QPushButton#title_btn`, `QPushButton#title_btn_close` |
| **AppBar Toolbar** | `QWidget#appbar_toolbar`, `QPushButton#toolbar_btn` |
| **Side Panel** | `QWidget#tool_side_panel`, `QPushButton#tool_selector_btn` |
| **Console Toolbar** | `QWidget#console_toolbar` |
| **Workspace Tabs** | `QTabBar#workspace_tabs`, `QTabBar::tab`, `QTabBar::close-button` |
| **Splitter** | `QSplitter::handle`, `QSplitter#workspace_splitter::handle` |
| **Line Edit** | `QLineEdit`, `QLineEdit:focus`, `QLineEdit:disabled` |
| **Spin Box** | `QSpinBox`, `QDoubleSpinBox`, `QSpinBox::up-button` |
| **Combo Box** | `QComboBox`, `QComboBox::drop-down`, `QComboBox QAbstractItemView` |
| **Check Box** | `QCheckBox`, `QCheckBox::indicator` |
| **Table** | `QTableWidget`, `QTableWidget::item`, `QHeaderView::section` |
| **Text Browser/Edit** | `QTextBrowser`, `QTextEdit` |
| **Progress Bar** | `QProgressBar`, `QProgressBar::chunk` |

---

### `AnimationManager` — `resources/styles/AnimationManager.py`

Gerenciador central de animações Qt via `QPropertyAnimation`. Cria animações reutilizáveis sem necessidade de subclasses ou event filters manuais.

Atualmente usado pelo `ToolbarButton` para animar hover grow (botão + ícone aumentam ao passar o mouse).

```python
from resources.styles.AnimationManager import AnimationManager
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `animate_property(widget, prop, start, end, duration, easing)` | Animação genérica de qualquer propriedade Qt |
| `animate_hover_grow(widget, grow_px, grow_icon_px, duration)` | Configura hover grow (enter/leave) no widget |
| `animate_bounce(widget, prop, start, peak, end, duration)` | Animação bounce (vai ao pico e retorna) |
| `clear_hover_grow(widget)` | Remove animação hover grow |

**Uso — Hover Grow (padrão para ToolbarButton):**

```python
from resources.styles.AnimationManager import AnimationManager

# Hover grow com valores default do tema
AnimationManager.animate_hover_grow(widget)

# Custom:
AnimationManager.animate_hover_grow(
    widget,
    grow_px=4,          # botão aumenta 4px
    grow_icon_px=24,    # ícone vai para 24x24 no hover
    duration=120,       # duração em ms
)
```

**Uso — Animação genérica:**

```python
anim = AnimationManager.animate_property(
    widget,
    b"minimumSize",
    QSize(32, 32),
    QSize(52, 52),
    duration=180,
    easing=QEasingCurve.Type.OutCubic,
)
```

**Como funciona `animate_hover_grow`:**
1. Salva os handlers `enterEvent`/`leaveEvent` originais do widget
2. No Enter: anima `minimumSize`, `maximumSize` e `iconSize` para valores maiores
3. No Leave: anima de volta para os valores originais
4. Propaga o evento para o handler original (preservando tooltip, cursor, etc.)

**Tokens do tema usados:**
- `TOOLBAR_BTN_HOVER_GROW` — pixels extras no hover
- `ANIMATION_FAST` — duração da animação (ms)

---

### `AppStyles` — `resources/styles/AppStyles.py`

Herda de `BaseStyle` e adiciona estilos específicos da aplicação: botões, badges, logs, menus, tabs e diálogos.

**Métodos de botões:**

| Método | Descrição | Uso |
|--------|-----------|-----|
| `btn_secondary_style()` | Botão secundário — gradiente suave, hover com glow | `SimpleSecondaryButton` |
| `btn_primary_style()` | Botão primário — gradiente dourado/acento | `SimplePrimaryButton` |
| `btn_danger_style()` | Botão de perigo — vermelho escuro | `SimpleDangerButton` |
| `btn_ghost_style()` | Botão ghost — invisível, aparece no hover | `SimpleGhostButton` |
| `btn_remove_style()` | Botão remover — preto, hover vermelho | `SimpleRemoveButton` |

**Métodos de badges:**

| Método | Cor | Uso |
|--------|-----|-----|
| `badge_success()` | `COLOR_SUCCESS` | Operação concluída |
| `badge_running()` | `COLOR_WARNING` | Processando |
| `badge_error()` | `COLOR_DANGER` | Erro |
| `badge_canceled()` | `COLOR_WARNING` | Cancelado |
| `badge_info()` | `COLOR_INFO` | Informativo |

**Métodos de menu:**

| Método | Descrição |
|--------|-----------|
| `menu_bar_style()` | Estilo da `QMenuBar` (tabs + barra) |
| `menu_dropdown_style()` | Estilo do `QMenu` (dropdown suspenso) |

**Métodos de diálogo:**

| Método | Descrição |
|--------|-----------|
| `dialog_stylesheet()` | QSS genérico para `QDialog` |
| `dialog_content_border_style()` | Borda sutil para content widget do `BaseDialog` |
| `about_dialog_stylesheet()` | QSS completo para `AboutDialog` |

**Métodos de tab (cores para paintEvent custom):**

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `tab_common_colors()` | `dict[str, str]` | Cores padronizadas para tabs (vertical e horizontal) |
| `theme_colors()` | `dict[str, str]` | Todas as cores do tema atual (cacheado) |
| `vertical_tab_colors()` | `dict[str, str]` | Cores para pintura manual do `VerticalTab` |

**Métodos de log HTML:**

| Método | Descrição |
|--------|-----------|
| `log_html(text, timestamp, color, ts_color, weight)` | Linha de log formatada com timestamp |
| `log_link_html(text, url)` | Link clicável para log |
| `log_section_html(text)` | Título de seção para log |

**Métodos de CollapsibleParams:**

| Método | Descrição |
|--------|-----------|
| `collapsible_header_height()` | Altura do header |
| `collapsible_header_style()` | Estilo do header clicável |
| `collapsible_content_style()` | Estilo do container de conteúdo |

**Métodos de RecentProjectsMenu:**

| Método | Descrição |
|--------|-----------|
| `recent_project_name_style(active)` | Estilo do nome do projeto |
| `recent_project_sub_style(active)` | Estilo do path/data |
| `recent_project_hover_style()` | Cor de fundo hover |
| `recent_project_hover_name_style()` | Estilo do nome no hover |
| `recent_project_hover_sub_style()` | Estilo do path/data no hover |

---

### Temas Concretos

#### `DarkCharcoalTheme` — `resources/styles/DarkCharcoalTheme.py`

Tema padrão do sistema. Visual minimalista escuro com detalhes em dourado.

```python
ACCENT = "#C9A84C"           # Dourado
SURFACE_0 = "#08080A"        # Fundo absoluto (quase preto)
SURFACE_1 = "#0C0C0F"        # Fundo padrão
SURFACE_2 = "#121216"        # Painéis
SURFACE_3 = "#18181D"        # Cards
SURFACE_4 = "#1E1E24"        # Elementos elevados
SURFACE_5 = "#24242B"        # Superfície hover
TEXT_HIGH = "#F0F0F0"        # Títulos
TEXT_MEDIUM = "#DCDCDC"      # Corpo
TEXT_LOW = "#888890"         # Secundário
```

#### `ZeroGrausTheme` — `resources/styles/ZeroGrausTheme.py`

Tema cristalino Ice Glass. Tons azulados profundos com acento ciano.

```python
ACCENT = "#7FE8FF"           # Crystal Cyan
SURFACE_0 = "#02060A"        # Deep Arctic Glass
SURFACE_1 = "#071018"
SURFACE_2 = "#0C1824"
SURFACE_3 = "#122131"
SURFACE_4 = "#173046"
SURFACE_5 = "#1C3E59"
TEXT_HIGH = "#F7FDFF"        # Branco gelo
```

#### `BlueTheme` — `resources/styles/BlueTheme.py`

Tema inspirado em Modern Dashboard UI. Azul elétrico vibrante.

```python
ACCENT = "#1EA7FF"           # Azul elétrico
SURFACE_0 = "#050B1A"        # Navy profundo
SURFACE_1 = "#081426"
SURFACE_2 = "#0C1D35"
SURFACE_3 = "#102744"
SURFACE_4 = "#183355"
SURFACE_5 = "#21426B"
TEXT_HIGH = "#FFFFFF"        # Branco puro
```

---

## 🎯 Como Usar

### Em Widgets (QSS via stylesheet)

```python
from resources.styles.AppStyles import AppStyles

# Aplicar estilo de botão primário
btn.setStyleSheet(AppStyles.btn_primary_style())

# Aplicar badge de sucesso
badge.setStyleSheet(AppStyles.badge_success())

# Aplicar estilo de menu dropdown
menu.setStyleSheet(AppStyles.menu_dropdown_style())
```

### Em paintEvent (cores para pintura manual)

```python
from resources.styles.AppStyles import AppStyles

def paintEvent(self, event):
    current_theme = AppStyles.current_theme
    painter.fillRect(rect(), QColor(current_theme.SURFACE_0))
    painter.setPen(QColor(current_theme.ACCENT_TEXT))
    painter.drawText(rect(), "Texto")
```

### Em tabs custom (VerticalTab, HorizontalTab)

```python
from resources.styles.AppStyles import AppStyles

P = AppStyles.tab_common_colors()
if self.selected:
    painter.fillRect(rect(), QColor(P["bg_selected"]))
    painter.setPen(QColor(P["fg_selected"]))
else:
    painter.fillRect(rect(), QColor(P["bg_default"]))
    painter.setPen(QColor(P["fg_default"]))
```

### Em logs HTML

```python
from resources.styles.AppStyles import AppStyles

current_theme = AppStyles.current_theme
html = AppStyles.log_html(
    text="Processamento concluído",
    timestamp="14:30:00",
    color=current_theme.COLOR_SUCCESS,
    ts_color=current_theme.TEXT_LOW,
)
browser.append(html)
```

### Aplicar stylesheet global

```python
from PySide6.QtWidgets import QApplication
from resources.styles.AppStyles import AppStyles

app = QApplication([])
app.setStyleSheet(AppStyles.global_stylesheet())
```

---

## 🆕 Como Criar um Novo Tema

1. **Crie o arquivo** em `resources/styles/MeuTema.py`
2. **Herde de `BaseTheme`** e sobrescreva **todos** os atributos
3. **Registre no `ThemeManager.THEMES`** adicionando entrada no dicionário
4. **Altere a preferência** `System > "theme"` para a chave do novo tema
5. **Recarregue** com `ct.reload_theme()` ou reinicie a UI

```python
# resources/styles/MeuTema.py
from resources.styles.BaseTheme import BaseTheme

class MeuTema(BaseTheme):
    ACCENT = "#FF6600"
    ACCENT_HOVER = "#FF8833"
    # ... sobrescrever TODOS os tokens ...
    SURFACE_0 = "#0A0A0A"
    SURFACE_1 = "#141414"
    # ...
```

```python
# Em ThemeManager.THEMES:
"meu_tema": {
    "module":      "resources.styles.MeuTema",
    "label":       "Meu Tema",
    "description": "Descrição visual do tema",
},
```

---

## 🚫 Proibido: Import de PySide6/Qt no terminal

**Nunca** execute comandos como `python -c "from PySide6.QtWidgets import ..."` ou `python -c "from resources.widgets.X import Y"` no terminal para verificar código. O PySide6/Qt **trava** ao importar widgets fora de um `QApplication` — o terminal congela sem resposta.

**Sempre use `ast.parse` para verificação sintática:**
```powershell
python -c "import ast; ast.parse(open('arquivo.py', encoding='utf-8').read()); print('✓ OK')"
```

Para testes completos, execute o aplicativo real (`main.py`).

---

## 🧠 Regra de Decisão: Token com Unidade (px) vs Token Numérico

Todo token de tema que representa uma **grandeza dimensional usada em QSS** deve ser uma **string com a unidade `px`** (ex: `"12px"`, `"-6px"`, `"999px"`). Tokens que só são lidos em Python puro (QSize, setFixedHeight, animation.setDuration, QPainter) permanecem **numéricos** (`int`/`float`).

### Critério de decisão (aplicar token por token)

Para cada token do tema, pergunte:
> "Esse valor é usado em algum lugar dentro de uma f-string de QSS (global_stylesheet, ou qualquer outro .py que monte `setStyleSheet(...)`)?"

| Cenário | Formato do valor | Exemplo |
|---------|------------------|---------|
| **SIM, só em QSS** | string com unidade: `"12px"`, `"-6px"`, `"999px"`, `"0.3px"`, `"18px"` | `SCROLLBAR_WIDTH = "6px"` |
| **SIM, mas também é lido em Python puro** (QSize, setFixedHeight, effect.setBlurRadius, animation.setDuration) | mantenha numérico, resolva o QSS de outro modo (veja "Casos ambíguos") | `RADIUS_MD = 8` |
| **NÃO é usado em QSS, só em Python** | mantenha numérico | `ANIMATION_FAST = 120` |

### ⚠️ Casos ambíguos: token usado tanto em QSS quanto em Python

Exemplo: `RADIUS_MD = 8` é usado em QSS (`border-radius`) e em `QPainterPath.addRoundedRect()` no paintEvent.

| ❌ NUNCA faça | ✅ Faça |
|--------------|---------|
| `RADIUS_MD = "8px"` — quebra paintEvent que espera `int` | Mantenha `RADIUS_MD = 8` (int). No QSS, `BaseStyle` formata como `f"{t.RADIUS_MD}px"` |
| `FONT_SIZE_NORMAL = 13` + `BaseStyle` concatenar `px` | Faça `FONT_SIZE_NORMAL = "13px"` (string) — só é usado em QSS |

### Checklist prático por família de token

| Família | Ação |
|---------|------|
| `FONT_SIZE_*` | string com px (ex: `"13px"`) |
| `BORDER_RADIUS_*` (toda a família) | string com px, mesmo quando o valor é 0 → `"0px"` |
| `*_LETTER_SPACING`, `LETTER_SPACING_*` | já devem ser string (`"0.3px"`) — confirmar, não deixar número puro |
| `*_PADDING_V`, `*_PADDING_H`, `*_PADDING` (paddings de widgets) | já devem ser string — se algum vier numérico, converter |
| `SCROLLBAR_WIDTH`, `SCROLLBAR_MIN_HEIGHT` | string com px |
| `TAB_CLOSE_BUTTON_SIZE`, `CLOSE_BUTTON_BORDER_RADIUS` | string com px |
| `PROGRESS_BAR_HEIGHT` | string com px |
| `TITLE_BTN_HEIGHT`, `TITLE_BTN_WIDTH`, `TITLE_BTN_FONT_SIZE` | string com px |
| `GROUP_MARGIN_TOP`, `GROUP_TITLE_LEFT`, `GROUP_TITLE_TOP` | string com px (cuidado com negativos: `"-6px"`) |
| `SPLITTER_HANDLE_WIDTH` (e variantes `_H`/`_V`, se usadas em QSS) | string com px |
| `CHECKBOX_SIZE`, `CHECKBOX_SPACING` | string com px |
| `SPINBOX_BTN_WIDTH` | string com px |
| `COMBOBOX_MIN_WIDTH`, `COMBOBOX_DROPDOWN_WIDTH` | string com px |
| `TEXT_EDIT_FONT_SIZE` | string com px |
| `WINDOW_TITLE_FONT_SIZE` | string com px |
| `HEADER_FONT_SIZE` | string com px |
| `CARD_PADDING_V`, `CARD_PADDING_H` | string com px |
| `MENUBAR_ITEM_BORDER_RADIUS`, `GROUP_TITLE_BORDER_RADIUS`, `COMBOBOX_POPUP_BORDER_RADIUS` | string com px |
| `BUTTON_FONT_SIZE_PRIMARY` | string com px |

### Famílias que NÃO devem ser convertidas (manter int/float)

| Família | Motivo |
|---------|--------|
| `ICON_XS/SM/MD/LG/XL` | usados em `QSize(t.ICON_MD, t.ICON_MD)` |
| `TOOLBAR_ICON_SIZE`, `TOOLBAR_BTN_SIZE`, `TOOLBAR_BTN_HOVER_GROW` | `QSize()` / animação hover grow |
| `ANIMATION_FAST/NORMAL/SLOW` | milissegundos, `animation.setDuration(t.ANIMATION_FAST)` |
| `INPUT_HEIGHT`, `BUTTON_HEIGHT`, `BUTTON_HEIGHT_PRIMARY`, `ITEM_HEIGHT`, `TAB_HEIGHT`, `RADIO_SIZE` | `setFixedHeight()` / `QSize()` |
| `RADIUS_XS...RADIUS_FULL`, `SPACE_XXS...SPACE_3XL` | escalas genéricas consumidas em Python (layouts, margins, paintEvent) |
| `OPACITY_*`, `ELEVATION_*` | float/índice sem unidade |
| `SHADOW_BLUR_*`, `GLOW_BLUR`, `GLOW_OFFSET_*`, `SHADOW_OFFSET_Y_*` | `QGraphicsDropShadowEffect` Python puro |
| `SHADOW_COLOR_ALPHA`, `GLOW_ALPHA`, `GLOW_STRONG_ALPHA` | alpha 0-255, sem unidade |
| `FONT_LETTER_SPACING_DISPLAY` | `QFont.setLetterSpacing()` Python puro |
| `BADGE_OUTLINE_BORDER_WIDTH`, `BADGE_OUTLINE_BG_ALPHA` | inteiros sem unidade |
| `BORDER_GRADIENT_WIDTH` | float sem unidade |
| `BUTTON_FONT_WEIGHT_PRIMARY` | inteiro sem unidade |

### Antipadrão: pxpx

**Nunca faça o valor carregar unidade E o BaseStyle concatenar unidade ao mesmo tempo.** É exatamente essa duplicação que gera `pxpx`.

```python
# ❌ ERRADO — gera "12pxpx" no QSS
FONT_SIZE_NORMAL = "12px"    # já tem px
# BaseStyle faz: f"{t.FONT_SIZE_NORMAL}px" → "12pxpx"

# ✅ CERTO — string com px embutido
FONT_SIZE_NORMAL = "12px"    # já tem px
# BaseStyle usa diretamente: t.FONT_SIZE_NORMAL → "12px"

# ✅ CERTO — int puro, BaseStyle formata
RADIUS_MD = 8                # int
# BaseStyle faz: f"{t.RADIUS_MD}px" → "8px"
```

---

## ⚠️ Regras e Boas Práticas

| Regra | Descrição |
|-------|-----------|
| **Contrato 19** | Fora de `resources/styles/`, importe APENAS `AppStyles`. Nunca importe `BaseTheme`, `ThemeManager`, temas concretos ou `ct` diretamente. |
| **Zero hardcoded** | Todo QSS deve usar tokens do tema via `current_theme.ATRIBUTO`. Nunca use cores fixas em stylesheets. |
| **Acesso ao tema via AppStyles** | Widgets que precisam de cores em paintEvent usam `current_theme = AppStyles.current_theme` e depois acessam `current_theme.ACCENT_TEXT`, `current_theme.SURFACE_1`, etc. Esta é a ÚNICA forma de acesso. **Nunca importe** `ThemeManager` ou `ct` diretamente. |
| **Evite metodos-ponte** | Nao crie metodos como `hud_accent_color()` no AppStyles para cada cor que um widget precisa. Se o widget precisa de uma cor em paintEvent, ele usa `AppStyles.current_theme.COR` diretamente. AppStyles expoe apenas **estilos QSS completos** (`log_viewer_table_style()`, `btn_primary_style()`, etc.), nunca cores avulsas. |
| **Nome da variavel** | Use sempre o nome extenso `current_theme`. **Nunca** use variaveis ambiguas como `t` ou `ct`. Isso mantem o codigo legivel e consistente em todo o sistema. |
| **Aliases para legado** | Código antigo pode usar `BG_DARK`, `GOLD`, etc. — eles mapeiam para tokens semânticos. |
| **Tema padrão** | `dark_charcoal` é o tema padrão se não houver preferência salva. |
| **Lazy loading** | Temas são carregados sob demanda — só o módulo do tema ativo é importado. |
| **Compatibilidade** | Ao modificar `BaseTheme`, atualize todos os temas concretos para sobrescrever os novos tokens. |
| **px em tokens QSS** | Tokens usados exclusivamente em QSS devem ser `str` com `px`. Tokens usados em Python puro devem ser `int`/`float`. Tokens usados em ambos devem ser numéricos e o QSS formata com `f"{valor}px"`. |
| **Sem pxpx** | Nunca duplique a unidade. Se o valor já é `"12px"`, o BaseStyle não deve concatenar outro `px`. Se o valor é `12` (int), o BaseStyle formata como `f"{12}px"`. |

## 🧪 Lições Aprendidas (Problemas e Soluções)

### ❌ O que NÃO funciona

1. **Importar `ThemeManager` ou `theme_manager` diretamente em widgets**
   ```python
   # ERRADO — viola Contrato 19
   from resources.styles.ThemeManager import theme_manager
   t = theme_manager.theme
   ```
   **Problema:** Cria acoplamento direto com o ThemeManager. Se o sistema de temas mudar, todo widget que fez isso quebra.

2. **`paintEvent` com QPainter que termina antes do `super().paintEvent()`**
   ```python
   # ERRADO — não funciona
   def paintEvent(self, event):
       painter = QPainter(self)
       painter.setClipPath(path)
       painter.end()  # ← QPainter morre aqui
       super().paintEvent(event)  # ← super() cria OUTRO QPainter, ignorando o clip
   ```
   **Problema:** O `super().paintEvent()` abre seu próprio `QPainter` que ignora qualquer clip configurado anteriormente. O clip só vale dentro do mesmo `QPainter`.

3. **Apenas `setAttribute(Qt.WA_StyledBackground)` sem `paintEvent` custom**
   ```python
   # ERRADO — não arredonda o ícone
   self.setAttribute(Qt.WA_StyledBackground, True)
   ```
   **Problema:** O `QToolButton` no Windows respeita o `border-radius` do QSS no fundo, mas o **ícone** continua sendo desenhado quadrado pelo `QToolButton.paintEvent()` padrão.

4. **`QToolButton` com `border-radius` no QSS sem `WA_StyledBackground`**
   ```python
   # ERRADO — QToolButton no Windows ignora border-radius
   self.setStyleSheet("border-radius: 999px;")
   ```
   **Problema:** No Windows, `QToolButton` não respeita `border-radius` vindo de QSS a menos que `WA_StyledBackground` esteja ativo.

### ✅ O que funciona de verdade

1. **Acessar tema via `AppStyles.current_theme`**
   ```python
   from resources.styles.AppStyles import AppStyles
   
   # ÚNICA forma correta de acessar o tema em widgets
   t = AppStyles.current_theme
   cor_fundo = t.SURFACE_1
   cor_texto = t.TEXT_MEDIUM
   ```
   **Por que funciona:** `AppStyles` já tem `current_theme` como atributo de classe, atualizado automaticamente quando o tema muda. Nenhum import direto do `ThemeManager`.

2. **Arredondar QToolButton com ícone (paintEvent completo manual)**
   ```python
   def paintEvent(self, event):
       """Pintura completa com clip arredondado no fundo e no ícone."""
       painter = QPainter(self)
       painter.setRenderHint(QPainter.RenderHint.Antialiasing)
       painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
       
       # Clip arredondado
       radius = AppStyles.toolbar_btn_border_radius()
       path = QPainterPath()
       path.addRoundedRect(QRectF(self.rect()), radius, radius)
       painter.setClipPath(path)
       
       # Background hover/pressed
       t = AppStyles.current_theme
       if self.isDown():
           painter.fillRect(self.rect(), QColor(t.SURFACE_2))
       elif self.underMouse():
           painter.fillRect(self.rect(), QColor(t.SURFACE_4))
       
       # Ícone (também arredondado pelo clip)
       icon = self.icon()
       if not icon.isNull():
           icon_sz = self.iconSize()
           x = (self.width() - icon_sz.width()) // 2
           y = (self.height() - icon_sz.height()) // 2
           icon.paint(painter, QRect(x, y, icon_sz.width(), icon_sz.height()))
       
       painter.end()  # ← NÃO chama super().paintEvent()!
   ```
   **Por que funciona:** Faz a pintura COMPLETA manualmente com um único `QPainter`. O clip path arredondado afeta tanto o fundo quanto o ícone. Não chama `super().paintEvent()`.

3. **`setAttribute(Qt.WA_StyledBackground, True)` + `paintEvent` custom**
   ```python
   # No __init__:
   self.setAttribute(Qt.WA_StyledBackground, True)
   self.setStyleSheet(AppStyles.toolbar_btn_style())
   
   # No paintEvent: pintura manual com clip (como acima)
   ```
   **Por que funciona:** `WA_StyledBackground` força o `QToolButton` a respeitar o QSS no Windows, e o `paintEvent` manual garante que o ícone também seja arredondado.

4. **`BORDER_RADIUS_TOOLBAR_BTN = "999px"` para pill total**
   ```python
   # No tema concreto (ex: PearlWhiteTheme.py):
   BORDER_RADIUS_TOOLBAR_BTN = "999px"  # pill / totalmente redondo
   ```
   **Por que funciona:** O valor `999px` é maior que qualquer tamanho de botão, então o Qt interpreta como "totalmente arredondado" (pill shape).

### 🔍 Checklist para widgets com paintEvent custom

- [ ] Usei `AppStyles.current_theme` (NUNCA `theme_manager.theme` ou `ct.theme`)?
- [ ] O `QPainter` é criado e finalizado DENTRO do `paintEvent`, sem chamar `super().paintEvent()` depois?
- [ ] O clip path com `addRoundedRect` é aplicado ANTES de pintar qualquer coisa?
- [ ] Usei `setAttribute(Qt.WA_StyledBackground, True)` no `__init__` se for `QToolButton`?
- [ ] O `border-radius` vem de um token do tema (ex: `BORDER_RADIUS_TOOLBAR_BTN`), nunca hardcoded?
- [ ] Importei apenas `AppStyles` (nunca `ThemeManager`, `BaseTheme` ou `ct`)?

---

## 🆕 Sistema de Tipos de Gradiente (GradientType)

### `core/enum/GradientType.py`

Enum que define os tipos de gradiente disponíveis:

| Valor | QSS gerado | Descrição |
|-------|-----------|-----------|
| `GradientType.LINEAR` | `qlineargradient(x1,y1,x2,y2, stop:...)` | Gradiente linear entre dois pontos (padrão) |
| `GradientType.RADIAL` | `qradialgradient(cx,cy,radius,fx,fy, stop:...)` | Gradiente radial com centro e ponto focal |
| `GradientType.CONICAL` | `qconicalgradient(cx,cy,angle, stop:...)` | Gradiente cônico em torno de um centro |

### Novos tokens no `BaseTheme`

| Token | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `GRADIENT_ACCENT_TYPE` | `GradientType \| None` | `None` (=LINEAR) | Tipo de gradiente para botões primários e progress bars |
| `GRADIENT_ACCENT_STOPS` | `tuple` | `()` | Stops multi-stop para gradiente de acento |
| `GRADIENT_ACCENT_ANGLE` | `int` | `45` | Ângulo do gradiente linear de acento |
| `GRADIENT_BUTTON_TYPE` | `GradientType \| None` | `None` (=LINEAR) | Tipo de gradiente para botões secundários |
| `GRADIENT_BUTTON_STOPS` | `tuple` | `()` | Stops multi-stop para botões secundários |
| `GRADIENT_BUTTON_ANGLE` | `int` | `45` | Ângulo do gradiente de botão secundário |
| `GRADIENT_TAB_TYPE` | `GradientType \| None` | `None` (=LINEAR) | Tipo de gradiente para fundo de tabs |
| `GRADIENT_TAB_STOPS` | `tuple` | `()` | Stops multi-stop para tabs |
| `GRADIENT_TAB_ANGLE` | `int` | `45` | Ângulo do gradiente de tabs |
| `GLOW_BUTTON_ENABLED` | `bool` | `False` | Ativa glow em botões secundários |
| `GLOW_TAB_ENABLED` | `bool` | `False` | Ativa glow em tabs selecionadas |
| `GRADIENT_RADIAL_CX` | `float` | `0.5` | Centro X do gradiente radial (0.0–1.0) |
| `GRADIENT_RADIAL_CY` | `float` | `0.5` | Centro Y do gradiente radial |
| `GRADIENT_RADIAL_FX` | `float` | `0.5` | Ponto focal X do gradiente radial |
| `GRADIENT_RADIAL_FY` | `float` | `0.5` | Ponto focal Y do gradiente radial |
| `GRADIENT_RADIAL_RADIUS` | `float` | `0.5` | Raio do gradiente radial |
| `GRADIENT_CONICAL_CX` | `float` | `0.5` | Centro X do gradiente cônico |
| `GRADIENT_CONICAL_CY` | `float` | `0.5` | Centro Y do gradiente cônico |
| `GRADIENT_CONICAL_ANGLE` | `float` | `0.0` | Ângulo inicial do gradiente cônico |

### Métodos helpers no `BaseStyle`

| Método | Descrição |
|--------|-----------|
| `_gradient_qss_from_stops(stops, angle, fallback_start, fallback_end, gradient_type, cx, cy, fx, fy, radius)` | Gera string QSS para qualquer tipo de gradiente |
| `_build_linear_gradient(stops, angle, rect_w, rect_h)` | Constrói `QLinearGradient` para paintEvent |
| `_build_radial_gradient(stops, cx, cy, fx, fy, radius, rect_w, rect_h)` | Constrói `QRadialGradient` para paintEvent |
| `_build_conical_gradient(stops, cx, cy, angle, rect_w, rect_h)` | Constrói `QConicalGradient` para paintEvent |
| `_border_gradient_pen(stops, width, angle, rect_w, rect_h, fallback)` | Cria `QPen` com borda gradiente (efeito foil) |
| `apply_drop_shadow(widget, blur, offset_x, offset_y, color_rgb, alpha)` | Aplica `QGraphicsDropShadowEffect` programático |

### Exemplo: Tema com gradiente RADIAL e glow

```python
from core.enum.GradientType import GradientType
from resources.styles.BaseTheme import BaseTheme

class MeuTemaPremium(BaseTheme):
    # Gradiente radial dourado para botões primários
    GRADIENT_ACCENT_TYPE = GradientType.RADIAL
    GRADIENT_ACCENT_STOPS = (
        (0.00, "#A08020"),
        (0.35, "#D4AF37"),
        (0.55, "#F5E6A3"),
        (0.80, "#D4AF37"),
        (1.00, "#8A6A10"),
    )
    GRADIENT_RADIAL_CX = 0.5
    GRADIENT_RADIAL_CY = 0.5
    GRADIENT_RADIAL_FX = 0.5
    GRADIENT_RADIAL_FY = 0.3
    GRADIENT_RADIAL_RADIUS = 0.6

    # Gradiente radial sutil para botões secundários
    GRADIENT_BUTTON_TYPE = GradientType.RADIAL
    GRADIENT_BUTTON_STOPS = (
        (0.00, "#1C1C17"),
        (0.50, "#2A2A22"),
        (1.00, "#0A0A08"),
    )

    # Glow ativado
    GLOW_BUTTON_ENABLED = True
    GLOW_TAB_ENABLED = True
    GLOW_BLUR = 12
    GLOW_ALPHA = 60
    GLOW_COLOR_RGB = "#D4AF37"
```

### Comportamento dos widgets com gradiente e glow

| Widget | Gradiente (QSS/paintEvent) | Glow |
|--------|---------------------------|------|
| `SimplePrimaryButton` | Usa `GRADIENT_ACCENT_TYPE` + `GRADIENT_ACCENT_STOPS` via QSS | `QGraphicsDropShadowEffect` se `GLOW_BLUR>0` |
| `SimpleSecondaryButton` | Usa `GRADIENT_BUTTON_TYPE` + `GRADIENT_BUTTON_STOPS` via QSS | `QGraphicsDropShadowEffect` se `GLOW_BUTTON_ENABLED` |
| `VerticalTab` | Usa `GRADIENT_TAB_STOPS` no paintEvent (default/hovered) | Borda glow em selected se `GLOW_TAB_ENABLED` |
| `HorizontalTab` | Usa `GRADIENT_TAB_STOPS` no paintEvent (default/hovered) | Borda glow em selected se `GLOW_TAB_ENABLED` |

### Fallback automático

- Se `GRADIENT_ACCENT_STOPS` estiver vazio → usa `ACCENT_GRADIENT` (2 stops, comportamento original)
- Se `GRADIENT_BUTTON_STOPS` estiver vazio → usa `GRADIENT_BUTTON` (2 stops, comportamento original)
- Se `GRADIENT_TAB_STOPS` estiver vazio → usa `GRADIENT_TAB` (2 stops, comportamento original)
- Se `GLOW_BUTTON_ENABLED` for `False` → nenhum glow é aplicado
- Se `GRADIENT_ACCENT_TYPE` for `None` → comporta-se como `GradientType.LINEAR`

---

## ✅ Checklist ao criar novo tema

- [ ] A classe herda de `BaseTheme`?
- [ ] Todos os 18 grupos de tokens foram sobrescritos?
- [ ] Os aliases de compatibilidade (BG_*, GOLD*, etc.) foram mapeados?
- [ ] O tema foi registrado no dicionário `THEMES` do `ThemeManager`?
- [ ] O módulo foi adicionado ao `__init__.py` de `resources/styles/`?
- [ ] Esta skill foi atualizada com o novo tema?
- [ ] Tokens de QSS (FONT_SIZE_*, BORDER_RADIUS_*, SCROLLBAR_WIDTH, etc.) são string com `px`?
- [ ] Tokens de Python puro (ICON_*, ANIMATION_*, INPUT_HEIGHT, etc.) são int/float?
- [ ] Tokens usados em ambos (RADIUS_*, SPACE_*) são int (o QSS formata com `f"{valor}px"`)?
- [ ] **(Opcional)** Definir `GRADIENT_ACCENT_TYPE`/`GRADIENT_BUTTON_TYPE`/`GRADIENT_TAB_TYPE` para gradientes customizados?
- [ ] **(Opcional)** Ativar `GLOW_BUTTON_ENABLED`/`GLOW_TAB_ENABLED` para efeito de brilho?

## ✅ Checklist ao usar estilos em widget

- [ ] Usei `AppStyles.método()` em vez de escrever QSS manual com cores fixas?
- [ ] Para paintEvent, usei `current_theme = AppStyles.current_theme` + tokens diretos (ex: `current_theme.SURFACE_0`, `current_theme.ACCENT_TEXT`)?
- [ ] **Evitei** usar `AppStyles.theme_colors()` — é um dicionario legado com aliases GOLD que gera acoplamento. Use `current_theme.COR` diretamente.
- [ ] Para logs HTML, usei `AppStyles.log_html()`?
- [ ] Para badges, usei `AppStyles.badge_*()`?
- [ ] Para botões, usei `AppStyles.btn_*_style()`?
- [ ] Importei apenas `AppStyles` (nunca `BaseTheme`, `ThemeManager` ou `ct` diretamente)?
- [ ] Usei nome extenso `current_theme` (nunca `t`, `ct` ou variavel ambigua)?
- [ ] **(Widgets custom)** Se o widget usa gradiente em paintEvent, ele consulta `GRADIENT_*_STOPS` do tema?
- [ ] **Nao criei** metodos-ponte no AppStyles para cores avulsas? AppStyles só deve expor estilos QSS completos.
- [ ] **Tokens numéricos no QSS**: Se o token é `int` (ex: `RADIUS_MD = 8`), o QSS deve formatar como `f"{valor}px"`. Se o token já é `str` com `px`, usar direto.

---

## 🔗 Referências

- `core/enum/GradientType.py` — Enum com tipos de gradiente (LINEAR, RADIAL, CONICAL)
- `docs/skills/SKILL_PLUGIN_CONTRACT.md` — Contrato 19 (importação de estilos)
- `docs/skills/SKILL_WIDGETS.md` — Widgets que usam estilos do AppStyles
- `resources/styles/BaseTheme.py` — Definição completa de todos os tokens
- `resources/styles/BaseStyle.py` — Helpers de gradiente e sombra
- `resources/styles/ThemeManager.py` — Gerenciamento de temas e preferências
- `resources/styles/GoldPremiumTheme.py` — Tema de exemplo com RADIAL + glow
- `resources/widgets/simple/SimplePrimaryButton.py` — Botão primário com glow
- `resources/widgets/simple/SimpleSecondaryButton.py` — Botão secundário com glow
- `resources/widgets/VerticalTab.py` — Aba vertical com gradiente + glow
- `resources/widgets/HorizontalTab.py` — Aba horizontal com gradiente + glow