# -*- coding: utf-8 -*-
"""
OsTrackerPlugin — Acompanhamento de OS
======================================
Ferramenta CENTRAL que lê o banco de dados (``.BancoDados``) e, para a OS
selecionada, exibe os dados gerais da OS e os cards de SubOS (cliente, nome
comercial e CNPJ).

- A pasta-mãe é a mesma do Gerenciador de Estrutura (somente leitura aqui).
- Abrir a ferramenta apenas LÊ o consolidado; nada é recalculado/gravado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from plugins.BasePlugin import BasePlugin
from plugins.os_tracker.OsTrackerService import OsTrackerService
from resources.widgets.grid.GridCardView import GridCardView
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from resources.widgets.simple.SimpleSelector import SimpleSelector
from utils.Preferences import Preferences


class OsTrackerPlugin(BasePlugin):
    """Ferramenta CENTRAL: escolhe uma OS e exibe seus dados."""

    def __init__(self, parent=None) -> None:
        self._mother_folder: Optional[Path] = None
        self._orders: List[Dict[str, Any]] = []
        super().__init__(
            tool_key=ToolKey.OS_TRACKER.value,
            parent=parent,
            title="Acompanhamento de OS",
        )
        QTimer.singleShot(0, self._load_from_disk)
        self.logger.info("Ferramenta inicializada", code="OST_READY")

    # ── Preferências ─────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Carrega a pasta-mãe (do ProjectStructure) e a última OS escolhida."""
        struct_prefs = Preferences.load_tool_prefs(
            ToolKey.PROJECT_STRUCTURE,
            caller_tool_key=ToolKey.OS_TRACKER.value,
        )
        saved_mother = struct_prefs.get("mother_folder", "") or ""
        self._mother_folder = Path(saved_mother) if saved_mother else None
        self._mother_selector.set_path(saved_mother)

    def save_prefs(self) -> None:
        """Persiste a última OS selecionada."""
        self.preferences["selected_os"] = self._os_combo.current_value or ""

    # ── UI ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        super()._build_ui()

        self._mother_selector = SimpleSelector(
            "Pasta-mãe:",
            placeholder="Definida no Gerenciador de Estrutura",
            browse_mode="directory",
            tooltip="Pasta-mãe dos projetos (somente leitura — vem do Gerenciador de Estrutura)",
        )
        self._mother_selector.edit.setReadOnly(True)
        self._mother_selector.btn.setVisible(False)
        grupo_origem = GroupPainel("Origem")
        grupo_origem.group_layout.addWidget(self._mother_selector)

        self._os_combo = SimpleComboBox(
            items={},
            on_item_changed=self._on_os_changed,
            label="OS:",
        )
        grupo_selecao = GroupPainel("Seleção")
        grupo_selecao.group_layout.addWidget(self._os_combo)

        self.main_layout.addWidget(GridGroupPainel(grupo_origem, grupo_selecao))
        self._build_cards()
        self._build_panels()
        self._build_legend()

    def _build_cards(self) -> None:
        """Cria os cards de resumo da OS selecionada."""
        def card(text: str) -> Dict[str, Any]:
            return {"labels": [
                {"type": "great_accent", "text": "—"},
                {"type": "simple", "text": text},
            ]}

        self._cards = GridCardView({
            "items_per_row": 4,
            "cards": [
                card("OS"),
                card("SubOS"),
                card("Pastas criadas"),
                card("Anos criados"),
            ],
        })
        self.main_layout.addWidget(self._cards)

    def _build_panels(self) -> None:
        """Cria os painéis de dados gerais e de SubOS."""
        grupo_geral = GroupPainel("Dados Gerais")
        self._general = GridLabel({
            "os": {"label": "OS", "value": "—"},
            "folders": {"label": "Pastas criadas", "value": "—"},
            "years": {"label": "Anos criados", "value": "—"},
            "path": {"label": "Caminho", "value": "—", "link": True},
        }, columns=2)
        grupo_geral.group_layout.addWidget(self._general)

        grupo_sub = GroupPainel("SubOS")
        self._sub_cards = GridCardView({"items_per_row": 2, "cards": []})
        grupo_sub.group_layout.addWidget(self._sub_cards)

        self.main_layout.addWidget(GridGroupPainel(grupo_geral, grupo_sub), 1)

    def _build_legend(self) -> None:
        """Cria a legenda/estado vazio abaixo dos painéis."""
        self._legend = GridLabel({"hint": {"label": "", "value": ""}}, columns=1)
        self._legend.widget("hint").setStyleSheet(
            "color: #A1A1AA; font-family: Consolas, monospace; font-size: 12px;"
        )
        self.main_layout.addWidget(self._legend)

    # ── Carga ────────────────────────────────────────────────────────

    def _load_from_disk(self) -> None:
        """Lê o consolidado existente (somente leitura) e popula a UI."""
        self._orders = []
        if self._mother_folder is not None and self._mother_folder.exists():
            self._orders = OsTrackerService.load_orders(
                self._mother_folder, tool_key=self.tool_key
            )
        self._populate_selector()
        self._render()
        self.page.set_badge(
            self.page.PRONTA if self._orders else self.page.INFO
        )

    def _populate_selector(self) -> None:
        """Preenche o combo de OS e restaura a última seleção."""
        items = {
            str(record.get("os", "")): OsTrackerService.order_label(record)
            for record in self._orders
        }
        self._os_combo.set_items(items)
        saved = self.preferences.get("selected_os", "") or ""
        if saved and saved in items:
            self._os_combo.current_value = saved
        elif items:
            self._os_combo.select_first()

    def _on_os_changed(self, os_key: str) -> None:
        """Reage à troca de OS no seletor."""
        self.preferences["selected_os"] = os_key or ""
        self._render()

    # ── Render ───────────────────────────────────────────────────────

    def _current_record(self) -> Optional[Dict[str, Any]]:
        """Retorna o registro da OS selecionada, ou None."""
        key = self._os_combo.current_value
        if not key:
            return None
        for record in self._orders:
            if str(record.get("os", "")) == key:
                return record
        return None

    def _render(self) -> None:
        """Atualiza cards, dados gerais e SubOS para a OS selecionada."""
        record = self._current_record()
        self._render_cards(record)
        self._render_general(record)
        self._render_sub_cards(record)
        self._render_legend(record)

    def _render_cards(self, record: Optional[Dict[str, Any]]) -> None:
        """Atualiza os cards de resumo."""
        sub_os = OsTrackerService.build_sub_os(record) if record else []
        summary = OsTrackerService.record_summary(record) if record else {}
        self._cards.set_card_value(0, 0, str(record.get("os", "")) if record else "—")
        self._cards.set_card_value(1, 0, str(len(sub_os)))
        self._cards.set_card_value(2, 0, str(len(summary.get("folders", []))))
        self._cards.set_card_value(3, 0, str(len(summary.get("years", []))))

    def _render_general(self, record: Optional[Dict[str, Any]]) -> None:
        """Atualiza os labels de dados gerais da OS."""
        os_number = str(record.get("os", "")) if record else "—"
        summary = OsTrackerService.record_summary(record) if record else {}
        folders = len(summary.get("folders", []))
        years = len(summary.get("years", []))
        path = str(summary.get("path", "") or "")
        self._general.set("os", os_number or "—")
        self._general.set("folders", str(folders))
        self._general.set("years", str(years))
        self._general.set("path", path or "—", url=path or None)

    def _render_sub_cards(self, record: Optional[Dict[str, Any]]) -> None:
        """Reconstrói os cards de SubOS da OS selecionada."""
        sub_os_list = OsTrackerService.build_sub_os(record) if record else []
        cards = [
            {"labels": [
                {"type": "great_accent", "text": f"SubOS {sub.code or '—'}"},
                {"type": "simple_accent", "text": sub.name or "—"},
                {"type": "simple", "text": sub.commercial_name or "—"},
                {"type": "simple", "text": sub.document or "—"},
            ]}
            for sub in sub_os_list
        ]
        self._sub_cards.build({"items_per_row": 2, "cards": cards})

    def _render_legend(self, record: Optional[Dict[str, Any]]) -> None:
        """Atualiza a legenda/estado vazio."""
        if record and record.get("sub_os"):
            text = "● SubOS da OS selecionada — cliente, nome comercial e CNPJ"
        elif record:
            text = "OS selecionada sem SubOS cadastradas no banco."
        elif self._mother_folder is None:
            text = (
                "Defina a pasta-mãe no Gerenciador de Estrutura e rode "
                "ATUALIZAR DADOS no Banco de Dados."
            )
        else:
            text = "Sem dados no banco. Rode ATUALIZAR DADOS no Banco de Dados."
        self._legend.widget("hint").setText(text)
