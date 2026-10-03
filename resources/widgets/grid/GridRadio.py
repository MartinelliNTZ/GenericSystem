# -*- coding: utf-8 -*-
"""
GridRadio — Grade de radio buttons organizados em colunas
===========================================================
Exibe radio buttons para cada item de um dicionario, organizados
em um numero configuravel de colunas. Similar ao GridCheckBox,
mas com radio buttons (selecao unica).

Configuracao via dicionario:
    {
        "single": {
            "label": "Arquivo Unico",
            "description": "Processa 1 MRK com 1 arquivo de dados",
            "default": True,
            "tooltip": "Seleciona modo de arquivo unico",
        },
        "batch": {
            "label": "Lote por Pasta",
            "description": "Busca MRKs e dados correspondentes em pasta",
            "default": False,
            "tooltip": "Seleciona modo de lote por pasta",
        },
    }

Uso:
    grid = GridRadio(config, num_columns=3)
    selected = grid.selected       # "single" (chave do selecionado)
    grid.set_selected("batch")
    grid.changed.connect(self._on_radio_changed)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QLabel,
    QRadioButton,
    QWidget,
)


class GridRadio(QWidget):
    """
    Grade de radio buttons configurados por dicionario.

    Sinais:
        changed(key) — emitido quando a selecao muda (key = chave do selecionado)
    """

    changed = Signal(str)

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        num_columns: int = 3,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._config = config
        self._num_columns = max(1, num_columns)
        self._buttons: Dict[str, QRadioButton] = {}
        self._group = QButtonGroup(self)
        self._group.buttonClicked.connect(self._on_changed)
        self.setObjectName("grid_radio")

        self._build()

    def _build(self):
        """Constroi a grade de radio buttons a partir do config."""
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(2, 2, 2, 2)
        self._grid.setSpacing(4)

        keys = list(self._config.keys())
        if not keys:
            lbl = QLabel("Nenhuma opcao disponivel.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("grid_empty_label")
            self._grid.addWidget(lbl, 0, 0)
            return

        num_items = len(keys)

        # Calcula colunas dinamicamente
        if num_items < self._num_columns:
            cols = num_items
        else:
            cols = self._num_columns

        rows = (num_items + cols - 1) // cols

        # Configura stretches iguais para colunas
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)

        row = 0
        col = 0
        first_key = None

        for idx, key in enumerate(keys):
            if first_key is None:
                first_key = key

            item = self._config[key]
            label = item.get("label", key)
            desc = item.get("description", "")
            tooltip = item.get("tooltip", "")
            default = item.get("default", False)

            rb = QRadioButton(label)
            rb.setToolTip(tooltip or desc)
            if desc and not tooltip:
                rb.setToolTip(desc)
            rb.setObjectName("grid_radio_btn")
            self._buttons[key] = rb
            self._group.addButton(rb)

            # Configura default
            if default:
                rb.setChecked(True)
            elif idx == 0 and not any(v.get("default") for v in self._config.values()):
                rb.setChecked(True)

            self._grid.addWidget(rb, row, col, Qt.AlignmentFlag.AlignLeft)

            col += 1
            if col >= cols:
                col = 0
                row += 1

        # Row stretch absorve espaco vertical extra
        stretch_row = row + (1 if col > 0 else 0)
        if keys:
            self._grid.setRowStretch(stretch_row, 1)

    def _on_changed(self, button: QRadioButton):
        """Propaga mudanca de selecao."""
        for key, rb in self._buttons.items():
            if rb is button:
                self.changed.emit(key)
                return

    # ── Propriedades publicas ────────────────────────────────────────

    @property
    def selected(self) -> Optional[str]:
        """
        Retorna a chave do radio button atualmente selecionado,
        ou None se nenhum estiver selecionado.
        """
        for key, rb in self._buttons.items():
            if rb.isChecked():
                return key
        return None

    @property
    def selected_text(self) -> Optional[str]:
        """
        Retorna o label do radio button atualmente selecionado,
        ou None se nenhum estiver selecionado.
        """
        key = self.selected
        if key and key in self._config:
            return self._config[key].get("label", key)
        return None

    def set_selected(self, key: str):
        """
        Define programaticamente o radio button selecionado.

        Args:
            key: Chave do item a selecionar.

        Raises:
            KeyError: se a chave nao existir.
        """
        rb = self._buttons.get(key)
        if rb is None:
            raise KeyError(f"Radio button '{key}' nao encontrado no GridRadio")
        rb.setChecked(True)
        self.changed.emit(key)

    def widget(self, key: str) -> QRadioButton:
        """
        Retorna o QRadioButton subjacente.

        Args:
            key: Chave do radio button

        Returns:
            QRadioButton interno

        Raises:
            KeyError: se a chave nao existir
        """
        rb = self._buttons.get(key)
        if rb is None:
            raise KeyError(f"Radio button '{key}' nao encontrado no GridRadio")
        return rb

    @property
    def keys(self) -> list:
        """Retorna lista de chaves dos radio buttons."""
        return list(self._buttons.keys())