# -*- coding: utf-8 -*-
"""
FileManagerPlugin — Explorador de Arquivos Interno
====================================================
Ferramenta SIDE (painel lateral) que exibe o conteúdo da root_folder
definida pelo SaveProjectPlugin.

Funcionalidades:
- Exibe árvore de diretórios com QFileSystemModel (ícones do Windows)
- Renomear via F2 (nativo do QTreeView)
- Excluir via Del com confirmação
- Drag & Drop interno e externo (arrastar para QGIS/Explorer)
- Context menu padrão do QTreeView + "Abrir Local no Explorer"
- Reage ao sinal project_changed do SignalManager
"""

from __future__ import annotations

import os
from pathlib import Path

from core.dialogs.FilePreviewDialog import FilePreviewDialog
from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.FileTreeWidget import FileTreeWidget


class FileManagerPlugin(BasePlugin):
    """
    Explorador de arquivos interno do projeto.
    Lê root_folder das sys_preferences e exibe na árvore.
    """

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.FILE_MANAGER.value,
            parent=parent,
            sys_prefs=True,
            title="Explorador",
        )
        self._current_root: str | None = None
        self._connect_signals()
        self.load_prefs()
        self.logger.info("FileManagerPlugin carregado", code="FM_READY")

    # ── UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        """Constrói a UI com ExecutionButtons e FileTreeWidget."""
        super()._build_ui()

        # Botões de ação
        self.buttons = ExecutionButtons(self, {
            "create_file": {
                "text": "CRIAR ARQUIVO",
                "callback": self._on_create_file,
                "type": "secondary",
                "description": "Cria um arquivo de texto vazio na pasta selecionada",
            },
            "refresh": {
                "text": "ATUALIZAR",
                "callback": self._on_refresh,
                "type": "secondary",
                "description": "Recarrega a árvore de diretórios",
            },
        })
        self.main_layout.addWidget(self.buttons)

        # Árvore de arquivos
        self.file_tree = FileTreeWidget(self)
        self.file_tree.file_double_clicked.connect(self._on_file_double_clicked)
        self.main_layout.addWidget(self.file_tree, 1)

    # ── Preferências ───────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Carrega root_folder das sys_preferences e atualiza árvore."""
        root = self.sys_preferences.get("root_folder", None)

        if root and os.path.isdir(root):
            resolved = str(Path(root).resolve())
            self._current_root = resolved
            self.file_tree.set_root_path(resolved)
            self.logger.info("Root folder carregada", code="FM_ROOT",
                             root_folder=resolved)
        else:
            self._current_root = None
            self.logger.info("Nenhuma root folder encontrada",
                             code="FM_NO_ROOT")

    def save_prefs(self) -> None:
        """Sem preferências próprias para persistir."""
        pass

    # ── Sinais ─────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """Conecta ao sinal project_changed do SignalManager."""
        SignalManager.instance().project_changed.connect(self._on_project_changed)

    def _on_project_changed(self) -> None:
        """
        Chamado quando o projeto ativo muda (SaveProjectPlugin).
        Recarrega root_folder das sys_preferences.
        """
        from utils.Preferences import Preferences
        self.sys_preferences = Preferences.load_tool_prefs(ToolKey.SYSTEM)
        self.load_prefs()

    # ── Handlers ───────────────────────────────────────────────────

    def _on_file_double_clicked(self, path: str) -> None:
        """Abre diálogo de preview do arquivo."""
        from core.dialogs.FilePreviewDialog import FilePreviewDialog
        FilePreviewDialog.exec_preview(file_path=path, parent=self)

    def _on_create_file(self) -> None:
        """Cria um arquivo de texto na pasta selecionada."""
        self.file_tree.create_text_file()

    def _on_refresh(self) -> None:
        """Recarrega a árvore de diretórios."""
        self.file_tree.refresh()
        self.logger.info("Árvore atualizada manualmente", code="FM_REFRESH")