# -*- coding: utf-8 -*-
"""
CrsSelectorWidget — Widget de seleção de CRS/EPSG
===================================================
Widget composto contendo um SimpleComboBox com os EPSGs mais comuns
e um botão 🌎 que abre o CrsSearchDialog para busca completa.

O EPSG selecionado fica apenas em memória — NÃO persiste em disco.

Uso:
    from resources.widgets.crs.CrsSelectorWidget import CrsSelectorWidget

    selector = CrsSelectorWidget()
    selector.crs_changed.connect(self._on_crs_changed)
    selector.set_crs("EPSG:31983")
    current = selector.get_crs()      # "EPSG:31983"
    code = selector.crs_code          # 31983
    label = selector.crs_label        # "EPSG:31983 - SIRGAS 2000 / UTM zone 23S"
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from core.enum.CommonCrs import CommonCrs
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton

# ── Tenta importar pyproj (para validação opcional) ──
try:
    from pyproj import CRS as PyProjCRS
    _HAS_PYPROJ = True
except ImportError:
    _HAS_PYPROJ = False


class CrsSelectorWidget(QWidget):
    """
    Widget de seleção de CRS/EPSG com combo dos comuns + botão de busca.

    Sinais
    ------
    crs_changed(str) — emitido quando o CRS selecionado muda.
        O argumento é o código EPSG completo: "EPSG:4326".
    """

    crs_changed = Signal(str)

    def __init__(
        self,
        label: str | None = "CRS:",
        parent: QWidget | None = None,
        compact: bool = False,
    ):
        super().__init__(parent)
        self._extra_items: Dict[str, str] = {}  # EPSGs temporários (não do enum)
        self._label_text = label
        self._compact = compact

        self._build_ui()
        self._connect_signals()

    # ── Construção da UI ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Constrói o layout do widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Label opcional ──
        if self._label_text:
            lbl = QLabel(self._label_text)
            layout.addWidget(lbl)

        # ── ComboBox com itens do CommonCrs ──
        items = CommonCrs.to_simple_dict() if self._compact else CommonCrs.to_dict()
        self._combo = SimpleComboBox(
            items=items,
            on_item_changed=self._on_combo_changed,
        )
        min_width = 150 if self._compact else 320
        self._combo.setMinimumWidth(min_width)
        layout.addWidget(self._combo, 1)

        # ── Botão 🌎 para abrir busca avançada ──
        self._search_btn = SimpleSecondaryButton("🌎")
        self._search_btn.setFixedWidth(30)
        self._search_btn.setToolTip("Buscar CRS...")
        layout.addWidget(self._search_btn)

    def _connect_signals(self) -> None:
        """Conecta os sinais internos."""
        self._search_btn.clicked.connect(self._on_search_clicked)

    # ── API Pública ───────────────────────────────────────────────────────

    def set_crs(self, epsg_code: str) -> None:
        """
        Define o CRS selecionado programaticamente.

        Se o EPSG não estiver no CommonCrs enum, ele é adicionado
        como item temporário no combo.

        Args:
            epsg_code: Código EPSG completo (ex: "EPSG:31983").
        """
        if not epsg_code or ":" not in epsg_code:
            return

        # Verifica se já está no combo
        if epsg_code in self._combo._items:
            self._combo.current_value = epsg_code
            return

        # Tenta validar com pyproj
        if _HAS_PYPROJ:
            try:
                crs = PyProjCRS.from_epsg(epsg_code.split(":")[1])
                if crs is None:
                    return
                label = f"{epsg_code} - {crs.name}"
            except Exception:
                return
        else:
            label = epsg_code

        # Adiciona como item temporário
        self._extra_items[epsg_code] = label
        self._rebuild_combo()
        self._combo.current_value = epsg_code

    def get_crs(self) -> str:
        """Retorna o código EPSG completo selecionado (ex: 'EPSG:4326')."""
        value = self._combo.current_value
        return value or ""

    @property
    def crs_code(self) -> int:
        """Código numérico EPSG selecionado (ex: 4326)."""
        value = self.get_crs()
        if value and ":" in value:
            try:
                return int(value.split(":")[1])
            except ValueError:
                pass
        return 0

    @property
    def crs_label(self) -> str:
        """Texto completo exibido no combo (ex: 'EPSG:4326 - WGS 84')."""
        return self._combo.current_text

    # ── Métodos internos ──────────────────────────────────────────────────

    def _rebuild_combo(self) -> None:
        """Reconstrói o combo com itens do enum + extras temporários."""
        items = dict(CommonCrs.to_dict())
        items.update(self._extra_items)
        self._combo.set_items(items)

    def _on_combo_changed(self, value: str) -> None:
        """Dispara quando o usuário seleciona um item no combo."""
        self.crs_changed.emit(value)

    def _on_search_clicked(self) -> None:
        """Abre a dialog de busca de CRS."""
        # Import lazy para evitar circular imports
        from resources.widgets.crs.CrsSearchDialog import CrsSearchDialog

        dialog = CrsSearchDialog(parent=self.window() if self.window() else self)
        dialog.crs_selected.connect(self._on_dialog_selected)

        if dialog.exec():
            selected = dialog.selected_epsg
            if selected:
                self.set_crs(selected)

    def _on_dialog_selected(self, epsg_code: str) -> None:
        """
        Callback quando um CRS é selecionado na dialog.
        Aplica o EPSG selecionado no combo (apenas em memória).
        """
        self.set_crs(epsg_code)