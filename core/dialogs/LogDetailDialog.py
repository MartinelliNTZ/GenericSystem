# -*- coding: utf-8 -*-
"""
LogDetailDialog — Dialog de detalhes de um evento de log
===========================================================
Exibe todos os campos de um evento em formato texto selecionavel.
Uso:
    dialog = LogDetailDialog({"level": "INFO", "message": "OK"}, parent=self)
    dialog.exec()
"""

from __future__ import annotations

from typing import List

from PySide6.QtWidgets import QApplication, QHBoxLayout, QTextEdit

from core.dialogs.BaseDialog import BaseDialog


class LogDetailDialog(BaseDialog):
    """
    Dialog de detalhes de um evento de log.
    Exibe todos os campos em formato texto selecionavel.
    """

    def __init__(self, event: dict, parent=None):
        self._event = event
        super().__init__(
            parent=parent,
            title="Detalhes do Evento",
            min_size=(600, 400),
            modal=False,
        )
    def _build_ui(self) -> None:
        from utils.ColorProvider import ColorProvider

        lines: List[str] = []
        for key, value in self._event.items():
            if isinstance(value, dict):
                value = str(value)
            if value is None:
                value = ""
            lines.append(f"{key}: {value}")

        self.text_edit = QTextEdit("\n".join(lines))
        self.text_edit.setReadOnly(False)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0C0C0F;
                color: {ColorProvider.text_primary()};
                border: 1px solid #1A1A20;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                selection-background-color: #C9A84C;
                selection-color: #08080A;
            }}
        """)
        self.main_layout.addWidget(self.text_edit, 1)

        from resources.widgets.simple.SimpleGhostButton import SimpleGhostButton

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        copy_btn = SimpleGhostButton("Copiar Tudo")
        copy_btn.clicked.connect(self._copy_all)
        btn_layout.addWidget(copy_btn)
        close_btn = SimpleGhostButton("Fechar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        self.main_layout.addLayout(btn_layout)

    def _copy_all(self) -> None:
        """Copia todo o texto para a clipboard."""
        QApplication.clipboard().setText(self.text_edit.toPlainText())