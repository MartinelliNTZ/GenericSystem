# -*- coding: utf-8 -*-
"""
LogViewerTool — Visualizador de logs do Aetheris ToolBox
==========================================================
Exibe todos os eventos de log em uma tabela com suporte a:
- Pesquisa por texto (filtra em tempo real)
- Filtro por nivel (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Ordenacao por coluna (clique no cabecalho)
- Selecao multipla (CTRL / SHIFT)
- Copiar filtro ou selecao para clipboard
- Duplo clique abre dialog de detalhes
- Cores de fonte via ColorProvider (tool, class, level)

Uso:
    from plugins.log_viewer.log_viewer import LogViewerTool
    widget = LogViewerTool()
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QPushButton, QHeaderView, QLabel,
    QAbstractItemView, QApplication,
)
from PySide6.QtGui import QColor, QBrush

from plugins.BasePlugin import BasePlugin
from resources.styles.AppStyles import AppStyles


class LogViewerPlugin(BasePlugin):
    """
    Visualizador de logs com tabela, pesquisa e filtro.

    Layout:
      [Busca | Nivel | Export Filtro | Export Selecao | Refresh]
      [Tabela: timestamp | level | tool | class | message | code]
    """

    COLUMNS = ["timestamp", "level", "tool", "class", "message", "code"]

    def __init__(self, parent=None):
        # Inicializa atributos ANTES do super().__init__ porque o
        # BasePlugin.__init__ chama load_prefs(), que dispara
        # _on_filter_changed → _render_table() → acessa self._raw_events.
        self._raw_events: List[dict] = []
        self._filtered_events: List[dict] = []
        self._sort_column: str = "timestamp"
        self._sort_ascending: bool = False

        super().__init__(tool_key="LogViewer", parent=parent)

        # NOTA: BasePlugin.__init__ já chama _build_ui() e load_prefs()
        # automaticamente. Não duplicar as chamadas aqui.

        self._load_and_refresh()
        self.logger.info("LogViewer carregado", code="TOOL_READY")

    # ═════════════════════════════════════════════════════════════════════
    # Preferences
    # ═════════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega search_text e level_filter do disco e aplica nos widgets."""
        search_text = self.preferences.get("search_text", "")
        if search_text:
            self.search_input.setText(search_text)

        level_filter = self.preferences.get("level_filter", "ALL")
        index = self.level_combo.findText(level_filter)
        if index >= 0:
            self.level_combo.setCurrentIndex(index)

    def save_prefs(self) -> None:
        """Le os valores atuais dos widgets e salva no disco."""
        self.preferences["search_text"] = self.search_input.text()
        self.preferences["level_filter"] = self.level_combo.currentText()
        # Ferramentas laterais nunca recebem closeEvent, então força persistência imediata
        self.force_save_prefs()

    # ═════════════════════════════════════════════════════════════════════
    # Construcao da UI
    # ═════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        from utils.ColorProvider import ColorProvider
        from resources.widgets.simple.SimpleGhostButton import SimpleGhostButton

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Barra de ferramentas ─────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar nos logs...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.search_input, 1)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.level_combo)

        self.export_filter_btn = SimpleGhostButton("Exportar Filtro")
        self.export_filter_btn.setToolTip("Copia todos os eventos filtrados (TSV)")
        self.export_filter_btn.clicked.connect(self._export_filter)
        toolbar.addWidget(self.export_filter_btn)

        self.export_selection_btn = SimpleGhostButton("Exportar Selecao")
        self.export_selection_btn.setToolTip("Copia as celulas selecionadas (TSV)")
        self.export_selection_btn.clicked.connect(self._export_selection)
        toolbar.addWidget(self.export_selection_btn)

        self.refresh_btn = SimpleGhostButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_and_refresh)
        toolbar.addWidget(self.refresh_btn)

        layout.addLayout(toolbar)

        # ── Tabela ───────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)

        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.setStyleSheet(AppStyles.log_viewer_table_style())

        header = self.table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.sectionClicked.connect(self._on_header_clicked)
        header.resizeSection(0, 180)
        header.resizeSection(1, 80)
        header.resizeSection(2, 100)
        header.resizeSection(3, 120)
        header.resizeSection(4, 400)
        header.resizeSection(5, 100)
        header.setStretchLastSection(True)

        layout.addWidget(self.table, 1)

        self.status_label = QLabel("Carregando...")
        layout.addWidget(self.status_label)

    # ═════════════════════════════════════════════════════════════════════
    # Carregamento e renderizacao
    # ═════════════════════════════════════════════════════════════════════

    def _load_and_refresh(self) -> None:
        from core.config.LogFilter import LogFilter

        self._raw_events = LogFilter.load_all()
        self._render_table()
        self.status_label.setText(
            f"{len(self._raw_events)} evento(s) carregado(s) "
            f"de {self._count_log_files()} arquivo(s)"
        )

    def _count_log_files(self) -> int:
        log_dir = Path(__file__).resolve().parent.parent.parent / "log"
        if not log_dir.is_dir():
            return 0
        return sum(1 for p in log_dir.iterdir() if p.suffix.lower() == ".json")

    def _render_table(self) -> None:
        from core.config.LogFilter import LogFilter
        from utils.ColorProvider import ColorProvider

        events = self._raw_events

        search_text = self.search_input.text()
        if search_text:
            events = LogFilter.filter_text(events, search_text)

        level = self.level_combo.currentText()
        if level != "ALL":
            events = LogFilter.filter_level(events, level)

        events = LogFilter.sort(events, self._sort_column, self._sort_ascending)

        self._filtered_events = events
        self.table.setRowCount(len(events))

        for row, event in enumerate(events):
            for col, col_name in enumerate(self.COLUMNS):
                value = event.get(col_name, "")
                if isinstance(value, dict):
                    value = str(value)
                if value is None:
                    value = ""

                if col_name == "timestamp":
                    value = self._format_timestamp(str(value))

                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, event)

                if col_name == "level":
                    color_hex = ColorProvider.level_color(str(value))
                elif col_name == "tool":
                    color_hex = ColorProvider.tool_color(str(value))
                elif col_name == "class":
                    color_hex = ColorProvider.class_color(str(value))
                else:
                    color_hex = ColorProvider.text_primary()

                item.setForeground(QBrush(QColor(color_hex)))
                self.table.setItem(row, col, item)

        filtered = len(events)
        total = len(self._raw_events)
        if filtered != total:
            self.status_label.setText(f"{filtered} de {total} evento(s) (filtrado)")

    @staticmethod
    def _format_timestamp(ts: str) -> str:
        if not ts:
            return ts
        ts = ts.replace("T", " ")
        if "." in ts:
            ts = ts.split(".")[0]
        return ts

    # ═════════════════════════════════════════════════════════════════════
    # Exportacao
    # ═════════════════════════════════════════════════════════════════════

    def _export_filter(self) -> None:
        if not self._filtered_events:
            return

        lines: List[str] = []
        lines.append("\t".join(self.COLUMNS))
        for event in self._filtered_events:
            row_values: List[str] = []
            for col_name in self.COLUMNS:
                value = event.get(col_name, "")
                if isinstance(value, dict):
                    value = str(value)
                if value is None:
                    value = ""
                row_values.append(str(value).replace("\t", " "))
            lines.append("\t".join(row_values))

        QApplication.clipboard().setText("\n".join(lines))
        self.status_label.setText(
            f"{len(self._filtered_events)} evento(s) copiados (filtro)"
        )

    def _export_selection(self) -> None:
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        lines: List[str] = []
        for sel_range in selected_ranges:
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                row_values: List[str] = []
                for col in range(sel_range.leftColumn(), sel_range.rightColumn() + 1):
                    item = self.table.item(row, col)
                    value = item.text() if item else ""
                    row_values.append(value.replace("\t", " "))
                lines.append("\t".join(row_values))

        QApplication.clipboard().setText("\n".join(lines))
        cell_count = sum(
            (r.bottomRow() - r.topRow() + 1) * (r.rightColumn() - r.leftColumn() + 1)
            for r in selected_ranges
        )
        self.status_label.setText(f"{cell_count} celula(s) copiadas (selecao)")

    # ═════════════════════════════════════════════════════════════════════
    # Eventos
    # ═════════════════════════════════════════════════════════════════════

    def _on_filter_changed(self) -> None:
        self._render_table()
        self.save_prefs()

    def _on_header_clicked(self, logical_index: int) -> None:
        col_name = self.COLUMNS[logical_index]
        if self._sort_column == col_name:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = col_name
            self._sort_ascending = True
        self._render_table()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        from core.dialogs.LogDetailDialog import LogDetailDialog

        item = self.table.item(row, 0)
        if item is None:
            return

        event = item.data(Qt.ItemDataRole.UserRole)
        if event is None:
            event = {}
            for c, col_name in enumerate(self.COLUMNS):
                cell = self.table.item(row, c)
                event[col_name] = cell.text() if cell else ""

        dialog = LogDetailDialog(event, self)
        dialog.exec()