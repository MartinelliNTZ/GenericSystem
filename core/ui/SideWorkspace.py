# -*- coding: utf-8 -*-
"""
SideWorkspace — Painel lateral expansível (esquerdo ou direito)
=================================================================
Gerencia ferramentas do tipo SIDE (esquerdo ou direito).
Funciona com largura controlada: W_TABS (colapsado, mostra só as abas)
ou largura definida pelo usuário (expandido, mostra conteúdo).

Para side="right": abas à direita, conteúdo à esquerda.
Para side="left":  abas à esquerda, conteúdo à direita.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QLabel
)

from core.config.LogUtils import LogUtils
from core.enum.CategoryTool import CategoryTool
from core.model.Tool import Tool
from resources.widgets.VerticalTab import VerticalTab


class SideWorkspace(QWidget):
    """
    Painel lateral com abas verticais.

    O conteúdo SEMPRE existe dentro do widget.
    Quando colapsado, mostra só a aba vertical.
    Quando expandido, mostra a tool SIDE.
    """

    tool_activated = Signal(str)
    tool_closed    = Signal(str)
    size_changed   = Signal(int)     # largura total desejada (W_TABS se colapsado)
    tool_request_move_to_central = Signal(str)

    W_TABS     = 24   # largura das abas verticais (fixa)
    W_DEFAULT  = 400  # largura padrão do conteúdo quando expandido

    def __init__(self, side: str = "right", parent=None):
        """
        Parâmetros:
            side: "left" ou "right" — define onde as abas ficam
        """
        super().__init__(parent)
        self._side = side  # "left" ou "right"
        self._tools: dict[str, Tool] = {}
        self._tabs:  dict[str, VerticalTab] = {}
        self._expanded = False
        self._current_name: str | None = None
        self._log = LogUtils(tool="System", class_name="SideWorkspace")

        self.setObjectName(f"side_workspace_{side}")

        # Layout principal: conteúdo + abas
        mlo = QHBoxLayout(self)
        mlo.setContentsMargins(0, 0, 0, 0)
        mlo.setSpacing(0)

        # ── Abas verticais ─────────────────────────────────────────
        self._tab_box = QWidget()
        self._tab_box.setObjectName(f"side_tabs_container_{side}")
        self._tab_box.setFixedWidth(self.W_TABS)
        tbl = QVBoxLayout(self._tab_box)
        tbl.setContentsMargins(0, 0, 0, 0)
        tbl.setSpacing(2)
        tbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._tabs_layout = tbl

        # ── Conteúdo (stack) ──────────────────────────────────────
        self._content = QWidget()
        clo = QVBoxLayout(self._content)
        clo.setContentsMargins(0, 0, 0, 0)
        clo.setSpacing(0)

        tf = QFrame()
        tf.setObjectName("side_title_frame")
        tf.setFixedHeight(32)
        tl = QHBoxLayout(tf)
        tl.setContentsMargins(8, 0, 8, 0)
        self._title_label = QLabel("Ferramentas")
        self._title_label.setObjectName("side_title_label")
        tl.addWidget(self._title_label)
        tl.addStretch()
        clo.addWidget(tf)

        self.stack = QStackedWidget()
        clo.addWidget(self.stack, 1)

        # Ordem de adição conforme o lado
        if side == "left":
            # Abas à esquerda, conteúdo à direita
            mlo.addWidget(self._tab_box)
            mlo.addWidget(self._content, 1)
        else:
            # Conteúdo à esquerda, abas à direita (padrão)
            mlo.addWidget(self._content, 1)
            mlo.addWidget(self._tab_box)

        # Inicializa colapsado
        self._content.setVisible(False)

    # ── Propriedades ─────────────────────────────────────────────────

    @property
    def side(self) -> str:
        return self._side

    # ── API ──────────────────────────────────────────────────────────

    def register_tool(self, tool: Tool) -> str:
        name = tool.name
        if name in self._tools:
            return name
        self._tools[name] = tool

        placeholder = QWidget()
        self.stack.addWidget(placeholder)

        tab = VerticalTab(title=tool.title,
                          tooltip=tool.tooltip or tool.title)
        tab.clicked.connect(lambda n=name: self._on_tab_clicked(n))
        tab.double_clicked.connect(lambda n=name: self._on_tab_double_clicked(n))
        self._tabs[name] = tab
        self._tabs_layout.addWidget(tab)

        self._log.info(f"Tool SIDE registrada (lazy): {name}", code="SIDE_REG")
        return name

    def open_tool(self, tool: Tool) -> str:
        name = tool.name
        if name in self._tools:
            if self._expanded and self._current_name == name:
                self._set_collapsed()
            else:
                self._set_expanded(name)
            return name
        self.register_tool(tool)
        self._set_expanded(name)
        return name

    # ── Controle de estado ────────────────────────────────────────────

    def _set_collapsed(self):
        self._expanded = False
        self._current_name = None
        for tab in self._tabs.values():
            tab.selected = False
        self._content.setVisible(False)
        self.size_changed.emit(self.W_TABS)

    def _set_expanded(self, name: str, content_width: int | None = None):
        if name not in self._tools:
            return
        self._current_name = name
        self._expanded = True

        for n, tab in self._tabs.items():
            tab.selected = (n == name)

        self._load_tool(name)
        self._content.setVisible(True)
        w = (content_width or self.W_DEFAULT) + self.W_TABS
        self.size_changed.emit(w)
        self.tool_activated.emit(name)

    def collapse(self):
        self._set_collapsed()

    def expand(self, name: str, content_width: int | None = None):
        self._set_expanded(name, content_width)

    # ── Helpers ────────────────────────────────────────────────────────

    def _load_tool(self, name: str):
        tool = self._tools.get(name)
        if not tool:
            return
        keys = list(self._tools.keys())
        if name not in keys:
            return
        idx = keys.index(name)

        widget = tool.widget

        old = self.stack.widget(idx)
        if old is widget:
            pass
        else:
            self._log.info(f"Carregando tool SIDE (lazy): {name}", code="SIDE_LOAD")
            self.stack.removeWidget(old)
            old.deleteLater()
            self.stack.insertWidget(idx, widget)

        self.stack.setCurrentIndex(idx)

    # ── Slots ──────────────────────────────────────────────────────────

    def _on_tab_clicked(self, name: str):
        if self._expanded and self._current_name == name:
            self._set_collapsed()
        else:
            self._set_expanded(name)

    def _on_tab_double_clicked(self, name: str):
        """Duplo clique em BOTH move para o central."""
        if name not in self._tools:
            return
        tool = self._tools[name]
        if tool.category in (CategoryTool.BOTH, CategoryTool.SIDE):
            self.tool_request_move_to_central.emit(name)

    def remove_tool(self, name: str):
        if name not in self._tools:
            return
        tool = self._tools[name]

        if self._expanded and self._current_name == name:
            self._set_collapsed()

        tab = self._tabs.pop(name, None)
        if tab:
            self._tabs_layout.removeWidget(tab)
            tab.deleteLater()

        keys = list(self._tools.keys())
        if name in keys:
            idx = keys.index(name)
            w = self.stack.widget(idx)
            if w:
                self.stack.removeWidget(w)
                w.deleteLater()

        del self._tools[name]
        tool.unload()
        self.tool_closed.emit(name)
        self._log.info(f"Tool SIDE fechada: {name}", code="SIDE_CLOSED")

        if len(self._tools) == 0:
            self._set_collapsed()

    def is_tool_open(self, name: str) -> bool:
        return name in self._tools

    @property
    def expanded(self) -> bool:
        return self._expanded