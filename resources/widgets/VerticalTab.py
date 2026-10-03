# -*- coding: utf-8 -*-
"""
VerticalTab — Aba vertical estilo Civil 3D
==========================================
Texto renderizado rotacionado 90° via paintEvent.
Sem QLabel — controle total sobre aparência.

Cores vindas de Palette (styles.py) para consistência com o tema.
Padding reduzido em relação ao WorkspaceTab por ser vertical.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, Signal, QRect, QSize
from PySide6.QtGui     import QPainter, QPen, QColor, QFont, QFontMetrics, QPainterPath, QBrush
from PySide6.QtWidgets import QWidget, QSizePolicy

from resources.styles.AppStyles import AppStyles
from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import theme_manager


class VerticalTab(QWidget):
    """
    Aba vertical clicável com texto rotacionado 90° (bottom → top),
    estilo painel lateral do Civil 3D / AutoCAD.

    Emite `clicked` ao ser pressionada.
    """

    clicked = Signal()
    double_clicked = Signal()

    _WIDTH  = 24               # espessura da aba
    _HEIGHT = 80               # altura (vira largura do texto após rotação -90°)

    def __init__(
        self,
        title:   str,
        tooltip: str = "",
        icon=None,
        parent=None,
    ):
        super().__init__(parent)
        self._title    = title
        self._selected = False
        self._hovered  = False
        self._icon     = icon

        self.setObjectName("vertical_tab")
        if tooltip:
            self.setToolTip(tooltip)

        # Bloqueio absoluto de tamanho
        self.setFixedWidth(self._WIDTH)
        self.setFixedHeight(self._HEIGHT)
        self.setMinimumWidth(self._WIDTH)
        self.setMaximumWidth(self._WIDTH)
        self.setMinimumHeight(self._HEIGHT)
        self.setMaximumHeight(self._HEIGHT)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

    # ── Pintura ──────────────────────────────────────────────────────

    def _draw_rounded_rect(self, painter, rect, tl=2, tr=2, br=2, bl=8):
        """
        Desenha retângulo com corner-radius customizado para cada canto.
        tl=top-left, tr=top-right, br=bottom-right, bl=bottom-left
        """
        path = QPainterPath()
        path.moveTo(rect.left() + tl, rect.top())
        path.lineTo(rect.right() - tr, rect.top())
        path.arcTo(rect.right() - 2*tr, rect.top(), 2*tr, 2*tr, 90, -90)
        path.lineTo(rect.right(), rect.bottom() - br)
        path.arcTo(rect.right() - 2*br, rect.bottom() - 2*br, 2*br, 2*br, 0, -90)
        path.lineTo(rect.left() + bl, rect.bottom())
        path.arcTo(rect.left(), rect.bottom() - 2*bl, 2*bl, 2*bl, 270, -90)
        path.lineTo(rect.left(), rect.top() + tl)
        path.arcTo(rect.left(), rect.top(), 2*tl, 2*tl, 180, -90)
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        P    = AppStyles.tab_common_colors()
        t    = theme_manager.theme

        if self._selected:
            bg     = QColor(P["bg_selected"])
            fg     = QColor(P["fg_selected"])
            border = QColor(P["border_selected"])
        elif self._hovered:
            bg     = QColor(P["bg_hovered"])
            fg     = QColor(P["fg_hovered"])
            border = QColor(P["border_hovered"])
        else:
            bg     = QColor(P["bg_default"])
            fg     = QColor(P["fg_default"])
            border = QColor(P["border_default"])

        rect = QRect(0, 0, w, h)
        path = self._draw_rounded_rect(painter, rect, tl=2, tr=2, br=8, bl=2)

        painter.setClipPath(path)

        # ── Preencher background com gradiente ────────────────────────
        if self._selected:
            # Selected: usa GRADIENT_ACCENT_STOPS (gradiente de acento)
            accent_stops = t.GRADIENT_ACCENT_STOPS
            if accent_stops:
                grad = BaseStyle._build_linear_gradient(
                    accent_stops, t.GRADIENT_ACCENT_ANGLE, w, h,
                )
                painter.fillPath(path, QBrush(grad))
            else:
                # Fallback: cor sólida ACCENT (comportamento original)
                painter.fillPath(path, bg)
        else:
            # Default/hovered: usa gradiente via GRADIENT_TAB_STOPS
            tab_stops = t.GRADIENT_TAB_STOPS
            if tab_stops:
                grad = BaseStyle._build_linear_gradient(
                    tab_stops, t.GRADIENT_TAB_ANGLE, w, h,
                )
                painter.fillPath(path, QBrush(grad))
            else:
                # Fallback: gradiente 2-stop clássico
                grad_stops = (
                    (0.0, t.GRADIENT_TAB[0]),
                    (1.0, t.GRADIENT_TAB[1]),
                )
                grad = BaseStyle._build_linear_gradient(grad_stops, 45, w, h)
                painter.fillPath(path, QBrush(grad))

        # Indicador de seleção (barra na esquerda)
        if self._selected:
            painter.fillRect(0, 0, 3, h, QColor(P["indicator"]))

        # Desenhar borda
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)

        painter.setClipping(False)

        # ── Glow na aba selecionada (opcional) ──────────────────────
        if self._selected and t.GLOW_TAB_ENABLED and t.GLOW_BLUR > 0:
            glow_color = QColor(t.GLOW_COLOR_RGB or t.ACCENT)
            glow_color.setAlpha(t.GLOW_ALPHA)
            painter.setPen(QPen(glow_color, 2))
            painter.drawPath(path)

        # Desenhar texto
        font = QFont("Segoe UI", 8)
        font.setWeight(QFont.Weight.Medium if self._selected else QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QPen(fg))

        painter.save()
        painter.translate(w / 2, h / 2)
        painter.rotate(-90)

        fm   = QFontMetrics(font)
        text = fm.elidedText(self._title, Qt.TextElideMode.ElideRight, h - 8)
        tw   = fm.horizontalAdvance(text)
        th   = fm.height()

        painter.drawText(
            QRect(-tw // 2, -th // 2, tw, th),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
        painter.restore()

        painter.end()

    # ── Eventos de mouse ────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Duplo clique emite double_clicked."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)#

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):#
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # ── Propriedades ────────────────────────────────────────────────

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self.update()

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        if self._selected != value:
            self._selected = value
            self.update()

    # ── Tamanho ideal ────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(self._WIDTH, self._HEIGHT)