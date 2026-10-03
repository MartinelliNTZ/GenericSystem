# -*- coding: utf-8 -*-
"""
GridDoubleSpinBox — Grade de campos numéricos (QDoubleSpinBox) com labels
==========================================================================
Agrupa múltiplos campos numéricos em um layout de grid, configurados
via dicionário. Suporta inteiros (decimal=0) e floats, valor padrão,
mínimo, máximo, step, tooltip e callback onchanged.

Configuração via dicionário:
    {
        "intervalo": {
            "label": "Intervalo (s)",
            "description": "Intervalo entre execuções",
            "decimal": 1,
            "default": 1.0,
            "min": 0.0,
            "max": 999.0,
            "step": 0.1,
            "prefix": "",      # opcional, texto antes do valor
            "suffix": "s",     # opcional, texto depois do valor
        },
        "repeticoes": {
            "label": "Repetições",
            "description": "Número de vezes",
            "decimal": 0,       # 0 = inteiro (QSpinBox internally)
            "default": 3,
            "min": 1,
            "max": 9999,
        },
    }

Uso:
    grid = GridDoubleSpinBox(config)
    grid.values          # {"intervalo": 1.0, "repeticoes": 3}
    grid.set_values({"intervalo": 2.5})
    grid.get("intervalo")   # 1.0
    grid.set("repeticoes", 5)
    grid.changed.connect(self._on_value_changed)
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox,
    QHBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Signal


class GridDoubleSpinBox(QWidget):
    """
    Grade de campos numéricos (QDoubleSpinBox) configurados por dicionário.
    Widget compacto — sem QScrollArea para evitar expansão vertical indesejada.

    Sinais:
        changed(key, value) — emitido quando qualquer spin box muda de valor
    """

    changed = Signal(str, float)

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        columns: int = 1,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._spinboxes: Dict[str, QDoubleSpinBox | QSpinBox] = {}
        self._columns = max(1, columns)
        self.setObjectName("grid_doublespinbox")

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)

        self._build()

    def _build(self):
        """Constrói a grade de spin boxes a partir do config em N colunas."""
        for idx, (key, item) in enumerate(self._config.items()):
            label_text = item.get("label", key)
            description = item.get("description", "")
            decimal = item.get("decimal", 1)
            default = item.get("default", 0.0)
            min_val = item.get("min", 0.0)
            max_val = item.get("max", 999999.0)
            step = item.get("step", 1.0 if decimal == 0 else 0.01)
            prefix = item.get("prefix", "")
            suffix = item.get("suffix", "")

            if self._columns > 1:
                # Layout multi-coluna
                col_pair = idx % self._columns          # 0, 1, 2...
                row = idx // self._columns               # linha base
                col_start = col_pair * 2                 # label ocupa esta col
                col_value = col_pair * 2 + 1             # value ocupa esta col
            else:
                # Layout vertical (1 coluna)
                row = idx
                col_start = 0
                col_value = 1

            # Label
            lbl = QLabel(label_text)
            lbl.setObjectName("grid_dsb_label")
            if description:
                lbl.setToolTip(description)
            self._grid.addWidget(lbl, row, col_start, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            # Spin box container (value + suffix)
            spin_container = QHBoxLayout()
            spin_container.setContentsMargins(0, 0, 0, 0)
            spin_container.setSpacing(2)

            if decimal == 0:
                spin = QSpinBox()
                spin.setRange(int(min_val), int(max_val))
                spin.setValue(int(default))
                spin.setSingleStep(int(step) if step >= 1 else 1)
                spin.setObjectName("grid_spinbox_int")
            else:
                spin = QDoubleSpinBox()
                spin.setRange(float(min_val), float(max_val))
                spin.setValue(float(default))
                spin.setDecimals(decimal)
                spin.setSingleStep(float(step))
                spin.setObjectName("grid_spinbox_float")

            spin.setFixedWidth(100)
            spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if description:
                spin.setToolTip(description)

            spin.valueChanged.connect(lambda val, k=key: self._on_changed(k, val))
            self._spinboxes[key] = spin
            spin_container.addWidget(spin)

            if suffix:
                suffix_lbl = QLabel(suffix)
                suffix_lbl.setObjectName("grid_dsb_suffix")
                spin_container.addWidget(suffix_lbl)

            if prefix:
                prefix_lbl = QLabel(prefix)
                prefix_lbl.setObjectName("grid_dsb_prefix")
                spin_container.insertWidget(0, prefix_lbl)

            self._grid.addLayout(spin_container, row, col_value, Qt.AlignmentFlag.AlignLeft)

        # Define stretch nas colunas pares (label) e ímpares (value)
        if self._columns > 1:
            for c in range(self._columns * 2):
                if c % 2 == 0:
                    self._grid.setColumnStretch(c, 0)      # label — fixo
                else:
                    self._grid.setColumnStretch(c, 1)      # value — expande

            num_rows = (len(self._config) + self._columns - 1) // self._columns
            self._grid.setRowStretch(num_rows, 1)
        else:
            self._grid.setColumnStretch(1, 1)
            self._grid.setRowStretch(len(self._config), 1)

    def _on_changed(self, key: str, value: float):
        """Propaga mudança."""
        # Callback opcional do config
        onchanged = self._config.get(key, {}).get("onchanged")
        if onchanged and callable(onchanged):
            onchanged(value)
        self.changed.emit(key, value)

    def widget(self, key: str) -> QDoubleSpinBox | QSpinBox:
        """
        Retorna o spin box subjacente para acesso direto (compatibilidade).

        Args:
            key: Chave do campo configurado no construtor

        Returns:
            QDoubleSpinBox ou QSpinBox interno

        Raises:
            KeyError: se a chave não existir
        """
        spin = self._spinboxes.get(key)
        if spin is None:
            raise KeyError(f"Campo '{key}' não encontrado no GridDoubleSpinBox")
        return spin

    # ── Propriedades públicas ────────────────────────────────────────

    @property
    def values(self) -> Dict[str, float]:
        """Retorna dict com todos os valores atuais."""
        result = {}
        for key, spin in self._spinboxes.items():
            result[key] = spin.value()
        return result

    def get(self, key: str) -> float:
        """Retorna o valor de um campo específico."""
        spin = self._spinboxes.get(key)
        if spin is not None:
            return spin.value()
        raise KeyError(f"Campo '{key}' não encontrado no GridDoubleSpinBox")

    def set(self, key: str, value: float, block_signals: bool = False):
        """Define o valor de um campo específico."""
        spin = self._spinboxes.get(key)
        if spin is not None:
            if block_signals:
                spin.blockSignals(True)
            spin.setValue(value)
            if block_signals:
                spin.blockSignals(False)
        else:
            raise KeyError(f"Campo '{key}' não encontrado no GridDoubleSpinBox")

    def set_enabled(self, key: str, enabled: bool) -> None:
        """
        Habilita/desabilita o spin box de uma chave específica.

        Args:
            key: Chave do campo.
            enabled: True para habilitar, False para desabilitar.
        """
        spin = self._spinboxes.get(key)
        if spin is not None:
            spin.setEnabled(enabled)

    def set_values(self, values: Dict[str, float], block_signals: bool = True):
        """
        Define múltiplos valores de uma vez.

        Args:
            values: Dict no formato {"key": value}
            block_signals: Se True, emite 'changed' uma única vez no final
        """
        if block_signals:
            for key in self._spinboxes:
                self._spinboxes[key].blockSignals(True)

        for key, value in values.items():
            spin = self._spinboxes.get(key)
            if spin is not None:
                spin.setValue(value)

        if block_signals:
            for key in self._spinboxes:
                self._spinboxes[key].blockSignals(False)
            # Emite uma única vez com o primeiro valor
            keys = list(values.keys())
            if keys:
                self.changed.emit(keys[0], values[keys[0]])