# -*- coding: utf-8 -*-
"""
CheckBoxSelectDialog — Diálogo genérico de seleção múltipla por checkboxes
==========================================================================
Herda de BaseDialog e exibe uma grade de checkboxes (`GridCheckBox`).
O consumidor informa os itens pelo mesmo dicionário aceito pelo GridCheckBox
e recebe as chaves marcadas via `selected_keys`.

Uso:
    from resources.widgets.dialogs.CheckBoxSelectDialog import CheckBoxSelectDialog

    dialog = CheckBoxSelectDialog(
        config={"2019": {"label": "2019"}, "2020": {"label": "2020"}},
        title="Selecionar anos",
        num_columns=3,
        parent=self,
    )
    if dialog.exec():
        selecionados = dialog.selected_keys  # ["2020", ...]
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.dialogs.BaseDialog import BaseDialog
from resources.widgets.grid.GridCheckBox import GridCheckBox


class CheckBoxSelectDialog(BaseDialog):
    """Diálogo genérico de seleção múltipla via checkboxes.

    Args:
        config: Dicionário no formato aceito pelo GridCheckBox.
        title: Título da janela e da AppBar.
        num_columns: Número de colunas da grade de checkboxes.
        parent: Widget pai.
    """

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        title: str = "Seleção",
        num_columns: int = 3,
        parent=None,
    ) -> None:
        self._config = config
        self._num_columns = num_columns
        self._selected: List[str] = []
        super().__init__(
            parent=parent,
            title=title,
            object_name="checkbox_select_dialog",
            min_size=(360, 260),
            modal=True,
            has_appbar=True,
        )

    def _build_ui(self) -> None:
        """Constrói a grade de checkboxes e a barra de botões."""
        self._grid = GridCheckBox(self._config, num_columns=self._num_columns)
        self.main_layout.addWidget(self._grid, 1)
        self._add_button_bar({
            "cancel": {"text": "Cancelar", "callback": self.reject},
            "ok": {"text": "Criar", "callback": self.accept},
        })

    @property
    def selected_keys(self) -> List[str]:
        """Retorna as chaves marcadas após ``exec()`` retornar True."""
        return self._selected

    def accept(self) -> None:
        """Coleta as chaves marcadas antes de aceitar (exige ao menos 1)."""
        self._selected = list(self._grid.checked.keys())
        if not self._selected:
            return
        super().accept()
