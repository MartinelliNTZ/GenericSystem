# -*- coding: utf-8 -*-
"""
GridTree — Árvore multicoluna genérica configurável
====================================================
Encapsula um QTreeWidget com colunas configuráveis, cores por célula,
nós hierárquicos (por chave) e widgets de ação por linha.

Não contém lógica de negócio — o consumidor define colunas, cria nós por
chave e atualiza textos/cores/widgets via API pública.

Sinais:
    node_activated(key: str) — emitido no duplo clique de um nó
    node_expanded(key: str)  — emitido quando um nó é expandido

Uso:
    from resources.widgets.grid.GridTree import GridTree

    tree = GridTree(columns=[
        {"header": "Projeto / Pasta", "stretch": True},
        {"header": "Status", "width": 110},
        {"header": "Ações", "width": 300},
    ])
    tree.add_node(key=str(path), texts={0: "OS_1", 1: "PROJETO"},
                  bold=True, kind="projeto")
    tree.add_node(key=str(folder), parent_key=str(path),
                  texts={0: "05_ASA", 1: "CORRETA"},
                  colors={0: "#61C975", 1: "#61C975"}, kind="pasta")
    tree.set_cell_text(str(folder), 2, "1.234")
    tree.set_cell_widget(str(folder), 2, meu_widget)
    tree.node_activated.connect(self._on_double_click)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

_KEY_ROLE = Qt.ItemDataRole.UserRole
_KIND_ROLE = Qt.ItemDataRole.UserRole + 1


class GridTree(QTreeWidget):
    """Árvore multicoluna genérica, indexada por chave de nó."""

    node_activated = Signal(str)
    node_expanded = Signal(str)

    def __init__(
        self,
        columns: List[Dict[str, Any]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._columns = columns
        self._nodes: Dict[str, QTreeWidgetItem] = {}
        self._build()

    # ── Construção ───────────────────────────────────────────────────

    def _build(self) -> None:
        """Configura colunas, cabeçalho e sinais."""
        self.setColumnCount(len(self._columns))
        self.setHeaderLabels([col.get("header", "") for col in self._columns])
        self.setAnimated(True)
        self.setIndentation(20)
        self.setIconSize(QSize(16, 16))
        self.setRootIsDecorated(True)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        header = self.header()
        for idx, col in enumerate(self._columns):
            if col.get("stretch"):
                header.setSectionResizeMode(idx, QHeaderView.ResizeMode.Stretch)
            elif col.get("width"):
                header.setSectionResizeMode(idx, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(idx, int(col["width"]))
            else:
                header.setSectionResizeMode(
                    idx, QHeaderView.ResizeMode.ResizeToContents
                )

        self.itemDoubleClicked.connect(self._on_double_clicked)
        self.itemExpanded.connect(self._on_item_expanded)

    # ── API pública ──────────────────────────────────────────────────

    def clear_nodes(self) -> None:
        """Remove todos os nós e limpa o índice interno."""
        self._nodes.clear()
        self.clear()

    def add_node(
        self,
        key: str,
        texts: Dict[int, Any],
        *,
        parent_key: Optional[str] = None,
        colors: Optional[Dict[int, str]] = None,
        icons: Optional[Dict[int, QIcon]] = None,
        bold: bool = False,
        kind: str = "",
    ) -> Optional[QTreeWidgetItem]:
        """
        Cria um nó (top-level ou filho) indexado por ``key``.

        Args:
            key: Chave única do nó.
            texts: Mapa {coluna: texto}.
            parent_key: Chave do nó pai (None = top-level).
            colors: Mapa {coluna: cor} aplicado como foreground.
            icons: Mapa {coluna: QIcon} aplicado como ícone da célula.
            bold: Se True, aplica negrito na coluna 0.
            kind: Rótulo livre do tipo de nó.

        Returns:
            O item criado, ou None se o pai não existir.
        """
        parent_item = self._nodes.get(parent_key) if parent_key else None
        if parent_key and parent_item is None:
            return None

        if parent_item is None:
            item = QTreeWidgetItem(self)
        else:
            item = QTreeWidgetItem(parent_item)

        for col, text in texts.items():
            item.setText(col, str(text))

        if colors:
            for col, color in colors.items():
                item.setForeground(col, QColor(color))

        if icons:
            for col, icon in icons.items():
                item.setIcon(col, icon)

        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(0, font)

        item.setData(0, _KEY_ROLE, key)
        item.setData(0, _KIND_ROLE, kind)
        self._nodes[key] = item
        return item

    def node(self, key: str) -> Optional[QTreeWidgetItem]:
        """Retorna o item do nó, ou None se não existir."""
        return self._nodes.get(key)

    def node_kind(self, key: str) -> str:
        """Retorna o rótulo ``kind`` do nó, ou string vazia."""
        item = self._nodes.get(key)
        return item.data(0, _KIND_ROLE) if item is not None else ""

    def set_cell_text(self, key: str, col: int, text: Any) -> None:
        """Define o texto de uma célula."""
        item = self._nodes.get(key)
        if item is not None:
            item.setText(col, str(text))

    def set_cell_color(self, key: str, col: int, color: str) -> None:
        """Define a cor de texto de uma célula."""
        item = self._nodes.get(key)
        if item is not None:
            item.setForeground(col, QColor(color))

    def set_cell_widget(self, key: str, col: int, widget: QWidget) -> None:
        """Define o widget exibido em uma célula (ex: botões de ação)."""
        item = self._nodes.get(key)
        if item is not None:
            self.setItemWidget(item, col, widget)

    def set_cell_icon(self, key: str, col: int, icon: QIcon) -> None:
        """Define o ícone de uma célula."""
        item = self._nodes.get(key)
        if item is not None:
            item.setIcon(col, icon)

    def clear_cell_icon(self, key: str, col: int) -> None:
        """Remove o ícone de uma célula."""
        item = self._nodes.get(key)
        if item is not None:
            item.setIcon(col, QIcon())

    def remove_node(self, key: str) -> None:
        """Remove um nó pelo índice (índice e árvore)."""
        item = self._nodes.pop(key, None)
        if item is None:
            return
        parent = item.parent()
        if parent is None:
            index = self.indexOfTopLevelItem(item)
            if index >= 0:
                self.takeTopLevelItem(index)
        else:
            parent.removeChild(item)

    def remove_children(self, parent_key: str) -> None:
        """Remove todos os descendentes de ``parent_key`` (mantém o nó).

        Útil para reconstruir apenas um ramo da árvore (refresh incremental).
        """
        item = self._nodes.get(parent_key)
        if item is None:
            return
        prefix = parent_key + os.sep
        for key in [k for k in self._nodes if k.startswith(prefix)]:
            self._nodes.pop(key, None)
        item.takeChildren()

    def set_node_hidden(self, key: str, hidden: bool) -> None:
        """Esconde/exibe um nó."""
        item = self._nodes.get(key)
        if item is not None:
            item.setHidden(hidden)

    def set_node_expanded(self, key: str, expanded: bool) -> None:
        """Expande/recolhe um nó."""
        item = self._nodes.get(key)
        if item is not None:
            item.setExpanded(expanded)

    def is_node_expanded(self, key: str) -> bool:
        """Indica se o nó está expandido."""
        item = self._nodes.get(key)
        return item.isExpanded() if item is not None else False

    def has_node(self, key: str) -> bool:
        """Indica se o nó existe no índice."""
        return key in self._nodes

    def keys(self) -> List[str]:
        """Retorna as chaves de todos os nós indexados."""
        return list(self._nodes.keys())

    def expanded_keys(self) -> List[str]:
        """Retorna as chaves de todos os nós expandidos."""
        return [key for key, item in self._nodes.items() if item.isExpanded()]

    def expand_all(self) -> None:
        """Expande todos os nós da árvore."""
        self.expandAll()

    def collapse_all(self) -> None:
        """Recolhe todos os nós da árvore."""
        self.collapseAll()

    # ── Privados ─────────────────────────────────────────────────────

    def _on_double_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        """Emite node_activated com a chave do nó clicado."""
        key = item.data(0, _KEY_ROLE)
        if key:
            self.node_activated.emit(str(key))

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Emite node_expanded com a chave do nó expandido."""
        key = item.data(0, _KEY_ROLE)
        if key:
            self.node_expanded.emit(str(key))
