# -*- coding: utf-8 -*-
"""
GridCheckBox — Grade de checkboxes organizados em colunas
===========================================================
Exibe checkboxes para cada item de um dicionário, organizados
em um número configurável de colunas.

Configuração via dicionário:
    {
        ".ext": {
            "label": ".txt",
            "description": "Tooltip explicativo",
            "default": True
        },
        ...
    }

Uso:
    grid = GridCheckBox(config_dict, num_columns=4)
    checked = grid.checked     # só os True
    unchecked = grid.unchecked # só os False
    all_states = grid.all      # todos com estado atual
    grid.set_all(all_states)   # restaura estados
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QCheckBox, QLabel, QSizePolicy,
)
from PySide6.QtCore import Signal


class GridCheckBox(QWidget):
    """
    Grade de checkboxes configurados por dicionário.
    Widget compacto — sem QScrollArea para evitar expansão vertical indesejada.

    Sinais:
        changed — emitido quando qualquer checkbox muda de estado
    """

    changed = Signal()

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        num_columns: int = 4,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._num_columns = max(1, num_columns)
        self._checkboxes: Dict[str, QCheckBox] = {}
        self.setObjectName("grid_checkbox")

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setSpacing(2)

        self._build()

    def _build(self):
        """Constrói a grade de checkboxes a partir do config."""
        keys = list(self._config.keys())
        if not keys:
            lbl = QLabel("Nenhum item disponível.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("grid_empty_label")
            self._grid.addWidget(lbl, 0, 0)
            return

        row = 0
        col = 0
        for key in keys:
            item = self._config[key]
            label = item.get("label", key)
            desc = item.get("description", "")
            default = item.get("default", True)

            cb = QCheckBox(label)
            cb.setChecked(default)
            cb.setObjectName("grid_cb")
            if desc:
                cb.setToolTip(desc)
            cb.stateChanged.connect(self._on_changed)
            self._checkboxes[key] = cb

            self._grid.addWidget(cb, row, col, Qt.AlignmentFlag.AlignLeft)

            col += 1
            if col >= self._num_columns:
                col = 0
                row += 1

        # Row stretch absorve espaço vertical extra sem criar linha visível
        stretch_row = row + (1 if col > 0 else 0)
        if keys:
            self._grid.setRowStretch(stretch_row, 1)

    def _on_changed(self):
        """Propaga mudança."""
        self.changed.emit()

    def widget(self, key: str) -> QCheckBox:
        """
        Retorna o QCheckBox subjacente (compatibilidade).

        Args:
            key: Chave do checkbox

        Returns:
            QCheckBox interno

        Raises:
            KeyError: se a chave não existir
        """
        cb = self._checkboxes.get(key)
        if cb is None:
            raise KeyError(f"Checkbox '{key}' não encontrado no GridCheckBox")
        return cb

    # ── Propriedades públicas ────────────────────────────────────────

    @property
    def checked(self) -> Dict[str, bool]:
        """Retorna dict apenas com os itens que estão checados (True)."""
        result = {}
        for key, cb in self._checkboxes.items():
            if cb.isChecked():
                result[key] = True
        return result

    @property
    def unchecked(self) -> Dict[str, bool]:
        """Retorna dict apenas com os itens que estão deschecados (False)."""
        result = {}
        for key, cb in self._checkboxes.items():
            if not cb.isChecked():
                result[key] = False
        return result

    @property
    def all(self) -> Dict[str, bool]:
        """Retorna dict com todos os itens e seus estados atuais."""
        result = {}
        for key, cb in self._checkboxes.items():
            result[key] = cb.isChecked()
        return result

    def set_all(self, states: Dict[str, bool]):
        """
        Restaura o estado de todos os checkboxes a partir de um dict.

        Args:
            states: Dict no formato { "key": True/False }
                    Itens não presentes no config são ignorados.
        """
        for key, checked in states.items():
            cb = self._checkboxes.get(key)
            if cb is not None:
                cb.blockSignals(True)
                cb.setChecked(bool(checked))
                cb.blockSignals(False)
        self.changed.emit()

    def set_checked(self, key: str, checked: bool):
        """Define o estado de um checkbox específico."""
        cb = self._checkboxes.get(key)
        if cb is not None:
            cb.setChecked(checked)

    def is_item_checked(self, key: str) -> bool:
        """Retorna True se o item está checado."""
        cb = self._checkboxes.get(key)
        return cb.isChecked() if cb else False