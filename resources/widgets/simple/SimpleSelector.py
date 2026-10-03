# -*- coding: utf-8 -*-
"""
SimpleSelector — Linha com label, QLineEdit e botão "..." para selecionar arquivo/pasta.
Uso: campo de caminho único com seletor embutido.

QFileDialog é PROIBIDO fora de utils/ExplorerUtils.
SimpleSelector usa ExplorerUtils para todas as operações de seleção.

O botão 📂 (suggested_path) funciona da seguinte forma:
  - O plugin passa um PATH RELATIVO (ex: "vetores/black_points_filter")
  - Quando o botão 📂 é clicado, o SimpleSelector busca o root_folder
    do projeto ativo via ProjectUtil.get_root_folder()
  - Concatena root_folder + path_relativo e insere no QLineEdit

Mode Selector (mode_selector):
  - Se informado, exibe um GridRadio com opções (ex: "Arquivo"/"Pasta")
  - O browse_mode e placeholder se adaptam automaticamente ao modo selecionado
  - Acesse o modo atual via selector.mode

Callbacks (atributos públicos, sobrescreva para conectar lógica externa):
    selector.on_path_change = meu_callback    # recebe (new_path)
    selector.on_browse_click = meu_callback   # recebe ()
    selector.on_suggest_click = meu_callback  # recebe ()
    selector.on_mode_change = meu_callback    # recebe (mode_key)
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit

from core.config.LogUtils import LogUtils
from resources.widgets.dialogs.ListFileDialog import ListFileDialog
from resources.widgets.grid.GridRadio import GridRadio
from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton
from utils.ExplorerUtils import ExplorerUtils
from utils.ProjectUtil import ProjectUtil


class SimpleSelector(QWidget):
    """
    Linha com label, QLineEdit editável e botão "..." que abre explorador.

    Tipos de seleção (browse_mode):
        "open_file"    — 1 arquivo (leitura)
        "open_files"   — múltiplos arquivos (leitura)
        "save_file"    — 1 arquivo (salvar)
        "directory"    — 1 pasta
        "directories"  — múltiplas pastas

    Mode Selector (mode_selector):
        Dict com chaves para cada modo. Ex:
        {
            "file": {"label": "Arquivo", "description": "Processar 1 arquivo", "default": True},
            "folder": {"label": "Pasta", "description": "Processar pasta inteira"},
        }
        Quando informado, exibe GridRadio acima do campo e alterna browse_mode.

    Suporta suggested_path: str opcional. Se informado, um botão "📂" é
    adicionado ao lado do "..." que, ao ser clicado, busca o root_folder
    do projeto ativo e concatena com o path relativo recebido.

    Uso:
        sel = SimpleSelector("Imagem:", file_filter="GeoTIFF (*.tif *.tiff)",
                             browse_mode="open_file")
        sel.path()  # retorna o caminho atual
        layout.addWidget(sel)

        # Com mode_selector
        sel = SimpleSelector("Entrada:", mode_selector={
            "file": {"label": "Arquivo", "default": True},
            "folder": {"label": "Pasta"},
        })
        sel.mode  # "file" ou "folder"

        # Callbacks opcionais
        sel.on_path_change = self._quando_path_mudar
        sel.on_browse_click = self._quando_browse
        sel.on_suggest_click = self._quando_suggest
        sel.on_mode_change = self._quando_modo_mudar
    """

    def __init__(
        self,
        label_text: str = "",
        default_path: str = "",
        placeholder: str = "Caminho...",
        tooltip: str = "",
        file_filter: str = "Todos (*.*)",
        browse_mode: str = "open_file",
        label_width: int = 130,
        suggested_path: str = "",
        mode_selector: dict = None,
        parent=None,
    ):
        super().__init__(parent)

        self._file_filter = file_filter
        self._browse_mode = browse_mode
        self._suggested_rel_path: str = ""
        self._mode_selector_config = mode_selector
        self._mode: str = ""

        # Logger para rastreio
        self._logger = LogUtils(tool="SimpleSelector", class_name="SimpleSelector")

        # Callbacks públicos — plugin pode sobrescrever
        self.on_path_change = None    # callback(new_path)
        self.on_browse_click = None   # callback()
        self.on_suggest_click = None  # callback()
        self.on_mode_change = None    # callback(mode_key)

        # Layout principal (vertical se tem mode_selector)
        if mode_selector:
            self._build_with_mode(label_text, default_path, placeholder, tooltip, label_width)
        else:
            self._build_simple(label_text, default_path, placeholder, tooltip, label_width)

        # Mostra botão 📄 apenas nos modos open_file / open_files
        self._update_project_button_visibility()

    def _build_simple(self, label_text, default_path, placeholder, tooltip, label_width):
        """Constrói layout horizontal simples (sem mode_selector)."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._add_label(layout, label_text, tooltip, label_width)
        self._add_edit(layout, default_path, placeholder, tooltip)
        self._add_buttons(layout)

    def _build_with_mode(self, label_text, default_path, placeholder, tooltip, label_width):
        """Constrói layout vertical com GridRadio + linha horizontal."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── GridRadio ──
        self._radio = GridRadio(
            config=self._mode_selector_config,
            num_columns=len(self._mode_selector_config),
            parent=self,
        )
        layout.addWidget(self._radio)

        # Define modo inicial
        self._mode = self._radio.selected or ""
        self._radio.changed.connect(self._on_mode_changed)

        # ── Linha horizontal: label + edit + buttons ──
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        self._add_label(h_layout, label_text, tooltip, label_width)
        self._add_edit(h_layout, default_path, placeholder, tooltip)
        self._add_buttons(h_layout)

        layout.addLayout(h_layout)

        # Aplica modo inicial
        self._apply_mode(self._mode)

    def _add_label(self, layout, label_text, tooltip, label_width):
        """Adiciona label ao layout."""
        self.label = QLabel(label_text)
        self.label.setFixedWidth(label_width)
        if tooltip:
            self.label.setToolTip(tooltip)
        layout.addWidget(self.label)

    def _add_edit(self, layout, default_path, placeholder, tooltip):
        """Adiciona QLineEdit ao layout."""
        self.edit = QLineEdit(default_path)
        self.edit.setPlaceholderText(placeholder)
        if tooltip:
            self.edit.setToolTip(tooltip)
        layout.addWidget(self.edit, 1)
        self.edit.textChanged.connect(self._on_text_changed)

    def _add_buttons(self, layout):
        """Adiciona botões ... e 📂 ao layout."""
        # ── Botão "..." (selecionar) ──
        self.btn = SimpleSecondaryButton("...")
        self.btn.setFixedWidth(30)
        self.btn.setToolTip("Selecionar pasta manualmente")
        self.btn.clicked.connect(self._browse)
        layout.addWidget(self.btn)

        # ── Botão de Caminho Padrão (depois do "...") ──
        self._btn_suggest = SimpleSecondaryButton("📂")
        self._btn_suggest.setFixedWidth(30)
        self._btn_suggest.setVisible(False)
        self._btn_suggest.clicked.connect(self._on_suggest_clicked)
        self._btn_suggest.setToolTip("Usar pasta do projeto")
        layout.addWidget(self._btn_suggest)

        # ── Botão de Arquivos do Projeto (📄) ──
        self._btn_project = SimpleSecondaryButton("📄")
        self._btn_project.setFixedWidth(30)
        self._btn_project.setVisible(False)
        self._btn_project.clicked.connect(self._on_project_clicked)
        self._btn_project.setToolTip("Selecionar arquivo do projeto")
        layout.addWidget(self._btn_project)

    def _on_mode_changed(self, mode_key: str):
        """Callback quando o radio mode muda."""
        self._mode = mode_key
        self._apply_mode(mode_key)
        self._logger.info(
            f"Modo alterado para: {mode_key}",
            code="MODE_CHANGED",
        )
        if self.on_mode_change:
            self.on_mode_change(mode_key)

    def _update_project_button_visibility(self):
        """Mostra/esconde o botão 📄 conforme o browse_mode."""
        visible = self._browse_mode in ("open_file", "open_files")
        self._btn_project.setVisible(visible)

    def _apply_mode(self, mode_key: str):
        """Aplica configurações de browse_mode e placeholder conforme o modo."""
        if not self._mode_selector_config:
            return

        mode_cfg = self._mode_selector_config.get(mode_key, {})
        mode_type = mode_cfg.get("mode_type", "")

        if mode_type == "folder" or mode_key == "folder":
            # Modo pasta
            self._browse_mode = "directory"
            self.edit.setPlaceholderText("Selecione uma pasta...")
            self._file_filter = "Todos (*.*)"
        else:
            # Modo arquivo (default)
            self._browse_mode = "open_file"
            self.edit.setPlaceholderText("Selecione um arquivo...")

        self._update_project_button_visibility()

    # ── Handlers internos (log + callback externo) ─────────────────────

    def _on_text_changed(self, text: str):
        """Loga mudança de path e chama callback externo se existir."""
        self._logger.info(
            f"path alterado: \"{text[:100]}\"",
            code="PATH_CHANGED",
        )
        if self.on_path_change:
            self.on_path_change(text)

    # ── Lógica do seletor ─────────────────────────────────────────────

    def _browse(self):
        current = self.edit.text().strip()
        initial_dir = ExplorerUtils.resolve_initial_dir(current)

        self._logger.info("botão '...' clicado", code="BROWSE_CLICKED")
        if self.on_browse_click:
            self.on_browse_click()

        if self._browse_mode == "save_file":
            path = ExplorerUtils.save_file(
                "Salvar arquivo", initial_dir, self._file_filter, self,
            )
            if path:
                self.edit.setText(path)

        elif self._browse_mode == "open_files":
            paths = ExplorerUtils.open_files(
                "Selecionar arquivos", initial_dir, self._file_filter, self,
            )
            if paths:
                self.edit.setText("; ".join(paths))

        elif self._browse_mode == "directories":
            path = ExplorerUtils.select_directory(
                "Selecionar pasta", initial_dir, self,
            )
            if path:
                self.edit.setText(path)

        else:  # "directory" ou "open_file"
            if self._browse_mode == "directory":
                path = ExplorerUtils.select_directory(
                    "Selecionar pasta", initial_dir, self,
                )
            else:
                path = ExplorerUtils.open_file(
                    "Selecionar arquivo", initial_dir, self._file_filter, self,
                )
            if path:
                self.edit.setText(path)

    def _on_project_clicked(self):
        """
        Callback do botão 📄.
        Abre ListFileDialog com as extensões do filtro atual.
        Só funciona se houver um projeto ativo.
        """
        self._logger.info(
            "botão '📄' clicado",
            code="PROJECT_CLICKED",
        )

        # Verifica se há projeto ativo
        root_folder = ProjectUtil.get_root_folder()
        if not root_folder:
            self._logger.warning(
                "Nenhum projeto ativo — botão não fará nada",
                code="PROJECT_NO_PROJECT",
            )
            return

        # Extrai extensões do file_filter
        extensions = self._parse_extensions_from_filter(self._file_filter)
        if not extensions:
            self._logger.warning(
                "Nenhuma extensão extraída do filtro",
                code="PROJECT_NO_EXT",
                file_filter=self._file_filter,
            )
            return

        multi = self._browse_mode == "open_files"

        dialog = ListFileDialog(
            extensions=extensions,
            multi_select=multi,
            parent=self,
        )
        if dialog.exec():
            paths = dialog.selected_paths
            if paths:
                if multi:
                    self.edit.setText("; ".join(paths))
                else:
                    self.edit.setText(paths[0])

    @staticmethod
    def _parse_extensions_from_filter(file_filter: str) -> list[str]:
        """
        Extrai extensões de um filtro de arquivo no formato
        "Descrição (*.ext1 *.ext2)".
        Ex: "LAS/LAZ (*.las *.laz)" → [".las", ".laz"]
        """
        import re
        match = re.search(r'\(([^)]+)\)', file_filter)
        if not match:
            return []
        parts = match.group(1).split()
        exts = [p.strip().lower() for p in parts if p.startswith("*")]
        return [e.replace("*", "") for e in exts if e.replace("*", "")]

    def _on_suggest_clicked(self):
        """
        Callback do botão 📂.
        Busca o root_folder do projeto ativo e concatena com o path relativo.
        """
        self._logger.info(
            f"botão '📂' clicado. Path relativo: {self._suggested_rel_path}",
            code="SUGGEST_CLICKED",
        )
        if self.on_suggest_click:
            self.on_suggest_click()

        if not self._suggested_rel_path:
            self._logger.warning(
                "Path relativo vazio — botão não fará nada",
                code="SUGGEST_EMPTY",
            )
            return

        # Busca root_folder do projeto ativo
        root_folder = ProjectUtil.get_root_folder()
        self._logger.info(
            f"root_folder obtido: {root_folder}",
            code="SUGGEST_ROOT",
        )

        if not root_folder:
            self._logger.warning(
                "Nenhum projeto ativo (root_folder vazio)",
                code="SUGGEST_NO_PROJECT",
            )
            return

        # Concatena root_folder + path relativo
        full_path = os.path.join(root_folder, self._suggested_rel_path)
        self._logger.info(
            f"Caminho completo gerado: {full_path}",
            code="SUGGEST_PATH",
        )

        self.edit.setText(full_path)

    # ── Getters / Setters ─────────────────────────────────────────────

    @property
    def mode(self) -> str:
        """Retorna o modo atual ('file', 'folder', etc.) ou '' se não tem mode_selector."""
        return self._mode

    def set_mode(self, mode_key: str):
        """Define o modo programaticamente."""
        if self._mode_selector_config and mode_key in self._mode_selector_config:
            self._radio.set_selected(mode_key)

    def path(self) -> str:
        """Retorna o caminho atual (primeiro, se multi)."""
        text = self.edit.text().strip()
        if ";" in text:
            return text.split(";")[0].strip()
        return text

    def paths(self) -> list[str]:
        """Retorna lista de caminhos."""
        text = self.edit.text().strip()
        if not text:
            return []
        return [p.strip() for p in text.split(";")]

    def set_suggested_path(self, suggested_rel_path: str):
        """
        Define o path relativo para o botão 📂.

        O plugin DEVE passar um PATH RELATIVO (ex: "vetores/black_points_filter").
        Quando o botão for clicado, o SimpleSelector busca o root_folder
        do projeto ativo e concatena com este path relativo.

        Se suggested_rel_path for vazio, esconde o botão.
        Se for válido, mostra o botão e atualiza o tooltip.
        """
        self._logger.info(
            f"set_suggested_path chamado com: '{suggested_rel_path}'",
            code="SET_SUGGESTED",
        )

        if suggested_rel_path:
            self._suggested_rel_path = suggested_rel_path
            self._btn_suggest.setToolTip(
                f"Usar pasta do projeto: {suggested_rel_path}"
            )
            self._btn_suggest.setVisible(True)
            self._logger.info(
                f"Botão 📂 ativado com path relativo: {suggested_rel_path}",
                code="SUGGEST_ACTIVATED",
            )
        else:
            self._suggested_rel_path = ""
            self._btn_suggest.setVisible(False)
            self._logger.info(
                "Botão 📂 desativado (path vazio)",
                code="SUGGEST_DEACTIVATED",
            )

    def set_project_button_visible(self, visible: bool):
        """
        Controla a visibilidade do botão 📄 (arquivos do projeto).

        Args:
            visible: True para mostrar, False para esconder.
        """
        self._btn_project.setVisible(visible)
        self._logger.info(
            f"Botão 📄 visibilidade: {visible}",
            code="PROJECT_BTN_VISIBLE",
        )

    def set_suggested_callback(self, callback: Callable[[], None], tooltip: str = ""):
        """
        Permite que o plugin defina um callback personalizado para o botão 📂,
        em vez do comportamento padrão de buscar o projeto.

        Args:
            callback: Função sem argumentos a ser chamada quando o botão for clicado.
            tooltip: Tooltip opcional para o botão.
        """
        self._logger.info(
            "Callback personalizado registrado para botão 📂",
            code="SUGGEST_CALLBACK",
        )
        try:
            self._btn_suggest.clicked.disconnect()
        except TypeError:
            pass
        self._btn_suggest.clicked.connect(callback)
        if tooltip:
            self._btn_suggest.setToolTip(tooltip)
        self._btn_suggest.setVisible(True)

    @property
    def file_filter(self) -> str:
        """Filtro de arquivo atual."""
        return self._file_filter

    @file_filter.setter
    def file_filter(self, value: str) -> None:
        """Define o filtro e loga a mudança."""
        old = self._file_filter
        self._file_filter = value
        self._logger.info(
            f"file_filter alterado: '{value}'",
            code="FILE_FILTER_CHANGED",
        )

    @property
    def browse_mode(self) -> str:
        """Modo de seleção atual."""
        return self._browse_mode

    @browse_mode.setter
    def browse_mode(self, value: str) -> None:
        """Define o browse_mode e atualiza botão 📄."""
        old = self._browse_mode
        self._browse_mode = value
        if old != value:
            self._update_project_button_visibility()
            self._logger.info(
                f"browse_mode alterado: '{value}'",
                code="BROWSE_MODE_CHANGED",
            )

    def set_path(self, path: str):
        """Define o caminho do QLineEdit."""
        self._logger.info(
            f"set_path chamado: {path[:80]}...",
            code="SET_PATH",
        )
        self.edit.setText(path)

    def clear(self):
        """Limpa o QLineEdit."""
        self._logger.info("clear() chamado", code="CLEAR")
        self.edit.setText("")