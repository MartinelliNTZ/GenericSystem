# -*- coding: utf-8 -*-
"""
HorizontalTab — Aba horizontal estilo Workspace
================================================
QTabBar customizado com paintEvent próprio para estilo consistente.
Substitui o antigo _WorkspaceTabBar de CentralWorkspace.

Toda cor e gradiente vem do tema ativo via AppStyles.current_theme.
Usa AppStyles.tab_common_colors() para cores padronizadas entre tabs.

Corner-radius: 2 8 2 2 (top-right arredondado, encaixe no topo).

Contrato 19: Fora de resources/styles/, importa APENAS AppStyles.

Args:
    closable: Se True (padrão), exibe botão de fechar nas abas.
    parent: Widget pai.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics, QPainterPath, QBrush
from PySide6.QtWidgets import QTabBar

from core.config.LogUtils import LogUtils
from resources.styles.AppStyles import AppStyles


class HorizontalTab(QTabBar):
    """
    Abas horizontais customizadas com paintEvent próprio.
    Toda cor e gradiente vem do tema ativo via AppStyles.current_theme.

    Emite os sinais padrão do QTabBar:
        - currentChanged(int)
        - tabCloseRequested(int)
        - tabMoved(int, int)

    Uso:
        tabs = HorizontalTab(parent=self)
        tabs.addTab("Aba 1")
        tabs.setTabData(0, ("key", "title"))
        tabs.currentChanged.connect(self._on_tab_changed)
    """

    _paint_error_logged: bool = False

    def __init__(self, closable: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("workspace_tabs")
        self._closable = closable
        self._hovered_tab = -1
        self.logger = LogUtils(tool="System", class_name="HorizontalTab")

        self.setMouseTracking(True)
        self.setDrawBase(True)
        self.setExpanding(False)
        self.setMovable(True)
        self.setTabsClosable(closable)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

    # ── Closable ────────────────────────────────────────────────────

    @property
    def closable(self) -> bool:
        return self._closable

    @closable.setter
    def closable(self, value: bool):
        self._closable = value
        self.setTabsClosable(value)
        self.update()

    # ── Geometria ───────────────────────────────────────────────────

    def _tab_rect(self, index: int) -> QRect:
        """Retorna o retângulo da aba sem margem inferior."""
        r = self.tabRect(index)
        return QRect(r.x() + 1, r.y(), r.width() -2, r.height())

    def tabSizeHint(self, index: int) -> QSize:
        """Retorna tamanho mínimo baseado no texto + padding."""
        data = self.tabData(index)
        if data and isinstance(data, tuple):
            display = str(data[1])
        else:
            display = str(data) if data else f"Tab {index}"
        font = QFont("Segoe UI", 10)
        fm = QFontMetrics(font)
        close_margin = 8 if self._closable else 0
        text_w = fm.horizontalAdvance(display) + 30 + close_margin
        return QSize(max(text_w, 80), 28)

    # ── Pintura ─────────────────────────────────────────────────────

    def _draw_rounded_rect(self, painter, rect, tl=2, tr=8, br=2, bl=2):
        """Desenha retângulo com corner-radius customizado.
        tl=top-left, tr=top-right, br=bottom-right, bl=bottom-left."""
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
        try:
            if not self.isVisible() or not self.isEnabled():
                return
            painter = QPainter()
            if not painter.begin(self):
                return
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

            current_theme = AppStyles.current_theme

            # Fundo do tab bar (área vazia à direita)
            painter.fillRect(event.rect(), QColor(current_theme.TITLE_BAR))

            P = AppStyles.tab_common_colors()

            for i in range(self.count()):
                rect = self._tab_rect(i)
                if not rect.isValid() or rect.width() < 4:
                    continue

                selected = (i == self.currentIndex())
                hovered  = (i == self._hovered_tab)

                if selected:
                    fg     = QColor(P["fg_selected"])
                    border = QColor(P["border_selected"])
                elif hovered:
                    fg     = QColor(P["fg_hovered"])
                    border = QColor(P["border_hovered"])
                else:
                    fg     = QColor(P["fg_default"])
                    border = QColor(P["border_default"])

                path = self._draw_rounded_rect(painter, rect, tl=2, tr=8, br=2, bl=2)
                painter.setClipPath(path)

                w, h = rect.width(), rect.height()

                # ── Preencher com gradiente ──────────────────────────
                if selected:
                    # Selected: usa GRADIENT_ACCENT_STOPS (gradiente de acento)
                    accent_stops = current_theme.GRADIENT_ACCENT_STOPS
                    if accent_stops:
                        grad = AppStyles._build_linear_gradient(
                            accent_stops, current_theme.GRADIENT_ACCENT_ANGLE, w, h,
                        )
                        painter.fillPath(path, QBrush(grad))
                    else:
                        # Fallback: cor sólida ACCENT
                        painter.fillPath(path, QColor(P["bg_selected"]))
                else:
                    # Default/hovered: usa gradiente via GRADIENT_TAB_STOPS
                    tab_stops = current_theme.GRADIENT_TAB_STOPS
                    if tab_stops:
                        grad = AppStyles._build_linear_gradient(
                            tab_stops, current_theme.GRADIENT_TAB_ANGLE, w, h,
                        )
                        painter.fillPath(path, QBrush(grad))
                    else:
                        # Fallback: gradiente 2-stop clássico
                        grad_stops = (
                            (0.0, current_theme.GRADIENT_TAB[0]),
                            (1.0, current_theme.GRADIENT_TAB[1]),
                        )
                        grad = AppStyles._build_linear_gradient(
                            grad_stops, 45, w, h,
                        )
                        painter.fillPath(path, QBrush(grad))

                # Indicador de seleção (barra no topo)
                if selected:
                    painter.fillRect(rect.x(), rect.y(), rect.width(), 3, QColor(P["indicator"]))

                painter.setPen(QPen(border, 1))
                painter.drawPath(path)
                painter.setClipping(False)

                # ── Glow na aba selecionada (opcional) ────────────
                if selected and current_theme.GLOW_TAB_ENABLED and current_theme.GLOW_BLUR > 0:
                    glow_color = QColor(current_theme.GLOW_COLOR_RGB or current_theme.ACCENT)
                    glow_color.setAlpha(current_theme.GLOW_ALPHA)
                    painter.setPen(QPen(glow_color, 2))
                    painter.drawPath(path)

                # Texto da aba — usa o title (segundo elemento do tuple)
                data = self.tabData(i)
                if data and isinstance(data, tuple):
                    display = str(data[1])
                else:
                    display = str(data) if data else f"Tab {i}"
                font = QFont("Segoe UI", 10)
                font.setWeight(QFont.Weight.Medium if selected else QFont.Weight.Normal)
                painter.setFont(font)
                painter.setPen(QPen(fg))

                fm = QFontMetrics(font)
                text = fm.elidedText(display, Qt.TextElideMode.ElideRight, rect.width() - 16)
                painter.drawText(
                    rect.adjusted(8, 0, -8, 0),
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                    text,
                )

            painter.end()
        except SystemError as e:
            if not HorizontalTab._paint_error_logged:
                HorizontalTab._paint_error_logged = True
                self.logger.warning(
                    "PaintEvent suprimido (tab bar em transição)",
                    code="PAINT_SYS_ERR",
                    error=str(e),
                )

    # ── Eventos de mouse ────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        tab = self.tabAt(event.pos())
        old = self._hovered_tab
        self._hovered_tab = tab if tab >= 0 else -1
        if old != self._hovered_tab:
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hovered_tab = -1
        self.update()
        super().leaveEvent(event)