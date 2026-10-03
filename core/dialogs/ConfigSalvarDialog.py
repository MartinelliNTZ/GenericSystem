# -*- coding: utf-8 -*-
"""
ConfigSalvarDialog — Diálogo genérico para salvar configurações em JSON.
Uso: qualquer plugin que precise persistir configurações nomeadas.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from PySide6.QtWidgets import QDialog, QLabel, QLineEdit

from core.dialogs.BaseDialog import BaseDialog
from utils.MessageBox import MessageBox


class ConfigSalvarDialog(BaseDialog):
    """
    Diálogo para salvar dados JSON em um diretório.
    """

    def __init__(
        self,
        parent=None,
        title: str = "Salvar Configuração",
        placeholder: str = "Ex: config_padrao",
    ):
        self._placeholder = placeholder
        super().__init__(parent=parent, title=title, fixed_size=(400, 140), modal=True)

    def _build_ui(self):
        self.main_layout.addWidget(QLabel("Nome da configuração:"))

        self._edit_nome = QLineEdit()
        self._edit_nome.setPlaceholderText(self._placeholder)
        self.main_layout.addWidget(self._edit_nome)

        self._add_button_bar({
            "cancel": {"text": "Cancelar", "callback": self.reject},
            "save": {"text": "Salvar", "callback": self.accept},
        })

    @property
    def nome(self) -> str:
        """Nome digitado (sem extensão)."""
        return self._edit_nome.text().strip()

    @staticmethod
    def exec_save(
        config_dir: Path,
        data: Dict[str, Any],
        parent=None,
        title: str = "Salvar Configuração",
        placeholder: str = "Ex: config_padrao",
        logger: Optional[Any] = None,
        console_message_fn: Optional[Callable[[str], None]] = None,
        plugin_tag: str = "Plugin",
    ) -> Optional[str]:
        """
        Abre o diálogo e salva os dados se confirmado.
        """
        config_dir.mkdir(parents=True, exist_ok=True)

        dlg = ConfigSalvarDialog(
            parent=parent,
            title=title,
            placeholder=placeholder,
        )

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        nome = dlg.nome
        if not nome:
            MessageBox.show_warning("O nome não pode estar vazio.", title="Aviso")
            return None

        filepath = config_dir / f"{nome}.json"

        if filepath.exists():
            substituir = MessageBox.show_question(
                f"O arquivo '{nome}.json' já existe.\nDeseja substituir?",
                title="Substituir?",
            )
            if not substituir:
                return None

        data_to_save = dict(data)
        data_to_save["_saved_at"] = datetime.now().isoformat()

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

            if logger:
                logger.info("Config salva", code="CONFIG_SAVED", name=nome)
            if console_message_fn:
                console_message_fn(f"{plugin_tag} config salva: {nome}.json")

            MessageBox.show_info(
                f"Configuração '{nome}' salva com sucesso!",
                title="Salvo",
            )
            return nome

        except Exception as e:
            if logger:
                logger.error("Erro ao salvar config", code="CONFIG_SAVE_ERR", error=str(e))
            if console_message_fn:
                console_message_fn(f"{plugin_tag} erro ao salvar: {e}")
            MessageBox.show_error(f"Erro ao salvar configuração:\n{e}", title="Erro")
            return None