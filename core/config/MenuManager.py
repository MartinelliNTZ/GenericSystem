# -*- coding: utf-8 -*-
"""
MenuManager — Construtor e gestor da toolbar + barra de menus
================================================================
Responsabilidades:
  1. Ler o ToolRegistry e obter a lista completa de ferramentas
  2. Agrupar por ToolType para criar ToolGroups (toolbar)
  3. Instanciar FileMenuItem, SystemMenuItem, HelpMenuItem
  4. Montar a MenuBar com os items e conectar sinais
  5. Encapsular MenuBar, Toolbar e seus sinais em um único lugar

  A MainWindow apenas posiciona os widgets prontos.

  O MenuManager também gerencia a lógica de "Novo", "Abrir" e "Salvar como"
  do menu Arquivo, pois essas ações pertencem ao fluxo de projeto global
  (não a um plugin específico).
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget

from core.config.LogUtils import LogUtils
from core.config.ToolRegistry import ToolRegistry
from core.enum.ToolKey import ToolKey
from core.enum.ToolType import ToolType
from core.governor.RamLimitPolicy import RamLimitPolicy, RamLimitMode
from core.governor.ResourceGovernor import ResourceGovernor
from core.manager.SignalManager import SignalManager
from core.menus.FileMenuItem import FileMenuItem
from core.menus.SystemMenuItem import SystemMenuItem
from core.menus.HelpMenuItem import HelpMenuItem
from core.model.Tool import Tool
from core.monitor.SystemMonitorService import SystemMonitorService
from resources.widgets.MenuBar import MenuBar
from resources.widgets.ToolGroup import ToolGroup
from resources.widgets.ToolBar import ToolBar
from resources.widgets.grid.GridPercentView import GridPercentView
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProjectUtil import ProjectUtil
from utils.RecentProjectsManager import RecentProjectsManager


class MenuManager(QObject):
    """
    Constrói e gerencia a toolbar E a barra de menus.

    Uso:
        manager = MenuManager()
        manager.build()
        root_layout.addWidget(manager.menu_bar)
        root_layout.addWidget(manager.toolbar_widget)

    Sinais:
        tool_activated — emitido quando o usuário clica em uma ferramenta
                         (seja na toolbar ou no menu)
    """

    tool_activated = Signal(str)  # nome da ferramenta selecionada

    _MTL_FILTER = "Projeto Aetheris (*.mtl)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups: list[ToolGroup] = []
        self._menu_bar: Optional[MenuBar] = None
        self._toolbar_widget: Optional[QWidget] = None
        self._logger = LogUtils(tool=ToolKey.SYSTEM.value, class_name="MenuManager")
        self._recent_manager = RecentProjectsManager()
        self._governor: Optional["ResourceGovernor"] = None
        self._monitor_service: Optional["SystemMonitorService"] = None
        self._monitor_view: Optional["GridPercentView"] = None

    # ────────────────────────────────────────────────────────────────
    # API pública
    # ────────────────────────────────────────────────────────────────

    def build(self) -> None:
        """
        Constrói a toolbar (ToolGroups) e popula o MenuBar.
        Chame este método antes de acessar .menu_bar e .toolbar_widget.
        """
        import time as _time
        _t0 = _time.perf_counter()

        registry = ToolRegistry()
        tools = registry.get_all()
        _t1 = _time.perf_counter()
        self._logger.info(f"[TIMING] ToolRegistry.get_all()", code="TIMING_TREG", elapsed_ms=f"{(_t1-_t0)*1000:.1f}")

        # ── 1. Criar MenuBar ──
        self._menu_bar = MenuBar()
        _t2 = _time.perf_counter()
        self._logger.info(f"[TIMING] MenuBar()", code="TIMING_MENUBAR", elapsed_ms=f"{(_t2-_t1)*1000:.1f}")

        # ── 2. Criar e registrar FileMenuItem ──
        self._file_item = FileMenuItem()
        self._file_item.novo_clicked.connect(self._on_novo)
        self._file_item.abrir_clicked.connect(self._on_abrir)
        self._file_item.salvar_como_clicked.connect(self._on_salvar_como)
        self._file_item.recente_clicked.connect(self._on_recente_abrir)
        self._file_item.sair_clicked.connect(self._on_sair)
        SignalManager.instance().recent_projects_changed.connect(
            self._file_item.rebuild_recentes_from_signal
        )
        self._menu_bar.add_menu_item(self._file_item)
        _t3 = _time.perf_counter()
        self._logger.info(f"[TIMING] FileMenuItem", code="TIMING_FILE", elapsed_ms=f"{(_t3-_t2)*1000:.1f}")

        # ── 3. Criar e registrar SystemMenuItem ──
        self._system_item = SystemMenuItem()
        _t3a = _time.perf_counter()
        self._logger.info(f"[TIMING] SystemMenuItem()", code="TIMING_SYS_INIT", elapsed_ms=f"{(_t3a-_t3)*1000:.1f}")
        self._system_item.refresh_tools()
        _t3b = _time.perf_counter()
        self._logger.info(f"[TIMING] SystemMenuItem.refresh_tools()", code="TIMING_SYS_REFRESH", elapsed_ms=f"{(_t3b-_t3a)*1000:.1f}")
        self._system_item.tool_clicked.connect(self._on_tool_clicked)
        self._menu_bar.add_menu_item(self._system_item)

        # ── 4. Criar e registrar HelpMenuItem ──
        self._help_item = HelpMenuItem()
        self._help_item.sobre_clicked.connect(self._on_sobre)
        self._menu_bar.add_menu_item(self._help_item)
        self._menu_bar.action_triggered.connect(self._on_menu_action)
        _t4 = _time.perf_counter()
        self._logger.info(f"[TIMING] HelpMenuItem + signals", code="TIMING_HELP", elapsed_ms=f"{(_t4-_t3b)*1000:.1f}")

        # ── 5. Criar ToolGroups (toolbar) ──
        grouped: Dict[ToolType, list[Tool]] = {}
        for tool in tools:
            if not tool.show_in_toolbar:
                continue
            tt = tool.tool_type
            if tt not in grouped:
                grouped[tt] = []
            grouped[tt].append(tool)

        self._groups.clear()
        for tool_type in ToolType:
            if tool_type in grouped and grouped[tool_type]:
                group = ToolGroup(tool_type=tool_type, tools=grouped[tool_type])
                self._groups.append(group)
        _t5 = _time.perf_counter()
        self._logger.info(f"[TIMING] ToolGroups ({len(self._groups)} groups)", code="TIMING_GROUPS", elapsed_ms=f"{(_t5-_t4)*1000:.1f}")

        # ── 6. Montar toolbar_widget via ToolBar ──
        if self._groups:
            self._toolbar_widget = ToolBar(groups=self._groups)
            self._toolbar_widget.tool_clicked.connect(self._on_tool_clicked)
        else:
            self._toolbar_widget = QWidget()
            self._toolbar_widget.setVisible(False)
        _t6 = _time.perf_counter()
        self._logger.info(f"[TIMING] ToolBar", code="TIMING_TOOLBAR", elapsed_ms=f"{(_t6-_t5)*1000:.1f}")

        # ── 7. System Monitor ──
        self._setup_system_monitor()
        _t7 = _time.perf_counter()
        self._logger.info(f"[TIMING] _setup_system_monitor()", code="TIMING_MONITOR", elapsed_ms=f"{(_t7-_t6)*1000:.1f}")

        self._logger.info(f"[TIMING] MenuManager.build() TOTAL", code="TIMING_TOTAL", elapsed_ms=f"{(_t7-_t0)*1000:.1f}")

    # ────────────────────────────────────────────────────────────────
    # Widgets prontos
    # ────────────────────────────────────────────────────────────────

    @property
    def menu_bar(self) -> MenuBar:
        """Barra de menus pronta para ser adicionada ao layout."""
        if self._menu_bar is None:
            raise RuntimeError("Chame build() antes de acessar menu_bar.")
        return self._menu_bar

    @property
    def toolbar_widget(self) -> QWidget:
        """Widget da toolbar pronto para ser adicionado ao layout."""
        if self._toolbar_widget is None:
            raise RuntimeError("Chame build() antes de acessar toolbar_widget.")
        return self._toolbar_widget

    @property
    def tool_groups(self) -> list[ToolGroup]:
        """Lista dos ToolGroups criados (útil para inspeção)."""
        return list(self._groups)

    # ────────────────────────────────────────────────────────────────
    # Sinais internos (conectados pela MainWindow)
    # ────────────────────────────────────────────────────────────────

    sair_clicked = Signal()
    sobre_clicked = Signal()

    # ────────────────────────────────────────────────────────────────
    # Lógica do menu Arquivo
    # ────────────────────────────────────────────────────────────────

    def _on_novo(self) -> None:
        """Novo projeto: zera current_project e root_folder nas prefs e emite project_changed."""
        try:
            self._logger.info("Criando novo projeto em branco", code="MENU_NOVO")

            # Salva current_project e root_folder como string vazia
            Preferences.save_tool_prefs(ToolKey.SYSTEM, {
                "current_project": "",
                "root_folder": "",
            })

            # Emite sinal para FileManager recarregar com estado vazio
            SignalManager.instance().project_changed.emit()
            MessageBox.show_info(
                "Projeto em branco criado.\n"
                "Use 'Salvar como' para definir local e nome.",
                title="Novo Projeto",
            )
        except Exception as e:
            self._logger.error(
                "Erro ao criar novo projeto", code="MENU_NOVO_ERR", error=str(e),
            )
            MessageBox.show_error(
                "Erro ao criar novo projeto", title="Novo Projeto", detail=str(e),
            )

    def _on_abrir(self) -> None:
        """Abrir projeto: seleciona .mtl, carrega prefs e emite project_changed."""
        try:
            self._logger.info("Abrindo projeto existente", code="MENU_ABRIR")

            file_path = ExplorerUtils.open_file(
                title="Abrir projeto",
                file_filter=self._MTL_FILTER,
                parent=self.parent(),
            )
            if not file_path:
                return  # usuário cancelou

            # Carrega o .mtl para validar
            project_data = ProjectUtil.load_project(file_path)
            if project_data is None:
                self._logger.warning(
                    "Arquivo .mtl inválido", code="MENU_ABRIR_INVALIDO",
                    file_path=file_path,
                )
                MessageBox.show_error(
                    f"O arquivo '{file_path}' não é um projeto válido.",
                    title="Abrir Projeto",
                )
                return

            # Salva nas preferências do sistema
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            sys_prefs["current_project"] = file_path
            sys_prefs["root_folder"] = os.path.dirname(file_path)
            Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

            # Atualiza last_modified
            ProjectUtil.update_last_modified(file_path)

            # Adiciona aos projetos recentes
            self._recent_manager.add_recent(file_path)

            # Emite sinal para FileManager recarregar e atualiza recentes em tempo real
            SignalManager.instance().recent_projects_changed.emit(
                self._recent_manager.get_validated()
            )
            SignalManager.instance().project_changed.emit()

            self._logger.info(
                "Projeto aberto com sucesso", code="MENU_ABRIR_OK",
                file_path=file_path,
                project_name=project_data.get("project_name", ""),
            )
            MessageBox.show_info(
                f"Projeto '{project_data.get('project_name', '')}' aberto com sucesso!",
                title="Projeto Aberto",
            )
        except Exception as e:
            self._logger.error(
                "Erro ao abrir projeto", code="MENU_ABRIR_ERR", error=str(e),
            )
            MessageBox.show_error(
                "Erro ao abrir projeto", title="Abrir Projeto", detail=str(e),
            )

    def _on_salvar_como(self) -> None:
        """Salvar como: cria novo .mtl, salva prefs e emite project_changed."""
        try:
            self._logger.info("Salvando projeto como...", code="MENU_SALVAR_COMO")

            file_path = ExplorerUtils.save_file(
                title="Salvar projeto como",
                file_filter=self._MTL_FILTER,
                parent=self.parent(),
            )
            if not file_path:
                return  # usuário cancelou

            # Extrai pasta e nome
            folder = os.path.dirname(file_path)
            project_name = os.path.splitext(os.path.basename(file_path))[0]

            # ProjectUtil cuida de verificar se já existe
            result = ProjectUtil.create_project_safe(folder, project_name)
            if result is None:
                return  # usuário cancelou a substituição

            # Salva nas preferências do sistema
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            sys_prefs["current_project"] = result["file_path"]
            sys_prefs["root_folder"] = folder
            Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

            # Adiciona aos projetos recentes
            self._recent_manager.add_recent(result["file_path"])

            # Emite sinal para FileManager recarregar e atualiza recentes em tempo real
            SignalManager.instance().recent_projects_changed.emit(
                self._recent_manager.get_validated()
            )
            SignalManager.instance().project_changed.emit()

            self._logger.info(
                "Projeto salvo como", code="MENU_SALVAR_COMO_OK",
                file_path=result["file_path"],
                project_name=project_name,
            )
            MessageBox.show_info(
                f"Projeto '{project_name}' salvo com sucesso!",
                title="Projeto Salvo",
            )
        except Exception as e:
            self._logger.error(
                "Erro ao salvar projeto como", code="MENU_SALVAR_COMO_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                "Erro ao salvar projeto", title="Salvar como", detail=str(e),
            )

    # ────────────────────────────────────────────────────────────────
    # Handler: projeto recente
    # ────────────────────────────────────────────────────────────────

    def _on_recente_abrir(self, file_path: str) -> None:
        """
        Abre um projeto da lista de recentes.

        Valida se o arquivo ainda existe. Se não existir (active=False),
        não faz nada (o RecentProjectsMenu já desabilita o item, mas
        este handler serve como fallback).
        """
        try:
            if not os.path.isfile(file_path):
                self._logger.warning(
                    "Projeto recente não encontrado em disco",
                    code="MENU_RECENTE_NOT_FOUND",
                    file_path=file_path,
                )
                MessageBox.show_warning(
                    f"O arquivo '{file_path}' não foi encontrado.\n"
                    "Ele será mantido na lista de recentes como inativo.",
                    title="Arquivo Não Encontrado",
                )
                return

            project_data = ProjectUtil.load_project(file_path)
            if project_data is None:
                self._logger.warning(
                    "Projeto recente inválido", code="MENU_RECENTE_INVALIDO",
                    file_path=file_path,
                )
                MessageBox.show_error(
                    f"O arquivo '{file_path}' não é um projeto válido.",
                    title="Projeto Inválido",
                )
                return

            # Salva nas preferências do sistema
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            sys_prefs["current_project"] = file_path
            sys_prefs["root_folder"] = os.path.dirname(file_path)
            Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

            # Atualiza last_modified
            ProjectUtil.update_last_modified(file_path)

            # Move ao topo dos recentes
            self._recent_manager.add_recent(file_path)

            # Emite sinal para FileManager recarregar e atualiza recentes em tempo real
            SignalManager.instance().recent_projects_changed.emit(
                self._recent_manager.get_validated()
            )
            SignalManager.instance().project_changed.emit()

            self._logger.info(
                "Projeto recente aberto", code="MENU_RECENTE_OK",
                file_path=file_path,
                project_name=project_data.get("project_name", ""),
            )

        except Exception as e:
            self._logger.error(
                "Erro ao abrir projeto recente", code="MENU_RECENTE_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                "Erro ao abrir projeto recente",
                title="Abrir Recente",
                detail=str(e),
            )

    # ────────────────────────────────────────────────────────────────
    # System Monitor
    # ────────────────────────────────────────────────────────────────

    def _setup_system_monitor(self) -> None:
        """Configura o monitor de CPU/RAM na barra de menus (view imediata, service deferred)."""
        # Cria view primeiro (leve, instantâneo)
        self._monitor_view = GridPercentView({
            "cpu": {
                "label": "CPU",
                "value": 0.0,
                "tooltip": "Aguardando...",
                "callback": self._on_cpu_clicked,
            },
            "ram": {
                "label": "RAM",
                "value": 0.0,
                "tooltip": "Aguardando...",
            },
        })
        self._menu_bar.add_widget_right(self._monitor_view)
        self._monitor_initialized = False
        # ResourceGovernor + SystemMonitorService NÃO são iniciados aqui!
        # São iniciados por MainWindow._open_home_on_startup() após Home abrir.

    def _init_monitor_deferred(self) -> None:
        """Inicializa ResourceGovernor e SystemMonitorService (após UI pronta) — seguro chamar múltiplas vezes."""
        if getattr(self, '_monitor_initialized', False):
            return  # já inicializou
        self._monitor_initialized = True
        import time as _time
        _t0 = _time.perf_counter()
        self._logger.info(f"Monitor deferred: iniciando ResourceGovernor", code="MON_DEFERRED_START")

        self._governor = ResourceGovernor(
            policy=RamLimitPolicy(mode=RamLimitMode.GLOBAL, fraction=0.90),
            tool_key=ToolKey.SYSTEM.value,
        )

        self._monitor_service = SystemMonitorService(
            governor=self._governor,
            interval_ms=2000,
        )
        self._monitor_service.stats_updated.connect(self._on_stats_updated)
        self._monitor_service.start()

        _t1 = _time.perf_counter()
        self._logger.info(f"Monitor deferred: completo", code="MON_DEFERRED_DONE", elapsed_ms=f"{(_t1-_t0)*1000:.1f}")

    def _on_stats_updated(self, data: dict) -> None:
        """Atualiza o GridPercentView com novos valores (animado)."""
        self._monitor_view.animate_to("cpu", data["cpu"], tooltip=data.get("cpu_tooltip"))
        self._monitor_view.animate_to("ram", data["ram"], tooltip=data.get("ram_tooltip"))

    def _on_cpu_clicked(self, key: str, value: float) -> None:
        """Callback ao clicar em CPU."""
        self._logger.info(
            "CPU monitor clicked", code="MONITOR_CPU_CLICK",
            value=value,
        )

    def shutdown(self) -> None:
        """Para serviços em background."""
        if self._monitor_service:
            self._monitor_service.stop()
            self._monitor_service = None
            self._governor = None
            self._logger.info("System monitor shut down", code="MONITOR_SHUTDOWN")

    # ────────────────────────────────────────────────────────────────
    # Métodos privados
    # ────────────────────────────────────────────────────────────────

    def _on_tool_clicked(self, tool_name: str):
        """Propaga o clique da toolbar ou menu."""
        self.tool_activated.emit(tool_name)

    def _on_menu_action(self, data: str):
        """
        Fallback para ações disparadas pelo MenuBar.
        Se o data for um tool_name conhecido, propaga como tool_activated.
        """
        # Apenas propaga se não foi tratado por File/System/Help
        registry = ToolRegistry()
        tool = registry.get(data)
        if tool is not None:
            self.tool_activated.emit(data)

    def _on_sair(self):
        """Propaga sair_clicked."""
        self.sair_clicked.emit()

    def _on_sobre(self):
        """Propaga sobre_clicked."""
        self.sobre_clicked.emit()
