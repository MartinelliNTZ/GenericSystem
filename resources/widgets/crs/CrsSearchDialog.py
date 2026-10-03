# -*- coding: utf-8 -*-
"""
CrsSearchDialog — Diálogo de busca e seleção de CRS/EPSG
===========================================================
Herda de BaseDialog e exibe uma lista agrupada de todos os CRS
disponíveis no banco de dados PROJ (via pyproj), com campo de
filtro em tempo real.

Uso:
    from resources.widgets.crs.CrsSearchDialog import CrsSearchDialog

    dialog = CrsSearchDialog(parent=self)
    dialog.crs_selected.connect(self._on_crs_selected)
    if dialog.exec():
        epsg = dialog.selected_epsg  # "EPSG:31983"
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from core.dialogs.BaseDialog import BaseDialog
from resources.styles.AppStyles import AppStyles

# ── Tenta importar pyproj (opcional — fallback se não estiver instalado) ──
try:
    from pyproj.database import query_crs_info, PJType
    from pyproj import CRS as PyProjCRS

    _HAS_PYPROJ = True
except ImportError:
    _HAS_PYPROJ = False


# ── Categorias de CRS (mesmo agrupamento do QGIS) ────────────────────────
# A primeira categoria "⭐ Mais Comuns" é populada manualmente com os itens
# do CommonCrs (WGS84, SIRGAS 2000 UTM). As demais vêm do pyproj.
_CRS_CATEGORIES: Dict[str, tuple] = {
    "⭐ Mais Comuns": None,  # manual — não usa pyproj query
    "🌍 Geográfico 2D": (PJType.GEOGRAPHIC_2D_CRS,),
    "🌐 Geográfico 3D": (PJType.GEOGRAPHIC_3D_CRS,),
    "📐 Projetado": (PJType.PROJECTED_CRS,),
    "🌌 Geocêntrico": (PJType.GEOCENTRIC_CRS,),
    "📏 Vertical": (PJType.VERTICAL_CRS,),
    "🧩 Composto": (PJType.COMPOUND_CRS,),
}

_CATEGORY_ORDER: list[str] = [
    "⭐ Mais Comuns",
    "📐 Projetado",
    "🌍 Geográfico 2D",
    "🌐 Geográfico 3D",
    "🌌 Geocêntrico",
    "📏 Vertical",
    "🧩 Composto",
]


class CrsSearchDialog(BaseDialog):
    """
    Diálogo de busca de CRS/EPSG com filtro e lista agrupada.

    Sinais
    ------
    crs_selected(str) — emitido quando um CRS é selecionado.
        O argumento é o código EPSG completo: "EPSG:31983".
    """

    crs_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        self._selected_epsg: str = ""
        self._all_crs: Optional[Dict[str, list]] = None  # cache lazy

        super().__init__(
            parent=parent,
            title="Selecionar Sistema de Referência de Coordenadas (CRS)",
            object_name="crs_search_dialog",
            fixed_size=(760, 560),
            modal=True,
            has_appbar=True,
        )

    # ── Propriedades ──────────────────────────────────────────────────────

    @property
    def selected_epsg(self) -> str:
        """Código EPSG selecionado (ex: 'EPSG:31983')."""
        return self._selected_epsg

    # ── Construção da UI ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Constrói a UI do diálogo."""
        self._add_title("Selecione o Sistema de Referência de Coordenadas")

        # ── Campo de filtro ──
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText(
            "Digite nome, código EPSG ou autoridade..."
        )
        self._filter_edit.textChanged.connect(self._on_filter_changed)
        self.main_layout.addWidget(self._filter_edit)

        # ── TreeWidget com colunas ──
        # Coluna "Código" maior (140px) para não precisar reajustar toda vez
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Código", "Nome", "Tipo"])
        self._tree.setColumnWidth(0, 140)
        self._tree.setColumnWidth(1, 360)
        self._tree.setColumnWidth(2, 120)
        self._tree.setAlternatingRowColors(False)
        self._tree.setRootIsDecorated(True)
        self._tree.setAnimated(True)
        self._tree.setSortingEnabled(False)
        self._tree.setStyleSheet(AppStyles.tree_style())
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.main_layout.addWidget(self._tree, 1)

        # ── Label de status ──
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self._status_label)

        # ── Botões ──
        self._add_button_bar(["cancel", "selecionar"])

        # ── Carrega dados (lazy) ──
        self._load_all_crs()

    # ── Carga de dados "⭐ Mais Comuns" ───────────────────────────────────

    def _get_common_crs_data(self) -> list:
        """Retorna lista de dicts com os CRS mais comuns do CommonCrs."""
        from core.enum.CommonCrs import CommonCrs

        _COMMON_TO_CATEGORY = {
            4326: "🌍 Geográfico 2D",
            31980: "📐 Projetado",
            31981: "📐 Projetado",
            31982: "📐 Projetado",
            31983: "📐 Projetado",
            31984: "📐 Projetado",
        }

        result = []
        for item in CommonCrs:
            if not item.value:
                continue
            cat = _COMMON_TO_CATEGORY.get(item.code, "Projetado")
            result.append({
                "code": item.code,
                "code_str": item.value,
                "name": item.name_clean,
                "type": cat.split(" ", 1)[1] if " " in cat else cat,
                "tooltip": item.label(),
            })
        return result

    # ── Carga de dados geral (lazy, uma única vez) ───────────────────────

    def _load_all_crs(self) -> None:
        """Carrega todos os CRS do banco PROJ em cache."""
        if not _HAS_PYPROJ:
            self._status_label.setText("⚠️ pyproj não instalado — modo limitado")
            self._populate_fallback()
            return

        if self._all_crs is not None:
            self._populate_tree(self._all_crs)
            return

        self._filter_edit.setPlaceholderText("Carregando CRS...")
        self._filter_edit.setEnabled(False)
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        try:
            self._all_crs: Dict[str, list] = {}

            # Primeiro: dados comuns (manuais)
            self._all_crs["⭐ Mais Comuns"] = self._get_common_crs_data()

            # Depois: consulta pyproj para cada categoria
            for category_name, pj_types in _CRS_CATEGORIES.items():
                if pj_types is None:
                    continue
                results = query_crs_info(
                    auth_name="EPSG", pj_types=list(pj_types)
                )
                self._all_crs[category_name] = list(results)

            self._populate_tree(self._all_crs)
            self._filter_edit.setPlaceholderText(
                "Digite nome, código EPSG ou autoridade..."
            )
        except Exception as e:
            self._status_label.setText(f"⚠️ Erro ao carregar CRS: {e}")
            self._populate_fallback()
        finally:
            self._filter_edit.setEnabled(True)

    def _populate_fallback(self) -> None:
        """Popula a lista com dados estáticos de fallback (sem pyproj)."""
        from core.enum.CommonCrs import CommonCrs

        _COMMON_TO_CATEGORY = {
            4326: "🌍 Geográfico 2D",
            31980: "📐 Projetado",
            31981: "📐 Projetado",
            31982: "📐 Projetado",
            31983: "📐 Projetado",
            31984: "📐 Projetado",
        }

        root = QTreeWidgetItem(self._tree, ["⭐ EPSG Comuns", "", ""])
        root.setFlags(root.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        for item in CommonCrs:
            if not item.value:
                continue
            child = QTreeWidgetItem(root)
            child.setText(0, item.value)
            child.setText(1, item.name_clean)
            cat = _COMMON_TO_CATEGORY.get(item.code, "Projetado")
            child.setText(2, cat.split(" ", 1)[1] if " " in cat else cat)
            child.setData(0, Qt.ItemDataRole.UserRole, str(item.code))
            child.setToolTip(0, item.label())
        root.setExpanded(True)
        self._status_label.setText(
            f"{CommonCrs.count()} CRS comuns (modo offline)"
        )

    # ── População da Tree ─────────────────────────────────────────────────

    def _populate_tree(self, data: Dict[str, list]) -> None:
        """Popula a QTreeWidget com os dados agrupados por categoria."""
        self._tree.clear()
        total = 0

        for category_name in _CATEGORY_ORDER:
            items = data.get(category_name, [])
            if not items:
                continue

            # Item pai (categoria) — não selecionável
            parent = QTreeWidgetItem(self._tree, [category_name, "", ""])
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            parent.setExpanded(True)

            for crs_info in items:
                child = QTreeWidgetItem(parent)
                # Suporta tanto objetos pyproj (categorias regulares)
                # quanto dicts (⭐ Mais Comuns)
                if isinstance(crs_info, dict):
                    code_str = crs_info["code_str"]
                    name = crs_info["name"]
                    type_name = crs_info["type"]
                    code_data = str(crs_info["code"])
                    tooltip = crs_info["tooltip"]
                else:
                    code_str = f"EPSG:{crs_info.code}"
                    name = crs_info.name
                    type_name = (
                        category_name.split(" ", 1)[1]
                        if " " in category_name
                        else category_name
                    )
                    code_data = crs_info.code
                    tooltip = f"{code_str} - {crs_info.name}"

                child.setText(0, code_str)
                child.setText(1, name)
                child.setText(2, type_name)
                child.setData(0, Qt.ItemDataRole.UserRole, code_data)
                child.setToolTip(0, tooltip)
                total += 1

        self._status_label.setText(f"{total} CRS encontrados")

    # ── Filtro em tempo real (em memória) ─────────────────────────────────

    def _on_filter_changed(self, text: str) -> None:
        """Filtra a lista em memória a cada tecla (NÃO reconsulta pyproj)."""
        if self._all_crs is None:
            return

        if not text.strip():
            self._populate_tree(self._all_crs)
            return

        text_lower = text.strip().lower()
        filtered: Dict[str, list] = {cat: [] for cat in _CATEGORY_ORDER}

        for category_name in _CATEGORY_ORDER:
            items = self._all_crs.get(category_name, [])
            for crs_info in items:
                if isinstance(crs_info, dict):
                    name = crs_info["name"].lower()
                    code = str(crs_info["code"])
                else:
                    name = crs_info.name.lower()
                    code = str(crs_info.code)

                if text_lower in name or text_lower in code:
                    filtered[category_name].append(crs_info)

        self._populate_tree(filtered)

    # ── Seleção ───────────────────────────────────────────────────────────

    def _on_item_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        """Seleciona o item ao dar duplo clique."""
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            self._select_item(item)

    def accept(self) -> None:
        """Coleta o EPSG selecionado antes de aceitar."""
        item = self._tree.currentItem()
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            self._select_item(item)

    def _select_item(self, item: QTreeWidgetItem) -> None:
        """Seleciona um item e fecha o diálogo."""
        code = item.data(0, Qt.ItemDataRole.UserRole)
        if code:
            self._selected_epsg = f"EPSG:{code}"
            self.crs_selected.emit(self._selected_epsg)
            super().accept()