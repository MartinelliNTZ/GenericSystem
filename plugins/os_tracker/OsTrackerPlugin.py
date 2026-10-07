# -*- coding: utf-8 -*-
"""
OsTrackerPlugin — Acompanhamento de OS
======================================
Ferramenta CENTRAL de OS. Lê a FONTE OFICIAL (Firebase) e, para a OS/SubOS
selecionada, exibe os dados gerais e os cards de SubOS. Permite também:

- **CRIAR OS** — pede os dados básicos (só o NÚMERO é obrigatório) e cria a
  SubOS ``A`` automaticamente. A OS é lançada DIRETO no Firebase.
- **CRIAR SUBOS** — adiciona uma SubOS (letra) à OS selecionada.
- **ADICIONAR PASTA** — abre um checklist com as pastas da estrutura do projeto
  e cria as selecionadas (com as subpastas), EXCETO os anos do
  ``03_ENVIO_DE_DOCUMENTOS``, na pasta da SubOS selecionada.

A ferramenta tem ZERO contato com o JSON de dados — a persistência (Firebase +
backup JSON) é da classe ``CloudProjectDatabase`` (Contrato 28).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseWorker import FirebaseWorker
from core.firebase.CloudProjectDatabase import CloudProjectDatabase
from plugins.BasePlugin import BasePlugin
from plugins.os_tracker.OsTrackerService import OsTrackerService
from resources.widgets.dialogs.CheckBoxSelectDialog import CheckBoxSelectDialog
from resources.widgets.dialogs.FormLineEditDialog import FormLineEditDialog
from resources.widgets.grid.GridCardView import GridCardView
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from resources.widgets.simple.SimpleSelector import SimpleSelector
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProjectStructureUtil import (
    DEFAULT_PROJECT_FOLDERS,
    ProjectStructureUtil,
)


class OsTrackerPlugin(BasePlugin):
    """Ferramenta CENTRAL: escolhe OS/SubOS, cria OS/SubOS e adiciona pastas."""

    def __init__(self, parent=None) -> None:
        self._mother_folder: Optional[Path] = None
        self._orders: List[Dict[str, Any]] = []
        self._load_worker: Optional[FirebaseWorker] = None
        super().__init__(
            tool_key=ToolKey.OS_TRACKER.value,
            parent=parent,
            title="Acompanhamento de OS",
            buttons_config={
                "criar_os": {
                    "text": "CRIAR OS",
                    "callback": self._on_create_os,
                    "type": "secondary",
                    "description": "Cria uma OS (número obrigatório) com SubOS A",
                },
                "criar_subos": {
                    "text": "CRIAR SUBOS",
                    "callback": self._on_create_subos,
                    "type": "secondary",
                    "description": "Adiciona uma SubOS à OS selecionada",
                },
                "adicionar_pasta": {
                    "text": "ADICIONAR PASTA",
                    "callback": self._on_add_folder,
                    "type": "primary",
                    "description": "Cria pastas da estrutura do projeto na SubOS selecionada",
                },
            },
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
        """Persiste a última OS/SubOS selecionadas."""
        self.preferences["selected_os"] = self._os_combo.current_value or ""
        self.preferences["selected_subos"] = self._sub_combo.current_value or ""

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
        self._sub_combo = SimpleComboBox(
            items={},
            on_item_changed=self._on_sub_changed,
            label="SubOS:",
        )
        grupo_selecao = GroupPainel("Seleção")
        grupo_selecao.group_layout.addWidget(self._os_combo)
        grupo_selecao.group_layout.addWidget(self._sub_combo)

        self.main_layout.addWidget(GridGroupPainel(grupo_origem, grupo_selecao))
        self._build_cards()
        self._build_panels()
        self._build_legend()

    def _build_cards(self) -> None:
        """Cria os cards de resumo da OS/SubOS selecionada."""
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
            "subos": {"label": "SubOS", "value": "—"},
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
        """Lê a base da FONTE OFICIAL (Firebase) via classe de banco, em background."""
        self._orders = []
        self._load_worker = FirebaseWorker(
            CloudProjectDatabase.load_orders,
            tool_key=self.tool_key,
            parent=self,
        )
        self._load_worker.finished_with_result.connect(self._on_orders_loaded)
        self._load_worker.failed.connect(self._on_load_failed)
        self._load_worker.start()

    def _on_orders_loaded(self, result: Optional[list]) -> None:
        """Aplica a base lida na UI."""
        self._orders = list(result or [])
        self._populate_selector()
        self._render()
        self.page.set_badge(self.page.PRONTA if self._orders else self.page.INFO)

    def _on_load_failed(self, message: str) -> None:
        """Trata falha ao ler a base (mantém o estado atual)."""
        self.logger.warning(
            "Falha ao ler a base do Firebase", code="OST_LOAD_ERR", error=message
        )
        self._on_orders_loaded(list(self._orders))

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
        self._populate_sub_selector()

    def _populate_sub_selector(self) -> None:
        """Preenche o combo de SubOS da OS selecionada (default SubOS ``A``)."""
        record = self._current_record()
        codes = OsTrackerService.sub_os_codes(record) if record else []
        items = {code: self._sub_os_label(record, code) for code in codes}
        self._sub_combo.set_items(items)
        saved = self.preferences.get("selected_subos", "") or ""
        if "A" in items:
            self._sub_combo.current_value = "A"
        elif saved and saved in items:
            self._sub_combo.current_value = saved
        elif items:
            self._sub_combo.select_first()

    @staticmethod
    def _sub_os_label(record: Dict[str, Any], code: str) -> str:
        """Rótulo do seletor de SubOS (``SubOS <letra> — <cliente>``)."""
        entry = OsTrackerService.sub_os_entry(record, code) or {}
        client = str(entry.get("client", "")).strip()
        return f"SubOS {code} — {client}" if client else f"SubOS {code}"

    def _on_os_changed(self, os_key: str) -> None:
        """Reage à troca de OS: repopula as SubOS e re-renderiza."""
        self.preferences["selected_os"] = os_key or ""
        self._populate_sub_selector()
        self._render()

    def _on_sub_changed(self, sub_key: str) -> None:
        """Reage à troca de SubOS."""
        self.preferences["selected_subos"] = sub_key or ""
        self._render()

    def _current_record(self) -> Optional[Dict[str, Any]]:
        """Retorna o registro da OS selecionada, ou None."""
        key = self._os_combo.current_value
        if not key:
            return None
        for record in self._orders:
            if str(record.get("os", "")) == key:
                return record
        return None

    def _current_sub_entry(
        self, record: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Retorna a entrada da SubOS selecionada (ou None)."""
        if record is None:
            return None
        code = self._sub_combo.current_value
        if not code:
            return None
        return OsTrackerService.sub_os_entry(record, code)

    # ── Render ───────────────────────────────────────────────────────

    def _render(self) -> None:
        """Atualiza cards, dados gerais e SubOS para a OS/SubOS selecionadas."""
        record = self._current_record()
        entry = self._current_sub_entry(record)
        self._render_cards(record, entry)
        self._render_general(record, entry)
        self._render_sub_cards(record, entry)
        self._render_legend(record)

    def _render_cards(
        self,
        record: Optional[Dict[str, Any]],
        entry: Optional[Dict[str, Any]],
    ) -> None:
        """Atualiza os cards de resumo (OS, nº de SubOS, pastas e anos)."""
        codes = OsTrackerService.sub_os_codes(record) if record else []
        folders = list((entry or {}).get("folders", []) or [])
        years = list((entry or {}).get("years", []) or [])
        self._cards.set_card_value(0, 0, str(record.get("os", "")) if record else "—")
        self._cards.set_card_value(1, 0, str(len(codes)))
        self._cards.set_card_value(2, 0, str(len(folders)))
        self._cards.set_card_value(3, 0, str(len(years)))

    def _render_general(
        self,
        record: Optional[Dict[str, Any]],
        entry: Optional[Dict[str, Any]],
    ) -> None:
        """Atualiza os labels de dados gerais da SubOS selecionada."""
        os_number = str(record.get("os", "")) if record else "—"
        code = self._sub_combo.current_value or "—"
        folders = list((entry or {}).get("folders", []) or [])
        years = list((entry or {}).get("years", []) or [])
        resolved = self._resolve_path(str((entry or {}).get("path", "") or ""))
        self._general.set("os", os_number or "—")
        self._general.set("subos", code)
        self._general.set("folders", str(len(folders)))
        self._general.set("years", str(len(years)))
        self._general.set("path", resolved or "—", url=resolved or None)

    def _resolve_path(self, rel_path: str) -> str:
        """Resolve um caminho relativo para exibição (absoluto local)."""
        if not rel_path or self._mother_folder is None:
            return rel_path or ""
        return str(ProjectStructureUtil.resolve_path(self._mother_folder, rel_path))

    def _render_sub_cards(
        self,
        record: Optional[Dict[str, Any]],
        entry: Optional[Dict[str, Any]],
    ) -> None:
        """Reconstrói os cards de SubOS (destacando a selecionada)."""
        sub_os_list = OsTrackerService.build_sub_os(record) if record else []
        selected = self._sub_combo.current_value or ""
        cards = []
        for sub in sub_os_list:
            marker = "◀" if sub.code == selected else ""
            cards.append({"labels": [
                {"type": "great_accent", "text": f"SubOS {sub.code or '—'} {marker}".strip()},
                {"type": "simple_accent", "text": sub.name or "—"},
                {"type": "simple", "text": sub.commercial_name or "—"},
                {"type": "simple", "text": sub.document or "—"},
            ]})
        self._sub_cards.build({"items_per_row": 2, "cards": cards})

    def _render_legend(self, record: Optional[Dict[str, Any]]) -> None:
        """Atualiza a legenda/estado vazio."""
        if record and record.get("sub_os"):
            text = "● SubOS da OS selecionada — cliente, nome comercial e CNPJ"
        elif record:
            text = "OS selecionada sem SubOS cadastradas no banco."
        elif self._mother_folder is None:
            text = "Defina a pasta-mãe no Gerenciador de Estrutura."
        else:
            text = "Sem OS na base. Clique em CRIAR OS."
        self._legend.widget("hint").setText(text)

    # ── Ações ────────────────────────────────────────────────────────

    def _on_create_os(self) -> None:
        """Cria uma OS (número obrigatório) com SubOS A e lança no Firebase."""
        if self._mother_folder is None:
            MessageBox.show_warning(
                "Defina a pasta-mãe no Gerenciador de Estrutura.",
                title="Acompanhamento de OS", parent=self,
            )
            return
        dialog = FormLineEditDialog(
            config={
                "os": {"label": "Número da OS *", "placeholder": "ex.: 39"},
                "name": {"label": "Nome", "placeholder": "opcional"},
                "client": {"label": "Cliente", "placeholder": "opcional"},
                "commercial_name": {"label": "Nome comercial", "placeholder": "opcional"},
                "cnpj": {"label": "CNPJ", "placeholder": "opcional"},
            },
            title="Criar OS",
            required_keys=["os"],
            ok_text="Criar OS",
            min_size=(420, 360),
            parent=self,
        )
        if not dialog.exec():
            return
        values = dialog.values
        try:
            record = OsTrackerService.create_order(
                self._mother_folder,
                values.get("os", ""),
                name=values.get("name", ""),
                client=values.get("client", ""),
                commercial_name=values.get("commercial_name", ""),
                cnpj=values.get("cnpj", ""),
                tool_key=self.tool_key,
            )
        except Exception as e:
            self.logger.error("Falha ao criar OS", code="OST_CREATE_ERR", error=str(e))
            MessageBox.show_error(f"Falha ao criar OS: {e}", parent=self)
            return
        number = str(record.get("os", ""))
        self._reload(number, "A")
        MessageBox.show_toast(f"OS {number} criada (SubOS A).", parent=self)

    def _on_create_subos(self) -> None:
        """Adiciona uma SubOS à OS selecionada e grava no Firebase."""
        record = self._current_record()
        if record is None:
            MessageBox.show_warning(
                "Selecione uma OS primeiro.",
                title="Acompanhamento de OS", parent=self,
            )
            return
        suggested = OsTrackerService.next_sub_os_code(record)
        dialog = FormLineEditDialog(
            config={
                "sub_os": {
                    "label": "SubOS (letra)", "default": suggested,
                    "placeholder": "ex.: B",
                },
                "client": {"label": "Cliente", "placeholder": "opcional"},
                "commercial_name": {"label": "Nome comercial", "placeholder": "opcional"},
                "cnpj": {"label": "CNPJ", "placeholder": "opcional"},
            },
            title="Criar SubOS",
            required_keys=["sub_os"],
            ok_text="Criar SubOS",
            min_size=(420, 320),
            parent=self,
        )
        if not dialog.exec():
            return
        values = dialog.values
        try:
            OsTrackerService.add_sub_os(
                self._mother_folder,
                record,
                code=values.get("sub_os", ""),
                client=values.get("client", ""),
                commercial_name=values.get("commercial_name", ""),
                cnpj=values.get("cnpj", ""),
                tool_key=self.tool_key,
            )
        except Exception as e:
            self.logger.error("Falha ao criar SubOS", code="OST_SUBOS_ERR", error=str(e))
            MessageBox.show_error(f"Falha ao criar SubOS: {e}", parent=self)
            return
        code = values.get("sub_os", "").strip().upper()
        self._reload(str(record.get("os", "")), code)
        MessageBox.show_toast(f"SubOS {code} criada.", parent=self)

    def _on_add_folder(self) -> None:
        """Abre o checklist de pastas da estrutura e cria as selecionadas."""
        record = self._current_record()
        entry = self._current_sub_entry(record)
        if record is None or entry is None:
            MessageBox.show_warning(
                "Selecione uma OS e uma SubOS primeiro.",
                title="Acompanhamento de OS", parent=self,
            )
            return
        if self._mother_folder is None:
            MessageBox.show_warning(
                "Defina a pasta-mãe no Gerenciador de Estrutura.",
                title="Acompanhamento de OS", parent=self,
            )
            return
        config = {
            name: {"label": name, "default": False}
            for name in DEFAULT_PROJECT_FOLDERS
        }
        dialog = CheckBoxSelectDialog(
            config, title="Adicionar pastas ao projeto", num_columns=2, parent=self
        )
        if not dialog.exec():
            return
        selected = list(dialog.selected_keys)
        if not selected:
            return
        code = str(entry.get("sub_os", ""))
        try:
            result = OsTrackerService.add_folders(
                self._mother_folder, record, code, selected, tool_key=self.tool_key
            )
        except Exception as e:
            self.logger.error(
                "Falha ao adicionar pastas", code="OST_ADD_FOLDER_ERR", error=str(e)
            )
            MessageBox.show_error(f"Falha ao adicionar pastas: {e}", parent=self)
            return
        self._reload(str(record.get("os", "")), code)
        MessageBox.show_toast(
            f"{result.get('created', 0)} pasta(s) criada(s) na SubOS {code}.",
            parent=self,
        )

    def _reload(self, os_key: str, sub_key: str) -> None:
        """Recarrega a base do Firebase e restaura a seleção informada."""
        self.preferences["selected_os"] = os_key
        self.preferences["selected_subos"] = sub_key
        self._load_from_disk()
