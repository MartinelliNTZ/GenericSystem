# -*- coding: utf-8 -*-
"""
FileTreeWidget — Widget QTreeView + QFileSystemModel para exploração de arquivos
=================================================================================
Componente reutilizável que exibe uma árvore de diretórios usando o modelo
nativo QFileSystemModel do Qt (ícones do Windows, datas, zero dependências externas).

Suporta:
- Navegação por árvore com root folder fixa (não sai da raiz)
- Multi-seleção (Ctrl+clique, Shift+clique, Ctrl+A)
- Renomear nativo via F2 (QTreeView já suporta)
- Drag & Drop interno (mover arquivos entre pastas)
- Drag externo (arrastar arquivos para QGIS, Explorer, etc.)
- Atalho Del para excluir com confirmação
- Diálogo de ações (FileContextDialog) ao clicar com botão direito
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import List

from PySide6.QtCore import QDir, QMimeData, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileSystemModel,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QTreeView,
    QWidget,
)

from core.dialogs.FileContextMenu import FileAction, FileContextMenu
from utils.MessageBox import MessageBox


class FileTreeWidget(QWidget):
    """
    Árvore de diretórios baseada em QFileSystemModel.

    Sinais:
        file_double_clicked(path: str)
        file_deleted(path: str)
        file_moved(src: str, dst: str)
    """

    file_double_clicked = Signal(str)
    file_deleted = Signal(str)
    file_moved = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._root_path: str | None = None
        self._root_index = None

        # ── Modelo nativo do Qt ────────────────────────────────────
        self._model = QFileSystemModel(self)
        self._model.setFilter(
            QDir.Filter.AllDirs
            | QDir.Filter.Files
            | QDir.Filter.NoDotAndDotDot
        )
        self._model.setRootPath(QDir.rootPath())

        # ── TreeView (mínima configuração) ─────────────────────────
        self._tree = _FileTreeView(self)
        self._tree.setObjectName("file_tree")
        self._tree.setModel(self._model)
        self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._tree.setDragEnabled(True)
        self._tree.setAcceptDrops(True)
        self._tree.setDropIndicatorShown(True)
        self._tree.setDragDropMode(QAbstractItemView.DragDrop)
        self._tree.setDefaultDropAction(Qt.MoveAction)
        self._tree.setAnimated(True)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.AscendingOrder)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.setSelectionBehavior(QAbstractItemView.SelectRows)

        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.doubleClicked.connect(self._on_double_click)

        # ── Layout ─────────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree, 1)

    # ── API pública ────────────────────────────────────────────────

    def set_root_path(self, path: str) -> None:
        """Define o diretório raiz da árvore."""
        self._root_path = str(Path(path).resolve())
        self._root_index = self._model.setRootPath(self._root_path)
        self._tree.setRootIndex(self._root_index)

    def refresh(self) -> None:
        """Recarrega o modelo."""
        if self._root_path:
            self._model.setRootPath(self._root_path)

    def selected_path(self) -> str | None:
        """Retorna o path do primeiro item selecionado ou None."""
        paths = self.selected_paths()
        return paths[0] if paths else None

    def selected_paths(self) -> List[str]:
        """Retorna paths únicos dos itens selecionados."""
        indexes = self._tree.selectedIndexes()
        seen: set[str] = set()
        paths: list[str] = []
        for idx in indexes:
            if idx.column() != 0:
                continue
            path = self._model.filePath(idx)
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
        return paths

    def rename_selected(self) -> bool:
        """Renomeia o item selecionado (apenas 1)."""
        path = self.selected_path()
        if not path:
            return False

        old = Path(path)
        new_name, ok = QInputDialog.getText(
            self, "Renomear", "Novo nome:", text=old.name,
        )
        if not ok or not new_name or new_name == old.name:
            return False

        new_path = old.parent / new_name
        try:
            os.rename(str(old), str(new_path))
            return True
        except Exception:
            return False

    def create_text_file(self, directory: str | None = None) -> bool:
        """
        Cria um arquivo de texto vazio.
        Se directory=None, usa a pasta selecionada ou a raiz.
        """
        if directory is None:
            sel = self.selected_path()
            if sel and Path(sel).is_dir():
                directory = sel
            elif sel:
                directory = str(Path(sel).parent)
            else:
                directory = self._root_path

        if not directory:
            return False

        name, ok = QInputDialog.getText(
            self, "Criar Arquivo", "Nome do arquivo:", text="novo_arquivo.txt",
        )
        if not ok or not name:
            return False

        p = Path(name)
        if not p.suffix:
            name = name + ".txt"

        file_path = Path(directory) / name
        if file_path.exists():
            confirm = MessageBox.show_question(
                f"Arquivo '{name}' já existe. Substituir?",
                title="Arquivo Existente",
                buttons=MessageBox.YES_NO,
                default_button=MessageBox.NO,
            )
            if confirm != MessageBox.YES:
                return False

        try:
            file_path.touch(exist_ok=True)
            return True
        except Exception:
            return False

    def delete_selected(self) -> bool:
        """Exclui itens selecionados com confirmação."""
        paths = self.selected_paths()
        if not paths:
            return False

        count = len(paths)
        label = (
            f"Excluir {count} itens?" if count > 1
            else f'Excluir "{Path(paths[0]).name}"?'
        )

        confirmed = MessageBox.show_question(
            label,
            title="Confirmar Exclusão",
            detail="Esta ação não pode ser desfeita.",
            buttons=MessageBox.YES_NO,
            default_button=MessageBox.NO,
        )
        if confirmed != MessageBox.YES:
            return False

        errors: list[str] = []
        for path in paths:
            try:
                p = Path(path)
                if p.is_dir():
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.file_deleted.emit(path)
            except Exception:
                errors.append(path)

        if errors:
            MessageBox.show_warning(
                f"Não foi possível excluir {len(errors)} item(ns).",
                title="Erro ao Excluir",
            )

        return len(errors) == 0

    # ── Context menu (via FileContextDialog) ───────────────────────

    def _on_context_menu(self, pos) -> None:
        """Mostra menu de contexto com ações para arquivos/pastas."""
        paths = self.selected_paths()
        actions = []
        callbacks = {}

        if len(paths) == 1:
            actions.append(FileAction.RENAME)
            callbacks[FileAction.RENAME] = self.rename_selected

        if paths:
            actions.append(FileAction.DELETE)
            callbacks[FileAction.DELETE] = self.delete_selected
            actions.append(FileAction.OPEN_IN_EXPLORER)
            callbacks[FileAction.OPEN_IN_EXPLORER] = self._open_in_explorer
        else:
            actions.append(FileAction.CREATE_FILE)
            callbacks[FileAction.CREATE_FILE] = lambda: self.create_text_file()
            actions.append(FileAction.REFRESH)
            callbacks[FileAction.REFRESH] = self.refresh

        menu = FileContextMenu(actions, callbacks, self)
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _on_double_click(self, index) -> None:
        """Emite file_double_clicked com o path do item clicado."""
        path = self._model.filePath(index)
        if path:
            self.file_double_clicked.emit(path)

    def _open_in_explorer(self) -> None:
        """Abre Windows Explorer no local do item selecionado."""
        paths = self.selected_paths()
        if not paths:
            if self._root_path:
                subprocess.Popen(f'explorer "{self._root_path}"')
            return
        path = paths[0]
        try:
            p = Path(path)
            if p.is_file():
                subprocess.Popen(f'explorer /select,"{path}"')
            else:
                subprocess.Popen(f'explorer "{path}"')
        except Exception:
            pass


class _FileTreeView(QTreeView):
    """
    QTreeView customizado:
    - Del → exclui selecionados
    - Drag externo com urls (QGIS, Explorer)
    - Drop interno com shutil.move e conflito
    """

    def keyPressEvent(self, event) -> None:
        """Captura Del para excluir."""
        if event.key() == Qt.Key_Delete:
            widget = self.parent()
            if isinstance(widget, FileTreeWidget):
                widget.delete_selected()
                return
        super().keyPressEvent(event)

    def startDrag(self, supported_actions) -> None:
        """Drag externo com urls para QGIS/Explorer."""
        widget = self.parent()
        if not isinstance(widget, FileTreeWidget):
            super().startDrag(supported_actions)
            return

        paths = widget.selected_paths()
        if not paths:
            return

        from PySide6.QtCore import QUrl

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(p) for p in paths])

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction | Qt.MoveAction)

    def dropEvent(self, event) -> None:
        """
        Drop interno com shutil.move.
        Se conflito: substitui. Se destino = origem: ignora.
        """
        widget = self.parent()
        if not isinstance(widget, FileTreeWidget):
            super().dropEvent(event)
            return

        src_paths = widget.selected_paths()
        if not src_paths:
            event.ignore()
            return

        drop_idx = self.indexAt(event.position().toPoint())
        if drop_idx.isValid():
            dst_dir = Path(widget._model.filePath(drop_idx))
            if not dst_dir.is_dir():
                dst_dir = dst_dir.parent
        else:
            dst_dir = Path(widget._root_path or "")

        if not dst_dir.exists():
            event.ignore()
            return

        for src in src_paths:
            src_p = Path(src)
            dst = dst_dir / src_p.name

            if src_p in dst.parents or src_p == dst:
                continue

            if dst.exists():
                reply = QMessageBox.question(
                    self,
                    "Substituir Arquivo",
                    f'O destino já contém "{dst.name}". Substituir?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    continue

            try:
                shutil.move(str(src), str(dst))
                widget.file_moved.emit(str(src), str(dst))
            except Exception:
                pass

        event.accept()