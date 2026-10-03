# -*- coding: utf-8 -*-
"""
AppStyles — Estilos específicos da aplicação
=============================================
Herda de BaseStyle e adiciona estilos de botões, badges, logs e menu.
Usa o tema atual via ThemeManager.

Regra de ouro deste arquivo:
    - A ÚNICA referência ao tema é `current_theme` (resolvida uma vez,
      no import do módulo, a partir de `theme_manager.theme`).
      Nenhum método deve fazer `t = theme_manager.theme` ou
      `theme_manager.theme.X` — sempre `current_theme.X`.
    - Nenhum valor após os dois-pontos do QSS é hardcoded quando o valor
      vem do tema. Ou seja: `font-size: {current_theme.FONT_SIZE_SMALL};`
      e NUNCA `font-size: {current_theme.FONT_SIZE_SMALL}px;`.
      A unidade (px, %, etc.) já vem embutida no valor do token, dentro
      do tema (ex.: FONT_SIZE_SMALL = "11px").

    ⚠ Nota: como `current_theme` é resolvido uma única vez no import do
    módulo, ele não reagirá a uma troca de tema em runtime feita depois
    do import. Se o projeto precisar de troca de tema dinâmica, isso deve
    ser resolvido no ThemeManager (ex.: recarregando o módulo ou expondo
    um objeto proxy), não neste arquivo — aqui seguimos estritamente o
    padrão pedido de uma única variável de acesso.
"""

from __future__ import annotations

from typing import Optional

from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import theme_manager

current_theme = theme_manager.theme


class AppStyles(BaseStyle):
    current_theme = current_theme
    """
    Estilos específicos: botões (secondary, primary, danger, ghost, remove),
    badges de status, logs coloridos e menus.
    Todo estilo busca valores do tema atual via `current_theme`.
    """

    # ────────────────────────────────────────────────────────────────────
    # BOTÕES
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def btn_secondary_style(cls) -> str:
        """
        Botao secundario — gradiente suave, hover com glow.
        Usa GRADIENT_BUTTON_STOPS com tipo e angulo do tema quando disponivel,
        ou GRADIENT_BUTTON (2-stop) como fallback.
        """
        grad = cls._gradient_qss_from_stops(
            current_theme.GRADIENT_BUTTON_STOPS,
            current_theme.GRADIENT_BUTTON_ANGLE,
            current_theme.GRADIENT_BUTTON[0],
            current_theme.GRADIENT_BUTTON[1],
            gradient_type=current_theme.GRADIENT_BUTTON_TYPE,
            cx=current_theme.GRADIENT_RADIAL_CX,
            cy=current_theme.GRADIENT_RADIAL_CY,
            fx=current_theme.GRADIENT_RADIAL_FX,
            fy=current_theme.GRADIENT_RADIAL_FY,
            radius=current_theme.GRADIENT_RADIAL_RADIUS,
        )
        return (
            f"QPushButton {{"
            f"  background: {grad};"
            f"  color: {current_theme.ACCENT_TEXT};"
            f"  border: none;"
            f"  border-radius: {current_theme.BORDER_RADIUS_BUTTON};"
            f"  padding: {current_theme.BUTTON_PADDING_V} {current_theme.BUTTON_PADDING_H};"
            f"  font-weight: {current_theme.FONT_WEIGHT_BOLD};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {current_theme.SURFACE_4};"
            f"  color: {current_theme.ACCENT_BRIGHT};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {current_theme.SURFACE_2};"
            f"}}"
        )

    @classmethod
    def btn_primary_style(cls) -> str:
        """
        Botao primario — gradiente.
        Usa GRADIENT_ACCENT_STOPS (3+ stops) com tipo, angulo e parametros
        do tema quando disponivel, ou ACCENT_GRADIENT (2 stops) como fallback
        para compatibilidade retroativa.

        Tipos de gradiente suportados (via GradientType):
            LINEAR  — gradiente linear com angulo (padrao)
            RADIAL  — gradiente radial com centro e ponto focal
            CONICAL — gradiente conico com centro e angulo inicial
        """
        bg_gradient = cls._gradient_qss_from_stops(
            current_theme.GRADIENT_ACCENT_STOPS,
            current_theme.GRADIENT_ACCENT_ANGLE,
            current_theme.ACCENT_GRADIENT[0],
            current_theme.ACCENT_GRADIENT[1],
            gradient_type=current_theme.GRADIENT_ACCENT_TYPE,
            cx=current_theme.GRADIENT_RADIAL_CX,
            cy=current_theme.GRADIENT_RADIAL_CY,
            fx=current_theme.GRADIENT_RADIAL_FX,
            fy=current_theme.GRADIENT_RADIAL_FY,
            radius=current_theme.GRADIENT_RADIAL_RADIUS,
        )
        hover_gradient = cls._gradient_qss_from_stops(
            (),
            45,
            current_theme.ACCENT_HOVER,
            current_theme.ACCENT,
        )
        return (
            f"QPushButton {{"
            f"  background: {bg_gradient};"
            f"  color: {current_theme.TEXT_ON_ACCENT};"
            f"  border: none;"
            f"  border-radius: {current_theme.BORDER_RADIUS_BUTTON};"
            f"  padding: {current_theme.BUTTON_PADDING_V_PRIMARY} {current_theme.BUTTON_PADDING_H_PRIMARY};"
            f"  font-weight: {current_theme.BUTTON_FONT_WEIGHT_PRIMARY or current_theme.FONT_WEIGHT_HEAVY};"
            f"  font-size: {current_theme.BUTTON_FONT_SIZE_PRIMARY or current_theme.FONT_SIZE_NORMAL};"
            f"  letter-spacing: {current_theme.BUTTON_LETTER_SPACING_PRIMARY};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {hover_gradient};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {current_theme.ACCENT_ACTIVE};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  color: {current_theme.TEXT_DISABLED};"
            f"}}"
        )

    @classmethod
    def btn_danger_style(cls) -> str:
        """Botao danger — vermelho escuro, sem borda."""
        return (
            f"QPushButton {{"
            f"  background-color: {current_theme.COLOR_DANGER_DIM};"
            f"  color: {current_theme.TEXT_ON_DANGER};"
            f"  border: none;"
            f"  border-radius: {current_theme.BORDER_RADIUS_BUTTON};"
            f"  padding: {current_theme.BUTTON_PADDING_V} {current_theme.BUTTON_PADDING_H};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"  letter-spacing: {current_theme.BUTTON_LETTER_SPACING_NORMAL};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {current_theme.COLOR_DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {current_theme.COLOR_DANGER_DIM};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  color: {current_theme.TEXT_DISABLED};"
            f"}}"
        )

    @classmethod
    def btn_ghost_style(cls) -> str:
        """Botao ghost — invisível, aparece no hover."""
        return (
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {current_theme.ACCENT_TEXT};"
            f"  border: none;"
            f"  border-radius: {current_theme.BORDER_RADIUS_GHOST};"
            f"  padding: {current_theme.BUTTON_PADDING_V_SMALL} {current_theme.BUTTON_PADDING_H_SMALL};"
            f"  font-weight: {current_theme.FONT_WEIGHT_BOLD};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {current_theme.SURFACE_2};"
            f"}}"
        )

    @classmethod
    def btn_remove_style(cls) -> str:
        """Botao remover — preto arredondado, fonte branca, hover vermelho."""
        return (
            f"QPushButton {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  color: {current_theme.TEXT_ON_DANGER};"
            f"  border: none;"
            f"  border-radius: {current_theme.BORDER_RADIUS_TABLE};"
            f"  padding: {current_theme.BUTTON_PADDING_V_SMALL} {current_theme.BUTTON_PADDING_H_SMALL};"
            f"  font-weight: {current_theme.FONT_WEIGHT_BOLD};"
            f"  font-size: {current_theme.FONT_SIZE_TINY};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {current_theme.COLOR_DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {current_theme.COLOR_DANGER_DIM};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # MENU BAR
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def menu_bar_style(cls) -> str:
        """Estilo da barra de menus."""
        return (
            f"QMenuBar#app_menu_bar {{"
            f"  background-color: {current_theme.TITLE_BAR};"
            f"  border: none;"
            f"  border-bottom: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  padding: 0;"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"  color: {current_theme.TEXT_LOW};"
            f"}}"
            f"QMenuBar::item {{"
            f"  background-color: transparent;"
            f"  color: {current_theme.TEXT_LOW};"
            f"  padding: 2px 10px;"
            f"  margin: 0;"
            f"}}"
            f"QMenuBar::item:hover {{"
            f"  background-color: {current_theme.ACCENT};"
            f"  color: {current_theme.SURFACE_0};"
            f"  border-radius: {current_theme.MENUBAR_ITEM_BORDER_RADIUS};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenuBar::item:selected {{"
            f"  background-color: {current_theme.ACCENT};"
            f"  color: {current_theme.SURFACE_0};"
            f"  border-radius: {current_theme.MENUBAR_ITEM_BORDER_RADIUS};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenuBar::item:pressed {{"
            f"  background-color: {current_theme.ACCENT_ACTIVE};"
            f"  color: {current_theme.SURFACE_0};"
            f"  border-radius: {current_theme.MENUBAR_ITEM_BORDER_RADIUS};"
            f"}}"
        )

    @classmethod
    def menu_dropdown_style(cls) -> str:
        """Estilo do QMenu dropdown."""
        return (
            f"QMenu {{"
            f"  background-color: {current_theme.SURFACE_0};"
            f"  border: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  border-radius: {current_theme.BORDER_RADIUS_MENU};"
            f"  padding: {current_theme.MENU_PADDING};"
            f"  margin: {current_theme.MENU_MARGIN_V};"
            f"}}"
            f"QMenu::item {{"
            f"  background-color: transparent;"
            f"  color: {current_theme.TEXT_MEDIUM};"
            f"  padding: {current_theme.MENU_ITEM_PADDING};"
            f"  border-radius: {current_theme.BORDER_RADIUS_MENU_ITEM};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"  border-left: 1px solid transparent;"
            f"}}"
            f"QMenu::item:hover {{"
            f"  background-color: {current_theme.ACCENT};"
            f"  color: {current_theme.SURFACE_0};"
            f"  border-left: 1px solid {current_theme.ACCENT_HOVER};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenu::item:selected {{"
            f"  background-color: {current_theme.ACCENT_HOVER};"
            f"  color: {current_theme.SURFACE_0};"
            f"  border-left: 1px solid {current_theme.ACCENT};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenu::item:disabled {{"
            f"  background-color: transparent;"
            f"  color: {current_theme.TEXT_DISABLED};"
            f"  border-left: 1px solid transparent;"
            f"}}"
            f"QMenu::separator {{"
            f"  height: {current_theme.MENU_SEPARATOR_HEIGHT};"
            f"  background: {current_theme.DIVIDER};"
            f"  margin: {current_theme.MENU_SEPARATOR_MARGIN};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # BADGES
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def badge_style(cls, bg_color: str, text_color: Optional[str] = None) -> str:
        """Badge preenchido padrão — fundo sólido, texto claro."""
        tc = text_color or current_theme.SURFACE_0
        return (
            f"QLabel {{"
            f"  background-color: {bg_color};"
            f"  color: {tc};"
            f"  border-radius: {current_theme.BORDER_RADIUS_BADGE};"
            f"  padding: {current_theme.BADGE_PADDING_V} {current_theme.BADGE_PADDING_H};"
            f"  font-weight: {current_theme.FONT_WEIGHT_HEAVY};"
            f"  font-size: {current_theme.FONT_SIZE_TINY};"
            f"  letter-spacing: {current_theme.BADGE_LETTER_SPACING};"
            f"}}"
        )

    @classmethod
    def badge_outline_style(cls, border_color: str, bg_color: str = "") -> str:
        """
        Badge estilo outline — borda colorida + fundo translúcido.

        Args:
            border_color: Cor da borda (ex: ACCENT, COLOR_SUCCESS).
            bg_color: Cor de fundo translúcido (ex: ACCENT_SOFT).
                      Vazio = usa ACCENT_SOFT do tema como fallback.

        Returns:
            String QSS para QLabel.
        """
        bg = bg_color or current_theme.ACCENT_SOFT
        return (
            f"QLabel {{"
            f"  background: {bg};"
            f"  border: {current_theme.BADGE_OUTLINE_BORDER_WIDTH}px solid {border_color};"
            f"  color: {border_color};"
            f"  border-radius: {current_theme.BORDER_RADIUS_BADGE};"
            f"  padding: {current_theme.BADGE_PADDING_V} {current_theme.BADGE_PADDING_H};"
            f"  font-weight: {current_theme.FONT_WEIGHT_HEAVY};"
            f"  font-size: {current_theme.FONT_SIZE_TINY};"
            f"  letter-spacing: {current_theme.BADGE_LETTER_SPACING};"
            f"}}"
        )

    @classmethod
    def tool_group_label_style(cls) -> str:
        """Estilo do label de título de um ToolGroup na toolbar."""
        return (
            f"QLabel {{"
            f"  color: {current_theme.TEXT_ACCENT};"
            f"  font-size: {current_theme.FONT_SIZE_TINY};"
            f"  padding: 0px;"
            f"  margin: 0px;"
            f"}}"
        )

    @classmethod
    def badge_success(cls) -> str:
        return cls.badge_style(current_theme.COLOR_SUCCESS)

    @classmethod
    def badge_running(cls) -> str:
        return cls.badge_style(current_theme.COLOR_WARNING)

    @classmethod
    def badge_error(cls) -> str:
        return cls.badge_style(current_theme.COLOR_DANGER)

    @classmethod
    def badge_canceled(cls) -> str:
        return cls.badge_style(current_theme.COLOR_WARNING)

    @classmethod
    def badge_info(cls) -> str:
        return cls.badge_style(current_theme.COLOR_INFO)

    # ────────────────────────────────────────────────────────────────────
    # DIALOG — Estilo base para QDialog
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def dialog_stylesheet(cls) -> str:
        """QSS genérico para QDialog. Nenhum hardcoded."""
        return (
            f"QDialog {{"
            f"  background-color: {current_theme.SURFACE_1};"
            f"  border: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  border-radius: {current_theme.BORDER_RADIUS_DIALOG};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # DIALOG CONTENT — borda fina para o content widget do BaseDialog
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def dialog_content_border_style(cls) -> str:
        """Borda sutil para o QWidget de conteúdo dentro do BaseDialog."""
        return (
            f"QWidget#dialog_content {{"
            f"  border: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  border-radius: {current_theme.RADIUS_SM};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # ABOUT DIALOG — QSS completo para AboutDialog
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def about_dialog_stylesheet(cls) -> str:
        """QSS completo para o AboutDialog. Nenhum hardcoded."""
        return cls.dialog_stylesheet() + (
            f"QLabel#about_title {{"
            f"  color: {current_theme.ACCENT_TEXT};"
            f"  font-size: {current_theme.FONT_SIZE_BIG};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"  letter-spacing: {current_theme.LETTER_SPACING_TITLE};"
            f"}}"
            f"QLabel#about_version {{"
            f"  color: {current_theme.TEXT_LOW};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"}}"
            f"QLabel#about_desc {{"
            f"  color: {current_theme.TEXT_MEDIUM};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"  line-height: 1.4;"
            f"}}"
            f"QLabel#about_copyright {{"
            f"  color: {current_theme.TEXT_DISABLED};"
            f"  font-size: {current_theme.FONT_SIZE_TINY};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # VERTICAL TAB — cores para VerticalTab (paintEvent custom)
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def vertical_tab_colors(cls) -> dict[str, str]:
        """Retorna cores para pintura manual do VerticalTab.
        Usa tokens semânticos — nenhum alias antigo.
        Inclui gradientes top-left → bottom-right para backgrounds."""
        return {
            "bg_selected": current_theme.ACCENT,
            "fg_selected": current_theme.SURFACE_0,
            "border_selected": current_theme.ACCENT_DIM,
            "indicator": current_theme.ACCENT_HOVER,
            "bg_hovered": current_theme.SURFACE_3,
            "fg_hovered": current_theme.TEXT_MEDIUM,
            "border_hovered": current_theme.BORDER_ACCENT,
            "bg_default": current_theme.SURFACE_0,
            "fg_default": current_theme.TEXT_LOW,
            "border_default": current_theme.BORDER_DEFAULT,
            # Gradientes (start, end) para background
            "gradient_default_start": current_theme.GRADIENT_TAB[0],
            "gradient_default_end": current_theme.GRADIENT_TAB[1],
            "gradient_hovered_start": current_theme.GRADIENT_BUTTON[0],
            "gradient_hovered_end": current_theme.GRADIENT_BUTTON[1],
            "gradient_selected_start": current_theme.ACCENT_GRADIENT[0],
            "gradient_selected_end": current_theme.ACCENT_GRADIENT[1],
        }

    # ────────────────────────────────────────────────────────────────────
    # TAB COLORS — cores centralizadas para QUALQUER tab (vertical/horizontal)
    #              Tanto VerticalTab quanto HorizontalTab usam o mesmo
    #              dicionário, garantindo consistência.
    #              Uso: P = AppStyles.tab_common_colors()
    #              painter.fillRect(..., QColor(P["bg_selected"]))
    # ────────────────────────────────────────────────────────────────────

    _TAB_COLORS_CACHE: dict = {}

    @classmethod
    def tab_common_colors(cls) -> dict[str, str]:
        """Retorna cores padronizadas para tabs (vertical e horizontal).
        Todas as tabs usam o mesmo schema de cores via tokens semânticos:
          - selected: fundo ACCENT, texto SURFACE_0, border ACCENT_DIM, indicator ACCENT_HOVER
          - hovered:  fundo ACCENT, texto SURFACE_0, border BORDER_ACCENT
          - default:  fundo SURFACE_0, texto TEXT_HIGH, border BORDER_DEFAULT
        Cacheado por performance (chave = identidade do objeto current_theme).

        ⚠ Nota de design:
        Diferente de `vertical_tab_colors()`, que usa ACCENT apenas para `selected`
        e SURFACE_3 para `hovered` (hover sutil). Este método (`tab_common_colors`)
        usa ACCENT tanto para `selected` quanto para `hovered` (hover ousado).
        A escolha entre um e outro define a agressividade visual do feedback
        de hover na tab. Para consistência, HorizontalTab e VerticalTab podem usar
        métodos diferentes — verifique qual se adequa ao design desejado."""
        cache_key = id(current_theme)
        if cls._TAB_COLORS_CACHE.get("_cache_key") != cache_key:
            cls._TAB_COLORS_CACHE = {
                "_cache_key": cache_key,
                "bg_selected": current_theme.ACCENT,
                "fg_selected": current_theme.SURFACE_0,
                "border_selected": current_theme.ACCENT_DIM,
                "indicator": current_theme.ACCENT_HOVER,
                "bg_hovered": current_theme.ACCENT,
                "fg_hovered": current_theme.SURFACE_0,
                "border_hovered": current_theme.BORDER_ACCENT,
                "bg_default": current_theme.SURFACE_0,
                "fg_default": current_theme.TEXT_HIGH,
                "border_default": current_theme.BORDER_DEFAULT,
            }
        return cls._TAB_COLORS_CACHE

    # ────────────────────────────────────────────────────────────────────
    # THEME COLORS — cores avulsas para widgets que usam paintEvent
    #                (VerticalTab, WorkspaceTabBar, etc.)
    #                Uso: from AppStyles import theme_colors
    #                colors = AppStyles.theme_colors()
    #                painter.fillRect(..., QColor(colors["BG_DEEPEST"]))
    # ────────────────────────────────────────────────────────────────────

    _THEME_COLORS_CACHE: dict = {}

    @classmethod
    def theme_colors(cls) -> dict[str, str]:
        """DEPRECIADO, NAO ULTILIZE ESSA GAMBIARRA PARA NADA
        Retorna um dicionário com TODAS as cores do tema atual.
        Cacheado por performance (paintEvent é chamado a 60 fps).
        Usa a identidade de current_theme como chave de cache."""
        cache_key = id(current_theme)
        if cls._THEME_COLORS_CACHE.get("_cache_key") != cache_key:
            cls._THEME_COLORS_CACHE = {
                "_cache_key": cache_key,
                # Aliases de compatibilidade para widgets legados
                "BG_DEEPEST": current_theme.BG_DEEPEST,
                "BG_DARK": current_theme.BG_DARK,
                "BG_PANEL": current_theme.BG_PANEL,
                "BG_CARD": current_theme.BG_CARD,
                "BG_ELEVATED": current_theme.BG_ELEVATED,
                "BG_SURFACE": current_theme.BG_SURFACE,
                "TITLE_BAR_BG": current_theme.TITLE_BAR_BG,
                "BORDER": current_theme.BORDER,
                "BORDER_HOVER": current_theme.BORDER_HOVER,
                "TEXT_BRIGHT": current_theme.TEXT_BRIGHT,
                "TEXT_PRIMARY": current_theme.TEXT_PRIMARY,
                "TEXT_SECONDARY": current_theme.TEXT_SECONDARY,
                "TEXT_MUTED": current_theme.TEXT_MUTED,
                "TEXT_ACCENT": current_theme.TEXT_ACCENT,
                "GOLD": current_theme.ACCENT_COLOR,  # ← compat: GOLD → ACCENT_COLOR
                "GOLD_HOVER": current_theme.ACCENT_COLOR_HOVER,  # ← compat
                "GOLD_DIM": current_theme.ACCENT_COLOR_DIM,  # ← compat
                "GOLD_LIGHT": current_theme.ACCENT_COLOR_LIGHT,  # ← compat
                "GOLD_GRADIENT": current_theme.ACCENT_COLOR_GRADIENT,  # ← compat
                "ACCENT_COLOR": current_theme.ACCENT_COLOR,
                "ACCENT_COLOR_HOVER": current_theme.ACCENT_COLOR_HOVER,
                "ACCENT_COLOR_DIM": current_theme.ACCENT_COLOR_DIM,
                "ACCENT_COLOR_LIGHT": current_theme.ACCENT_COLOR_LIGHT,
                "ACCENT_COLOR_GRADIENT": current_theme.ACCENT_COLOR_GRADIENT,
                # Tokens semânticos
                "ACCENT": current_theme.ACCENT,
                "ACCENT_TEXT": current_theme.ACCENT_TEXT,
                "ACCENT_BRIGHT": current_theme.ACCENT_BRIGHT,
                "SURFACE_0": current_theme.SURFACE_0,
                "SURFACE_1": current_theme.SURFACE_1,
                "SURFACE_2": current_theme.SURFACE_2,
                "SURFACE_3": current_theme.SURFACE_3,
                "SURFACE_4": current_theme.SURFACE_4,
                "SURFACE_5": current_theme.SURFACE_5,
                "COLOR_SUCCESS": current_theme.COLOR_SUCCESS,
                "COLOR_WARNING": current_theme.COLOR_WARNING,
                "COLOR_DANGER": current_theme.COLOR_DANGER,
                "COLOR_INFO": current_theme.COLOR_INFO,
            }
        return cls._THEME_COLORS_CACHE

    # ────────────────────────────────────────────────────────────────────
    # LOG HTML
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def log_html(
        cls, text: str, timestamp: str, color: str, ts_color: str, weight: str = "400"
    ) -> str:
        mono = current_theme.FONT_FAMILY_MONO
        return (
            f"<span style='color:{ts_color};"
            f"font-family:{mono};"
            f"font-size:11px;font-weight:500;'>[{timestamp}]</span> "
            f"<span style='color:{color};"
            f"font-family:{mono};"
            f"font-size:12px;font-weight:{weight};'>{text}</span>"
        )

    @classmethod
    def log_link_html(cls, text: str, url: str) -> str:
        mono = current_theme.FONT_FAMILY_MONO
        return (
            f"<span style='color:{current_theme.TEXT_LOW};"
            f"font-family:{mono};font-size:12px;'>"
            f"{text}: <a href='{url}' style='color:{current_theme.ACCENT};"
            f"text-decoration:none;'>abrir</a></span>"
        )

    @classmethod
    def log_section_html(cls, text: str) -> str:
        mono = current_theme.FONT_FAMILY_MONO
        return (
            f"<span style='color:{current_theme.ACCENT};"
            f"font-family:{mono};"
            f"font-size:12px;font-weight:700;'>{text}</span>"
        )

    # ────────────────────────────────────────────────────────────────────
    # COLLAPSIBLE — estilo para CollapsibleParams
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def collapsible_header_height(cls) -> str:
        """Altura do header do CollapsibleParams.
        INPUT_HEIGHT é numérico (usado em aritmética), por isso permanece
        int no tema — não é um valor CSS direto."""
        return str(current_theme.INPUT_HEIGHT + 2)

    @classmethod
    def collapsible_header_style(cls) -> str:
        """Estilo do header clicável do CollapsibleParams."""
        return (
            f"QLabel#collapsible_header {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  color: {current_theme.ACCENT_TEXT};"
            f"  padding: 6px 12px;"
            f"  border-radius: {current_theme.RADIUS_SM};"
            f"  font-weight: {current_theme.FONT_WEIGHT_BOLD};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"}}"
            f"QLabel#collapsible_header:hover {{"
            f"  background-color: {current_theme.SURFACE_4};"
            f"}}"
        )

    @classmethod
    def collapsible_content_style(cls) -> str:
        """Estilo do container de conteúdo do CollapsibleParams."""
        return (
            f"QWidget#collapsible_content {{"
            f"  background-color: {current_theme.SURFACE_1};"
            f"  border: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  border-top: none;"
            f"  border-radius: 0px 0px {current_theme.RADIUS_SM} {current_theme.RADIUS_SM};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # RECENT PROJECTS — estilos para RecentProjectsMenu
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def recent_project_name_style(cls, active: bool = True) -> str:
        """
        Estilo para o label do nome do projeto (RecentProjectsMenu).

        Args:
            active: Se True, nome em ACCENT_TEXT negrito. Se False,
                    nome em TEXT_MUTED itálico (projeto não encontrado).
        """
        color = current_theme.ACCENT_TEXT if active else current_theme.TEXT_MUTED
        italic = "font-style: italic;" if not active else ""
        return (
            f"QLabel {{"
            f"  color: {color};"
            f"  font-weight: bold;"
            f"  {italic}"
            f"}}"
        )

    @classmethod
    def recent_project_sub_style(cls, active: bool = True) -> str:
        """
        Estilo para os labels de path e data (RecentProjectsMenu).

        Args:
            active: Se True, cor TEXT_LOW. Se False,
                    cor TEXT_DISABLED (projeto não encontrado).
        """
        color = current_theme.TEXT_LOW if active else current_theme.TEXT_DISABLED
        return f"QLabel {{" f"  color: {color};" f"}}"

    @classmethod
    def recent_project_hover_style(cls) -> str:
        """
        Cor de fundo hover para o item do RecentProjectsMenu.
        Usa ACCENT com baixa opacidade simulada via SURFACE_3.
        """
        return current_theme.SURFACE_3

    @classmethod
    def recent_project_hover_name_style(cls) -> str:
        """
        Estilo do nome do projeto no hover (ACCENT_BRIGHT).
        """
        return f"QLabel {{" f"  color: {current_theme.ACCENT_BRIGHT};" f"  font-weight: bold;" f"}}"

    @classmethod
    def recent_project_hover_sub_style(cls) -> str:
        """
        Estilo do path/data no hover (TEXT_MEDIUM).
        """
        return f"QLabel {{" f"  color: {current_theme.TEXT_MEDIUM};" f"}}"

    # ────────────────────────────────────────────────────────────────────
    # TOOLBAR — tokens centralizados de tamanhos e estilos
    # Todos os métodos usam current_theme, zero hardcoded.
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def toolbar_icon_size(cls) -> int:
        """Tamanho do ícone na toolbar (px). Valor numérico puro — usado
        programaticamente (setIconSize etc.), não em QSS."""
        return current_theme.TOOLBAR_ICON_SIZE

    @classmethod
    def toolbar_btn_size(cls) -> int:
        """Tamanho do botão na toolbar (px). Valor numérico puro."""
        return current_theme.TOOLBAR_BTN_SIZE

    @classmethod
    def toolbar_btn_border_radius(cls) -> int:
        """Border-radius do botão da toolbar (px), como inteiro.
        BORDER_RADIUS_TOOLBAR_BTN no tema já vem formatado como string
        CSS (ex.: '4px'); aqui convertemos de volta para int porque este
        método é consumido programaticamente (ex.: QPainter, QSize)."""
        return int(str(current_theme.BORDER_RADIUS_TOOLBAR_BTN).rstrip("px"))

    @classmethod
    def toolbar_btn_hover_grow(cls) -> int:
        """Pixels extras no hover para animação grow."""
        return current_theme.TOOLBAR_BTN_HOVER_GROW

    @classmethod
    def toolbar_btn_style(cls) -> str:
        """
        QSS completo para botão da toolbar (QToolButton).
        Zero hardcoded — border-radius, cores de hover/pressed vêm do tema.
        A animação de hover grow é feita via AnimationManager, não via QSS.
        """
        return (
            f"QToolButton {{"
            f"  background-color: transparent;"
            f"  border: none;"
            f"  border-radius: {current_theme.BORDER_RADIUS_TOOLBAR_BTN};"
            f"}}"
            f"QToolButton:hover {{"
            f"  background-color: {current_theme.SURFACE_4};"
            f"}}"
            f"QToolButton:pressed {{"
            f"  background-color: {current_theme.SURFACE_2};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # TABLE — estilo genérico para QTableWidget
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def table_style(
        cls,
        *,
        bg_color: str = "",
        alt_bg_color: str = "",
        border_radius: int = 0,
        grid_color: str = "",
        header_bg: str = "",
        header_fg: str = "",
        header_border_bottom: str = "",
        item_selected_bg: str = "",
        item_selected_fg: str = "",
        font_size: int = 0,
        header_font_size: int = 0,
        header_letter_spacing: str = "",
    ) -> str:
        """
        Gera QSS completo para QTableWidget usando tokens do tema.
        Qualquer parametro vazio usa o valor do tema ativo (que já vem
        com a unidade embutida, ex.: '8px'). Quando o parametro numerico
        (border_radius, font_size, header_font_size) é informado, ele é
        um inteiro puro e o 'px' é aplicado apenas na hora do uso, aqui.

        Args:
            bg_color: Fundo da tabela (padrao: SURFACE_4).
            alt_bg_color: Fundo alternado (padrao: SURFACE_3).
            border_radius: Border-radius em px, inteiro (padrao: tema).
            grid_color: Cor da grade (padrao: DIVIDER).
            header_bg: Fundo do cabecalho (padrao: SURFACE_3).
            header_fg: Texto do cabecalho (padrao: TEXT_LOW).
            header_border_bottom: Borda inferior do cabecalho (padrao: ACCENT).
            item_selected_bg: Fundo do item selecionado (padrao: SURFACE_5).
            item_selected_fg: Texto do item selecionado (padrao: TEXT_HIGH).
            font_size: Tamanho da fonte da celula em px, inteiro (0 = tema).
            header_font_size: Tamanho da fonte do cabecalho em px, inteiro (0 = tema).
            header_letter_spacing: Letter-spacing do cabecalho (vazio = tema).

        Returns:
            String QSS completa para QTableWidget + QHeaderView.
        """
        bg = bg_color or current_theme.SURFACE_4
        alt_bg = alt_bg_color or current_theme.SURFACE_3
        br = f"{border_radius}px" if border_radius else current_theme.BORDER_RADIUS_TABLE
        grid = grid_color or current_theme.DIVIDER
        h_bg = header_bg or current_theme.SURFACE_3
        h_fg = header_fg or current_theme.TEXT_LOW
        h_border = header_border_bottom or current_theme.ACCENT
        sel_bg = item_selected_bg or current_theme.SURFACE_5
        sel_fg = item_selected_fg or current_theme.TEXT_HIGH
        fs = f"{font_size}px" if font_size else current_theme.FONT_SIZE_SMALL
        hfs = f"{header_font_size}px" if header_font_size else current_theme.HEADER_FONT_SIZE
        hls = header_letter_spacing or current_theme.HEADER_LETTER_SPACING
        return (
            f"QTableWidget {{"
            f"  background-color: {bg};"
            f"  alternate-background-color: {alt_bg};"
            f"  border: none;"
            f"  border-radius: {br};"
            f"  gridline-color: {grid};"
            f"  color: {current_theme.TEXT_MEDIUM};"
            f"  font-size: {fs};"
            f"}}"
            f"QTableWidget::item:selected {{"
            f"  background-color: {sel_bg};"
            f"  color: {sel_fg};"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: {h_bg};"
            f"  color: {h_fg};"
            f"  padding: 4px 6px;"
            f"  border: none;"
            f"  border-bottom: 2px solid {h_border};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"  font-size: {hfs};"
            f"  letter-spacing: {hls};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # LOG VIEWER TABLE — estilo dedicado para LogViewerPlugin
    # Toda cor vem do tema via tokens semanticos. Zero acoplamento.
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def log_viewer_table_style(cls) -> str:
        """
        QSS completo para a tabela do LogViewerPlugin.
        Nao recebe parametros — todas as cores sao resolvidas internamente
        via current_theme.
        """
        return (
            f"QTableWidget {{"
            f"  background-color: {current_theme.SURFACE_1};"
            f"  alternate-background-color: {current_theme.SURFACE_2};"
            f"  border: none;"
            f"  border-radius: {current_theme.BORDER_RADIUS_TABLE};"
            f"  gridline-color: {current_theme.BORDER_DEFAULT};"
            f"  color: {current_theme.TEXT_MEDIUM};"
            f"}}"
            f"QTableWidget::item:selected {{"
            f"  background-color: {current_theme.SURFACE_5};"
            f"  color: {current_theme.TEXT_HIGH};"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  color: {current_theme.TEXT_LOW};"
            f"  padding: 4px 6px;"
            f"  border: none;"
            f"  border-bottom: 2px solid {current_theme.ACCENT};"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"  font-size: {current_theme.HEADER_FONT_SIZE};"
            f"  letter-spacing: {current_theme.HEADER_LETTER_SPACING};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # TOAST NOTIFICATION — estilo para ToastNotification
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def toast_style(cls, is_error: bool = False) -> str:
        """
        QSS para o label interno do ToastNotification.
        Usa gradiente do tema (ACCENT_GRADIENT para sucesso, COLOR_DANGER para erro)
        com borda sutil, padding generoso e fonte em negrito.

        Args:
            is_error: True para estilo vermelho (erro), False para padrão (tema).

        Retorna:
            String QSS completa para o QLabel do toast.
        """
        if is_error:
            bg_gradient = cls._gradient_qss_from_stops(
                (),
                45,
                current_theme.COLOR_DANGER_DIM,
                current_theme.COLOR_DANGER,
                gradient_type=current_theme.GRADIENT_ACCENT_TYPE,
                cx=current_theme.GRADIENT_RADIAL_CX,
                cy=current_theme.GRADIENT_RADIAL_CY,
                fx=current_theme.GRADIENT_RADIAL_FX,
                fy=current_theme.GRADIENT_RADIAL_FY,
                radius=current_theme.GRADIENT_RADIAL_RADIUS,
            )
            border_color = current_theme.COLOR_DANGER
            text_color = current_theme.TEXT_ON_DANGER
        else:
            bg_gradient = cls._gradient_qss_from_stops(
                current_theme.GRADIENT_ACCENT_STOPS,
                current_theme.GRADIENT_ACCENT_ANGLE,
                current_theme.ACCENT_GRADIENT[0],
                current_theme.ACCENT_GRADIENT[1],
                gradient_type=current_theme.GRADIENT_ACCENT_TYPE,
                cx=current_theme.GRADIENT_RADIAL_CX,
                cy=current_theme.GRADIENT_RADIAL_CY,
                fx=current_theme.GRADIENT_RADIAL_FX,
                fy=current_theme.GRADIENT_RADIAL_FY,
                radius=current_theme.GRADIENT_RADIAL_RADIUS,
            )
            border_color = current_theme.ACCENT
            text_color = current_theme.SURFACE_0

        return (
            f"QLabel {{"
            f"  background: {bg_gradient};"
            f"  color: {text_color};"
            f"  border: 1px solid {border_color};"
            f"  border-radius: {current_theme.BORDER_RADIUS_CARD};"
            f"  padding: 14px 28px;"
            f"  font-size: {current_theme.FONT_SIZE_NORMAL};"
            f"  font-weight: {current_theme.FONT_WEIGHT_BOLD};"
            f"  letter-spacing: {current_theme.BUTTON_LETTER_SPACING_NORMAL};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # GRID PERCENT VIEW — cores para GridPercentView (system monitor)
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def grid_percent_colors(cls) -> dict[str, str]:
        """Retorna cores para o GridPercentView (paintEvent).
        Usa tokens semânticos — zero hardcoded."""
        return {
            "label_fg": current_theme.TEXT_MEDIUM,
            "value_fg": current_theme.ACCENT,
            "value_fg_hover": current_theme.ACCENT_HOVER,
            "bar_bg": current_theme.SURFACE_3,
            "bar_fill": current_theme.ACCENT,
            "bar_border": current_theme.BORDER_SUBTLE,
            "hover_bg": current_theme.ACCENT + "15",
        }

    @classmethod
    def menu_bar_container_style(cls) -> str:
        """Estilo do QWidget container da MenuBar (fundo igual ao TITLE_BAR)."""
        return (
            f"QWidget#app_menu_bar_container {{"
            f"  background-color: {current_theme.TITLE_BAR};"
            f"  border-bottom: 1px solid {current_theme.BORDER_DEFAULT};"
            f"}}"
        )

    @classmethod
    def explorer_link_style(cls) -> str:
        """
        Estilo CSS para links clicáveis que abrem no Windows Explorer.
        Usa ACCENT como cor.
        Retorna apenas o trecho style='...' para uso inline em tags <a>.
        """
        return (
            f"color: {current_theme.ACCENT}; "
            f"text-decoration: underline; "
            f"cursor: pointer;"
        )

    @classmethod
    def tree_style(cls) -> str:
        """
        Estilo completo para QTreeWidget (usado em CrsSearchDialog, etc.).
        Inclui header, itens, hover, selected e branch indicators.
        """
        return (
            f"QTreeWidget {{"
            f"  background-color: {current_theme.SURFACE_1};"
            f"  color: {current_theme.TEXT_MEDIUM};"
            f"  border: 1px solid {current_theme.BORDER_DEFAULT};"
            f"  border-radius: {current_theme.RADIUS_SM};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"}}"
            f"QTreeWidget::item:hover {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"}}"
            f"QTreeWidget::item:selected {{"
            f"  background-color: {current_theme.ACCENT};"
            f"  color: {current_theme.SURFACE_0};"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: {current_theme.SURFACE_3};"
            f"  color: {current_theme.TEXT_LOW};"
            f"  border: none;"
            f"  border-bottom: 2px solid {current_theme.ACCENT};"
            f"  padding: 4px 6px;"
            f"  font-weight: {current_theme.FONT_WEIGHT_EXTRABOLD};"
            f"  font-size: {current_theme.FONT_SIZE_SMALL};"
            f"}}"
            f"QTreeWidget::branch:has-children:!has-siblings:closed,"
            f"QTreeWidget::branch:closed:has-children:has-siblings {{"
            f"  border-image: none;"
            f"}}"
        )

    @classmethod
    def grid_percent_font_label(cls) -> str:
        """Família e tamanho da fonte do label no GridPercentView."""
        return f"{current_theme.FONT_FAMILY_MONO}, 10px"

    @classmethod
    def grid_percent_font_value(cls) -> str:
        """Família e tamanho da fonte do valor no GridPercentView."""
        return f"{current_theme.FONT_FAMILY_MONO}, 10px bold"