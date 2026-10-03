# -*- coding: utf-8 -*-
"""
SimpleComboBox — QComboBox genérico com label opcional e auto-população
========================================================================
Widget composto que encapsula um QLabel + QComboBox + stretch,
com suporte a população por Dict ou List.

Responsabilidades:
- Receber dados via Dict (chave → valor exibido) ou List (strings)
- Popular o combo internamente
- Emitir callback quando o item muda
- Expor o item selecionado via propriedades

O plugin apenas fornece os dados e o callback, sem se preocupar
com a lógica interna do combo.

Uso com Dict (recomendado — mais semântico e manutenível):
    combo = SimpleComboBox(
        items={"console": "Console", "renamer": "Renomeador"},
        on_item_changed=self._on_item_changed,
        label="Ferramenta:",
    )
    combo.current_value  # "console"
    combo.current_text   # "Console"

Uso com List:
    combo = SimpleComboBox(
        items=["Opção A", "Opção B"],
        on_item_changed=self._on_item_changed,
    )
    combo.current_value  # "Opção A"
"""

from __future__ import annotations

from typing import Callable, Dict, List

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PySide6.QtCore import Signal


class SimpleComboBox(QWidget):
    """
    ComboBox genérico com label opcional.

    Sinais
    ------
    currentTextChanged(str) — encaminhado do QComboBox interno (compatibilidade)
    currentIndexChanged(int) — encaminhado do QComboBox interno

    Parameters
    ----------
    items : Dict[str, str] | List[str]
        Dict: {valor_interno: texto_exibido}
        List: ["texto1", "texto2"] (valor = texto)
    on_item_changed : Callable[[str], None] | None
        Callback chamado quando o item muda. Recebe o valor interno.
    label : str | None
        Texto do label à esquerda. None = sem label.
    parent : QWidget | None
    """

    def __init__(
        self,
        items: Dict[str, str] | List[str],
        on_item_changed: Callable[[str], None] | None = None,
        label: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._on_item_changed = on_item_changed
        self._items: Dict[str, str] = {}
        self._order: List[str] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        if label:
            lbl = QLabel(label)
            layout.addWidget(lbl)

        self._combo = QComboBox()
        self._combo.setMinimumWidth(200)

        # Encaminha sinais do combo interno para compatibilidade com controllers
        self._combo.currentIndexChanged.connect(self._on_index_changed)
        self._combo.currentTextChanged.connect(self._forward_current_text)
        self._combo.currentIndexChanged.connect(self._forward_index)

        layout.addWidget(self._combo, 1)

        layout.addStretch()

        self.set_items(items)

    def _populate(self) -> None:
        """Preenche o combo com os itens armazenados."""
        self._combo.blockSignals(True)
        self._combo.clear()
        for key in self._order:
            text = self._items[key]
            self._combo.addItem(text, key)
        self._combo.blockSignals(False)

    def _on_index_changed(self, idx: int) -> None:
        """Dispara callback quando o índice muda."""
        value = self._combo.itemData(idx)
        if value is not None and self._on_item_changed:
            self._on_item_changed(value)

    @property
    def current_value(self) -> str | None:
        """Valor interno atualmente selecionado."""
        idx = self._combo.currentIndex()
        if idx < 0:
            return None
        return self._combo.itemData(idx)

    @current_value.setter
    def current_value(self, value: str) -> None:
        """Define programaticamente pelo valor interno."""
        idx = self._combo.findData(value)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)

    @property
    def current_text(self) -> str:
        """Texto exibido atualmente no combo."""
        return self._combo.currentText()

    @property
    def count(self) -> int:
        """Número de itens no combo."""
        return self._combo.count()

    def set_items(self, items: Dict[str, str] | List[str]) -> None:
        """
        Substitui os itens e repopula o combo.

        Dict: {valor_interno: texto_exibido}
        List: ["a", "b"] vira {"a": "a", "b": "b"}
        """
        if isinstance(items, dict):
            self._items = dict(items)
        else:
            self._items = {item: item for item in items}

        self._order = list(self._items.keys())
        self._populate()

    # Sinais encaminhados para compatibilidade
    currentTextChanged = Signal(str)
    currentIndexChanged = Signal(int)

    def _forward_current_text(self, text: str):
        """Encaminha currentTextChanged do combo interno."""
        self.currentTextChanged.emit(text)

    def _forward_index(self, idx: int):
        """Encaminha currentIndexChanged do combo interno."""
        self.currentIndexChanged.emit(idx)

    def widget(self) -> QComboBox:
        """
        Retorna o QComboBox interno para binding de sinais (compatibilidade).

        Returns:
            QComboBox interno
        """
        return self._combo

    def select_first(self) -> None:
        """Seleciona o primeiro item se existir."""
        if self._combo.count() > 0:
            self._combo.setCurrentIndex(0)