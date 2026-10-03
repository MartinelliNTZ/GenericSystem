# -*- coding: utf-8 -*-
"""
GridFieldMapping — Grade de mapeamento de campos configuravel por dicionario
==============================================================================
Cada linha: [QCheckBox] [QLabel: from_label] [QLineEdit: campo_origem] [QLabel: to_label] [QLineEdit: campo_destino]

Checkbox unchecked = linha toda inativa (disabled visual).
Checkbox checked = campos editaveis.

Widget generico — nao contem logica de negocios, apenas exibicao.
Usa Signal proprio (PySide6) para notificar mudancas (Contrato 24).

Uso:
    config = {
        "altitude": {
            "from_label": "Campo Origem:",
            "from_placeholder": "Ex: AbsZ",
            "to_label": "Campo MRK:",
            "to_placeholder": "Ex: Ellh",
            "default_from": "AbsZ",
            "default_to": "Ellh",
            "default_enabled": True,
            "tooltip": "Mapeamento de altitude",
        },
    }
    grid = GridFieldMapping(config)
    grid.values      # {"altitude": {"from": "AbsZ", "to": "Ellh", "enabled": True}}
    grid.all         # dict completo, inclusive inativos
    grid.set_values({"altitude": {"from": "Novo", "to": "Ellh", "enabled": False}})
    grid.changed.connect(self._on_mapping_changed)
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QWidget,
    QSizePolicy,
)


class GridFieldMapping(QWidget):
    """
    Grade configuravel de mapeamento de campos.
    Cada linha: checkbox + label_from + lineedit_from + label_to + lineedit_to.

    Sinais:
        changed(key, values) — emitido quando qualquer campo ou checkbox muda.
            key: str — chave do item
            values: dict — {"from": str, "to": str, "enabled": bool}
    """

    changed = Signal(str, dict)  # key, {"from": str, "to": str, "enabled": bool}

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._config = config
        self._rows: Dict[str, dict] = {}  # key -> {checkbox, from_label, from_edit, to_label, to_edit}
        self.setObjectName("grid_field_mapping")

        self._build()

    def _build(self):
        """Constroi a grade interna com QGridLayout."""
        # Scroll area para suportar muitos itens
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setObjectName("grid_field_mapping_scroll")

        container = QWidget()
        container.setObjectName("grid_field_mapping_container")
        grid = QGridLayout(container)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 0)  # checkbox
        grid.setColumnStretch(1, 0)  # from_label
        grid.setColumnStretch(2, 1)  # from_edit (stretch)
        grid.setColumnStretch(3, 0)  # to_label
        grid.setColumnStretch(4, 1)  # to_edit (stretch)

        keys = list(self._config.keys())
        if not keys:
            lbl = QLabel("Nenhum mapeamento configurado.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("grid_empty_label")
            grid.addWidget(lbl, 0, 0, 1, 5)
        else:
            for row_idx, key in enumerate(keys):
                item = self._config[key]
                tooltip = item.get("tooltip", "")

                # Checkbox
                cb = QCheckBox()
                cb.setChecked(item.get("default_enabled", True))
                cb.setToolTip(tooltip)
                cb.stateChanged.connect(lambda checked, k=key: self._on_checkbox_changed(k, checked))
                grid.addWidget(cb, row_idx, 0, Qt.AlignmentFlag.AlignCenter)

                # From label
                from_lbl = QLabel(item.get("from_label", "Origem:"))
                from_lbl.setToolTip(tooltip)
                from_lbl.setObjectName("grid_field_label")
                grid.addWidget(from_lbl, row_idx, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # From line edit
                from_edit = QLineEdit()
                from_edit.setPlaceholderText(item.get("from_placeholder", ""))
                from_edit.setText(item.get("default_from", ""))
                from_edit.setToolTip(tooltip)
                from_edit.setObjectName("grid_field_edit")
                from_edit.textChanged.connect(lambda text, k=key: self._on_field_changed(k))
                grid.addWidget(from_edit, row_idx, 2)

                # To label
                to_lbl = QLabel(item.get("to_label", "MRK:"))
                to_lbl.setToolTip(tooltip)
                to_lbl.setObjectName("grid_field_label")
                grid.addWidget(to_lbl, row_idx, 3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # To line edit
                to_edit = QLineEdit()
                to_edit.setPlaceholderText(item.get("to_placeholder", ""))
                to_edit.setText(item.get("default_to", ""))
                to_edit.setToolTip(tooltip)
                to_edit.setObjectName("grid_field_edit")
                to_edit.textChanged.connect(lambda text, k=key: self._on_field_changed(k))
                grid.addWidget(to_edit, row_idx, 4)

                # Store references
                self._rows[key] = {
                    "checkbox": cb,
                    "from_label": from_lbl,
                    "from_edit": from_edit,
                    "to_label": to_lbl,
                    "to_edit": to_edit,
                }

                # Apply initial enabled state
                self._apply_row_enabled(key, cb.isChecked())

        # Stretch row at bottom
        if keys:
            grid.setRowStretch(len(keys), 1)

        scroll.setWidget(container)

        # Outer layout: scroll area fills the widget
        outer = QGridLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll, 0, 0)

    # ── Estado interno ───────────────────────────────────────────────

    def _apply_row_enabled(self, key: str, enabled: bool):
        """Habilita/desabilita todos os widgets de uma linha (exceto checkbox)."""
        row = self._rows.get(key)
        if not row:
            return
        row["from_label"].setEnabled(enabled)
        row["from_edit"].setEnabled(enabled)
        row["to_label"].setEnabled(enabled)
        row["to_edit"].setEnabled(enabled)

    def _on_checkbox_changed(self, key: str, state: int):
        """Checkbox mudou — atualiza estado visual e emite sinal."""
        enabled = bool(state)
        self._apply_row_enabled(key, enabled)
        self._emit_changed(key)

    def _on_field_changed(self, key: str):
        """Campo de texto mudou — emite sinal."""
        self._emit_changed(key)

    def _emit_changed(self, key: str):
        """Emite sinal changed com estado atual do item."""
        values = self.get(key)
        self.changed.emit(key, values)

    # ── API Publica ──────────────────────────────────────────────────

    @property
    def values(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna dict apenas com mapeamentos ativos (enabled=True).

        Returns:
            {"chave": {"from": str, "to": str, "enabled": True}, ...}
        """
        result = {}
        for key, row in self._rows.items():
            if row["checkbox"].isChecked():
                result[key] = {
                    "from": row["from_edit"].text(),
                    "to": row["to_edit"].text(),
                    "enabled": True,
                }
        return result

    @property
    def all(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna dict com todos os mapeamentos (inclusive inativos).

        Returns:
            {"chave": {"from": str, "to": str, "enabled": bool}, ...}
        """
        result = {}
        for key, row in self._rows.items():
            result[key] = {
                "from": row["from_edit"].text(),
                "to": row["to_edit"].text(),
                "enabled": row["checkbox"].isChecked(),
            }
        return result

    def get(self, key: str) -> Dict[str, Any]:
        """
        Retorna valores de uma chave especifica.

        Args:
            key: Chave do item.

        Returns:
            {"from": str, "to": str, "enabled": bool}

        Raises:
            KeyError: se chave nao existir.
        """
        row = self._rows.get(key)
        if row is None:
            raise KeyError(f"Chave '{key}' nao encontrada no GridFieldMapping")
        return {
            "from": row["from_edit"].text(),
            "to": row["to_edit"].text(),
            "enabled": row["checkbox"].isChecked(),
        }

    def set_values(self, values: Dict[str, Dict[str, Any]], block_signals: bool = False):
        """
     Restaura estado de todos os itens a partir de um dict.

        Args:
            values: {"chave": {"from": str, "to": str, "enabled": bool}, ...}
            block_signals: Se True, nao emite changed durante a restauracao.
        """
        if block_signals:
            self.blockSignals(True)

        for key, data in values.items():
            row = self._rows.get(key)
            if row is None:
                continue
            row["from_edit"].blockSignals(True)
            row["to_edit"].blockSignals(True)
            row["checkbox"].blockSignals(True)

            row["from_edit"].setText(str(data.get("from", "")))
            row["to_edit"].setText(str(data.get("to", "")))
            enabled = bool(data.get("enabled", True))
            row["checkbox"].setChecked(enabled)
            self._apply_row_enabled(key, enabled)

            row["from_edit"].blockSignals(False)
            row["to_edit"].blockSignals(False)
            row["checkbox"].blockSignals(False)

        if block_signals:
            self.blockSignals(False)
        else:
            # Emite changed para o primeiro item como notificacao
            if values:
                first_key = next(iter(values.keys()))
                self._emit_changed(first_key)

    def set_enabled(self, key: str, enabled: bool):
        """
        Habilita/desabilita uma linha inteira por chave.

        Args:
            key: Chave do item.
            enabled: True para habilitar, False para desabilitar.

        Raises:
            KeyError: se chave nao existir.
        """
        row = self._rows.get(key)
        if row is None:
            raise KeyError(f"Chave '{key}' nao encontrada no GridFieldMapping")
        row["checkbox"].setChecked(enabled)