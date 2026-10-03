# -*- coding: utf-8 -*-
"""
BaseTheme — Classe base abstrata para temas do Aetheris ToolBox
================================================================
Define TODAS as variáveis de tema organizadas em grupos semânticos.

Cada tema concreto (ex: DarkCharcoalTheme, ModernBlueTheme) deve
sobrescrever todos os atributos com valores concretos.

Grupos de tokens semânticos (organizados por categoria):
    1.  ACCENT       — Cores de destaque principal
    2.  SURFACE      — Níveis de profundidade (0=fundo … 5=topo)
    3.  TEXT         — Hierarquia tipográfica
    4.  BORDER       — Hierarquia de bordas
    5.  SHADOW       — Sombras por tamanho
    6.  RADIUS       — Escala global de cantos arredondados (int, usado em Python e QSS com f"{v}px")
    7.  SPACE        — Escala global de espaçamento (int, usado em Python e QSS com f"{v}px")
    8.  ICON         — Tamanhos de ícone (int, usado em QSize)
    9.  ANIMATION    — Durações de animação (int ms) + easing
    10. OPACITY      — Níveis de opacidade (float 0.0–1.0)
    11. LAYOUT       — Layout global (int, padding, gap, max-width)
    12. ELEVATION    — Níveis de elevação (int, z-index conceitual)
    13. OVERLAY      — Sobreposições / glass effect
    14. FOCUS_RING   — Anel de foco visual
    15. STATUS       — Cores de estado (success, warning, danger, info)
    16. FONT         — Tipografia (famílias, tamanhos str c/ px, pesos int)
    17. DIMENSIONS   — Alturas e tamanhos de widgets (int para Python, str c/ px para QSS)
    18. GRADIENT     — Configurações de gradiente multi-stop, tipo e ângulo
    19. SPECIFICS    — Tokens específicos de implementação (str c/ px para QSS, int para Python)

    Aliases de compatibilidade retroativa (mapeiam nomes antigos → semânticos)

    ═══════════════════════════════════════════════════════════════
    REGRA DE TIPOS:
    - str com "px":  usado APENAS em QSS (ex: FONT_SIZE_NORMAL, BORDER_RADIUS_CARD)
    - int:           usado em Python puro (ex: ICON_MD → QSize, ANIMATION_FAST → setDuration)
    - int (ambíguo): usado tanto em QSS quanto em Python (ex: RADIUS_MD → paintEvent + QSS com f"{v}px")
    ═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from typing import Any


class BaseTheme:
    """Classe base abstrata para temas. Todos os atributos devem ser sobrescritos
    pelos temas concretos.

    Attributes:
        ── ACCENT ───────────────────────────────────────────
        ACCENT: Cor principal de destaque (botões, links, seleção).
        ACCENT_HOVER: Hover / foco do accent.
        ACCENT_ACTIVE: Estado pressed / ativo.
        ACCENT_DIM: Versão escurecida / muted do accent.
        ACCENT_LIGHT: Versão clara (badges, highlights sutis).
        ACCENT_SOFT: Versão translucent rgba para backgrounds.
        ACCENT_TEXT: Cor para texto sobre superfície escura com accent.
        ACCENT_BRIGHT: Versão brilhante (glow, hover highlight).
        ACCENT_GRADIENT: Par (start, stop) para gradientes lineares.

        ── SURFACE ─────────────────────────────────────────
        SURFACE_0: Fundo absoluto (backdrop), profundidade 0.
        SURFACE_1: Fundo padrão da janela, profundidade 1.
        SURFACE_2: Painéis base / side panels, profundidade 2.
        SURFACE_3: Cards / groupbox / áreas elevadas, profundidade 3.
        SURFACE_4: Inputs, tabelas, elementos interativos, profundidade 4.
        SURFACE_5: Superfície hover / focus, profundidade 5.
        TITLE_BAR: Cor de fundo da barra de título da janela.

        ── TEXT ────────────────────────────────────────────
        TEXT_HIGH: Títulos, labels de alta importância.
        TEXT_MEDIUM: Corpo padrão, texto principal.
        TEXT_LOW: Secundário, metadados, texto auxiliar.
        TEXT_DISABLED: Widget desabilitado, baixo contraste.
        TEXT_ON_ACCENT: Texto sobre fundo ACCENT.
        TEXT_ON_DANGER: Texto sobre fundo danger (close btn, btn_danger).

        ── BORDER ──────────────────────────────────────────
        BORDER_SUBTLE: Linhas muito sutis (divisores leves).
        BORDER_DEFAULT: Borda padrão de widgets.
        BORDER_STRONG: Borda de destaque (foco, validação).
        BORDER_ACCENT: Borda com cor de acento.
        DIVIDER: Separadores (linhas horizontais/verticais).
        BORDER_GRADIENT_STOPS: Stops para borda gradiente ("efeito foil").
        BORDER_GRADIENT_WIDTH: Largura da borda gradiente.

        ── SHADOW ──────────────────────────────────────────
        SHADOW_SM: Sombra pequena (string com tom/alpha).
        SHADOW_MD: Sombra média (string com tom/alpha).
        SHADOW_LG: Sombra grande (string com tom/alpha).
        SHADOW_XL: Sombra extra grande (string com tom/alpha).
        SHADOW_ACCENT: Sombra com cor de acento (glow em string).
        GLOW: Brilho sutil (string cor+alpha).
        GLOW_STRONG: Brilho forte (string cor+alpha).
        SHADOW_BLUR_SM/MD/LG/XL: Blur radius int para drop shadow.
        SHADOW_OFFSET_Y_SM/MD/LG: Offset vertical da sombra (int px).
        SHADOW_COLOR_RGB: Cor base da sombra sem alfa (#RRGGBB).
        SHADOW_COLOR_ALPHA: Alfa da sombra (int 0-255).
        GLOW_BLUR: Blur radius do glow (int px).
        GLOW_OFFSET_X/Y: Offset do glow (int px).
        GLOW_COLOR_RGB: Cor do glow (#RRGGBB). Vazio = usa ACCENT.
        GLOW_ALPHA: Alfa do glow (int 0-255).
        GLOW_STRONG_BLUR/ALPHA: Blur e alfa do glow forte.

        ── RADIUS ──────────────────────────────────────────
        RADIUS_XS/MD/LG/XL/FULL: int (usado em paintEvent e QSS com f"{v}px").

        ── SPACE ───────────────────────────────────────────
        SPACE_XXS/XS/SM/MD/LG/XL/2XL/3XL: int (usado em layouts Python e QSS com f"{v}px").

        ── ICON ────────────────────────────────────────────
        ICON_XS/SM/MD/LG/XL, TOOLBAR_ICON_SIZE: int (usado em QSize).

        ── ANIMATION ───────────────────────────────────────
        ANIMATION_FAST/NORMAL/SLOW: int ms. EASING_STANDARD: str.

        ── OPACITY ─────────────────────────────────────────
        OPACITY_DISABLED/MUTED/HOVER/ACTIVE: float 0.0-1.0.

        ── LAYOUT ──────────────────────────────────────────
        PAGE_PADDING, SECTION_GAP, GRID_GAP, CONTENT_MAX_WIDTH: int px.

        ── ELEVATION ───────────────────────────────────────
        ELEVATION_FLAT/LOW/MEDIUM/HIGH: int (z-index).

        ── OVERLAY ─────────────────────────────────────────
        OVERLAY_BG: str rgba. BACKDROP_BLUR: str com px.

        ── FOCUS_RING ──────────────────────────────────────
        FOCUS_RING_COLOR: str. FOCUS_RING_WIDTH/OFFSET: str com px.

        ── STATUS ──────────────────────────────────────────
        COLOR_SUCCESS/WARNING/DANGER/INFO e variantes: str cor.

        ── FONT ────────────────────────────────────────────
        FONT_FAMILY_*: str. FONT_SIZE_*: str com px (QSS).
        FONT_WEIGHT_*: int. FONT_LETTER_SPACING_DISPLAY: int (QFont Python).

        ── DIMENSIONS ──────────────────────────────────────
        INPUT_HEIGHT, BUTTON_HEIGHT, ITEM_HEIGHT, TAB_HEIGHT, RADIO_SIZE: int (setFixedHeight/QSize).
        CHECKBOX_SIZE, SCROLLBAR_WIDTH, SCROLLBAR_MIN_HEIGHT, TAB_CLOSE_BUTTON_SIZE: str com px (QSS).
        CLOSE_BUTTON_BORDER_RADIUS, PROGRESS_BAR_HEIGHT: str com px (QSS).
        TITLE_BTN_HEIGHT, TITLE_BTN_WIDTH, TITLE_BTN_FONT_SIZE: str com px (QSS).
        TOOLBAR_BTN_SIZE, TOOLBAR_BTN_HOVER_GROW: int (QSize/animacão).
        GROUP_MARGIN_TOP, SPLITTER_HANDLE_WIDTH: str com px (QSS).

        ── SPECIFICS (border radius) ───────────────────────
        BORDER_RADIUS_*: str com px (QSS). MENUBAR_ITEM_BORDER_RADIUS: str com px.

        ── SPECIFICS (checkbox) ────────────────────────────
        CHECKBOX_BORDER_WIDTH: int. CHECKBOX_SPACING: str com px.

        ── SPECIFICS (badge) ───────────────────────────────
        BADGE_PADDING_*, BADGE_LETTER_SPACING: str com px.

        ── SPECIFICS (button) ──────────────────────────────
        BUTTON_PADDING_*, BUTTON_LETTER_SPACING_*: str com px.
        BUTTON_FONT_SIZE_PRIMARY: str com px. BUTTON_FONT_WEIGHT_PRIMARY: int.

        ── SPECIFICS (toolbar/tool selector/input) ─────────
        TOOLBAR_BTN_PADDING_*, TOOL_SELECTOR_PADDING_*, INPUT_PADDING_*: str com px.

        ── SPECIFICS (spinbox) ─────────────────────────────
        SPINBOX_PADDING, SPINBOX_BTN_MARGIN: str com px. SPINBOX_BTN_WIDTH: str com px.

        ── SPECIFICS (combobox) ────────────────────────────
        COMBOBOX_PADDING, COMBOBOX_ARROW_SIZE: str com px.
        COMBOBOX_MIN_WIDTH, COMBOBOX_DROPDOWN_WIDTH: str com px.
        COMBOBOX_POPUP_BORDER_RADIUS: str com px.

        ── SPECIFICS (text edit) ───────────────────────────
        TEXT_EDIT_PADDING: str com px. TEXT_EDIT_FONT_SIZE: str com px.

        ── SPECIFICS (groupbox) ────────────────────────────
        GROUP_TITLE_LEFT, GROUP_TITLE_TOP, GROUP_TITLE_BORDER_RADIUS: str com px.
        GROUP_TITLE_PADDING, GROUP_TITLE_LETTER_SPACING: str com px.

        ── SPECIFICS (letter spacing) ──────────────────────
        LETTER_SPACING_*: str com px.

        ── SPECIFICS (window title) ────────────────────────
        WINDOW_TITLE_FONT_SIZE: str com px. WINDOW_TITLE_LETTER_SPACING: str com px.

        ── SPECIFICS (title bar) ───────────────────────────
        TITLE_BAR_BORDER_WIDTH: str com px. TITLE_BAR_BORDER_COLOR: str.

        ── SPECIFICS (card) ────────────────────────────────
        CARD_PADDING_V, CARD_PADDING_H: str com px.

        ── SPECIFICS (splitter) ────────────────────────────
        SPLITTER_HANDLE_WIDTH_H, SPLITTER_HANDLE_WIDTH_V: str com px.

        ── SPECIFICS (menu) ────────────────────────────────
        MENU_PADDING, MENU_MARGIN_V, MENU_ITEM_PADDING, MENU_SEPARATOR_HEIGHT/MARGIN: str com px.

        ── SPECIFICS (table) ───────────────────────────────
        HEADER_FONT_SIZE: str com px. HEADER_LETTER_SPACING: str com px.
        TABLE_ITEM_PADDING, HEADER_PADDING: str com px.

        ── GRADIENT CONFIG ─────────────────────────────────
        GRADIENT_BUTTON/PANEL/TAB/INPUT: tuple[str,str].
        GRADIENT_ACCENT/BUTTON/TAB_TYPE/STOPS/ANGLE: multi-stop config.
        GLOW_BUTTON_ENABLED, GLOW_TAB_ENABLED: bool.
        GRADIENT_RADIAL_*, GRADIENT_CONICAL_*: float.

        ── ALIASES DE COMPATIBILIDADE ──────────────────────
        BG_DEEPEST/DARK/PANEL/CARD/ELEVATED/SURFACE: str → SURFACE_*.
        TITLE_BAR_BG: str → TITLE_BAR.
        SHADOW/SHADOW_DEEP: str → SHADOW_SM/LG.
        BORDER/BORDER_HOVER: str → BORDER_DEFAULT/ACCENT.
        TEXT_BRIGHT/PRIMARY/SECONDARY/MUTED: str → TEXT_*.
        TEXT_ACCENT/ACCENT_BRIGHT: str → ACCENT_TEXT/BRIGHT.
        ACCENT_COLOR_*: str → ACCENT_*.
        SUCCESS/WARNING/DANGER_*: str → COLOR_*.
    """

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Cores de destaque principal
    # ═══════════════════════════════════════════════════════════════════

    ACCENT: str = ""
    """FUNDO de botões primários e links ativos.
    Cor principal de destaque da interface.
    Usado em: botão primário, links clicáveis, indicador de tab selecionada, checkbox marcado."""

    ACCENT_HOVER: str = ""
    """FUNDO de botão primário quando o mouse passa por cima (hover).
    Tom mais claro que ACCENT para feedback visual."""

    ACCENT_ACTIVE: str = ""
    """FUNDO de botão primário quando está sendo pressionado (click).
    Tom mais escuro que ACCENT para simular profundidade."""

    ACCENT_DIM: str = ""
    """BORDA e INDICADOR de elementos de acento em estado desabilitado ou muted.
    Usado como borda de tab selecionada, versão menos chamativa do accent."""

    ACCENT_LIGHT: str = ""
    """FUNDO de badges e highlights sutis.
    Versão clara do accent para elementos que precisam de destaque discreto."""

    ACCENT_SOFT: str = ""
    """FUNDO translúcido para hover e backgrounds de elementos com accent.
    Usa rgba para criar uma camada suave sobre superfícies escuras.
    Usado em: badge outline (fundo translúcido), overlay sutil."""

    ACCENT_TEXT: str = ""
    """COR do TEXTO que fica sobre fundo escuro com detalhes em accent.
    Usado em: labels de tool group, textos de botões ghost, títulos de groupbox."""

    ACCENT_BRIGHT: str = ""
    """COR de GLOW e HOVER highlight para textos sobre accent.
    Versão mais clara e brilhante do ACCENT_TEXT.
    Usado em: hover de botões secundários e ghost para efeito de iluminação."""

    ACCENT_GRADIENT: tuple[str, str] = ("", "")
    """GRADIENTE LINEAR de 2 cores para fundo de botões primários.
    Par (cor_inicio, cor_fim) — gradiente top-left → bottom-right."""

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Níveis de profundidade (0 = mais fundo, 5 = mais alto)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0: str = ""
    """FUNDO mais profundo da hierarquia (backdrop/absoluto).
    Aparece em: fundo atrás de modais (fora do dialog), menus dropdown,
    fundo de áreas que precisam parecer 'cavadas' na tela."""

    SURFACE_1: str = ""
    """FUNDO padrão da janela principal (nível base).
    Cor principal de fundo da aplicação — a maior área visual."""

    SURFACE_2: str = ""
    """FUNDO de painéis laterais e barras secundárias.
    Usado em: side panels, console toolbar, tool panels.
    Um nível acima do fundo da janela para criar contraste sutil."""

    SURFACE_3: str = ""
    """FUNDO de cards, groupbox e áreas elevadas.
    Elementos que precisam parecer 'flutuando' sobre a superfície base.
    Usado em: cartões de conteúdo, QGroupBox, botão ghost hover."""

    SURFACE_4: str = ""
    """FUNDO de inputs, tabelas e elementos interativos.
    Áreas onde o usuário interage diretamente: campos de texto,
    combobox, spinbox, células de tabela, checkbox indicator."""

    SURFACE_5: str = ""
    """FUNDO de hover/focus em elementos interativos.
    Usado quando o mouse passa sobre inputs, botões com hover,
    e quando um campo recebe foco do teclado."""

    TITLE_BAR: str = ""
    """FUNDO da barra de título da janela (topo).
    Também usado como fundo da barra de menus principal."""

    # ── Gradientes de superfície (top-left → bottom-right) ─────

    GRADIENT_BUTTON: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para botões secundários e ghost.
    Par (cor_inicio, cor_fim) — gradiente sutil top-left → bottom-right."""

    GRADIENT_PANEL: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para side panels e tool panels.
    Aplicado em QWidget#tool_side_panel e QGroupBox."""

    GRADIENT_TAB: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para tabs NÃO selecionadas.
    Aplicado em QTabBar::tab."""

    GRADIENT_INPUT: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para inputs, combobox e spinbox.
    Aplicado em QLineEdit, QComboBox, QSpinBox."""

    # ── Gradiente rico (3+ stops) ──

    GRADIENT_ACCENT_TYPE: "GradientType" = None
    """TIPO de gradiente para elementos de acento (botão primário).
    Valores: GradientType.LINEAR (padrão), RADIAL, CONICAL.
    None = usa LINEAR para compatibilidade.
    ⚠ CONICAL só funciona em paintEvent custom, NÃO em QSS."""

    GRADIENT_ACCENT_STOPS: tuple = ()
    """STOPS multi-cor para gradiente de botão primário.
    Tupla de (posição_float 0.0-1.0, cor_hex) ordenada.
    Vazio = usa ACCENT_GRADIENT (2 stops) como fallback."""

    GRADIENT_ACCENT_ANGLE: int = 45
    """ÂNGULO do gradiente linear de acento em graus.
    0 = left→right, 45 = top-left→bottom-right, 90 = top→bottom."""

    GRADIENT_BUTTON_TYPE: "GradientType" = None
    """TIPO de gradiente para botões secundários.
    None = usa GRADIENT_BUTTON (2-stop) compatibilidade.
    ⚠ CONICAL só funciona em paintEvent custom."""

    GRADIENT_BUTTON_STOPS: tuple = ()
    """STOPS multi-cor para gradiente de botão secundário.
    Formato: (pos_float, cor_hex). Vazio = usa GRADIENT_BUTTON."""

    GRADIENT_BUTTON_ANGLE: int = 45
    """ÂNGULO do gradiente de botão secundário em graus."""

    GRADIENT_TAB_TYPE: "GradientType" = None
    """TIPO de gradiente para fundo de tabs.
    None = usa GRADIENT_TAB (2-stop). ⚠ CONICAL apenas paintEvent."""

    GRADIENT_TAB_STOPS: tuple = ()
    """STOPS multi-cor para gradiente de fundo de tabs.
    Vazio = usa GRADIENT_TAB (2-stop)."""

    GRADIENT_TAB_ANGLE: int = 45
    """ÂNGULO do gradiente de tabs em graus."""

    GLOW_BUTTON_ENABLED: bool = False
    """ATIVA/DESATIVA o efeito de brilho (QGraphicsDropShadowEffect)
    em botões secundários quando o mouse passa por cima.
    True = botões secundários ganham glow suave no hover."""

    GLOW_TAB_ENABLED: bool = False
    """ATIVA/DESATIVA o efeito de borda brilhante em tabs selecionadas.
    True = tab selecionada ganha brilho extra na borda inferior."""

    GRADIENT_RADIAL_CX: float = 0.5
    """Centro X do gradiente radial (0.0=esquerda, 0.5=centro, 1.0=direita)."""

    GRADIENT_RADIAL_CY: float = 0.5
    """Centro Y do gradiente radial (0.0=topo, 0.5=centro, 1.0=base)."""

    GRADIENT_RADIAL_FX: float = 0.5
    """Ponto focal X do gradiente radial — onde a cor começa a irradiar."""

    GRADIENT_RADIAL_FY: float = 0.5
    """Ponto focal Y do gradiente radial."""

    GRADIENT_RADIAL_RADIUS: float = 0.5
    """RAIO do gradiente radial (0.0=apenas centro, 1.0=toda a área)."""

    GRADIENT_CONICAL_CX: float = 0.5
    """Centro X do gradiente cônico (0.0-1.0). Apenas para paintEvent."""

    GRADIENT_CONICAL_CY: float = 0.5
    """Centro Y do gradiente cônico (0.0-1.0). Apenas para paintEvent."""

    GRADIENT_CONICAL_ANGLE: float = 0.0
    """Ângulo inicial do gradiente cônico em graus. Apenas para paintEvent."""

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia de texto
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH: str = ""
    """COR do TEXTO para títulos e labels de alta importância.
    Usado em: header_title (título de seção), texto de tab default."""

    TEXT_MEDIUM: str = ""
    """COR do TEXTO para corpo padrão e texto principal.
    Usado em: labels comuns, parágrafos, itens de menu, células de tabela."""

    TEXT_LOW: str = ""
    """COR do TEXTO para metadados, texto auxiliar e secundário.
    Usado em: subtítulos, itens de menu inativos, texto de header de tabela."""

    TEXT_DISABLED: str = ""
    """COR do TEXTO para widgets desabilitados (baixo contraste).
    Usado em: botões desabilitados, inputs desabilitados, labels inativas."""

    TEXT_ON_ACCENT: str = ""
    """COR do TEXTO que fica SOBRE o fundo ACCENT (botão primário).
    Deve ter alto contraste com ACCENT."""

    TEXT_ON_DANGER: str = ""
    """COR do TEXTO que fica SOBRE o fundo COLOR_DANGER.
    Usado em: botão fechar (title_btn_close), botão danger."""

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia de bordas
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE: str = ""
    """BORDA muito sutil para divisores leves.
    Usado em: linhas de separação discretas, bar_border no GridPercentView."""

    BORDER_DEFAULT: str = ""
    """BORDA padrão da maioria dos widgets.
    Usado em: QMenu, QDialog, QGroupBox borda, separador workspace."""

    BORDER_STRONG: str = ""
    """BORDA de destaque — foco, validação, hover forte.
    Usado em: elementos que precisam de borda mais visível."""

    BORDER_ACCENT: str = ""
    """BORDA com cor de acento para hover em elementos interativos.
    Usado em: hover de tabs (borda), hover de itens de menu."""

    DIVIDER: str = ""
    """LINHAS SEPARADORAS (horizontais/verticais) entre seções.
    Usado em: separador de menu, gridline-color de tabela, divisor de toolbar."""

    BORDER_GRADIENT_STOPS: tuple = ()
    """STOPS para borda em GRADIENTE ('efeito foil').
    Tupla de (pos_float, cor_hex). Vazio = desligado (borda sólida)."""

    BORDER_GRADIENT_WIDTH: float = 1.0
    """LARGURA da borda gradiente em pixels."""

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM: str = ""
    """SOMBRA PEQUENA — string com cor+alpha para QSS.
    Usado em widgets que precisam de sombra sutil via box-shadow CSS."""

    SHADOW_MD: str = ""
    """SOMBRA MÉDIA — string cor+alpha para QSS."""

    SHADOW_LG: str = ""
    """SOMBRA GRANDE — string cor+alpha para QSS."""

    SHADOW_XL: str = ""
    """SOMBRA EXTRA GRANDE — string cor+alpha para QSS."""

    SHADOW_ACCENT: str = ""
    """SOMBRA com COR DE ACENTO para glow em QSS.
    Efeito de brilho ao redor de elementos de acento."""

    GLOW: str = ""
    """BRILHO SUTIL — string cor+alpha para glow em QSS.
    Efeito de iluminação suave ao redor de elementos."""

    GLOW_STRONG: str = ""
    """BRILHO FORTE — string cor+alpha para glow intenso em QSS."""

    SHADOW_BLUR_SM: int = 0
    """DESFOQUE da sombra pequena em pixels para QGraphicsDropShadowEffect (int Python)."""

    SHADOW_BLUR_MD: int = 0
    """DESFOQUE da sombra média em pixels para QGraphicsDropShadowEffect (int Python)."""

    SHADOW_BLUR_LG: int = 0
    """DESFOQUE da sombra grande em pixels para QGraphicsDropShadowEffect (int Python)."""

    SHADOW_BLUR_XL: int = 0
    """DESFOQUE da sombra extra grande em pixels para QGraphicsDropShadowEffect (int Python)."""

    SHADOW_OFFSET_Y_SM: int = 0
    """DESLOCAMENTO VERTICAL da sombra pequena (int px). Positivo = sombra para baixo."""

    SHADOW_OFFSET_Y_MD: int = 0
    """DESLOCAMENTO VERTICAL da sombra média (int px)."""

    SHADOW_OFFSET_Y_LG: int = 0
    """DESLOCAMENTO VERTICAL da sombra grande (int px)."""

    SHADOW_COLOR_RGB: str = "#000000"
    """COR BASE da sombra sem alfa em formato #RRGGBB.
    Para QGraphicsDropShadowEffect programático."""

    SHADOW_COLOR_ALPHA: int = 0
    """ALFA (opacidade) da sombra (int 0-255). 0 = invisível."""

    GLOW_BLUR: int = 0
    """DESFOQUE do glow em pixels para QGraphicsDropShadowEffect (int).
    0 = glow desligado."""

    GLOW_OFFSET_X: int = 0
    """DESLOCAMENTO HORIZONTAL do glow em pixels (int)."""

    GLOW_OFFSET_Y: int = 0
    """DESLOCAMENTO VERTICAL do glow em pixels (int)."""

    GLOW_COLOR_RGB: str = ""
    """COR do glow em #RRGGBB. Vazio = usa ACCENT do tema como fallback."""

    GLOW_ALPHA: int = 0
    """ALFA do glow (int 0-255). 0 = glow invisível."""

    GLOW_STRONG_BLUR: int = 0
    """DESFOQUE do glow forte em pixels (int)."""

    GLOW_STRONG_ALPHA: int = 0
    """ALFA do glow forte (int 0-255)."""

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global de arredondamento (int, usado em Python e QSS com f"{v}px")
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS: int = 0
    """CANTO ARREDONDADO extra pequeno (int, usado em paintEvent e QSS com f"{v}px").
    Aplicado em: checkbox, scrollbar handle, spinbox buttons."""

    RADIUS_SM: int = 0
    """CANTO ARREDONDADO pequeno (int).
    Aplicado em: badges, toolbar buttons, group title."""

    RADIUS_MD: int = 0
    """CANTO ARREDONDADO médio (int).
    Aplicado em: botões padrão, inputs, menus dropdown."""

    RADIUS_LG: int = 0
    """CANTO ARREDONDADO grande (int).
    Aplicado em: cards, tabelas, progress bar."""

    RADIUS_XL: int = 0
    """CANTO ARREDONDADO extra grande (int).
    Aplicado em: diálogos, painéis grandes."""

    RADIUS_FULL: int = 999
    """CANTO ARREDONDADO total (int) — círculo/pílula.
    Aplicado em: radio button, badges em formato pill."""

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Escala global de espaçamento (int, usado em Python e QSS com f"{v}px")
    # ═══════════════════════════════════════════════════════════════════

    SPACE_XXS: int = 0
    """ESPAÇAMENTO micro (int). Entre elementos muito próximos."""

    SPACE_XS: int = 0
    """ESPAÇAMENTO muito pequeno (int)."""

    SPACE_SM: int = 0
    """ESPAÇAMENTO pequeno (int). Ex: entre botões adjacentes."""

    SPACE_MD: int = 0
    """ESPAÇAMENTO médio (int). Ex: padding interno de cards."""

    SPACE_LG: int = 0
    """ESPAÇAMENTO grande (int). Ex: entre seções de formulário."""

    SPACE_XL: int = 0
    """ESPAÇAMENTO extra grande (int). Ex: margem entre seções."""

    SPACE_2XL: int = 0
    """ESPAÇAMENTO de seção (int). Ex: antes/depois de grupos grandes."""

    SPACE_3XL: int = 0
    """ESPAÇAMENTO de seção grande (int). Ex: padding de página."""

    # ═══════════════════════════════════════════════════════════════════
    # 8. ICON — Tamanhos de ícone (int, usado em QSize)
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS: int = 0
    """ÍCONE extra pequeno (int px). Indicadores tiny, bullets, status dots."""

    ICON_SM: int = 0
    """ÍCONE pequeno (int px). Itens de menu, ícones em listas."""

    ICON_MD: int = 0
    """ÍCONE médio (int px). Botão padrão, toolbar."""

    ICON_LG: int = 0
    """ÍCONE grande (int px). Seção, header de grupo, ícone de tab."""

    ICON_XL: int = 0
    """ÍCONE extra grande (int px). Featured, empty state, ícone principal."""

    TOOLBAR_ICON_SIZE: int = 0
    """ÍCONE da TOOLBAR em pixels (int, usado em QSize)."""

    # ═══════════════════════════════════════════════════════════════════
    # 9. ANIMATION — Durações de animação (int ms) + easing
    # ═══════════════════════════════════════════════════════════════════

    ANIMATION_FAST: int = 0
    """DURAÇÃO de animação RÁPIDA em milissegundos (int).
    Usado em: hover de botões, micro-interações, feedback de clique."""

    ANIMATION_NORMAL: int = 0
    """DURAÇÃO de animação NORMAL em milissegundos (int).
    Usado em: transições padrão, fade in/out, mudança de cor."""

    ANIMATION_SLOW: int = 0
    """DURAÇÃO de animação LENTA em milissegundos (int).
    Usado em: expansão/colapso de painéis, abertura de menus."""

    EASING_STANDARD: str = ""
    """CURVA de easing (aceleração/desaceleração) para animações."""

    # ═══════════════════════════════════════════════════════════════════
    # 10. OPACITY — Níveis de opacidade (float 0.0 = transparente, 1.0 = opaco)
    # ═══════════════════════════════════════════════════════════════════

    OPACITY_DISABLED: float = 0.0
    """OPACIDADE de widgets desabilitados (float)."""

    OPACITY_MUTED: float = 0.0
    """OPACIDADE de texto/elementos secundários (float)."""

    OPACITY_HOVER: float = 0.0
    """OPACIDADE de feedback hover (float)."""

    OPACITY_ACTIVE: float = 0.0
    """OPACIDADE de estado ativo/pressionado (float)."""

    # ═══════════════════════════════════════════════════════════════════
    # 11. LAYOUT — Layout global (int px)
    # ═══════════════════════════════════════════════════════════════════

    PAGE_PADDING: int = 0
    """PADDING externo da página em pixels (int)."""

    SECTION_GAP: int = 0
    """ESPAÇAMENTO entre seções da página em pixels (int)."""

    GRID_GAP: int = 0
    """GAP (espaçamento entre células) em layouts grid (int)."""

    CONTENT_MAX_WIDTH: int = 0
    """LARGURA MÁXIMA do conteúdo da página em pixels (int)."""

    # ═══════════════════════════════════════════════════════════════════
    # 12. ELEVATION — Níveis de elevação (int, z-index conceitual)
    # ═══════════════════════════════════════════════════════════════════

    ELEVATION_FLAT: int = 0
    """ELEVAÇÃO flat — z-index 0 (int)."""

    ELEVATION_LOW: int = 0
    """ELEVAÇÃO baixa — z-index 1 (int)."""

    ELEVATION_MEDIUM: int = 0
    """ELEVAÇÃO média — z-index 2 (int). Cards, menus, popups."""

    ELEVATION_HIGH: int = 0
    """ELEVAÇÃO alta — z-index 3 (int). Modais, dialogs, overlays."""

    # ═══════════════════════════════════════════════════════════════════
    # 13. OVERLAY — Sobreposições / Glass effect
    # ═══════════════════════════════════════════════════════════════════

    OVERLAY_BG: str = ""
    """FUNDO de sobreposição (backdrop) de modais e diálogos (str rgba)."""

    BACKDROP_BLUR: str = ""
    """DESFOQUE do backdrop (efeito vidro) em CSS (str com px)."""

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING — Anel de foco visual
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR: str = ""
    """COR do anel de foco (str)."""

    FOCUS_RING_WIDTH: str = ""
    """ESPESSURA do anel de foco em CSS (str com px)."""

    FOCUS_RING_OFFSET: str = ""
    """DISTÂNCIA do anel de foco em relação ao elemento (str com px)."""

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS — Cores de estado semântico
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS: str = ""
    """VERDE — indica operação bem-sucedida (str)."""

    COLOR_SUCCESS_HOVER: str = ""
    """VERDE claro — hover do success (str)."""

    COLOR_SUCCESS_DIM: str = ""
    """VERDE escuro — versão escurecida do success (str)."""

    COLOR_WARNING: str = ""
    """AMARELO/LARANJA — indica atenção ou warning (str)."""

    COLOR_WARNING_HOVER: str = ""
    """LARANJA claro — hover do warning (str)."""

    COLOR_WARNING_DIM: str = ""
    """LARANJA escuro — versão escurecida do warning (str)."""

    COLOR_DANGER: str = ""
    """VERMELHO — indica erro, perigo, ação destrutiva (str)."""

    COLOR_DANGER_HOVER: str = ""
    """VERMELHO claro — hover do danger (str)."""

    COLOR_DANGER_DIM: str = ""
    """VERMELHO escuro — versão escurecida do danger (str)."""

    COLOR_INFO: str = ""
    """AZUL — indica informação (str)."""

    COLOR_INFO_HOVER: str = ""
    """AZUL claro — hover do info (str)."""

    COLOR_INFO_DIM: str = ""
    """AZUL escuro — versão escurecida do info (str)."""

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT — Tipografia
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT: str = ""
    """FAMÍLIA de fonte PADRÃO para toda a interface (str)."""

    FONT_FAMILY_MONO: str = ""
    """FAMÍLIA de fonte MONOESPAÇADA (str)."""

    FONT_FAMILY_DISPLAY: str = ""
    """FAMÍLIA de fonte DISPLAY/SERIF para títulos editoriais (str)."""

    FONT_LETTER_SPACING_DISPLAY: int = 0
    """ESPAÇAMENTO entre letras para fonte display (int, QFont.setLetterSpacing Python).
    0 = sem espaço extra. NÃO é QSS."""

    FONT_SIZE_TITLE: str = ""
    """TAMANHO da fonte de título — string com px (QSS).
    Usado em: header_title."""

    FONT_SIZE_BIG: str = ""
    """TAMANHO da fonte GRANDE — string com px (QSS)."""

    FONT_SIZE_NORMAL: str = ""
    """TAMANHO da fonte NORMAL — string com px (QSS)."""

    FONT_SIZE_SMALL: str = ""
    """TAMANHO da fonte PEQUENA — string com px (QSS)."""

    FONT_SIZE_TINY: str = ""
    """TAMANHO da fonte MUITO PEQUENA — string com px (QSS)."""

    FONT_WEIGHT_NORMAL: int = 400
    """PESO da fonte NORMAL (int 400 — regular)."""

    FONT_WEIGHT_BOLD: int = 600
    """PESO da fonte BOLD (int 600 — semi-bold)."""

    FONT_WEIGHT_EXTRABOLD: int = 700
    """PESO da fonte EXTRA BOLD (int 700 — bold)."""

    FONT_WEIGHT_HEAVY: int = 800
    """PESO da fonte HEAVY (int 800 — extra bold)."""

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS — Alturas e tamanhos de widgets
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT: int = 0
    """ALTURA de campos de input (int, usado em setFixedHeight)."""

    BUTTON_HEIGHT: int = 0
    """ALTURA de botões padrão (int, usado em setFixedHeight)."""

    BUTTON_HEIGHT_PRIMARY: int = 0
    """ALTURA de botões primários (int, usado em setFixedHeight)."""

    ITEM_HEIGHT: int = 0
    """ALTURA de itens de lista (int, usado em setFixedHeight)."""

    CHECKBOX_SIZE: str = ""
    """LARGURA/ALTURA do checkbox — string com px (QSS)."""

    RADIO_SIZE: int = 0
    """LARGURA/ALTURA do radio button (int, usado em QSize)."""

    SCROLLBAR_WIDTH: str = ""
    """LARGURA da scrollbar vertical — string com px (QSS)."""

    SCROLLBAR_MIN_HEIGHT: str = ""
    """ALTURA MÍNIMA do handle da scrollbar — string com px (QSS)."""

    TAB_HEIGHT: int = 0
    """ALTURA das abas (tabs) (int, usado em setFixedHeight)."""

    TAB_CLOSE_BUTTON_SIZE: str = ""
    """TAMANHO do botão fechar (X) da tab — string com px (QSS)."""

    CLOSE_BUTTON_BORDER_RADIUS: str = ""
    """AREDONDAMENTO do botão fechar na tab — string com px (QSS)."""

    PROGRESS_BAR_HEIGHT: str = ""
    """ALTURA da barra de progresso — string com px (QSS)."""

    TITLE_BTN_HEIGHT: str = ""
    """ALTURA dos botões de janela — string com px (QSS)."""

    TITLE_BTN_WIDTH: str = ""
    """LARGURA dos botões de janela — string com px (QSS)."""

    TITLE_BTN_FONT_SIZE: str = ""
    """TAMANHO da fonte dos botões de janela — string com px (QSS)."""

    TOOLBAR_BTN_SIZE: int = 0
    """TAMANHO do botão da toolbar (int, usado em QSize)."""

    TOOLBAR_BTN_HOVER_GROW: int = 0
    """PIXELS EXTRAS no hover (int, animação hover grow)."""

    GROUP_MARGIN_TOP: str = ""
    """MARGEM SUPERIOR do QGroupBox — string com px (QSS)."""

    SPLITTER_HANDLE_WIDTH: str = ""
    """LARGURA do pegador do QSplitter — string com px (QSS)."""

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — Tokens específicos de implementação
    # ═══════════════════════════════════════════════════════════════════

    # ── Border Radius específicos (str com px, usados em QSS) ──

    BORDER_RADIUS_CARD: str = ""
    """AREDONDAMENTO de CARDS — string com px (QSS)."""

    BORDER_RADIUS_BUTTON: str = ""
    """AREDONDAMENTO de BOTÕES — string com px (QSS)."""

    BORDER_RADIUS_INPUT: str = ""
    """AREDONDAMENTO de INPUTS — string com px (QSS)."""

    BORDER_RADIUS_CHECKBOX: str = ""
    """AREDONDAMENTO do CHECKBOX — string com px (QSS)."""

    BORDER_RADIUS_RADIO: str = ""
    """AREDONDAMENTO do RADIO BUTTON — string com px (QSS). Usar "0px" ou "999px"."""

    BORDER_RADIUS_BADGE: str = ""
    """AREDONDAMENTO de BADGES — string com px (QSS)."""

    BORDER_RADIUS_PROGRESS: str = ""
    """AREDONDAMENTO da PROGRESS BAR — string com px (QSS)."""

    BORDER_RADIUS_TABLE: str = ""
    """AREDONDAMENTO de TABELAS — string com px (QSS)."""

    BORDER_RADIUS_TITLE_BTN: str = ""
    """AREDONDAMENTO dos botões da title bar — string com px (QSS)."""

    BORDER_RADIUS_TOOLBAR_BTN: str = ""
    """AREDONDAMENTO dos botões da toolbar — string com px (QSS)."""

    BORDER_RADIUS_GHOST: str = ""
    """AREDONDAMENTO do botão GHOST — string com px (QSS)."""

    BORDER_RADIUS_TOOL_SELECTOR: str = ""
    """AREDONDAMENTO do seletor de tool — string com px (QSS)."""

    BORDER_RADIUS_SCROLLBAR: str = ""
    """AREDONDAMENTO da SCROLLBAR — string com px (QSS)."""

    BORDER_RADIUS_SPINBOX_BTN: str = ""
    """AREDONDAMENTO dos botões do SPINBOX — string com px (QSS)."""

    BORDER_RADIUS_TAB_CLOSE: str = ""
    """AREDONDAMENTO do botão fechar tab — string com px (QSS)."""

    BORDER_RADIUS_MENU: str = ""
    """AREDONDAMENTO do MENU DROPDOWN — string com px (QSS)."""

    BORDER_RADIUS_MENU_ITEM: str = ""
    """AREDONDAMENTO dos ITENS DE MENU — string com px (QSS)."""

    BORDER_RADIUS_GROUP_TITLE: str = ""
    """AREDONDAMENTO do TÍTULO DO GROUPBOX — string com px (QSS)."""

    BORDER_RADIUS_DIALOG: str = ""
    """AREDONDAMENTO de DIÁLOGOS — string com px (QSS)."""

    MENUBAR_ITEM_BORDER_RADIUS: str = ""
    """AREDONDAMENTO dos itens da MENUBAR — string com px (QSS)."""

    @property
    def BORDER_RADIUS_COMBO_POPUP(self) -> str:
        """Alias de compatibilidade → COMBOBOX_POPUP_BORDER_RADIUS (str com px)."""
        return self.COMBOBOX_POPUP_BORDER_RADIUS

    # ── Checkbox ──

    CHECKBOX_BORDER_WIDTH: int = 0
    """LARGURA da BORDA do checkbox (int, usado em QSS com f"{v}px")."""

    CHECKBOX_SPACING: str = ""
    """ESPAÇAMENTO entre checkbox e label — string com px (QSS)."""

    # ── Badge ──

    BADGE_PADDING_V: str = ""
    """PADDING VERTICAL do badge — string com px (QSS)."""

    BADGE_PADDING_H: str = ""
    """PADDING HORIZONTAL do badge — string com px (QSS)."""

    BADGE_LETTER_SPACING: str = ""
    """LETTER-SPACING do texto do badge — string com px (QSS)."""

    BADGE_OUTLINE_ENABLED: bool = False
    """Se True, badges usam estilo outline."""

    BADGE_OUTLINE_BORDER_WIDTH: int = 1
    """ESPESSURA da borda do badge outline (int, sem unidade)."""

    BADGE_OUTLINE_BG_ALPHA: int = 0
    """ALFA do fundo translúcido do badge outline (int 0-255)."""

    # ── Button ──

    BUTTON_PADDING_V: str = ""
    """PADDING VERTICAL de botão padrão — string com px (QSS)."""

    BUTTON_PADDING_H: str = ""
    """PADDING HORIZONTAL de botão padrão — string com px (QSS)."""

    BUTTON_PADDING_V_SMALL: str = ""
    """PADDING VERTICAL de botão pequeno — string com px (QSS)."""

    BUTTON_PADDING_H_SMALL: str = ""
    """PADDING HORIZONTAL de botão pequeno — string com px (QSS)."""

    BUTTON_PADDING_V_PRIMARY: str = ""
    """PADDING VERTICAL de botão primário — string com px (QSS)."""

    BUTTON_PADDING_H_PRIMARY: str = ""
    """PADDING HORIZONTAL de botão primário — string com px (QSS)."""

    BUTTON_LETTER_SPACING_NORMAL: str = ""
    """LETTER-SPACING de botão normal — string com px (QSS)."""

    BUTTON_LETTER_SPACING_PRIMARY: str = ""
    """LETTER-SPACING de botão primário — string com px (QSS)."""

    BUTTON_FONT_SIZE_PRIMARY: str = ""
    """TAMANHO da fonte do botão primário — string com px (QSS). Vazio = usa FONT_SIZE_NORMAL."""

    BUTTON_FONT_WEIGHT_PRIMARY: int = 0
    """PESO da fonte do botão primário (int). 0 = usa FONT_WEIGHT_HEAVY."""

    # ── Toolbar ──

    TOOLBAR_BTN_PADDING_V: str = ""
    """PADDING VERTICAL do botão toolbar — string com px (QSS)."""

    TOOLBAR_BTN_PADDING_H: str = ""
    """PADDING HORIZONTAL do botão toolbar — string com px (QSS)."""

    # ── Tool Selector ──

    TOOL_SELECTOR_PADDING_V: str = ""
    """PADDING VERTICAL do seletor de tool — string com px (QSS)."""

    TOOL_SELECTOR_PADDING_H: str = ""
    """PADDING HORIZONTAL do seletor de tool — string com px (QSS)."""

    TOOL_SELECTOR_LETTER_SPACING: str = ""
    """LETTER-SPACING do seletor de tool — string com px (QSS)."""

    # ── Input ──

    INPUT_PADDING_V: str = ""
    """PADDING VERTICAL de input — string com px (QSS)."""

    INPUT_PADDING_H: str = ""
    """PADDING HORIZONTAL de input — string com px (QSS)."""

    # ── SpinBox ──

    SPINBOX_PADDING: str = ""
    """PADDING do spinbox — string com px (QSS)."""

    SPINBOX_BTN_WIDTH: str = ""
    """LARGURA dos botões do spinbox — string com px (QSS)."""

    SPINBOX_BTN_MARGIN: str = ""
    """MARGEM dos botões do spinbox — string com px (QSS)."""

    # ── ComboBox ──

    COMBOBOX_PADDING: str = ""
    """PADDING do combobox — string com px (QSS)."""

    COMBOBOX_MIN_WIDTH: str = ""
    """LARGURA MÍNIMA do combobox — string com px (QSS)."""

    COMBOBOX_DROPDOWN_WIDTH: str = ""
    """LARGURA do dropdown button — string com px (QSS)."""

    COMBOBOX_ARROW_SIZE: str = ""
    """TAMANHO da seta do combobox — string com px (QSS)."""

    COMBOBOX_POPUP_BORDER_RADIUS: str = ""
    """AREDONDAMENTO do POPUP do combobox — string com px (QSS)."""

    # ── TextEdit / TextBrowser ──

    TEXT_EDIT_PADDING: str = ""
    """PADDING do text edit — string com px (QSS)."""

    TEXT_EDIT_FONT_SIZE: str = ""
    """TAMANHO da fonte do text edit — string com px (QSS)."""

    # ── GroupBox ──

    GROUP_TITLE_LEFT: str = ""
    """DESLOCAMENTO HORIZONTAL do título — string com px (QSS)."""

    GROUP_TITLE_TOP: str = ""
    """DESLOCAMENTO VERTICAL do título — string com px (QSS). Valor negativo = sobe."""

    GROUP_TITLE_PADDING: str = ""
    """PADDING do título do groupbox — string com px (QSS)."""

    GROUP_TITLE_BORDER_RADIUS: str = ""
    """AREDONDAMENTO do título do groupbox — string com px (QSS)."""

    GROUP_TITLE_LETTER_SPACING: str = ""
    """LETTER-SPACING do título do groupbox — string com px (QSS)."""

    # ── Letter Spacing ──

    LETTER_SPACING_TITLE: str = ""
    """LETTER-SPACING de títulos grandes — string com px (QSS)."""

    LETTER_SPACING_BADGE: str = ""
    """LETTER-SPACING de badges — string com px (QSS)."""

    LETTER_SPACING_GROUP: str = ""
    """LETTER-SPACING de título groupbox — string com px (QSS)."""

    LETTER_SPACING_BUTTON: str = ""
    """LETTER-SPACING de botão normal — string com px (QSS)."""

    LETTER_SPACING_BUTTON_PRIMARY: str = ""
    """LETTER-SPACING de botão primário — string com px (QSS)."""

    LETTER_SPACING_HEADER: str = ""
    """LETTER-SPACING de cabeçalho de tabela — string com px (QSS)."""

    LETTER_SPACING_TOOL_SELECTOR: str = ""
    """LETTER-SPACING de seletor de tool — string com px (QSS)."""

    LETTER_SPACING_WINDOW_TITLE: str = ""
    """LETTER-SPACING de título da janela — string com px (QSS)."""

    # ── Window Title ──

    WINDOW_TITLE_FONT_SIZE: str = ""
    """TAMANHO da fonte do título da janela — string com px (QSS)."""

    WINDOW_TITLE_LETTER_SPACING: str = ""
    """LETTER-SPACING do título da janela — string com px (QSS)."""

    # ── Title Bar ──

    TITLE_BAR_BORDER_WIDTH: str = ""
    """LARGURA da borda inferior da title bar — string com px (QSS)."""

    TITLE_BAR_BORDER_COLOR: str = ""
    """COR da borda inferior da title bar. Vazio = usa SURFACE_2 como fallback."""

    # ── Card ──

    CARD_PADDING_V: str = ""
    """PADDING VERTICAL de cards — string com px (QSS)."""

    CARD_PADDING_H: str = ""
    """PADDING HORIZONTAL de cards — string com px (QSS)."""

    # ── Splitter ──

    SPLITTER_HANDLE_WIDTH_H: str = ""
    """LARGURA do handle do splitter horizontal — string com px (QSS)."""

    SPLITTER_HANDLE_WIDTH_V: str = ""
    """LARGURA do handle do splitter vertical — string com px (QSS)."""

    # ── Menu ──

    MENU_PADDING: str = ""
    """PADDING do menu dropdown — string com px (QSS)."""

    MENU_MARGIN_V: str = ""
    """MARGEM vertical do menu — string com px (QSS)."""

    MENU_ITEM_PADDING: str = ""
    """PADDING dos itens de menu — string com px (QSS)."""

    MENU_SEPARATOR_HEIGHT: str = ""
    """ALTURA do separador de menu — string com px (QSS)."""

    MENU_SEPARATOR_MARGIN: str = ""
    """MARGEM do separador de menu — string com px (QSS)."""

    # ── Table / Header ──

    HEADER_FONT_SIZE: str = ""
    """TAMANHO da fonte do cabeçalho — string com px (QSS)."""

    HEADER_LETTER_SPACING: str = ""
    """LETTER-SPACING do cabeçalho — string com px (QSS)."""

    TABLE_ITEM_PADDING: str = ""
    """PADDING das células da tabela — string com px (QSS)."""

    HEADER_PADDING: str = ""
    """PADDING das células do cabeçalho — string com px (QSS)."""

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
    # ═══════════════════════════════════════════════════════════════════

    # ── Fundos (BG_*) → SURFACE ──

    BG_DEEPEST: str = ""
    """Alias de compatibilidade → SURFACE_0 (fundo absoluto / backdrop)."""

    BG_DARK: str = ""
    """Alias de compatibilidade → SURFACE_1 (fundo padrão da janela)."""

    BG_PANEL: str = ""
    """Alias de compatibilidade → SURFACE_2 (painéis base / side panels)."""

    BG_CARD: str = ""
    """Alias de compatibilidade → SURFACE_3 (cards / groupbox)."""

    BG_ELEVATED: str = ""
    """Alias de compatibilidade → SURFACE_4 (elementos elevados / inputs)."""

    BG_SURFACE: str = ""
    """Alias de compatibilidade → SURFACE_5 (superfície hover / focus)."""

    TITLE_BAR_BG: str = ""
    """Alias de compatibilidade → TITLE_BAR (barra de título da janela)."""

    # ── Sombras (SHADOW*) → SHADOW ──

    SHADOW: str = ""
    """Alias de compatibilidade → SHADOW_SM (sombra pequena)."""

    SHADOW_DEEP: str = ""
    """Alias de compatibilidade → SHADOW_LG (sombra grande/profunda)."""

    # ── Bordas (BORDER*) → BORDER ──

    BORDER: str = ""
    """Alias de compatibilidade → BORDER_DEFAULT (borda padrão de widgets)."""

    BORDER_HOVER: str = ""
    """Alias de compatibilidade → BORDER_ACCENT (borda com cor de acento no hover)."""

    # ── Texto (TEXT_*) → TEXT / ACCENT ──

    TEXT_BRIGHT: str = ""
    """Alias de compatibilidade → TEXT_HIGH (títulos, labels importantes)."""

    TEXT_PRIMARY: str = ""
    """Alias de compatibilidade → TEXT_MEDIUM (corpo padrão)."""

    TEXT_SECONDARY: str = ""
    """Alias de compatibilidade → TEXT_LOW (secundário, metadados)."""

    TEXT_MUTED: str = ""
    """Alias de compatibilidade → TEXT_DISABLED (widget desabilitado)."""

    TEXT_ACCENT: str = ""
    """Alias de compatibilidade → ACCENT_TEXT (texto sobre fundo escuro com cor de acento)."""

    TEXT_ACCENT_BRIGHT: str = ""
    """Alias de compatibilidade → ACCENT_BRIGHT (versão brilhante do texto de acento)."""

    # ── Acento (ACCENT_COLOR_*) → ACCENT ──

    ACCENT_COLOR: str = ""
    """Alias de compatibilidade → ACCENT (cor principal de destaque)."""

    ACCENT_COLOR_HOVER: str = ""
    """Alias de compatibilidade → ACCENT_HOVER (hover / foco)."""

    ACCENT_COLOR_ACTIVE: str = ""
    """Alias de compatibilidade → ACCENT_ACTIVE (pressed / ativo)."""

    ACCENT_COLOR_DIM: str = ""
    """Alias de compatibilidade → ACCENT_DIM (versão escurecida / muted)."""

    ACCENT_COLOR_LIGHT: str = ""
    """Alias de compatibilidade → ACCENT_LIGHT (versão clara / highlights)."""

    ACCENT_COLOR_GRADIENT: tuple[str, str] = ("", "")
    """Alias de compatibilidade → ACCENT_GRADIENT (par start/stop para gradientes)."""

    # ── Status (SUCCESS/WARNING/DANGER*) → COLOR_ ──

    SUCCESS: str = ""
    """Alias de compatibilidade → COLOR_SUCCESS (verde - operação bem-sucedida)."""

    SUCCESS_HOVER: str = ""
    """Alias de compatibilidade → COLOR_SUCCESS_HOVER."""

    SUCCESS_DIM: str = ""
    """Alias de compatibilidade → COLOR_SUCCESS_DIM."""

    WARNING: str = ""
    """Alias de compatibilidade → COLOR_WARNING (amarelo/laranja - atenção)."""

    WARNING_HOVER: str = ""
    """Alias de compatibilidade → COLOR_WARNING_HOVER."""

    WARNING_DIM: str = ""
    """Alias de compatibilidade → COLOR_WARNING_DIM."""

    DANGER: str = ""
    """Alias de compatibilidade → COLOR_DANGER (vermelho - erro/perigo)."""

    DANGER_HOVER: str = ""
    """Alias de compatibilidade → COLOR_DANGER_HOVER."""

    DANGER_DIM: str = ""
    """Alias de compatibilidade → COLOR_DANGER_DIM."""