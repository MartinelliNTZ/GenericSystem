# -*- coding: utf-8 -*-
"""
EmeraldTealTheme — Tema concreto Esmeralda / Verde-Teal
========================================================
Inspirado no design de botão 'docs/implementacoes/botao.py'.
Tema escuro com acento verde-teal profundo, gradiente vertical
3-stop e sombra 3D pronunciada.

Cores principais do botao.py (referência):
    - Gradiente normal: #1c6b63 → #0f5952 → #0a3d38 (top→bottom)
    - Hover: #218077 → #126a61 → #0d443e
    - Pressed: #0a3d38 → #062824
    - Sombra: black @ alpha=160, blur=25, offset=(0,8)
    - Border-radius: 35px (pill)
    - Texto: branco, 20px bold
    - Background da janela: #0a2f2b

Subclasse de BaseTheme com todos os tokens sobrescritos.

Convenção deste tema (alinhada ao AppStyles):
    Tokens que o AppStyles usa DIRETAMENTE em uma propriedade CSS
    (font-size, border-radius, etc.) já vêm como string com a unidade
    embutida (ex.: FONT_SIZE_SMALL = "11px"). Isso evita que o AppStyles
    precise concatenar "px" manualmente em cada f-string.

    Tokens que são usados apenas programaticamente (aritmética, QSize,
    setFixedHeight, contagem de pixels em Python) permanecem como int
    puro — ex.: INPUT_HEIGHT, ICON_*, TOOLBAR_ICON_SIZE, TOOLBAR_BTN_SIZE,
    TOOLBAR_BTN_HOVER_GROW.

    BORDER_RADIUS_TOOLBAR_BTN é usado nos dois mundos: como CSS
    (toolbar_btn_style) e como int puro (toolbar_btn_border_radius()).
    Por isso ele guarda a string com "px", e o método programático faz
    o parse de volta para int (ver AppStyles.toolbar_btn_border_radius).
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


class EmeraldTealTheme(BaseTheme):
    """
    Tema escuro esmeralda-teal com gradiente vertical e sombra 3D.
    """

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Verde-teal (do botao.py)
    # ═══════════════════════════════════════════════════════════════════

    ACCENT = "#1c6b63"
    ACCENT_HOVER = "#218077"
    ACCENT_ACTIVE = "#0a3d38"
    ACCENT_DIM = "#0a3d38"
    ACCENT_LIGHT = "#3a9b91"
    ACCENT_SOFT = "rgba(28,107,99,0.12)"
    ACCENT_TEXT = "#1c6b63"
    ACCENT_BRIGHT = "#4abfb3"
    ACCENT_GRADIENT = ("#1c6b63", "#0a3d38")

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Profundidade (0 = fundo, 5 = topo)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0 = "#062824"
    SURFACE_1 = "#0a2f2b"
    SURFACE_2 = "#0d3d36"
    SURFACE_3 = "#0f4840"
    SURFACE_4 = "#12544b"
    SURFACE_5 = "#156056"
    TITLE_BAR = "#071d1a"

    # ── Gradientes de superfície (top-left → bottom-right) ─────
    GRADIENT_BUTTON = ("#062824", "#12544b")
    GRADIENT_PANEL = ("#0d3d36", "#156056")
    GRADIENT_TAB = ("#0f4840", "#12544b")
    GRADIENT_INPUT = ("#0a2f2b", "#12544b")

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH = "#FFFFFF"
    TEXT_MEDIUM = "#E0F2F1"
    TEXT_LOW = "#8DAFAA"
    TEXT_DISABLED = "#507A74"
    TEXT_ON_ACCENT = "#FFFFFF"
    TEXT_ON_DANGER = "#FFFFFF"

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE = "#12544b"
    BORDER_DEFAULT = "#1a6b61"
    BORDER_STRONG = "#289287"
    BORDER_ACCENT = "#1c6b63"
    DIVIDER = "#0d3d36"

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM = "#040405"
    SHADOW_MD = "#000000"
    SHADOW_LG = "#000000"
    SHADOW_XL = "#000000"
    SHADOW_ACCENT = "#1c6b6315"
    GLOW = "#1c6b6315"
    GLOW_STRONG = "#1c6b6325"

    SHADOW_BLUR_SM = 4
    SHADOW_BLUR_MD = 8
    SHADOW_BLUR_LG = 25
    SHADOW_BLUR_XL = 40
    SHADOW_OFFSET_Y_SM = 2
    SHADOW_OFFSET_Y_MD = 4
    SHADOW_OFFSET_Y_LG = 8
    SHADOW_COLOR_RGB = "#000000"
    SHADOW_COLOR_ALPHA = 160

    GLOW_BLUR = 25
    GLOW_OFFSET_X = 0
    GLOW_OFFSET_Y = 8
    GLOW_COLOR_RGB = "#000000"
    GLOW_ALPHA = 160

    GLOW_STRONG_BLUR = 30
    GLOW_STRONG_ALPHA = 200

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global
    # Usada como valor CSS direto em vários lugares (ex.: RADIUS_SM no
    # AppStyles) → string com "px" embutido.
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS = "2px"
    RADIUS_SM = "4px"
    RADIUS_MD = "6px"
    RADIUS_LG = "12px"
    RADIUS_XL = "20px"
    RADIUS_FULL = "999px"

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Escala global de espaçamento
    # ═══════════════════════════════════════════════════════════════════

    SPACE_XXS = 2
    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 12
    SPACE_LG = 16
    SPACE_XL = 24
    SPACE_2XL = 32
    SPACE_3XL = 48

    # ═══════════════════════════════════════════════════════════════════
    # 8. ICON — Tamanhos (uso programático — QSize, setIconSize etc.)
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS = 12
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 24
    ICON_XL = 32
    TOOLBAR_ICON_SIZE = 34
    TOOLBAR_BTN_SIZE = 40
    TOOLBAR_BTN_HOVER_GROW = 4

    # ═══════════════════════════════════════════════════════════════════
    # 9. ANIMATION
    # ═══════════════════════════════════════════════════════════════════

    ANIMATION_FAST = 120
    ANIMATION_NORMAL = 180
    ANIMATION_SLOW = 260
    EASING_STANDARD = "cubic-bezier(0.4, 0, 0.2, 1)"

    # ═══════════════════════════════════════════════════════════════════
    # 10. OPACITY
    # ═══════════════════════════════════════════════════════════════════

    OPACITY_DISABLED = 0.35
    OPACITY_MUTED = 0.60
    OPACITY_HOVER = 0.85
    OPACITY_ACTIVE = 1.0

    # ═══════════════════════════════════════════════════════════════════
    # 11. LAYOUT
    # ═══════════════════════════════════════════════════════════════════

    PAGE_PADDING = 24
    SECTION_GAP = 24
    GRID_GAP = 20
    CONTENT_MAX_WIDTH = 1600

    # ═══════════════════════════════════════════════════════════════════
    # 12. ELEVATION
    # ═══════════════════════════════════════════════════════════════════

    ELEVATION_FLAT = 0
    ELEVATION_LOW = 1
    ELEVATION_MEDIUM = 2
    ELEVATION_HIGH = 3

    # ═══════════════════════════════════════════════════════════════════
    # 13. OVERLAY / Glass
    # ═══════════════════════════════════════════════════════════════════

    OVERLAY_BG = "rgba(6, 40, 36, 0.75)"
    BACKDROP_BLUR = "4px"

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR = "#1c6b63"
    FOCUS_RING_WIDTH = "2px"
    FOCUS_RING_OFFSET = "1px"

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS = "#43A047"
    COLOR_SUCCESS_HOVER = "#66BB6A"
    COLOR_SUCCESS_DIM = "#2E7D32"
    COLOR_WARNING = "#EF9A00"
    COLOR_WARNING_HOVER = "#FFB74D"
    COLOR_WARNING_DIM = "#BF6E00"
    COLOR_DANGER = "#D32F2F"
    COLOR_DANGER_HOVER = "#E53935"
    COLOR_DANGER_DIM = "#A02020"
    COLOR_INFO = "#5B9BD5"
    COLOR_INFO_HOVER = "#7BB8E8"
    COLOR_INFO_DIM = "#3A7CC2"

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT
    # FONT_SIZE_* é usado como valor CSS direto no AppStyles → string
    # com "px" embutido. FONT_WEIGHT_* nunca teve unidade (número puro
    # de CSS) e permanece int.
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT = "'Segoe UI', 'Inter', 'Roboto', sans-serif"
    FONT_FAMILY_MONO = "'Consolas', 'Courier New', monospace"

    FONT_SIZE_TITLE = "21px"
    FONT_SIZE_BIG = "16px"
    FONT_SIZE_NORMAL = "13px"
    FONT_SIZE_SMALL = "11px"
    FONT_SIZE_TINY = "10px"

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS — uso programático (aritmética, setFixedHeight etc.)
    # Permanecem int puro.
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT = 24
    BUTTON_HEIGHT = 0
    BUTTON_HEIGHT_PRIMARY = 0
    ITEM_HEIGHT = 0
    CHECKBOX_SIZE = 16
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = 6
    SCROLLBAR_MIN_HEIGHT = 28
    TAB_HEIGHT = 0
    TAB_CLOSE_BUTTON_SIZE = 20
    CLOSE_BUTTON_BORDER_RADIUS = 3
    PROGRESS_BAR_HEIGHT = 18
    TITLE_BTN_HEIGHT = 22
    TITLE_BTN_WIDTH = 28
    TITLE_BTN_FONT_SIZE = 11
    GROUP_MARGIN_TOP = 8
    SPLITTER_HANDLE_WIDTH = 4

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — BORDER_RADIUS
    # Todos usados como valor CSS direto no AppStyles → string com "px"
    # embutido.
    # ═══════════════════════════════════════════════════════════════════

    BORDER_RADIUS_CARD = "10px"
    BORDER_RADIUS_BUTTON = "35px"
    BORDER_RADIUS_INPUT = "6px"
    BORDER_RADIUS_CHECKBOX = "3px"
    BORDER_RADIUS_RADIO = "0px"
    BORDER_RADIUS_BADGE = "4px"
    BORDER_RADIUS_PROGRESS = "5px"
    BORDER_RADIUS_TABLE = "8px"
    BORDER_RADIUS_TITLE_BTN = "3px"
    BORDER_RADIUS_TOOLBAR_BTN = "4px"
    BORDER_RADIUS_GHOST = "5px"
    BORDER_RADIUS_TOOL_SELECTOR = "6px"
    BORDER_RADIUS_SCROLLBAR = "3px"
    BORDER_RADIUS_SPINBOX_BTN = "2px"
    BORDER_RADIUS_TAB_CLOSE = "3px"
    BORDER_RADIUS_COMBO_POPUP = "4px"
    BORDER_RADIUS_MENU = "6px"
    BORDER_RADIUS_MENU_ITEM = "3px"
    BORDER_RADIUS_GROUP_TITLE = "4px"
    BORDER_RADIUS_DIALOG = "16px"
    MENUBAR_ITEM_BORDER_RADIUS = "1px"

    CHECKBOX_BORDER_WIDTH = 0
    CHECKBOX_SPACING = 8

    BADGE_PADDING_V = "3px"
    BADGE_PADDING_H = "12px"
    BADGE_LETTER_SPACING = "0.3px"

    BUTTON_PADDING_V = "2px"
    BUTTON_PADDING_H = "2px"
    BUTTON_PADDING_V_SMALL = "2px"
    BUTTON_PADDING_H_SMALL = "2px"
    BUTTON_PADDING_V_PRIMARY = "10px"
    BUTTON_PADDING_H_PRIMARY = "30px"
    BUTTON_LETTER_SPACING_NORMAL = "0.3px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.5px"
    BUTTON_FONT_SIZE_PRIMARY = "20px"
    BUTTON_FONT_WEIGHT_PRIMARY = 700
    LETTER_SPACING_TITLE = "1px"
    LETTER_SPACING_BADGE = "0.3px"
    LETTER_SPACING_GROUP = "0.5px"
    LETTER_SPACING_BUTTON = "0.3px"
    LETTER_SPACING_BUTTON_PRIMARY = "0.5px"
    LETTER_SPACING_HEADER = "0.3px"
    LETTER_SPACING_TOOL_SELECTOR = "0.3px"
    LETTER_SPACING_WINDOW_TITLE = "0.3px"

    TOOLBAR_BTN_PADDING_V = "4px"
    TOOLBAR_BTN_PADDING_H = "10px"

    TOOL_SELECTOR_PADDING_V = "6px"
    TOOL_SELECTOR_PADDING_H = "4px"
    TOOL_SELECTOR_LETTER_SPACING = "0.3px"

    INPUT_PADDING_V = "2px"
    INPUT_PADDING_H = "2px"

    SPINBOX_PADDING = "3px 8px"
    SPINBOX_BTN_WIDTH = 16
    SPINBOX_BTN_MARGIN = "1px"

    COMBOBOX_PADDING = "3px 8px"
    COMBOBOX_MIN_WIDTH = 80
    COMBOBOX_DROPDOWN_WIDTH = 22
    COMBOBOX_ARROW_SIZE = "4px"
    COMBOBOX_POPUP_BORDER_RADIUS = 4

    TEXT_EDIT_PADDING = "8px"
    TEXT_EDIT_FONT_SIZE = 12

    GROUP_TITLE_LEFT = 4
    GROUP_TITLE_TOP = -2
    GROUP_TITLE_PADDING = "0 6px"
    GROUP_TITLE_BORDER_RADIUS = 4
    GROUP_TITLE_LETTER_SPACING = "0.5px"

    WINDOW_TITLE_FONT_SIZE = 11
    WINDOW_TITLE_LETTER_SPACING = "0.3px"

    TITLE_BAR_BORDER_WIDTH = "1px"
    TITLE_BAR_BORDER_COLOR = ""
    CARD_PADDING_V = 16
    CARD_PADDING_H = 10

    SPLITTER_HANDLE_WIDTH_H = 4
    SPLITTER_HANDLE_WIDTH_V = 4

    MENU_PADDING = "10px 30px"
    MENU_MARGIN_V = "1px 0"
    MENU_ITEM_PADDING = "4px 16px 4px 8px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "2px 6px"

    HEADER_FONT_SIZE = "11px"
    HEADER_LETTER_SPACING = "0.3px"
    TABLE_ITEM_PADDING = "3px 6px"
    HEADER_PADDING = "4px 6px"

    # ── Gradiente multi-stop para botão primário (3-stop vertical como botao.py) ──
    # botao.py usa: stop:0 #1c6b63, stop:0.5 #0f5952, stop:1 #0a3d38 (vertical)
    # Em QSS: x1=0,y1=0,x2=0,y2=1 para gradiente vertical top→bottom
    GRADIENT_ACCENT_STOPS = (
        (0.00, "#1c6b63"),
        (0.50, "#0f5952"),
        (1.00, "#0a3d38"),
    )
    GRADIENT_ACCENT_ANGLE = 90  # vertical top→bottom (como no botao.py)

    # Hover: #218077 → #126a61 → #0d443e
    GRADIENT_ACCENT_TYPE = None  # LINEAR (padrão)

    # Stops para hover (usado inline no btn_primary_style via ACCENT_HOVER/ACCENT)
    # O método btn_primary_style já gera hover com fallback 2-stop

    # ═══════════════════════════════════════════════════════════════════
    # GLOW — Sombra preta 3D (botao.py: black @160, blur 25, offset 0,8)
    # ═══════════════════════════════════════════════════════════════════

    GLOW_BUTTON_ENABLED = True
    GLOW_TAB_ENABLED = False

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
    # ═══════════════════════════════════════════════════════════════════

    BG_DEEPEST = SURFACE_0
    BG_DARK = SURFACE_1
    BG_PANEL = SURFACE_2
    BG_CARD = SURFACE_3
    BG_ELEVATED = SURFACE_4
    BG_SURFACE = SURFACE_5
    TITLE_BAR_BG = TITLE_BAR

    SHADOW = SHADOW_SM
    SHADOW_DEEP = SHADOW_LG
    BORDER = BORDER_DEFAULT
    BORDER_HOVER = BORDER_ACCENT

    TEXT_BRIGHT = TEXT_HIGH
    TEXT_PRIMARY = TEXT_MEDIUM
    TEXT_SECONDARY = TEXT_LOW
    TEXT_MUTED = TEXT_DISABLED
    TEXT_ACCENT = ACCENT_TEXT
    TEXT_ACCENT_BRIGHT = ACCENT_BRIGHT

    ACCENT_COLOR = ACCENT
    ACCENT_COLOR_HOVER = ACCENT_HOVER
    ACCENT_COLOR_ACTIVE = ACCENT_ACTIVE
    ACCENT_COLOR_DIM = ACCENT_DIM
    ACCENT_COLOR_LIGHT = ACCENT_LIGHT
    ACCENT_COLOR_GRADIENT = ACCENT_GRADIENT

    SUCCESS = COLOR_SUCCESS
    SUCCESS_HOVER = COLOR_SUCCESS_HOVER
    SUCCESS_DIM = COLOR_SUCCESS_DIM
    WARNING = COLOR_WARNING
    WARNING_HOVER = COLOR_WARNING_HOVER
    WARNING_DIM = COLOR_WARNING_DIM
    DANGER = COLOR_DANGER
    DANGER_HOVER = COLOR_DANGER_HOVER
    DANGER_DIM = COLOR_DANGER_DIM