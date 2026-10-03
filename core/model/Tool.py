# -*- coding: utf-8 -*-
"""
Tool — Modelo de ferramenta com lazy loading
==============================================
Cada ferramenta (tool) no Aetheris ToolBox é representada por uma
instância de Tool, que só instancia o widget QWidget sob demanda
(lazy loading) para evitar importações desnecessárias na inicialização.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from core.enum.CategoryTool import CategoryTool
from core.enum.MenuCategory import MenuCategory
from core.enum.ToolType import ToolType
from resources.IconManager import IconManager


class Tool:
    """
    Representa uma ferramenta registrada no sistema.

    O widget QWidget real **só é criado** quando a propriedade ``widget``
    é acessada pela primeira vez. Isso permite registrar dezenas de
    ferramentas sem impacto na memória/tempo de inicialização.

    Uso:
        tool = Tool(
            name="Console",
            widget_factory=lambda: ConsoleTool(),
            tooltip="Console de execução",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.WORKSPACE,
        )
        w = tool.widget  # ← cria o widget aqui, na primeira vez
    """

    def __init__(
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
    ) -> None:
        """
        Parâmetros:
            name             : Chave única da ferramenta (ex: "Console", "Home")
            widget_factory   : Callable sem argumentos que retorna um QWidget.
            title            : Nome exibido nas abas/títulos. Se None, usa name.
            tooltip          : Texto de dica ao passar o mouse (opcional).
            tool_type        : Categoria visual (ToolType.SYSTEM, RASTER, etc.)
            category         : Onde exibir (WORKSPACE ou SIDE).
            icon             : QIcon personalizado. Se None, usa IconManager.default_icon().
            show_in_toolbar  : Se True (padrão), exibe na toolbar. Se False, oculta.
            menu_category    : Se definido, exibe no menu suspenso correspondente.
                               Se None, não vai para o menu.
        """
        self._name = name
        self._title = title or name
        self._factory = widget_factory
        self._tooltip = tooltip
        self._tool_type = tool_type
        self._category = category
        self._icon = icon
        self._widget: Optional[QWidget] = None
        self._show_in_toolbar = show_in_toolbar
        self._menu_category = menu_category

    # ────────────────────────────────────────────────────────────────────────
    # Propriedades públicas
    # ────────────────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Chave única da ferramenta."""
        return self._name

    @property
    def title(self) -> str:
        """Nome exibido nas abas e títulos."""
        return self._title

    @property
    def widget(self) -> QWidget:
        """
        Retorna o widget da ferramenta, criando-o sob demanda (lazy).
        A factory é chamada apenas na primeira vez.

        Para ferramentas INSTANT (que se auto-destroem via deleteLater()),
        detecta se o objeto C++ foi deletado e recria o widget.
        """
        if self._widget is not None:
            try:
                # Verifica se o objeto C++ ainda existe
                self._widget.isWidgetType()
                return self._widget
            except RuntimeError:
                # Objeto C++ foi deletado (INSTANT tool se auto-destruiu)
                self._widget = None
        self._widget = self._factory()
        return self._widget

    @property
    def is_loaded(self) -> bool:
        """True se o widget já foi instanciado."""
        return self._widget is not None

    @property
    def tooltip(self) -> str:
        """Texto de dica da ferramenta."""
        return self._tooltip

    @property
    def tool_type(self) -> ToolType:
        """Categoria visual da ferramenta."""
        return self._tool_type

    @property
    def category(self) -> CategoryTool:
        """Onde a ferramenta deve ser exibida (WORKSPACE ou SIDE)."""
        return self._category

    @property
    def show_in_toolbar(self) -> bool:
        """Se True, exibe na toolbar. Se False, oculta."""
        return self._show_in_toolbar

    @property
    def menu_category(self) -> Optional[MenuCategory]:
        """Categoria de menu onde a ferramenta aparece. None = não vai para menu."""
        return self._menu_category

    @property
    def icon(self) -> QIcon:
        """Ícone da ferramenta. Carregado lazy se None."""
        if self._icon is None:
            # O nome do arquivo de ícone é o próprio nome da tool (ToolKey)
            # Ex: "LogViewer" → resources/icons/LogViewer.ico
            # Se não existir, usa o ícone default
            self._icon = IconManager.get_tool_icon(self._name)
        return self._icon

    # ────────────────────────────────────────────────────────────────────────
    # Métodos úteis
    # ────────────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Retorna representação serializável (útil para debug).
        """
        return {
            "name": self._name,
            "title": self._title,
            "tooltip": self._tooltip,
            "category": self._category.value,
            "loaded": self.is_loaded,
        }

    def unload(self) -> None:
        """
        Descarrega o widget, liberando memória.
        Útil para ferramentas que ficam ocultas por muito tempo.
        O widget será recriado na próxima vez que ``self.widget`` for acessado.
        """
        if self._widget is not None:
            self._widget.deleteLater()
            self._widget = None

    def __repr__(self) -> str:
        return (
            f"Tool(name={self._name!r}, title={self._title!r}, "
            f"category={self._category.value}, loaded={self.is_loaded})"
        )