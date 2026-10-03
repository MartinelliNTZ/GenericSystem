# -*- coding: utf-8 -*-
"""
PropertyInfoWidget — Exibe propriedades básicas de um arquivo
===============================================================
Mostra nome, tamanho, caminho (clicável), diretório, extensão,
datas de criação e modificação.

Usa GridLabel internamente para exibir os pares label: valor.

Uso:
    widget = PropertyInfoWidget(parent=self)
    widget.load_data({
        "name": "arquivo.txt",
        "size_formatted": "1.2 KB",
        "extension_name": "TXT",
        "path": "c:/pasta/arquivo.txt",
        "directory": "c:/pasta",
        "created": "01/06/2026 12:00:00",
        "modified": "01/06/2026 14:30:00",
    })
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from resources.widgets.grid.GridLabel import GridLabel

_logger = LogUtils(tool=ToolKey.UNTRACEABLE.value, class_name="PropertyInfoWidget")


class PropertyInfoWidget(QWidget):
    """
    Exibe metadados básicos de um arquivo em formato label: valor.
    O caminho do arquivo aparece como link clicável.
    """

    _LABEL_CONFIG = {
        "name": {
            "label": "Nome",
            "value": "—",
            "description": "Nome do arquivo",
        },
        "size": {
            "label": "Tamanho",
            "value": "—",
        },
        "type": {
            "label": "Tipo",
            "value": "—",
        },
        "path": {
            "label": "Caminho",
            "value": "—",
            "link": True,
        },
        "dir": {
            "label": "Diretório",
            "value": "—",
        },
        "created": {
            "label": "Criado em",
            "value": "—",
        },
        "modified": {
            "label": "Modificado em",
            "value": "—",
        },
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._file_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Grid de propriedades ─────────────────────────────────────
        self._grid = GridLabel(
            config=self._LABEL_CONFIG,
            columns=1,
            parent=self,
        )
        self._grid.link_clicked.connect(self._on_path_clicked)
        layout.addWidget(self._grid)

        _logger.info(
            "GridLabel de propriedades criado",
            code="PROP_GRID_OK",
        )

        # ── Seção colapsável ─────────────────────────────────────────
        from resources.widgets.CollapsibleParams import CollapsibleParams

        self._extra_section = CollapsibleParams(
            title="Informações Avançadas",
            collapsed=True,
            parent=self,
        )
        self._extra_section.content_layout.addWidget(
            QLabel("Configurações adicionais em breve.")
        )
        layout.addWidget(self._extra_section)

        _logger.info(
            "Seção colapsável adicionada ao layout",
            code="COLLAPSE_ADDED",
        )

    def load_data(self, data: Dict[str, Any]) -> None:
        """
        Carrega dados de um dicionário (enriquecido via BasicExtractor).

        Args:
            data: Dicionário com chaves name, size_formatted, extension_name,
                  path, directory, created, modified.
        """
        _logger.info(
            "Carregando dados no PropertyInfoWidget",
            code="PROP_LOAD_DATA",
            has_name="name" in data,
            has_path="path" in data,
        )

        file_path = data.get("path", "")
        self._file_path = file_path

        self._grid.set_values({
            "name": data.get("name", "—"),
            "size": data.get("size_formatted", "—"),
            "type": data.get("extension_name", "—"),
            "path": (data.get("name", "—"), file_path) if file_path else "—",
            "dir": data.get("directory", "—"),
            "created": data.get("created", "—"),
            "modified": data.get("modified", "—"),
        })

        _logger.info(
            "Dados carregados no PropertyInfoWidget",
            code="PROP_DATA_DONE",
            file_path=file_path,
        )

    def _on_path_clicked(self, key: str, url: str) -> None:
        """
        Abre o local do arquivo no Explorer.
        Se for arquivo, seleciona-o (abre a pasta pai com o arquivo selecionado).
        """
        if key != "path":
            return

        file_path = self._file_path
        if not file_path:
            return

        directory = os.path.dirname(file_path)
        if not directory or not os.path.exists(directory):
            return

        QDesktopServices.openUrl(f"file:///{os.path.normpath(directory).replace(os.sep, '/')}")