# -*- coding: utf-8 -*-
"""
GroupPainel — Container com título dourado e fundo escuro.
==========================================================
Uso: agrupar widgets relacionados dentro de um card com título.
Suporta QVBoxLayout (padrão) e QGridLayout.

Uso:
    from resources.widgets.GroupPainel import GroupPainel

    grp = GroupPainel("Configurações")
    grp.add_widgets(QLabel("Linha 1"), QLineEdit())
    parent_layout.addWidget(grp)
"""

from __future__ import annotations

from typing import List, Type

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLayout
)


class GroupPainel(QWidget):
    """
    Container com título dourado estilo QGroupBox.

    ⚠️ NÃO instanciar diretamente. Sempre usar via GridGroupPainel.
    """

    def __init__(
        self,
        title: str = "",
        parent=None,
        layout_type: Type[QLayout] = QVBoxLayout,
    ):
        super().__init__(parent)

        self._group = QGroupBox(title)

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)
        self._outer_layout.addWidget(self._group)

        self.group_layout: QLayout = layout_type(self._group)

    def add_widgets(self, *widgets: QWidget, stretch: int = 0) -> None:
        """
        Adiciona múltiplos widgets ao group_layout de uma só vez.

        Args:
            *widgets: Widgets a serem adicionados (ordem sequencial)
            stretch: Fator de esticamento aplicado a todos (padrão 0)

        Exemplo:
            grp.add_widgets(QLabel("Nome:"), QLineEdit(), QSpinBox())
        """
        for widget in widgets:
            self.group_layout.addWidget(widget, stretch)