# -*- coding: utf-8 -*-
"""
TextPreviewWidget — Widget de pré-visualização e edição de texto
=================================================================
Exibe conteúdo de arquivos texto com botões Copiar e Salvar.

Uso:
    text_widget = TextPreviewWidget()
    text_widget.load_file("c:/arquivo.txt")
    text_widget.load_text("conteúdo manual")
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QClipboard
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton, QApplication,
)


# ── Códigos de encoding para tentativa ───────────────────────────────
_ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]


class TextPreviewWidget(QWidget):
    """
    Editor de texto simples com botões Copiar e Salvar.

    Suporta:
    - Carregamento de arquivo com detecção de encoding
    - Edição livre
    - Copiar conteúdo para área de transferência
    - Salvar alterações no arquivo original
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Barra de botões ─────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 4, 4, 0)
        btn_layout.setSpacing(6)

        self._btn_copy = QPushButton("Copiar")
        self._btn_copy.clicked.connect(self._on_copy)
        btn_layout.addWidget(self._btn_copy)

        btn_layout.addStretch()

        self._btn_save = QPushButton("Salvar")
        self._btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self._btn_save)

        layout.addLayout(btn_layout)

        # ── Área de texto ───────────────────────────────────────────
        self._editor = QPlainTextEdit()
        self._editor.setObjectName("text_preview_editor")
        font = QFont("Consolas", 10)
        self._editor.setFont(font)
        self._editor.setTabStopDistance(20)
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._editor, 1)

        self._dirty: bool = False
        self._editor.textChanged.connect(self._on_text_changed)

    # ── API Pública ─────────────────────────────────────────────────

    def load_file(self, path: str) -> None:
        """
        Carrega o conteúdo de um arquivo no editor.

        Tenta múltiplos encodings automaticamente.
        Se falhar, exibe mensagem de erro no editor.
        """
        self._file_path = path
        if not path or not os.path.isfile(path):
            self._editor.setPlainText(f"Arquivo não encontrado:\n{path}")
            self._update_state(False)
            return

        for enc in _ENCODINGS:
            try:
                with open(path, "r", encoding=enc) as f:
                    content = f.read()
                self._editor.setPlainText(content)
                self._update_state(False)
                return
            except (UnicodeDecodeError, UnicodeError):
                continue

        # Fallback: tenta binary ignore
        try:
            with open(path, "rb") as f:
                raw = f.read()
            content = raw.decode("utf-8", errors="replace")
            self._editor.setPlainText(content)
            self._update_state(False)
        except Exception as e:
            self._editor.setPlainText(f"Erro ao ler arquivo:\n{path}\n{e}")
            self._update_state(False)

    def load_text(self, text: str) -> None:
        """Carrega texto diretamente (sem arquivo associado)."""
        self._file_path = None
        self._editor.setPlainText(text)
        self._update_state(False)

    def clear(self) -> None:
        """Limpa editor e reseta estado."""
        self._file_path = None
        self._editor.clear()
        self._update_state(False)

    @property
    def text(self) -> str:
        """Retorna o texto atual do editor."""
        return self._editor.toPlainText()

    @property
    def is_dirty(self) -> bool:
        """True se o texto foi modificado após última carga/salvamento."""
        return self._dirty

    # ── Internos ────────────────────────────────────────────────────

    def _update_state(self, dirty: bool) -> None:
        """Atualiza estado dirty e label do botão salvar."""
        self._dirty = dirty
        if self._file_path and dirty:
            self._btn_save.setText("Salvar *")
        else:
            self._btn_save.setText("Salvar")

    def _on_text_changed(self) -> None:
        """Marcado como dirty quando o texto muda."""
        if not self._dirty:
            self._update_state(True)

    def _on_copy(self) -> None:
        """Copia o texto para área de transferência."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._editor.toPlainText())

    def _on_save(self) -> None:
        """Salva o conteúdo no arquivo original."""
        if not self._file_path:
            return
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                f.write(self._editor.toPlainText())
            self._update_state(False)
        except Exception as e:
            from utils.MessageBox import MessageBox
            MessageBox.critical(self, "Erro", f"Não foi possível salvar:\n{e}")
