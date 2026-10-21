# -*- coding: utf-8 -*-
"""
LimitesPlugin — Base de Limites e Zonas de Manejo
=================================================
Ferramenta CENTRAL com DOIS modos de importação:

- **Limites** (``08_LIMITES/TALHOES``): talhão obrigatório, duplicidade bloqueada;
- **Zonas de Manejo** (``13_ZONAS_DE_MANEJO``): zona obrigatória, talhão opcional
  e SEM regra de duplicidade.

Ambos gravam:

    <BASE_DADOS>/limites/limites.shp          → completão de limites
    <BASE_DADOS>/limites/<OS>/<OS>_limites.shp
    <BASE_DADOS>/limites/zonas_manejo.shp     → completão de zonas
    <BASE_DADOS>/limites/<OS>/<OS>_zonas_manejo.shp
    <projeto da SubOS>/08_LIMITES/TALHOES/<OS>_limites.shp
    <projeto da SubOS>/13_ZONAS_DE_MANEJO/<OS>_zonas_manejo.shp

Fluxo: escolhe o modo → seleciona o vetor → mapeia os campos → informa
manualmente o que não foi mapeado → VALIDAR (não grava) ou IMPORTAR (calcula a
área, grava na base, copia para o projeto e registra no banco).

A OS manual é preenchida automaticamente pelo padrão do caminho de origem
(`OS_<numero>` na pasta ou `P<numero>` no arquivo) quando identificado; um valor
digitado pelo usuário é preservado.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QThreadPool, QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from plugins.limites_db.LimitesService import (
    BASE_ROOT,
    DEFAULT_SUB_OS,
    DEFAULT_TOLERANCE_PCT,
    MODE_LIMITES,
    MODE_SETTINGS,
    MODE_ZONAS,
    LimitesImportConfig,
    LimitesImportWorker,
    LimitesInspectWorker,
    LimitesService,
)
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.grid.GridRadio import GridRadio
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SectionPanel import SectionPanel
from resources.widgets.SeparatorWidget import SeparatorWidget
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from utils.MessageBox import MessageBox


class LimitesPlugin(BasePlugin):
    """Ferramenta CENTRAL: importa vetores para a base de limites por OS."""

    _SELECTOR_KEY = "Vetor"
    _FILTER = "Vetores (*.shp *.gpkg *.kml *.kmz *.geojson *.json)"

    _COMBO_SPECS = {
        MODE_LIMITES: (
            ("talhao", "Talhão *", "Campo obrigatório: nome do talhão."),
            ("fazenda", "Fazenda", "Se não mapeado, informe a fazenda no valor manual."),
            ("os", "OS", "Se não mapeado, informe a OS no valor manual."),
            ("subos", "SubOS", "Campo da SubOS (letra única). Padrão: A."),
            ("cliente", "Cliente", "Campo do cliente (opcional)."),
            ("area", "Área informada", "Campo da área informada em hectares (opcional)."),
        ),
        MODE_ZONAS: (
            ("zona", "Zona *", "Campo obrigatório da zona de manejo (Zone/Zona)."),
            ("fazenda", "Fazenda", "Se não mapeado, informe a fazenda no valor manual."),
            ("os", "OS", "Se não mapeado, informe a OS no valor manual."),
            ("subos", "SubOS", "Campo da SubOS (letra única). Padrão: A."),
            ("talhao", "Talhão", "Opcional nas zonas de manejo."),
            ("cliente", "Cliente", "Campo do cliente (opcional)."),
            ("area", "Área informada", "Campo da área informada em hectares (opcional)."),
        ),
    }

    def __init__(self, parent=None) -> None:
        self._generation = 0
        self._fields: list = []
        self._meta: dict = {}
        self._pending_field_map: dict = {}
        self._mode = MODE_LIMITES
        self._restoring = False
        self._running = False
        self._inspect_worker = None
        self._import_worker = None
        self._auto_os = ""
        self._os_locked = False
        self._setting_auto_os = False

        super().__init__(
            tool_key=ToolKey.LIMITES_DB.value,
            parent=parent,
            title="Base de Limites",
            buttons_config={
                "validar": {
                    "text": "VALIDAR",
                    "callback": self._on_validar,
                    "type": "secondary",
                    "description": "Valida o vetor (campos, áreas, duplicidades) sem gravar nada",
                },
                "importar": {
                    "text": "IMPORTAR",
                    "callback": self._on_importar,
                    "type": "primary",
                    "description": "Valida, calcula a área e grava o resultado na base e no projeto",
                },
            },
        )

        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        QTimer.singleShot(0, self._inspect_saved_path)
        self.logger.info("Ferramenta inicializada", code="LIM_READY")

    # ── Ciclo de vida ───────────────────────────────────────────────

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Encerra os workers pendentes antes de fechar."""
        self._pool.clear()
        self._pool.waitForDone(2000)
        super().closeEvent(event)

    # ── Preferências ────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Restaura o modo, o vetor, o mapeamento de campos e os valores manuais."""
        saved_map = self.preferences.get("field_map", {}) or {}
        if saved_map and all(isinstance(value, str) for value in saved_map.values()):
            saved_map = {MODE_LIMITES: saved_map}
        self._pending_field_map = {
            mode: dict(values)
            for mode, values in saved_map.items()
            if isinstance(values, dict)
        }

        saved_mode = str(self.preferences.get("mode", MODE_LIMITES) or MODE_LIMITES)
        if saved_mode not in MODE_SETTINGS:
            saved_mode = MODE_LIMITES
        self._modo.set_selected(saved_mode)

        manual = self.preferences.get("manual", {}) or {}
        if manual:
            self._manual.set_values(
                {key: str(value) for key, value in manual.items()},
                block_signals=True,
            )

        self._os_locked = False

        path = self.preferences.get("vector_path", "") or ""
        if not path:
            return

        self._restoring = True
        try:
            self._selector[self._SELECTOR_KEY].set_path(path)
        finally:
            self._restoring = False

        guess = LimitesService.guess_os_from_path(path)
        if guess and self._manual.get("os").strip() == guess:
            self._auto_os = guess

    def save_prefs(self) -> None:
        """Persiste modo, vetor, mapeamento de campos e valores manuais."""
        self.preferences["mode"] = self._mode
        self.preferences["vector_path"] = self._selector[self._SELECTOR_KEY].path()
        self.preferences["field_map"] = {
            mode: {
                key: (combo.current_value or "")
                for key, combo in combos.items()
            }
            for mode, combos in self._combos.items()
        }
        self.preferences["manual"] = self._manual.values

    # ── UI ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        super()._build_ui()

        self._selector = GridComplexSelector({
            self._SELECTOR_KEY: {
                "label_text": "Arquivo vetorial:",
                "file_filter": self._FILTER,
                "allow_file": True,
                "allow_folder": False,
                "multiple": False,
                "selection_mode": "file",
                "show_project_button": True,
                "tooltip": "Vetor de origem (SHP, GPKG, KML, KMZ ou GeoJSON).",
            },
        }, title="Origem")
        self._selector.set_on_input_changed(self._on_input_changed)

        self._modo = GridRadio({
            MODE_LIMITES: {
                "label": "Limites",
                "description": "Importa os limites dos talhões (duplicidade bloqueada)",
                "default": True,
            },
            MODE_ZONAS: {
                "label": "Zonas de Manejo",
                "description": "Importa as zonas de manejo (sem regra de duplicidade)",
            },
        }, num_columns=2)
        self._modo.changed.connect(self._on_mode_changed)

        painel_mapa = GroupPainel("Mapeamento de Campos")
        painel_mapa.group_layout.addWidget(self._modo)
        painel_mapa.group_layout.addWidget(
            SeparatorWidget(orientation="horizontal")
        )
        self._combos: dict = {}
        self._sections: dict = {}
        for mode, specs in self._COMBO_SPECS.items():
            section = SectionPanel(object_name=f"map_{mode}", spacing=6)
            combos: dict = {}
            for key, label, tooltip in specs:
                combo = SimpleComboBox(items={"": "(não usar)"}, label=label)
                combo.setToolTip(tooltip)
                combos[key] = combo
                section.section_layout.addWidget(combo)
            painel_mapa.group_layout.addWidget(section)
            self._combos[mode] = combos
            self._sections[mode] = section

        painel_manual = GroupPainel("Valores Manuais")
        self._manual = GridLineEdit({
            "fazenda": {"label": "Fazenda", "placeholder": "Obrigatória se não mapeada"},
            "os": {"label": "OS", "placeholder": "Obrigatória se não mapeada"},
            "subos": {"label": "SubOS", "default": DEFAULT_SUB_OS, "placeholder": "A"},
            "cliente": {"label": "Cliente", "placeholder": "Opcional"},
            "area": {"label": "Área informada (ha)", "placeholder": "Opcional"},
            "tolerancia": {
                "label": "Tolerância área (%)",
                "default": f"{DEFAULT_TOLERANCE_PCT:g}",
                "placeholder": "1",
            },
        })
        painel_manual.group_layout.addWidget(self._manual)
        self._manual.changed.connect(self._on_manual_changed)

        self._resumo = GridLabel({
            "arquivo": {"label": "Arquivo", "value": "—"},
            "feicoes": {"label": "Feições", "value": "—"},
            "crs": {"label": "CRS", "value": "—"},
            "geometria": {"label": "Geometria", "value": "—"},
            "campos": {"label": "Campos", "value": "—"},
            "os_caminho": {"label": "OS no caminho", "value": "—"},
            "base": {"label": "Base", "value": BASE_ROOT},
        }, columns=2)
        painel_resumo = GroupPainel("Resumo da Origem")
        painel_resumo.group_layout.addWidget(self._resumo)

        self.main_layout.addWidget(self._selector)
        self.main_layout.addWidget(GridGroupPainel(painel_mapa, painel_manual))
        self.main_layout.addWidget(GridGroupPainel(painel_resumo))
        self.main_layout.addStretch(1)
        self.page.set_badge(self.page.PRONTA)
        self._apply_mode_visibility()

    # ── Modo (limites / zonas) ──────────────────────────────────────

    def _on_mode_changed(self, key: str) -> None:
        """Troca o modo de importação (limites ou zonas de manejo)."""
        if key not in MODE_SETTINGS:
            return

        self._mode = key
        self._apply_mode_visibility()
        self.logger.info(
            f"Modo de importação: {MODE_SETTINGS[key]['label']}",
            code="LIM_MODE",
            mode=key,
        )

    def _apply_mode_visibility(self) -> None:
        """Mostra apenas o mapeamento do modo ativo."""
        for mode, section in self._sections.items():
            section.setVisible(mode == self._mode)

    # ── Inspeção do vetor ───────────────────────────────────────────

    def _inspect_saved_path(self) -> None:
        """Inspeciona o vetor restaurado das preferências (sem sobrescrever a OS salva)."""
        path = self._selector[self._SELECTOR_KEY].path()
        if not (path and os.path.isfile(path)):
            return

        if not self._manual.get("os").strip():
            self._autofill_os(path)
        self._start_inspect(path)

    def _on_input_changed(self, label: str, paths: list) -> None:
        """Reage à troca do vetor de entrada."""
        if self._restoring:
            return

        path = paths[0] if paths else ""
        if not path:
            self._reset_meta()
            return

        self._autofill_os(path)
        self._start_inspect(path)

    def _on_manual_changed(self, key: str, value: str) -> None:
        """Marca a OS manual como digitada pelo usuário (impede o auto-preenchimento)."""
        if key == "os" and not self._setting_auto_os:
            self._os_locked = bool(value.strip())

    def _autofill_os(self, path: str) -> None:
        """Preenche a OS manual pelo padrão do caminho (apenas quando identificado)."""
        guess = LimitesService.guess_os_from_path(path)
        if not guess:
            return

        current = self._manual.get("os").strip()
        if self._os_locked and current and current != self._auto_os:
            self.logger.info(
                f"OS manual mantida ({current}) — o caminho sugere {guess}",
                code="LIM_OS_KEPT",
            )
            return

        self._setting_auto_os = True
        try:
            self._manual.set("os", guess)
        finally:
            self._setting_auto_os = False

        self._auto_os = guess
        self._os_locked = False

        self.logger.info(
            f"OS preenchida pelo caminho de origem: {guess}",
            code="LIM_OS_GUESS",
        )

    def _start_inspect(self, path: str) -> None:
        """Dispara a leitura do vetor em background."""
        self._generation += 1
        worker = LimitesInspectWorker(self._generation, path)
        worker.signals.finished.connect(self._on_inspect_done)
        worker.signals.failed.connect(self._on_inspect_failed)
        self._inspect_worker = worker
        self._pool.start(worker)

    def _on_inspect_done(self, generation: int, payload: dict) -> None:
        """Aplica campos, CRS e contagem lidos do vetor."""
        if generation != self._generation:
            return

        self._meta = payload
        self._fields = payload.get("fields", [])
        self._apply_fields()
        self._update_summary()
        self.page.set_badge(self.page.PRONTA)

    def _on_inspect_failed(self, generation: int, message: str) -> None:
        """Informa a falha de leitura do vetor."""
        if generation != self._generation:
            return

        self._reset_meta()
        self.page.set_badge(self.page.ERROR)
        SignalManager.instance().console_message.emit(f"ERRO ao ler vetor: {message}")
        MessageBox.show_error(
            "Não foi possível ler o vetor selecionado.",
            title="Leitura do vetor",
            detail=message,
            parent=self,
        )

    def _apply_fields(self) -> None:
        """Repopula os combos (dos dois modos) e pré-seleciona os campos sugeridos."""
        choices = {"": "(não usar)"}
        choices.update({field: field for field in self._fields})

        for mode, combos in self._combos.items():
            saved_map = self._pending_field_map.get(mode, {})
            for key, combo in combos.items():
                combo.set_items(choices)
                saved = saved_map.get(key, "")
                target = (
                    saved
                    if saved and saved in choices
                    else LimitesService.guess_field(self._fields, key)
                )
                combo.current_value = target

        self._pending_field_map = {}

    def _update_summary(self) -> None:
        """Atualiza o painel de resumo com os metadados do vetor."""
        self._resumo.set_values({
            "arquivo": os.path.basename(self._meta.get("path", "")) or "—",
            "feicoes": self._format_int(self._meta.get("count", 0)),
            "crs": self._meta.get("crs") or "—",
            "geometria": self._meta.get("geometry") or "—",
            "campos": ", ".join(self._meta.get("fields", [])[:8]) or "—",
            "os_caminho": (
                LimitesService.guess_os_from_path(self._meta.get("path", "")) or "—"
            ),
        })

    def _reset_meta(self) -> None:
        """Limpa metadados do vetor e os combos de mapeamento."""
        self._meta = {}
        self._fields = []

        empty = {"": "(não usar)"}
        for combos in self._combos.values():
            for combo in combos.values():
                combo.set_items(empty)

        self._resumo.set_values({
            "arquivo": "—",
            "feicoes": "—",
            "crs": "—",
            "geometria": "—",
            "campos": "—",
            "os_caminho": "—",
        })

    # ── Configuração da importação ──────────────────────────────────

    def _collect_config(self) -> LimitesImportConfig:
        """Monta e valida a configuração informada na UI."""
        path = self._selector[self._SELECTOR_KEY].path().strip()
        if not path:
            raise ValueError("Selecione o arquivo vetorial de origem.")
        if not os.path.isfile(path):
            raise ValueError(f"Arquivo não encontrado: {path}")

        field_map = {
            key: (combo.current_value or "")
            for key, combo in self._combos[self._mode].items()
        }
        manual = {key: value.strip() for key, value in self._manual.values.items()}

        if self._mode == MODE_LIMITES and not field_map.get("talhao"):
            raise ValueError(
                "O campo do TALHÃO é obrigatório. Selecione-o em 'Mapeamento de Campos'."
            )
        if self._mode == MODE_ZONAS and not field_map.get("zona"):
            raise ValueError(
                "O campo da ZONA é obrigatório. Selecione-o em 'Mapeamento de Campos'."
            )
        if not field_map.get("fazenda") and not manual.get("fazenda"):
            raise ValueError(
                "Informe a FAZENDA: mapeie o campo ou preencha o valor manual."
            )
        if not field_map.get("os") and not manual.get("os"):
            raise ValueError(
                "Informe a OS: mapeie o campo ou preencha o valor manual."
            )

        tolerance = LimitesService.parse_float(manual.get("tolerancia"))
        if tolerance is None or tolerance < 0:
            raise ValueError(
                "Tolerância de área inválida. Informe um número maior ou igual a 0 (ex.: 1)."
            )

        return LimitesImportConfig(
            vector_path=path,
            field_map=field_map,
            manual={
                key: manual.get(key, "")
                for key in ("fazenda", "os", "subos", "cliente", "area")
            },
            tolerance_pct=tolerance,
            mode=self._mode,
        )

    # ── Execução ────────────────────────────────────────────────────

    def _on_validar(self) -> None:
        """Valida o vetor sem gravar nada."""
        self._start_import(dry_run=True)

    def _on_importar(self) -> None:
        """Valida, calcula a área e grava o resultado (base + projeto + banco)."""
        self._start_import(dry_run=False)

    def _start_import(self, dry_run: bool) -> None:
        """Dispara a validação/importação em background."""
        if self._running:
            return

        try:
            config = self._collect_config()
        except ValueError as e:
            self.logger.warning(
                "Configuração incompleta",
                code="LIM_CONFIG_INVALID",
                error=str(e),
            )
            MessageBox.show_warning(
                str(e),
                title="Configuração incompleta",
                parent=self,
            )
            return

        self._running = True
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("validar", False)
        self.page.buttons.set_enabled("importar", False)

        mode_label = MODE_SETTINGS[self._mode]["label"]
        SignalManager.instance().hud_show.emit({
            "message": (
                f"Validando {mode_label}..." if dry_run
                else f"Importando {mode_label}..."
            )
        })
        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"Validando {mode_label.lower()}..." if dry_run
            else f"Importando {mode_label.lower()}: {os.path.basename(config.vector_path)}..."
        )

        self._generation += 1
        worker = LimitesImportWorker(self._generation, config, dry_run)
        worker.signals.progress.connect(self._on_import_progress)
        worker.signals.finished.connect(self._on_import_done)
        worker.signals.invalid.connect(self._on_import_invalid)
        worker.signals.failed.connect(self._on_import_failed)
        self._import_worker = worker
        self._pool.start(worker)

    def _on_import_progress(self, generation: int, pct: int, message: str) -> None:
        """Atualiza HUD e barra de progresso central."""
        if generation != self._generation:
            return

        SignalManager.instance().progress_update.emit(float(pct))
        SignalManager.instance().hud_update.emit({
            "message": message,
            "progress": float(pct),
        })

    def _on_import_done(self, generation: int, payload: dict) -> None:
        """Exibe o resumo da validação/importação."""
        if generation != self._generation:
            return

        self._finish_execution()

        warnings = payload.get("warnings", []) or []
        detail = "\n".join(warnings)
        os_numbers = payload.get("os_numbers", []) or []
        subs = payload.get("sub_os", {}) or {}
        mode_label = MODE_SETTINGS.get(
            payload.get("mode", MODE_LIMITES), MODE_SETTINGS[MODE_LIMITES]
        )["label"]

        stats = (
            f"Modo: {mode_label}\n"
            f"{self._format_int(payload.get('n_features', 0))} feição(ões)\n"
            f"OS: {', '.join(str(number) for number in os_numbers) or '—'}\n"
            f"SubOS: {self._format_sub_os(subs)}\n"
            f"Área calculada: {self._format_number(payload.get('total_ha', 0.0))} ha"
        )

        if not payload.get("dry_run"):
            stats += (
                f"\nCópias no projeto: {self._format_int(len(payload.get('copies', []) or []))}"
                f"\nRegistros no banco: {self._format_int(payload.get('db_updated', 0))}"
            )

        if payload.get("dry_run"):
            text = f"Validação concluída.\n\n{stats}\n\nNada foi gravado."
            if warnings:
                text += f"\n\n⚠ {len(warnings)} aviso(s) — veja os detalhes."
            MessageBox.show_info(
                text,
                title="Validação concluída",
                detail=detail,
                parent=self,
            )
            console = "Validação concluída"
        else:
            text = f"Importação concluída.\n\n{stats}"
            if warnings:
                text += f"\n\n⚠ {len(warnings)} aviso(s) — veja os detalhes."
            MessageBox.show_info(
                text,
                title="Importação concluída",
                detail=detail,
                parent=self,
            )
            self.output_message(BASE_ROOT, label="Base de Limites")
            console = "Importação concluída"

        if not payload.get("dry_run"):
            console += (
                f" | {len(payload.get('copies', []) or [])} cópia(s) no projeto"
                f" | {payload.get('db_updated', 0)} registro(s) no banco"
            )

        if warnings:
            console += f" | {len(warnings)} aviso(s)"

        SignalManager.instance().console_message.emit(console)
        self.logger.info(
            "Operação de limites finalizada",
            code="LIM_DONE",
            dry_run=bool(payload.get("dry_run")),
            n_features=payload.get("n_features", 0),
            n_warnings=len(warnings),
        )

    def _on_import_invalid(self, generation: int, problems: list) -> None:
        """Bloqueia a importação e exibe os problemas encontrados."""
        if generation != self._generation:
            return

        self._finish_execution(info_only=True)
        MessageBox.show_warning(
            "Importação bloqueada — nada foi gravado.",
            title="Validação bloqueou a importação",
            detail="\n".join(problems),
            parent=self,
        )
        SignalManager.instance().console_message.emit(
            f"Importação bloqueada: {len(problems)} problema(s)."
        )
        self.logger.warning(
            "Importação bloqueada",
            code="LIM_BLOCKED",
            problems=len(problems),
        )

    def _on_import_failed(self, generation: int, message: str) -> None:
        """Reporta falha inesperada na importação."""
        if generation != self._generation:
            return

        self._finish_execution(error=True)
        MessageBox.show_error(
            "Falha ao importar o vetor.",
            title="Importação",
            detail=message,
            parent=self,
        )
        SignalManager.instance().console_message.emit(f"ERRO: {message}")

    def _finish_execution(self, error: bool = False, info_only: bool = False) -> None:
        """Restaura botões/badge e encerra HUD e progresso."""
        self._running = False
        self.page.buttons.set_enabled("validar", True)
        self.page.buttons.set_enabled("importar", True)

        if error:
            self.page.set_badge(self.page.ERROR)
        elif info_only:
            self.page.set_badge(self.page.INFO)
        else:
            self.page.set_badge(self.page.PRONTA)

        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().progress_update.emit(0.0)

    # ── Formatação ──────────────────────────────────────────────────

    @staticmethod
    def _format_sub_os(sub_counts: dict) -> str:
        """Formata a contagem por SubOS."""
        if not sub_counts:
            return "—"
        return ", ".join(
            f"{key} ({value})" for key, value in sub_counts.items()
        )

    @staticmethod
    def _format_int(value) -> str:
        """Formata inteiro com separador de milhar brasileiro."""
        if not isinstance(value, (int, float)):
            return "0"
        return f"{int(value):,}".replace(",", ".")

    @staticmethod
    def _format_number(value, decimals: int = 2) -> str:
        """Formata número decimal no padrão brasileiro."""
        if not isinstance(value, (int, float)):
            value = 0.0
        text = f"{float(value):,.{decimals}f}"
        return text.replace(",", "X").replace(".", ",").replace("X", ".")
