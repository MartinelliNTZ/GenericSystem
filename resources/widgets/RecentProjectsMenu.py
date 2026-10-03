# -*- coding: utf-8 -*-
"""
RecentProjectsMenu — Submenu de projetos recentes
===================================================
QMenu especializado em exibir lista de projetos recentes.
Cada item e um QWidgetAction com label estilizado para destacar
o nome do projeto (dourado, negrito) do path e data (cinza, menor).

Layout:
    Linha 1: NomeDoProjeto | C:/caminho/para/projeto.mtl
    Linha 2: Ultima modificacao: dd/mm/AAAA HH:MM:SS

Uso:
    from resources.widgets.RecentProjectsMenu import RecentProjectsMenu

    recent_menu = RecentProjectsMenu()
    recent_menu.rebuild(recents)
    recent_menu.project_clicked.connect(self._on_recent_clicked)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QMouseEvent, QEnterEvent
from PySide6.QtWidgets import QMenu, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QWidgetAction

from resources.styles.AppStyles import AppStyles


STYLE_NORMAL = 0
STYLE_HOVER = 1


class _RecentProjectItem(QWidget):
    """
    Widget customizado para cada item do menu de recentes.

    Layout:
        Linha 1: [Nome (destaque)]  |  [caminho (cinza)]
        Linha 2: Ultima modificacao: data

    Hover: fundo SURFACE_3, nome ACCENT_BRIGHT, path/data TEXT_MEDIUM.
    """

    clicked = Signal(str)  # path do projeto

    def __init__(self, name: str, path: str, last_modified: str, active: bool, parent=None):
        super().__init__(parent)
        self._path = path
        self._active = active
        self._labels: List[QLabel] = []
        self._build_ui(name, path, last_modified)

    def _build_ui(self, name: str, path: str, last_modified: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 1, 6, 1)
        layout.setSpacing(0)

        # Linha 1: Nome (destaque) + Caminho
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(8)

        name_label = QLabel(name)
        name_label.setObjectName("recent_name")
        name_label.setStyleSheet(AppStyles.recent_project_name_style(self._active))

        path_label = QLabel(path)
        path_label.setObjectName("recent_path")
        path_label.setStyleSheet(AppStyles.recent_project_sub_style(self._active))

        row1.addWidget(name_label)
        row1.addWidget(path_label)
        self._labels = [name_label, path_label]

        # Linha 2: Data
        date_text = (
            f"\u00daltima modifica\u00e7\u00e3o: {last_modified}"
            if last_modified else ""
        )
        date_label = QLabel(date_text)
        date_label.setObjectName("recent_date")

        layout.addLayout(row1)
        if date_text:
            date_label.setStyleSheet(AppStyles.recent_project_sub_style(self._active))
            layout.addWidget(date_label)
            self._labels.append(date_label)

    # Hover

    def enterEvent(self, event: QEnterEvent) -> None:
        """Mouse entrou no item: fundo SURFACE_3, labels em hover."""
        if self._active:
            self.setStyleSheet(f"background-color: {AppStyles.recent_project_hover_style()};")
            if len(self._labels) >= 2:
                self._labels[0].setStyleSheet(AppStyles.recent_project_hover_name_style())
                for lbl in self._labels[1:]:
                    lbl.setStyleSheet(AppStyles.recent_project_hover_sub_style())
        super().enterEvent(event)

    def leaveEvent(self, event: QMouseEvent) -> None:
        """Mouse saiu do item: volta ao estilo normal."""
        if self._active:
            self.setStyleSheet("")
            if len(self._labels) >= 2:
                self._labels[0].setStyleSheet(AppStyles.recent_project_name_style(True))
                for lbl in self._labels[1:]:
                    lbl.setStyleSheet(AppStyles.recent_project_sub_style(True))
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Clique no item emite sinal se ativo."""
        try:
            if self._active:
                self.clicked.emit(self._path)
        except RuntimeError:
            pass  # objeto C++ ja destruido (menu fechou)
        try:
            super().mouseReleaseEvent(event)
        except RuntimeError:
            pass


class RecentProjectsMenu(QMenu):
    """
    Menu dinamico exibindo a lista de projetos recentes.

    Cada item e um QWidgetAction com:
        Linha 1: Nome do projeto (destaque) | Caminho (cinza)
        Linha 2: Data da ultima modificacao

    Sinais:
        project_clicked(path: str)  emitido ao clicar em um projeto ativo
    """

    project_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Abrir Recente", parent)
        self.setStyleSheet(AppStyles.menu_dropdown_style())

    def rebuild(self, recents: List[Dict[str, Any]]) -> None:
        """
        Reconstroi o menu com a lista de projetos recentes.

        Args:
            recents: Lista de dicts com chaves path, name, folder, last_modified, active
        """
        self.clear()

        if not recents:
            empty_action = QAction("(nenhum projeto recente)", self)
            empty_action.setEnabled(False)
            self.addAction(empty_action)
            return

        for recent in recents:
            path = recent.get("path", "")
            name = recent.get("name", Path(path).stem if path else "?")
            last_modified = recent.get("last_modified", "")
            active = recent.get("active", False)

            widget = _RecentProjectItem(name, path, last_modified, active)
            widget.clicked.connect(self._emit_project_clicked)

            widget_action = QWidgetAction(self)
            widget_action.setDefaultWidget(widget)
            self.addAction(widget_action)

    def _emit_project_clicked(self, path: str) -> None:
        """Propaga o clique com o path do projeto."""
        self.project_clicked.emit(path)