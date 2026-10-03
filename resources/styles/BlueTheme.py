# -*- coding: utf-8 -*-
"""
ModernDashboardTheme
====================

Tema inspirado no dashboard:
https://dribbble.com/shots/23707627-Modern-Dashboard-UI-Design

Este tema herda de BaseTheme e preenche os tokens mais relevantes.

⚠ CONVENÇÃO DE UNIDADES
------------------------
Todo token consumido apenas dentro de QSS (BaseStyle.global_stylesheet)
já carrega sua unidade como string (ex: "12px", "-6px", "999px").
O BaseStyle NUNCA concatena "px" — apenas interpola {t.TOKEN} puro.
Isso evita bugs como "20pxpx" ou "0.5pxpx".

Tokens que são consumidos como valor numérico puro em código Python
(QSize, setFixedHeight, setDuration, blur/offset de sombra, etc.)
permanecem como int/float, pois converter para string quebraria
essas chamadas. Ex: ICON_*, ANIMATION_*, RADIO_SIZE, TOOLBAR_ICON_SIZE,
TOOLBAR_BTN_SIZE, TOOLBAR_BTN_HOVER_GROW, BUTTON_HEIGHT*, INPUT_HEIGHT,
ITEM_HEIGHT, TAB_HEIGHT.
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


class BlueTheme(BaseTheme):

    # ==========================================================
    # ACCENT
    # ==========================================================
    ACCENT = "#1EA7FF"
    ACCENT_HOVER = "#42B8FF"
    ACCENT_ACTIVE = "#0F8CE6"
    ACCENT_DIM = "#0A5FA8"
    ACCENT_LIGHT = "#8FD6FF"
    ACCENT_SOFT = "rgba(30, 167, 255, 0.14)"
    ACCENT_TEXT = "#EAF7FF"
    ACCENT_BRIGHT = "#FFFFFF"
    ACCENT_GRADIENT = ("#2CC4FF", "#1E8BFF")

    # ==========================================================
    # SURFACES
    # ==========================================================
    SURFACE_0 = "#050B1A"
    SURFACE_1 = "#081426"
    SURFACE_2 = "#0C1D35"
    SURFACE_3 = "#102744"
    SURFACE_4 = "#183355"
    SURFACE_5 = "#21426B"
    TITLE_BAR = "#081426"

    GRADIENT_BUTTON = ("#163458", "#1E4470")
    GRADIENT_PANEL = ("#0C1D35", "#113055")
    GRADIENT_TAB = ("#102744", "#16365D")
    GRADIENT_INPUT = ("#183355", "#21426B")

    # ==========================================================
    # TEXT
    # ==========================================================
    TEXT_HIGH = "#FFFFFF"
    TEXT_MEDIUM = "#D9E9FF"
    TEXT_LOW = "#8FAFD4"
    TEXT_DISABLED = "#58739A"
    TEXT_ON_ACCENT = "#FFFFFF"
    TEXT_ON_DANGER = "#FFFFFF"

    # ==========================================================
    # BORDERS
    # ==========================================================
    BORDER_SUBTLE = "rgba(255,255,255,0.04)"
    BORDER_DEFAULT = "rgba(140,190,255,0.08)"
    BORDER_STRONG = "rgba(140,190,255,0.16)"
    BORDER_ACCENT = ACCENT
    DIVIDER = "rgba(255,255,255,0.05)"

    # ==========================================================
    # SHADOWS
    # ==========================================================
    SHADOW_SM = "rgba(0,0,0,0.16)"
    SHADOW_MD = "rgba(0,0,0,0.24)"
    SHADOW_LG = "rgba(0,0,0,0.34)"
    SHADOW_XL = "rgba(0,0,0,0.45)"
    SHADOW_ACCENT = "rgba(30,167,255,0.20)"
    GLOW = "rgba(30,167,255,0.12)"
    GLOW_STRONG = "rgba(30,167,255,0.25)"

    # ==========================================================
    # RADIUS (escala genérica — mantida numérica, uso em Python)
    # ==========================================================
    RADIUS_XS = 3
    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_XL = 16
    RADIUS_FULL = 999

    # ==========================================================
    # SPACING (escala genérica — mantida numérica, uso em Python)
    # ==========================================================
    SPACE_XXS = 2
    SPACE_XS = 4
    SPACE_SM = 6
    SPACE_MD = 10
    SPACE_LG = 14
    SPACE_XL = 20
    SPACE_2XL = 28
    SPACE_3XL = 40

    # ==========================================================
    # ICON — usados como int (QSize) em código Python, sem unidade
    # ==========================================================
    ICON_XS = 12
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 24
    ICON_XL = 32
    TOOLBAR_ICON_SIZE = 40
    TOOLBAR_BTN_SIZE = 36
    TOOLBAR_BTN_HOVER_GROW = 6

    # ==========================================================
    # ANIMATION — milissegundos, uso em setDuration() (int)
    # ==========================================================
    ANIMATION_FAST = 120
    ANIMATION_NORMAL = 180
    ANIMATION_SLOW = 260
    EASING_STANDARD = "cubic-bezier(0.4, 0, 0.2, 1)"

    # ==========================================================
    # OPACITY (float 0..1, sem unidade)
    # ==========================================================
    OPACITY_DISABLED = 0.35
    OPACITY_MUTED = 0.60
    OPACITY_HOVER = 0.85
    OPACITY_ACTIVE = 1.0

    # ==========================================================
    # LAYOUT — mantidos numéricos (uso em código Python / layouts)
    # ==========================================================
    PAGE_PADDING = 18
    SECTION_GAP = 18
    GRID_GAP = 14
    CONTENT_MAX_WIDTH = 1600

    # ==========================================================
    # ELEVATION (índice, sem unidade)
    # ==========================================================
    ELEVATION_FLAT = 0
    ELEVATION_LOW = 1
    ELEVATION_MEDIUM = 2
    ELEVATION_HIGH = 3

    # ==========================================================
    # OVERLAY / Glass
    # ==========================================================
    OVERLAY_BG = "rgba(0, 0, 0, 0.60)"
    BACKDROP_BLUR = "6px"

    # ==========================================================
    # FOCUS_RING
    # ==========================================================
    FOCUS_RING_COLOR = "#1EA7FF"
    FOCUS_RING_WIDTH = "2px"
    FOCUS_RING_OFFSET = "1px"

    # ==========================================================
    # STATUS
    # ==========================================================
    COLOR_SUCCESS = "#22C55E"
    COLOR_SUCCESS_HOVER = "#34D399"
    COLOR_SUCCESS_DIM = "#14532D"

    COLOR_WARNING = "#F59E0B"
    COLOR_WARNING_HOVER = "#FBBF24"
    COLOR_WARNING_DIM = "#78350F"

    COLOR_DANGER = "#EF4444"
    COLOR_DANGER_HOVER = "#F87171"
    COLOR_DANGER_DIM = "#7F1D1D"

    COLOR_INFO = "#38BDF8"
    COLOR_INFO_HOVER = "#7DD3FC"
    COLOR_INFO_DIM = "#0C4A6E"

    # ==========================================================
    # FONT
    # ==========================================================
    FONT_FAMILY_DEFAULT = "'Segoe UI', 'Inter', sans-serif"
    FONT_FAMILY_MONO = "'Cascadia Code', 'Consolas', monospace"

    # >>> convertidos para string com unidade (consumidos só em QSS) <
    FONT_SIZE_TITLE = "32px"
    FONT_SIZE_BIG = "18px"
    FONT_SIZE_NORMAL = "12px"
    FONT_SIZE_SMALL = "11px"
    FONT_SIZE_TINY = "10px"

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ==========================================================
    # DIMENSIONS
    # ==========================================================
    # mantidos como int — usados em setFixedHeight/QSize no Python
    INPUT_HEIGHT = 34
    BUTTON_HEIGHT = 34
    BUTTON_HEIGHT_PRIMARY = 38
    ITEM_HEIGHT = 30
    RADIO_SIZE = 16
    TAB_HEIGHT = 32

    # >>> convertidos para string com unidade (usados em QSS) <
    CHECKBOX_SIZE = "16px"
    SCROLLBAR_WIDTH = "8px"
    SCROLLBAR_MIN_HEIGHT = "24px"
    TAB_CLOSE_BUTTON_SIZE = "12px"
    PROGRESS_BAR_HEIGHT = "8px"
    TITLE_BTN_HEIGHT = "30px"
    TITLE_BTN_WIDTH = "44px"
    GROUP_MARGIN_TOP = "14px"
    SPLITTER_HANDLE_WIDTH = "3px"

    # ==========================================================
    # SPECIFIC RADII — >>> todos convertidos para string com "px" <
    # (família BORDER_RADIUS_* é 100% consumida em QSS)
    # ==========================================================
    BORDER_RADIUS_CARD = "14px"
    BORDER_RADIUS_BUTTON = "999px"
    BORDER_RADIUS_INPUT = "8px"
    BORDER_RADIUS_CHECKBOX = "4px"
    BORDER_RADIUS_RADIO = "999px"
    BORDER_RADIUS_BADGE = "999px"
    BORDER_RADIUS_PROGRESS = "999px"
    BORDER_RADIUS_TABLE = "12px"
    BORDER_RADIUS_TITLE_BTN = "6px"
    BORDER_RADIUS_TOOLBAR_BTN = "999px"
    BORDER_RADIUS_GHOST = "999px"
    BORDER_RADIUS_TOOL_SELECTOR = "999px"
    BORDER_RADIUS_SCROLLBAR = "999px"
    BORDER_RADIUS_SPINBOX_BTN = "4px"
    BORDER_RADIUS_TAB_CLOSE = "999px"
    BORDER_RADIUS_COMBO_POPUP = "10px"
    BORDER_RADIUS_MENU = "12px"
    BORDER_RADIUS_MENU_ITEM = "8px"
    BORDER_RADIUS_GROUP_TITLE = "6px"
    BORDER_RADIUS_DIALOG = "16px"
    MENUBAR_ITEM_BORDER_RADIUS = "6px"
    CLOSE_BUTTON_BORDER_RADIUS = "6px"

    # ==========================================================
    # PADDINGS / SPECIFICS (já eram strings com unidade — mantidos)
    # ==========================================================
    BADGE_PADDING_V = "2px"
    BADGE_PADDING_H = "8px"
    BADGE_LETTER_SPACING = "0.3px"

    BUTTON_PADDING_V = "2px"
    BUTTON_PADDING_H = "2px"
    BUTTON_PADDING_V_SMALL = "2px"
    BUTTON_PADDING_H_SMALL = "2px"
    BUTTON_PADDING_V_PRIMARY = "2px"
    BUTTON_PADDING_H_PRIMARY = "2px"

    BUTTON_LETTER_SPACING_NORMAL = "0.2px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.4px"

    TOOLBAR_BTN_PADDING_V = "6px"
    TOOLBAR_BTN_PADDING_H = "10px"

    TOOL_SELECTOR_PADDING_V = "6px"
    TOOL_SELECTOR_PADDING_H = "10px"
    TOOL_SELECTOR_LETTER_SPACING = "0.3px"

    INPUT_PADDING_V = "6px"
    INPUT_PADDING_H = "10px"

    SPINBOX_PADDING = "4px 8px"
    # >>> convertido: usado com px em QSS <
    SPINBOX_BTN_WIDTH = "18px"
    SPINBOX_BTN_MARGIN = "1px"

    COMBOBOX_PADDING = "6px 10px"
    # >>> convertidos: usados com px em QSS <
    COMBOBOX_MIN_WIDTH = "100px"
    COMBOBOX_DROPDOWN_WIDTH = "22px"
    COMBOBOX_ARROW_SIZE = "4px"

    TEXT_EDIT_PADDING = "10px"
    # >>> convertido <
    TEXT_EDIT_FONT_SIZE = "11px"

    # >>> convertidos: usados com px em QSS (GROUP_TITLE_TOP é negativo) <
    GROUP_TITLE_LEFT = "8px"
    GROUP_TITLE_TOP = "-6px"
    GROUP_TITLE_PADDING = "2px 6px"
    GROUP_TITLE_LETTER_SPACING = "0.3px"

    # >>> convertido <
    HEADER_FONT_SIZE = "10px"
    HEADER_LETTER_SPACING = "0.3px"
    TABLE_ITEM_PADDING = "6px"
    HEADER_PADDING = "8px 10px"

    # >>> convertido <
    WINDOW_TITLE_FONT_SIZE = "11px"
    WINDOW_TITLE_LETTER_SPACING = "0.2px"
    # >>> convertido <
    TITLE_BTN_FONT_SIZE = "13px"

    CARD_PADDING_V = "14px"
    CARD_PADDING_H = "14px"

    MENU_PADDING = "6px"
    MENU_MARGIN_V = "4px"
    MENU_ITEM_PADDING = "6px 10px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "4px 6px"

    CHECKBOX_BORDER_WIDTH = 1
    # >>> convertido: usado como "spacing: {t.X}px" em QSS <
    CHECKBOX_SPACING = "6px"

    # ==========================================================
    # LEGACY ALIASES
    # ==========================================================
    BG_DEEPEST = SURFACE_0
    BG_DARK = SURFACE_1
    BG_PANEL = SURFACE_2
    BG_CARD = SURFACE_3
    BG_ELEVATED = SURFACE_4
    BG_SURFACE = SURFACE_5
    TITLE_BAR_BG = TITLE_BAR

    SHADOW = SHADOW_MD
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

    COLOR_INFO = COLOR_INFO
    COLOR_INFO_HOVER = COLOR_INFO_HOVER
    COLOR_INFO_DIM = COLOR_INFO_DIM