# -*- coding: utf-8 -*-
"""
PointBoundaryPlugin — Geração de Limite de Pontos com validação iterativa
=============================================================================
Plugin que gera o limite (boundary) de nuvens de pontos a partir de múltiplas
fontes (LAS/LAZ, SHP, GPKG, KML, CSV, GeoJSON), com validação iterativa
via concave hull e detecção automática de "escada".

Fluxo:
  1. GridComplexSelector para entrada (LAS, vetor ou CSV) e saída (linked)
  2. GridDoubleSpinBox para parâmetros (ratio, step, limiar, suavização, amostras)
  3. CrsSelectorWidget para CRS de saída
  4. GridLabel com resultados
  5. ExecutionButtons: EXECUTAR + SALVAR JSON
  6. PipelineRunner + PointBoundaryStep em background
"""

from __future__ import annotations

import json
import os

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from plugins.BasePlugin import BasePlugin
from plugins.point_boundary.PointBoundaryStep import PointBoundaryStep
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from resources.widgets.simple.SimpleLabel import SimpleLabel
from resources.widgets.crs.CrsSelectorWidget import CrsSelectorWidget
from utils.ExplorerUtils import ExplorerUtils
from utils.las.LasLayerSource import LasLayerSource
from utils.MessageBox import MessageBox
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil
from utils.vector.VectorLayerSource import VectorLayerSource


# ── Extensões suportadas ─────────────────────────────────────────
SUPPORTED_EXTENSIONS = (
    "LAS/LAZ (*.las *.laz);;"
    "Shapefile (*.shp);;"
    "GeoPackage (*.gpkg);;"
    "KML (*.kml);;"
    "CSV (*.csv);;"
    "GeoJSON (*.geojson)"
)

# ── Extensões que requerem GridLineEdit extra ────────────────────
CSV_EXTENSIONS = frozenset({".csv"})


class PointBoundaryPlugin(BasePlugin):
    """
    Plugin para gerar limite (boundary) de nuvens de pontos.
    """

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._current_metadata: dict = {}
        self._hull_result: dict | None = None
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.POINT_BOUNDARY.value,
            parent=parent,
            title="Limite de Pontos",
        )
        self.logger.info("Ferramenta inicializada", code="PB_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Constrói a interface completa do plugin."""
        super()._build_ui()

        # ── ExecutionButtons ────────────────────────────────────────
        self._btns = ExecutionButtons(self, {
            "salvar_json": {
                "text": "SALVAR JSON",
                "callback": self._on_salvar_json,
                "type": "secondary",
                "description": "Salvar resultados em JSON",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Gerar limite de pontos",
            },
        })
        self._btns.set_enabled("executar", False)
        self._btns.set_enabled("salvar_json", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Arquivos" ──────────────────────────────────
        grupo_arquivos = GroupPainel("Arquivos")
        self.main_layout.addWidget(grupo_arquivos)

        self._selector_grid = GridComplexSelector(
            {
                "Arquivo de Pontos": {
                    "file_filter": SUPPORTED_EXTENSIONS,
                    "mode_type": "input",
                    "allow_file": True,
                    "allow_folder": False,
                    "multiple": False,
                    "show_project_button": True,
                },
                "Saída": {
                    "mode_type": "output",
                    "parent": "Arquivo de Pontos",
                    "dynamic_parent": True,
                    "allow_file": True,
                    "allow_folder": False,
                    "multiple": False,
                    "show_suggest_button": True,
                    "suffix": "_boundary",
                    "extension": "gpkg",
                    "fixed_name": "boundary.gpkg",
                    "subfolder": "boundary",
                },
            },
        )
        grupo_arquivos.group_layout.addWidget(self._selector_grid)

        # Conecta callback de mudança na entrada
        self._selector_grid.set_on_input_changed(self._on_input_changed)

        # Label de info da fonte (visível apenas quando arquivo carregado)
        self._info_label = SimpleLabel("")
        self._info_label.setVisible(False)
        grupo_arquivos.group_layout.addWidget(self._info_label)

        # ── GridLineEdit para CSV (invisível por padrão) ────────────
        self._csv_grid = GridLineEdit({
            "csv_x_field": {
                "label": "Coluna X (CSV)",
                "description": "Nome da coluna de coordenada X",
                "default": "x",
                "placeholder": "x",
            },
            "csv_y_field": {
                "label": "Coluna Y (CSV)",
                "description": "Nome da coluna de coordenada Y",
                "default": "y",
                "placeholder": "y",
            },
        })
        self._csv_grid.setVisible(False)
        grupo_arquivos.group_layout.addWidget(self._csv_grid)

        # ── GroupPainel "Parâmetros" ────────────────────────────────
        grupo_params = GroupPainel("Parâmetros")
        self.main_layout.addWidget(grupo_params)

        self._params_grid = GridDoubleSpinBox({
            "ratio_inicial": {
                "label": "Ratio Inicial",
                "description": "Ratio inicial do limite côncavo (0.01-0.50)",
                "decimal": 3,
                "default": 0.10,
                "min": 0.001,
                "max": 0.50,
                "step": 0.01,
            },
            "ratio_step": {
                "label": "Decremento",
                "description": "Decremento do ratio por iteração",
                "decimal": 3,
                "default": 0.01,
                "min": 0.001,
                "max": 0.10,
                "step": 0.001,
            },
            "limiar_escada": {
                "label": "Limiar Escada (%)",
                "description": "Queda de área que dispara detecção de escada",
                "decimal": 1,
                "default": 12.0,
                "min": 1.0,
                "max": 50.0,
                "step": 0.5,
                "suffix": "%",
            },
            "suavisacao": {
                "label": "Suavização (m)",
                "description": "Buffer de suavização pós-hull",
                "decimal": 1,
                "default": 20.0,
                "min": 0.0,
                "max": 200.0,
                "step": 1.0,
                "suffix": "m",
            },
            "n_amostras": {
                "label": "Nº Amostras",
                "description": "Pontos usados para o hull",
                "decimal": 0,
                "default": 100_000,
                "min": 1000,
                "max": 10_000_000,
                "step": 10000,
            },
        }, columns=2)
        self._params_grid.changed.connect(self._on_param_changed)
        grupo_params.group_layout.addWidget(self._params_grid)

        self._ckb_intermediarios = GridCheckBox(
            {
                "salvar_intermediarios": {
                    "label": "Salvar iterações intermediárias",
                    "description": "Salva GPKGs de cada iteração em subpasta intermediarios/",
                    "default": False,
                },
            },
            num_columns=1,
        )
        grupo_params.group_layout.addWidget(self._ckb_intermediarios)

        # CrsSelectorWidget para CRS de saída
        self._crs_selector = CrsSelectorWidget(label="CRS:")
        grupo_params.group_layout.addWidget(self._crs_selector)
        self._crs_selector.set_crs("EPSG:31982")

        # Conecta mudança de CRS para atualizar botão executar
        self._crs_selector.crs_changed.connect(self._on_crs_changed)

        # ── GroupPainel "Resultados" ────────────────────────────────
        grupo_result = GroupPainel("Resultados")
        self.main_layout.addWidget(grupo_result)

        self._result_label = GridLabel(
            {
                "fonte":         {"label": "Fonte", "value": "—"},
                "n_pontos":      {"label": "Total Pontos", "value": "—"},
                "n_amostrados":  {"label": "Amostrados", "value": "—"},
                "ratio_ideal":   {"label": "Ratio Ideal", "value": "—"},
                "area_hull":     {"label": "Área Hull", "value": "—"},
                "area_suav":     {"label": "Área Suavizada", "value": "—"},
                "escada":        {"label": "Escada", "value": "—"},
                "crs_utilizado": {"label": "CRS", "value": "—"},
                "status":        {"label": "Status", "value": "Aguardando..."},
            },
            columns=2,
        )
        grupo_result.group_layout.addWidget(self._result_label)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_crs_changed(self, value: str):
        """Disparado quando o CRS muda."""
        self._atualizar_botao_executar()

    def _on_input_changed(self, label: str, paths: list[str]):
        """Disparado quando o path do selector de entrada muda."""
        if label != "Arquivo de Pontos":
            return
        path = paths[0] if paths else ""
        if not path or not os.path.isfile(path):
            return
        if path == self._current_path:
            return

        ext = os.path.splitext(path)[1].lower()
        supported = {".las", ".laz", ".shp", ".gpkg", ".kml", ".csv", ".geojson"}
        if ext not in supported:
            return

        # Mostra/esconde campos CSV
        is_csv = ext in CSV_EXTENSIONS
        self._csv_grid.setVisible(is_csv)

        # Extrai metadados
        try:
            if ext in (".las", ".laz"):
                info = LasLayerSource.get_info(path, tool_key=self.tool_key)
                n_pontos = info.get("point_count", 0)
                has_rgb = info.get("has_rgb", False)
                fonte_nome = "LAS" if ext == ".las" else "LAZ"

                # ── Pergunta sobre projeção se LAS sem CRS ──────────
                self.las_projection(path)

            elif ext in (".shp", ".gpkg", ".kml", ".geojson", ".csv"):
                # Usa VectorLayerSource para metadados básicos
                _, _, metadata = VectorLayerSource.extract_point_coordinates(
                    path, tool_key=self.tool_key, sample=1,
                )
                n_pontos = metadata["n_total"]
                has_rgb = False
                fonte_nome = metadata.get("fonte", ext.lstrip(".")).upper()
            else:
                return

            self._current_path = path
            self._current_metadata = {
                "n_total": n_pontos,
                "fonte": fonte_nome,
            }

            self._info_label.setText(
                f"Fonte: {fonte_nome} | Pontos: {n_pontos:,} | RGB: {'sim' if has_rgb else 'nao'}"
            )
            self._info_label.setVisible(True)

            self._result_label.set("fonte", fonte_nome)
            self._result_label.set("n_pontos", f"{n_pontos:,}")
            self._btns.set_enabled("executar", True)
            self.page.set_badge(self.page.PRONTA)

            self.logger.info(
                "Arquivo carregado",
                code="PB_FILE_LOADED",
                path=path,
                n_pontos=n_pontos,
                fonte=fonte_nome,
            )

        except Exception as e:
            self.logger.error(
                "Erro ao carregar arquivo",
                code="PB_FILE_LOAD_ERR",
                path=path,
                error=str(e),
            )
            self._info_label.setText(f"Erro: {str(e)}")
            self._info_label.setVisible(True)

    def _atualizar_botao_executar(self):
        """Habilita/desabilita o botão executar conforme estado."""
        tem_path = bool(self._current_path)
        tem_crs = bool(self._crs_selector.get_crs())
        self._btns.set_enabled("executar", tem_path and tem_crs)

    def _on_param_changed(self, key: str, value: float):
        """Disparado quando qualquer parâmetro numérico muda."""
        self.logger.debug(
            "Parâmetro alterado",
            code="PB_PARAM_CHANGED",
            key=key,
            value=value,
        )

    def _on_executar(self):
        """Executa a geração do limite via PipelineRunner em background."""
        self.logger.info(
            "Botao EXECUTAR pressionado",
            code="PB_EXEC_BTN",
            path=self._current_path,
        )

        if self._runner is not None and self._runner.isRunning():
            self.logger.warning(
                "Tentativa de executar enquanto ja em execucao",
                code="PB_EXEC_ALREADY_RUNNING",
            )
            MessageBox.show_warning(
                "Ja existe uma geracao de limite em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            self.logger.warning(
                "Tentativa de executar sem arquivo carregado",
                code="PB_EXEC_NO_FILE",
            )
            MessageBox.show_warning(
                "Nenhum arquivo de entrada carregado.", title="Limite de Pontos",
            )
            return

        # Coleta parâmetros
        params = self._params_grid.values
        csv_values = self._csv_grid.values if self._csv_grid.isVisible() else {}
        crs = self._crs_selector.get_crs() or "EPSG:31982"

        # Prepara UI para execução
        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)
        self._hull_result = None

        self._result_label.set_values({
            "ratio_ideal": "—",
            "area_hull": "—",
            "area_suav": "—",
            "escada": "—",
            "crs_utilizado": "—",
            "status": "Processando...",
        })

        n_total = self._current_metadata.get("n_total", 0)

        # Statistics
        self.statistics.start(
            n=0,
            ntype=ProcessStatisticsUtil.POINTS,
            ntotal=n_total,
        )
        total_estimate = self.get_eta_seconds()

        self.logger.info(
            "Iniciando geracao de limite em background",
            code="PB_EXEC_START",
            path=self._current_path,
            params=params,
            crs=crs,
            total_estimate_s=round(total_estimate, 1),
        )

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({
            "message": "Validando limite de pontos...",
            "stages": [total_estimate, 3],
            "eta": total_estimate,
        })
        SignalManager.instance().console_message.emit(
            f"Iniciando geracao de limite: "
            f"{os.path.basename(self._current_path)}"
        )

        # Diretório de saída
        output_path = self._selector_grid["Saída"].path()
        output_dir = os.path.dirname(output_path) if output_path else os.path.dirname(self._current_path)

        # Cria step com parâmetros exclusivos no construtor (Contrato 28)
        step = PointBoundaryStep(
            input_path=self._current_path,
            tool_key=self.tool_key,
            output_path=output_path,
            output_dir=output_dir,
            ratio_inicial=params.get("ratio_inicial", 0.10),
            ratio_step=params.get("ratio_step", 0.01),
            limiar_escada=params.get("limiar_escada", 12.0),
            suavisacao=params.get("suavisacao", 20.0),
            n_amostras=int(params.get("n_amostras", 100_000)),
            crs=crs,
            salvar_intermediarios=self._ckb_intermediarios.checked.get("salvar_intermediarios", False),
            csv_x_field=csv_values.get("csv_x_field", "x"),
            csv_y_field=csv_values.get("csv_y_field", "y"),
        )
        runner = PipelineRunner(
            steps=[step],
            input_path=self._current_path,
            output_path=output_dir,
            tool_key=self.tool_key,
            parent=self,
        )
        runner.finished_ok.connect(self._on_done)
        runner.failed.connect(self._on_error)
        runner.finished.connect(self._on_runner_finished)
        self._runner = runner
        runner.start()

        self.logger.debug(
            "PipelineRunner iniciado em QThread",
            code="PB_RUNNER_STARTED",
            thread_id=id(runner),
        )

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        self.logger.info(
            "Pipeline finalizada com sucesso",
            code="PB_PIPELINE_DONE",
        )

        self.statistics.end()

        # Extrai resultados
        hull_result = context.get_result("hull_result", {})
        hull_summary = context.get_result("hull_summary", {})

        if hull_summary:
            self._hull_result = hull_result
            self._result_label.set_values(hull_summary)
            gpkg_final = self._hull_result.get("gpkg_final", "") if self._hull_result else ""
            self._btns.set_enabled("salvar_json", True)

            if gpkg_final:
                pasta = os.path.dirname(gpkg_final)
                self.output_message(
                    output_path=pasta,
                    label="Pasta de Saída",
                    message=f"Limite gerado: area={hull_summary.get('area_hull', '?')}, ratio={hull_summary.get('ratio_ideal', '?')} | ",
                )
            else:
                msg = (
                    f"Limite gerado: "
                    f"area={hull_summary.get('area_hull', '?')}, "
                    f"ratio={hull_summary.get('ratio_ideal', '?')}"
                )
                SignalManager.instance().console_message.emit(msg)

        SignalManager.instance().execution_finished.emit(self.tool_key)

        self.logger.info(
            "Limite gerado com sucesso",
            code="PB_EXEC_DONE",
            hull_summary=hull_summary,
        )

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        self.logger.critical(
            "Pipeline falhou com erro",
            code="PB_PIPELINE_FAILED",
            error=message,
            path=self._current_path,
        )
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"ERRO: {message}"
        )
        self.logger.error(
            "Erro na geracao de limite",
            code="PB_EXEC_ERR",
            error=message,
            path=self._current_path,
        )

        self._result_label.set("status", f"❌ Erro")
        MessageBox.show_error(
            f"Erro durante a geracao do limite:\n{message}",
            title="Limite de Pontos",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
        self.logger.info(
            "PipelineRunner finalizado",
            code="PB_RUNNER_FINISHED",
        )
        self._runner = None
        self._btns.set_all_enabled(True)
        self._btns.set_enabled("executar", bool(self._current_path))
        self._btns.set_enabled("salvar_json", self._hull_result is not None)
        self.page.set_badge(self.page.PRONTA if self._hull_result else self.page.ERROR)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Handlers de Ação
    # ══════════════════════════════════════════════════════════════════

    def _on_salvar_json(self):
        """Abre dialogo para salvar o JSON de resultados em disco."""
        self.logger.info(
            "Botao SALVAR JSON pressionado",
            code="PB_SAVE_JSON_BTN",
            path=self._current_path,
        )

        if self._hull_result is None:
            self.logger.warning(
                "Tentativa de salvar JSON sem dados disponiveis",
                code="PB_SAVE_JSON_NO_DATA",
            )
            MessageBox.show_warning(
                "Nao ha dados para salvar.\n"
                "Execute a geracao de limite primeiro.",
                title="Limite de Pontos",
            )
            return

        basename = os.path.splitext(os.path.basename(self._current_path))[0]
        default_name = f"{basename}_resultado_boundary.json"

        file_path = ExplorerUtils.save_file(
            "Salvar Resultados JSON",
            initial_dir=os.path.join(
                os.path.dirname(self._current_path), default_name
            ),
            file_filter="JSON (*.json)",
            parent=self,
        )

        if not file_path:
            self.logger.info(
                "Usuario cancelou o dialogo de salvamento",
                code="PB_SAVE_JSON_CANCELLED",
            )
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._hull_result, f, indent=2, ensure_ascii=False)

            self.logger.info(
                "JSON salvo com sucesso",
                code="PB_SAVE_JSON_OK",
                path=file_path,
                filesize=os.path.getsize(file_path),
            )

            SignalManager.instance().console_message.emit(
                f"JSON salvo: {file_path}"
            )
            MessageBox.show_info(
                f"Resultados salvos em:\n{file_path}",
                title="Limite de Pontos",
            )

        except OSError as e:
            self.logger.error(
                "Erro ao salvar JSON",
                code="PB_SAVE_JSON_ERR",
                path=file_path,
                error=str(e),
            )
            MessageBox.show_error(
                f"Erro ao salvar arquivo:\n{str(e)}",
                title="Limite de Pontos",
            )

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferencias", code="PB_PREFS_LOAD")
        last_path = self.preferences.get("last_path", "")
        last_output_gpkg = self.preferences.get("output_gpkg", "")
        params = self.preferences.get("params", {})
        crs = self.preferences.get("crs", "EPSG:31982")
        csv_fields = self.preferences.get("csv_fields", {})

        if last_path:
            self._selector_grid["Arquivo de Pontos"].set_path(last_path)

        if last_output_gpkg:
            self._selector_grid["Saída"].set_path(last_output_gpkg)

        if params:
            self._params_grid.set_values(params)

        salvar_inter = self.preferences.get("salvar_intermediarios", False)
        self._ckb_intermediarios.set_all({"salvar_intermediarios": salvar_inter})

        if crs:
            self._crs_selector.set_crs(crs)

        if csv_fields:
            self._csv_grid.set_values(csv_fields)

        self.logger.info("Preferencias carregadas", code="PB_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._selector_grid["Arquivo de Pontos"].path()
        self.preferences["output_gpkg"] = self._selector_grid["Saída"].path()
        self.preferences["params"] = self._params_grid.values
        self.preferences["salvar_intermediarios"] = self._ckb_intermediarios.checked.get("salvar_intermediarios", False)
        self.preferences["crs"] = self._crs_selector.get_crs()
        if self._csv_grid.isVisible():
            self.preferences["csv_fields"] = self._csv_grid.values
        self.logger.info("Preferencias salvas no cache", code="PB_PREFS_SAVED")