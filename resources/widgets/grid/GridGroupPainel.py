# -*- coding: utf-8 -*-
"""
GridGroupPainel — Container que distribui GroupPainel em grade
====================================================================
Recebe N instâncias de GroupPainel e as organiza em colunas
com stretch=1 igual para todas.

Uso:
    from resources.widgets.GridGroupPainel import GridGroupPainel

    painel_a = GroupPainel("Pastas")
    painel_a.group_layout.addWidget(SimpleSelector(...))
    painel_a.group_layout.addWidget(GridCheckBox(...))

    painel_b = GroupPainel("Modo")
    painel_b.group_layout.addWidget(SimpleComboBox(...))

    grid = GridGroupPainel(painel_a, painel_b)
    main_layout.addWidget(grid)
"""

from __future__ import annotations

from typing import List

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout

from resources.widgets.GroupPainel import GroupPainel


class GridGroupPainel(QWidget):
    """
    Container que distribui GroupPainel em colunas com stretch=1.

    Parameters
    ----------
    *painels : GroupPainel
        Um GroupPainel para cada coluna do grid.
    """

    def __init__(self, *painels: GroupPainel, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(10)
        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 1)

        self._painels: List[GroupPainel] = list(painels)

        for col, painel in enumerate(self._painels):
            self._grid.addWidget(painel, 0, col)
            self._grid.setColumnStretch(col, 1)

    @property
    def painels(self) -> List[GroupPainel]:
        """Lista de GroupPainel, um por coluna."""
        return self._painels

    def painel(self, index: int) -> GroupPainel:
        """Retorna o GroupPainel do índice especificado."""
        return self._painels[index]