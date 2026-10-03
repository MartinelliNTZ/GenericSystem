# -*- coding: utf-8 -*-
"""
GridSlider — Grade de sliders horizontais com label e valor numérico
=====================================================================
Widget genérico e reutilizável que agrupa múltiplos sliders em grid,
cada um com label, QSlider horizontal e label de valor.

Configuração via dicionário:
    {
        "quality": {
            "label": "Qualidade:",
            "default": 95,
            "min": 1,
            "max": 100,
            "step": 1,
            "suffix": "%",
            "description": "Qualidade para formatos lossy",
        },
    }

Uso:
    slider = GridSlider(config)
    slider.values          # {"quality": 95}
    slider.get("quality")  # 95
    slider.set("quality", 80)
    slider.set_on_changed("quality", self._on_quality_changed)
    slider.set_enabled("quality", False)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QSlider, QHBoxLayout, QSizePolicy,
)


class GridSlider(QWidget):
    """
    Grade de sliders horizontais configurados por dicionário.

    Cada slider possui:
    - Label à esquerda
    - QSlider horizontal no centro
    - Label de valor à direita (com sufixo opcional)

    A comunicação com o plugin é via callbacks (set_on_changed),
    não via Signals do PySide6 (conforme SKILL_COMUNICATION.md).
    """

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        columns: int = 1,
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._sliders: Dict[str, QSlider] = {}
        self._value_labels: Dict[str, QLabel] = {}
        self._callbacks: Dict[str, Optional[Callable[[str, int], None]]] = {}
        self._columns = max(1, columns)
        self.setObjectName("grid_slider")

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)

        self._build()

    def _build(self):
        """Constrói a grade de sliders a partir do config em N colunas."""
        for idx, (key, item) in enumerate(self._config.items()):
            label_text = item.get("label", key)
            description = item.get("description", "")
            default = item.get("default", 50)
            min_val = item.get("min", 0)
            max_val = item.get("max", 100)
            step = item.get("step", 1)
            suffix = item.get("suffix", "")

            if self._columns > 1:
                col_pair = idx % self._columns
                row = idx // self._columns
                col_start = col_pair * 3
                col_slider = col_pair * 3 + 1
                col_value = col_pair * 3 + 2
            else:
                row = idx
                col_start = 0
                col_slider = 1
                col_value = 2

            # Label
            lbl = QLabel(label_text)
            lbl.setObjectName("grid_slider_label")
            if description:
                lbl.setToolTip(description)
            self._grid.addWidget(
                lbl, row, col_start,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            )

            # Slider
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            slider.setSingleStep(step)
            slider.setPageStep(step * 10)
            slider.setObjectName("grid_slider_h")
            if description:
                slider.setToolTip(description)
            slider.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            slider.valueChanged.connect(lambda val, k=key: self._on_changed(k, val))
            self._sliders[key] = slider

            # Container do slider (para controlar altura)
            slider_container = QHBoxLayout()
            slider_container.setContentsMargins(0, 0, 0, 0)
            slider_container.addWidget(slider)
            self._grid.addLayout(slider_container, row, col_slider)

            # Label de valor
            val_lbl = QLabel(f"{default}{suffix}")
            val_lbl.setObjectName("grid_slider_value")
            val_lbl.setFixedWidth(60)
            val_lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )
            if description:
                val_lbl.setToolTip(description)
            self._value_labels[key] = val_lbl
            self._grid.addWidget(
                val_lbl, row, col_value,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            )

        # Stretch nas colunas
        if self._columns > 1:
            total_cols = self._columns * 3
            for c in range(total_cols):
                if c % 3 == 0:
                    self._grid.setColumnStretch(c, 0)       # label — fixo
                elif c % 3 == 1:
                    self._grid.setColumnStretch(c, 1)       # slider — expande
                else:
                    self._grid.setColumnStretch(c, 0)       # valor — fixo
            num_rows = (len(self._config) + self._columns - 1) // self._columns
            self._grid.setRowStretch(num_rows, 1)
        else:
            self._grid.setColumnStretch(0, 0)   # label
            self._grid.setColumnStretch(1, 1)   # slider
            self._grid.setColumnStretch(2, 0)   # valor
            self._grid.setRowStretch(len(self._config), 1)

    def _on_changed(self, key: str, value: int):
        """Atualiza label de valor e dispara callback."""
        suffix = self._config.get(key, {}).get("suffix", "")
        val_lbl = self._value_labels.get(key)
        if val_lbl:
            val_lbl.setText(f"{value}{suffix}")

        callback = self._callbacks.get(key)
        if callback and callable(callback):
            callback(key, value)

    # ── API Pública ─────────────────────────────────────────────────

    @property
    def values(self) -> Dict[str, int]:
        """Retorna dict com todos os valores atuais."""
        return {key: slider.value() for key, slider in self._sliders.items()}

    def get(self, key: str) -> int:
        """Retorna o valor de um slider específico."""
        slider = self._sliders.get(key)
        if slider is not None:
            return slider.value()
        raise KeyError(f"Campo '{key}' não encontrado no GridSlider")

    def set(self, key: str, value: int, block_callbacks: bool = False):
        """Define o valor de um slider específico."""
        slider = self._sliders.get(key)
        if slider is not None:
            if block_callbacks:
                slider.blockSignals(True)
            slider.setValue(value)
            # Atualiza label mesmo com signals bloqueados
            suffix = self._config.get(key, {}).get("suffix", "")
            val_lbl = self._value_labels.get(key)
            if val_lbl:
                val_lbl.setText(f"{value}{suffix}")
            if block_callbacks:
                slider.blockSignals(False)
        else:
            raise KeyError(f"Campo '{key}' não encontrado no GridSlider")

    def set_enabled(self, key: str, enabled: bool) -> None:
        """Habilita/desabilita o slider de uma chave específica."""
        slider = self._sliders.get(key)
        if slider is not None:
            slider.setEnabled(enabled)
            # Desabilita também o label de valor
            val_lbl = self._value_labels.get(key)
            if val_lbl:
                val_lbl.setEnabled(enabled)

    def set_on_changed(self, key: str, callback: Callable[[str, int], None]) -> None:
        """
        Define o callback para quando o slider mudar.

        Args:
            key: Chave do campo
            callback: Função que recebe (key, value)
        """
        self._callbacks[key] = callback

    def set_values(self, values: Dict[str, int], block_callbacks: bool = True):
        """
        Define múltiplos valores de uma vez.

        Args:
            values: Dict no formato {"key": value}
            block_callbacks: Se True, não dispara callbacks individuais
        """
        if block_callbacks:
            for key in self._sliders:
                self._sliders[key].blockSignals(True)

        for key, value in values.items():
            slider = self._sliders.get(key)
            if slider is not None:
                slider.setValue(value)
                suffix = self._config.get(key, {}).get("suffix", "")
                val_lbl = self._value_labels.get(key)
                if val_lbl:
                    val_lbl.setText(f"{value}{suffix}")

        if block_callbacks:
            for key in self._sliders:
                self._sliders[key].blockSignals(False)