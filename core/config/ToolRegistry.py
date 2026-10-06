# -*- coding: utf-8 -*-
"""
ToolRegistry — Registro centralizado de ferramentas (lazy loading)
===================================================================
Aqui ficam definidas TODAS as ferramentas do sistema.
Cada ferramenta é um objeto Tool com lazy loading via widget_factory.

Uso:
    registry = ToolRegistry()
    registry.register_default_tools()
    tools = registry.get_all()       # lista de objetos Tool
    widget = tools[0].widget          # lazy: cria aqui
"""

from __future__ import annotations

from typing import Callable, List, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from core.enum.CategoryTool import CategoryTool
from core.enum.MenuCategory import MenuCategory
from core.enum.ToolKey import ToolKey
from core.enum.ToolType import ToolType
from core.model.Tool import Tool
from utils.StringUtils import StringUtils


def _make_factory(module_path: str, class_name: str) -> Callable[[], QWidget]:
    """
    Retorna uma factory que importa e instancia a classe sob demanda.
    Função no nível do módulo para ser usada na definição do dict _TOOLS.

    module_path: caminho do módulo sem .py (ex: "plugins.home.HomePlugin")
    class_name:  nome exato da classe (ex: "HomePlugin")
    """

    def factory() -> QWidget:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        return cls()

    return factory


class ToolRegistry:
    """
    Singleton que mantém o registro de todas as ferramentas disponiveis.

    Cada tool e um objeto Tool com lazy loading via widget_factory.
    """

    _instance: ToolRegistry | None = None

    def __new__(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: dict[str, Tool] = {}
            cls._instance._order: list[str] = []
        return cls._instance

    # ══════════════════════════════════════════════════════════════════
    # Definição direta de todas as ferramentas como objetos Tool
    # ══════════════════════════════════════════════════════════════════
    # Para adicionar uma NOVA ferramenta:
    #   1. Crie a classe widget em plugins/NomeDaFerramenta/NomeDaFerramentaPlugin.py
    #   2. Adicione uma entrada no dict _TOOLS abaixo
    #      com Tool() contendo name, title, widget_factory, etc.
    #
    # REGRA: module_path = "plugins.pasta_plugin.NomeDoArquivoPlugin"
    #        class_name   = mesmo nome da classe (PascalCase + Plugin)
    # ══════════════════════════════════════════════════════════════════

    _TOOLS: dict[str, Tool] = {
        ToolKey.HOME.value: Tool(
            name=ToolKey.HOME.value,
            title="Inicial",
            widget_factory=_make_factory(
                "plugins.home.HomePlugin", "HomePlugin"
            ),
            tooltip=f"Pagina inicial do {StringUtils.APP_NAME}",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.CENTRAL,
        ),
        ToolKey.CONSOLE.value: Tool(
            name=ToolKey.CONSOLE.value,
            title="Console",
            widget_factory=_make_factory(
                "plugins.console.ConsolePlugin", "ConsolePlugin"
            ),
            tooltip="Console de execucao compartilhado",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.RIGHT_SIDE,
            show_in_toolbar=False,
        ),
        ToolKey.LOGVIEWER.value: Tool(
            name=ToolKey.LOGVIEWER.value,
            title="LogViewer",
            widget_factory=_make_factory(
                "plugins.log_viewer.LogViewerPlugin", "LogViewerPlugin"
            ),
            tooltip="Visualizador de logs do sistema",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.BOTH,
        ),
        ToolKey.HOTKEY_PLUGIN.value: Tool(
            name=ToolKey.HOTKEY_PLUGIN.value,
            title="Teclador",
            widget_factory=_make_factory(
                "plugins.hotkey.HotkeyPlugin", "HotkeyPlugin"
            ),
            tooltip="Automacao de teclado: digita uma string ao pressionar F",
            tool_type=ToolType.FOLDER,
            category=CategoryTool.CENTRAL,
        ),
        ToolKey.PREFERENCES.value: Tool(
            name=ToolKey.PREFERENCES.value,
            title="Preferências",
            widget_factory=_make_factory(
                "plugins.preferences_manager.PreferencesPlugin",
                "PreferencesPlugin",
            ),
            tooltip="Gerenciar preferências das ferramentas do sistema",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=False,
            menu_category=MenuCategory.SYSTEM,
        ),
        ToolKey.CONFIGURATION.value: Tool(
            name=ToolKey.CONFIGURATION.value,
            title="Configuração",
            widget_factory=_make_factory(
                "plugins.configuration_manager.ConfigurationPlugin",
                "ConfigurationPlugin",
            ),
            tooltip="Configurações gerais do sistema",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.BOTH,
            show_in_toolbar=False,
            menu_category=MenuCategory.SYSTEM,
        ),
        ToolKey.RENAMER.value: Tool(
            name=ToolKey.RENAMER.value,
            title="Renomeador",
            widget_factory=_make_factory(
                "plugins.renamer.RenamerPlugin",
                "RenamerPlugin",
            ),
            tooltip="Renomear arquivos em lote (prefixo, sufixo, substituir, etc.)",
            tool_type=ToolType.FOLDER,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
        ToolKey.SAVE_PROJECT.value: Tool(
            name=ToolKey.SAVE_PROJECT.value,
            title="Gerenciar Projeto",
            widget_factory=_make_factory(
                "plugins.project_manager.SaveProjectPlugin",
                "SaveProjectPlugin",
            ),
            tooltip="Criar ou salvar projeto atual (.mtl)",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.INSTANT,
            show_in_toolbar=True,
        ),
        ToolKey.FILE_MANAGER.value: Tool(
            name=ToolKey.FILE_MANAGER.value,
            title="Explorador",
            widget_factory=_make_factory(
                "plugins.file_manager.FileManagerPlugin",
                "FileManagerPlugin",
            ),
            tooltip="Explorador de arquivos interno do projeto",
            tool_type=ToolType.FOLDER,
            category=CategoryTool.LEFT_SIDE,
            show_in_toolbar=True,
        ),
        ToolKey.PROJECT_STRUCTURE.value: Tool(
            name=ToolKey.PROJECT_STRUCTURE.value,
            title="Gerenciador de Estrutura",
            widget_factory=_make_factory(
                "plugins.project_structure_manager.ProjectStructurePlugin",
                "ProjectStructurePlugin",
            ),
            tooltip="Confere e padroniza a estrutura de pastas dos projetos",
            tool_type=ToolType.VERRA,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
        ToolKey.PROJECT_DATABASE.value: Tool(
            name=ToolKey.PROJECT_DATABASE.value,
            title="Banco de Dados",
            widget_factory=_make_factory(
                "plugins.project_database_manager.ProjectDatabasePlugin",
                "ProjectDatabasePlugin",
            ),
            tooltip="Banco de dados (JSON) das pastas e anos criados por OS",
            tool_type=ToolType.VERRA,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
        ToolKey.OS_TRACKER.value: Tool(
            name=ToolKey.OS_TRACKER.value,
            title="Acompanhamento de OS",
            widget_factory=_make_factory(
                "plugins.os_tracker.OsTrackerPlugin",
                "OsTrackerPlugin",
            ),
            tooltip="Escolha uma OS e visualize seus dados (SubOS, cliente, CNPJ)",
            tool_type=ToolType.VERRA,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
        ToolKey.ICO_CONVERTER.value: Tool(
            name=ToolKey.ICO_CONVERTER.value,
            title="Conversor ICO",
            widget_factory=_make_factory(
                "plugins.ico_converter.IcoConverterPlugin",
                "IcoConverterPlugin",
            ),
            tooltip="Converter imagens (PNG, JPG, etc.) para formato ICO do Windows",
            tool_type=ToolType.RASTER,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
        ToolKey.IMAGE_CONVERTER.value: Tool(
            name=ToolKey.IMAGE_CONVERTER.value,
            title="Conversor de Imagens",
            widget_factory=_make_factory(
                "plugins.image_converter.ImageConverterPlugin",
                "ImageConverterPlugin",
            ),
            tooltip="Converte imagens entre formatos (PNG, JPG, WEBP, ICO, etc.)",
            tool_type=ToolType.RASTER,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
        ToolKey.DOCLING.value: Tool(
            name=ToolKey.DOCLING.value,
            title="Docling",
            widget_factory=_make_factory(
                "plugins.docling.DoclingPlugin", "DoclingPlugin"
            ),
            tooltip="Converte documentos (PDF, imagens, Office) para Markdown via Docling",
            tool_type=ToolType.FOLDER,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
        ToolKey.MAP_VIEWER.value: Tool(
            name=ToolKey.MAP_VIEWER.value,
            title="Visualizador de Mapas",
            widget_factory=_make_factory(
                "plugins.map_viewer.MapViewerPlugin", "MapViewerPlugin"
            ),
            tooltip="Visualizador de mapas com basemap de satélite (arraste LAS, SHP, KML)",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.CENTRAL,
            show_in_toolbar=True,
        ),
    }

    def register_default_tools(self) -> None:
        """Registra todas as ferramentas definidas em _TOOLS."""
        for name, tool in self._TOOLS.items():
            if name not in self._tools:  # evita duplicatas
                self._tools[name] = tool
                self._order.append(name)

    # ==================================================================
    # Metodos de registro direto
    # ==================================================================

    def register(
        self,
        name: str,
        widget_factory: Callable[[], QWidget],
        *,
        title: str | None = None,
        tooltip: str = "",
        tool_type: ToolType = ToolType.SYSTEM,
        category: CategoryTool = CategoryTool.CENTRAL,
        icon: Optional[QIcon] = None,
        show_in_toolbar: bool = True,
        menu_category: Optional[MenuCategory] = None,
    ) -> int:
        """
        Registra uma ferramenta no sistema com lazy loading.

        Parametros:
            name           : Chave unica da ferramenta (ex: "Home", "Console")
            widget_factory : Callable sem argumentos que retorna um QWidget.
            title          : Nome exibido nas abas/titulos. Se None, usa name.
            tooltip        : Texto de dica (opcional).
            tool_type      : Categoria visual (ToolType.SYSTEM, RASTER, etc.)
            category       : Onde exibir (WORKSPACE ou SIDE).
            icon           : QIcon personalizado.
            show_in_toolbar: Se True (padrão), exibe na toolbar. Se False, oculta.
            menu_category  : Se definido, exibe no menu suspenso correspondente.

        Retorna:
            Indice da ferramenta na ordem de registro.
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' ja esta registrada.")
        tool = Tool(
            name=name,
            title=title or name,
            widget_factory=widget_factory,
            tooltip=tooltip,
            tool_type=tool_type,
            category=category,
            icon=icon,
            show_in_toolbar=show_in_toolbar,
            menu_category=menu_category,
        )
        self._tools[name] = tool
        self._order.append(name)
        return len(self._order) - 1

    def unregister(self, name: str) -> bool:
        """Remove uma ferramenta pelo nome. Retorna True se removeu."""
        tool = self._tools.pop(name, None)
        if tool is None:
            return False
        tool.unload()
        self._order.remove(name)
        return True

    # ==================================================================
    # Consulta
    # ==================================================================

    def get_all(self) -> List[Tool]:
        """Retorna lista de objetos Tool na ordem de registro."""
        return [self._tools[name] for name in self._order]

    def get(self, name: str) -> Optional[Tool]:
        """Retorna um objeto Tool pelo nome, ou None."""
        return self._tools.get(name)

    def count(self) -> int:
        """Quantidade de ferramentas registradas."""
        return len(self._tools)

    def names(self) -> List[str]:
        """Lista dos nomes de todas as ferramentas na ordem de registro."""
        return list(self._order)