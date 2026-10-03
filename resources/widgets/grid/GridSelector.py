# -*- coding: utf-8 -*-
"""
SelectorGrid — Grade de SimpleSelectors configurados por dicionário.
Uso: criar múltiplos seletores de arquivo/pasta em lote com um único dict.
Suporta múltiplas colunas.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout
from resources.widgets.simple.SimpleSelector import SimpleSelector
from resources.widgets.GroupPainel import GroupPainel


class GridSelector(QWidget):
    """
    Grade de SimpleSelectors configurados por dicionário.

    Cada entrada do dict vira uma linha (ou coluna) na grade.

    Uso:
        grid = GridSelector({
            "Imagem Treino":   {"file_filter": "GeoTIFF (*.tif *.tiff)", "default_path": "dados/treino.tif"},
            "Imagem Classif.": {"file_filter": "GeoTIFF (*.tif *.tiff)", "default_path": "dados/classif.tif"},
            "Saída":           {"file_filter": "GeoTIFF (*.tif *.tiff)", "browse_mode": "save_file"},
        }, title="Imagens & Saída")
        parent_layout.addWidget(grid)

    Para acessar os valores:
        grid["Imagem Treino"].path()    # retorna caminho do seletor "Imagem Treino"
        grid.get("Imagem Treino").path()
    """

    def __init__(
        self,
        specs: dict[str, dict],
        title: Optional[str] = None,
        columns: int = 1,
        suggested_paths: Optional[dict[str, str]] = None,
        parent=None,
    ):
        super().__init__(parent)

        self._selectors: dict[str, SimpleSelector] = {}
        self._build(specs, title, columns)

    def _build(self, specs: dict[str, dict], title: Optional[str], columns: int):
        if title:
            container = GroupPainel(title)
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)
            outer.addWidget(container)
            inner = container.group_layout
        else:
            inner = QVBoxLayout(self)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(6)

        if columns <= 1:
            # Layout vertical simples
            inner.setSpacing(6)
            inner.setContentsMargins(6, 6, 6, 6)
            for label_text, kwargs in specs.items():
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("label_text", "parent")}
                sel = SimpleSelector(label_text=label_text, parent=self, **clean_kwargs)
                self._selectors[label_text] = sel
                inner.addWidget(sel)
        else:
            # Layout em grade com N colunas
            inner.setSpacing(6)
            inner.setContentsMargins(6, 6, 6, 6)
            grid = QGridLayout()
            grid.setSpacing(6)
            grid.setContentsMargins(6, 6, 6, 6)
            for i, (label_text, kwargs) in enumerate(specs.items()):
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("label_text", "parent")}
                sel = SimpleSelector(label_text=label_text, parent=self, **clean_kwargs)
                self._selectors[label_text] = sel
                row = i // columns
                col = i % columns
                grid.addWidget(sel, row, col)
            grid_wrapper = QWidget()
            grid_wrapper.setLayout(grid)
            inner.addWidget(grid_wrapper)

    # ── Acesso aos selectores ─────────────────────────────────────────

    def get(self, label: str) -> Optional[SimpleSelector]:
        """Retorna o SimpleSelector pelo texto do label."""
        return self._selectors.get(label)

    def __getitem__(self, label: str) -> SimpleSelector:
        """Acesso via colchetes: grid["Imagem Treino"]"""
        return self._selectors[label]

    def __contains__(self, label: str) -> bool:
        return label in self._selectors

    def items(self):
        """Itera sobre (label, SimpleSelector)."""
        return self._selectors.items()

    def selectors(self) -> dict[str, SimpleSelector]:
        """Retorna o dict interno de label → SimpleSelector."""
        return self._selectors.copy()

    def paths(self) -> dict[str, str]:
        """Retorna dict com label → caminho atual."""
        return {label: sel.path() for label, sel in self._selectors.items()}

    def all_paths(self) -> list[str]:
        """Retorna lista de todos os caminhos (sem labels)."""
        return [sel.path() for sel in self._selectors.values() if sel.path()]