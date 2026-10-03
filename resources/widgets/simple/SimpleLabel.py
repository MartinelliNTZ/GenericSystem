# -*- coding: utf-8 -*-
"""
SimpleLabel — Label padrão com estilo consistente.
===================================================
⚠️ NÃO INSTANCIÁVEL DIRETAMENTE — Use `GridLabel` de
`resources/widgets/grid/GridLabel.py` para exibir qualquer label.

    from resources.widgets.grid.GridLabel import GridLabel

    label = SimpleLabel("texto")   # ❌ criar diretamente
    grid = GridLabel({"key": {"label": "Texto", "value": "—"}})  # ✅ usar GridLabel

Uso interno:
    SimpleLabel só deve ser usado internamente por outros widgets.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel


class SimpleLabel(QLabel):
    """
    Label padrão com fonte monospace e cor clara.

    ⚠️ NÃO instanciar diretamente. Sempre usar via GridLabel.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: #A1A1AA; font-family: Consolas, monospace; font-size: 12px;")