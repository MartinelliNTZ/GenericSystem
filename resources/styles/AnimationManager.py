# -*- coding: utf-8 -*-
"""
AnimationManager — Gerenciador central de animações Qt
========================================================
Cria e gerencia animações via QPropertyAnimation com suporte
a hover grow, bounce e qualquer propriedade numérica.

Uso:
    from resources.styles.AnimationManager import AnimationManager

    # Hover grow com aumento do icone
    AnimationManager.animate_hover_grow(meu_botao, grow_px=4, grow_icon_px=24)

    # Animação custom
    anim = AnimationManager.animate_property(
        widget, b"minimumSize", QSize(32, 32), QSize(36, 36), duration=150
    )
"""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import QWidget

from resources.styles.ThemeManager import theme_manager


class AnimationManager:
    """
    Gerador de animações reutilizáveis.

    Todos os métodos são estáticos — não é necessário instanciar.
    """

    # ── Animações Genéricas ───────────────────────────────────────

    @staticmethod
    def animate_property(
        widget: QWidget,
        property_name: bytes,
        start_value,
        end_value,
        duration: int | None = None,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> QPropertyAnimation:
        """
        Cria e inicia uma QPropertyAnimation no widget.

        Args:
            widget: Widget alvo.
            property_name: Propriedade Qt a animar (ex: b"minimumSize").
            start_value: Valor inicial.
            end_value: Valor final.
            duration: Duração em ms. Se None, usa ANIMATION_NORMAL do tema.
            easing: Curva de easing.

        Returns:
            A instância da QPropertyAnimation já iniciada.
        """
        duration = duration or theme_manager.theme.ANIMATION_NORMAL
        anim = QPropertyAnimation(widget, property_name)
        anim.setDuration(duration)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.setEasingCurve(easing)
        anim.start()
        return anim

    # ── Hover Grow ────────────────────────────────────────────────

    @classmethod
    def animate_hover_grow(
        cls,
        widget: QWidget,
        grow_px: int | None = None,
        grow_icon_px: int | None = None,
        duration: int | None = None,
    ) -> None:
        """
        Configura animação de aumentar o widget + icone ao passar o mouse.

        Instala os eventos enter/leave no widget para animar
        minimumSize, maximumSize e iconSize simultaneamente.

        Args:
            widget: Widget alvo.
            grow_px: Quantos pixels aumentar o widget. Se None, usa
                     TOOLBAR_BTN_HOVER_GROW do tema.
            grow_icon_px: Tamanho do icone no hover. Se None, calcula
                          como base_icon + grow_px.
            duration: Duração em ms. Se None, usa ANIMATION_FAST do tema.
        """
        grow_px = grow_px if grow_px is not None else theme_manager.theme.TOOLBAR_BTN_HOVER_GROW
        duration = duration if duration is not None else theme_manager.theme.ANIMATION_FAST
        from PySide6.QtCore import QEvent

        original = widget.property("_hover_base_size")
        if original is None:
            original = widget.size()
            widget.setProperty("_hover_base_size", original)

        original_icon = widget.property("_hover_base_icon")
        if original_icon is None:
            original_icon = widget.iconSize()
            widget.setProperty("_hover_base_icon", original_icon)

        # Se grow_icon_px nao foi passado, calcula como original + grow_px
        icon_hover = grow_icon_px if grow_icon_px else original_icon.width() + grow_px

        # Salva os event handlers originais ANTES de sobrescrever
        original_enter = widget.enterEvent
        original_leave = widget.leaveEvent

        def _enter(event):
            w = original.width() + grow_px
            h = original.height() + grow_px
            cls.animate_property(
                widget, b"minimumSize", widget.minimumSize(), QSize(w, h),
                duration=duration,
            )
            cls.animate_property(
                widget, b"maximumSize", widget.maximumSize(), QSize(w, h),
                duration=duration,
            )
            cls.animate_property(
                widget, b"iconSize", widget.iconSize(), QSize(icon_hover, icon_hover),
                duration=duration,
            )
            # Propaga o evento para o handler original (tooltip, etc.)
            if original_enter:
                original_enter(event)

        def _leave(event):
            w = original.width()
            h = original.height()
            cls.animate_property(
                widget, b"minimumSize", widget.minimumSize(), QSize(w, h),
                duration=duration,
            )
            cls.animate_property(
                widget, b"maximumSize", widget.maximumSize(), QSize(w, h),
                duration=duration,
            )
            cls.animate_property(
                widget, b"iconSize", widget.iconSize(), QSize(original_icon.width(), original_icon.height()),
                duration=duration,
            )
            # Propaga o evento para o handler original
            if original_leave:
                original_leave(event)

        widget.enterEvent = _enter
        widget.leaveEvent = _leave

    # ── Bounce ────────────────────────────────────────────────────

    @classmethod
    def animate_bounce(
        cls,
        widget: QWidget,
        property_name: bytes,
        start_value,
        peak_value,
        end_value,
        duration: int | None = None,
    ) -> list[QPropertyAnimation]:
        """
        Cria uma animação bounce (vai ao pico e retorna).
        """
        duration = duration or theme_manager.theme.ANIMATION_SLOW
        half = duration // 2

        fwd = QPropertyAnimation(widget, property_name)
        fwd.setDuration(half)
        fwd.setStartValue(start_value)
        fwd.setEndValue(peak_value)
        fwd.setEasingCurve(QEasingCurve.Type.OutQuad)
        fwd.finished.connect(lambda: cls._bounce_back(widget, property_name, peak_value, end_value, half))
        fwd.start()
        return [fwd]

    @classmethod
    def _bounce_back(cls, widget, prop, peak, end, duration):
        anim = QPropertyAnimation(widget, prop)
        anim.setDuration(duration)
        anim.setStartValue(peak)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.InQuad)
        anim.start()

    # ── Limpeza ───────────────────────────────────────────────────

    @classmethod
    def clear_hover_grow(cls, widget: QWidget) -> None:
        """Remove a animação hover grow do widget."""
        if hasattr(widget, "_hover_grow_enter"):
            del widget._hover_grow_enter
        if hasattr(widget, "_hover_grow_leave"):
            del widget._hover_grow_leave
        base = widget.property("_hover_base_size")
        if base:
            widget.setFixedSize(base)