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

O ATUALIZAR procura os shapes que já existem nas pastas (completão, arquivo da OS
na base e cópia no projeto), pergunta se devem ser substituídos e troca as feições
das OS/SubOS do vetor nesses arquivos — as demais OS/SubOS ficam intactas.

Preferências: carregadas ao INICIAR (modo, vetor e valores manuais — fazenda, OS,
SubOS, cliente, área e tolerância) e atualizadas a cada mudança. Ao TROCAR o
vetor, o auto-preenchimento da OS pelo caminho passa a mandar — só um valor
digitado pelo usuário no campo é preservado. O **mapeamento de campos NÃO vai
para as preferências** — é sempre recalculado a partir dos campos do vetor.
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
    LimitesExistingWorker,
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
from utils.Preferences import Preferences


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
        self._mode = MODE_LIMITES
        self._restoring = False
        self._running = False
        self._inspect_worker = None
        self._import_worker = None
        self._existing_worker = None
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
                "atualizar": {
                    "text": "ATUALIZAR",
                    "callback": self._on_atualizar,
                    "type": "danger",
                    "description": (
                        "Procura os shapes que já existem nas pastas e, com sua confirmação, "
                        "substitui as feições das OS/SubOS do vetor"
                    ),
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
        """Restaura modo, vetor e valores manuais (preferências são o estado inicial).

        O **mapeamento de campos NÃO é persistido** — ele é sempre recalculado a
        partir dos campos do vetor carregado.

        A OS restaurada vale como estado inicial: ao TROCAR o vetor, o
        auto-preenchimento do caminho passa a mandar (só um valor digitado pelo
        usuário no campo é preservado).
        """
        self.preferences.pop("field_map", None)
        Preferences.remove_tool_prefs(self.tool_key, ["field_map"])

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
        """Persiste modo, vetor e valores manuais (mapeamento de campos fica fora)."""
        self.preferences["mode"] = self._mode
        self.preferences["vector_path"] = self._selector[self._SELECTOR_KEY].path()
        self.preferences["manual"] = self._manual.values

    def _persist_prefs(self) -> None:
        """Atualiza o cache e grava as preferências no disco (escrita com debounce)."""
        self.save_prefs()
        self.force_save_prefs()

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
            "validacao": {"label": "Validação", "value": "—"},
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
        self._persist_prefs()

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
        """Reage à troca do vetor de entrada e persiste a escolha."""
        if self._restoring:
            return

        path = paths[0] if paths else ""
        if not path:
            self._reset_meta()
            self._persist_prefs()
            return

        self._autofill_os(path)
        self._start_inspect(path)
        self._persist_prefs()

    def _on_manual_changed(self, key: str, value: str) -> None:
        """Marca a OS digitada pelo usuário e mantém os valores manuais salvos."""
        if key == "os" and not self._setting_auto_os:
            self._os_locked = bool(value.strip())
        self.save_prefs()

    def _autofill_os(self, path: str) -> None:
        """Preenche a OS manual pelo padrão do caminho ao TROCAR o vetor.

        O auto-preenchimento manda sobre o valor que veio das preferências — apenas
        um valor DIGITADO pelo usuário no campo é preservado.
        """
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
        """Aplica campos, CRS e contagem lidos do vetor e sinaliza vetores fora do padrão."""
        if generation != self._generation:
            return

        self._meta = payload
        self._fields = payload.get("fields", [])
        self._apply_fields()
        self._update_summary()

        problems = payload.get("problems", []) or []
        if not problems:
            self.page.set_badge(self.page.PRONTA)
            return

        self.page.set_badge(self.page.ERROR)
        SignalManager.instance().console_message.emit(
            f"⚠ Vetor fora do padrão ({len(problems)} problema(s)): {problems[0]}"
        )
        self.logger.warning(
            "Vetor fora do padrão de importação",
            code="LIM_VECTOR_WARN",
            path=payload.get("path", ""),
            n_problems=len(problems),
        )

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
        """Repopula os combos (dos dois modos) e pré-seleciona os campos sugeridos.

        A sugestão é SEMPRE recalculada a partir do vetor atual — o mapeamento não
        vem das preferências.
        """
        choices = {"": "(não usar)"}
        choices.update({field: field for field in self._fields})

        for combos in self._combos.values():
            for key, combo in combos.items():
                combo.set_items(choices)
                combo.current_value = LimitesService.guess_field(self._fields, key)

    def _update_summary(self) -> None:
        """Atualiza o painel de resumo com os metadados do vetor."""
        self._resumo.set_values({
            "arquivo": os.path.basename(self._meta.get("path", "")) or "—",
            "feicoes": self._format_int(self._meta.get("count", 0)),
            "crs": self._meta.get("crs") or "—",
            "geometria": self._meta.get("geometry") or "—",
            "validacao": self._validation_summary(self._meta.get("problems", []) or []),
            "campos": self._fields_summary(self._meta.get("fields", [])),
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
            "validacao": "—",
            "campos": "—",
            "os_caminho": "—",
        })

    # ── Configuração da importação ──────────────────────────────────

    def _collect_config(self, update: bool = False) -> LimitesImportConfig:
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
            update=update,
        )

    # ── Execução ────────────────────────────────────────────────────

    def _on_validar(self) -> None:
        """Valida o vetor sem gravar nada."""
        self._start_import(dry_run=True)

    def _on_importar(self) -> None:
        """Valida, calcula a área e grava o resultado (base + projeto + banco)."""
        self._start_import(dry_run=False)

    def _on_atualizar(self) -> None:
        """Procura os shapes já existentes e pede confirmação antes de substituí-los."""
        if self._running:
            return

        try:
            config = self._collect_config(update=True)
        except ValueError as e:
            self._warn_config(e)
            return

        self._persist_prefs()
        mode_label = MODE_SETTINGS[self._mode]["label"]
        self._begin_execution(f"Verificando shapes existentes ({mode_label})...")
        SignalManager.instance().console_message.emit(
            f"Verificando shapes existentes ({mode_label.lower()}): "
            f"{os.path.basename(config.vector_path)}..."
        )

        self._generation += 1
        worker = LimitesExistingWorker(self._generation, config)
        worker.signals.finished.connect(self._on_check_done)
        worker.signals.invalid.connect(self._on_import_invalid)
        worker.signals.failed.connect(self._on_import_failed)
        self._existing_worker = worker
        self._pool.start(worker)

    def _on_check_done(self, generation: int, payload: dict) -> None:
        """Confirma a substituição dos shapes encontrados nas pastas."""
        if generation != self._generation:
            return

        self._finish_execution()
        targets = [str(path) for path in (payload.get("targets") or [])]

        if not targets:
            MessageBox.show_info(
                "Nenhum shape existente encontrado nas pastas.\n\n"
                "Use IMPORTAR para gravar a primeira versão.",
                title="Nada para atualizar",
                parent=self,
            )
            SignalManager.instance().console_message.emit(
                "Atualização: nenhum shape existente encontrado."
            )
            self.logger.info(
                "Atualização sem shapes existentes",
                code="LIM_UPDATE_EMPTY",
                mode=payload.get("mode", self._mode),
            )
            return

        if not self._confirm_update(targets, payload):
            SignalManager.instance().console_message.emit(
                "Atualização cancelada pelo usuário."
            )
            self.logger.info("Atualização cancelada", code="LIM_UPDATE_CANCEL")
            return

        self._start_import(dry_run=False, update=True)

    def _confirm_update(self, targets: list, payload: dict) -> bool:
        """Pergunta se os shapes encontrados devem ser substituídos pelo vetor atual."""
        answer = MessageBox.show_question(
            f"{len(targets)} shape(s) já existem nas pastas.\n\n"
            "Deseja substituir o conteúdo desses arquivos pelas feições do vetor atual?",
            title="Atualizar shapes existentes",
            detail=(
                f"{self._format_int(payload.get('n_features', 0))} feição(ões) do vetor "
                "substituem as feições das mesmas OS/SubOS nos arquivos abaixo "
                "(as demais OS/SubOS são preservadas):\n\n"
                + "\n".join(targets)
            ),
            parent=self,
        )
        return answer == MessageBox.YES

    def _warn_config(self, error: ValueError) -> None:
        """Informa configuração incompleta sem iniciar a execução."""
        self.logger.warning(
            "Configuração incompleta",
            code="LIM_CONFIG_INVALID",
            error=str(error),
        )
        MessageBox.show_warning(
            str(error),
            title="Configuração incompleta",
            parent=self,
        )

    def _begin_execution(self, message: str) -> None:
        """Bloqueia os botões, liga o HUD e sinaliza o início da execução."""
        self._running = True
        self.page.set_badge(self.page.RUNNING)
        for key in ("validar", "importar", "atualizar"):
            self.page.buttons.set_enabled(key, False)

        SignalManager.instance().hud_show.emit({"message": message})
        SignalManager.instance().execution_started.emit(self.tool_key)

    def _start_import(self, dry_run: bool, update: bool = False) -> None:
        """Dispara a validação/importação/atualização em background."""
        if self._running:
            return

        try:
            config = self._collect_config(update=update)
        except ValueError as e:
            self._warn_config(e)
            return

        self._persist_prefs()
        mode_label = MODE_SETTINGS[self._mode]["label"]
        source = os.path.basename(config.vector_path)
        if dry_run:
            message = f"Validando {mode_label}..."
            console = f"Validando {mode_label.lower()}..."
        elif update:
            message = f"Atualizando {mode_label}..."
            console = f"Atualizando {mode_label.lower()}: {source}..."
        else:
            message = f"Importando {mode_label}..."
            console = f"Importando {mode_label.lower()}: {source}..."

        self._begin_execution(message)
        SignalManager.instance().console_message.emit(console)

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

        if payload.get("update"):
            stats += (
                f"\nFeições substituídas: {self._format_int(payload.get('replaced', 0))}"
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
            operation = "Atualização" if payload.get("update") else "Importação"
            text = f"{operation} concluída.\n\n{stats}"
            if warnings:
                text += f"\n\n⚠ {len(warnings)} aviso(s) — veja os detalhes."
            MessageBox.show_info(
                text,
                title=f"{operation} concluída",
                detail=detail,
                parent=self,
            )
            self.output_message(BASE_ROOT, label="Base de Limites")
            console = f"{operation} concluída"

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
            update=bool(payload.get("update")),
            n_features=payload.get("n_features", 0),
            n_replaced=payload.get("replaced", 0),
            n_warnings=len(warnings),
        )

    def _on_import_invalid(self, generation: int, problems: list) -> None:
        """Bloqueia a operação e exibe os problemas encontrados."""
        if generation != self._generation:
            return

        self._finish_execution(info_only=True)
        MessageBox.show_warning(
            "Operação bloqueada — nada foi gravado.",
            title="Validação bloqueou a operação",
            detail="\n".join(problems),
            parent=self,
        )
        SignalManager.instance().console_message.emit(
            f"Operação bloqueada: {len(problems)} problema(s)."
        )
        self.logger.warning(
            "Operação bloqueada",
            code="LIM_BLOCKED",
            problems=len(problems),
        )

    def _on_import_failed(self, generation: int, message: str) -> None:
        """Reporta falha inesperada na operação."""
        if generation != self._generation:
            return

        self._finish_execution(error=True)
        MessageBox.show_error(
            "Falha ao processar o vetor.",
            title="Base de Limites",
            detail=message,
            parent=self,
        )
        SignalManager.instance().console_message.emit(f"ERRO: {message}")

    def _finish_execution(self, error: bool = False, info_only: bool = False) -> None:
        """Restaura botões/badge e encerra HUD e progresso."""
        self._running = False
        for key in ("validar", "importar", "atualizar"):
            self.page.buttons.set_enabled(key, True)

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
    def _validation_summary(problems: list) -> str:
        """Resumo da validação do vetor (EPSG, polígonos e geometrias)."""
        if not problems:
            return "OK (EPSG:4326, polígonos válidos)"
        return f"{len(problems)} problema(s) — clique em VALIDAR"

    @staticmethod
    def _fields_summary(fields: list) -> str:
        """Resumo curto dos campos do vetor (evita texto gigante no painel)."""
        if not fields:
            return "—"

        shown = ", ".join(str(field) for field in fields[:6])
        extra = len(fields) - 6
        if extra > 0:
            shown += f" (+{extra})"

        return shown if len(shown) <= 80 else f"{shown[:77]}…"

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
