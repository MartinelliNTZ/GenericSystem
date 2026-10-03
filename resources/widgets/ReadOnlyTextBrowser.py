# -*- coding: utf-8 -*-
"""
ReadOnlyTextBrowser — Widget de texto somente leitura
=====================================================
QTextBrowser pré-configurado para exibição de logs, resultados e
conteúdo textual sem edição. Suporta HTML, links internos e
placeholder.

Uso:
    from resources.widgets.ReadOnlyTextBrowser import ReadOnlyTextBrowser

    browser = ReadOnlyTextBrowser(
        placeholder="Mensagens aparecem aqui...",
        open_links=True,
    )
    browser.append_html("<b>texto</b>")
    browser.clear_content()
    browser.select_all()
    browser.copy_all()
    browser.to_plain_text()
"""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QTextBrowser


class ReadOnlyTextBrowser(QTextBrowser):
    """
    QTextBrowser read-only com configurações padronizadas.

    Serve como base para consoles, visualizadores de log, previews
    de texto, etc. Todo plugin que precisar exibir texto formatado
    deve usar este widget em vez de configurar um QTextBrowser bruto.

    Atalhos de teclado:
        Ctrl+A  → selecionar todo o texto
        Ctrl+C  → copiar texto selecionado
    """

    def __init__(
        self,
        placeholder: str = "",
        open_links: bool = False,
        open_external_links: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenLinks(open_links)
        self.setOpenExternalLinks(open_external_links)
        if placeholder:
            self.setPlaceholderText(placeholder)

    # ── Métodos auxiliares ──────────────────────────────────────────

    def append_html(self, html: str) -> None:
        """Adiciona conteúdo HTML ao final do texto existente."""
        self.append(html)

    def clear_content(self) -> None:
        """Limpa todo o conteúdo exibido."""
        self.clear()

    def select_all(self) -> None:
        """Seleciona todo o texto."""
        self.selectAll()

    def copy_all(self) -> None:
        """
        Copia todo o conteúdo (plain text) para a área de transferência.
        """
        QGuiApplication.clipboard().setText(self.toPlainText())

    def to_plain_text(self) -> str:
        """Retorna o conteúdo como texto puro."""
        return self.toPlainText()