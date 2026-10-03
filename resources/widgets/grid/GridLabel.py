# -*- coding: utf-8 -*-
"""
GridLabel — Grade de labels informativos (label: valor)
========================================================
Exibe pares "label: valor" em grid, usando QLabel com estilo
consistente (monospace, cor clara). Suporta múltiplas colunas
e valores clicáveis (links).

Configuração via dicionário:
    {
        "name": {
            "label": "Nome",
            "value": "—",
            "description": "Nome do arquivo",   # opcional
            "link": False,                       # opcional, True = link clicável
        },
        "size": {
            "label": "Tamanho",
            "value": "—",
        },
    }

Uso:
    grid = GridLabel(config)
    grid.values          # {"name": "—", "size": "—"}
    grid.set_values({"name": "arquivo.txt", "size": "1.2 KB"})
    grid.set("name", "novo_valor")
    grid.get("name")     # "novo_valor"
    grid.link_clicked.connect(self._on_link_clicked)
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import quote

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QWidget


class GridLabel(QWidget):
    """
    Grade de labels informativos configurados por dicionário.
    Cada célula exibe "label: valor" com estilo SimpleLabel.

    Sinais:
        link_clicked(key, value) — emitido quando um link é clicado
    """

    link_clicked = Signal(str, str)

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        columns: int = 1,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._config = config
        self._labels: Dict[str, QLabel] = {}
        self._link_keys: set[str] = set()
        self._columns = max(1, columns)
        self.setObjectName("grid_label")

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)

        self._build()

    # ── Construção ───────────────────────────────────────────────────

    def _build(self):
        """Constrói a grade de labels a partir do config."""
        items = list(self._config.items())

        if self._columns > 1:
            self._build_multi_column(items)
        else:
            self._build_single_column(items)

        # Stretch vertical na última linha
        num_rows = (len(items) + self._columns - 1) // self._columns
        self._grid.setRowStretch(num_rows, 1)

    def _build_single_column(self, items):
        """Layout vertical: uma label por linha."""
        for row, (key, item) in enumerate(items):
            label_text = item.get("label", key)
            value = item.get("value", "—")
            description = item.get("description", "")
            is_link = item.get("link", False)

            cell = self._create_cell(key, label_text, value, description, is_link)
            self._grid.addWidget(cell, row, 0)

    def _build_multi_column(self, items):
        """Layout multi-coluna: distribui itens em N colunas."""
        for idx, (key, item) in enumerate(items):
            label_text = item.get("label", key)
            value = item.get("value", "—")
            description = item.get("description", "")
            is_link = item.get("link", False)

            row = idx // self._columns
            col = idx % self._columns

            cell = self._create_cell(key, label_text, value, description, is_link)
            self._grid.addWidget(cell, row, col)

        # Stretch igual para todas as colunas
        for c in range(self._columns):
            self._grid.setColumnStretch(c, 1)

    def _create_cell(
        self,
        key: str,
        label_text: str,
        value: str,
        description: str,
        is_link: bool,
    ) -> QLabel:
        """Cria um QLabel com o texto 'label: value'."""
        display = f"{label_text}: {value}" if value else label_text

        cell = QLabel(display)
        cell.setObjectName("grid_label_cell")
        cell.setStyleSheet(
            "color: #A1A1AA; font-family: Consolas, monospace; font-size: 12px;"
        )
        cell.setWordWrap(True)
        cell.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        if description:
            cell.setToolTip(description)

        if is_link:
            cell.setTextInteractionFlags(
                Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
            cell.setOpenExternalLinks(False)
            cell.linkActivated.connect(lambda url, k=key: self.link_clicked.emit(k, url))
            self._link_keys.add(key)

        self._labels[key] = cell
        return cell

    def _format_label(self, key: str) -> str:
        """Retorna o label_text do config."""
        return self._config.get(key, {}).get("label", key)

    # ── Métodos públicos ─────────────────────────────────────────────

    def set(self, key: str, value: str, url: Optional[str] = None):
        """
        Define o valor de um campo específico.

        Args:
            key: Chave do campo
            value: Novo valor texto
            url: Se fornecido e o campo for link, define o href do link
        """
        cell = self._labels.get(key)
        if cell is None:
            raise KeyError(f"Chave '{key}' não encontrada no GridLabel")

        label_text = self._format_label(key)
        is_link = key in self._link_keys

        if is_link and url:
            encoded = quote(url.replace("\\", "/"), safe="/:@!$&()*+,;=")
            href = f"file:///{encoded}"
            html = (
                f'<a href="{href}" '
                f'style="color:#3B82F6;text-decoration:underline;'
                f'font-family:Consolas,monospace;font-size:12px;">'
                f"{value}</a>"
            )
            display = f"{label_text}: {html}" if value else label_text
            cell.setText(display)
        else:
            display = f"{label_text}: {value}" if value else label_text
            cell.setText(display)

    def get(self, key: str) -> str:
        """Retorna o texto visível de um campo (sem o label prefixo)."""
        cell = self._labels.get(key)
        if cell is None:
            raise KeyError(f"Chave '{key}' não encontrada no GridLabel")

        full_text = cell.text()
        label_text = self._format_label(key)
        prefix = f"{label_text}: "
        if full_text.startswith(prefix):
            return full_text[len(prefix):]
        return full_text

    def set_values(self, values: Dict[str, Any]):
        """
        Define múltiplos valores de uma vez.

        Args:
            values: Dict no formato {"key": value} ou {"key": (value, url)} para links
        """
        for key, val in values.items():
            if isinstance(val, (list, tuple)) and len(val) == 2:
                self.set(key, str(val[0]), url=str(val[1]))
            else:
                self.set(key, str(val))

    @property
    def values(self) -> Dict[str, str]:
        """Retorna dict com todos os valores atuais."""
        result = {}
        for key in self._labels:
            result[key] = self.get(key)
        return result

    def widget(self, key: str) -> QLabel:
        """
        Retorna o QLabel subjacente para acesso direto.

        Args:
            key: Chave do campo configurado no construtor

        Returns:
            QLabel interno

        Raises:
            KeyError: se a chave não existir
        """
        cell = self._labels.get(key)
        if cell is None:
            raise KeyError(f"Chave '{key}' não encontrada no GridLabel")
        return cell