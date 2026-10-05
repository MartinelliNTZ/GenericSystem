# -*- coding: utf-8 -*-
"""
ProjectDatabasePlugin — Banco de Dados de Projetos (OS)
======================================================
Ferramenta CENTRAL que persiste um retrato (JSON) das pastas padrão e dos
anos criados por OS de uma pasta-mãe, além de um backup diário do banco.

- Os dados só são recalculados/gravados quando o usuário clica em
  ATUALIZAR DADOS; abrir a ferramenta apenas LÊ o consolidado.
- A pasta-mãe vem do Gerenciador de Estrutura (fonte única — somente
  leitura aqui).
- O backup diário é disparado ao iniciar esta ferramenta.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import QThreadPool, QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from plugins.project_database_manager.ProjectDatabaseService import (
    ProjectDatabaseWorker,
)
from plugins.project_database_manager.ProjectDatabaseStore import (
    ProjectDatabaseStore,
)
from resources.widgets.grid.GridCardView import GridCardView
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridTree import GridTree
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleSelector import SimpleSelector
from utils.FormatUtils import FormatUtils
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProjectDatabaseBackup import ProjectDatabaseBackup
from utils.ProjectStructureUtil import DOCUMENT_YEARS_FOLDER


class ProjectDatabasePlugin(BasePlugin):
    """Ferramenta CENTRAL: banco de dados (JSON) das pastas/anos por OS."""

    _COL_OS = 0
    _COL_CLIENT = 1
    _COL_FOLDERS = 2
    _COL_YEARS = 3
    _COL_PATH = 4

    # Tempo (ms) que o 100% fica visível antes de resetar a barra central.
    _PROGRESS_RESET_MS = 1200

    def __init__(self, parent=None) -> None:
        super().__init__(
            tool_key=ToolKey.PROJECT_DATABASE.value,
            parent=parent,
            title="Banco de Dados",
            buttons_config={
                "atualizar": {
                    "text": "ATUALIZAR DADOS",
                    "callback": self._on_refresh_clicked,
                    "type": "primary",
                    "description": "Recalcula e grava os dados das OS",
                },
            },
        )
        self._init_runtime()
        self.logger.info("Ferramenta inicializada", code="PDB_READY")

    # ── Ciclo de vida / runtime ──────────────────────────────────────

    def _init_runtime(self) -> None:
        """Configura pool, estado e agenda a carga inicial e o backup."""
        self._generation = 0
        self._worker: Optional[ProjectDatabaseWorker] = None
        self._database: Dict[str, Any] = {}
        self._suspend_backup_cb = False
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        QTimer.singleShot(0, self._load_from_disk)
        QTimer.singleShot(0, self._maybe_backup)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Cancela o worker e limpa a fila antes de fechar."""
        if self._worker is not None:
            self._worker.cancel()
        self._pool.clear()
        super().closeEvent(event)

    # ── Preferências ─────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Carrega a pasta-mãe (do ProjectStructure) e a pasta de backup."""
        self._suspend_backup_cb = True

        struct_prefs = Preferences.load_tool_prefs(
            ToolKey.PROJECT_STRUCTURE,
            caller_tool_key=ToolKey.PROJECT_DATABASE.value,
        )
        saved_mother = struct_prefs.get("mother_folder", "") or ""
        self._mother_folder: Optional[Path] = (
            Path(saved_mother) if saved_mother else None
        )
        self._mother_selector.set_path(saved_mother)

        backup_dir = self.preferences.get("backup_dir", "") or ""
        self._backup_selector.set_path(backup_dir)

        self._suspend_backup_cb = False

    def save_prefs(self) -> None:
        """Persiste a pasta de backup escolhida (Contrato 4)."""
        self.preferences["backup_dir"] = self._backup_selector.path()

    def _on_backup_changed(self, _path: str) -> None:
        """Persiste a pasta de backup quando o usuário a altera."""
        if self._suspend_backup_cb:
            return
        self.save_prefs()

    # ── UI ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        super()._build_ui()

        self._mother_selector = SimpleSelector(
            "Pasta-mãe:",
            placeholder="Definida no Gerenciador de Estrutura",
            browse_mode="directory",
            tooltip="Pasta-mãe dos projetos (somente leitura — vem do Gerenciador de Estrutura)",
        )
        self._mother_selector.edit.setReadOnly(True)
        self._mother_selector.btn.setVisible(False)
        grupo_origem = GroupPainel("Origem")
        grupo_origem.group_layout.addWidget(self._mother_selector)

        self._backup_selector = SimpleSelector(
            "Pasta de backup:",
            placeholder=ProjectDatabaseBackup.DEFAULT_BACKUP_DIR,
            browse_mode="directory",
            tooltip="Pasta onde o backup diário (.zip) do banco é gravado",
        )
        self._backup_selector.on_path_change = self._on_backup_changed
        grupo_backup = GroupPainel("Backup")
        grupo_backup.group_layout.addWidget(self._backup_selector)

        self.main_layout.addWidget(GridGroupPainel(grupo_origem, grupo_backup))
        self._build_cards()
        self._build_tree()
        self._build_legend()

    def _build_cards(self) -> None:
        """Cria os cards de resumo do banco de dados."""
        def card(text: str) -> Dict[str, Any]:
            return {"labels": [
                {"type": "great_accent", "text": "0"},
                {"type": "simple", "text": text},
            ]}

        self._cards = GridCardView({
            "items_per_row": 4,
            "cards": [
                card("Projetos"),
                card("Pastas criadas"),
                card("Anos criados"),
                card("Última atualização"),
            ],
        })
        self.main_layout.addWidget(self._cards)

    def _build_tree(self) -> None:
        """Cria a árvore multicoluna dos registros por OS."""
        self._tree = GridTree(columns=[
            {"header": "OS", "width": 130},
            {"header": "Cliente", "width": 170},
            {"header": "Pastas criadas", "stretch": True},
            {"header": "Anos", "width": 170},
            {"header": "Caminho", "width": 320},
        ])
        self.main_layout.addWidget(self._tree, 1)

    def _build_legend(self) -> None:
        """Cria a legenda/estado vazio abaixo da árvore."""
        self._legend = GridLabel({"hint": {"label": "", "value": ""}}, columns=1)
        self._legend.widget("hint").setStyleSheet(
            "color: #A1A1AA; font-family: Consolas, monospace; font-size: 12px;"
        )
        self.main_layout.addWidget(self._legend)

    # ── Backup ───────────────────────────────────────────────────────

    def _maybe_backup(self) -> None:
        """Dispara o backup diário do banco (no máximo 1x/dia)."""
        if self._mother_folder is None:
            return
        created = ProjectDatabaseBackup.ensure_daily_backup(
            mother_folder=str(self._mother_folder),
            backup_dir=self.preferences.get("backup_dir", ""),
            label="BancoDados",
            tool_key=ToolKey.PROJECT_DATABASE.value,
        )
        if created:
            SignalManager.instance().console_message.emit(
                f"Backup do banco de dados criado: {created}"
            )

    # ── Carga / atualização ──────────────────────────────────────────

    def _load_from_disk(self) -> None:
        """Lê o consolidado existente (somente leitura) e popula a UI."""
        self._database = {}
        if self._mother_folder is not None and self._mother_folder.exists():
            data = ProjectDatabaseStore.load_consolidated(
                self._mother_folder, tool_key=ToolKey.PROJECT_DATABASE.value
            )
            if data.get("projects"):
                self._database = data
        self._render()
        self.page.set_badge(
            self.page.PRONTA if self._database else self.page.INFO
        )

    def _on_refresh_clicked(self) -> None:
        """Valida a pasta-mãe e inicia a atualização dos dados."""
        if self._mother_folder is None:
            self.page.set_badge(self.page.INFO)
            MessageBox.show_warning(
                "Configure a pasta-mãe no Gerenciador de Estrutura antes de "
                "atualizar os dados.",
                title="Banco de Dados",
                parent=self,
            )
            return
        if not self._mother_folder.exists():
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_warning(
                f"A pasta-mãe não existe:\n{self._mother_folder}",
                title="Pasta-mãe inexistente",
                parent=self,
            )
            return
        self._start_refresh()

    def _start_refresh(self) -> None:
        """Inicia a varredura assíncrona da pasta-mãe."""
        self._generation += 1
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("atualizar", False)
        SignalManager.instance().console_message.emit("Lendo os projetos (OS)...")
        SignalManager.instance().progress_update.emit(0.0)

        self._worker = ProjectDatabaseWorker(
            self._generation, str(self._mother_folder)
        )
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.signals.failed.connect(self._on_failed)
        self._pool.start(self._worker)

    def _on_progress(self, generation: int, done: int, total: int) -> None:
        """Atualiza a barra central durante a varredura (Contrato 20)."""
        if generation != self._generation:
            return
        SignalManager.instance().progress_update.emit(
            100.0 * done / max(total, 1)
        )

    def _on_finished(self, generation: int, database: dict) -> None:
        """Grava os JSONs, atualiza a UI e finaliza o progresso."""
        if generation != self._generation:
            return
        self._save_database(database)
        self._database = database
        self._render()
        self.page.set_badge(self.page.PRONTA)
        self.page.buttons.set_enabled("atualizar", True)
        self.save_prefs()

        message = (
            "Banco de dados atualizado: "
            f"{database.get('total_projects', 0)} OS."
        )
        MessageBox.show_toast(message, parent=self)
        SignalManager.instance().console_message.emit(message)
        self._finish_progress()

    def _on_failed(self, generation: int, message: str) -> None:
        """Trata falha da varredura em background."""
        if generation != self._generation:
            return
        self.logger.error(
            "Falha ao atualizar o banco de dados",
            code="PDB_REFRESH_ERR",
            error=message,
        )
        MessageBox.show_toast(
            f"Erro ao atualizar: {message}", is_error=True, parent=self
        )
        self.page.set_badge(self.page.ERROR)
        self.page.buttons.set_enabled("atualizar", True)
        SignalManager.instance().progress_reset.emit()

    def _finish_progress(self) -> None:
        """Mostra 100% e agenda o reset da barra central."""
        signals = SignalManager.instance()
        signals.progress_update.emit(100.0)
        QTimer.singleShot(self._PROGRESS_RESET_MS, signals.progress_reset.emit)

    def _save_database(self, database: dict) -> None:
        """Grava um JSON por OS + o consolidado em ``.BancoDados``."""
        if self._mother_folder is None:
            return
        key = ToolKey.PROJECT_DATABASE.value
        for record in database.get("projects", []):
            ProjectDatabaseStore.save_project(
                self._mother_folder, record, tool_key=key
            )
        ProjectDatabaseStore.save_consolidated(
            self._mother_folder, database, tool_key=key
        )
        ProjectDatabaseStore.prune_projects(
            self._mother_folder,
            [record.get("os", "") for record in database.get("projects", [])],
            tool_key=key,
        )

    # ── Render ───────────────────────────────────────────────────────

    def _render(self) -> None:
        """Popula a árvore, os cards e a legenda com os dados atuais."""
        self._tree.clear_nodes()
        for index, record in enumerate(self._database.get("projects", [])):
            node_key = f"os::{record.get('name', index)}::{index}"
            self._tree.add_node(
                key=node_key,
                texts={
                    self._COL_OS: record.get("os", ""),
                    self._COL_CLIENT: record.get("client", "") or "—",
                    self._COL_FOLDERS: ", ".join(record.get("folders", [])) or "—",
                    self._COL_YEARS: ", ".join(record.get("years", [])) or "—",
                    self._COL_PATH: record.get("path", ""),
                },
                bold=True,
                kind="os",
            )
        self._update_cards()
        self._update_legend()

    def _update_cards(self) -> None:
        """Atualiza os cards de resumo."""
        projects = self._database.get("projects", [])
        total_folders = sum(len(r.get("folders", [])) for r in projects)
        total_years = sum(len(r.get("years", [])) for r in projects)
        self._cards.set_card_value(0, 0, str(len(projects)))
        self._cards.set_card_value(1, 0, str(total_folders))
        self._cards.set_card_value(2, 0, str(total_years))
        self._cards.set_card_value(3, 0, self._format_updated())

    def _format_updated(self) -> str:
        """Formata o ``generated_at`` do banco (Contrato 22)."""
        generated = self._database.get("generated_at", "")
        if not generated:
            return "—"
        try:
            moment = datetime.fromisoformat(generated)
            return FormatUtils.format_date(
                moment.timestamp(), tool_key=ToolKey.PROJECT_DATABASE.value
            )
        except ValueError as e:
            self.logger.error(
                "Data inválida no banco de dados",
                code="PDB_DATE_ERR",
                error=str(e),
                value=generated,
            )
            return generated

    def _update_legend(self) -> None:
        """Atualiza a legenda/estado vazio."""
        if self._database.get("projects"):
            text = (
                "● Pastas padrão do projeto · Anos dentro de "
                f"{DOCUMENT_YEARS_FOLDER}"
            )
        else:
            text = "Sem dados. Clique em ATUALIZAR DADOS."
        self._legend.widget("hint").setText(text)
