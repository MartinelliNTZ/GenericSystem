# -*- coding: utf-8 -*-
"""
FirebaseAuthWidget — Widget composto de login e estado do Firebase Auth
========================================================================
Encapsula formulário de autenticação (E-mail e Senha), exibição de status
da sessão na nuvem e botões de ação (Entrar/Desconectar). Executa o login
de forma assíncrona para manter a interface responsiva.
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseAuthService import FirebaseAuthService
from core.firebase.FirebaseWorker import FirebaseWorker
from core.manager.SignalManager import SignalManager
from resources.styles.AppStyles import AppStyles
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.simple.SimplePrimaryButton import SimplePrimaryButton
from utils.BaseUtil import BaseUtil
from utils.MessageBox import MessageBox


class FirebaseAuthWidget(QWidget):
    """Widget composto para autenticação e gestão de sessão Firebase."""

    auth_changed: Signal = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = BaseUtil._get_logger(ToolKey.FIREBASE.value, "FirebaseAuthWidget")
        self._worker: Optional[FirebaseWorker] = None
        self._build_ui()
        self._connect_signals()
        self._update_auth_state()

    def _build_ui(self) -> None:
        self.setObjectName("firebase_auth_widget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Status do usuário
        self._status_label = QLabel(self)
        self._status_label.setStyleSheet(
            f"color: {AppStyles.current_theme.TEXT_SECONDARY}; "
            f"font-size: {AppStyles.current_theme.FONT_SIZE_SMALL};"
        )
        layout.addWidget(self._status_label)

        # Grade de campos de entrada
        config = {
            "email": {
                "label": "E-mail:",
                "placeholder": "usuario@exemplo.com",
                "default": "",
            },
            "password": {
                "label": "Senha:",
                "placeholder": "••••••••",
                "default": "",
            },
        }
        self._grid_inputs = GridLineEdit(config, parent=self)
        self._grid_inputs.widget("password").setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._grid_inputs)

        # Barra de botões
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        self._btn_login = SimplePrimaryButton(
            text="Entrar",
            style_key="primary",
            parent=self,
        )
        self._btn_login.clicked.connect(self._on_login_clicked)
        btn_layout.addWidget(self._btn_login)

        self._btn_logout = SimplePrimaryButton(
            text="Desconectar",
            style_key="danger",
            parent=self,
        )
        self._btn_logout.clicked.connect(self._on_logout_clicked)
        btn_layout.addWidget(self._btn_logout)

        layout.addLayout(btn_layout)

    def _connect_signals(self) -> None:
        SignalManager.instance().cloud_auth_changed.connect(self._on_cloud_auth_changed)

    def _update_auth_state(self) -> None:
        is_auth = FirebaseAuthService.is_authenticated()
        user = FirebaseAuthService.get_current_user()

        if is_auth and user.get("email"):
            self._status_label.setText(f"Conectado como: <b>{user['email']}</b>")
            self._grid_inputs.setVisible(False)
            self._btn_login.setVisible(False)
            self._btn_logout.setVisible(True)
        else:
            self._status_label.setText("Status: <i>Não autenticado</i>")
            self._grid_inputs.setVisible(True)
            self._btn_login.setVisible(True)
            self._btn_logout.setVisible(False)

    def _on_login_clicked(self) -> None:
        email = self._grid_inputs.get("email").strip()
        password = self._grid_inputs.get("password")

        if not email or not password:
            MessageBox.show_warning("Por favor, preencha o e-mail e a senha.", parent=self)
            return

        self._btn_login.setEnabled(False)
        self._btn_login.setText("Conectando...")

        self._worker = FirebaseWorker(
            FirebaseAuthService.sign_in_with_email,
            email,
            password,
            parent=self,
        )
        self._worker.finished_with_result.connect(self._on_login_finished)
        self._worker.failed.connect(self._on_login_failed)
        self._worker.start()

    def _on_login_finished(self, result: Optional[dict]) -> None:
        self._btn_login.setEnabled(True)
        self._btn_login.setText("Entrar")
        if not result:
            MessageBox.show_error("Falha ao entrar. Verifique suas credenciais e conexão.", parent=self)
            return
        self._update_auth_state()
        self.auth_changed.emit(True)

    def _on_login_failed(self, error_msg: str) -> None:
        self._btn_login.setEnabled(True)
        self._btn_login.setText("Entrar")
        self._logger.error("Erro na autenticação assíncrona", code="FB_UI_AUTH_ERR", error=error_msg)
        MessageBox.show_error(f"Erro na autenticação: {error_msg}", parent=self)

    def _on_logout_clicked(self) -> None:
        FirebaseAuthService.sign_out()
        self._update_auth_state()
        self.auth_changed.emit(False)

    def _on_cloud_auth_changed(self, data: dict) -> None:
        self._update_auth_state()
