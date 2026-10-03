# -*- coding: utf-8 -*-
"""
SimpleThemeButton — Botão 100% autossuficiente com estilo vindo do tema.
=======================================================================
Diferente dos outros botões (SimplePrimaryButton, SimpleSecondaryButton),
este widget NÃO depende do AppStyles para gerar QSS. Ele importa
diretamente o singleton `theme_manager` e constrói todo o stylesheet
internamente usando os tokens do tema ativo, via `current_theme`.

Isolamento total:
  - Nenhum método do AppStyles é chamado para estilização.
  - A única importação externa de estilo é `BaseStyle.apply_drop_shadow`
    para o efeito glow (utilitário de sombra, não de estilo visual).
  - O border-radius vem exclusivamente de `current_theme.BORDER_RADIUS_BUTTON`
    (que já traz a unidade "px" embutida), a menos que `border_radius`
    seja explicitamente informado no construtor (nesse caso é um inteiro
    puro, e a unidade é aplicada aqui na hora do uso).
  - Comportamentos booleanos (glow, etc.) são controlados por tokens
    do tema (GLOW_BUTTON_ENABLED, etc.).

Uso:
    btn = SimpleThemeButton("EXECUTAR")
    btn = SimpleThemeButton("SALVAR", min_width=140, shadow_enabled=True)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import theme_manager

current_theme = theme_manager.theme


class SimpleThemeButton(QPushButton):
    """
    Botão temático autossuficiente.

    Todo o QSS é gerado internamente a partir dos tokens do tema ativo
    (via `current_theme`). Nenhuma dependência do AppStyles para
    estilização.

    Args:
        text: Texto exibido no botão.
        parent: Widget pai.
        min_width: Largura mínima em pixels. 0 = sem mínimo.
        min_height: Altura mínima em pixels. 0 = sem mínimo.
        shadow_enabled: Se True, aplica glow via QGraphicsDropShadowEffect
                        usando os tokens GLOW_* do tema.
        border_radius: Border-radius em px, inteiro. None = usa o valor
                        do tema (current_theme.BORDER_RADIUS_BUTTON).
    """

    def __init__(
        self,
        text: str = "BOTÃO",
        parent=None,
        *,
        min_width: int = 180,
        min_height: int = 34,
        shadow_enabled: bool = True,
        border_radius: int | None = None,
    ):
        super().__init__(text, parent)

        self._shadow_enabled = shadow_enabled
        self._border_radius = border_radius

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if min_width > 0:
            self.setMinimumWidth(min_width)
        if min_height > 0:
            self.setMinimumHeight(min_height)

        self._refresh_style()
        self._apply_glow()

    # ──────────────────────────────────────────────────────────────────
    # API PÚBLICA
    # ──────────────────────────────────────────────────────────────────

    def update_theme(self) -> None:
        """
        Reaplica o estilo e o glow (útil após troca de tema em runtime).
        Chame este método se o tema for alterado em tempo de execução.
        """
        self._refresh_style()
        self._apply_glow()

    def set_shadow_enabled(self, enabled: bool) -> None:
        """Ativa ou desativa o efeito de glow."""
        self._shadow_enabled = enabled
        self._apply_glow()

    # ──────────────────────────────────────────────────────────────────
    # INTERNOS — Geração de QSS 100% via tokens do tema
    # ──────────────────────────────────────────────────────────────────

    def _build_stylesheet(self) -> str:
        """
        Constrói o QSS completo usando APENAS tokens do tema ativo.
        Sem chamadas ao AppStyles. Sem valores hardcoded.

        Os tokens de tema (BORDER_RADIUS_BUTTON, BUTTON_PADDING_*_PRIMARY,
        BUTTON_FONT_SIZE_PRIMARY, BUTTON_LETTER_SPACING_PRIMARY) já vêm
        com a unidade "px" embutida — por isso NUNCA são concatenados
        com "px" aqui. Apenas o override `border_radius` (inteiro puro,
        vindo do construtor) recebe "px" na hora do uso.
        """
        # Gradiente de fundo (fallback para ACCENT_GRADIENT se não houver stops)
        stops = current_theme.GRADIENT_ACCENT_STOPS
        if stops:
            bg_gradient = BaseStyle._gradient_qss_from_stops(
                stops,
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
        else:
            bg_gradient = (
                f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                f"stop:0 {current_theme.ACCENT_GRADIENT[0]}, "
                f"stop:1 {current_theme.ACCENT_GRADIENT[1]})"
            )

        # Gradiente hover (simplificado: ACCENT_HOVER -> ACCENT)
        hover_gradient = (
            f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {current_theme.ACCENT_HOVER}, "
            f"stop:1 {current_theme.ACCENT})"
        )

        # border_radius: se informado no construtor, é int puro → aplica "px".
        # Caso contrário, usa o token do tema, que já vem com "px" embutido.
        border_radius = (
            f"{self._border_radius}px"
            if self._border_radius is not None
            else current_theme.BORDER_RADIUS_BUTTON
        )
        padding_v = current_theme.BUTTON_PADDING_V_PRIMARY
        padding_h = current_theme.BUTTON_PADDING_H_PRIMARY
        font_weight = current_theme.BUTTON_FONT_WEIGHT_PRIMARY or current_theme.FONT_WEIGHT_HEAVY
        font_size = current_theme.BUTTON_FONT_SIZE_PRIMARY or current_theme.FONT_SIZE_NORMAL
        letter_spacing = current_theme.BUTTON_LETTER_SPACING_PRIMARY

        return (
            f"QPushButton {{"
            f"  background: {bg_gradient};"
            f"  color: {current_theme.TEXT_ON_ACCENT};"
            f"  border: none;"
            f"  border-radius: {border_radius};"
            f"  padding: {padding_v} {padding_h};"
            f"  font-weight: {font_weight};"
            f"  font-size: {font_size};"
            f"  min-height: 60px;"
            f"  letter-spacing: {letter_spacing};"
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
            f"  border: none;"
            f"  border-radius: {border_radius};"
            f"}}"
        )

    def _refresh_style(self) -> None:
        """Aplica o stylesheet gerado internamente."""
        self.setStyleSheet(self._build_stylesheet())

    def _apply_glow(self) -> None:
        """
        Aplica glow via QGraphicsDropShadowEffect usando tokens do tema.
        Controlado por GLOW_BUTTON_ENABLED e GLOW_BLUR/GLOW_ALPHA.
        Estes tokens são consumidos programaticamente (não em QSS),
        por isso permanecem inteiros puros no tema.
        """
        if not self._shadow_enabled:
            self.setGraphicsEffect(None)
            return

        if not current_theme.GLOW_BUTTON_ENABLED:
            self.setGraphicsEffect(None)
            return

        blur = current_theme.GLOW_BLUR
        alpha = current_theme.GLOW_ALPHA

        if blur <= 0 or alpha <= 0:
            self.setGraphicsEffect(None)
            return

        glow_color = current_theme.GLOW_COLOR_RGB or current_theme.ACCENT

        BaseStyle.apply_drop_shadow(
            self,
            blur=blur,
            offset_x=current_theme.GLOW_OFFSET_X,
            offset_y=current_theme.GLOW_OFFSET_Y,
            color_rgb=glow_color,
            alpha=alpha,
        )