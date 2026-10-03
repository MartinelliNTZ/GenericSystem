# -*- coding: utf-8 -*-
"""
Workspace — Área de trabalho do Aetheris ToolBox
==================================================
Gerencia múltiplas ferramentas via QTabBar + QStackedWidget.
Cada ferramenta é um widget registrado com um nome único.

Abas podem ser fechadas (×) e movidas (drag).
Ao clicar em uma ferramenta na toolbar, se já estiver aberta,
apenas foca a aba. Caso contrário, abre uma nova aba.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget,
    QScrollArea, QFrame, QMenu
)

from core.config.LogUtils import LogUtils
from core.enum.CategoryTool import CategoryTool
from core.model.Tool import Tool
from resources.widgets.HorizontalTab import HorizontalTab


class CentralWorkspace(QWidget):

    current_tool_changed = Signal(int, object)
    tool_closed          = Signal(str)
    tool_request_move_to_side = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: dict[str, Tool] = {}   # nome -> Tool
        self._log = LogUtils(tool="System", class_name="Workspace")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_bar = HorizontalTab(closable=True, parent=self)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.tabMoved.connect(self._on_tab_moved)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self._on_tab_context_menu)
        layout.addWidget(self.tab_bar)

        sep = QFrame()
        sep.setObjectName("workspace_separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def register_tool(self, tool: Tool, focus: bool = True) -> str:
        """Registra uma ferramenta. Retorna o nome."""
        name = tool.name
        self._tools[name] = tool

        # Placeholder no stack (na mesma posição da aba)
        placeholder = QWidget()
        self.stack.addWidget(placeholder)

        # Aba no tab bar — tabData guarda (name, title) (title viaja junto no drag)
        # BLOQUEIA sinais para evitar que QTabBar dispare currentChanged
        # automaticamente ao adicionar a primeira aba (tab_bar vazio).
        # O tabData precisa estar setado antes de qualquer currentChanged ser processado
        # para que _on_tab_changed consiga identificar a tool corretamente.
        self.tab_bar.blockSignals(True)
        tab_index = self.tab_bar.addTab("")
        if tool.tooltip:
            self.tab_bar.setTabToolTip(tab_index, tool.tooltip)
        self.tab_bar.setTabData(tab_index, (name, tool.title))
        self.tab_bar.blockSignals(False)

        self._log.info(f"Tool registrada: {name}", code="TOOL_REG")

        if focus:
            # Se currentIndex já é o da nova aba (caso da primeira aba
            # adicionada a um QTabBar vazio), setCurrentIndex é um no‑op
            # e não emite currentChanged. Precisamos chamar _on_tab_changed
            # diretamente para garantir que o conteúdo seja carregado.
            if self.tab_bar.currentIndex() == tab_index:
                self._on_tab_changed(tab_index)
            else:
                self.tab_bar.setCurrentIndex(tab_index)

        return name

    def open_tool(self, tool: Tool) -> str:
        """Abre ou foca uma ferramenta. Retorna o nome."""
        name = tool.name
        if name in self._tools:
            self.set_current_tool(name)
            return name
        return self.register_tool(tool, focus=True)

    def set_current_tool(self, name: str) -> None:
        """Muda para a aba com o nome da ferramenta."""
        for tab_id in range(self.tab_bar.count()):
            data = self.tab_bar.tabData(tab_id)
            if data and isinstance(data, tuple) and data[0] == name:
                if self.tab_bar.currentIndex() == tab_id:
                    self._on_tab_changed(tab_id)
                else:
                    self.tab_bar.setCurrentIndex(tab_id)
                return

    def current_tool_name(self) -> str | None:
        tid = self.tab_bar.currentIndex()
        if tid < 0:
            return None
        data = self.tab_bar.tabData(tid)
        if data and isinstance(data, tuple):
            return str(data[0])
        return str(data) if data else None

    def current_tool_widget(self) -> QWidget | None:
        name = self.current_tool_name()
        if name and name in self._tools:
            return self._tools[name].widget
        return None

    def is_tool_open(self, name: str) -> bool:
        return name in self._tools

    def remove_tool_by_name(self, name: str, keep_widget: bool = True) -> bool:
        tool = self._tools.get(name)
        if tool is None:
            return False

        tab_index = -1
        for tid in range(self.tab_bar.count()):
            data = self.tab_bar.tabData(tid)
            if data and isinstance(data, tuple) and data[0] == name:
                tab_index = tid
                break
        if tab_index < 0:
            return False

        w = self.stack.widget(tab_index)
        if w:
            self.stack.removeWidget(w)
            if keep_widget:
                if isinstance(w, QScrollArea):
                    inner = w.widget()
                    if inner:
                        w.takeWidget()
                        inner.setParent(None)
                w.deleteLater()
            else:
                w.deleteLater()

        self.tab_bar.removeTab(tab_index)
        del self._tools[name]

        if not keep_widget:
            tool.unload()
            self.tool_closed.emit(name)

        self._log.info(f"Aba removida (move): {name}", code="TAB_MOVED_OUT")
        return True

    # ------------------------------------------------------------------
    # Slots privados
    # ------------------------------------------------------------------

    @Slot(int, int)
    def _on_tab_moved(self, from_idx: int, to_idx: int) -> None:
        w = self.stack.widget(from_idx)
        if w:
            self.stack.removeWidget(w)
            self.stack.insertWidget(to_idx, w)
        self._log.debug(f"Aba movida: {from_idx} -> {to_idx}", code="TAB_MOVED")

    @Slot(int)
    def _on_tab_changed(self, tab_index: int) -> None:
        data = self.tab_bar.tabData(tab_index)
        if not data:
            return
        name = data[0] if isinstance(data, tuple) else str(data)
        if name not in self._tools:
            return

        tool = self._tools[name]

        # Verifica se o widget no stack já é o scroll area correto
        current_stack_widget = self.stack.widget(tab_index)
        needs_load = True

        if isinstance(current_stack_widget, QScrollArea):
            inner = current_stack_widget.widget()
            if inner is not None and hasattr(inner, 'tool_key') and inner.tool_key == name:
                needs_load = False

        if needs_load:
            self._log.info(f"Carregando tool (lazy): {name}", code="LAZY_LOAD")
            widget = tool.widget
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(widget)
            scroll.setObjectName(f"workspace_scroll_{name}")

            if current_stack_widget:
                self.stack.removeWidget(current_stack_widget)
                current_stack_widget.deleteLater()
            self.stack.insertWidget(tab_index, scroll)

        self.stack.setCurrentIndex(tab_index)
        self.current_tool_changed.emit(-1, tool.widget if tool.is_loaded else None)

    @Slot(QPoint)
    def _on_tab_context_menu(self, pos):
        tab_index = self.tab_bar.tabAt(pos)
        if tab_index < 0:
            return
        data = self.tab_bar.tabData(tab_index)
        if not data:
            return
        name = data[0] if isinstance(data, tuple) else str(data)
        if name not in self._tools:
            return

        tool = self._tools[name]
        if tool.category != CategoryTool.BOTH:
            return

        menu = QMenu(self)
        move_action = menu.addAction("Mover para Side")
        action = menu.exec(self.tab_bar.mapToGlobal(pos))
        if action == move_action:
            self.tool_request_move_to_side.emit(name)

    @Slot(int)
    def _on_tab_close_requested(self, tab_index: int) -> None:
        data = self.tab_bar.tabData(tab_index)
        if not data:
            self._log.error(
                f"Tentativa de fechar aba inexistente: tab={tab_index}",
                code="TAB_CLOSE_ERR")
            return
        name = data[0] if isinstance(data, tuple) else str(data)
        if name not in self._tools:
            self._log.error(
                f"Tentativa de fechar aba inexistente: tab={tab_index}",
                code="TAB_CLOSE_ERR")
            return

        tool = self._tools[name]

        # Dispara closeEvent no widget interno (save_prefs + preferences.save())
        w = self.stack.widget(tab_index)
        if w:
            inner = w.widget() if hasattr(w, 'widget') else None
            if inner is not None:
                inner.close()  # <-- dispara closeEvent → save_prefs → preferences.save()
            self.stack.removeWidget(w)
            w.deleteLater()

        self.tab_bar.removeTab(tab_index)
        del self._tools[name]
        tool.unload()
        self.tool_closed.emit(name)
        self._log.info(f"Aba fechada: {name}", code="TAB_CLOSED")
