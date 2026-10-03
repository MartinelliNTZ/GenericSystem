# -*- coding: utf-8 -*-
"""
PreferenceItemGrid — Grade de itens de preferência editáveis
==============================================================
Exibe uma lista vertical de itens de preferência onde cada item
contém: título | valor (bool → checkbox, float → spin, str → line edit) | botão lixeira.

Configuração via dicionário:
    {
        "search_text": {
            "type": "text",
            "default": "",
            "label": "Texto de Busca"
        },
        "max_results": {
            "type": "float",
            "default": 50.0,
            "label": "Máx. Resultados"
        },
        "auto_save": {
            "type": "bool",
            "default": True,
            "label": "Salvar Automaticamente"
        }
    }

Uso:
    grid = GridPreferenceItem(config_dict, section="MinhaFerramenta")
    grid.load_values()
    grid.save_values()
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QDoubleSpinBox, QScrollArea, QPushButton,
)
from PySide6.QtCore import Qt, Signal

from resources.widgets.simple.SimpleDangerButton import SimpleDangerButton
from utils.Preferences import Preferences
from core.enum.ToolKey import ToolKey


class PreferenceRow(QWidget):
    """
    Linha única de preferência: título | valor | botão lixeira.
    """

    removed = Signal(str)  # key do item removido

    def __init__(
        self,
        key: str,
        config: Dict[str, Any],
        current_value: Any,
        parent=None,
    ):
        super().__init__(parent)
        self._key = key
        self._config = config
        self._type = config.get("type", "text")
        self._label = config.get("label", key)

        self._build_ui(current_value)

    def _build_ui(self, current_value: Any):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Label
        lbl = QLabel(self._label)
        lbl.setMinimumWidth(140)
        lbl.setObjectName("pref_row_label")
        layout.addWidget(lbl)

        # Widget de valor conforme o tipo
        self._value_widget = self._create_value_widget(current_value)
        layout.addWidget(self._value_widget, 1)

        # Botão lixeira
        btn_remove = QPushButton("🗑")
        btn_remove.setFixedSize(28, 28)
        btn_remove.setToolTip(f"Remover '{self._label}'")
        btn_remove.setObjectName("pref_remove_btn")
        btn_remove.clicked.connect(lambda: self.removed.emit(self._key))
        layout.addWidget(btn_remove)

    def _create_value_widget(self, current_value: Any) -> QWidget:
        if self._type == "bool":
            cb = QCheckBox()
            cb.setChecked(bool(current_value))
            cb.setObjectName("pref_check")
            return cb

        if self._type in ("float", "int"):
            sp = QDoubleSpinBox()
            min_ = self._config.get("min", -999999.0)
            max_ = self._config.get("max", 999999.0)
            step = self._config.get("step", 0.1 if self._type == "float" else 1.0)
            sp.setRange(min_, max_)
            sp.setSingleStep(step)
            sp.setDecimals(self._config.get("decimals", 2) if self._type == "float" else 0)
            try:
                sp.setValue(float(current_value))
            except (TypeError, ValueError):
                sp.setValue(self._config.get("default", 0.0))
            sp.setObjectName("pref_spin")
            return sp

        # default: text
        le = QLineEdit(str(current_value) if current_value is not None else "")
        le.setPlaceholderText(self._config.get("placeholder", ""))
        le.setObjectName("pref_text")
        return le

    def get_value(self) -> Any:
        """Retorna o valor atual do widget."""
        if self._type == "bool":
            return self._value_widget.isChecked()
        if self._type in ("float", "int"):
            val = self._value_widget.value()
            return val if self._type == "float" else int(val)
        return self._value_widget.text()

    @property
    def key(self) -> str:
        return self._key


class GridPreferenceItem(QScrollArea):
    """
    Grade rolável de itens de preferência configurados por dicionário.

    Sinais:
        changed — emitido quando um valor é alterado
    """

    changed = Signal()

    def __init__(self, config: Dict[str, Dict[str, Any]], section: str, parent=None):
        super().__init__(parent)
        self._config = config
        self._section = section
        # Carrega dict do disco
        try:
            tk = ToolKey.from_name(section)
        except ValueError:
            tk = section
        self._data: Dict[str, Any] = Preferences.load_tool_prefs(tk)
        self._rows: Dict[str, PreferenceRow] = {}

        self.setWidgetResizable(True)
        self.setObjectName("pref_grid_scroll")

        self._container = QWidget()
        self._container.setObjectName("pref_grid_container")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(2)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._container)

        self._rebuild()

    def _rebuild(self):
        """Remove todas as linhas e recria a partir do config."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._rows.clear()

        if not self._config:
            lbl = QLabel("Nenhuma preferência configurada.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("pref_empty_label")
            self._layout.addWidget(lbl)
            return

        for key, cfg in self._config.items():
            current = self._data.get(key, cfg.get("default"))
            row = PreferenceRow(key, cfg, current)
            row.removed.connect(self._on_row_removed)
            self._rows[key] = row
            self._layout.addWidget(row)

    def _on_row_removed(self, key: str):
        """Remove o item da memória e da UI."""
        row = self._rows.pop(key, None)
        if row:
            self._data[key] = None
            self._layout.removeWidget(row)
            row.deleteLater()
            self.changed.emit()

    def load_values(self):
        """Recarrega valores das preferências do disco."""
        try:
            tk = ToolKey.from_name(self._section)
        except ValueError:
            tk = self._section
        self._data = Preferences.load_tool_prefs(tk)
        self._rebuild()

    def save_values(self) -> Dict[str, Any]:
        """
        Salva todos os valores atuais nas preferências.
        Retorna o dict dos valores salvos.
        """
        saved = {}
        for key, row in self._rows.items():
            val = row.get_value()
            self._data[key] = val
            saved[key] = val

        try:
            tk = ToolKey.from_name(self._section)
        except ValueError:
            tk = self._section
        Preferences.save_tool_prefs(tk, self._data)
        return saved

    def reset_values(self):
        """Restaura todos os valores para os defaults do config."""
        for key, cfg in self._config.items():
            default = cfg.get("default")
            self._data[key] = default

        try:
            tk = ToolKey.from_name(self._section)
        except ValueError:
            tk = self._section
        Preferences.save_tool_prefs(tk, self._data)
        self._rebuild()
        self.changed.emit()

    def clear_all(self):
        """Remove todos os itens das preferências desta seção."""
        for key in list(self._rows.keys()):
            self._data[key] = None

        try:
            tk = ToolKey.from_name(self._section)
        except ValueError:
            tk = self._section
        Preferences.save_tool_prefs(tk, self._data)
        self._rebuild()
        self.changed.emit()