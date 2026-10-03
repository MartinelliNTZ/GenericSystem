# -*- coding: utf-8 -*-
"""
ZeroGrausTheme — Tema Ice Glass / Frozen Crystal
================================================
Visual inspirado em gelo translúcido, superfícies cristalinas,
tons azulados e brilho frio elegante.

Todos os valores estão nos tokens semânticos.
Os aliases de compatibilidade (BG_*, GOLD*, etc.) apontam
para os mesmos tokens → código legado continua funcionando.

Identidade visual:
- ACCENT: Crystal Cyan (#7FE8FF)
- SURFACE: Deep Arctic Glass (azulados escuros)
- TEXT: Branco gelo, azul claro
- GLOW: Azul-gelo translúcido
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


class ZeroGrausTheme(BaseTheme):
    """
    Tema 0Graus — visual cristalino baseado em gelo e vidro.
    """

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Crystal Cyan
    # ═══════════════════════════════════════════════════════════════════

    ACCENT = "#7FE8FF"
    ACCENT_HOVER = "#A6F2FF"
    ACCENT_ACTIVE = "#56D8F5"
    ACCENT_DIM = "#4CA7BD"
    ACCENT_LIGHT = "#D9FBFF"
    ACCENT_SOFT = "rgba(127,232,255,0.12)"
    ACCENT_TEXT = "#8EEFFF"
    ACCENT_BRIGHT = "#CFFBFF"
    ACCENT_GRADIENT = ("#A6F2FF", "#56D8F5")

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Deep Arctic Glass (0 = fundo, 5 = topo)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0 = "#02060A"
    SURFACE_1 = "#071018"
    SURFACE_2 = "#0C1824"
    SURFACE_3 = "#122131"
    SURFACE_4 = "#173046"
    SURFACE_5 = "#1C3E59"
    TITLE_BAR = "#040B12"

    # ── Gradientes de superfície (top-left → bottom-right) ─────
    # PANEL/TAB precisam contrastar com SURFACE_1 (fundo da janela)
    GRADIENT_BUTTON = ("#02060A", "#173046")   # SURFACE_0 → SURFACE_4
    GRADIENT_PANEL = ("#122131", "#1C3E59")     # SURFACE_3 → SURFACE_5 (mais claro, contrasta com fundo)
    GRADIENT_TAB = ("#122131", "#173046")       # SURFACE_3 → SURFACE_4
    GRADIENT_INPUT = ("#071018", "#173046")    # SURFACE_1 → SURFACE_4

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH = "#F7FDFF"
    TEXT_MEDIUM = "#DDF6FF"
    TEXT_LOW = "#9CC7D8"
    TEXT_DISABLED = "#5C7D90"
    TEXT_ON_ACCENT = "#02060A"
    TEXT_ON_DANGER = "#FFFFFF"

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE = "#142737"
    BORDER_DEFAULT = "#2A475D"
    BORDER_STRONG = "#3A5F78"
    BORDER_ACCENT = "#8EEFFF"
    DIVIDER = "#142737"

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM = "#000000"
    SHADOW_MD = "#000000"
    SHADOW_LG = "#000000"
    SHADOW_XL = "#000000"
    SHADOW_ACCENT = "#7FE8FF15"
    GLOW = "#7FE8FF18"
    GLOW_STRONG = "#7FE8FF40"

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS = 2
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 10
    RADIUS_XL = 16
    RADIUS_FULL = 999

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
    # 8. ICON — Tamanhos
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS = 12
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 24
    ICON_XL = 32
    TOOLBAR_ICON_SIZE = 40
    TOOLBAR_BTN_SIZE = 40

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

    OVERLAY_BG = "rgba(2, 6, 10, 0.75)"
    BACKDROP_BLUR = "4px"

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR = "#7FE8FF"
    FOCUS_RING_WIDTH = "2px"
    FOCUS_RING_OFFSET = "1px"

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS — Cores de estado semântico
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS = "#2EE59D"
    COLOR_SUCCESS_HOVER = "#5EF0B5"
    COLOR_SUCCESS_DIM = "#1CA772"
    COLOR_WARNING = "#FFC857"
    COLOR_WARNING_HOVER = "#FFD87E"
    COLOR_WARNING_DIM = "#D89B1D"
    COLOR_DANGER = "#FF6B7A"
    COLOR_DANGER_HOVER = "#FF8C98"
    COLOR_DANGER_DIM = "#D94A58"
    COLOR_INFO = "#5B9BD5"
    COLOR_INFO_HOVER = "#7BB8E8"
    COLOR_INFO_DIM = "#3A7CC2"

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT = "'Segoe UI', 'Inter', 'Roboto', sans-serif"
    FONT_FAMILY_MONO = "'Consolas', 'Courier New', monospace"

    FONT_SIZE_TITLE = 21
    FONT_SIZE_BIG = 16
    FONT_SIZE_NORMAL = 13
    FONT_SIZE_SMALL = 11
    FONT_SIZE_TINY = 10

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT = 20
    BUTTON_HEIGHT = 0
    BUTTON_HEIGHT_PRIMARY = 0
    ITEM_HEIGHT = 0
    CHECKBOX_SIZE = 16
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = 6
    SCROLLBAR_MIN_HEIGHT = 28
    TAB_HEIGHT = 0
    TAB_CLOSE_BUTTON_SIZE = 16
    CLOSE_BUTTON_BORDER_RADIUS = 3
    PROGRESS_BAR_HEIGHT = 18
    TITLE_BTN_HEIGHT = 22
    TITLE_BTN_WIDTH = 28
    TITLE_BTN_FONT_SIZE = 11
    GROUP_MARGIN_TOP = 8
    SPLITTER_HANDLE_WIDTH = 4
    TOOLBAR_BTN_SIZE = 32
    TOOLBAR_BTN_HOVER_GROW = 4

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — Border Radius (mapeados dos RADIUS semânticos)
    # ═══════════════════════════════════════════════════════════════════

    BORDER_RADIUS_CARD = 12          # ≈ RADIUS_LG + 2 (mais aredondado)
    BORDER_RADIUS_BUTTON = 8         # ≈ RADIUS_MD + 2
    BORDER_RADIUS_INPUT = 8          # ≈ RADIUS_MD + 2
    BORDER_RADIUS_CHECKBOX = 4       # ≈ RADIUS_SM
    BORDER_RADIUS_RADIO = 8          # ≈ RADIUS_MD + 2
    BORDER_RADIUS_BADGE = 5          # ≈ RADIUS_SM + 1
    BORDER_RADIUS_PROGRESS = 6       # ≈ RADIUS_MD
    BORDER_RADIUS_TABLE = 10         # ≈ RADIUS_LG
    BORDER_RADIUS_TITLE_BTN = 4      # ≈ RADIUS_SM
    BORDER_RADIUS_TOOLBAR_BTN = 6    # ≈ RADIUS_MD
    BORDER_RADIUS_GHOST = 5
    BORDER_RADIUS_TOOL_SELECTOR = 8  # ≈ RADIUS_MD + 2
    BORDER_RADIUS_SCROLLBAR = 3      # ≈ RADIUS_XS + 1
    BORDER_RADIUS_SPINBOX_BTN = 2    # ≈ RADIUS_XS
    BORDER_RADIUS_TAB_CLOSE = 3
    BORDER_RADIUS_COMBO_POPUP = 4    # ≈ RADIUS_SM
    BORDER_RADIUS_MENU = 6           # ≈ RADIUS_MD
    BORDER_RADIUS_MENU_ITEM = 3      # ≈ RADIUS_XS + 1
    BORDER_RADIUS_GROUP_TITLE = 4    # ≈ RADIUS_SM
    BORDER_RADIUS_DIALOG = 16        # ≈ RADIUS_XL
    MENUBAR_ITEM_BORDER_RADIUS = 1

    CHECKBOX_BORDER_WIDTH = 0
    CHECKBOX_SPACING = 8

    BADGE_PADDING_V = "3px"
    BADGE_PADDING_H = "12px"
    BADGE_LETTER_SPACING = "0.3px"

    BUTTON_PADDING_V = "2px"
    BUTTON_PADDING_H = "2px"
    BUTTON_PADDING_V_SMALL = "2px"
    BUTTON_PADDING_H_SMALL = "2px"
    BUTTON_PADDING_V_PRIMARY = "2px"
    BUTTON_PADDING_H_PRIMARY = "2px"
    BUTTON_LETTER_SPACING_NORMAL = "0.3px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.5px"
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

    INPUT_PADDING_V = "4px"
    INPUT_PADDING_H = "8px"

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
    TITLE_BAR_BORDER_COLOR = ""  # usa BG_PANEL por compatibilidade
    CARD_PADDING_V = 16
    CARD_PADDING_H = 10

    SPLITTER_HANDLE_WIDTH_H = 4
    SPLITTER_HANDLE_WIDTH_V = 4

    MENU_PADDING = "2px"
    MENU_MARGIN_V = "1px 0"
    MENU_ITEM_PADDING = "4px 16px 4px 8px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "2px 6px"

    HEADER_FONT_SIZE = 11
    HEADER_LETTER_SPACING = "0.3px"
    TABLE_ITEM_PADDING = "3px 6px"
    HEADER_PADDING = "4px 6px"

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
    # Mapeiam nomes antigos → tokens semânticos
    # ═══════════════════════════════════════════════════════════════════

    # ── Fundos (BG_*) → SURFACE ─────────────────────────────────────
    BG_DEEPEST = SURFACE_0
    BG_DARK = SURFACE_1
    BG_PANEL = SURFACE_2
    BG_CARD = SURFACE_3
    BG_ELEVATED = SURFACE_4
    BG_SURFACE = SURFACE_5
    TITLE_BAR_BG = TITLE_BAR

    # ── Sombras → SHADOW ────────────────────────────────────────────
    SHADOW = SHADOW_SM
    SHADOW_DEEP = SHADOW_LG

    # ── Bordas → BORDER ─────────────────────────────────────────────
    BORDER = BORDER_DEFAULT
    BORDER_HOVER = BORDER_ACCENT

    # ── Texto (TEXT_*) → TEXT ───────────────────────────────────────
    TEXT_BRIGHT = TEXT_HIGH
    TEXT_PRIMARY = TEXT_MEDIUM
    TEXT_SECONDARY = TEXT_LOW
    TEXT_MUTED = TEXT_DISABLED
    TEXT_ACCENT = ACCENT_TEXT
    TEXT_ACCENT_BRIGHT = ACCENT_BRIGHT

    # ── Acento (ACCENT_COLOR_*) → ACCENT ─────────────────────────────
    ACCENT_COLOR = ACCENT
    ACCENT_COLOR_HOVER = ACCENT_HOVER
    ACCENT_COLOR_ACTIVE = ACCENT_ACTIVE
    ACCENT_COLOR_DIM = ACCENT_DIM
    ACCENT_COLOR_LIGHT = ACCENT_LIGHT
    ACCENT_COLOR_GRADIENT = ACCENT_GRADIENT

    # ── Status → COLOR_ ─────────────────────────────────────────────
    SUCCESS = COLOR_SUCCESS
    SUCCESS_HOVER = COLOR_SUCCESS_HOVER
    SUCCESS_DIM = COLOR_SUCCESS_DIM
    WARNING = COLOR_WARNING
    WARNING_HOVER = COLOR_WARNING_HOVER
    WARNING_DIM = COLOR_WARNING_DIM
    DANGER = COLOR_DANGER
    DANGER_HOVER = COLOR_DANGER_HOVER
    DANGER_DIM = COLOR_DANGER_DIM