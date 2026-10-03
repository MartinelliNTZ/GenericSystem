# -*- coding: utf-8 -*-
"""
ListFileDialog — Diálogo para listar e selecionar arquivos do projeto ativo
=============================================================================
Herda de BaseDialog e exibe uma lista de arquivos do projeto filtrados por
extensões. Suporta seleção única ou múltipla.

Uso:
    from resources.widgets.dialogs.ListFileDialog import ListFileDialog

    dialog = ListFileDialog(
        extensions=[".las", ".laz"],
        multi_select=True,
        parent=self,
    )
    if dialog.exec():
        selected = dialog.selected_paths  # list[str]
"""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QLabel

from core.dialogs.BaseDialog import BaseDialog
from utils.ProjectUtil import ProjectUtil


class ListFileDialog(BaseDialog):
    """
    Diálogo que exibe arquivos do projeto ativo filtrados por extensões.

    Args:
        extensions: Lista de extensões para filtrar (ex: [".las", ".laz"]).
        multi_select: Se True, permite selecionar múltiplos arquivos.
        parent: Widget pai.
    """

    def __init__(
        self,
        extensions: list[str],
        multi_select: bool = False,
        parent=None,
    ):
        self._extensions = extensions
        self._multi_select = multi_select
        self._selected: list[str] = []

        super().__init__(
            parent=parent,
            title="Arquivos do Projeto",
            object_name="list_file_dialog",
            fixed_size=(520, 420),
            modal=True,
            has_appbar=True,
        )

    def _build_ui(self):
        """Constrói a UI do diálogo."""
        self._add_title("Selecione os arquivos do projeto")

        # Label informativo
        ext_text = ", ".join(self._extensions)
        info = QLabel(f"Arquivos encontrados com as extensões: {ext_text}")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(info)

        # ListWidget
        self._list = QListWidget()
        self._list.setAlternatingRowColors(False)
        self.main_layout.addWidget(self._list, 1)

        if self._multi_select:
            self._list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        else:
            self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # Popula a lista
        self._populate()

        # Botões
        self._add_button_bar(["cancel", "carregar"])

    def _populate(self):
        """Busca arquivos do projeto e popula a lista."""
        files = ProjectUtil.get_files_by_extensions(self._extensions)
        if not files:
            item = QListWidgetItem("Nenhum arquivo encontrado no projeto ativo")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._list.addItem(item)
            return

        # Ordena por nome
        for name in sorted(files.keys()):
            full_path = files[name]
            item = QListWidgetItem(f"{name}  —  {full_path}")
            item.setData(Qt.ItemDataRole.UserRole, full_path)
            item.setToolTip(full_path)
            self._list.addItem(item)

    @property
    def selected_paths(self) -> list[str]:
        """Retorna a lista de caminhos selecionados."""
        return self._selected

    def accept(self):
        """Coleta os paths selecionados antes de aceitar."""
        self._selected = []
        for item in self._list.selectedItems():
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                self._selected.append(path)
        if not self._selected:
            return
        super().accept()