# -*- coding: utf-8 -*-
"""
FormLineEditDialog — Diálogo genérico de formulário (GridLineEdit)
==================================================================
Herda de ``BaseDialog`` (AppBar no topo) e monta um formulário de campos de
texto reutilizando ``GridLineEdit``, com validação de campos obrigatórios.
O consumidor informa a config no mesmo formato do ``GridLineEdit`` e recebe os
valores por ``values``.

Uso:
    from resources.widgets.dialogs.FormLineEditDialog import FormLineEditDialog

    dialog = FormLineEditDialog(
        config={"numero": {"label": "Número", "placeholder": "ex.: 39"}},
        title="Criar OS",
        required_keys=["numero"],
        parent=self,
    )
    if dialog.exec():
        valores = dialog.values  # {"numero": "39"}
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.dialogs.BaseDialog import BaseDialog
from resources.widgets.grid.GridLineEdit import GridLineEdit
from utils.MessageBox import MessageBox


class FormLineEditDialog(BaseDialog):
    """Diálogo genérico de formulário de campos de texto com validação.

    Args:
        config: Dicionário no formato aceito pelo ``GridLineEdit``.
        title: Título da janela e da AppBar.
        required_keys: Chaves que não podem ficar vazias para aceitar.
        ok_text: Texto do botão de confirmação.
        min_size: Tamanho mínimo do diálogo.
        parent: Widget pai.
    """

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        title: str = "Formulário",
        required_keys: Optional[List[str]] = None,
        ok_text: str = "Criar",
        min_size: tuple = (380, 300),
        parent=None,
    ) -> None:
        self._config = config
        self._required = list(required_keys or [])
        self._ok_text = ok_text
        self._values: Dict[str, str] = {}
        super().__init__(
            parent=parent,
            title=title,
            object_name="form_lineedit_dialog",
            min_size=min_size,
            modal=True,
            has_appbar=True,
        )

    def _build_ui(self) -> None:
        """Constrói o formulário e a barra de botões."""
        self._grid = GridLineEdit(self._config, parent=self)
        self.main_layout.addWidget(self._grid, 1)
        self._add_button_bar({
            "cancel": {"text": "Cancelar", "callback": self.reject},
            "ok": {"text": self._ok_text, "callback": self.accept},
        })

    @property
    def values(self) -> Dict[str, str]:
        """Retorna os valores informados após ``exec()`` retornar True."""
        return self._values

    def accept(self) -> None:
        """Coleta e valida os campos antes de aceitar."""
        values = {key: str(value).strip() for key, value in self._grid.values.items()}
        missing = [key for key in self._required if not values.get(key)]
        if missing:
            labels = ", ".join(
                self._config.get(key, {}).get("label", key) for key in missing
            )
            MessageBox.show_warning(
                f"Preencha os campos obrigatórios: {labels}",
                title="Formulário",
                parent=self,
            )
            return
        self._values = values
        super().accept()
