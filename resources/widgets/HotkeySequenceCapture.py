# -*- coding: utf-8 -*-
"""
HotkeySequenceCapture
====================

Widget para capturar uma sequência de teclas/atalhos.

Recursos:
- Captura teclas uma a uma
- Lista as teclas capturadas
- Remove itens individualmente
- Botão para limpar tudo
- Exibição em múltiplas colunas (padrão: 5)

Uso:
    capture = HotkeySequenceCapture(columns=5)
    capture.sequenceChanged.connect(...)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)

from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine, _to_display
from resources.widgets.simple.SimpleGhostButton import SimpleGhostButton
from resources.widgets.simple.SimpleLabel import SimpleLabel
from resources.widgets.simple.SimpleRemoveButton import SimpleRemoveButton


class HotkeySequenceCapture(QWidget):
    """
    Captura uma sequência de teclas/atalhos.

    Parameters:
        title: str | None — se informado, exibe um QLabel com o título antes do resto
        default_keys: list[str] | None
        placeholder: str
        columns: int
        parent: QWidget | None

    Signals:
        sequenceChanged(list[str])
    """

    sequenceChanged = Signal(list)

    def __init__(
        self,
        title: str | None = None,
        default_keys: list[str] | None = None,
        placeholder: str = "Clique e pressione uma tecla...",
        columns: int = 5,
        parent=None,
    ):
        super().__init__(parent)

        self._title = title
        self._keys = list(default_keys) if default_keys else []
        self._placeholder = placeholder
        self._columns = max(1, columns)

        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # ── Título opcional ──
        if self._title:
            title_lbl = QLabel(self._title)
            title_lbl.setObjectName("subsection_label")
            main_layout.addWidget(title_lbl)

        # --------------------------------------------------------------
        # Linha superior
        # --------------------------------------------------------------
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        self._capture_field = HotkeyCaptureLine(
            default_key="",
            placeholder=self._placeholder,
        )
        self._capture_field.setObjectName("hsc_capture_field")
        self._capture_field.keyChanged.connect(self._on_key_captured)
        top_row.addWidget(self._capture_field, 1)

        self._btn_add = SimpleGhostButton("+")
        self._btn_add.setObjectName("hsc_btn_add")
        self._btn_add.setToolTip("Adicionar próxima tecla")
        self._btn_add.clicked.connect(self._on_add_clicked)
        top_row.addWidget(self._btn_add)

        self._btn_clear = SimpleGhostButton("Limpar")
        self._btn_clear.setObjectName("hsc_btn_clear")
        self._btn_clear.clicked.connect(self.clear)
        top_row.addWidget(self._btn_clear)

        main_layout.addLayout(top_row)

        # --------------------------------------------------------------
        # Container da lista
        # --------------------------------------------------------------
        self._list_container = QWidget()
        self._list_container.setObjectName("hsc_list_container")

        self._grid = QGridLayout(self._list_container)
        self._grid.setContentsMargins(0, 2, 0, 2)
        self._grid.setHorizontalSpacing(4)
        self._grid.setVerticalSpacing(2)

        # Placeholder quando vazio
        self._empty_label = SimpleLabel("Nenhuma tecla capturada")
        self._empty_label.setObjectName("hsc_empty")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._grid.addWidget(
            self._empty_label,
            0, 0,
            1, self._columns
        )

        main_layout.addWidget(self._list_container)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _on_add_clicked(self):
        """Coloca o campo em modo de captura."""
        self._capture_field.setFocus()
        self._capture_field._start_capture()

    def _on_key_captured(self, key_name: str):
        """Adiciona uma tecla capturada."""
        if not key_name:
            return

        self._keys.append(key_name)
        self._refresh()
        self.sequenceChanged.emit(self.captured_sequence())

    def _remove_key(self, index: int):
        """Remove uma tecla pelo índice."""
        if 0 <= index < len(self._keys):
            self._keys.pop(index)
            self._refresh()
            self.sequenceChanged.emit(self.captured_sequence())

    # ------------------------------------------------------------------
    # Atualização visual
    # ------------------------------------------------------------------

    def _refresh(self):
        """Atualiza a grade de teclas."""
        self._clear_dynamic_items()

        if not self._keys:
            self._empty_label.setVisible(True)
            return

        self._empty_label.setVisible(False)

        for index, key in enumerate(self._keys):
            row = index // self._columns
            col = index % self._columns

            item = self._create_key_item(key, index)
            self._grid.addWidget(item, row, col)

    def _clear_dynamic_items(self):
        """Remove todos os widgets, exceto o placeholder."""
        for i in reversed(range(self._grid.count())):
            item = self._grid.itemAt(i)
            widget = item.widget()

            if widget is not None and widget is not self._empty_label:
                self._grid.removeWidget(widget)
                widget.deleteLater()

    def _create_key_item(self, key: str, index: int) -> QWidget:
        """Cria o widget visual de uma tecla."""
        item = QFrame()
        item.setObjectName("hsc_key_item")
        item.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        # Texto
        label = QLabel(f"{index + 1}. {_to_display(key)}")
        label.setObjectName("hsc_key_label")
        layout.addWidget(label, 1)

        # Botão remover
        btn_remove = SimpleRemoveButton()
        btn_remove.setObjectName("hsc_btn_remove")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_remove.clicked.connect(
            lambda checked=False, i=index: self._remove_key(i)
        )
        layout.addWidget(btn_remove)

        return item

    # ------------------------------------------------------------------
    # API Pública
    # ------------------------------------------------------------------

    def captured_sequence(self) -> list[str]:
        """Retorna a sequência atual."""
        return list(self._keys)

    def set_captured_sequence(self, keys: list[str]):
        """Define programaticamente a sequência."""
        self._keys = list(keys)
        self._refresh()
        self.sequenceChanged.emit(self.captured_sequence())

    def clear(self):
        """Remove todas as teclas."""
        self._keys.clear()
        self._refresh()
        self.sequenceChanged.emit(self.captured_sequence())

    def set_columns(self, columns: int):
        """Define quantas colunas serão exibidas."""
        self._columns = max(1, columns)

        # Reposiciona o placeholder com novo colspan
        self._grid.removeWidget(self._empty_label)
        self._grid.addWidget(
            self._empty_label,
            0, 0,
            1, self._columns
        )

        self._refresh()

    def columns(self) -> int:
        """Retorna o número de colunas."""
        return self._columns