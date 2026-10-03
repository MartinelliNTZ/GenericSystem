# -*- coding: utf-8 -*-
"""
SimplePrimaryButton — Botão primário flexível com suporte a temas.
===============================================================
Aceita parâmetros de estilo suficientes para que o tema controle
totalmente a aparência. O botão mantém apenas o mínimo de estilização
interna (cursor, tamanhos mínimos) e delega a geração QSS para os
métodos do AppStyles — que por sua vez usam tokens do tema ativo.

style_key mapeia para métodos do AppStyles:
    "primary"   → btn_primary_style()   (gradiente ouro, padrão)
    "secondary" → btn_secondary_style() (gradiente escuro)
    "danger"    → btn_danger_style()    (vermelho)
    "ghost"     → btn_ghost_style()     (transparente)
    "remove"    → btn_remove_style()    (preto com hover vermelho)

O glow dourado é aplicado via QGraphicsDropShadowEffect usando os tokens
GLOW_* do tema (GLOW_BLUR, GLOW_COLOR_RGB, GLOW_ALPHA).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from resources.styles.AppStyles import AppStyles
from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import theme_manager

# Mapa de style_key → método do AppStyles
_STYLE_MAP = {
    "primary":   AppStyles.btn_primary_style,
    "secondary": AppStyles.btn_secondary_style,
    "danger":    AppStyles.btn_danger_style,
    "ghost":     AppStyles.btn_ghost_style,
    "remove":    AppStyles.btn_remove_style,
}


class SimplePrimaryButton(QPushButton):
    """
    Botão primário com suporte a múltiplos estilos via style_key.

    Args:
        text: Texto exibido no botão.
        parent: Widget pai.
        style_key: Chave do estilo. Opções: "primary", "secondary",
                   "danger", "ghost", "remove". Padrão: "primary".
        min_width: Largura mínima em pixels. 0 = sem mínimo.
        min_height: Altura mínima em pixels. 0 = sem mínimo.
        custom_stylesheet: QSS customizado. Se informado, substitui
                           completamente o estilo gerado pelo style_key.
        shadow_enabled: Se True, aplica QGraphicsDropShadowEffect com
                        os parâmetros do tema (GLOW_*).
        shadow_blur: Blur override (px). -1 = usa o valor do tema.
        shadow_offset_x: Offset X override (px). -1 = usa o valor do tema.
        shadow_offset_y: Offset Y override (px). -1 = usa o valor do tema.
        shadow_color_rgb: Cor override (#RRGGBB). "" = usa o valor do tema.
        shadow_alpha: Alpha override (0-255). -1 = usa o valor do tema.
    """

    def __init__(
        self,
        text: str = "EXECUTAR",
        parent=None,
        *,
        style_key: str = "primary",
        min_width: int = 180,
        min_height: int = 34,
        custom_stylesheet: Optional[str] = None,
        shadow_enabled: bool = True,
        shadow_blur: int = -1,
        shadow_offset_x: int = -1,
        shadow_offset_y: int = -1,
        shadow_color_rgb: str = "",
        shadow_alpha: int = -1,
    ):
        super().__init__(text, parent)

        self._style_key = style_key
        self._custom_stylesheet = custom_stylesheet
        self._shadow_enabled = shadow_enabled
        self._shadow_blur = shadow_blur
        self._shadow_offset_x = shadow_offset_x
        self._shadow_offset_y = shadow_offset_y
        self._shadow_color_rgb = shadow_color_rgb
        self._shadow_alpha = shadow_alpha

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

    @property
    def style_key(self) -> str:
        """Chave do estilo ativo."""
        return self._style_key

    def set_style_key(self, key: str) -> None:
        """Troca o estilo em runtime."""
        self._style_key = key
        self._refresh_style()

    def set_custom_stylesheet(self, qss: Optional[str]) -> None:
        """Define QSS customizado (substitui o style_key)."""
        self._custom_stylesheet = qss
        self._refresh_style()

    def update_glow(self) -> None:
        """
        Recria o efeito de glow (útil após troca de tema).
        Chame este método se o tema for alterado em tempo de execução.
        """
        self._apply_glow()

    def set_shadow_params(
        self,
        blur: int = -1,
        offset_x: int = -1,
        offset_y: int = -1,
        color_rgb: str = "",
        alpha: int = -1,
    ) -> None:
        """Atualiza parâmetros de sombra em runtime."""
        if blur >= 0:
            self._shadow_blur = blur
        if offset_x >= 0:
            self._shadow_offset_x = offset_x
        if offset_y >= 0:
            self._shadow_offset_y = offset_y
        if color_rgb:
            self._shadow_color_rgb = color_rgb
        if alpha >= 0:
            self._shadow_alpha = alpha
        self._apply_glow()

    # ──────────────────────────────────────────────────────────────────
    # INTERNOS
    # ──────────────────────────────────────────────────────────────────

    def _refresh_style(self) -> None:
        """Aplica o stylesheet com base no custom_stylesheet ou style_key."""
        if self._custom_stylesheet is not None:
            self.setStyleSheet(self._custom_stylesheet)
            return

        factory = _STYLE_MAP.get(self._style_key)
        if factory is None:
            factory = _STYLE_MAP["primary"]
        self.setStyleSheet(factory())

    def _apply_glow(self) -> None:
        """
        Aplica glow via QGraphicsDropShadowEffect.
        Usa valores override se fornecidos, senão lê do tema.
        Se shadow_enabled=False ou blur<=0 ou alpha<=0, não aplica.
        """
        if not self._shadow_enabled:
            return

        t = theme_manager.theme
        blur = self._shadow_blur if self._shadow_blur >= 0 else t.GLOW_BLUR
        ox = self._shadow_offset_x if self._shadow_offset_x >= 0 else t.GLOW_OFFSET_X
        oy = self._shadow_offset_y if self._shadow_offset_y >= 0 else t.GLOW_OFFSET_Y
        rgb = self._shadow_color_rgb if self._shadow_color_rgb else (t.GLOW_COLOR_RGB or t.ACCENT)
        alpha = self._shadow_alpha if self._shadow_alpha >= 0 else t.GLOW_ALPHA

        if blur <= 0 or alpha <= 0:
            self.setGraphicsEffect(None)
            return

        BaseStyle.apply_drop_shadow(
            self,
            blur=blur,
            offset_x=ox,
            offset_y=oy,
            color_rgb=rgb,
            alpha=alpha,
        )