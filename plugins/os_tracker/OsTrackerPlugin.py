# -*- coding: utf-8 -*-
"""
OsTrackerPlugin — Acompanhamento de OS
======================================
Ferramenta CENTRAL de OS. Lê a FONTE OFICIAL (Firebase) e, para a OS/SubOS
selecionada, exibe os dados gerais e as ÚLTIMAS ALTERAÇÕES DA OS (changelog da
estrutura, filtrado pelo número da OS). Permite também:

- **CRIAR OS** — pede os dados básicos (só o NÚMERO é obrigatório) e cria a
  SubOS ``A`` automaticamente. A OS é lançada DIRETO no Firebase.
- **CRIAR SUBOS** — adiciona uma SubOS (letra) à OS selecionada.
- **ADICIONAR PASTA** — abre um checklist com as pastas da estrutura do projeto
  e cria as selecionadas (com as subpastas), EXCETO os anos do
  ``03_ENVIO_DE_DOCUMENTOS``, na pasta da SubOS selecionada.

A ferramenta tem ZERO contato com o JSON de dados — a persistência (Firebase +
backup JSON) é da classe ``CloudProjectDatabase`` (Contrato 28).

O painel **Base de Limites e Zonas** exibe os dados que o banco guarda na SubOS
(``limites`` e ``zonas_manejo``: quantidade de feições, área em hectares, arquivo
de origem e data de registro) e o arquivo de cada um abre no Explorer com um
clique.

O painel **Atalhos** abre, com um clique, a pasta da SubOS, a pasta
``LIMITE ZM`` e o changelog Word da OS
(``11_AGROROBOTICA/OS_<numero>_CHANGELOG.DOCX``).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QDesktopServices

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseWorker import FirebaseWorker
from plugins.BasePlugin import BasePlugin
from plugins.os_tracker.OsTrackerService import OsTrackerService
from resources.widgets.dialogs.CheckBoxSelectDialog import CheckBoxSelectDialog
from resources.widgets.dialogs.FormLineEditDialog import FormLineEditDialog
from resources.widgets.grid.GridButtonPanel import GridButtonPanel
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

    # Assets gravados na SubOS pelo banco: (chave, label, label do arquivo)
    _ASSETS = (
        ("limites", "Limites", "Arquivo de limites"),
        ("zonas_manejo", "Zonas de manejo", "Arquivo de zonas"),
    )

    # Atalhos do painel "Atalhos": (chave, texto, descrição)
    _SHORTCUTS = (
        ("path", "CAMINHO DA PASTA", "Abre a pasta da SubOS no Explorer"),
        ("zm", "LIMITE ZM", "Abre a pasta LIMITE ZM da SubOS no Explorer"),
        ("changelog", "CHANGELOG (WORD)", "Abre o changelog Word da OS"),
    )

    def __init__(self, parent=None) -> None:
        self._mother_folder: Optional[Path] = None
        self._orders: List[Dict[str, Any]] = []
        self._changes: List[Dict[str, Any]] = []
        self._changes_generation = 0
        self._load_worker: Optional[FirebaseWorker] = None
        self._changes_worker: Optional[FirebaseWorker] = None
        self._asset_paths: Dict[str, str] = {}
        self._shortcut_paths: Dict[str, str] = {}
        self._sub_folder = ""
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
        self._build_panels()
        self._build_legend()

    def _build_panels(self) -> None:
        """Cria os painéis de dados gerais, atalhos, limites/zonas e alterações."""
        grupo_geral = GroupPainel("Dados Gerais")
        self._general = GridLabel({
            "os": {"label": "OS", "value": "—"},
            "subos": {"label": "SubOS", "value": "—"},
            "folders": {"label": "Pastas criadas", "value": "—"},
            "years": {"label": "Anos criados", "value": "—"},
            "features": {
                "label": "Feições",
                "value": "—",
                "description": "Soma das feições de limites e zonas de manejo da SubOS",
            },
            "area": {
                "label": "Área (ha)",
                "value": "—",
                "description": "Soma da área (hectares) de limites e zonas de manejo da SubOS",
            },
            "path": {
                "label": "Caminho",
                "value": "—",
                "link": True,
                "description": "Clique para abrir a pasta da SubOS",
            },
        }, columns=2)
        self._general.link_clicked.connect(self._on_general_link)
        grupo_geral.group_layout.addWidget(self._general)

        grupo_atalhos = GroupPainel("Atalhos")
        self._shortcuts = GridButtonPanel({
            "columns": 2,
            "buttons": [
                {
                    "key": key,
                    "text": text,
                    "description": description,
                    "type": "secondary",
                }
                for key, text, description in self._SHORTCUTS
            ],
        })
        self._shortcuts.clicked.connect(self._on_shortcut)
        grupo_atalhos.group_layout.addWidget(self._shortcuts)

        grupo_base = GroupPainel("Base de Limites e Zonas")
        self._assets = GridLabel(self._asset_config(), columns=2)
        self._assets.link_clicked.connect(self._on_asset_link)
        grupo_base.group_layout.addWidget(self._assets)

        grupo_alteracoes = GroupPainel("Últimas alterações da OS")
        self._change_cards = GridCardView({"items_per_row": 1, "cards": []})
        grupo_alteracoes.group_layout.addWidget(self._change_cards)

        self.main_layout.addWidget(GridGroupPainel(grupo_geral, grupo_atalhos))
        self.main_layout.addWidget(
            GridGroupPainel(grupo_base, grupo_alteracoes), 1
        )

    @classmethod
    def _asset_config(cls) -> Dict[str, Dict[str, Any]]:
        """Config do GridLabel dos assets do banco (limites e zonas de manejo)."""
        config: Dict[str, Dict[str, Any]] = {}
        for key, label, file_label in cls._ASSETS:
            config[key] = {
                "label": label,
                "value": "—",
                "description": f"Registro '{key}' da SubOS no banco",
            }
            config[f"{key}_file"] = {
                "label": file_label,
                "value": "—",
                "link": True,
                "description": "Clique para abrir a pasta do arquivo",
            }
        return config

    def _build_legend(self) -> None:
        """Cria a legenda/estado vazio abaixo dos painéis."""
        self._legend = GridLabel({"hint": {"label": "", "value": ""}}, columns=1)
        self._legend.widget("hint").setStyleSheet(
            "color: #A1A1AA; font-family: Consolas, monospace; font-size: 12px;"
        )
        self.main_layout.addWidget(self._legend)

    # ── Carga ────────────────────────────────────────────────────────

    def _load_from_disk(self) -> None:
        """Lê a base de OS do banco, em background."""
        self._orders = []
        self._changes = []
        self._load_worker = FirebaseWorker(
            OsTrackerService.load_orders,
            tool_key=self.tool_key,
            parent=self,
        )
        self._load_worker.finished_with_result.connect(self._on_data_loaded)
        self._load_worker.failed.connect(self._on_load_failed)
        self._load_worker.start()

    def _on_data_loaded(self, result: Optional[list]) -> None:
        """Aplica a base de OS e carrega as alterações da OS selecionada."""
        self._orders = list(result or [])
        self._changes = []
        self._populate_selector()
        self._render()
        self._load_changes()
        self.page.set_badge(self.page.PRONTA if self._orders else self.page.INFO)

    def _on_load_failed(self, message: str) -> None:
        """Trata falha ao ler o banco (mantém a base atual em tela)."""
        self.logger.warning(
            "Falha ao ler a base do Firebase", code="OST_LOAD_ERR", error=message
        )
        self._on_data_loaded(list(self._orders))

    def _load_changes(self) -> None:
        """Lê as alterações da OS selecionada (background, com geração)."""
        record = self._current_record()
        number = str(record.get("os", "")).strip() if record else ""
        self._changes = []
        self._changes_generation += 1
        generation = self._changes_generation
        if not number:
            self._render_changes()
            self._render_legend(record)
            return
        worker = FirebaseWorker(
            OsTrackerService.load_changes,
            number,
            tool_key=self.tool_key,
            parent=self,
        )
        worker.finished_with_result.connect(
            lambda result: self._on_changes_loaded(generation, result)
        )
        worker.failed.connect(
            lambda message: self._on_changes_failed(generation, message)
        )
        self._changes_worker = worker
        worker.start()

    def _on_changes_loaded(self, generation: int, result: Optional[list]) -> None:
        """Aplica as alterações da OS (ignora respostas de seleções antigas)."""
        if generation != self._changes_generation:
            return
        self._changes = list(result or [])
        self._render_changes()
        self._render_legend(self._current_record())

    def _on_changes_failed(self, generation: int, message: str) -> None:
        """Trata falha ao ler as alterações da OS selecionada."""
        if generation != self._changes_generation:
            return
        self.logger.warning(
            "Falha ao ler as alterações da OS", code="OST_CHANGES_ERR", error=message
        )
        self._changes = []
        self._render_changes()
        self._render_legend(self._current_record())

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
        """Reage à troca de OS: repopula as SubOS, re-renderiza e busca alterações."""
        self.preferences["selected_os"] = os_key or ""
        self._populate_sub_selector()
        self._changes = []
        self._render()
        self._load_changes()

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
        """Atualiza dados gerais, atalhos, limites/zonas e alterações."""
        record = self._current_record()
        entry = self._current_sub_entry(record)
        self._render_general(record, entry)
        self._render_assets(entry)
        self._render_shortcuts(entry)
        self._render_changes()
        self._render_legend(record)

    @classmethod
    def _asset_totals(cls, entry: Optional[Dict[str, Any]]) -> tuple:
        """Soma feições e hectares dos assets (limites + zonas) da SubOS."""
        features = 0
        area_ha = 0.0
        for key, _label, _file_label in cls._ASSETS:
            info = OsTrackerService.asset_info(entry, key)
            features += int(info.get("features", 0) or 0)
            area_ha += float(info.get("area_ha", 0.0) or 0.0)
        return features, area_ha

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
        features, area_ha = self._asset_totals(entry)
        resolved = self._resolve_path(str((entry or {}).get("path", "") or ""))
        self._sub_folder = resolved
        self._general.set("os", os_number or "—")
        self._general.set("subos", code)
        self._general.set("folders", str(len(folders)))
        self._general.set("years", str(len(years)))
        self._general.set("features", self._format_int(features))
        self._general.set("area", self._format_number(area_ha))
        self._general.set("path", resolved or "—", url=resolved or None)

    def _render_assets(self, entry: Optional[Dict[str, Any]]) -> None:
        """Exibe se a SubOS tem limites/zonas no banco e o arquivo de cada um."""
        for key, _label, _file_label in self._ASSETS:
            info = OsTrackerService.asset_info(entry, key)
            path = OsTrackerService.asset_file_path(self._mother_folder, entry, key)
            file_key = f"{key}_file"

            self._asset_paths[key] = path
            self._asset_paths[file_key] = path
            self._assets.set(key, self._asset_text(info), url=path or None)
            self._assets.set(file_key, self._asset_file_text(path), url=path or None)
            self._assets.widget(key).setToolTip(self._asset_tooltip(info))
            self._assets.widget(file_key).setToolTip(
                path or "Sem arquivo registrado para esta SubOS."
            )

    def _render_shortcuts(self, entry: Optional[Dict[str, Any]]) -> None:
        """Resolve os caminhos dos atalhos (pasta da SubOS, LIMITE ZM e Word)."""
        folder = OsTrackerService.sub_os_folder(self._mother_folder, entry)
        self._shortcut_paths = {
            "path": str(folder) if folder is not None else "",
            "zm": OsTrackerService.zm_folder(self._mother_folder, entry),
            "changelog": OsTrackerService.changelog_path(self._mother_folder, entry),
        }

    @classmethod
    def _asset_text(cls, info: Dict[str, Any]) -> str:
        """Status do asset no banco: ``Sim — 12 feições · 1.234,57 ha`` ou ``Não``."""
        if not info.get("has"):
            return "Não"

        parts = [f"{cls._format_int(info.get('features', 0))} feição(ões)"]
        if info.get("area_ha"):
            parts.append(f"{cls._format_number(info.get('area_ha', 0.0))} ha")
        return "Sim — " + " · ".join(parts)

    @staticmethod
    def _asset_file_text(path: str) -> str:
        """Nome do arquivo do asset (``—`` quando a SubOS não tem registro)."""
        if not path:
            return "—"
        return os.path.basename(path) or path

    @staticmethod
    def _asset_tooltip(info: Dict[str, Any]) -> str:
        """Detalhes do registro do banco (arquivo de origem e data de registro)."""
        if not info.get("has"):
            return "Sem registro na SubOS."

        lines = []
        if info.get("source"):
            lines.append(f"Origem: {info['source']}")
        when = OsTrackerService.format_when(str(info.get("inserted_at", "")))
        if when:
            lines.append(f"Registrado em: {when}")
        return "\n".join(lines) or "Registro presente na SubOS."

    def _resolve_path(self, rel_path: str) -> str:
        """Resolve um caminho relativo para exibição (absoluto local)."""
        if not rel_path or self._mother_folder is None:
            return rel_path or ""
        return str(ProjectStructureUtil.resolve_path(self._mother_folder, rel_path))

    def _render_changes(self) -> None:
        """Reconstrói os cards das últimas alterações registradas no banco."""
        cards = [self._change_card(change) for change in self._changes]
        self._change_cards.build({"items_per_row": 1, "cards": cards})

    @classmethod
    def _change_card(cls, change: Dict[str, Any]) -> Dict[str, Any]:
        """Monta o card de uma alteração (OS/data, resumo e operador)."""
        os_number = str(change.get("os", "") or "—")
        when = OsTrackerService.change_when(change)
        scope = str(change.get("scope", "") or "")
        email = str(change.get("detected_by_email", "") or "")
        return {"labels": [
            {
                "type": "great_accent",
                "text": f"OS {os_number} · {when}" if when else f"OS {os_number}",
                "tooltip": scope,
            },
            {
                "type": "simple_accent",
                "text": OsTrackerService.change_summary(change),
                "tooltip": scope,
            },
            {
                "type": "simple",
                "text": cls._change_author(change),
                "tooltip": email or scope,
            },
        ]}

    @staticmethod
    def _change_author(change: Dict[str, Any]) -> str:
        """Operador/máquina que executou a conferência registrada."""
        name = str(change.get("detected_by", "") or "").strip()
        email = str(change.get("detected_by_email", "") or "").strip()
        machine = str(change.get("machine", "") or "").strip()
        who = name or email or "operador não registrado"
        return f"por {who} · {machine}" if machine else f"por {who}"

    def _render_legend(self, record: Optional[Dict[str, Any]]) -> None:
        """Atualiza a legenda/estado vazio."""
        if self._changes:
            text = "● Últimas alterações desta OS — data, resumo e operador"
        elif record and record.get("sub_os"):
            text = "Nenhuma alteração registrada para esta OS."
        elif self._mother_folder is None:
            text = "Defina a pasta-mãe no Gerenciador de Estrutura."
        else:
            text = "Sem OS na base. Clique em CRIAR OS."
        self._legend.widget("hint").setText(text)

    # ── Abrir caminhos ──────────────────────────────────────────────

    def _on_asset_link(self, key: str, url: str) -> None:
        """Abre no Explorer a pasta do arquivo de limites/zonas clicado."""
        path = self._asset_paths.get(key, "")
        if not path:
            MessageBox.show_warning(
                "Sem arquivo registrado para esta SubOS.",
                title="Acompanhamento de OS",
                parent=self,
            )
            return
        self._open_path(path)

    def _on_general_link(self, key: str, url: str) -> None:
        """Abre no Explorer a pasta da SubOS exibida em Dados Gerais."""
        if key != "path" or not self._sub_folder:
            return
        self._open_path(self._sub_folder)

    def _on_shortcut(self, key: str) -> None:
        """Abre o alvo do atalho clicado (pasta da SubOS, LIMITE ZM ou Word)."""
        path = self._shortcut_paths.get(key, "")
        if not path:
            MessageBox.show_warning(
                "Nada para abrir: selecione uma OS/SubOS com pasta em disco.",
                title="Acompanhamento de OS",
                parent=self,
            )
            return
        if key == "changelog":
            self._open_file(path)
            return
        self._open_path(path)

    def _open_path(self, path: str) -> None:
        """Abre no gerenciador de arquivos a pasta de ``path`` (arquivo ou pasta)."""
        target = Path(path)
        folder = target if target.is_dir() else target.parent
        if not folder.exists():
            MessageBox.show_warning(
                f"Pasta não encontrada:\n{folder}",
                title="Acompanhamento de OS",
                parent=self,
            )
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
        self.logger.info(
            "Pasta aberta no gerenciador de arquivos",
            code="OST_OPEN_PATH",
            path=str(folder),
        )

    def _open_file(self, path: str) -> None:
        """Abre um arquivo no aplicativo padrão do sistema."""
        target = Path(path)
        if not target.exists():
            MessageBox.show_warning(
                f"Arquivo não encontrado:\n{target}",
                title="Acompanhamento de OS",
                parent=self,
            )
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
        self.logger.info("Arquivo aberto", code="OST_OPEN_FILE", path=str(target))

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

    # ── Formatação ──────────────────────────────────────────────────

    @staticmethod
    def _format_int(value: Any) -> str:
        """Formata inteiro com separador de milhar brasileiro."""
        if not isinstance(value, (int, float)):
            return "0"
        return f"{int(value):,}".replace(",", ".")

    @staticmethod
    def _format_number(value: Any, decimals: int = 2) -> str:
        """Formata número decimal no padrão brasileiro."""
        if not isinstance(value, (int, float)):
            value = 0.0
        text = f"{float(value):,.{decimals}f}"
        return text.replace(",", "X").replace(".", ",").replace("X", ".")
