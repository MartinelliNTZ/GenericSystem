# -*- coding: utf-8 -*-
"""
CloudUserStatusWidget — Indicador de status de usuário Firebase na barra de menus
=================================================================================
Exibe o estado de conexão (Online / Offline / Desconectado) e o nome do usuário
ao lado dos indicadores de CPU/RAM na MenuBar. Atualiza periodicamente o status
de forma assíncrona para manter a interface responsiva.
"""

from __future__ import annotations

import socket
from typing import Optional
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseAuthService import FirebaseAuthService
from core.firebase.FirebaseCredentialManager import FirebaseCredentialManager
from core.manager.SignalManager import SignalManager
from resources.styles.AppStyles import AppStyles
from utils.BaseUtil import BaseUtil


class _CloudHeartbeatWorker(QThread):
    """Thread em background para verificar conectividade com o Firebase."""

    status_checked = Signal(bool, str)

    def run(self) -> None:
        """Verifica se há conectividade ativa com a nuvem."""
        try:
            # Teste rápido de socket DNS/HTTPS (porta 443 do Google) com timeout de 2s
            sock = socket.create_connection(("identitytoolkit.googleapis.com", 443), timeout=2.0)
            sock.close()
            self.status_checked.emit(True, "Online")
        except OSError:
            self.status_checked.emit(False, "Sem conexão com a nuvem")
        except Exception as e:
            self.status_checked.emit(False, str(e))


class CloudUserStatusWidget(QWidget):
    """Widget de status de autenticação na nuvem para a MenuBar."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = BaseUtil._get_logger(ToolKey.SYSTEM.value, "CloudUserStatusWidget")
        self._user_name: str = ""
        self._email: str = ""
        self._is_online: bool = False
        self._is_authenticated: bool = False
        self._heartbeat_worker: Optional[_CloudHeartbeatWorker] = None

        self._build_ui()
        self._connect_signals()
        self._setup_heartbeat()
        self._refresh_state()

    def _build_ui(self) -> None:
        self.setObjectName("cloud_user_status_widget")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(26)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(5)

        self._icon_label = QLabel("⚪", self)
        self._icon_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._icon_label)

        self._name_label = QLabel("Nuvem: Verificando...", self)
        self._name_label.setStyleSheet(
            f"color: {AppStyles.current_theme.TEXT_PRIMARY}; "
            f"font-size: {AppStyles.current_theme.FONT_SIZE_SMALL}; "
            "font-weight: 500;"
        )
        layout.addWidget(self._name_label)

        self._apply_style()

    def _apply_style(self) -> None:
        bg_surface = AppStyles.current_theme.SURFACE_1
        border_color = AppStyles.current_theme.BORDER_DEFAULT
        hover_border = AppStyles.current_theme.BORDER_ACCENT
        hover_bg = AppStyles.current_theme.SURFACE_3
        self.setStyleSheet(f"""
            QWidget#cloud_user_status_widget {{
                background-color: {bg_surface};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            QWidget#cloud_user_status_widget:hover {{
                border-color: {hover_border};
                background-color: {hover_bg};
            }}
        """)

    def _connect_signals(self) -> None:
        SignalManager.instance().cloud_auth_changed.connect(self._on_cloud_auth_changed)

    def _setup_heartbeat(self) -> None:
        """Configura timer de atualização periódica similar ao monitor de RAM."""
        self._timer = QTimer(self)
        self._timer.setInterval(3000)  # Checa a cada 3 segundos
        self._timer.timeout.connect(self._trigger_heartbeat)
        self._timer.start()

    def _trigger_heartbeat(self) -> None:
        """Inicia verificação assíncrona se não houver worker em execução."""
        if self._heartbeat_worker is not None and self._heartbeat_worker.isRunning():
            return
        self._heartbeat_worker = _CloudHeartbeatWorker(self)
        self._heartbeat_worker.status_checked.connect(self._on_heartbeat_result)
        self._heartbeat_worker.start()

    def _on_heartbeat_result(self, is_reachable: bool, message: str) -> None:
        """Atualiza a interface com o resultado da verificação de conectividade."""
        self._is_online = is_reachable
        self._refresh_state()

    def _refresh_state(self) -> None:
        """Determina o estado atual a partir da sessão, credenciais e conectividade."""
        current_user = FirebaseAuthService.get_current_user()
        saved_name = FirebaseCredentialManager.get_user_name()
        has_token = bool(current_user.get("id_token"))
        has_saved = FirebaseCredentialManager.has_saved_credentials()

        name = current_user.get("name") or saved_name or "Usuário"
        email = current_user.get("email", "")

        if has_token or has_saved:
            self._is_authenticated = True
            self._user_name = name
            self._email = email
            if self._is_online:
                self._icon_label.setText("🟢")
                self._name_label.setText(f"Cloud: {name}")
                tooltip = f"Firebase: Conectado e Online\nUsuário: {name}"
                if email:
                    tooltip += f"\nE-mail: {email}"
                tooltip += "\nStatus: Operacional\n(Clique para opções)"
                self.setToolTip(tooltip)
            else:
                self._icon_label.setText("🟡")
                self._name_label.setText(f"Cloud: {name} (Offline)")
                tooltip = f"Firebase: Offline (Sem conexão)\nUsuário: {name}"
                if email:
                    tooltip += f"\nE-mail: {email}"
                tooltip += "\n(Clique para opções)"
                self.setToolTip(tooltip)
        else:
            self._is_authenticated = False
            self._icon_label.setText("⚪")
            self._name_label.setText("Cloud: Desconectado")
            self.setToolTip("Firebase Desconectado\n(Clique para conectar)")

    def _on_cloud_auth_changed(self, data: dict) -> None:
        """Slot chamado quando o sinal de autenticação na nuvem é emitido."""
        self._refresh_state()
        self._trigger_heartbeat()

    def mousePressEvent(self, event) -> None:
        """Abre menu de contexto estilizado ao clicar no widget."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_options_menu()
        super().mousePressEvent(event)

    def _show_options_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(AppStyles.menu_dropdown_style())

        status_text = "🟢 Online" if self._is_online else "🟡 Offline"
        status_action = menu.addAction(f"Status: {status_text}")
        status_action.setEnabled(False)

        if self._is_authenticated:
            user_action = menu.addAction(f"👤 {self._user_name}")
            user_action.setEnabled(False)
            if self._email:
                email_action = menu.addAction(f"✉️ {self._email}")
                email_action.setEnabled(False)
            menu.addSeparator()
            refresh_action = menu.addAction("Verificar Conexão Agora")
            refresh_action.triggered.connect(self._trigger_heartbeat)
            logout_action = menu.addAction("Desconectar")
            logout_action.triggered.connect(self._do_logout)
        else:
            login_action = menu.addAction("Conectar ao Firebase...")
            login_action.triggered.connect(self._open_login_dialog)

        menu.exec(QCursor.pos())

    def _do_logout(self) -> None:
        FirebaseAuthService.sign_out()
        FirebaseCredentialManager.delete_credentials()
        self._refresh_state()

    def _open_login_dialog(self) -> None:
        from resources.widgets.dialogs.FirebaseLoginDialog import FirebaseLoginDialog
        dialog = FirebaseLoginDialog(parent=self.window())
        if dialog.exec():
            name, email, password = dialog.get_credentials()
            FirebaseCredentialManager.save_credentials(email, password, name)
            FirebaseAuthService.sign_in_with_email(email, password, name)

    def stop_heartbeat(self) -> None:
        """Para o timer e encerra worker em background."""
        if hasattr(self, "_timer") and self._timer.isActive():
            self._timer.stop()
        if self._heartbeat_worker is not None and self._heartbeat_worker.isRunning():
            self._heartbeat_worker.quit()
            self._heartbeat_worker.wait(1000)
