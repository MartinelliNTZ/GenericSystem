# -*- coding: utf-8 -*-
"""
ItemTable — Tabela genérica com itens, IDs, labels e botão remover
=====================================================================
Tabela pré-formatada configurável por colunas. Cada coluna pode ter:
- Texto (QTableWidgetItem, editável ou não)
- SpinBox (QSpinBox com range configurável)
- LineEdit (QLineEdit com placeholder)
- Botão Remover (SimpleRemoveButton)

Uso:
    from resources.widgets.ItemTable import ItemTable

    table = ItemTable(
        columns=[
            {"header": "Caminho", "type": "text", "stretch": True, "editable": False},
            {"header": "ID",      "type": "spin", "width": 55, "min": 0, "max": 999},
            {"header": "Legenda", "type": "line", "width": 90, "placeholder": "Legenda..."},
            {"header": "",        "type": "remove", "width": 65},
        ]
    )
    painel.group_layout.addWidget(table)

    table.add_row("caminho/arquivo.shp", 1, "Mata")
    table.get_row_data(0)  # {"col_0": "caminho/...", "col_1": 1, "col_2": "Mata"}
    table.all_rows()
    table.remove_row(0)
    table.clear_rows()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSpinBox,
    QLineEdit,
)
from PySide6.QtCore import Qt

from resources.widgets.simple.SimpleRemoveButton import SimpleRemoveButton


class ItemTable(QTableWidget):
    """
    Tabela genérica configurável por especificação de colunas.

    Parameters
    ----------
    columns : list[dict]
        Lista de specs de coluna. Cada dict pode conter:
          - "header"      : str — título da coluna
          - "type"        : str — "text" | "spin" | "line" | "remove"
          - "width"       : int — largura fixa (opcional)
          - "stretch"     : bool — se True, coluna expande (padrão False)
          - "editable"    : bool — apenas para type="text" (padrão True)
          - "min"/"max"   : int — para type="spin" (padrão 0/999)
          - "placeholder" : str — para type="line"
          - "remove_text" : str — texto do botão remover (padrão "Remover")
    parent : QWidget | None
    """

    def __init__(
        self,
        columns: List[Dict[str, Any]],
        parent=None,
    ):
        num_cols = len(columns)
        super().__init__(0, num_cols, parent)
        self._columns = columns
        self._build()

    def _build(self) -> None:
        """Configura headers, resize modes e larguras das colunas."""
        headers = []
        for col_spec in self._columns:
            headers.append(col_spec.get("header", ""))

        self.setHorizontalHeaderLabels(headers)
        hh = self.horizontalHeader()

        for idx, col_spec in enumerate(self._columns):
            stretch = col_spec.get("stretch", False)
            width = col_spec.get("width")

            if stretch:
                hh.setSectionResizeMode(idx, QHeaderView.ResizeMode.Stretch)
            elif width:
                hh.setSectionResizeMode(idx, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(idx, width)

        self.setMinimumHeight(100)
        self.verticalHeader().setDefaultSectionSize(24)

    def _make_widget(self, col_spec: Dict[str, Any], value: Any = None) -> Optional[QWidget]:
        """Cria o widget apropriado para a coluna baseado na spec."""
        col_type = col_spec.get("type", "text")

        if col_type == "text":
            text = str(value) if value is not None else ""
            item = QTableWidgetItem(text)
            if not col_spec.get("editable", True):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            return item  # QTableWidgetItem, não QWidget

        elif col_type == "spin":
            spin = QSpinBox()
            spin.setRange(col_spec.get("min", 0), col_spec.get("max", 999))
            if value is not None:
                spin.setValue(int(value))
            spin.setStyleSheet("background-color: transparent; border: none;")
            return spin

        elif col_type == "line":
            line = QLineEdit()
            placeholder = col_spec.get("placeholder", "")
            if placeholder:
                line.setPlaceholderText(placeholder)
            if value is not None:
                line.setText(str(value))
            line.setStyleSheet("background-color: transparent; border: none;")
            return line

        elif col_type == "remove":
            text = col_spec.get("remove_text", "Remover")
            btn = SimpleRemoveButton(text)
            return btn

        return None

    def add_row(self, *values: Any) -> None:
        """
        Adiciona uma linha na tabela.

        Args:
            *values: Valores para cada coluna, na ordem das colunas.
                     Para colunas "remove", o valor é ignorado.
        """
        row = self.rowCount()
        self.insertRow(row)

        for idx, col_spec in enumerate(self._columns):
            value = values[idx] if idx < len(values) else None
            widget = self._make_widget(col_spec, value)

            if isinstance(widget, QTableWidgetItem):
                self.setItem(row, idx, widget)
            elif widget is not None:
                # Botão remover — conecta sinal
                if col_spec.get("type") == "remove":
                    widget.clicked.connect(lambda checked, r=row: self.remove_row(r))
                self.setCellWidget(row, idx, widget)

    def remove_row(self, row: int) -> None:
        """
        Remove uma linha e reconecta os botões das linhas restantes.

        Args:
            row: Índice da linha a remover
        """
        self.removeRow(row)
        # Reconecta botões remover para manter índices corretos
        remove_cols = [
            idx for idx, col in enumerate(self._columns)
            if col.get("type") == "remove"
        ]
        for idx in remove_cols:
            for r in range(self.rowCount()):
                btn = self.cellWidget(r, idx)
                if btn:
                    try:
                        btn.clicked.disconnect()
                    except Exception:
                        pass
                    btn.clicked.connect(
                        lambda checked, fixed_row=r: self.remove_row(fixed_row)
                    )

    def get_row_data(self, row: int) -> Dict[str, Any]:
        """
        Retorna os dados de uma linha como dicionário.

        Args:
            row: Índice da linha

        Returns:
            Dict com chaves "col_0", "col_1", ... conforme as colunas
        """
        data: Dict[str, Any] = {}
        for idx, col_spec in enumerate(self._columns):
            col_type = col_spec.get("type", "text")
            key = f"col_{idx}"

            if col_type == "text":
                item = self.item(row, idx)
                data[key] = item.text() if item else ""
            elif col_type == "spin":
                spin = self.cellWidget(row, idx)
                data[key] = spin.value() if spin else 0
            elif col_type == "line":
                line_edit = self.cellWidget(row, idx)
                data[key] = line_edit.text() if line_edit else ""
            elif col_type == "remove":
                data[key] = None  # botão — sem dado

        return data

    def all_rows(self) -> List[Dict[str, Any]]:
        """
        Retorna todas as linhas como lista de dicionários.

        Returns:
            Lista de dicts com "col_0", "col_1", ...
        """
        return [self.get_row_data(r) for r in range(self.rowCount())]

    def clear_rows(self) -> None:
        """Remove todas as linhas da tabela."""
        while self.rowCount() > 0:
            self.removeRow(0)