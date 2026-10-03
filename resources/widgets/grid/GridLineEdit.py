# -*- coding: utf-8 -*-
"""
GridLineEdit — Grade de campos de texto (QLineEdit) com labels
===============================================================
Agrupa múltiplos QLineEdit em um layout de grid, configurados
via dicionário. Suporta placeholder, valor padrão, tooltip e callback.

Configuração via dicionário:
    {
        "valor": {
            "label": "Valor",
            "description": "Texto a ser digitado",
            "default": "texto padrão",
            "placeholder": "Digite algo...",
        },
    }

Uso:
    grid = GridLineEdit(config)
    grid.values          # {"valor": "texto"}
    grid.get("valor")    # "texto"
    grid.set("valor", "novo texto")
    grid.set_values({"valor": "outro"})
    grid.changed.connect(self._on_value_changed)
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QLineEdit,
)
from PySide6.QtCore import Signal


class GridLineEdit(QWidget):
    """
    Grade de QLineEdit configurados por dicionário.
    Widget compacto — sem QScrollArea para evitar expansão vertical indesejada.

    Sinais:
        changed(key, value) — emitido quando qualquer campo muda
    """

    changed = Signal(str, str)

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._line_edits: Dict[str, QLineEdit] = {}
        self.setObjectName("grid_lineedit")

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)
        self._grid.setColumnStretch(1, 1)

        self._build()

    def _build(self):
        """Constrói a grade de line edits a partir do config."""
        row = 0
        for key, item in self._config.items():
            label_text = item.get("label", key)
            description = item.get("description", "")
            default = item.get("default", "")
            placeholder = item.get("placeholder", "")

            # Label
            lbl = QLabel(label_text)
            lbl.setObjectName("grid_le_label")
            if description:
                lbl.setToolTip(description)
            self._grid.addWidget(lbl, row, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            # Line edit
            le = QLineEdit()
            le.setObjectName("grid_lineedit")
            le.setText(str(default))
            if placeholder:
                le.setPlaceholderText(placeholder)
            if description:
                le.setToolTip(description)

            le.textChanged.connect(lambda text, k=key: self._on_changed(k, text))
            self._line_edits[key] = le
            self._grid.addWidget(le, row, 1)

            row += 1

        # Preenche final com stretch para absorver espaço vertical extra
        if row > 0:
            self._grid.setRowStretch(row, 1)

    def _on_changed(self, key: str, text: str):
        """Propaga mudança."""
        self.changed.emit(key, text)

    def widget(self, key: str) -> QLineEdit:
        """
        Retorna o QLineEdit subjacente para acesso direto (compatibilidade).

        Args:
            key: Chave do campo configurado no construtor

        Returns:
            QLineEdit interno

        Raises:
            KeyError: se a chave não existir
        """
        le = self._line_edits.get(key)
        if le is None:
            raise KeyError(f"Campo '{key}' não encontrado no GridLineEdit")
        return le

    # ── Propriedades públicas ────────────────────────────────────────

    @property
    def values(self) -> Dict[str, str]:
        """Retorna dict com todos os valores atuais."""
        result = {}
        for key, le in self._line_edits.items():
            result[key] = le.text()
        return result

    def get(self, key: str) -> str:
        """Retorna o valor de um campo específico."""
        le = self._line_edits.get(key)
        if le is not None:
            return le.text()
        raise KeyError(f"Campo '{key}' não encontrado no GridLineEdit")

    def set(self, key: str, value: str, block_signals: bool = False):
        """Define o valor de um campo específico."""
        le = self._line_edits.get(key)
        if le is not None:
            if block_signals:
                le.blockSignals(True)
            le.setText(value)
            if block_signals:
                le.blockSignals(False)
        else:
            raise KeyError(f"Campo '{key}' não encontrado no GridLineEdit")

    def set_values(self, values: Dict[str, str], block_signals: bool = True):
        """
        Define múltiplos valores de uma vez.

        Args:
            values: Dict no formato {"key": value}
            block_signals: Se True, emite 'changed' uma única vez no final
        """
        if block_signals:
            for le in self._line_edits.values():
                le.blockSignals(True)

        for key, value in values.items():
            le = self._line_edits.get(key)
            if le is not None:
                le.setText(value)

        if block_signals:
            for le in self._line_edits.values():
                le.blockSignals(False)
            keys = list(values.keys())
            if keys:
                self.changed.emit(keys[0], values[keys[0]])