# -*- coding: utf-8 -*-
"""
FileContextMenu — Menu de contexto reutilizável para arquivos/pastas
=====================================================================
Wrapper em volta de QMenu com ações comuns de arquivos.
Pode ser usado por qualquer widget que precise de um menu de contexto
para operações em arquivos (FileTreeWidget, etc.).
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, List, Optional

from PySide6.QtWidgets import QMenu


class FileAction(str, Enum):
    """Ações disponíveis no menu de contexto."""
    RENAME = "rename"
    DELETE = "delete"
    CREATE_FILE = "create_file"
    OPEN_IN_EXPLORER = "open_in_explorer"
    REFRESH = "refresh"


# Metadados das ações: título e atalho
_FILE_ACTION_META: Dict[FileAction, Dict[str, str]] = {
    FileAction.RENAME: {"title": "Renomear", "shortcut": "F2"},
    FileAction.DELETE: {"title": "Excluir", "shortcut": "Del"},
    FileAction.CREATE_FILE: {"title": "Criar Arquivo de Texto", "shortcut": "Ctrl+N"},
    FileAction.OPEN_IN_EXPLORER: {"title": "Abrir Local no Explorer", "shortcut": ""},
    FileAction.REFRESH: {"title": "Atualizar", "shortcut": "F5"},
}


class FileContextMenu(QMenu):
    """
    Menu de contexto configurável com ações de arquivo.

    Uso:
        actions = [FileAction.RENAME, FileAction.DELETE]
        callbacks = {
            FileAction.RENAME: lambda: print("rename"),
            FileAction.DELETE: lambda: print("delete"),
        }
        menu = FileContextMenu(actions, callbacks, self)
        menu.exec(some_point)
    """

    def __init__(
        self,
        actions: List[FileAction],
        callbacks: Dict[FileAction, Callable[[], None]],
        parent=None,
    ):
        super().__init__(parent)
        self._build(actions, callbacks)

    def _build(
        self,
        actions: List[FileAction],
        callbacks: Dict[FileAction, Callable[[], None]],
    ) -> None:
        """Constrói o menu com as ações fornecidas."""
        for i, action in enumerate(actions):
            meta = _FILE_ACTION_META.get(action, {})
            title = meta.get("title", action.value)
            shortcut = meta.get("shortcut", "")

            text = title
            if shortcut:
                text += f"\t{shortcut}"

            act = self.addAction(text)
            act.triggered.connect(callbacks.get(action, lambda: None))

            if action == FileAction.OPEN_IN_EXPLORER:
                self.addSeparator()

        self.addSeparator()
        self.addAction("Fechar").setEnabled(False)