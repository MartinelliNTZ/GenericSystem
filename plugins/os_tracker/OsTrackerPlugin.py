# -*- coding: utf-8 -*-
"""
OsTrackerPlugin — Acompanhamento de OS
======================================
Ferramenta CENTRAL de OS. Lê a FONTE OFICIAL (Firebase) e, para a OS selecionada,
exibe os dados gerais e as ÚLTIMAS ALTERAÇÕES DA OS (changelog da estrutura,
filtrado pela chave da OS). Permite também:

- **CRIAR OS** — pede os dados básicos (só a CHAVE é obrigatória) e lança a OS
  DIRETO no Firebase. A chave é TEXTO e pode conter LETRA (ex.: ``169A``), que é
  o que diferencia as OS de um mesmo projeto.
- **ADICIONAR PASTA** — abre um checklist com as pastas da estrutura do projeto
  e cria as selecionadas (com as subpastas), EXCETO os anos do
  ``03_ENVIO_DE_DOCUMENTOS``, na pasta da OS.

A ferramenta tem ZERO contato com o JSON de dados — a persistência (Firebase +
backup JSON) é da classe ``CloudProjectDatabase`` (Contrato 28).

O painel **Dados Gerais** reúne OS, cliente, pastas/anos criados e as infos de cada
base do banco (``limites`` e ``zonas_manejo``: feições e área em hectares).

O painel **Atalhos** abre, com um clique, a pasta da OS, a pasta do arquivo de
cada base obtida (``LIMITES`` e ``ZONAS DE MANEJO`` — um botão por link registrado
no banco, escondido quando a OS não tem o registro) e o changelog Word da OS
(``11_AGROROBOTICA/OS_<chave>_CHANGELOG.DOCX``).
"""

from __future__ import annotations

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
from utils.ProjectStructureUtil import DEFAULT_PROJECT_FOLDERS


class OsTrackerPlugin(BasePlugin):
    """Ferramenta CENTRAL: escolhe a OS, cria OS e adiciona pastas."""

    # Bases gravadas na OS pelo banco: (chave, label, prefixo das chaves do GridLabel)
    _ASSETS = (
        ("limites", "Limites", "lim"),
        ("zonas_manejo", "Zonas de manejo", "zon"),
    )

    # Atalhos do painel "Atalhos": (chave, texto, descrição)
    _SHORTCUTS = (
        ("path", "PASTA DA OS", "Abre a pasta da OS no Explorer"),
        ("limites", "LIMITES", "Abre a pasta do arquivo de limites da OS"),
        (
            "zonas_manejo",
            "ZONAS DE MANEJO",
            "Abre a pasta do arquivo de zonas de manejo da OS",
        ),
        ("changelog", "CHANGELOG (WORD)", "Abre o changelog Word da OS"),
    )

    def __init__(self, parent=None) -> None:
        self._mother_folder: Optional[Path] = None
        self._orders: List[Dict[str, Any]] = []
        self._changes: List[Dict[str, Any]] = []
        self._changes_generation = 0
        self._load_worker: Optional[FirebaseWorker] = None
        self._changes_worker: Optional[FirebaseWorker] = None
        self._shortcut_paths: Dict[str, str] = {}
        super().__init__(
            tool_key=ToolKey.OS_TRACKER.value,
            parent=parent,
            title="Acompanhamento de OS",
            buttons_config={
                "criar_os": {
                    "text": "CRIAR OS",
                    "callback": self._on_create_os,
                    "type": "secondary",
                    "description": "Cria uma OS (chave obrigatória — pode conter letra)",
                },
                "adicionar_pasta": {
                    "text": "ADICIONAR PASTA",
                    "callback": self._on_add_folder,
                    "type": "primary",
                    "description": "Cria pastas da estrutura do projeto na OS selecionada",
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
        self._build_panels()
        self._build_legend()

    def _build_panels(self) -> None:
        """Cria os painéis de dados gerais, atalhos e alterações."""
        grupo_geral = GroupPainel("Dados Gerais")
        self._general = GridLabel(self._general_config(), columns=2)
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

        grupo_alteracoes = GroupPainel("Últimas alterações da OS")
        self._change_cards = GridCardView({"items_per_row": 1, "cards": []})
        grupo_alteracoes.group_layout.addWidget(self._change_cards)

        self.main_layout.addWidget(GridGroupPainel(grupo_geral, grupo_atalhos))
        self.main_layout.addWidget(GridGroupPainel(grupo_alteracoes), 1)

    @classmethod
    def _general_config(cls) -> Dict[str, Dict[str, Any]]:
        """Config do GridLabel de Dados Gerais (OS + cliente + bases de limites/zonas)."""
        config: Dict[str, Dict[str, Any]] = {
            "os": {"label": "OS", "value": "—"},
            "client": {"label": "Cliente", "value": "—"},
            "folders": {"label": "Pastas criadas", "value": "—"},
            "years": {"label": "Anos criados", "value": "—"},
        }
        for key, label, prefix in cls._ASSETS:
            config[f"{prefix}_features"] = {
                "label": f"Feições — {label}",
                "value": "—",
                "description": f"Feições da base '{key}' registrada na OS",
            }
            config[f"{prefix}_area"] = {
                "label": f"Área — {label} (ha)",
                "value": "—",
                "description": f"Área (hectares) da base '{key}' registrada na OS",
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

    def _on_os_changed(self, os_key: str) -> None:
        """Reage à troca de OS: re-renderiza os painéis e busca as alterações."""
        self.preferences["selected_os"] = os_key or ""
        self._changes = []
        self._render()
        self._load_changes()

    def _current_record(self) -> Optional[Dict[str, Any]]:
        """Retorna o registro da OS selecionada, ou None."""
        key = self._os_combo.current_value
        if not key:
            return None
        for record in self._orders:
            if str(record.get("os", "")) == key:
                return record
        return None

    # ── Render ───────────────────────────────────────────────────────

    def _render(self) -> None:
        """Atualiza dados gerais, atalhos e alterações."""
        record = self._current_record()
        self._render_general(record)
        self._render_shortcuts(record)
        self._render_changes()
        self._render_legend(record)

    def _render_general(self, record: Optional[Dict[str, Any]]) -> None:
        """Atualiza os labels de dados gerais (OS + cliente + bases de limites/zonas)."""
        os_key = str(record.get("os", "")) if record else ""
        client = str((record or {}).get("client", "") or "")
        folders = list((record or {}).get("folders") or [])
        years = list((record or {}).get("years") or [])
        self._general.set("os", os_key or "—")
        self._general.set("client", client or "—")
        self._general.set("folders", str(len(folders)))
        self._general.set("years", str(len(years)))
        for key, _label, prefix in self._ASSETS:
            self._render_asset(record, key, prefix)

    def _render_asset(
        self,
        record: Optional[Dict[str, Any]],
        key: str,
        prefix: str,
    ) -> None:
        """Escreve as infos (feições e área) de uma base nos labels de Dados Gerais."""
        info = OsTrackerService.asset_info(record, key)
        tooltip = self._asset_tooltip(info)
        values = {
            f"{prefix}_features": self._format_int(info.get("features", 0)),
            f"{prefix}_area": self._format_number(info.get("area_ha", 0.0)),
        }
        for field, value in values.items():
            self._general.set(field, value)
            self._general.widget(field).setToolTip(tooltip)

    def _render_shortcuts(self, record: Optional[Dict[str, Any]]) -> None:
        """Resolve os atalhos e exibe um botão por link (limites/zonas) obtido."""
        folder = OsTrackerService.project_folder(self._mother_folder, record)
        self._shortcut_paths = {
            "path": str(folder) if folder is not None else "",
            "changelog": OsTrackerService.changelog_path(self._mother_folder, record),
        }
        for key, _label, _prefix in self._ASSETS:
            path = OsTrackerService.asset_file_path(self._mother_folder, record, key)
            self._shortcut_paths[key] = path
            self._shortcuts.set_visible(key, bool(path))

    @staticmethod
    def _asset_tooltip(info: Dict[str, Any]) -> str:
        """Detalhes do registro do banco (arquivo de origem e data de registro)."""
        if not info.get("has"):
            return "Sem registro na OS."

        lines = []
        if info.get("source"):
            lines.append(f"Origem: {info['source']}")
        when = OsTrackerService.format_when(str(info.get("inserted_at", "")))
        if when:
            lines.append(f"Registrado em: {when}")
        return "\n".join(lines) or "Registro presente na OS."

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
        elif record:
            text = "Nenhuma alteração registrada para esta OS."
        elif self._mother_folder is None:
            text = "Defina a pasta-mãe no Gerenciador de Estrutura."
        else:
            text = "Sem OS na base. Clique em CRIAR OS."
        self._legend.widget("hint").setText(text)

    # ── Abrir caminhos ──────────────────────────────────────────────

    def _on_shortcut(self, key: str) -> None:
        """Abre o alvo do atalho clicado (pasta da OS, limites/zonas ou Word)."""
        path = self._shortcut_paths.get(key, "")
        if not path:
            MessageBox.show_warning(
                "Nada para abrir: selecione uma OS com pasta em disco.",
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
        """Cria uma OS (chave obrigatória — pode conter letra) e lança no Firebase."""
        if self._mother_folder is None:
            MessageBox.show_warning(
                "Defina a pasta-mãe no Gerenciador de Estrutura.",
                title="Acompanhamento de OS", parent=self,
            )
            return
        dialog = FormLineEditDialog(
            config={
                "os": {"label": "OS *", "placeholder": "ex.: 169A"},
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
        os_key = str(record.get("os", ""))
        self._reload(os_key)
        MessageBox.show_toast(f"OS {os_key} criada.", parent=self)

    def _on_add_folder(self) -> None:
        """Abre o checklist de pastas da estrutura e cria as selecionadas."""
        record = self._current_record()
        if record is None:
            MessageBox.show_warning(
                "Selecione uma OS primeiro.",
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
        os_key = str(record.get("os", ""))
        try:
            result = OsTrackerService.add_folders(
                self._mother_folder, record, selected, tool_key=self.tool_key
            )
        except Exception as e:
            self.logger.error(
                "Falha ao adicionar pastas", code="OST_ADD_FOLDER_ERR", error=str(e)
            )
            MessageBox.show_error(f"Falha ao adicionar pastas: {e}", parent=self)
            return
        self._reload(os_key)
        MessageBox.show_toast(
            f"{result.get('created', 0)} pasta(s) criada(s) na OS {os_key}.",
            parent=self,
        )

    def _reload(self, os_key: str) -> None:
        """Recarrega a base do Firebase e restaura a seleção informada."""
        self.preferences["selected_os"] = os_key
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
