# -*- coding: utf-8 -*-
"""
SimpleSecondaryButton — Botão secundário com gradiente e glow opcional.
Uso: Salvar Config, Carregar Config, Restaurar Padrão, etc.
Aplica glow via QGraphicsDropShadowEffect quando o tema define
GLOW_BUTTON_ENABLED=True e GLOW_BLUR > 0.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from resources.styles.AppStyles import AppStyles
from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import theme_manager


class SimpleSecondaryButton(QPushButton):
    """
    Botão secundário com fundo escuro e texto dourado.
    Glow opcional controlado pelo token GLOW_BUTTON_ENABLED do tema.
    """

    def __init__(self, text: str = "Ação", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_secondary_style())
        self.setMinimumHeight(32)
        self._apply_glow()

    # ──────────────────────────────────────────────────────────────────
    # GLOW (efeito de brilho) via QGraphicsDropShadowEffect
    # ──────────────────────────────────────────────────────────────────

    def _apply_glow(self) -> None:
        """Aplica glow se GLOW_BUTTON_ENABLED=True e GLOW_BLUR > 0."""
        t = theme_manager.theme
        if not t.GLOW_BUTTON_ENABLED:
            return
        glow_color = t.GLOW_COLOR_RGB or t.ACCENT
        BaseStyle.apply_drop_shadow(
            self,
            blur=t.GLOW_BLUR,
            offset_x=t.GLOW_OFFSET_X,
            offset_y=t.GLOW_OFFSET_Y,
            color_rgb=glow_color,
            alpha=t.GLOW_ALPHA,
        )

    def update_glow(self) -> None:
        """Recria o efeito de glow (útil após troca de tema)."""
        self._apply_glow()
