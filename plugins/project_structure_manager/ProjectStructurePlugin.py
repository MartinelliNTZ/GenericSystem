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
- Navegação de arquivos: subpastas e arquivos reais são carregados sob
  demanda ao expandir um nó, com abertura no programa padrão (duplo clique).

Performance (assíncrono + refresh incremental):
- A varredura COMPLETA roda em thread secundária apenas 1 vez (abrir/ATUALIZAR).
- Depois, só o projeto afetado é re-escaneado quando o usuário o abre, mexe nas
  pastas ou o watcher reporta mudança (nunca recarrega a árvore inteira).
- A árvore é montada em lotes (QTimer), mantendo a UI responsiva.
- Progresso exibido SOMENTE na ProgressBar central (sem HUD/overlay).
- Operações de pasta rodam em worker; menus de ação são criados sob demanda.
"""

from __future__ import annotations

import os
import time
from collections import deque
from functools import partial
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QFileSystemWatcher, QThreadPool, QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from plugins.project_structure_manager import FolderOperations as FsOps
from plugins.project_structure_manager import ProjectStructureScanner as Scanner
from resources.IconManager import IconManager
from resources.styles.AppStyles import AppStyles
from resources.widgets.dialogs.CheckBoxSelectDialog import CheckBoxSelectDialog
from resources.widgets.grid.GridActionCell import GridActionCell
from resources.widgets.grid.GridCardView import GridCardView
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.grid.GridTree import GridTree
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleMenuButton import SimpleMenuButton
from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton
from resources.widgets.simple.SimpleSelector import SimpleSelector
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProjectDatabaseBackup import ProjectDatabaseBackup


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

    # Faixa de progresso reservada à varredura (o restante vai para o render).
    _SCAN_WEIGHT = 40.0
    # Número de nós renderizados por lote (mantém a UI responsiva).
    _RENDER_BATCH = 60
    # Intervalo entre lotes (0 = volta ao loop de eventos imediatamente).
    _RENDER_DELAY_MS = 0
    # Tempo (ms) que o 100% fica visível antes de resetar a barra.
    _PROGRESS_RESET_MS = 800
    # Intervalo mínimo (s) entre refreshes automáticos de um projeto ao abrir.
    _EXPAND_REFRESH_INTERVAL = 5.0

    def __init__(self, parent=None) -> None:
        super().__init__(
            tool_key=ToolKey.PROJECT_STRUCTURE.value,
            parent=parent,
            title="Gerenciador de Estrutura",
            buttons_config={
                "abrir_abas": {
                    "text": "ABRIR ABAS",
                    "callback": self._on_expand_all,
                    "type": "secondary",
                    "description": "Abre todas as pastas (abas) da árvore",
                },
                "fechar_abas": {
                    "text": "FECHAR ABAS",
                    "callback": self._on_collapse_all,
                    "type": "secondary",
                    "description": "Fecha todas as pastas (abas) da árvore",
                },
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
        """Configura watcher, timers e pools de trabalho (após UI e prefs)."""
        self._generation = 0
        self._operations_in_progress = 0
        self._ignore_watcher_until = 0.0
        self._workers: set = set()

        # Pools dedicados — não competem com o pool global de outros plugins.
        self._scan_pool = QThreadPool(self)
        self._scan_pool.setMaxThreadCount(1)
        self._work_pool = QThreadPool(self)
        self._work_pool.setMaxThreadCount(4)

        # Estado do carregamento incremental.
        self._loading = False
        self._reload_pending = False
        self._pending_toast = False
        self._show_progress = True
        self._progress_message = ""
        self._render_queue: Deque[Callable[[], None]] = deque()
        self._render_total = 0
        self._render_done = 0
        self._project_counts: Dict[str, Dict[str, int]] = {}
        self._load_state: Dict[str, Any] = {}
        self._load_projects_list: List[Path] = []
        self._filter_text = ""
        self._scan_worker: Optional[Scanner.ScanWorker] = None

        # Refresh incremental por projeto.
        self._pending_changes: Set[str] = set()
        self._refreshing: Set[str] = set()
        self._refresh_pending: Set[str] = set()
        self._refreshed_at: Dict[str, float] = {}

        # Conteúdo real (subpastas + arquivos) carregado sob demanda por nó.
        self._contents_loaded: Set[str] = set()
        self._content_queue: Deque[Tuple[str, Path, bool, int]] = deque()

        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._schedule_auto_refresh)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(700)
        self._refresh_timer.timeout.connect(self._on_refresh_timeout)

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._render_batch)

        self._content_timer = QTimer(self)
        self._content_timer.setSingleShot(True)
        self._content_timer.timeout.connect(self._render_content_batch)

        self._runtime_ready = True
        QTimer.singleShot(0, lambda: self._load_projects(show_toast=False))
        QTimer.singleShot(0, self._maybe_backup)

    def _maybe_backup(self) -> None:
        """Dispara o backup diário do banco ao iniciar (compartilhado)."""
        if self._mother_folder is None:
            return
        prefs = Preferences.load_tool_prefs(
            ToolKey.PROJECT_DATABASE,
            caller_tool_key=ToolKey.PROJECT_STRUCTURE.value,
        )
        ProjectDatabaseBackup.ensure_daily_backup(
            mother_folder=str(self._mother_folder),
            backup_dir=prefs.get("backup_dir", ""),
            label="BancoDados",
            tool_key=ToolKey.PROJECT_STRUCTURE.value,
        )

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Encerra workers e monitoramento antes de fechar."""
        self._refresh_timer.stop()
        self._render_timer.stop()
        self._content_timer.stop()
        self._render_queue.clear()
        self._content_queue.clear()
        if self._scan_worker is not None:
            self._scan_worker.cancel()
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
        self._work_pool.clear()
        self._scan_pool.clear()
        super().closeEvent(event)

    def load_prefs(self) -> None:
        """Carrega a pasta-mãe e as preferências de exibição (Contrato 4)."""
        saved = self.preferences.get("mother_folder", "")
        self._mother_folder: Optional[Path] = Path(saved) if saved else None
        if saved:
            self._selector.set_path(saved)
        self._show_icons = bool(self.preferences.get("show_icons", True))
        if not self._show_icons:
            self._icons_cb.blockSignals(True)
            self._icons_cb.set_checked("icons", False)
            self._icons_cb.blockSignals(False)

    def save_prefs(self) -> None:
        """Persiste a pasta-mãe e a preferência de exibição de ícones."""
        self.preferences["mother_folder"] = (
            str(self._mother_folder) if self._mother_folder else ""
        )
        self.preferences["show_icons"] = self._show_icons

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

        self._icons_cb = GridCheckBox({
            "icons": {
                "label": "Ícones do sistema",
                "description": "Exibe os ícones nativos do Windows em arquivos e pastas",
                "default": True,
            },
        }, num_columns=1)
        self._icons_cb.changed.connect(self._on_icons_toggled)
        grupo_exibicao = GroupPainel("Exibição")
        grupo_exibicao.group_layout.addWidget(self._icons_cb)

        self.main_layout.addWidget(
            GridGroupPainel(grupo_origem, grupo_pesquisa, grupo_exibicao)
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
        self._tree.node_expanded.connect(self._on_node_expanded)
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

    def _on_expand_all(self) -> None:
        """Abre todas as pastas (abas) da árvore."""
        self._tree.expand_all()

    def _on_collapse_all(self) -> None:
        """Fecha todas as pastas (abas) da árvore."""
        self._tree.collapse_all()

    def _load_projects(
        self, show_toast: bool, show_progress: bool = True
    ) -> None:
        """Recarrega TUDO a partir da pasta-mãe (assíncrono).

        Usado na primeira carga, na troca da pasta-mãe e no botão ATUALIZAR.
        Mudanças do watcher usam refresh incremental por projeto
        (``_refresh_project``). Se já houver carga em andamento, apenas marca
        como pendente (coalescência).
        """
        if not getattr(self, "_runtime_ready", False):
            return

        if self._loading:
            self._reload_pending = True
            self._pending_toast = self._pending_toast or show_toast
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

        self._start_load(show_toast, show_progress)

    def _start_load(self, show_toast: bool, show_progress: bool) -> None:
        """Inicia a varredura completa (fase 1) em background."""
        self._loading = True
        self._reload_pending = False
        self._pending_toast = show_toast
        self._show_progress = show_progress
        self._generation += 1
        self._load_state = self._capture_state()
        self._project_counts = {}
        self._refreshed_at = {}
        self._load_projects_list = []
        self._render_queue.clear()
        self._render_timer.stop()
        self._contents_loaded.clear()
        self._content_queue.clear()
        self._content_timer.stop()
        self._render_total = 0
        self._render_done = 0

        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("atualizar", False)
        self._tree.clear_nodes()

        self._progress_message = "Lendo a pasta-mãe..."
        if show_progress:
            SignalManager.instance().console_message.emit(
                "Lendo estrutura dos projetos..."
            )
            self._set_progress(0.0)

        self._scan_worker = Scanner.ScanWorker(
            self._generation, str(self._mother_folder)
        )
        self._scan_worker.signals.progress.connect(self._on_scan_progress)
        self._scan_worker.signals.finished.connect(self._on_scan_finished)
        self._scan_worker.signals.failed.connect(self._on_scan_failed)
        self._scan_pool.start(self._scan_worker)

    def _on_scan_progress(self, generation: int, done: int, total: int) -> None:
        """Atualiza o progresso da fase de varredura (0→40%)."""
        if generation != self._generation:
            return
        self._set_progress(self._SCAN_WEIGHT * done / max(total, 1))

    def _on_scan_finished(self, generation: int, result: Scanner.ScanResult) -> None:
        """Recebe o resultado da varredura e agenda o render incremental."""
        if generation != self._generation:
            return
        self._build_render_queue(result)
        self._render_total = len(self._render_queue)
        self._render_done = 0
        if not self._render_queue:
            self._finish_load()
            return
        self._progress_message = "Montando a árvore de projetos..."
        self._render_timer.start(self._RENDER_DELAY_MS)

    def _on_scan_failed(self, generation: int, message: str) -> None:
        """Trata falha da varredura em background."""
        if generation != self._generation:
            return
        self.logger.error(
            "Falha ao varrer a pasta-mãe",
            code="PSM_SCAN_WORKER_ERR",
            error=message,
        )
        MessageBox.show_toast(
            f"Erro ao ler a pasta-mãe: {message}", is_error=True, parent=self
        )
        self._finish_load(success=False)

    def _build_render_queue(self, result: Scanner.ScanResult) -> None:
        """Monta a fila de render (pai antes de filho) a partir da varredura."""
        expected_years = [str(year) for year in Scanner.DEFAULT_YEARS]
        for structure in result.projects:
            key = str(structure.path)
            self._load_projects_list.append(structure.path)
            proj_years = self._project_years(structure, result.years)
            self._register_project_counts(key, structure, proj_years)
            self._render_queue.append(partial(self._render_project, structure))
            self._append_project_children(
                structure, result.years, expected_years
            )

    @staticmethod
    def _project_years(
        structure: Scanner.ProjectStructure,
        years: Dict[str, List[Scanner.StructureNode]],
    ) -> Dict[str, List[Scanner.StructureNode]]:
        """Retorna apenas as pastas de ano pertencentes ao projeto."""
        subset: Dict[str, List[Scanner.StructureNode]] = {}
        for folder in structure.folders:
            if folder.name != Scanner.DOCUMENT_YEARS_FOLDER or not folder.path:
                continue
            node_key = str(folder.path)
            if node_key in years:
                subset[node_key] = years[node_key]
        return subset

    def _append_project_children(
        self,
        structure: Scanner.ProjectStructure,
        years: Dict[str, List[Scanner.StructureNode]],
        expected_years: List[str],
    ) -> None:
        """Enfileira as pastas do projeto e a subárvore das pastas de ano."""
        for folder in structure.folders:
            self._render_queue.append(
                partial(self._render_folder, structure.path, folder)
            )
            if folder.name != Scanner.DOCUMENT_YEARS_FOLDER:
                continue
            key = str(folder.path) if folder.path else ""
            for node in years.get(key, []):
                self._queue_structure(node, key, expected_years, True)

    def _register_project_counts(
        self,
        key: str,
        structure: Scanner.ProjectStructure,
        years: Dict[str, List[Scanner.StructureNode]],
    ) -> None:
        """Guarda a contagem de status de um projeto (para os cards)."""
        self._project_counts[key] = Scanner.project_status_counts(
            structure, years
        )

    def _queue_structure(
        self,
        node: Scanner.StructureNode,
        parent_key: str,
        expected: List[str],
        is_year: bool,
    ) -> None:
        """Enfileira um nó estrutural e, recursivamente, seus filhos."""
        self._render_queue.append(
            partial(
                self._render_structure_node, node, parent_key, expected, is_year
            )
        )
        if not node.children:
            return
        child_expected = list(node.subtree.keys()) if node.subtree else []
        for child in node.children:
            self._queue_structure(child, str(node.path), child_expected, False)

    def _render_batch(self) -> None:
        """Renderiza um lote de nós (fase 2), mantendo a UI responsiva."""
        if not self._loading:
            return
        self._render_queue_batch()
        if self._render_queue:
            self._update_render_progress()
            self._render_timer.start(self._RENDER_DELAY_MS)
            return
        self._finish_load()

    def _render_queue_batch(self) -> None:
        """Consome até ``_RENDER_BATCH`` itens da fila de render."""
        self._tree.setUpdatesEnabled(False)
        try:
            processed = 0
            while self._render_queue and processed < self._RENDER_BATCH:
                self._render_queue.popleft()()
                processed += 1
                self._render_done += 1
        finally:
            self._tree.setUpdatesEnabled(True)

    def _update_render_progress(self) -> None:
        """Progresso da fase de render (40→99%)."""
        span = 99.0 - self._SCAN_WEIGHT
        pct = self._SCAN_WEIGHT + span * self._render_done / max(
            self._render_total, 1
        )
        self._set_progress(pct)

    def _finish_load(self, success: bool = True) -> None:
        """Finaliza o carregamento: restaura estado, watcher, cards e sinais."""
        self._render_timer.stop()
        self._render_queue.clear()

        if success:
            now = time.monotonic()
            for project in self._load_projects_list:
                self._refreshed_at[str(project)] = now
            self._restore_state(self._load_state)
            self._apply_current_filter()
            self._update_cards()
            self._configure_watcher(self._load_projects_list)
            self.page.set_badge(self.page.PRONTA)
            self.logger.info(
                f"Estrutura carregada: {len(self._load_projects_list)} projeto(s)",
                code="PSM_LOADED",
            )
        else:
            self.page.set_badge(self.page.ERROR)

        self.page.buttons.set_enabled("atualizar", True)
        self._finish_progress(success)

        if success and self._pending_toast:
            MessageBox.show_toast(
                f"Estrutura atualizada: {len(self._load_projects_list)} projeto(s).",
                parent=self,
            )
        self._pending_toast = False
        self._loading = False

        if self._reload_pending:
            self._reload_pending = False
            self._load_projects(show_toast=False, show_progress=False)
        elif success:
            self._load_contents_for_expanded()

    def _finish_progress(self, success: bool) -> None:
        """Mostra 100% e reseta a barra (só quando há progresso visível)."""
        if not self._show_progress:
            return
        signals = SignalManager.instance()
        if not success:
            signals.progress_reset.emit()
            return
        signals.progress_update.emit(100.0)
        QTimer.singleShot(self._PROGRESS_RESET_MS, signals.progress_reset.emit)

    def _set_progress(self, pct: float) -> None:
        """Propaga o progresso para a ProgressBar central (Contrato 20)."""
        if not self._show_progress:
            return
        pct = max(0.0, min(100.0, pct))
        SignalManager.instance().progress_update.emit(pct)

    def _apply_current_filter(self) -> None:
        """Reaplica o filtro atual após o render incremental."""
        if self._filter_text:
            self._on_filter_changed("busca", self._filter_text)

    def _reset_tree_view(self) -> None:
        """Limpa árvore e cards (usado quando não há pasta-mãe válida)."""
        self._tree.clear_nodes()
        self._load_projects_list = []
        self._project_counts = {}
        self._contents_loaded.clear()
        self._content_queue.clear()
        self._content_timer.stop()
        self._update_cards()

    def _render_project(self, structure: Scanner.ProjectStructure) -> None:
        """Cria o nó do projeto e agenda suas estatísticas."""
        theme = AppStyles.current_theme
        key = str(structure.path)
        self._tree.add_node(
            key,
            {
                self._COL_NAME: structure.name,
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
            key, self._COL_ACTIONS, self._build_project_actions(structure.path)
        )
        self._apply_icon(key, structure.path, True)
        self._request_statistics(key, structure.path)

    def _render_folder(self, project: Path, folder: Scanner.FolderStatus) -> None:
        """Cria o nó de uma pasta (correta, incoerente ou ausente)."""
        key = str(folder.path)
        color = _status_color(folder.status)
        missing = folder.status == Scanner.STATUS_MISSING
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
        self._apply_icon(key, Path(key), True)
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

    def _render_structure_node(
        self,
        node: Scanner.StructureNode,
        parent_key: str,
        expected: List[str],
        is_year: bool = False,
    ) -> None:
        """Renderiza um nó estrutural (ano ou pasta do template)."""
        key = str(node.path)
        color = _status_color(node.status)
        missing = node.status == Scanner.STATUS_MISSING
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
        self._apply_icon(key, Path(key), True)
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

    # ── Conteúdo real (subpastas + arquivos, sob demanda) ────────────

    def _load_folder_contents(self, key: str) -> None:
        """Lista (sob demanda) subpastas e arquivos de uma pasta ao expandir."""
        if key in self._contents_loaded:
            return
        self._contents_loaded.add(key)
        if not Path(key).is_dir():
            return
        worker = Scanner.FolderContentWorker(self._generation, key)
        self._workers.add(worker)
        worker.signals.finished.connect(self._on_folder_contents)
        worker.signals.finished.connect(lambda *_: self._workers.discard(worker))
        self._work_pool.start(worker)

    def _on_folder_contents(
        self,
        generation: int,
        folder: str,
        dirs: List[Path],
        files: List[Scanner.FileEntry],
    ) -> None:
        """Enfileira o conteúdo listado para render em lotes."""
        if generation != self._generation or not self._tree.has_node(folder):
            return
        for path in dirs:
            self._content_queue.append((folder, path, True, 0))
        for entry in files:
            self._content_queue.append((folder, entry.path, False, entry.size))
        if self._content_queue and not self._content_timer.isActive():
            self._content_timer.start(self._RENDER_DELAY_MS)

    def _render_content_batch(self) -> None:
        """Renderiza um lote de itens de conteúdo (mantém a UI responsiva)."""
        self._tree.setUpdatesEnabled(False)
        try:
            processed = 0
            while self._content_queue and processed < self._RENDER_BATCH:
                parent_key, path, is_dir, size = self._content_queue.popleft()
                self._render_content_item(parent_key, path, is_dir, size)
                processed += 1
        finally:
            self._tree.setUpdatesEnabled(True)
        if self._content_queue:
            self._content_timer.start(self._RENDER_DELAY_MS)

    def _render_content_item(
        self, parent_key: str, path: Path, is_dir: bool, size: int
    ) -> None:
        """Cria o nó de uma subpasta ou de um arquivo dentro de ``parent_key``."""
        if not self._tree.has_node(parent_key):
            return
        if is_dir:
            self._render_subfolder(parent_key, path)
        else:
            self._render_file(parent_key, path, size)

    def _render_subfolder(self, parent_key: str, path: Path) -> None:
        """Cria o nó de uma subpasta real (não validada pelo template)."""
        key = str(path)
        if self._tree.has_node(key):
            return
        theme = AppStyles.current_theme
        self._tree.add_node(
            key,
            {
                self._COL_NAME: path.name,
                self._COL_STATUS: "PASTA",
                self._COL_FILES: "...",
                self._COL_DIRS: "...",
                self._COL_SIZE: "...",
            },
            parent_key=parent_key,
            colors={
                self._COL_NAME: theme.TEXT_MEDIUM,
                self._COL_STATUS: theme.TEXT_LOW,
            },
            kind="subfolder",
        )
        self._tree.set_cell_widget(
            key, self._COL_ACTIONS, self._build_subfolder_actions(path)
        )
        self._apply_icon(key, path, True)
        self._request_statistics(key, path)

    def _render_file(self, parent_key: str, path: Path, size: int) -> None:
        """Cria o nó folha de um arquivo dentro da pasta ``parent_key``."""
        key = str(path)
        if self._tree.has_node(key):
            return
        theme = AppStyles.current_theme
        self._tree.add_node(
            key,
            {
                self._COL_NAME: path.name,
                self._COL_STATUS: "ARQUIVO",
                self._COL_FILES: "—",
                self._COL_DIRS: "—",
                self._COL_SIZE: Scanner.format_size(size),
            },
            parent_key=parent_key,
            colors={
                self._COL_NAME: theme.TEXT_MEDIUM,
                self._COL_STATUS: theme.TEXT_LOW,
            },
            kind="file",
        )
        self._tree.set_cell_widget(
            key, self._COL_ACTIONS, self._build_file_actions(path)
        )
        self._apply_icon(key, path, False)

    def _build_subfolder_actions(self, path: Path) -> GridActionCell:
        """Célula de ações de uma subpasta: Abrir no gerenciador de arquivos."""
        btn_open = SimpleSecondaryButton("Abrir", glow=False)
        btn_open.clicked.connect(
            lambda _=False: FsOps.open_in_explorer(path)
        )
        return GridActionCell(btn_open)

    def _build_file_actions(self, path: Path) -> GridActionCell:
        """Célula de ações de um arquivo: Abrir com o programa padrão."""
        btn_open = SimpleSecondaryButton("Abrir", glow=False)
        btn_open.clicked.connect(lambda _=False: FsOps.open_path(path))
        return GridActionCell(btn_open)

    def _apply_icon(self, key: str, path: Path, is_dir: bool) -> None:
        """Aplica (ou limpa) o ícone do sistema na coluna de nome do nó."""
        if not self._show_icons:
            self._tree.clear_cell_icon(key, self._COL_NAME)
            return
        self._tree.set_cell_icon(
            key,
            self._COL_NAME,
            IconManager.system_icon(str(path), is_dir=is_dir),
        )

    def _on_icons_toggled(self) -> None:
        """Alterna a exibição dos ícones e reaplica nos nós já renderizados."""
        self._show_icons = self._icons_cb.is_item_checked("icons")
        self.save_prefs()
        for key in self._tree.keys():
            if not self._show_icons:
                self._tree.clear_cell_icon(key, self._COL_NAME)
                continue
            is_dir = self._tree.node_kind(key) != "file"
            self._apply_icon(key, Path(key), is_dir)

    def _clear_contents_loaded(self, root_key: str) -> None:
        """Esquece o conteúdo carregado de um ramo (recarrega ao expandir)."""
        prefix = root_key + os.sep
        self._contents_loaded.discard(root_key)
        for key in [k for k in self._contents_loaded if k.startswith(prefix)]:
            self._contents_loaded.discard(key)
        self._content_queue = deque(
            item for item in self._content_queue
            if not item[0].startswith(prefix)
        )

    def _load_contents_for_expanded(self) -> None:
        """Recarrega o conteúdo das pastas que ficaram abertas após um reload."""
        for key in self._tree.expanded_keys():
            if self._tree.node_kind(key) in ("project", "folder", "subfolder"):
                self._load_folder_contents(key)

    # ── Estatísticas ─────────────────────────────────────────────────

    def _request_statistics(self, key: str, path: Path) -> None:
        """Agenda o cálculo de estatísticas de um nó em background."""
        worker = Scanner.StatisticsWorker(self._generation, str(path))
        self._workers.add(worker)
        worker.signals.finished.connect(self._on_statistics_finished)
        worker.signals.finished.connect(lambda *_: self._workers.discard(worker))
        self._work_pool.start(worker)

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

    def _update_cards(self) -> None:
        """Atualiza os cards de resumo a partir das contagens por projeto."""
        totals = {"correct": 0, "incorrect": 0, "missing": 0}
        for counts in self._project_counts.values():
            for key in totals:
                totals[key] += counts.get(key, 0)
        self._cards.set_card_value(0, 0, str(len(self._load_projects_list)))
        self._cards.set_card_value(1, 0, str(totals["correct"]))
        self._cards.set_card_value(2, 0, str(totals["incorrect"]))
        self._cards.set_card_value(3, 0, str(totals["missing"]))

    # ── Estado / filtro / watcher ────────────────────────────────────

    def _capture_state(self) -> Dict[str, Any]:
        """Captura os nós expandidos antes de recarregar."""
        return {"expanded": self._tree.expanded_keys()}

    def _restore_state(self, state: Dict[str, Any]) -> None:
        """Restaura os nós que estavam expandidos."""
        for key in state.get("expanded", []):
            self._tree.set_node_expanded(key, True)

    def _on_filter_changed(self, _key: str, text: str) -> None:
        """Filtra os projetos pelo nome digitado."""
        self._filter_text = text or ""
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

    def _schedule_auto_refresh(self, path: str = "") -> None:
        """Coleta a mudança do watcher e agenda o tratamento (debounce)."""
        if self._operations_in_progress > 0:
            return
        if time.monotonic() < self._ignore_watcher_until:
            return
        if path:
            self._pending_changes.add(path)
        self._refresh_timer.start()

    def _on_refresh_timeout(self) -> None:
        """Roteia as mudanças: refresh por projeto ou recarga completa."""
        if not self._pending_changes:
            return
        if self._loading:
            self._refresh_timer.start()
            return
        changes = list(self._pending_changes)
        self._pending_changes.clear()
        for raw in changes:
            project = self._resolve_project(Path(raw))
            if project is None:
                self._load_projects(show_toast=False, show_progress=False)
                return
            self._refresh_project(project)

    def _resolve_project(self, path: Path) -> Optional[Path]:
        """Retorna o projeto carregado que contém ``path`` (ou None)."""
        for project in self._load_projects_list:
            if path == project or project in path.parents:
                return project
        return None

    def _refresh_project(self, project: Path) -> None:
        """Re-escaneia apenas ``project`` e substitui o seu ramo na árvore."""
        key = str(project)
        if self._loading or not self._tree.has_node(key):
            return
        if key in self._refreshing:
            self._refresh_pending.add(key)
            return
        self._refreshing.add(key)
        worker = Scanner.ProjectScanWorker(self._generation, key)
        self._workers.add(worker)
        worker.signals.finished.connect(self._on_project_scanned)
        worker.signals.failed.connect(self._on_project_scan_failed)
        worker.signals.finished.connect(lambda *_: self._workers.discard(worker))
        worker.signals.failed.connect(lambda *_: self._workers.discard(worker))
        self._work_pool.start(worker)

    def _on_project_scanned(
        self, generation: int, result: Scanner.ProjectScanResult
    ) -> None:
        """Aplica o resultado do refresh de um projeto."""
        if generation != self._generation:
            return
        key = result.path
        self._refreshing.discard(key)
        self._refreshed_at[key] = time.monotonic()
        if self._tree.has_node(key):
            self._rebuild_project_branch(result)
        if key in self._refresh_pending:
            self._refresh_pending.discard(key)
            self._refresh_project(Path(key))

    def _expanded_branch(self, root_key: str) -> List[str]:
        """Retorna as chaves expandidas dentro do ramo ``root_key``."""
        prefix = root_key + os.sep
        return [
            key for key in self._tree.expanded_keys()
            if key.startswith(prefix)
        ]

    def _rebuild_project_branch(self, scan: Scanner.ProjectScanResult) -> None:
        """Remove e re-renderiza os filhos de um único projeto.

        Preserva as pastas (abas) que estavam abertas para que criar,
        renomear ou mesclar pastas não feche a navegação do usuário.
        """
        key = scan.path
        expected_years = [str(year) for year in Scanner.DEFAULT_YEARS]
        expanded = self._expanded_branch(key)
        self._clear_contents_loaded(key)
        self._render_queue.clear()
        self._register_project_counts(key, scan.structure, scan.years)
        self._append_project_children(
            scan.structure, scan.years, expected_years
        )
        self._tree.setUpdatesEnabled(False)
        try:
            self._tree.remove_children(key)
            while self._render_queue:
                self._render_queue.popleft()()
        finally:
            self._tree.setUpdatesEnabled(True)
        self._request_statistics(key, Path(key))
        self._tree.set_node_expanded(key, True)
        for node_key in expanded:
            self._tree.set_node_expanded(node_key, True)
        self._apply_current_filter()
        self._update_cards()

    def _on_project_scan_failed(self, generation: int, message: str) -> None:
        """Trata falha do refresh de um projeto (silencioso)."""
        if generation != self._generation:
            return
        self.logger.warning(
            f"Falha ao atualizar projeto: {message}",
            code="PSM_PROJ_SCAN_ERR",
            error=message,
        )

    def _on_node_expanded(self, key: str) -> None:
        """Atualiza o projeto (se defasado) e carrega o conteúdo da pasta."""
        if self._loading:
            return
        kind = self._tree.node_kind(key)
        if kind == "project":
            self._maybe_refresh_project(key)
        if kind in ("project", "folder", "subfolder"):
            self._load_folder_contents(key)

    def _maybe_refresh_project(self, key: str) -> None:
        """Re-escaneia um projeto ao ser aberto, se estiver defasado."""
        if self._resolve_project(Path(key)) != Path(key):
            return
        if time.monotonic() - self._refreshed_at.get(key, 0.0) < (
            self._EXPAND_REFRESH_INTERVAL
        ):
            return
        self._refresh_project(Path(key))

    def _suspend_watcher(self, seconds: float = 1.5) -> None:
        """Suspende o watcher temporariamente durante operações locais."""
        self._ignore_watcher_until = max(
            self._ignore_watcher_until, time.monotonic() + seconds
        )
        self._refresh_timer.stop()
        self._pending_changes.clear()

    # ── Ações (células) ──────────────────────────────────────────────

    def _build_project_actions(self, project: Path) -> GridActionCell:
        """Célula de ações de um projeto: Abrir + Adicionar pasta."""
        btn_open = SimpleSecondaryButton("Abrir", glow=False)
        btn_open.clicked.connect(lambda _=False: FsOps.open_in_explorer(project))
        menu = SimpleMenuButton(
            {name: name for name in Scanner.DEFAULT_PROJECT_FOLDERS},
            text="+ Adicionar pasta",
            lazy=True,
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
        btn_open = SimpleSecondaryButton("Abrir", glow=False)
        btn_open.clicked.connect(
            lambda _=False: FsOps.open_in_explorer(folder_path)
        )
        if folder_name == Scanner.DOCUMENT_YEARS_FOLDER:
            btn_years = SimpleSecondaryButton("+ Anos", glow=False)
            btn_years.clicked.connect(
                lambda _=False, path=folder_path: self._on_add_years(path)
            )
            return GridActionCell(btn_open, btn_years)
        menu = SimpleMenuButton(
            {name: name for name in Scanner.DEFAULT_PROJECT_FOLDERS},
            text="Padronizar",
            lazy=True,
        )
        menu.item_selected.connect(
            lambda name, origin=folder_path: self._rename_folder(origin, name)
        )
        return GridActionCell(btn_open, menu)

    def _build_structure_actions(
        self, folder_path: Path, expected: List[str]
    ) -> GridActionCell:
        """Célula de ações de um nó estrutural existente: Abrir (+ Padronizar)."""
        btn_open = SimpleSecondaryButton("Abrir", glow=False)
        btn_open.clicked.connect(
            lambda _=False: FsOps.open_in_explorer(folder_path)
        )
        if not expected:
            return GridActionCell(btn_open)
        menu = SimpleMenuButton(
            {name: name for name in expected}, text="Padronizar", lazy=True
        )
        menu.item_selected.connect(
            lambda name, origin=folder_path: self._rename_folder(origin, name)
        )
        return GridActionCell(btn_open, menu)

    def _build_structure_missing_actions(
        self, node: Scanner.StructureNode
    ) -> GridActionCell:
        """Célula de ações de um nó estrutural ausente: cria a subárvore."""
        btn = SimpleSecondaryButton("+ Criar", glow=False)
        btn.clicked.connect(lambda _=False, n=node: self._create_structure(n))
        return GridActionCell(btn)

    def _build_missing_actions(self, project: Path, name: str) -> GridActionCell:
        """Célula de ações de uma pasta ausente: Criar."""
        btn = SimpleSecondaryButton("+ Criar", glow=False)
        btn.clicked.connect(
            lambda _=False, proj=project, folder=name:
            self._create_folder(proj, folder)
        )
        return GridActionCell(btn)

    # ── Operações ────────────────────────────────────────────────────

    def _run_folder_operation(
        self,
        op: str,
        operation: Callable[[], Any],
        make_message: Callable[[str], str],
        project: Optional[Path] = None,
    ) -> None:
        """Executa uma operação de filesystem em background e atualiza a árvore.

        Quando ``project`` é informado, apenas o ramo desse projeto é
        re-escaneado; caso contrário, faz uma recarga completa silenciosa.
        """
        self._suspend_watcher(3.0)
        self._operations_in_progress += 1
        worker = FsOps.FolderTaskWorker(op, operation)
        self._workers.add(worker)

        def finish() -> None:
            self._operations_in_progress = max(
                0, self._operations_in_progress - 1
            )
            self._workers.discard(worker)

        def refresh() -> None:
            if project is not None:
                self._refresh_project(project)
            else:
                self._load_projects(show_toast=False, show_progress=False)

        def on_success(_op: str, value: str) -> None:
            finish()
            self._suspend_watcher(3.0)
            message = make_message(value)
            MessageBox.show_toast(message, parent=self)
            SignalManager.instance().console_message.emit(message)
            refresh()

        def on_error(_op: str, message: str) -> None:
            finish()
            self._suspend_watcher(1.0)
            self.logger.error(
                f"Falha na operação de pasta '{_op}'",
                code="PSM_OP_ERR",
                error=message,
            )
            MessageBox.show_toast(
                f"Erro: {message}", is_error=True, parent=self
            )
            refresh()

        worker.signals.success.connect(on_success)
        worker.signals.error.connect(on_error)
        self._work_pool.start(worker)

    def _create_folder(self, project: Path, name: str) -> None:
        """Cria uma pasta padrão dentro de um projeto."""
        destination = project / name
        if destination.exists():
            MessageBox.show_toast(f"{name} já existe.", parent=self)
            return
        self._run_folder_operation(
            "create_folder",
            lambda: FsOps.create_folder(project, name),
            lambda _value: f"Pasta criada: {name}",
            project=project,
        )

    def _create_structure(self, node: Scanner.StructureNode) -> None:
        """Cria a pasta ausente e todo o template abaixo dela."""
        self._run_folder_operation(
            "create_template",
            lambda: FsOps.create_template(node.path, node.subtree or {}),
            lambda _value: f"Estrutura criada: {node.name}",
            project=self._resolve_project(node.path),
        )

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

        def operation() -> int:
            created = 0
            for year in years:
                FsOps.create_document_year(envio_path, int(year))
                created += 1
            return created

        self._run_folder_operation(
            "create_years",
            operation,
            lambda value: f"{value} pasta(s) de ano criada(s).",
            project=self._resolve_project(envio_path),
        )

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
        project = self._resolve_project(origin)
        self._suspend_watcher(3.0)
        self._operations_in_progress += 1
        worker = FsOps.RenameFolderWorker(origin, new_name)
        self._workers.add(worker)

        def finish() -> None:
            self._operations_in_progress = max(
                0, self._operations_in_progress - 1
            )
            self._workers.discard(worker)

        def refresh() -> None:
            if project is not None:
                self._refresh_project(project)
            else:
                self._load_projects(show_toast=False, show_progress=False)

        def on_success(_op: str, _src: str, dst: str) -> None:
            finish()
            self._suspend_watcher(3.0)
            MessageBox.show_toast(f"Renomeada para {Path(dst).name}", parent=self)
            SignalManager.instance().console_message.emit(
                f"Pasta renomeada: {Path(dst).name}"
            )
            refresh()

        def on_error(_op: str, message: str) -> None:
            finish()
            self._suspend_watcher(1.0)
            MessageBox.show_toast(
                f"Erro ao renomear: {message}", is_error=True, parent=self
            )
            refresh()

        worker.signals.success.connect(on_success)
        worker.signals.error.connect(on_error)
        self._work_pool.start(worker)

    def _merge_folders(self, source: Path, destination: Path) -> None:
        """Mescla duas pastas em background e reporta o resultado."""
        self._run_folder_operation(
            "merge_folders",
            lambda: len(FsOps.merge_folders(source, destination)),
            lambda value: (
                "Pastas mescladas com sucesso."
                if value == "0"
                else f"Mesclado com {value} conflito(s)."
            ),
            project=self._resolve_project(source),
        )

    def _on_node_activated(self, key: str) -> None:
        """Abre o nó com duplo clique (arquivo no app padrão; pasta no explorer)."""
        path = Path(key)
        if not path.exists():
            return
        if self._tree.node_kind(key) == "file":
            FsOps.open_path(path)
            return
        FsOps.open_in_explorer(path)
