# -*- coding: utf-8 -*-
"""
ImagePreviewPanel — Widget de pré-visualização de imagem com zoom e pan
========================================================================
Widget standalone que exibe uma imagem com zoom (roda do mouse), arrasto
lateral (botão esquerdo), reset por duplo clique ou tecla '7'.

Usa paintEvent em vez de QLabel para evitar que o size hint mude
quando a imagem é carregada, mantendo o layout pai estável.

Uso:
    preview = ImagePreviewPanel(fixed_size=(480, 360))
    preview.show_preview("c:/foto.png")
    preview.clear_preview()
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPixmap, QImage, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget, QSizePolicy


class ImagePreviewPanel(QWidget):
    """
    Painel de pré-visualização de imagem com zoom e pan.

    Parâmetros:
        fixed_size: tuple (largura, altura) — tamanho fixo do preview.
                    None expande ao espaço disponível.
    """

    def __init__(
        self,
        fixed_size: tuple[int, int] | None = (480, 360),
        parent=None,
    ):
        super().__init__(parent)
        self._base_pixmap: QPixmap | None = None
        self._zoom_factor: float = 1.0
        self._pan_offset: QPoint = QPoint(0, 0)
        self._is_dragging: bool = False
        self._drag_start: QPointF = QPointF(0, 0)
        self._drag_start_pan: QPoint = QPoint(0, 0)
        self._fixed_size = fixed_size

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if fixed_size is not None:
            self.setMinimumSize(fixed_size[0], fixed_size[1])
            self.setMaximumSize(fixed_size[0], fixed_size[1])

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ── API Pública ─────────────────────────────────────────────────

    def show_preview(self, path: str) -> None:
        """Carrega e exibe a imagem do caminho informado."""
        if not path:
            self.clear_preview()
            return

        try:
            from PIL import Image as PILImage
            from io import BytesIO

            img = PILImage.open(path)
            self._load_image(img)
        except Exception as e:
            self._base_pixmap = None
            self.update()

    def _load_image(self, img) -> None:
        """Converte PIL Image para QPixmap e armazena."""
        from io import BytesIO
        bio = BytesIO()
        img.convert("RGBA").save(bio, format="PNG")
        qimg = QImage.fromData(bio.getvalue())
        self._base_pixmap = QPixmap.fromImage(qimg)
        self._zoom_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self.update()

    def clear_preview(self) -> None:
        """Limpa o preview."""
        self._base_pixmap = None
        self._zoom_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self.update()

    # ── Paint ───────────────────────────────────────────────────────

    def paintEvent(self, event: QPaintEvent) -> None:
        """Desenha o pixmap diretamente — sem QLabel."""
        super().paintEvent(event)
        if self._base_pixmap is None or self._base_pixmap.isNull():
            return

        w = self.width()
        h = self.height()
        if w < 1 or h < 1:
            return

        zoomed = self._base_pixmap.scaled(
            int(w * self._zoom_factor),
            int(h * self._zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        zw, zh = zoomed.width(), zoomed.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if zw <= w and zh <= h:
            off_x = (w - zw) // 2
            off_y = (h - zh) // 2
            painter.drawPixmap(off_x, off_y, zoomed)
        else:
            max_sx = max(0, zw - w)
            max_sy = max(0, zh - h)
            sx = max_sx // 2 + self._pan_offset.x()
            sy = max_sy // 2 + self._pan_offset.y()
            sx = max(0, min(sx, max_sx))
            sy = max(0, min(sy, max_sy))
            painter.drawPixmap(0, 0, w, h, zoomed, sx, sy, w, h)

        painter.end()

    # ── Eventos ─────────────────────────────────────────────────────

    def wheelEvent(self, event):
        """Zoom in/out com roda do mouse."""
        if self._base_pixmap is None or self._base_pixmap.isNull():
            super().wheelEvent(event)
            return
        delta = event.angleDelta().y()
        self._zoom_factor *= 1.15 if delta > 0 else (1.0 / 1.15)
        self._zoom_factor = max(0.1, min(10.0, self._zoom_factor))
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        """Inicia arrasto com botão esquerdo."""
        if (event.button() == Qt.MouseButton.LeftButton
                and self._base_pixmap is not None
                and not self._base_pixmap.isNull()):
            self._is_dragging = True
            self._drag_start = event.position()
            self._drag_start_pan = QPoint(self._pan_offset)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Atualiza pan durante arrasto."""
        if self._is_dragging:
            delta = event.position() - self._drag_start
            self._pan_offset = QPoint(
                int(self._drag_start_pan.x() - delta.x()),
                int(self._drag_start_pan.y() - delta.y()),
            )
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finaliza arrasto."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Reset zoom/pan no duplo clique."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._zoom_factor = 1.0
            self._pan_offset = QPoint(0, 0)
            self.update()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        """Tecla '7' reseta zoom/pan."""
        if event.key() == Qt.Key.Key_7:
            self._zoom_factor = 1.0
            self._pan_offset = QPoint(0, 0)
            self.update()
            event.accept()
            return
        super().keyPressEvent(event)