# -*- coding: utf-8 -*-
"""
ProjectDatabasePlugin — Banco de Dados de Projetos (OS)
======================================================
Ferramenta CENTRAL de ATUALIZAÇÃO do banco de OS.

Nova regra de negócio:
- A ferramenta **não cria mais OS**. Ela consulta a fonte oficial (Firebase,
  coleção ``banco_dados``) as OS já existentes, **re-escaneia** as pastas
  associadas a cada SubOS e **atualiza** ``folders``/``years`` no Firebase.
- A ferramenta tem **zero contato** com o JSON de dados: quem grava/lê e gera
  os backups JSON é a classe de banco ``CloudProjectDatabase`` (Contrato 28).
- Ao final, exibe um **modal** com o resumo do que foi atualizado.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import QThreadPool, QTimer

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseAuthService import FirebaseAuthService
from core.firebase.FirebaseCredentialManager import FirebaseCredentialManager
from core.firebase.FirebaseServiceAccountAuth import FirebaseServiceAccountAuth
from core.firebase.FirebaseTokenProvider import FirebaseTokenProvider
from core.firebase.CloudDatabaseSync import CloudDatabaseSync
from core.firebase.CloudProjectDatabase import CloudProjectDatabase
from core.firebase.FirebaseWorker import FirebaseWorker
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from plugins.project_database_manager.ProjectDatabaseService import (
    ProjectDatabaseWorker,
)
from resources.widgets.dialogs.FirebaseLoginDialog import FirebaseLoginDialog
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
from utils.ProjectStructureUtil import (
    DOCUMENT_YEARS_FOLDER,
    ProjectStructureUtil,
)


class ProjectDatabasePlugin(BasePlugin):
    """Ferramenta CENTRAL: atualiza (no Firebase) os dados das OS já existentes."""

    _COL_OS = 0
    _COL_CLIENT = 1
    _COL_FOLDERS = 2
    _COL_YEARS = 3
    _COL_PATH = 4

    # Coleção do Cloud Firestore onde o banco é espelhado.
    _CLOUD_COLLECTION = CloudProjectDatabase.COLLECTION

    # Tempo (ms) que o 100% fica visível antes de resetar a barra central.
    _PROGRESS_RESET_MS = 1200

    def __init__(self, parent=None) -> None:
        super().__init__(
            tool_key=ToolKey.PROJECT_DATABASE.value,
            parent=parent,
            title="Banco de Dados",
            buttons_config={
                "sincronizar": {
                    "text": "SINCRONIZAR NUVEM",
                    "callback": self._on_sync_clicked,
                    "type": "secondary",
                    "description": "Baixa a base do Firebase e materializa os backups JSON",
                },
                "atualizar": {
                    "text": "ATUALIZAR DADOS",
                    "callback": self._on_refresh_clicked,
                    "type": "primary",
                    "description": "Consulta o Firebase, re-escaneia as pastas e atualiza a base",
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
        self._auth_worker: Optional[FirebaseWorker] = None
        self._sync_worker: Optional[FirebaseWorker] = None
        self._load_worker: Optional[FirebaseWorker] = None
        self._save_worker: Optional[FirebaseWorker] = None
        self._database: Dict[str, Any] = {}
        self._pending_orders: list = []
        self._pending_summary: Dict[str, Any] = {}
        self._suspend_backup_cb = False
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        QTimer.singleShot(0, self._load_from_disk)
        QTimer.singleShot(0, self._maybe_backup)
        QTimer.singleShot(100, self._ensure_firebase_credentials)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Cancela os workers e limpa a fila antes de fechar."""
        if self._worker is not None:
            self._worker.cancel()
        for worker in (self._auth_worker, self._sync_worker,
                       self._load_worker, self._save_worker):
            if worker is not None and worker.isRunning():
                worker.quit()
                worker.wait(1000)
        self._pool.clear()
        super().closeEvent(event)

    # ── Autenticação / Firebase ──────────────────────────────────────

    def _ensure_firebase_credentials(self) -> None:
        """Garante a autenticação Firebase via credenciais salvas ou diálogo inicial."""
        if FirebaseServiceAccountAuth.is_configured():
            self.logger.info(
                "Conta de serviço configurada — login de usuário dispensado",
                code="FB_SA_CONFIGURED",
            )
            return
        if FirebaseCredentialManager.has_saved_credentials():
            creds = FirebaseCredentialManager.load_credentials()
            if creds and creds.get("email") and creds.get("password"):
                self.logger.info("Credenciais Firebase criptografadas detectadas", code="FB_AUTO_LOGIN")
                self._authenticate_async(creds["email"], creds["password"], creds.get("name", ""))
            return

        # Primeira vez: exibe diálogo solicitando credenciais
        dialog = FirebaseLoginDialog(
            default_name="Matheus Martinelli",
            default_email="martinelli.matheus0@gmail.com",
            default_password="12345678",
            parent=self,
        )
        if dialog.exec():
            name, email, password = dialog.get_credentials()
            saved = FirebaseCredentialManager.save_credentials(email, password, name)
            if saved:
                self.logger.info("Credenciais criptografadas salvas com sucesso", code="FB_CREDS_SAVED")
                self._authenticate_async(email, password, name)
        else:
            self.logger.warning("Configuração inicial do Firebase cancelada pelo usuário", code="FB_CREDS_SKIPPED")

    def _authenticate_async(self, email: str, password: str, name: str = "") -> None:
        """Autentica com o Firebase de forma assíncrona para não travar a UI."""
        self._auth_worker = FirebaseWorker(
            FirebaseAuthService.sign_in_with_email,
            email,
            password,
            name,
            parent=self,
        )
        self._auth_worker.finished_with_result.connect(self._on_auth_result)
        self._auth_worker.start()

    def _on_auth_result(self, result: Optional[Dict[str, Any]]) -> None:
        if result:
            self.logger.info("Sessão Firebase iniciada com sucesso", code="FB_SESSION_OK")
            self._load_from_disk()
        else:
            self.logger.warning("Não foi possível autenticar no Firebase (operação offline)", code="FB_SESSION_OFFLINE")

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
        """Lê a base da FONTE OFICIAL (Firebase) via classe de banco, em background."""
        self._database = {}
        if not FirebaseTokenProvider.has_credentials():
            self._render()
            self.page.set_badge(self.page.INFO)
            return
        self._load_worker = FirebaseWorker(
            CloudProjectDatabase.load_orders,
            tool_key=ToolKey.PROJECT_DATABASE.value,
            parent=self,
        )
        self._load_worker.finished_with_result.connect(self._on_orders_loaded)
        self._load_worker.failed.connect(self._on_load_failed)
        self._load_worker.start()

    def _on_orders_loaded(self, result: Optional[list]) -> None:
        """Aplica a base lida da fonte oficial na UI."""
        orders = list(result or [])
        self._database = {"projects": orders}
        self._render()
        self.page.set_badge(self.page.PRONTA if orders else self.page.INFO)

    def _on_load_failed(self, message: str) -> None:
        """Trata falha ao consultar o Firebase — a UI fica vazia (sem JSON local)."""
        self.logger.warning(
            "Falha ao consultar o Firebase", code="PDB_LOAD_ERR", error=message
        )
        self._database = {"projects": []}
        self._render()
        self.page.set_badge(self.page.INFO)

    def _on_refresh_clicked(self) -> None:
        """Valida pasta-mãe/credenciais e inicia a atualização das OS existentes."""
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
        if not FirebaseTokenProvider.has_credentials():
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_warning(
                "Configure a conta de serviço (ou conecte ao Firebase) para "
                "atualizar a base.",
                title="Banco de Dados",
                parent=self,
            )
            return
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("atualizar", False)
        SignalManager.instance().console_message.emit(
            "Consultando a base no Firebase..."
        )
        self._load_worker = FirebaseWorker(
            CloudProjectDatabase.load_orders,
            tool_key=ToolKey.PROJECT_DATABASE.value,
            parent=self,
        )
        self._load_worker.finished_with_result.connect(
            self._on_orders_loaded_for_refresh
        )
        self._load_worker.failed.connect(self._on_sync_failed)
        self._load_worker.start()

    def _on_orders_loaded_for_refresh(self, result: Optional[list]) -> None:
        """Após consultar a base, inicia a re-varredura das pastas existentes."""
        orders = list(result or [])
        if not orders:
            self.page.set_badge(self.page.INFO)
            self.page.buttons.set_enabled("atualizar", True)
            MessageBox.show_info(
                "Nenhuma OS cadastrada na base. Crie OS pela ferramenta "
                "Acompanhamento de OS.",
                title="Banco de Dados",
                parent=self,
            )
            return
        self._start_refresh(orders)

    def _start_refresh(self, orders: list) -> None:
        """Inicia a re-varredura assíncrona das pastas das OS existentes."""
        self._generation += 1
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("atualizar", False)
        SignalManager.instance().console_message.emit("Lendo as pastas das OS...")
        SignalManager.instance().progress_update.emit(0.0)

        self._worker = ProjectDatabaseWorker(
            self._generation, str(self._mother_folder), orders
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

    def _on_finished(self, generation: int, orders: object, summary: object) -> None:
        """Grava os dados atualizados no Firebase (classe de banco), em background."""
        if generation != self._generation:
            return
        self._pending_orders = list(orders or [])
        self._pending_summary = dict(summary or {})
        SignalManager.instance().console_message.emit(
            "Gravando atualizações no Firebase..."
        )
        self._save_worker = FirebaseWorker(
            CloudProjectDatabase.save_orders,
            self._pending_orders,
            str(self._mother_folder),
            tool_key=ToolKey.PROJECT_DATABASE.value,
            parent=self,
        )
        self._save_worker.finished_with_result.connect(self._on_saved)
        self._save_worker.failed.connect(self._on_failed_save)
        self._save_worker.start()

    def _on_saved(self, _result: Optional[object]) -> None:
        """Notifica o fim: atualiza a UI, mostra o resumo e libera os botões."""
        orders = self._pending_orders
        self._database = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "projects": orders,
        }
        self._render()
        self.page.set_badge(self.page.PRONTA)
        self.page.buttons.set_enabled("atualizar", True)
        self.save_prefs()
        SignalManager.instance().console_message.emit("Base atualizada no Firebase.")
        self._show_summary(self._pending_summary)
        self._finish_progress()

    def _show_summary(self, summary: Dict[str, Any]) -> None:
        """Exibe um MODAL com o resumo do que foi atualizado (Contrato 1)."""
        missing = list(summary.get("missing", []))
        text = (
            f"OS na base: {summary.get('total_orders', 0)}\n"
            f"OS atualizadas: {summary.get('updated_orders', 0)}\n"
            f"Pastas novas: {summary.get('folders_added', 0)}\n"
            f"Anos novos: {summary.get('years_added', 0)}\n"
            f"Pastas ausentes: {len(missing)}"
        )
        detail = "\n".join(missing[:80]) if missing else ""
        MessageBox.show_info(
            text,
            title="Banco de Dados — Atualização concluída",
            detail=detail,
            parent=self,
        )

    def _on_failed(self, generation: int, message: str) -> None:
        """Trata falha da re-varredura em background."""
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

    def _on_failed_save(self, message: str) -> None:
        """Trata falha ao gravar a base no Firebase."""
        self.logger.error(
            "Falha ao gravar a base no Firebase",
            code="PDB_SAVE_ERR",
            error=message,
        )
        MessageBox.show_toast(
            f"Erro ao gravar no Firebase: {message}", is_error=True, parent=self
        )
        self.page.set_badge(self.page.ERROR)
        self.page.buttons.set_enabled("atualizar", True)
        SignalManager.instance().progress_reset.emit()

    def _finish_progress(self) -> None:
        """Mostra 100% e agenda o reset da barra central."""
        signals = SignalManager.instance()
        signals.progress_update.emit(100.0)
        QTimer.singleShot(self._PROGRESS_RESET_MS, signals.progress_reset.emit)

    # ── Sincronização com a nuvem (Firestore) ────────────────────────

    def _cloud_dir(self) -> Optional[Path]:
        """Diretório local dos backups JSON (``<pasta-mãe>/.BancoDados``)."""
        if self._mother_folder is None:
            return None
        return Path(self._mother_folder) / ".BancoDados"

    def _on_sync_clicked(self) -> None:
        """Baixa a base do Firebase e materializa os backups JSON locais."""
        if self._mother_folder is None:
            self.page.set_badge(self.page.INFO)
            MessageBox.show_warning(
                "Defina a pasta-mãe no Gerenciador de Estrutura antes de sincronizar.",
                title="Banco de Dados",
                parent=self,
            )
            return
        if not FirebaseTokenProvider.has_credentials():
            MessageBox.show_warning(
                "Configure a conta de serviço ou conecte ao Firebase para sincronizar.",
                title="Banco de Dados",
                parent=self,
            )
            return
        self._start_pull()

    def _start_pull(self) -> None:
        """Inicia o download assíncrono da base a partir do Firestore."""
        local_dir = self._cloud_dir()
        if local_dir is None:
            return
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("sincronizar", False)
        self.page.buttons.set_enabled("atualizar", False)
        SignalManager.instance().console_message.emit("Baixando a base do Firebase...")
        self._sync_worker = FirebaseWorker(
            CloudDatabaseSync.pull,
            str(local_dir),
            self._CLOUD_COLLECTION,
            tool_key=ToolKey.PROJECT_DATABASE.value,
            parent=self,
        )
        self._sync_worker.finished_with_result.connect(self._on_pull_result)
        self._sync_worker.failed.connect(self._on_sync_failed)
        self._sync_worker.start()

    def _on_pull_result(self, result: Optional[Dict[str, Any]]) -> None:
        """Recarrega a base após materializar os backups JSON."""
        pulled = (result or {}).get("pulled", 0)
        self.page.set_badge(self.page.PRONTA)
        self.page.buttons.set_enabled("sincronizar", True)
        self.page.buttons.set_enabled("atualizar", True)
        self._load_from_disk()
        message = f"Nuvem sincronizada: {pulled} arquivo(s) restaurado(s)."
        MessageBox.show_toast(message, parent=self)
        SignalManager.instance().console_message.emit(message)

    def _on_sync_failed(self, message: str) -> None:
        """Trata falhas de sincronização/leitura em background."""
        self.logger.error(
            "Falha na operação com a base", code="PDB_SYNC_ERR", error=message
        )
        self.page.set_badge(self.page.ERROR)
        self.page.buttons.set_enabled("sincronizar", True)
        self.page.buttons.set_enabled("atualizar", True)
        MessageBox.show_toast(
            f"Erro na sincronização: {message}", is_error=True, parent=self
        )

    # ── Render ───────────────────────────────────────────────────────

    def _render(self) -> None:
        """Popula a árvore, os cards e a legenda com os dados atuais."""
        self._tree.clear_nodes()
        for index, record in enumerate(self._database.get("projects", [])):
            summary = ProjectStructureUtil.aggregate_record(record)
            resolved = self._resolve_display_path(summary["path"])
            node_key = f"os::{record.get('os', index)}::{index}"
            self._tree.add_node(
                key=node_key,
                texts={
                    self._COL_OS: record.get("os", ""),
                    self._COL_CLIENT: summary["client"] or "—",
                    self._COL_FOLDERS: ", ".join(summary["folders"]) or "—",
                    self._COL_YEARS: ", ".join(summary["years"]) or "—",
                    self._COL_PATH: resolved or "—",
                },
                bold=True,
                kind="os",
            )
        self._update_cards()
        self._update_legend()

    def _resolve_display_path(self, rel_path: str) -> str:
        """Resolve um caminho relativo para exibição (caminho absoluto local)."""
        if not rel_path or self._mother_folder is None:
            return rel_path or ""
        return str(ProjectStructureUtil.resolve_path(self._mother_folder, rel_path))

    def _update_cards(self) -> None:
        """Atualiza os cards de resumo."""
        projects = self._database.get("projects", [])
        summaries = [ProjectStructureUtil.aggregate_record(r) for r in projects]
        total_folders = sum(len(s["folders"]) for s in summaries)
        total_years = sum(len(s["years"]) for s in summaries)
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
                f"{DOCUMENT_YEARS_FOLDER} · atualização no Firebase"
            )
        else:
            text = "Sem dados. Clique em ATUALIZAR DADOS."
        self._legend.widget("hint").setText(text)
