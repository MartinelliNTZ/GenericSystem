# -*- coding: utf-8 -*-
"""
PreviewPanel — Widget de pré-visualização genérico
====================================================
Exibe preview de arquivos com detecção automática de tipo.

Delega o conteúdo para o widget apropriado conforme a extensão:

- Imagens → ImagePreviewPanel (zoom, pan, mouse/key 7)
- Texto  → TextPreviewWidget (editor com Copiar/Salvar)

Novos tipos podem ser registrados via register_handler().

Uso:
    preview = PreviewPanel()
    preview.show_preview("c:/foto.png")
    preview.clear_preview()
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from resources.widgets.ImagePreviewPanel import ImagePreviewPanel
from resources.widgets.TextPreviewWidget import TextPreviewWidget
from utils.DictManager import IMAGE_EXTENSIONS, TEXT_EXTENSIONS


# ── Registry de Handlers ─────────────────────────────────────────────
_HANDLERS: list[tuple[frozenset[str], Callable[[str], QWidget]]] = []


def register_handler(
    extensions: frozenset[str],
    factory: Callable[[str], QWidget],
) -> None:
    """Registra um handler para um conjunto de extensões."""
    _HANDLERS.append((extensions, factory))


register_handler(frozenset(IMAGE_EXTENSIONS.keys()), lambda p: (
    lambda panel: (panel.show_preview(p), panel)[1]
)(ImagePreviewPanel(fixed_size=None)))

register_handler(frozenset(TEXT_EXTENSIONS.keys()), lambda p: (
    lambda tw: (tw.load_file(p), tw)[1]
)(TextPreviewWidget()))


class PreviewPanel(QWidget):
    """
    Painel de pré-visualização genérico.
    Container simples que detecta o tipo do arquivo pela extensão
    e delega o preview ao widget adequado.
    """

    def __init__(
        self,
        fixed_size: tuple[int, int] | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Placeholder removido — show_preview coloca o widget direto
        self._handler_widget: QWidget | None = None

    # ── API Pública ─────────────────────────────────────────────────

    def show_preview(self, path: str) -> None:
        """Carrega e exibe preview do arquivo. Detecta tipo pela extensão."""
        if not path:
            return

        try:
            _, ext = os.path.splitext(path)
            ext = ext.lower()

            widget: QWidget | None = None
            if ext in IMAGE_EXTENSIONS:
                panel = ImagePreviewPanel(fixed_size=None)
                panel.show_preview(path)
                widget = panel
            elif ext in TEXT_EXTENSIONS:
                tw = TextPreviewWidget()
                tw.load_file(path)
                widget = tw
            else:
                for extensions, factory in _HANDLERS:
                    if ext in extensions:
                        widget = factory(path)
                        break

            if widget is None:
                return

            # Remove widget anterior se houver
            if self._handler_widget:
                self._layout.removeWidget(self._handler_widget)
                self._handler_widget.setParent(None)
                self._handler_widget.deleteLater()

            self._handler_widget = widget
            self._layout.addWidget(widget, 1)
        except Exception:
            pass

    def clear_preview(self) -> None:
        """Limpa o preview."""
        if self._handler_widget:
            self._layout.removeWidget(self._handler_widget)
            self._handler_widget.setParent(None)
            self._handler_widget.deleteLater()
            self._handler_widget = None