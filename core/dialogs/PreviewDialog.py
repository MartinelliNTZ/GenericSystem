# -*- coding: utf-8 -*-
"""
PreviewDialog — Diálogo genérico de pré-visualização
======================================================
Exibe uma lista de itens em um QTextEdit somente leitura,
com título dinâmico contendo a contagem de itens.

Uso:
    PreviewDialog.exec_preview(
        items=[("orig.txt", "novo.txt"), ...],
        title="Pré-Visualização",
        parent=self,
    )
"""

from __future__ import annotations

from typing import List, Tuple

from PySide6.QtWidgets import QTextEdit

from core.config.LogUtils import LogUtils
from core.dialogs.BaseDialog import BaseDialog
from core.enum.ToolKey import ToolKey
from resources.widgets.CollapsibleParams import CollapsibleParams
from resources.widgets.simple.SimpleLabel import SimpleLabel

_logger = LogUtils(tool=ToolKey.SYSTEM.value, class_name="PreviewDialog")


class PreviewDialog(BaseDialog):
    """
    Diálogo modal de pré-visualização.
    """

    def __init__(
        self,
        items: List[Tuple[str, str]],
        title: str = "Pré-Visualização",
        parent=None,
        max_preview: int = 50,
    ):
        self._items = items
        self._max_preview = max_preview
        super().__init__(
            parent=parent,
            title=f"{title} — {len(items)} itens",
            min_size=(600, 400),
            modal=True,
        )

    def _build_ui(self):
        lines = [f"{orig} → {novo}" for orig, novo in self._items[:self._max_preview]]
        if len(self._items) > self._max_preview:
            lines.append(f"... e mais {len(self._items) - self._max_preview} item(ns)")

        te = QTextEdit("\n".join(lines))
        te.setReadOnly(True)
        self.main_layout.addWidget(te, 1)

        # ── Seção colapsável de exemplo ─────────────────────────
        col = CollapsibleParams(
            title="Informações da Operação",
            collapsed=True,
            parent=self,
        )
        col.content_layout.addWidget(
            SimpleLabel(f"Total de itens: {len(self._items)}")
        )
        col.content_layout.addWidget(
            SimpleLabel(f"Máx. exibidos: {self._max_preview}")
        )
        self.main_layout.addWidget(col)

        self._add_button_bar(["close"])

        _logger.info(
            "PreviewDialog construído",
            code="PREVIEW_BUILD",
            total_items=len(self._items),
            max_preview=self._max_preview,
        )

    @staticmethod
    def exec_preview(
        items: List[Tuple[str, str]],
        title: str = "Pré-Visualização",
        parent=None,
    ) -> None:
        """Atalho para criar, executar e descartar o diálogo."""
        dlg = PreviewDialog(items=items, title=title, parent=parent)
        dlg.exec()