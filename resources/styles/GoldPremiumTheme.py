# -*- coding: utf-8 -*-
"""
GoldPremiumTheme — Tema Premium Dourado (5 estilos "gold")
==========================================================
Tema demonstrativo que usa 100% dos novos tokens de estilo premium:
  - Gradientes multi-stop com ângulo para reflexo metálico
  - Sombra/glow estruturados para QGraphicsDropShadowEffect
  - Borda em gradiente ("efeito foil")
  - Fonte display serifada para títulos editoriais
  - Letter-spacing numérico para QFont
  - Badge outline habilitado

Identidade visual:
  - ACCENT: Dourado luxo (#D4AF37 → gradientes 5 stops)
  - SURFACE: Preto aveludado profundo
  - TEXT: Off-white quente com hierarquia clara
  - GLOW: Dourado translúcido estruturado
  - FONTE DISPLAY: Georgia / serif para títulos
"""

from __future__ import annotations

from core.enum.GradientType import GradientType
from resources.styles.BaseTheme import BaseTheme


class GoldPremiumTheme(BaseTheme):
    """
    Tema Gold Premium — demonstra todos os novos tokens de estilo.
    Visual dourado/luxo com gradientes multi-stop, foil borders,
    glow estruturado e tipografia display.
    """

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Dourado Luxo
    # ═══════════════════════════════════════════════════════════════════

    ACCENT = "#D4AF37"
    ACCENT_HOVER = "#E0C25A"
    ACCENT_ACTIVE = "#C49A2E"
    ACCENT_DIM = "#A08020"
    ACCENT_LIGHT = "#F0DF8A"
    ACCENT_SOFT = "rgba(212,175,55,0.12)"
    ACCENT_TEXT = "#D4AF37"
    ACCENT_BRIGHT = "#F5E6A3"
    ACCENT_GRADIENT = ("#D4AF37", "#B8961A")

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Veludo Preto Profundo (0=fundo … 5=topo)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0 = "#050504"
    SURFACE_1 = "#0A0A08"
    SURFACE_2 = "#10100D"
    SURFACE_3 = "#161612"
    SURFACE_4 = "#1C1C17"
    SURFACE_5 = "#22221C"
    TITLE_BAR = "#070706"

    # ── Gradientes de superfície ─────────────────────────────────
    GRADIENT_BUTTON = ("#050504", "#1C1C17")
    GRADIENT_PANEL = ("#10100D", "#22221C")
    GRADIENT_TAB = ("#161612", "#1C1C17")
    GRADIENT_INPUT = ("#0A0A08", "#1C1C17")

    # ── Gradiente rico multi-stop (5 stops, reflexo metálico) ────
    # Ângulo 20° simula reflexo de metal polido (GoldText do protótipo)
    GRADIENT_ACCENT_TYPE: GradientType = GradientType.RADIAL
    GRADIENT_ACCENT_STOPS: tuple = (
        (0.00, "#A08020"),
        (0.35, "#D4AF37"),
        (0.55, "#F5E6A3"),
        (0.80, "#D4AF37"),
        (1.00, "#8A6A10"),
    )
    GRADIENT_ACCENT_ANGLE: int = 20

    # ── BUTTON GRADIENT (botões secundários) — também radial dourado ─
    GRADIENT_BUTTON_TYPE: GradientType = GradientType.RADIAL
    GRADIENT_BUTTON_STOPS: tuple = (
        (0.00, "#1C1C17"),
        (0.50, "#2A2A22"),
        (1.00, "#0A0A08"),
    )
    GRADIENT_BUTTON_ANGLE: int = 45

    # ── TAB GRADIENT (tabs não selecionadas) — gradiente suave ──────
    GRADIENT_TAB_TYPE: GradientType = GradientType.LINEAR
    GRADIENT_TAB_STOPS: tuple = (
        (0.00, "#22221C"),
        (1.00, "#10100D"),
    )
    GRADIENT_TAB_ANGLE: int = 45

    # ── GLOW CONTROLES ──────────────────────────────────────────────
    GLOW_BUTTON_ENABLED: bool = True
    GLOW_TAB_ENABLED: bool = True

    # ── Parâmetros do gradiente RADIAL (spotlight no centro) ─────
    GRADIENT_RADIAL_CX: float = 0.5
    GRADIENT_RADIAL_CY: float = 0.5
    GRADIENT_RADIAL_FX: float = 0.5
    GRADIENT_RADIAL_FY: float = 0.3   # foco levemente acima do centro
    GRADIENT_RADIAL_RADIUS: float = 0.6

    # ── Parâmetros do gradiente CONICAL (fallback) ───────────────
    GRADIENT_CONICAL_CX: float = 0.5
    GRADIENT_CONICAL_CY: float = 0.5
    GRADIENT_CONICAL_ANGLE: float = 0.0

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia tipográfica quente
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH = "#F5F0E8"
    TEXT_MEDIUM = "#E0D8C8"
    TEXT_LOW = "#A09888"
    TEXT_DISABLED = "#605850"
    TEXT_ON_ACCENT = "#050504"
    TEXT_ON_DANGER = "#FFFFFF"

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia com foil
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE = "#181812"
    BORDER_DEFAULT = "#282820"
    BORDER_STRONG = "#383830"
    BORDER_ACCENT = "#D4AF37"
    DIVIDER = "#181812"

    # ── Borda em gradiente ("efeito foil") ────────────────────────
    # Borda metálica que muda de tom ao longo do contorno.
    BORDER_GRADIENT_STOPS: tuple = (
        (0.00, "#D4AF37"),
        (0.25, "#F5E6A3"),
        (0.50, "#A08020"),
        (0.75, "#D4AF37"),
        (1.00, "#8A6A10"),
    )
    BORDER_GRADIENT_WIDTH: float = 2.0

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras e glow estruturados
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM = "#000000"
    SHADOW_MD = "#000000"
    SHADOW_LG = "#000000"
    SHADOW_XL = "#000000"
    SHADOW_ACCENT = "#D4AF3720"
    GLOW = "#D4AF3718"
    GLOW_STRONG = "#D4AF3730"

    # ── Sombra estruturada (QGraphicsDropShadowEffect) ──────────
    SHADOW_BLUR_SM: int = 4
    SHADOW_BLUR_MD: int = 8
    SHADOW_BLUR_LG: int = 16
    SHADOW_BLUR_XL: int = 24
    SHADOW_OFFSET_Y_SM: int = 1
    SHADOW_OFFSET_Y_MD: int = 2
    SHADOW_OFFSET_Y_LG: int = 4
    SHADOW_COLOR_RGB: str = "#000000"
    SHADOW_COLOR_ALPHA: int = 128   # 50% opacity

    # ── Glow estruturado (brilho dourado) ───────────────────────
    GLOW_BLUR: int = 12
    GLOW_OFFSET_X: int = 0
    GLOW_OFFSET_Y: int = 0
    GLOW_COLOR_RGB: str = "#D4AF37"   # fallback to gold accent
    GLOW_ALPHA: int = 60              # ~24% opacity
    GLOW_STRONG_BLUR: int = 20
    GLOW_STRONG_ALPHA: int = 80

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Arredondamento generoso (visual premium)
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS = 3
    RADIUS_SM = 5
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_XL = 20
    RADIUS_FULL = 999

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Espaçamento generoso
    # ═══════════════════════════════════════════════════════════════════

    SPACE_XXS = 3
    SPACE_XS = 5
    SPACE_SM = 10
    SPACE_MD = 14
    SPACE_LG = 18
    SPACE_XL = 28
    SPACE_2XL = 36
    SPACE_3XL = 52

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

    PAGE_PADDING = 28
    SECTION_GAP = 28
    GRID_GAP = 22
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

    OVERLAY_BG = "rgba(5, 5, 4, 0.75)"
    BACKDROP_BLUR = "6px"

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR = "#D4AF37"
    FOCUS_RING_WIDTH = "2px"
    FOCUS_RING_OFFSET = "1px"

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS — Cores de estado
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS = "#4CAF50"
    COLOR_SUCCESS_HOVER = "#66BB6A"
    COLOR_SUCCESS_DIM = "#2E7D32"
    COLOR_WARNING = "#FFB300"
    COLOR_WARNING_HOVER = "#FFCA28"
    COLOR_WARNING_DIM = "#BF6E00"
    COLOR_DANGER = "#E53935"
    COLOR_DANGER_HOVER = "#EF5350"
    COLOR_DANGER_DIM = "#A02020"
    COLOR_INFO = "#5B9BD5"
    COLOR_INFO_HOVER = "#7BB8E8"
    COLOR_INFO_DIM = "#3A7CC2"

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT — Tipografia com fonte display serifada
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT = "'Segoe UI', 'Inter', 'Roboto', sans-serif"
    FONT_FAMILY_MONO = "'Consolas', 'Courier New', monospace"

    # ── Fonte display/serif para títulos editoriais ──────────────
    # "Georgia" como fallback seguro; "'Cormorant Garamond'" seria ideal
    # se instalada no sistema.
    FONT_FAMILY_DISPLAY: str = "'Georgia', 'Playfair Display', serif"

    # Letter-spacing numérico para QFont.setLetterSpacing em
    # widgets com paintEvent customizado (ex: GoldText).
    FONT_LETTER_SPACING_DISPLAY: int = 2

    FONT_SIZE_TITLE = "24px"
    FONT_SIZE_BIG = "18px"
    FONT_SIZE_NORMAL = "13px"
    FONT_SIZE_SMALL = "11px"
    FONT_SIZE_TINY = "10px"

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS — Alturas e tamanhos de widgets
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT = 28
    BUTTON_HEIGHT = 0
    BUTTON_HEIGHT_PRIMARY = 0
    ITEM_HEIGHT = 0
    CHECKBOX_SIZE = "16px"
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = "6px"
    SCROLLBAR_MIN_HEIGHT = "30px"
    TAB_HEIGHT = 0
    TAB_CLOSE_BUTTON_SIZE = "20px"
    CLOSE_BUTTON_BORDER_RADIUS = "3px"
    PROGRESS_BAR_HEIGHT = "20px"
    TITLE_BTN_HEIGHT = "24px"
    TITLE_BTN_WIDTH = "30px"
    TITLE_BTN_FONT_SIZE = "11px"
    TOOLBAR_BTN_SIZE = 42
    TOOLBAR_BTN_HOVER_GROW = 5
    GROUP_MARGIN_TOP = "10px"
    SPLITTER_HANDLE_WIDTH = "4px"

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — Tokens específicos de implementação
    # ═══════════════════════════════════════════════════════════════════

    # ── Border Radius ────────────────────────────────────────────
    BORDER_RADIUS_CARD = "12px"
    BORDER_RADIUS_BUTTON = "8px"
    BORDER_RADIUS_INPUT = "8px"
    BORDER_RADIUS_CHECKBOX = "4px"
    BORDER_RADIUS_RADIO = "0px"
    BORDER_RADIUS_BADGE = "5px"
    BORDER_RADIUS_PROGRESS = "6px"
    BORDER_RADIUS_TABLE = "10px"
    BORDER_RADIUS_TITLE_BTN = "4px"
    BORDER_RADIUS_TOOLBAR_BTN = "5px"
    BORDER_RADIUS_GHOST = "6px"
    BORDER_RADIUS_TOOL_SELECTOR = "8px"
    BORDER_RADIUS_SCROLLBAR = "3px"
    BORDER_RADIUS_SPINBOX_BTN = "2px"
    BORDER_RADIUS_TAB_CLOSE = "3px"
    BORDER_RADIUS_COMBO_POPUP = "5px"
    BORDER_RADIUS_MENU = "8px"
    BORDER_RADIUS_MENU_ITEM = "4px"
    BORDER_RADIUS_GROUP_TITLE = "5px"
    BORDER_RADIUS_DIALOG = "20px"
    MENUBAR_ITEM_BORDER_RADIUS = "1px"

    # ── Checkbox ─────────────────────────────────────────────────
    CHECKBOX_BORDER_WIDTH = 0
    CHECKBOX_SPACING = "8px"

    # ── Badge ────────────────────────────────────────────────────
    BADGE_PADDING_V = "3px"
    BADGE_PADDING_H = "14px"
    BADGE_LETTER_SPACING = "0.4px"

    # ── Badge Outline (habilitado para estilo premium) ───────────
    BADGE_OUTLINE_ENABLED: bool = True
    BADGE_OUTLINE_BORDER_WIDTH: int = 1
    BADGE_OUTLINE_BG_ALPHA: int = 30   # fundo translúcido ~12%

    # ── Button ───────────────────────────────────────────────────
    BUTTON_PADDING_V = "3px"
    BUTTON_PADDING_H = "3px"
    BUTTON_PADDING_V_SMALL = "2px"
    BUTTON_PADDING_H_SMALL = "2px"
    BUTTON_PADDING_V_PRIMARY = "3px"
    BUTTON_PADDING_H_PRIMARY = "3px"
    BUTTON_LETTER_SPACING_NORMAL = "0.4px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.6px"

    # ── Toolbar ──────────────────────────────────────────────────
    TOOLBAR_BTN_PADDING_V = "5px"
    TOOLBAR_BTN_PADDING_H = "12px"

    # ── Tool Selector ────────────────────────────────────────────
    TOOL_SELECTOR_PADDING_V = "7px"
    TOOL_SELECTOR_PADDING_H = "5px"
    TOOL_SELECTOR_LETTER_SPACING = "0.4px"

    # ── Input ────────────────────────────────────────────────────
    INPUT_PADDING_V = "3px"
    INPUT_PADDING_H = "3px"

    # ── SpinBox ──────────────────────────────────────────────────
    SPINBOX_PADDING = "4px 10px"
    SPINBOX_BTN_WIDTH = "16px"
    SPINBOX_BTN_MARGIN = "1px"

    # ── ComboBox ─────────────────────────────────────────────────
    COMBOBOX_PADDING = "4px 10px"
    COMBOBOX_MIN_WIDTH = "80px"
    COMBOBOX_DROPDOWN_WIDTH = "22px"
    COMBOBOX_ARROW_SIZE = "4px"
    COMBOBOX_POPUP_BORDER_RADIUS = "5px"

    # ── TextEdit / TextBrowser ───────────────────────────────────
    TEXT_EDIT_PADDING = "10px"
    TEXT_EDIT_FONT_SIZE = "12px"

    # ── GroupBox ─────────────────────────────────────────────────
    GROUP_TITLE_LEFT = "6px"
    GROUP_TITLE_TOP = "-2px"
    GROUP_TITLE_PADDING = "0 8px"
    GROUP_TITLE_BORDER_RADIUS = "5px"
    GROUP_TITLE_LETTER_SPACING = "0.6px"

    # ── Letter Spacing ───────────────────────────────────────────
    LETTER_SPACING_TITLE = "1.2px"
    LETTER_SPACING_BADGE = "0.4px"
    LETTER_SPACING_GROUP = "0.6px"
    LETTER_SPACING_BUTTON = "0.4px"
    LETTER_SPACING_BUTTON_PRIMARY = "0.6px"
    LETTER_SPACING_HEADER = "0.4px"
    LETTER_SPACING_TOOL_SELECTOR = "0.4px"
    LETTER_SPACING_WINDOW_TITLE = "0.4px"

    # ── Window Title ─────────────────────────────────────────────
    WINDOW_TITLE_FONT_SIZE = "11px"
    WINDOW_TITLE_LETTER_SPACING = "0.4px"

    # ── Title Bar ────────────────────────────────────────────────
    TITLE_BAR_BORDER_WIDTH = "1px"
    TITLE_BAR_BORDER_COLOR = ""

    # ── Card ─────────────────────────────────────────────────────
    CARD_PADDING_V = "18px"
    CARD_PADDING_H = "12px"

    # ── Splitter ─────────────────────────────────────────────────
    SPLITTER_HANDLE_WIDTH_H = "4px"
    SPLITTER_HANDLE_WIDTH_V = "4px"

    # ── Menu ─────────────────────────────────────────────────────
    MENU_PADDING = "3px"
    MENU_MARGIN_V = "1px 0"
    MENU_ITEM_PADDING = "5px 18px 5px 10px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "3px 8px"

    # ── Table / Header ───────────────────────────────────────────
    HEADER_FONT_SIZE = "11px"
    HEADER_LETTER_SPACING = "0.4px"
    TABLE_ITEM_PADDING = "4px 8px"
    HEADER_PADDING = "5px 8px"

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
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
    TEXT_GOLD = ACCENT_TEXT
    TEXT_GOLD_BRIGHT = ACCENT_BRIGHT

    # ── Acento (GOLD*) → ACCENT ─────────────────────────────────────
    GOLD = ACCENT
    GOLD_HOVER = ACCENT_HOVER
    GOLD_ACTIVE = ACCENT_ACTIVE
    GOLD_DIM = ACCENT_DIM
    GOLD_LIGHT = ACCENT_LIGHT
    GOLD_GRADIENT = ACCENT_GRADIENT

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