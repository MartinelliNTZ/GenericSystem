# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, MenuManager e WorkspaceManager.

A MainWindow POSICIONA os widgets prontos — a lógica de negócio
fica encapsulada nos managers (MenuManager, WorkspaceManager).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QProgressBar,
)
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QIcon
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

from core.config.LogUtils import LogUtils
from core.manager.SignalManager import SignalManager
from core.model.Tool import Tool
from core.enum.ResizeMode import ResizeMode
from resources.widgets.app_bar import AppBar
from utils.ProjectUtil import ProjectUtil
from core.config.MenuManager import MenuManager
from core.config.WorkspaceManager import WorkspaceManager
from core.dialogs.AboutDialog import AboutDialog
from core.ui.HudCircularRingsLoader import HudCircularRingsLoader


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]
      [MenuManager.menu_bar]
      [MenuManager.toolbar_widget]
      [WorkspaceManager]  ← splitter: CentralWorkspace | SideWorkspace
      [ProgressBar]

    Nenhuma lógica de workspace ou menu vive aqui.
    """

    RESIZE_MARGIN = 8

    def __init__(self, tools: List[Tool]):
        super().__init__()
        self.setWindowTitle("Aetheris ToolBox")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)

        icon_path = Path(__file__).parent.parent.parent / "Aetheris.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._resize_mode: ResizeMode = ResizeMode.NATIVE
        self._resize_dragging = False
        self._resize_direction = 0
        self._resize_rect = QRect()
        self._resize_global_start = QPoint()

        self._build_ui(tools)
        self._setup_resize_mode()

        # ── Startup: console pronto e sinais de inicialização ──
        self._emit_startup_signals()

    # ── Resize mode ────────────────────────────────────────────────

    @property
    def resize_mode(self) -> ResizeMode:
        return self._resize_mode

    @resize_mode.setter
    def resize_mode(self, mode: ResizeMode) -> None:
        if mode == self._resize_mode:
            return
        self._resize_mode = mode
        self._setup_resize_mode()

    def _setup_resize_mode(self) -> None:
        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info("Modo de resize alterado", code="RESIZE_MODE", mode=self._resize_mode.value)
        self.setMouseTracking(False)
        if self._resize_mode == ResizeMode.CURSOR:
            self.setMouseTracking(True)

    # ── nativeEvent (Windows) ──────────────────────────────────────

    def nativeEvent(self, event_type: bytes, message) -> tuple:
        if self._resize_mode != ResizeMode.NATIVE or sys.platform != "win32":
            return super().nativeEvent(event_type, message)
        if event_type != b"windows_generic_MSG":
            return super().nativeEvent(event_type, message)
        try:
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message != 0x0084:
                return super().nativeEvent(event_type, message)
            raw = msg.lParam
            screen_x = ctypes.c_short(raw & 0xFFFF).value
            screen_y = ctypes.c_short((raw >> 16) & 0xFFFF).value
            return self._hit_test(screen_x, screen_y)
        except Exception:
            return super().nativeEvent(event_type, message)

    def _hit_test(self, screen_x: int, screen_y: int) -> tuple:
        if self.isMaximized() or self.isFullScreen():
            return False, 0
        r = self.frameGeometry()
        x = screen_x - r.x()
        y = screen_y - r.y()
        w, h = r.width(), r.height()
        m = self.RESIZE_MARGIN
        on_left = x < m
        on_right = x > w - m
        on_top = y < m
        on_bottom = y > h - m
        HT_LEFT, HT_RIGHT, HT_TOP, HT_BOTTOM = 10, 11, 12, 15
        HT_TOPLEFT, HT_TOPRIGHT = 13, 14
        HT_BOTTOMLEFT, HT_BOTTOMRIGHT = 16, 17
        if on_top and on_left: return True, HT_TOPLEFT
        if on_top and on_right: return True, HT_TOPRIGHT
        if on_bottom and on_left: return True, HT_BOTTOMLEFT
        if on_bottom and on_right: return True, HT_BOTTOMRIGHT
        if on_left: return True, HT_LEFT
        if on_right: return True, HT_RIGHT
        if on_top: return True, HT_TOP
        if on_bottom: return True, HT_BOTTOM
        return False, 0

    # ── Cursor resize ──────────────────────────────────────────────

    def _get_resize_direction(self, pos: QPoint) -> int:
        if self.isMaximized() or self.isFullScreen():
            return 0
        r = self.rect()
        x, y = pos.x(), pos.y()
        w, h = r.width(), r.height()
        m = self.RESIZE_MARGIN
        direction = 0
        if x < m: direction |= 4
        if x > w - m: direction |= 8
        if y < m: direction |= 1
        if y > h - m: direction |= 2
        return direction

    def _cursor_for_direction(self, direction: int) -> Qt.CursorShape:
        if direction in (5, 10): return Qt.CursorShape.SizeFDiagCursor  # NW=1|4, SE=2|8
        if direction in (9, 6): return Qt.CursorShape.SizeBDiagCursor  # NE=1|8, SW=2|4
        if direction in (4, 8): return Qt.CursorShape.SizeHorCursor
        if direction in (1, 2): return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    def mouseMoveEvent(self, event):
        if self._resize_mode != ResizeMode.CURSOR:
            super().mouseMoveEvent(event); return
        if self._resize_dragging:
            self._do_resize(event.globalPosition().toPoint()); event.accept(); return
        direction = self._get_resize_direction(event.position().toPoint())
        self.setCursor(self._cursor_for_direction(direction)) if direction else self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self._resize_mode != ResizeMode.CURSOR:
            super().mousePressEvent(event); return
        if event.button() == Qt.MouseButton.LeftButton:
            direction = self._get_resize_direction(event.position().toPoint())
            if direction:
                self._resize_dragging = True
                self._resize_direction = direction
                self._resize_rect = QRect(self.geometry())
                self._resize_global_start = event.globalPosition().toPoint()
                event.accept(); return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resize_mode != ResizeMode.CURSOR:
            super().mouseReleaseEvent(event); return
        if event.button() == Qt.MouseButton.LeftButton and self._resize_dragging:
            self._resize_dragging = False; self._resize_direction = 0; event.accept(); return
        super().mouseReleaseEvent(event)

    def _do_resize(self, global_pos: QPoint) -> None:
        start = self._resize_global_start
        dx = global_pos.x() - start.x()
        dy = global_pos.y() - start.y()
        r = QRect(self._resize_rect)
        dir_ = self._resize_direction
        min_w, min_h = self.minimumSize().width(), self.minimumSize().height()
        max_w, max_h = self.maximumWidth(), self.maximumHeight()
        if dir_ & 1:
            new_h = r.height() - dy
            if new_h < min_h: new_h = min_h
            elif 0 < max_h < new_h: new_h = max_h
            r.setY(r.bottom() - new_h); r.setHeight(new_h)
        if dir_ & 2:
            new_h = r.height() + dy
            if new_h < min_h: new_h = min_h
            elif 0 < max_h < new_h: new_h = max_h
            r.setHeight(new_h)
        if dir_ & 4:
            new_w = r.width() - dx
            if new_w < min_w: new_w = min_w
            elif 0 < max_w < new_w: new_w = max_w
            r.setX(r.right() - new_w); r.setWidth(new_w)
        if dir_ & 8:
            new_w = r.width() + dx
            if new_w < min_w: new_w = min_w
            elif 0 < max_w < new_w: new_w = max_w
            r.setWidth(new_w)
        if r != self.geometry():
            self.setGeometry(r)
            self._resize_global_start = global_pos
            self._resize_rect = QRect(self.geometry())

    # ── UI Build ───────────────────────────────────────────────────

    def _build_ui(self, tools: List[Tool]) -> None:
        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info("Construindo interface", code="UI_BUILD", num_tools=len(tools))

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # AppBar
        self.appbar = AppBar()
        self.appbar.minimize_clicked.connect(self.showMinimized)
        self.appbar.maximize_restore_clicked.connect(self._toggle_maximize_restore)
        self.appbar.close_clicked.connect(self.close)
        root_layout.addWidget(self.appbar)

        # Menu + Toolbar
        self._menu_manager = MenuManager()
        self._menu_manager.build()
        self._menu_manager.tool_activated.connect(self._on_tool_activated)
        self._menu_manager.sair_clicked.connect(self.close)
        self._menu_manager.sobre_clicked.connect(self._show_about)
        root_layout.addWidget(self._menu_manager.menu_bar)
        root_layout.addWidget(self._menu_manager.toolbar_widget)

        # Workspace
        self._workspace_manager = WorkspaceManager(tools)
        root_layout.addWidget(self._workspace_manager, 1)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(10000)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(" %p% - aguardando... ")
        self.progress.setFixedHeight(20)
        root_layout.addWidget(self.progress)
        SignalManager.instance().progress_update.connect(self._on_progress_update)
        SignalManager.instance().progress_reset.connect(self._on_progress_reset)

        # HUD Loader (overlay)
        self._hud = HudCircularRingsLoader(self)
        self._hud.setGeometry(self.rect())
        SignalManager.instance().hud_show.connect(self._on_hud_show)
        SignalManager.instance().hud_update.connect(self._on_hud_update)
        SignalManager.instance().hud_hide.connect(self._on_hud_hide)

        # Ciclo de vida de execução
        SignalManager.instance().execution_started.connect(self._on_execution_started)
        SignalManager.instance().execution_finished.connect(self._on_execution_finished)
        SignalManager.instance().execution_cancelled.connect(self._on_execution_cancelled)

        # Project status na AppBar
        SignalManager.instance().project_changed.connect(self._update_appbar_project_status)

    # ── Handlers ───────────────────────────────────────────────────

    def _emit_startup_signals(self) -> None:
        """
        Emite sinais de inicializacao e mensagem de boas-vindas no console.
        O ConsolePlugin ja foi pre-carregado pelo WorkspaceManager,
        portanto ja esta ouvindo os sinais console_message / console_html.

        A Home é aberta APÓS toda a UI estar construída e visível,
        via QTimer.singleShot para garantir que event loop já iniciou.
        """
        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info(
            "Aplicacao iniciada — emitindo sinais de startup",
            code="STARTUP_EMIT",
        )
        signals = SignalManager.instance()
        signals.app_startup.emit()
        signals.console_html.emit(
            '<b style="color:#10B981;">Aetheris ToolBox</b> '
            '<span style="color:#78716C;">iniciado — console pronto.</span>'
        )
        signals.console_message.emit(
            "Selecione uma ferramenta no menu para comecar."
        )

        # Abre Home ANTES do monitor deferred (que é pesado e lento)
        # Garante que UI aparece imediatamente para o usuário
        from PySide6.QtCore import QTimer as _Qtimer
        _Qtimer.singleShot(0, self._open_home_on_startup)

    def _open_home_on_startup(self) -> None:
        """Abre a Home no workspace central, depois agenda monitor deferred."""
        logger = LogUtils(tool="System", class_name="MainWindow")
        if hasattr(self, '_workspace_manager') and self._workspace_manager is not None:
            self._workspace_manager.switch_to_tool("Home")
            logger.info("Home aberta via startup signal", code="HOME_OPENED")
        else:
            logger.warning("WorkspaceManager indisponivel ao abrir Home", code="HOME_OPEN_FAIL")

        # Carrega status inicial do projeto na AppBar
        self._update_appbar_project_status()

        # Depois de abrir Home, agenda o monitor deferred (ResourceGovernor + psutil)
        # para rodar APÓS a UI estar totalmente responsiva
        if hasattr(self, '_menu_manager') and self._menu_manager is not None:
            from PySide6.QtCore import QTimer as _Qtimer
            _Qtimer.singleShot(0, self._menu_manager._init_monitor_deferred)

    def _show_about(self):
        from core.dialogs.AboutDialog import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()

    def _on_tool_activated(self, tool_name: str):
        self._workspace_manager.open_tool(tool_name)

    @property
    def left_workspace(self):
        """Retorna o SideWorkspace esquerdo (FileManager fixo)."""
        return self._workspace_manager.left_workspace

    @property
    def central_workspace(self):
        return self._workspace_manager.central_workspace

    @property
    def right_workspace(self):
        """Retorna o SideWorkspace direito (Console fixo)."""
        return self._workspace_manager.right_workspace

    @property
    def side_workspace(self):
        """Compatibilidade: retorna o right workspace."""
        return self._workspace_manager.right_workspace

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._workspace_manager.get_tool(name)

    def switch_to_tool(self, name: str) -> bool:
        return self._workspace_manager.switch_to_tool(name)

    def switch_to_console(self) -> None:
        self._workspace_manager.switch_to_console()

    def _on_progress_update(self, value: float):
        scaled = int(round(value * 100.0))
        self.progress.setValue(scaled)
        if value <= 0:
            self.progress.setFormat(" %p% - aguardando... ")
        elif value >= 100:
            self.progress.setFormat(" 100% - concluído! ")
        else:
            self.progress.setFormat(f" {value:.2f}% - executando... ")

    def closeEvent(self, event):
        """Garante que serviços em background sejam parados ao fechar."""
        if hasattr(self, '_menu_manager'):
            self._menu_manager.shutdown()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(self.rect())

    def _on_hud_show(self, data: dict):
        msg = data.get("message", "Processando...")
        timer = data.get("timer", None)     # Modo 2: segundos
        stages = data.get("stages", None)   # Modo 3: (segundos, num_etapas)
        eta = data.get("eta", None)         # ETA em segundos

        if timer is not None:
            self._hud.start_timer(float(timer), msg)
        elif stages is not None and isinstance(stages, (list, tuple)) and len(stages) == 2:
            self._hud.start_staged(float(stages[0]), int(stages[1]), msg)
        else:
            self._hud.set_progress(0.0, msg)

        if eta is not None:
            self._hud.set_eta(float(eta))

        self._hud.show_loader()

    def _on_hud_update(self, data: dict):
        msg = data.get("message", "")
        progress = data.get("progress", None)
        eta = data.get("eta", None)         # ETA em segundos (atualizacao)

        if progress is not None:
            # Atualiza valores diretamente sem set_progress()
            # para não resetar o modo automático (timer/staged)
            self._hud.progress = max(0.0, min(100.0, float(progress)))
        if msg:
            self._hud.message = msg
        if eta is not None:
            self._hud.set_eta(float(eta))
        if progress is not None or msg or eta is not None:
            self._hud.update()

    def _on_hud_hide(self):
        self._hud.hide_loader()

    def _on_progress_reset(self):
        """Reseta a barra de progresso para 0%."""
        self.progress.setValue(0)
        self.progress.setFormat(" %p% - aguardando... ")

    def _on_execution_started(self, tool_name: str):
        """Início de execução: mostra HUD e reseta progresso."""
        self._hud.set_progress(0.0, f"Iniciando {tool_name}...")
        self._hud.show_loader()
        self._on_progress_reset()

    def _on_execution_finished(self, tool_name: str):
        """Fim de execução: esconde HUD e reseta progress para 0%."""
        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info("Execucao finalizada, resetando progress", code="EXEC_DONE_RESET", tool=tool_name)
        self._hud.hide_loader()
        self._on_progress_reset()

    def _on_execution_cancelled(self, tool_name: str):
        """Cancelamento: esconde HUD e reseta progresso."""
        self._hud.hide_loader()
        self._on_progress_reset()

    # ── Project status na AppBar ───────────────────────────────────

    def _update_appbar_project_status(self) -> None:
        """
        Lê current_project das preferências do sistema e atualiza a AppBar.
        Se não houver projeto ativo, exibe [Não salvo].
        """
        try:
            from utils.Preferences import Preferences
            from core.enum.ToolKey import ToolKey
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            current_project = sys_prefs.get("current_project", None)
            if current_project and Path(current_project).is_file():
                project_data = ProjectUtil.load_project(current_project)
                if project_data:
                    name = project_data.get("project_name", "")
                    path = project_data.get("file_path", current_project)
                    self.appbar.set_project_status(name, path)
                else:
                    self.appbar.set_project_status(
                        Path(current_project).stem,
                        current_project,
                    )
            else:
                self.appbar.clear_project_status()
        except Exception:
            self.appbar.clear_project_status()

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
