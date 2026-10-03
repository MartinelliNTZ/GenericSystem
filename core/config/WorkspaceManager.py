# -*- coding: utf-8 -*-
"""
WorkspaceManager — Gestor dos workspaces Central + Side Esquerdo + Side Direito
=================================================================================
Responsabilidades:
  1. Criar e gerenciar o QSplitter entre LeftSide, CentralWorkspace e RightSide
  2. Registrar ferramentas no workspace correto (LEFT_SIDE, RIGHT_SIDE, CENTRAL, BOTH)
  3. Roteamento de ativação de ferramentas para o workspace adequado
  4. Movimentação de ferramentas BOTH entre workspaces
  5. Persistência do tamanho dos SideWorkspaces
  6. Gerenciamento do redimensionamento do splitter

A MainWindow recebe o widget pronto e só o posiciona no layout.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout

from core.enum.CategoryTool import CategoryTool
from core.enum.ToolKey import ToolKey
from core.model.Tool import Tool
from core.config.LogUtils import LogUtils
from core.ui.CentralWorkspace import CentralWorkspace
from core.ui.SideWorkspace import SideWorkspace
from utils.Preferences import Preferences


class WorkspaceManager(QWidget):
    """
    Gerencia 3 workspaces: LeftSide | CentralWorkspace | RightSide.

    Uso:
        manager = WorkspaceManager(tools)
        root_layout.addWidget(manager)

    Sinais:
        tool_activated — emitido quando uma ferramenta é ativada
    """

    tool_activated = Signal(str)

    # Larguras padrão
    SIDE_MIN_COLLAPSED = 24  # W_TABS
    SIDE_W_DEFAULT = 280    # largura padrão do conteúdo lateral

    def __init__(self, tools: List[Tool], parent=None):
        super().__init__(parent)
        self._tools: List[Tool] = tools
        self._tool_map: Dict[str, Tool] = {t.name: t for t in tools}
        self._sys_prefs: Dict[str, Any] = Preferences.load_tool_prefs(ToolKey.SYSTEM)
        self.logger = LogUtils(tool="System", class_name="WorkspaceManager")

        # Widgets internos
        self._left_workspace: Optional[SideWorkspace] = None
        self._central_workspace: Optional[CentralWorkspace] = None
        self._right_workspace: Optional[SideWorkspace] = None
        self._splitter: Optional[QSplitter] = None

        # Estado dos sides
        self._left_content_width: int = self.SIDE_W_DEFAULT
        self._right_content_width: int = self.SIDE_W_DEFAULT
        self._left_drag_lock: bool = True
        self._right_drag_lock: bool = True

        self._build()

    # ────────────────────────────────────────────────────────────────
    # Construção
    # ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        """Constrói o splitter com 3 workspaces e registra as ferramentas."""
        log = LogUtils(tool="System", class_name="WorkspaceManager")
        log.info("Construindo workspaces", code="WS_BUILD", num_tools=len(self._tools))

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setObjectName("workspace_splitter")

        # Layout do WorkspaceManager: só contém o splitter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter, 1)

        # ── Left Side ──
        self._left_workspace = SideWorkspace(side="left")
        self._left_workspace.setObjectName("left_side_workspace")
        self._splitter.addWidget(self._left_workspace)

        # ── Central ──
        self._central_workspace = CentralWorkspace()
        self._splitter.addWidget(self._central_workspace)

        # ── Right Side ──
        self._right_workspace = SideWorkspace(side="right")
        self._right_workspace.setObjectName("right_side_workspace")
        self._splitter.addWidget(self._right_workspace)

        # Restaura larguras salvas
        saved_left = self._sys_prefs.get("left_side_content_width", self.SIDE_W_DEFAULT)
        self._left_content_width = saved_left
        saved_right = self._sys_prefs.get("right_side_content_width", self.SIDE_W_DEFAULT)
        self._right_content_width = saved_right

        # Inicializa colapsados
        self._left_workspace.collapse()
        self._right_workspace.collapse()

        # Pré-carrega o Console para que ele já esteja ouvindo sinais
        # desde o startup (ex: console_message, app_startup)
        console_tool = self._tool_map.get(ToolKey.CONSOLE.value)
        if console_tool:
            _ = console_tool.widget  # Força a instanciação do widget
            log.info(
                "Console pre-carregado para startup",
                code="CONSOLE_PRELOAD",
            )

        QTimer.singleShot(0, self._init_splitter_sizes)
        self._left_drag_lock = True
        self._right_drag_lock = True

        # Conecta sinais dos sides
        self._left_workspace.size_changed.connect(self._on_left_size_changed)
        self._right_workspace.size_changed.connect(self._on_right_size_changed)
        self._splitter.splitterMoved.connect(self._on_splitter_moved)

        # Conecta movimentação BOTH
        self._central_workspace.tool_request_move_to_side.connect(self._move_tool_to_side)
        self._left_workspace.tool_request_move_to_central.connect(self._move_tool_to_central)
        self._right_workspace.tool_request_move_to_central.connect(self._move_tool_to_central)

        # Registra ferramentas nos workspaces
        for tool in self._tools:
            cat = tool.category

            if cat == CategoryTool.INSTANT:
                pass  # auto-destrutivas

            elif cat == CategoryTool.LEFT_SIDE:
                self._left_workspace.register_tool(tool)

            elif cat in (CategoryTool.SIDE, CategoryTool.RIGHT_SIDE):
                self._right_workspace.register_tool(tool)

            elif cat == CategoryTool.BOTH:
                # BOTH vai para o right side por padrão
                self._right_workspace.register_tool(tool)

            elif tool.name == "Home":
                self._central_workspace.register_tool(tool, focus=False)

        # Home NÃO é aberta aqui — é aberta via sinal app_startup
        # após toda a UI estar pronta e visível.

        # Ambos os workspaces laterais ficam recolhidos por padrão.
        # O utilizador expande clicando nas abas verticais.
        # fm_name = ToolKey.FILE_MANAGER.value
        # if self._left_workspace.is_tool_open(fm_name):
        #     self._left_workspace.expand(fm_name, self._left_content_width)
        #
        # console_name = ToolKey.CONSOLE.value
        # if self._right_workspace.is_tool_open(console_name):
        #     self._right_workspace.expand(console_name, self._right_content_width)

    # ────────────────────────────────────────────────────────────────
    # API pública para a MainWindow
    # ────────────────────────────────────────────────────────────────

    @property
    def left_workspace(self) -> SideWorkspace:
        if self._left_workspace is None:
            raise RuntimeError("WorkspaceManager não foi construído.")
        return self._left_workspace

    @property
    def central_workspace(self) -> CentralWorkspace:
        if self._central_workspace is None:
            raise RuntimeError("WorkspaceManager não foi construído.")
        return self._central_workspace

    @property
    def right_workspace(self) -> SideWorkspace:
        if self._right_workspace is None:
            raise RuntimeError("WorkspaceManager não foi construído.")
        return self._right_workspace

    # ── Compatibilidade com código legado ───────────────────────────

    @property
    def side_workspace(self) -> SideWorkspace:
        """Retorna o right workspace (compatibilidade)."""
        return self.right_workspace

    def get_tool(self, name: str) -> Optional[Tool]:
        """Retorna uma tool pelo nome."""
        return self._tool_map.get(name)

    def open_tool(self, tool_name: str) -> None:
        """
        Abre ou foca uma ferramenta no workspace correto.
        Chamado quando o usuário clica na toolbar ou menu.
        """
        tool = self._tool_map.get(tool_name)
        if not tool:
            return

        cat = tool.category

        if cat == CategoryTool.INSTANT:
            _ = tool.widget
            self.tool_activated.emit(tool_name)
            return

        if cat == CategoryTool.LEFT_SIDE:
            self._left_workspace.open_tool(tool)
        elif cat in (CategoryTool.SIDE, CategoryTool.RIGHT_SIDE):
            self._right_workspace.open_tool(tool)
        elif cat == CategoryTool.BOTH:
            # Tenta no side em que está aberta; senão, abre no central
            if self._right_workspace.is_tool_open(tool_name):
                self._right_workspace.open_tool(tool)
            elif self._left_workspace.is_tool_open(tool_name):
                self._left_workspace.open_tool(tool)
            else:
                self._central_workspace.open_tool(tool)
        else:
            self._central_workspace.open_tool(tool)

        self.tool_activated.emit(tool_name)

    def switch_to_tool(self, name: str) -> bool:
        """Muda para uma ferramenta já aberta."""
        if self._central_workspace.is_tool_open(name):
            self._central_workspace.set_current_tool(name)
            return True
        if self._right_workspace.is_tool_open(name):
            self._right_workspace.expand(name, self._right_content_width)
            return True
        if self._left_workspace.is_tool_open(name):
            self._left_workspace.expand(name, self._left_content_width)
            return True
        return False

    def switch_to_console(self) -> None:
        """Atalho para abrir o Console."""
        self.switch_to_tool("Console")

    # ────────────────────────────────────────────────────────────────
    # Redimensionamento do splitter
    # ────────────────────────────────────────────────────────────────

    def _init_splitter_sizes(self):
        """Força o splitter para estado inicial com sides colapsados."""
        if self._splitter is None:
            return
        try:
            total = max(300, self._splitter.width())
            tabs = SideWorkspace.W_TABS
            central = total - 2 * tabs
            self._splitter.setSizes([tabs, central, tabs])
        except Exception as e:
            self.logger.error("Falha ao inicializar tamanhos do splitter",
                              code="SPLIT_INIT_ERR", error=str(e))

    def _on_left_size_changed(self, total_width: int):
        """Ajusta os tamanhos do splitter conforme LeftSideWorkspace."""
        if self._splitter is None:
            return

        if total_width <= SideWorkspace.W_TABS:
            self._left_drag_lock = True
            sizes = self._splitter.sizes()
            if len(sizes) >= 3:
                self._splitter.setSizes([
                    SideWorkspace.W_TABS,
                    sizes[1] + (sizes[0] - SideWorkspace.W_TABS),
                    sizes[2],
                ])
            self._sys_prefs["left_side_collapsed"] = True
            self._sys_prefs["left_side_content_width"] = self._left_content_width
            Preferences.save_tool_prefs(ToolKey.SYSTEM, self._sys_prefs)
        else:
            self._left_drag_lock = False
            sizes = self._splitter.sizes()
            if len(sizes) >= 3:
                # Distribui: tira do central
                extra = total_width - sizes[0]
                self._splitter.setSizes([
                    total_width,
                    max(100, sizes[1] - extra),
                    sizes[2],
                ])

    def _on_right_size_changed(self, total_width: int):
        """Ajusta os tamanhos do splitter conforme RightSideWorkspace."""
        if self._splitter is None:
            return

        if total_width <= SideWorkspace.W_TABS:
            self._right_drag_lock = True
            sizes = self._splitter.sizes()
            if len(sizes) >= 3:
                self._splitter.setSizes([
                    sizes[0],
                    sizes[1] + (sizes[2] - SideWorkspace.W_TABS),
                    SideWorkspace.W_TABS,
                ])
            self._sys_prefs["right_side_collapsed"] = True
            self._sys_prefs["right_side_content_width"] = self._right_content_width
            Preferences.save_tool_prefs(ToolKey.SYSTEM, self._sys_prefs)
        else:
            self._right_drag_lock = False
            sizes = self._splitter.sizes()
            if len(sizes) >= 3:
                extra = total_width - sizes[2]
                self._splitter.setSizes([
                    sizes[0],
                    max(100, sizes[1] - extra),
                    total_width,
                ])

    def _on_splitter_moved(self, pos: int, idx: int):
        """Salva a largura do conteúdo side quando o usuário arrasta."""
        if self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if len(sizes) < 3:
            return

        # idx 0 = left handle, idx 1 = right handle
        if idx == 0 and not self._left_drag_lock:
            side_total = sizes[0]
            content_w = side_total - SideWorkspace.W_TABS
            if content_w > 20:
                self._left_content_width = content_w
                self._sys_prefs["left_side_collapsed"] = False
                self._sys_prefs["left_side_content_width"] = content_w
                Preferences.save_tool_prefs(ToolKey.SYSTEM, self._sys_prefs)
        elif idx == 1 and not self._right_drag_lock:
            side_total = sizes[2]
            content_w = side_total - SideWorkspace.W_TABS
            if content_w > 20:
                self._right_content_width = content_w
                self._sys_prefs["right_side_collapsed"] = False
                self._sys_prefs["right_side_content_width"] = content_w
                Preferences.save_tool_prefs(ToolKey.SYSTEM, self._sys_prefs)

    # ────────────────────────────────────────────────────────────────
    # Movimentação BOTH entre workspaces
    # ────────────────────────────────────────────────────────────────

    def _move_tool_to_side(self, tool_name: str):
        """Move uma ferramenta BOTH do Central para o Side (direito por padrão)."""
        tool = self._tool_map.get(tool_name)
        if not tool:
            return
        self._central_workspace.remove_tool_by_name(tool_name, keep_widget=True)

        # Tenta mover pro side em que já estava, senão vai pro direito
        if self._right_workspace.is_tool_open(tool_name):
            self._right_workspace.expand(tool_name, self._right_content_width)
        elif self._left_workspace.is_tool_open(tool_name):
            self._left_workspace.expand(tool_name, self._left_content_width)
        else:
            if not self._right_workspace.is_tool_open(tool_name):
                self._right_workspace.register_tool(tool)
            self._right_workspace.expand(tool_name, self._right_content_width)

    def _move_tool_to_central(self, tool_name: str):
        """Move uma ferramenta BOTH de qualquer side para o Central."""
        tool = self._tool_map.get(tool_name)
        if not tool:
            return

        # Remove de qualquer side
        if self._right_workspace.is_tool_open(tool_name):
            self._right_workspace.remove_tool(tool_name)
        elif self._left_workspace.is_tool_open(tool_name):
            self._left_workspace.remove_tool(tool_name)

        if not self._central_workspace.is_tool_open(tool_name):
            self._central_workspace.open_tool(tool)