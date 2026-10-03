# -*- coding: utf-8 -*-
"""
NeonAccentTheme — tema "Ouro Neon" para o Aetheris ToolBox
============================================================
Baseado no estilo `estilo_3_neon_accent` (paineis_dourados_v2.py):
fundo quase-preto, tipografia dourada e um único acento (ouro) que
"brilha" via glow forte em vez de depender de várias cores vibrantes.

Conceito de design
-------------------
- Fundo: quase-preto neutro, sem tons quentes, pra o ouro ser a única
  fonte de "cor" da interface (contraste = drama).
- Acento: uma única família de ouro (_GOLD_*) reaproveitada em botões,
  bordas de foco, seleção de tabs e nos glows — nunca hardcoded de novo.
- Glow: em vez de sombra escura tradicional, os elementos de destaque
  (botão primário, tab selecionada, badge) usam um "halo" dourado
  translúcido — por isso GLOW_BUTTON_ENABLED / GLOW_TAB_ENABLED = True.
- Status (success/warning/danger/info): cores neon próprias, para não
  competir com o ouro, mas mantendo a mesma saturação "elétrica".
"""

from __future__ import annotations

from core.enum.GradientType import GradientType
from resources.styles.BaseTheme import BaseTheme # ajuste o import conforme a estrutura do projeto


# ═══════════════════════════════════════════════════════════════════════
# PALETA — única fonte de verdade. Tudo abaixo reaproveita estas cores.
# ═══════════════════════════════════════════════════════════════════════

# ── Superfícies (do mais profundo ao mais alto) ──
_VOID = "#050506"        # SURFACE_0 — backdrop absoluto
_BASE = "#0b0b0d"         # SURFACE_1 — fundo da janela
_PANEL = "#121214"        # SURFACE_2 — painéis laterais
_CARD = "#18181b"         # SURFACE_3 — cards / groupbox
_ELEVATED = "#1f1f23"     # SURFACE_4 — inputs / tabelas
_HOVER_SURFACE = "#28282d"  # SURFACE_5 — hover/focus
_TITLE_BAR = "#08080a"

# ── Ouro (acento único, reaproveitado em tudo) ──
_GOLD_DEEP = "#8a7238"     # sombra do ouro / dim
_GOLD_MUTED = "#b8912f"    # ouro "frio", usado em stops de gradiente
_GOLD_CORE = "#e8c76a"     # ACCENT principal
_GOLD_HOVER = "#f0d783"    # hover do acento
_GOLD_ACTIVE = "#c9ab5c"   # pressed do acento
_GOLD_LIGHT = "#f4e3ab"    # badges / highlights sutis
_GOLD_BRIGHT = "#fff6d8"   # glow / topo do gradiente
_GOLD_SOFT_RGBA = "rgba(232, 199, 106, 0.16)"   # fundo translúcido (badge outline etc.)
_GOLD_SOFT_RGBA_STRONG = "rgba(232, 199, 106, 0.30)"

# ── Texto ──
_TEXT_HIGH = "#f3ead2"
_TEXT_MEDIUM = "#c9ab5c"
_TEXT_LOW = "#a8925a"
_TEXT_DISABLED = "#5c5442"

# ── Bordas / divisores ──
_BORDER_SUBTLE = "#1c1a15"
_BORDER_DEFAULT = "#2e2a1f"
_BORDER_STRONG = "#4a3f26"
_DIVIDER = "#221f17"

# ── Status (neon próprio, mesma "temperatura elétrica" do ouro) ──
_SUCCESS = "#4ade80"
_SUCCESS_HOVER = "#79ecA0"
_SUCCESS_DIM = "#2f9d5c"
_WARNING = "#ffb84d"
_WARNING_HOVER = "#ffcb75"
_WARNING_DIM = "#c98a2e"
_DANGER = "#ff5c5c"
_DANGER_HOVER = "#ff8080"
_DANGER_DIM = "#c53a3a"
_INFO = "#4cc9f0"
_INFO_HOVER = "#79d8f4"
_INFO_DIM = "#2f9dbf"

# ── Sombra base (neutra, só para profundidade de cards) ──
_SHADOW_RGB = "#000000"

# ── Tipografia ──
_FONT_DEFAULT = '"Poppins", "Segoe UI", sans-serif'
_FONT_MONO = '"JetBrains Mono", "Consolas", monospace'


class NeonAccentTheme(BaseTheme):
    """Tema escuro com acento único em ouro e glow forte (estilo 'Neon Accent')."""

    # ═══════════════════════════════════════════════════════════
    # ACCENT
    # ═══════════════════════════════════════════════════════════
    ACCENT = _GOLD_CORE
    ACCENT_HOVER = _GOLD_HOVER
    ACCENT_ACTIVE = _GOLD_ACTIVE
    ACCENT_DIM = _GOLD_DEEP
    ACCENT_LIGHT = _GOLD_LIGHT
    ACCENT_SOFT = _GOLD_SOFT_RGBA
    ACCENT_TEXT = _GOLD_CORE
    ACCENT_BRIGHT = _GOLD_BRIGHT
    ACCENT_GRADIENT = (_GOLD_MUTED, _GOLD_CORE)

    # ═══════════════════════════════════════════════════════════
    # SURFACE
    # ═══════════════════════════════════════════════════════════
    SURFACE_0 = _VOID
    SURFACE_1 = _BASE
    SURFACE_2 = _PANEL
    SURFACE_3 = _CARD
    SURFACE_4 = _ELEVATED
    SURFACE_5 = _HOVER_SURFACE
    TITLE_BAR = _TITLE_BAR

    GRADIENT_BUTTON = (_ELEVATED, _CARD)
    GRADIENT_PANEL = (_PANEL, _BASE)
    GRADIENT_TAB = (_CARD, _PANEL)
    GRADIENT_INPUT = (_ELEVATED, _CARD)

    # Gradiente rico do acento — reflete o botão da referência
    # (stop:0 muted -> stop:0.5 core -> stop:1 muted), horizontal.
    GRADIENT_ACCENT_STOPS = (
        (0.0, _GOLD_MUTED),
        (0.5, _GOLD_CORE),
        (1.0, _GOLD_MUTED),
    )
    GRADIENT_ACCENT_ANGLE = 0

    GLOW_BUTTON_ENABLED = True
    GLOW_TAB_ENABLED = True

    # ═══════════════════════════════════════════════════════════
    # TEXT
    # ═══════════════════════════════════════════════════════════
    TEXT_HIGH = _TEXT_HIGH
    TEXT_MEDIUM = _TEXT_MEDIUM
    TEXT_LOW = _TEXT_LOW
    TEXT_DISABLED = _TEXT_DISABLED
    TEXT_ON_ACCENT = "#241a05"
    TEXT_ON_DANGER = "#1a0505"

    # ═══════════════════════════════════════════════════════════
    # BORDER
    # ═══════════════════════════════════════════════════════════
    BORDER_SUBTLE = _BORDER_SUBTLE
    BORDER_DEFAULT = _BORDER_DEFAULT
    BORDER_STRONG = _BORDER_STRONG
    BORDER_ACCENT = _GOLD_CORE
    DIVIDER = _DIVIDER
    BORDER_GRADIENT_STOPS = (
        (0.0, _GOLD_DEEP),
        (0.5, _GOLD_LIGHT),
        (1.0, _GOLD_DEEP),
    )
    BORDER_GRADIENT_WIDTH = 1.2

    # ═══════════════════════════════════════════════════════════
    # SHADOW / GLOW — o glow é o protagonista visual deste tema
    # ═══════════════════════════════════════════════════════════
    SHADOW_SM = "rgba(0, 0, 0, 0.35)"
    SHADOW_MD = "rgba(0, 0, 0, 0.45)"
    SHADOW_LG = "rgba(0, 0, 0, 0.55)"
    SHADOW_XL = "rgba(0, 0, 0, 0.65)"
    SHADOW_ACCENT = "rgba(232, 199, 106, 0.35)"
    GLOW = "rgba(232, 199, 106, 0.25)"
    GLOW_STRONG = "rgba(232, 199, 106, 0.55)"

    SHADOW_BLUR_SM = 12
    SHADOW_BLUR_MD = 24
    SHADOW_BLUR_LG = 40
    SHADOW_BLUR_XL = 55
    SHADOW_OFFSET_Y_SM = 2
    SHADOW_OFFSET_Y_MD = 8
    SHADOW_OFFSET_Y_LG = 14
    SHADOW_COLOR_RGB = _SHADOW_RGB
    SHADOW_COLOR_ALPHA = 170

    # Glow forte, como no título "Nível Black" da referência (blur 45, alpha ~200)
    GLOW_BLUR = 45
    GLOW_OFFSET_X = 0
    GLOW_OFFSET_Y = 0
    GLOW_COLOR_RGB = _GOLD_CORE
    GLOW_ALPHA = 200
    GLOW_STRONG_BLUR = 60
    GLOW_STRONG_ALPHA = 235

    # ═══════════════════════════════════════════════════════════
    # RADIUS
    # ═══════════════════════════════════════════════════════════
    RADIUS_XS = 2
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 14
    RADIUS_XL = 20
    RADIUS_FULL = 999

    # ═══════════════════════════════════════════════════════════
    # SPACE
    # ═══════════════════════════════════════════════════════════
    SPACE_XXS = 2
    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 12
    SPACE_LG = 16
    SPACE_XL = 24
    SPACE_2XL = 32
    SPACE_3XL = 48

    # ═══════════════════════════════════════════════════════════
    # ICON
    # ═══════════════════════════════════════════════════════════
    ICON_XS = 12
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 24
    ICON_XL = 32
    TOOLBAR_ICON_SIZE = 40
    TOOLBAR_BTN_SIZE = 40
    TOOLBAR_BTN_HOVER_GROW = 4

    # ═══════════════════════════════════════════════════════════
    # ANIMATION
    # ═══════════════════════════════════════════════════════════
    ANIMATION_FAST = 120
    ANIMATION_NORMAL = 180
    ANIMATION_SLOW = 280
    EASING_STANDARD = "cubic-bezier(0.4, 0.0, 0.2, 1)"

    # ═══════════════════════════════════════════════════════════
    # OPACITY
    # ═══════════════════════════════════════════════════════════
    OPACITY_DISABLED = 0.35
    OPACITY_MUTED = 0.60
    OPACITY_HOVER = 0.88
    OPACITY_ACTIVE = 1.0

    # ═══════════════════════════════════════════════════════════
    # LAYOUT
    # ═══════════════════════════════════════════════════════════
    PAGE_PADDING = 24
    SECTION_GAP = 32
    GRID_GAP = 16
    CONTENT_MAX_WIDTH = 1200

    # ═══════════════════════════════════════════════════════════
    # ELEVATION
    # ═══════════════════════════════════════════════════════════
    ELEVATION_FLAT = 0
    ELEVATION_LOW = 1
    ELEVATION_MEDIUM = 2
    ELEVATION_HIGH = 3

    # ═══════════════════════════════════════════════════════════
    # OVERLAY
    # ═══════════════════════════════════════════════════════════
    OVERLAY_BG = "rgba(5, 5, 6, 0.72)"
    BACKDROP_BLUR = "6px"

    # ═══════════════════════════════════════════════════════════
    # FOCUS_RING
    # ═══════════════════════════════════════════════════════════
    FOCUS_RING_COLOR = _GOLD_CORE
    FOCUS_RING_WIDTH = "2px"
    FOCUS_RING_OFFSET = "1px"

    # ═══════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════
    COLOR_SUCCESS = _SUCCESS
    COLOR_SUCCESS_HOVER = _SUCCESS_HOVER
    COLOR_SUCCESS_DIM = _SUCCESS_DIM
    COLOR_WARNING = _WARNING
    COLOR_WARNING_HOVER = _WARNING_HOVER
    COLOR_WARNING_DIM = _WARNING_DIM
    COLOR_DANGER = _DANGER
    COLOR_DANGER_HOVER = _DANGER_HOVER
    COLOR_DANGER_DIM = _DANGER_DIM
    COLOR_INFO = _INFO
    COLOR_INFO_HOVER = _INFO_HOVER
    COLOR_INFO_DIM = _INFO_DIM

    # ═══════════════════════════════════════════════════════════
    # FONT
    # ═══════════════════════════════════════════════════════════
    FONT_FAMILY_DEFAULT = _FONT_DEFAULT
    FONT_FAMILY_MONO = _FONT_MONO
    FONT_FAMILY_DISPLAY = ""  # usa FONT_FAMILY_DEFAULT (o estilo neon não usa serifa)
    FONT_LETTER_SPACING_DISPLAY = 1

    FONT_SIZE_TITLE = "30px"
    FONT_SIZE_BIG = "22px"
    FONT_SIZE_NORMAL = "14px"
    FONT_SIZE_SMALL = "12px"
    FONT_SIZE_TINY = "11px"

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ═══════════════════════════════════════════════════════════
    # DIMENSIONS
    # ═══════════════════════════════════════════════════════════
    INPUT_HEIGHT = 36
    BUTTON_HEIGHT = 36
    BUTTON_HEIGHT_PRIMARY = 40
    ITEM_HEIGHT = 32
    CHECKBOX_SIZE = "16px"
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = "10px"
    SCROLLBAR_MIN_HEIGHT = "24px"
    TAB_HEIGHT = 34
    TAB_CLOSE_BUTTON_SIZE = "16px"
    CLOSE_BUTTON_BORDER_RADIUS = "4px"
    PROGRESS_BAR_HEIGHT = "6px"
    TITLE_BTN_HEIGHT = "30px"
    TITLE_BTN_WIDTH = "44px"
    TITLE_BTN_FONT_SIZE = "12px"
    TOOLBAR_BTN_SIZE = 32
    TOOLBAR_BTN_HOVER_GROW = 2
    GROUP_MARGIN_TOP = "14px"
    SPLITTER_HANDLE_WIDTH = "4px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Border radius
    # ═══════════════════════════════════════════════════════════
    BORDER_RADIUS_CARD = "14px"
    BORDER_RADIUS_BUTTON = "10px"
    BORDER_RADIUS_INPUT = "8px"
    BORDER_RADIUS_CHECKBOX = "4px"
    BORDER_RADIUS_RADIO = "999px"
    BORDER_RADIUS_BADGE = "11px"
    BORDER_RADIUS_PROGRESS = "4px"
    BORDER_RADIUS_TABLE = "10px"
    BORDER_RADIUS_TITLE_BTN = "6px"
    BORDER_RADIUS_TOOLBAR_BTN = "4px"
    BORDER_RADIUS_GHOST = "8px"
    BORDER_RADIUS_TOOL_SELECTOR = "8px"
    BORDER_RADIUS_SCROLLBAR = "5px"
    BORDER_RADIUS_SPINBOX_BTN = "4px"
    BORDER_RADIUS_TAB_CLOSE = "4px"
    BORDER_RADIUS_MENU = "10px"
    BORDER_RADIUS_MENU_ITEM = "6px"
    BORDER_RADIUS_GROUP_TITLE = "4px"
    BORDER_RADIUS_DIALOG = "16px"
    MENUBAR_ITEM_BORDER_RADIUS = "6px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Checkbox
    # ═══════════════════════════════════════════════════════════
    CHECKBOX_BORDER_WIDTH = 1
    CHECKBOX_SPACING = "8px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Badge (outline dourado, como na referência)
    # ═══════════════════════════════════════════════════════════
    BADGE_PADDING_V = "4px"
    BADGE_PADDING_H = "14px"
    BADGE_LETTER_SPACING = "2px"
    BADGE_OUTLINE_ENABLED = True
    BADGE_OUTLINE_BORDER_WIDTH = 1
    BADGE_OUTLINE_BG_ALPHA = 18

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Button
    # ═══════════════════════════════════════════════════════════
    BUTTON_PADDING_V = "10px"
    BUTTON_PADDING_H = "22px"
    BUTTON_PADDING_V_SMALL = "6px"
    BUTTON_PADDING_H_SMALL = "14px"
    BUTTON_PADDING_V_PRIMARY = "11px"
    BUTTON_PADDING_H_PRIMARY = "26px"
    BUTTON_LETTER_SPACING_NORMAL = "0.5px"
    BUTTON_LETTER_SPACING_PRIMARY = "1px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Toolbar
    # ═══════════════════════════════════════════════════════════
    TOOLBAR_BTN_PADDING_V = "6px"
    TOOLBAR_BTN_PADDING_H = "8px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Tool selector
    # ═══════════════════════════════════════════════════════════
    TOOL_SELECTOR_PADDING_V = "6px"
    TOOL_SELECTOR_PADDING_H = "12px"
    TOOL_SELECTOR_LETTER_SPACING = "1px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Input
    # ═══════════════════════════════════════════════════════════
    INPUT_PADDING_V = "8px"
    INPUT_PADDING_H = "10px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — SpinBox
    # ═══════════════════════════════════════════════════════════
    SPINBOX_PADDING = "6px"
    SPINBOX_BTN_WIDTH = "18px"
    SPINBOX_BTN_MARGIN = "1px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — ComboBox
    # ═══════════════════════════════════════════════════════════
    COMBOBOX_PADDING = "8px"
    COMBOBOX_MIN_WIDTH = "120px"
    COMBOBOX_DROPDOWN_WIDTH = "24px"
    COMBOBOX_ARROW_SIZE = "10px"
    COMBOBOX_POPUP_BORDER_RADIUS = "10px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — TextEdit
    # ═══════════════════════════════════════════════════════════
    TEXT_EDIT_PADDING = "8px"
    TEXT_EDIT_FONT_SIZE = "13px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — GroupBox
    # ═══════════════════════════════════════════════════════════
    GROUP_TITLE_LEFT = "12px"
    GROUP_TITLE_TOP = "-8px"
    GROUP_TITLE_PADDING = "0px 6px"
    GROUP_TITLE_BORDER_RADIUS = "4px"
    GROUP_TITLE_LETTER_SPACING = "1px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Letter spacing
    # ═══════════════════════════════════════════════════════════
    LETTER_SPACING_TITLE = "1px"
    LETTER_SPACING_BADGE = "2px"
    LETTER_SPACING_GROUP = "1px"
    LETTER_SPACING_BUTTON = "0.5px"
    LETTER_SPACING_BUTTON_PRIMARY = "1px"
    LETTER_SPACING_HEADER = "1px"
    LETTER_SPACING_TOOL_SELECTOR = "1px"
    LETTER_SPACING_WINDOW_TITLE = "2px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Window title
    # ═══════════════════════════════════════════════════════════
    WINDOW_TITLE_FONT_SIZE = "12px"
    WINDOW_TITLE_LETTER_SPACING = "2px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Title bar
    # ═══════════════════════════════════════════════════════════
    TITLE_BAR_BORDER_WIDTH = "1px"
    TITLE_BAR_BORDER_COLOR = ""  # cai para SURFACE_2 (BG_PANEL) como fallback

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Card
    # ═══════════════════════════════════════════════════════════
    CARD_PADDING_V = "50px"
    CARD_PADDING_H = "60px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Splitter
    # ═══════════════════════════════════════════════════════════
    SPLITTER_HANDLE_WIDTH_H = "4px"
    SPLITTER_HANDLE_WIDTH_V = "4px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Menu
    # ═══════════════════════════════════════════════════════════
    MENU_PADDING = "6px"
    MENU_MARGIN_V = "4px"
    MENU_ITEM_PADDING = "8px 12px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "4px 8px"

    # ═══════════════════════════════════════════════════════════
    # SPECIFICS — Table / Header
    # ═══════════════════════════════════════════════════════════
    HEADER_FONT_SIZE = "12px"
    HEADER_LETTER_SPACING = "1px"
    TABLE_ITEM_PADDING = "6px 10px"
    HEADER_PADDING = "8px 10px"

    # ═══════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE
    # (mantidos alinhados manualmente com os tokens semânticos acima,
    #  todos reaproveitando as mesmas variáveis de paleta)
    # ═══════════════════════════════════════════════════════════
    BG_DEEPEST = _VOID
    BG_DARK = _BASE
    BG_PANEL = _PANEL
    BG_CARD = _CARD
    BG_ELEVATED = _ELEVATED
    BG_SURFACE = _HOVER_SURFACE
    TITLE_BAR_BG = _TITLE_BAR

    SHADOW = SHADOW_SM
    SHADOW_DEEP = SHADOW_LG

    BORDER = _BORDER_DEFAULT
    BORDER_HOVER = _GOLD_CORE

    TEXT_BRIGHT = _TEXT_HIGH
    TEXT_PRIMARY = _TEXT_MEDIUM
    TEXT_SECONDARY = _TEXT_LOW
    TEXT_MUTED = _TEXT_DISABLED
    TEXT_ACCENT = _GOLD_CORE
    TEXT_ACCENT_BRIGHT = _GOLD_BRIGHT

    ACCENT_COLOR = _GOLD_CORE
    ACCENT_COLOR_HOVER = _GOLD_HOVER
    ACCENT_COLOR_ACTIVE = _GOLD_ACTIVE
    ACCENT_COLOR_DIM = _GOLD_DEEP
    ACCENT_COLOR_LIGHT = _GOLD_LIGHT
    ACCENT_COLOR_GRADIENT = (_GOLD_MUTED, _GOLD_CORE)

    SUCCESS = _SUCCESS
    SUCCESS_HOVER = _SUCCESS_HOVER
    SUCCESS_DIM = _SUCCESS_DIM
    WARNING = _WARNING
    WARNING_HOVER = _WARNING_HOVER
    WARNING_DIM = _WARNING_DIM
    DANGER = _DANGER
    DANGER_HOVER = _DANGER_HOVER
    DANGER_DIM = _DANGER_DIM