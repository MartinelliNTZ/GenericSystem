# -*- coding: utf-8 -*-
"""
ProjectStructurePlugin — Gerenciador de Estrutura de Projetos
============================================================
Ferramenta CENTRAL que confere e padroniza a estrutura de pastas dos
projetos de uma pasta-mãe (migrada de org.py).

Recursos preservados:
- Descoberta de projetos (pastas com prefixo "OS_") e ordenação por nome.
- Indicadores de pastas corretas, incoerentes e ausentes.
- Estatísticas assíncronas (arquivos, subpastas, tamanho).
- Filtro por nome de projeto.
- Atualização automática via QFileSystemWatcher (com debounce).
- Ações: abrir, criar pasta, renomear/padronizar e mesclar pastas.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QFileSystemWatcher, QThreadPool, QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from plugins.project_structure_manager import FolderOperations as FsOps
from plugins.project_structure_manager import ProjectStructureScanner as Scanner
from resources.styles.AppStyles import AppStyles
from resources.widgets.dialogs.CheckBoxSelectDialog import CheckBoxSelectDialog
from resources.widgets.grid.GridActionCell import GridActionCell
from resources.widgets.grid.GridCardView import GridCardView
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.grid.GridTree import GridTree
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleMenuButton import SimpleMenuButton
from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton
from resources.widgets.simple.SimpleSelector import SimpleSelector
from utils.MessageBox import MessageBox


def _status_color(status: str) -> str:
    """Retorna a cor de tema correspondente ao status de uma pasta."""
    theme = AppStyles.current_theme
    if status == Scanner.STATUS_CORRECT:
        return theme.COLOR_SUCCESS
    if status == Scanner.STATUS_INCORRECT:
        return theme.COLOR_DANGER
    return theme.COLOR_WARNING


class ProjectStructurePlugin(BasePlugin):
    """Ferramenta de conferência e padronização da estrutura de projetos."""

    _COL_NAME = 0
    _COL_STATUS = 1
    _COL_FILES = 2
    _COL_DIRS = 3
    _COL_SIZE = 4
    _COL_ACTIONS = 5

    def __init__(self, parent=None) -> None:
        super().__init__(
            tool_key=ToolKey.PROJECT_STRUCTURE.value,
            parent=parent,
            title="Gerenciador de Estrutura",
            buttons_config={
                "atualizar": {
                    "text": "ATUALIZAR",
                    "callback": self._on_refresh_clicked,
                    "type": "primary",
                    "description": "Recarrega a estrutura dos projetos",
                },
            },
        )
        self._init_runtime()
        self.logger.info("Ferramenta inicializada", code="PSM_READY")

    # ── Ciclo de vida / runtime ──────────────────────────────────────

    def _init_runtime(self) -> None:
        """Configura watcher, timer e thread pool (após UI e prefs)."""
        self._generation = 0
        self._operations_in_progress = 0
        self._ignore_watcher_until = 0.0
        self._workers: set = set()

        self._thread_pool = QThreadPool.globalInstance()
        self._thread_pool.setMaxThreadCount(4)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._schedule_auto_refresh)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(700)
        self._refresh_timer.timeout.connect(
            lambda: self._load_projects(show_toast=False)
        )

        self._runtime_ready = True
        QTimer.singleShot(0, lambda: self._load_projects(show_toast=False))

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Encerra workers e monitoramento antes de fechar."""
        self._refresh_timer.stop()
        try:
            watched = self._watcher.directories()
            if watched:
                self._watcher.removePaths(watched)
        except RuntimeError as e:
            self.logger.warning(
                "Falha ao finalizar monitoramento",
                code="PSM_CLOSE_ERR",
                error=str(e),
            )
        self._thread_pool.clear()
        super().closeEvent(event)

    def load_prefs(self) -> None:
        """Carrega a pasta-mãe salva (Contrato 4)."""
        saved = self.preferences.get("mother_folder", "")
        self._mother_folder: Optional[Path] = Path(saved) if saved else None
        if saved:
            self._selector.set_path(saved)

    def save_prefs(self) -> None:
        """Persiste a pasta-mãe atual."""
        self.preferences["mother_folder"] = (
            str(self._mother_folder) if self._mother_folder else ""
        )

    # ── UI ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        super()._build_ui()

        self._runtime_ready = False

        self._selector = SimpleSelector(
            "Pasta-mãe:",
            placeholder="Selecione a pasta-mãe dos projetos...",
            browse_mode="directory",
            tooltip="Pasta que contém as pastas de projeto (OS_...)",
        )
        self._selector.on_path_change = self._on_mother_changed
        grupo_origem = GroupPainel("Origem")
        grupo_origem.group_layout.addWidget(self._selector)

        self._filter = GridLineEdit({
            "busca": {
                "label": "Projeto:",
                "placeholder": "Digite parte do nome...",
            },
        })
        self._filter.changed.connect(self._on_filter_changed)
        grupo_pesquisa = GroupPainel("Pesquisa")
        grupo_pesquisa.group_layout.addWidget(self._filter)

        self.main_layout.addWidget(
            GridGroupPainel(grupo_origem, grupo_pesquisa)
        )
        self._build_cards()
        self._build_tree()
        self._build_legend()

    def _build_cards(self) -> None:
        """Cria os cards de resumo (projetos, corretas, incoerentes, ausentes)."""
        def card(text: str) -> Dict[str, Any]:
            return {"labels": [
                {"type": "great_accent", "text": "0"},
                {"type": "simple", "text": text},
            ]}

        self._cards = GridCardView({
            "items_per_row": 4,
            "cards": [
                card("Projetos"),
                card("Pastas corretas"),
                card("Incoerentes"),
                card("Ausentes"),
            ],
        })
        self.main_layout.addWidget(self._cards)

    def _build_tree(self) -> None:
        """Cria a árvore multicoluna de projetos e pastas."""
        self._tree = GridTree(columns=[
            {"header": "Projeto / Pasta", "stretch": True},
            {"header": "Status", "width": 120},
            {"header": "Arquivos", "width": 100},
            {"header": "Subpastas", "width": 100},
            {"header": "Tamanho", "width": 100},
            {"header": "Ações", "width": 300},
        ])
        self._tree.node_activated.connect(self._on_node_activated)
        self.main_layout.addWidget(self._tree, 1)

    def _build_legend(self) -> None:
        """Cria a legenda colorida de status."""
        theme = AppStyles.current_theme
        self._legend = GridLabel({
            "correct": {"label": "● Correta", "value": ""},
            "incorrect": {"label": "● Incoerente", "value": ""},
            "missing": {"label": "● Ausente", "value": ""},
        }, columns=3)
        colors = {
            "correct": theme.COLOR_SUCCESS,
            "incorrect": theme.COLOR_DANGER,
            "missing": theme.COLOR_WARNING,
        }
        for key, color in colors.items():
            self._legend.widget(key).setStyleSheet(
                f"color: {color}; font-family: Consolas, monospace; "
                f"font-size: 12px;"
            )
        self.main_layout.addWidget(self._legend)

    # ── Carregamento ─────────────────────────────────────────────────

    def _on_refresh_clicked(self) -> None:
        self._load_projects(show_toast=True)

    def _load_projects(self, show_toast: bool) -> None:
        """Recarrega a árvore a partir da pasta-mãe."""
        if not getattr(self, "_runtime_ready", False):
            return
        if self._mother_folder is None:
            self.page.set_badge(self.page.INFO)
            self._reset_tree_view()
            return

        if not self._mother_folder.exists():
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_warning(
                f"A pasta-mãe não existe:\n{self._mother_folder}",
                title="Pasta-mãe inexistente",
                parent=self,
            )
            self._reset_tree_view()
            return

        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("atualizar", False)
        state = self._capture_state()
        projects: List[Path] = []

        self._generation += 1
        try:
            self._thread_pool.clear()
        except RuntimeError as e:
            self.logger.warning(
                "Falha ao limpar fila de workers",
                code="PSM_POOL_CLEAR",
                error=str(e),
            )

        self._tree.setUpdatesEnabled(False)
        try:
            projects = Scanner.discover_projects(self._mother_folder)
            self._tree.clear_nodes()
            totals = {"correct": 0, "incorrect": 0, "missing": 0}
            for project in projects:
                self._render_project(project, totals)
            self._update_cards(len(projects), totals)
            self._restore_state(state)
            self._configure_watcher(projects)
        finally:
            self._tree.setUpdatesEnabled(True)
            self.page.buttons.set_enabled("atualizar", True)

        self.page.set_badge(self.page.PRONTA)
        if show_toast:
            MessageBox.show_toast(
                f"Estrutura atualizada: {len(projects)} projeto(s).",
                parent=self,
            )
        self.logger.info(
            f"Estrutura carregada: {len(projects)} projeto(s)",
            code="PSM_LOADED",
        )

    def _reset_tree_view(self) -> None:
        """Limpa árvore e cards (usado quando não há pasta-mãe válida)."""
        self._tree.clear_nodes()
        self._update_cards(0, {"correct": 0, "incorrect": 0, "missing": 0})

    def _render_project(self, project: Path, totals: Dict[str, int]) -> None:
        """Cria o nó do projeto, suas pastas e agenda as estatísticas."""
        theme = AppStyles.current_theme
        key = str(project)
        self._tree.add_node(
            key,
            {
                self._COL_NAME: project.name,
                self._COL_STATUS: "PROJETO",
                self._COL_FILES: "...",
                self._COL_DIRS: "...",
                self._COL_SIZE: "...",
            },
            colors={
                self._COL_NAME: theme.ACCENT_BRIGHT,
                self._COL_STATUS: theme.ACCENT,
            },
            bold=True,
            kind="project",
        )
        self._tree.set_cell_widget(
            key, self._COL_ACTIONS, self._build_project_actions(project)
        )
        self._request_statistics(key, project)

        structure = Scanner.scan_project(project, Scanner.DEFAULT_PROJECT_FOLDERS)
        for folder in structure.folders:
            self._render_folder(project, folder, totals)

    def _render_folder(
        self, project: Path, folder: Scanner.FolderStatus, totals: Dict[str, int]
    ) -> None:
        """Cria o nó de uma pasta (correta, incoerente ou ausente)."""
        key = str(folder.path)
        color = _status_color(folder.status)
        missing = folder.status == Scanner.STATUS_MISSING
        self._count_status(folder.status, totals)
        texts = {
            self._COL_NAME: folder.name,
            self._COL_STATUS: folder.status,
            self._COL_FILES: "—" if missing else "...",
            self._COL_DIRS: "—" if missing else "...",
            self._COL_SIZE: "—" if missing else "...",
        }
        self._tree.add_node(
            key,
            texts,
            parent_key=str(project),
            colors={self._COL_NAME: color, self._COL_STATUS: color},
            kind="folder",
        )
        if missing:
            self._tree.set_cell_widget(
                key,
                self._COL_ACTIONS,
                self._build_missing_actions(project, folder.name),
            )
            return
        self._tree.set_cell_widget(
            key,
            self._COL_ACTIONS,
            self._build_folder_actions(folder.path, folder.name),
        )
        self._request_statistics(key, folder.path)
        if folder.name == Scanner.DOCUMENT_YEARS_FOLDER:
            self._render_document_years(folder.path, key, totals)

    def _render_document_years(
        self, envio: Path, parent_key: str, totals: Dict[str, int]
    ) -> None:
        """Renderiza as pastas de ano (e seu template) dentro do 03."""
        expected = [str(year) for year in Scanner.DEFAULT_YEARS]
        for node in Scanner.scan_document_years(envio):
            self._render_structure_node(node, parent_key, totals, expected, True)

    def _render_structure_node(
        self,
        node: Scanner.StructureNode,
        parent_key: str,
        totals: Dict[str, int],
        expected: List[str],
        is_year: bool = False,
    ) -> None:
        """Renderiza recursivamente um nó estrutural (ano ou pasta do template)."""
        key = str(node.path)
        color = _status_color(node.status)
        missing = node.status == Scanner.STATUS_MISSING
        self._count_status(node.status, totals)
        pending = "..." if (is_year and not missing) else "—"
        texts = {
            self._COL_NAME: node.name,
            self._COL_STATUS: node.status,
            self._COL_FILES: pending,
            self._COL_DIRS: pending,
            self._COL_SIZE: pending,
        }
        self._tree.add_node(
            key,
            texts,
            parent_key=parent_key,
            colors={self._COL_NAME: color, self._COL_STATUS: color},
            kind="folder",
        )
        if missing:
            self._tree.set_cell_widget(
                key,
                self._COL_ACTIONS,
                self._build_structure_missing_actions(node),
            )
            return
        self._tree.set_cell_widget(
            key,
            self._COL_ACTIONS,
            self._build_structure_actions(node.path, expected),
        )
        if is_year:
            self._request_statistics(key, node.path)
        child_expected = list(node.subtree.keys()) if node.subtree else []
        for child in node.children:
            self._render_structure_node(child, key, totals, child_expected, False)

    @staticmethod
    def _count_status(status: str, totals: Dict[str, int]) -> None:
        """Acumula a contagem de um status nos totais dos cards."""
        if status == Scanner.STATUS_CORRECT:
            totals["correct"] += 1
        elif status == Scanner.STATUS_INCORRECT:
            totals["incorrect"] += 1
        else:
            totals["missing"] += 1

    # ── Estatísticas ─────────────────────────────────────────────────

    def _request_statistics(self, key: str, path: Path) -> None:
        """Agenda o cálculo de estatísticas de um nó em background."""
        worker = Scanner.StatisticsWorker(self._generation, str(path))
        self._workers.add(worker)
        worker.signals.finished.connect(self._on_statistics_finished)
        worker.signals.finished.connect(lambda *_: self._workers.discard(worker))
        self._thread_pool.start(worker)

    def _on_statistics_finished(
        self,
        generation: int,
        path: str,
        n_files: int,
        n_dirs: int,
        size: int,
    ) -> None:
        """Aplica o resultado das estatísticas (ignora gerações antigas)."""
        if generation != self._generation or not self._tree.has_node(path):
            return
        self._tree.set_cell_text(
            path, self._COL_FILES, Scanner.format_count(n_files)
        )
        self._tree.set_cell_text(
            path, self._COL_DIRS, Scanner.format_count(n_dirs)
        )
        self._tree.set_cell_text(path, self._COL_SIZE, Scanner.format_size(size))

    def _update_cards(self, n_projects: int, totals: Dict[str, int]) -> None:
        """Atualiza os cards de resumo."""
        self._cards.set_card_value(0, 0, str(n_projects))
        self._cards.set_card_value(1, 0, str(totals["correct"]))
        self._cards.set_card_value(2, 0, str(totals["incorrect"]))
        self._cards.set_card_value(3, 0, str(totals["missing"]))

    # ── Estado / filtro / watcher ────────────────────────────────────

    def _capture_state(self) -> Dict[str, Any]:
        """Captura os projetos expandidos antes de recarregar."""
        expanded: List[str] = [
            key for key in self._tree.keys()
            if self._tree.node_kind(key) == "project"
            and self._tree.is_node_expanded(key)
        ]
        return {"expanded": expanded}

    def _restore_state(self, state: Dict[str, Any]) -> None:
        """Restaura os projetos expandidos."""
        for key in state.get("expanded", []):
            self._tree.set_node_expanded(key, True)

    def _on_filter_changed(self, _key: str, text: str) -> None:
        """Filtra os projetos pelo nome digitado."""
        needle = (text or "").strip().lower()
        for key in self._tree.keys():
            if self._tree.node_kind(key) != "project":
                continue
            item = self._tree.node(key)
            if item is None:
                continue
            match = (not needle) or (needle in item.text(self._COL_NAME).lower())
            self._tree.set_node_hidden(key, not match)
            if needle and match:
                self._tree.set_node_expanded(key, True)

    def _on_mother_changed(self, path: str) -> None:
        """Reage à troca da pasta-mãe no selector."""
        if not path:
            self._mother_folder = None
            return
        self._mother_folder = Path(path)
        if not getattr(self, "_runtime_ready", False):
            return
        self.save_prefs()
        self._load_projects(show_toast=False)

    def _configure_watcher(self, projects: List[Path]) -> None:
        """Monitora a pasta-mãe e cada projeto, sem acumular watches."""
        try:
            current = self._watcher.directories()
            if current:
                self._watcher.removePaths(current)
            paths: List[str] = []
            if self._mother_folder and self._mother_folder.exists():
                paths.append(str(self._mother_folder))
            for project in projects:
                if not project.exists():
                    continue
                paths.append(str(project))
                envio = project / Scanner.DOCUMENT_YEARS_FOLDER
                if envio.exists():
                    paths.append(str(envio))
            if paths:
                self._watcher.addPaths(paths)
        except Exception as e:
            self.logger.warning(
                "Falha ao configurar monitoramento",
                code="PSM_WATCH_ERR",
                error=str(e),
            )

    def _schedule_auto_refresh(self, _path: str = "") -> None:
        """Agenda atualização automática com debounce."""
        if self._operations_in_progress > 0:
            return
        if time.monotonic() < self._ignore_watcher_until:
            return
        self._refresh_timer.start()

    def _suspend_watcher(self, seconds: float = 1.5) -> None:
        """Suspende o watcher temporariamente durante operações locais."""
        self._ignore_watcher_until = max(
            self._ignore_watcher_until, time.monotonic() + seconds
        )
        self._refresh_timer.stop()

    # ── Ações (células) ──────────────────────────────────────────────

    def _build_project_actions(self, project: Path) -> GridActionCell:
        """Célula de ações de um projeto: Abrir + Adicionar pasta."""
        btn_open = SimpleSecondaryButton("Abrir")
        btn_open.clicked.connect(lambda _=False: FsOps.open_in_explorer(project))
        menu = SimpleMenuButton(
            {name: name for name in Scanner.DEFAULT_PROJECT_FOLDERS},
            text="+ Adicionar pasta",
        )
        menu.item_selected.connect(
            lambda name, proj=project: self._create_folder(proj, name)
        )
        return GridActionCell(btn_open, menu)

    def _build_folder_actions(
        self, folder_path: Path, folder_name: str = ""
    ) -> GridActionCell:
        """Célula de ações de uma pasta existente.

        No 03_ENVIO_DE_DOCUMENTOS troca o "Padronizar" por "+ Anos".
        """
        btn_open = SimpleSecondaryButton("Abrir")
        btn_open.clicked.connect(
            lambda _=False: FsOps.open_in_explorer(folder_path)
        )
        if folder_name == Scanner.DOCUMENT_YEARS_FOLDER:
            btn_years = SimpleSecondaryButton("+ Anos")
            btn_years.clicked.connect(
                lambda _=False, path=folder_path: self._on_add_years(path)
            )
            return GridActionCell(btn_open, btn_years)
        menu = SimpleMenuButton(
            {name: name for name in Scanner.DEFAULT_PROJECT_FOLDERS},
            text="Padronizar",
        )
        menu.item_selected.connect(
            lambda name, origin=folder_path: self._rename_folder(origin, name)
        )
        return GridActionCell(btn_open, menu)

    def _build_structure_actions(
        self, folder_path: Path, expected: List[str]
    ) -> GridActionCell:
        """Célula de ações de um nó estrutural existente: Abrir (+ Padronizar)."""
        btn_open = SimpleSecondaryButton("Abrir")
        btn_open.clicked.connect(
            lambda _=False: FsOps.open_in_explorer(folder_path)
        )
        if not expected:
            return GridActionCell(btn_open)
        menu = SimpleMenuButton(
            {name: name for name in expected}, text="Padronizar"
        )
        menu.item_selected.connect(
            lambda name, origin=folder_path: self._rename_folder(origin, name)
        )
        return GridActionCell(btn_open, menu)

    def _build_structure_missing_actions(
        self, node: Scanner.StructureNode
    ) -> GridActionCell:
        """Célula de ações de um nó estrutural ausente: cria a subárvore."""
        btn = SimpleSecondaryButton("+ Criar")
        btn.clicked.connect(lambda _=False, n=node: self._create_structure(n))
        return GridActionCell(btn)

    def _build_missing_actions(self, project: Path, name: str) -> GridActionCell:
        """Célula de ações de uma pasta ausente: Criar."""
        btn = SimpleSecondaryButton("+ Criar")
        btn.clicked.connect(
            lambda _=False, proj=project, folder=name:
            self._create_folder(proj, folder)
        )
        return GridActionCell(btn)

    # ── Operações ────────────────────────────────────────────────────

    def _create_folder(self, project: Path, name: str) -> None:
        """Cria uma pasta padrão dentro de um projeto."""
        destination = project / name
        if destination.exists():
            MessageBox.show_toast(f"{name} já existe.", parent=self)
            return
        try:
            FsOps.create_folder(project, name)
        except Exception as e:
            self.logger.error(
                "Falha ao criar pasta",
                code="PSM_CREATE_ERR",
                error=str(e),
                path=str(destination),
            )
            MessageBox.show_toast(
                f"Erro ao criar pasta: {e}", is_error=True, parent=self
            )
            return
        SignalManager.instance().console_message.emit(f"Pasta criada: {name}")
        MessageBox.show_toast(f"Pasta criada: {name}", parent=self)
        self._suspend_watcher(0.8)
        self._load_projects(show_toast=False)

    def _create_structure(self, node: Scanner.StructureNode) -> None:
        """Cria a pasta ausente e todo o template abaixo dela."""
        try:
            FsOps.create_template(node.path, node.subtree or {})
        except Exception as e:
            self.logger.error(
                "Falha ao criar estrutura",
                code="PSM_CREATE_STRUCT_ERR",
                error=str(e),
                path=str(node.path),
            )
            MessageBox.show_toast(
                f"Erro ao criar estrutura: {e}", is_error=True, parent=self
            )
            return
        SignalManager.instance().console_message.emit(
            f"Estrutura criada: {node.name}"
        )
        MessageBox.show_toast(f"Estrutura criada: {node.name}", parent=self)
        self._suspend_watcher(0.8)
        self._load_projects(show_toast=False)

    def _on_add_years(self, envio_path: Path) -> None:
        """Abre o diálogo de seleção de anos para o 03_ENVIO_DE_DOCUMENTOS."""
        config = {
            str(year): {"label": str(year), "default": False}
            for year in Scanner.DEFAULT_YEARS
        }
        dialog = CheckBoxSelectDialog(
            config,
            title="Pastas de ano — 03_ENVIO_DE_DOCUMENTOS",
            num_columns=3,
            parent=self,
        )
        if not dialog.exec():
            return
        years = sorted(dialog.selected_keys)
        if years:
            self._create_years(envio_path, years)

    def _create_years(self, envio_path: Path, years: List[str]) -> None:
        """Cria as pastas de ano selecionadas com o template completo."""
        created = 0
        for year in years:
            try:
                FsOps.create_document_year(envio_path, int(year))
                created += 1
            except (ValueError, OSError) as e:
                self.logger.error(
                    "Falha ao criar pasta de ano",
                    code="PSM_CREATE_YEAR_ERR",
                    error=str(e),
                    year=year,
                    path=str(envio_path),
                )
                MessageBox.show_toast(
                    f"Erro ao criar {year}: {e}", is_error=True, parent=self
                )
        if created:
            SignalManager.instance().console_message.emit(
                f"Pastas de ano criadas: {created}"
            )
            MessageBox.show_toast(
                f"{created} pasta(s) de ano criada(s).", parent=self
            )
        self._suspend_watcher(1.0)
        self._load_projects(show_toast=False)

    def _rename_folder(self, origin: Path, new_name: str) -> None:
        """Renomeia (padroniza) uma pasta, mesclando se o destino existir."""
        if not origin.exists():
            MessageBox.show_toast(
                "A pasta não existe mais.", is_error=True, parent=self
            )
            return
        if origin.name == new_name:
            MessageBox.show_toast("A pasta já possui esse nome.", parent=self)
            return
        destination = origin.parent / new_name
        if not destination.exists():
            self._start_rename_worker(origin, new_name)
            return
        answer = MessageBox.show_question(
            f"A pasta:\n\n{new_name}\n\njá existe.\n\n"
            "Deseja mesclar o conteúdo?",
            title="Pasta já existente",
            parent=self,
            buttons=MessageBox.YES_NO,
            default_button=MessageBox.NO,
        )
        if answer == MessageBox.YES:
            self._merge_folders(origin, destination)

    def _start_rename_worker(self, origin: Path, new_name: str) -> None:
        """Executa a renomeação em background."""
        self._suspend_watcher(2.0)
        self._operations_in_progress += 1
        worker = FsOps.RenameFolderWorker(origin, new_name)
        self._workers.add(worker)

        def finish() -> None:
            self._operations_in_progress = max(
                0, self._operations_in_progress - 1
            )
            self._workers.discard(worker)

        def on_success(_op: str, _src: str, dst: str) -> None:
            finish()
            self._suspend_watcher(1.0)
            MessageBox.show_toast(f"Renomeada para {Path(dst).name}", parent=self)
            SignalManager.instance().console_message.emit(
                f"Pasta renomeada: {Path(dst).name}"
            )
            self._load_projects(show_toast=False)

        def on_error(_op: str, message: str) -> None:
            finish()
            self._suspend_watcher(0.8)
            MessageBox.show_toast(
                f"Erro ao renomear: {message}", is_error=True, parent=self
            )
            self._load_projects(show_toast=False)

        worker.signals.success.connect(on_success)
        worker.signals.error.connect(on_error)
        self._thread_pool.start(worker)

    def _merge_folders(self, source: Path, destination: Path) -> None:
        """Mescla duas pastas e reporta o resultado."""
        self._suspend_watcher(2.0)
        self._operations_in_progress += 1
        try:
            conflicts = FsOps.merge_folders(source, destination)
        except Exception as e:
            self.logger.error(
                "Falha na mesclagem", code="PSM_MERGE_UI_ERR", error=str(e)
            )
            MessageBox.show_toast(
                f"Erro na mesclagem: {e}", is_error=True, parent=self
            )
            return
        finally:
            self._operations_in_progress = max(
                0, self._operations_in_progress - 1
            )
        if conflicts:
            MessageBox.show_toast(
                f"Mesclado com {len(conflicts)} conflito(s).", parent=self
            )
        else:
            MessageBox.show_toast("Pastas mescladas com sucesso.", parent=self)
        SignalManager.instance().console_message.emit("Pastas mescladas")
        self._load_projects(show_toast=False)

    def _on_node_activated(self, key: str) -> None:
        """Abre no explorer o caminho do nó com duplo clique."""
        path = Path(key)
        if path.exists():
            FsOps.open_in_explorer(path)
