# -*- coding: utf-8 -*-
"""
FirebaseLoginDialog — Diálogo para entrada e confirmação de credenciais Firebase
================================================================================
Herda de BaseDialog e exibe campos estilizados com GridLineEdit.
Utilizado na primeira abertura de ferramentas integradas à nuvem.
"""

from __future__ import annotations

from typing import Tuple
from PySide6.QtWidgets import QLineEdit

from core.dialogs.BaseDialog import BaseDialog
from resources.widgets.grid.GridLineEdit import GridLineEdit
from utils.MessageBox import MessageBox


class FirebaseLoginDialog(BaseDialog):
    """Diálogo modal para captura e persistência de credenciais Firebase."""

    def __init__(
        self,
        default_name: str = "Matheus Martinelli",
        default_email: str = "martinelli.matheus0@gmail.com",
        default_password: str = "12345678",
        parent=None,
    ) -> None:
        self._default_name = default_name
        self._default_email = default_email
        self._default_password = default_password
        self._name = ""
        self._email = ""
        self._password = ""
        super().__init__(
            parent=parent,
            title="Autenticação Firebase",
            object_name="firebase_login_dialog",
            min_size=(420, 270),
            modal=True,
            has_appbar=True,
        )

    def _build_ui(self) -> None:
        self._add_title("Acesso ao Firebase")
        self._add_centered_text(
            "Informe suas credenciais para ativar o banco de dados em nuvem.\n"
            "As credenciais serão salvas de forma criptografada.",
            word_wrap=True,
        )

        config = {
            "name": {
                "label": "Nome:",
                "placeholder": "Seu nome completo",
                "default": self._default_name,
            },
            "email": {
                "label": "E-mail:",
                "placeholder": "usuario@exemplo.com",
                "default": self._default_email,
            },
            "password": {
                "label": "Senha:",
                "placeholder": "••••••••",
                "default": self._default_password,
            },
        }

        self._grid = GridLineEdit(config, parent=self)
        self._grid.widget("password").setEchoMode(QLineEdit.EchoMode.Password)
        self.main_layout.addWidget(self._grid)

        self._add_button_bar(["cancel", "save"])

    def accept(self) -> None:
        name = self._grid.get("name").strip()
        email = self._grid.get("email").strip()
        password = self._grid.get("password")

        if not name or not email or not password:
            MessageBox.show_warning("Por favor, preencha o nome, e-mail e a senha.", parent=self)
            return

        self._name = name
        self._email = email
        self._password = password
        super().accept()

    def get_credentials(self) -> Tuple[str, str, str]:
        """Retorna tupla com (nome, e-mail, senha)."""
        return self._name, self._email, self._password
