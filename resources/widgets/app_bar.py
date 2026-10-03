# -*- coding: utf-8 -*-
"""
AppBar — Barra de título e toolbar do Aetheris ToolBox
========================================================
Fornece:
  - Barra de título com controle de janela (min/max/close)
  - Suporte a arrasto da janela (frameless)
  - Área de toolbar para ações globais
"""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QToolBar,
    QSizePolicy, QMenu, QToolButton, QApplication
)


class AppBar(QWidget):
    """
    AppBar reutilizável com suporte a arrasto e toolbar.
    """

    minimize_clicked = Signal()
    maximize_restore_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_active = False
        self._drag_offset = QPoint()
        self._maximized = False

        self.setObjectName("title_bar")
        self.setFixedHeight(40)

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(6)

        # --- Window icon ---
        icon_path = Path(__file__).parent.parent / "Aetheris.png"
        if icon_path.exists():
            self._icon_label = QLabel()
            pixmap = QIcon(str(icon_path)).pixmap(18, 18)
            self._icon_label.setPixmap(pixmap)
            self._icon_label.setFixedSize(22, 22)
            layout.addWidget(self._icon_label)

        # --- Window title ---
        self.lbl_window_title = QLabel("Aetheris ToolBox")
        self.lbl_window_title.setObjectName("window_title")
        layout.addWidget(self.lbl_window_title)

        # --- Project status ---
        self.lbl_project_status = QLabel("")
        self.lbl_project_status.setObjectName("project_status")
        self.lbl_project_status.setStyleSheet("color: #78716C; font-size: 11px; padding: 0 4px;")
        layout.addWidget(self.lbl_project_status)

        # --- Toolbar area ---
        self.toolbar_container = QWidget()
        self.toolbar_container.setObjectName("appbar_toolbar")
        toolbar_layout = QHBoxLayout(self.toolbar_container)
        toolbar_layout.setContentsMargins(4, 0, 4, 0)
        toolbar_layout.setSpacing(4)
        self._toolbar_widgets: list[QWidget] = []
        layout.addWidget(self.toolbar_container, 1)

        layout.addStretch()

        # --- Window controls ---
        self.btn_min = QPushButton("\u2014")
        self.btn_min.setObjectName("title_btn")
        self.btn_min.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("\u25A1")
        self.btn_max.setObjectName("title_btn")
        self.btn_max.clicked.connect(self._on_max_restore)
        layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("\u2715")
        self.btn_close.setObjectName("title_btn_close")
        self.btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.btn_close)

    def add_tool_widget(self, widget: QWidget) -> None:
        """Adiciona um widget à toolbar (ex: botão de ferramenta)."""
        self._toolbar_widgets.append(widget)
        self.toolbar_container.layout().addWidget(widget)

    def add_tool_button(self, text: str, icon=None, tooltip: str = "") -> QPushButton:
        """Adiciona um botão simples à toolbar. Retorna o botão para conectar sinais."""
        btn = QPushButton(text)
        if icon:
            btn.setIcon(icon)
        if tooltip:
            btn.setToolTip(tooltip)
        btn.setObjectName("toolbar_btn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(28)
        self.add_tool_widget(btn)
        return btn

    def set_title(self, title: str) -> None:
        self.lbl_window_title.setText(title)

    # ── Project status ──────────────────────────────────────────────

    def set_project_status(self, project_name: str, project_path: str) -> None:
        """
        Define o texto do status do projeto na AppBar.
        Formato:  - [project_name] - [path]
        """
        from pathlib import Path
        path_obj = Path(project_path)
        display_path = str(path_obj.parent.resolve()) if not path_obj.suffix else str(path_obj.resolve())
        self.lbl_project_status.setText(f"  -  [{project_name}] - {display_path}")
        self.lbl_project_status.setToolTip(project_path)

    def clear_project_status(self) -> None:
        """Limpa o status do projeto (exibe [Não salvo])."""
        self.lbl_project_status.setText("  -  [Não salvo]")
        self.lbl_project_status.setToolTip("")

    def _on_max_restore(self):
        self._maximized = not self._maximized
        self.btn_max.setText("\u29C9" if self._maximized else "\u25A1")
        self.maximize_restore_clicked.emit()

    # ────────────────────────────────────────────────────────────────────────
    # Arrasto da janela (frameless support)
    # ────────────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and not self._maximized:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_max_restore()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)