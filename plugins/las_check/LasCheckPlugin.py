# -*- coding: utf-8 -*-
"""
LasCheckPlugin — Ferramenta de verificação de qualidade em nuvens LAS/LAZ
==========================================================================
Executa 8 checks de qualidade em arquivos LAS/LAZ e exibe dados
no GridLabel com valores compactos.

Fluxo:
  - SelectorGrid de entrada detecta mudança no path automaticamente
  - GridCheckBox para selecionar quais checks executar
  - ExecutionButtons: EXECUTAR
  - PipelineRunner + LasCheckStep para execução em background
  - GridLabel com todos os resultados
"""

from __future__ import annotations

import json
import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step import LasCheckStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.grid.GridSelector import GridSelector
from utils.ExplorerUtils import ExplorerUtils
from utils.las.LasLayerSource import LasLayerSource
from utils.MessageBox import MessageBox
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil


# ── Configuração dos checks ─────────────────────────────────────────────
CHECK_CONFIG: dict[str, dict] = {
    "point_count": {
        "label": "Contagem de Pontos",
        "description": "Verifica se ha pontos suficientes (> 0)",
        "default": True,
    },
    "bbox": {
        "label": "Bounding Box",
        "description": "Verifica se a bbox tem dimensoes validas",
        "default": True,
    },
    "rgb": {
        "label": "Bandas RGB",
        "description": "Verifica presenca de bandas RGB",
        "default": True,
    },
    "classification": {
        "label": "Classificacao",
        "description": "Verifica codigos de classificacao LAS (0-255)",
        "default": True,
    },
    "zero_coords": {
        "label": "Coordenadas Zero",
        "description": "Verifica pontos com X=Y=Z=0",
        "default": True,
    },
    "duplicates": {
        "label": "Duplicatas XY",
        "description": "Verifica duplicatas de coordenadas XY",
        "default": True,
    },
    "density": {
        "label": "Densidade / Gaps",
        "description": "Calcula densidade de pontos por area",
        "default": True,
    },
    "intensity": {
        "label": "Intensidade",
        "description": "Verifica range de intensidade (0-65535)",
        "default": True,
    },
    "statistics": {
        "label": "Estatisticas Completas",
        "description": "BBox XYZ, RGB, densidade, pixel ideal + JSON",
        "default": True,
    },
}


class LasCheckPlugin(BasePlugin):
    """
    Plugin para verificar qualidade de nuvens LAS/LAZ.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._las_info: dict = {}
        self._statistics_data: dict | None = None  # dados completos do check statistics
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.LAS_CHECK.value,
            parent=parent,
            title="LAS Quality Check",
        )
        self.logger.info("Ferramenta inicializada", code="LASCHECK_READY")

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
                "description": "Salvar estatisticas em JSON",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executar checks de qualidade",
            },
        })
        self._btns.set_enabled("executar", False)
        self._btns.set_enabled("salvar_json", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Arquivo de Entrada" ────────────────────────
        grupo_entrada = GroupPainel("Arquivo de Entrada")
        self.main_layout.addWidget(grupo_entrada)

        self._selector_grid = GridSelector(
            {
                "LAS/LAZ de Entrada": {
                    "file_filter": self._LAS_FILTER,
                    "browse_mode": "open_file",
                    "placeholder": "Selecione o arquivo LAS/LAZ...",
                },
            },
        )
        grupo_entrada.group_layout.addWidget(self._selector_grid)

        sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
        sel_entrada.edit.textChanged.connect(self._on_input_path_changed)

        # ── GroupPainel "Checks" ────────────────────────────────────
        grupo_checks = GroupPainel("Checks")
        self.main_layout.addWidget(grupo_checks)

        self._grid_checks = GridCheckBox(CHECK_CONFIG, num_columns=3)
        grupo_checks.group_layout.addWidget(self._grid_checks)

        # ── GroupPainel "Resultados" ────────────────────────────────
        grupo_result = GroupPainel("Resultados")
        self.main_layout.addWidget(grupo_result)

        self._result_label = GridLabel(
            {
                "total_pontos": {"label": "Total Pontos", "value": "—"},
                "altimetria": {"label": "Altitude", "value": "—"},
                "density": {"label": "Densidade", "value": "—"},
                "rgb": {"label": "RGB Check", "value": "—"},
                "zero_coords": {"label": "Coord Zero", "value": "—"},
                "rgb_red": {"label": "Red Stats", "value": "—"},
                "bbox": {"label": "BBox", "value": "—"},
                "rgb_green": {"label": "Green Stats", "value": "—"},
                "area_bbox": {"label": "Area BBox", "value": "—"},
                "rgb_blue": {"label": "Blue Stats", "value": "—"},
                "volume_bbox": {"label": "Volume BBox", "value": "—"},
                "scan_angle": {"label": "Scan Angle", "value": "—"},
                "gps_time": {"label": "GPS Time", "value": "—"},
                "resumo": {"label": "Resumo", "value": "—"},
            },
            columns=2,
        )
        grupo_result.group_layout.addWidget(self._result_label)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_input_path_changed(self, text: str):
        """Disparado quando o texto do selector de entrada muda."""
        path = text.strip()
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz") or not os.path.isfile(path):
            return
        if getattr(self, "_loading_las", False):
            return
        if path == self._current_path:
            return
        self._carregar_las(path)

    def _on_executar(self):
        """Executa os checks de qualidade via PipelineRunner em background."""
        self.logger.info(
            "Botao EXECUTAR pressionado",
            code="LASCHECK_EXEC_BTN",
            path=self._current_path,
        )

        if self._runner is not None and self._runner.isRunning():
            self.logger.warning(
                "Tentativa de executar enquanto ja em execucao",
                code="LASCHECK_EXEC_ALREADY_RUNNING",
            )
            MessageBox.show_warning(
                "Ja existe uma verificacao em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            self.logger.warning(
                "Tentativa de executar sem LAS carregado",
                code="LASCHECK_EXEC_NO_FILE",
            )
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="LAS Quality Check",
            )
            return

        checks_enabled = self._grid_checks.checked
        if not checks_enabled:
            self.logger.warning(
                "Tentativa de executar sem checks selecionados",
                code="LASCHECK_EXEC_NO_CHECKS",
            )
            MessageBox.show_warning(
                "Selecione ao menos um check para executar.",
                title="LAS Quality Check",
            )
            return

        # Prepara UI para execução
        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)
        self._statistics_data = None

        # Reseta resultados checks de qualidade + estatisticas
        self._result_label.set_values({
            "total_pontos": "—",
            "altimetria": "—",
            "density": "—",
            "rgb": "—",
            "zero_coords": "—",
            "rgb_red": "—",
            "bbox": "—",
            "rgb_green": "—",
            "area_bbox": "—",
            "rgb_blue": "—",
            "volume_bbox": "—",
            "scan_angle": "—",
            "gps_time": "—",
            "resumo": "—",
        })

        n_checks = len(checks_enabled)
        self.logger.info(
            "Iniciando execucao dos checks em background",
            code="LASCHECK_EXEC_START",
            path=self._current_path,
            n_checks=n_checks,
            checks=list(checks_enabled.keys()),
            ext=os.path.splitext(self._current_path)[1].lower(),
            total_points=self._las_info.get("n_pontos", 0),
        )

        SignalManager.instance().execution_started.emit(self.tool_key)

        # Inicia monitoramento de estatísticas para estimar tempo total
        self.statistics.start(
            n=0,
            ntype=ProcessStatisticsUtil.POINTS,
            ntotal=n_checks,
        )
        total_estimate = max(
            self.statistics.remaining_time,
            self.statistics.total_time,
            30.0,
        )
        self.logger.info(
            "Estimativa de tempo calculada para HUD stages",
            code="LASCHECK_STAGE_TIME",
            total_estimate_s=round(total_estimate, 1),
            n_stages=n_checks,
            remaining_time_s=round(self.statistics.remaining_time, 1),
            historical_time_s=round(self.statistics.total_time, 1),
        )

        SignalManager.instance().hud_show.emit({
            "message": "Verificando nuvem de pontos...",
            "stages": [total_estimate, n_checks],
        })
        SignalManager.instance().console_message.emit(
            f"[LasCheck] Iniciando {n_checks} checks em: "
            f"{os.path.basename(self._current_path)}"
        )

        # Cria step que executa checks inline na QThread
        # checks_enabled é parâmetro exclusivo do step (Contrato 28)
        step = LasCheckStep(checks_enabled=checks_enabled)
        runner = PipelineRunner(
            steps=[step],
            input_path=self._current_path,
            output_path=os.path.dirname(self._current_path),
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
            code="LASCHECK_RUNNER_STARTED",
            thread_id=id(runner),
        )

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        self.logger.info(
            "Pipeline finalizada com sucesso",
            code="LASCHECK_PIPELINE_DONE",
        )
        results = context.get_result("check_results", {})
        summary = context.get_result("summary", {})

        pass_count = summary.get("pass", 0)
        warn_count = summary.get("warning", 0)
        fail_count = summary.get("fail", 0)
        total = summary.get("total", 0)

        # Resumo
        self._result_label.set("resumo",
            f"{pass_count} ✅ {warn_count} ⚠️ {fail_count} ❌ ({total})")

        # Atualiza cada check apenas com o valor/mensagem (sem icone/rotulo)
        for check_name in ("bbox", "rgb", "zero_coords", "density"):
            result = results.get(check_name)
            if not result:
                continue
            message = result.get("message", "")
            status = result.get("status", "")
            # Mostra apenas o dado, sem APROVADO/ATENCAO/FALHA
            if status == "skipped":
                self._result_label.set(check_name, "-")
            else:
                self._result_label.set(check_name, message)

        # ── Processa check "statistics" (labels separados) ─────────────
        stats_result = results.get("statistics")
        if stats_result and stats_result.get("status") not in ("skipped",):
            detail_str = stats_result.get("detail", "")

            try:
                self._statistics_data = json.loads(detail_str)
                self._statistics_data["arquivo"] = self._current_path

                # Preenche labels específicos
                alt = self._statistics_data.get("altimetria", {})
                if alt:
                    self._result_label.set(
                        "altimetria",
                        f"med:{alt.get('media',0):.2f} "
                        f"P5%:{alt.get('p5',0):.2f} "
                        f"P95%:{alt.get('p95',0):.2f}",
                    )

                rgb = self._statistics_data.get("rgb", {})
                if rgb.get("presente"):
                    for banda in ("red", "green", "blue"):
                        bdata = rgb.get(banda, {})
                        if bdata:
                            self._result_label.set(
                                f"rgb_{banda}",
                                f"med:{bdata.get('media',0):.0f} "
                                f"P5%:{bdata.get('p5',0):.0f} "
                                f"P95%:{bdata.get('p95',0):.0f}",
                            )
                        else:
                            self._result_label.set(f"rgb_{banda}", "—")
                else:
                    for banda in ("red", "green", "blue"):
                        self._result_label.set(f"rgb_{banda}", "ausente")

                area_val = self._statistics_data.get("area_bbox_m2", 0)
                self._result_label.set(
                    "area_bbox", f"{area_val:,.2f} m²"
                )

                volume_val = self._statistics_data.get("volume_bbox_m3", 0)
                self._result_label.set(
                    "volume_bbox", f"{volume_val:,.2f} m³"
                )

                # ── Scan Angle ─────────────────────────────────────
                scan_angle = self._statistics_data.get("scan_angle")
                if scan_angle:
                    self._result_label.set(
                        "scan_angle",
                        f"min:{scan_angle.get('min',0):.1f}° "
                        f"max:{scan_angle.get('max',0):.1f}° "
                        f"med:{scan_angle.get('mean',0):.1f}°",
                    )
                else:
                    self._result_label.set("scan_angle", "ausente")

                # ── GPS Time ────────────────────────────────────────
                gps_time = self._statistics_data.get("gps_time")
                if gps_time:
                    self._result_label.set(
                        "gps_time",
                        f"min:{gps_time.get('min',0):.2f} "
                        f"max:{gps_time.get('max',0):.2f} "
                        f"med:{gps_time.get('mean',0):.2f}",
                    )
                else:
                    self._result_label.set("gps_time", "ausente")

                # Habilita botao JSON
                self._btns.set_enabled("salvar_json", True)
                self.logger.info(
                    "Dados de estatisticas prontos para exportacao JSON",
                    code="LASCHECK_STATS_JSON_READY",
                    path=self._current_path,
                )
                SignalManager.instance().console_message.emit(
                    "[LasCheck] Estatisticas completas disponiveis "
                    "(botao SALVAR JSON ativo)"
                )
            except (json.JSONDecodeError, TypeError) as e:
                self.logger.error(
                    "Erro ao fazer parse do JSON de estatisticas",
                    code="LASCHECK_STATS_PARSE_ERR",
                    error=str(e),
                )
                self._result_label.set("altimetria", "Erro")
        else:
            for lbl in ("altimetria", "rgb_red", "rgb_green", "rgb_blue", "area_bbox", "volume_bbox"):
                self._result_label.set(lbl, "-" if stats_result else "—")
            self._result_label.set("scan_angle", "-" if stats_result else "—")
            self._result_label.set("gps_time", "-" if stats_result else "—")

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasCheck] Checks concluidos! "
            f"{pass_count} ✅, {warn_count} ⚠️, {fail_count} ❌"
        )

        self.logger.info(
            "Checks concluidos com sucesso",
            code="LASCHECK_EXEC_DONE",
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            total=total,
        )

        if fail_count > 0:
            self.logger.warning(
                "Checks concluidos com falhas",
                code="LASCHECK_EXEC_HAS_FAILS",
                fail_count=fail_count,
                total=total,
            )
            MessageBox.show_warning(
                f"Checks concluidos com {fail_count} falha(s)!",
                title="LAS Quality Check",
            )

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        self.logger.critical(
            "Pipeline falhou com erro",
            code="LASCHECK_PIPELINE_FAILED",
            error=message,
            path=self._current_path,
        )
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasCheck] ERRO: {message}"
        )
        self.logger.error(
            "Erro nos checks",
            code="LASCHECK_EXEC_ERR",
            error=message,
            path=self._current_path,
        )

        # Exibe erro no GridLabel
        if "LAZ" in message or "laz" in message:
            self.logger.error(
                "Erro relacionado a LAZ",
                code="LASCHECK_LAZ_ERROR",
                message=message,
            )
            self._result_label.set("resumo", "❌ Erro LAZ - use .LAS")

        MessageBox.show_error(
            f"Erro durante os checks:\n{message}",
            title="LAS Quality Check",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
        self.logger.info(
            "PipelineRunner finalizado",
            code="LASCHECK_RUNNER_FINISHED",
        )
        self._runner = None
        self._btns.set_all_enabled(True)
        self._btns.set_enabled("executar", bool(self._current_path))
        # Mantem "salvar_json" apenas se ha dados de statistics disponiveis
        self._btns.set_enabled(
            "salvar_json",
            self._statistics_data is not None,
        )
        self.page.set_badge(self.page.PRONTA)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Handlers de Ação
    # ══════════════════════════════════════════════════════════════════

    def _on_salvar_json(self):
        """Abre dialogo para salvar o JSON de estatísticas em disco."""
        self.logger.info(
            "Botao SALVAR JSON pressionado",
            code="LASCHECK_SAVE_JSON_BTN",
            path=self._current_path,
        )

        if self._statistics_data is None:
            self.logger.warning(
                "Tentativa de salvar JSON sem dados disponiveis",
                code="LASCHECK_SAVE_JSON_NO_DATA",
            )
            MessageBox.show_warning(
                "Nao ha dados de estatisticas para salvar.\n"
                "Execute os checks com 'Estatisticas Completas' habilitado.",
                title="LAS Quality Check",
            )
            return

        # Define nome padrão baseado no arquivo de entrada
        basename = os.path.splitext(os.path.basename(self._current_path))[0]
        default_name = f"{basename}_estatisticas_las.json"

        # Usa o diretório do próprio LAS como initial_dir com nome default
        las_dir = os.path.dirname(self._current_path)
        initial_path = os.path.join(las_dir, default_name)

        file_path = ExplorerUtils.save_file(
            "Salvar Estatisticas LAS",
            initial_dir=initial_path,
            file_filter="JSON (*.json)",
            parent=self,
        )

        if not file_path:
            self.logger.info(
                "Usuario cancelou o dialogo de salvamento",
                code="LASCHECK_SAVE_JSON_CANCELLED",
            )
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._statistics_data, f, indent=2, ensure_ascii=False)

            self.logger.info(
                "JSON de estatisticas salvo com sucesso",
                code="LASCHECK_SAVE_JSON_OK",
                path=file_path,
                filesize=os.path.getsize(file_path),
            )

            SignalManager.instance().console_message.emit(
                f"[LasCheck] JSON salvo: {file_path}"
            )

            MessageBox.show_info(
                f"Estatisticas salvas em:\n{file_path}",
                title="LAS Quality Check",
            )

        except OSError as e:
            self.logger.error(
                "Erro ao salvar JSON de estatisticas",
                code="LASCHECK_SAVE_JSON_ERR",
                path=file_path,
                error=str(e),
            )
            MessageBox.show_error(
                f"Erro ao salvar arquivo:\n{str(e)}",
                title="LAS Quality Check",
            )

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_las(self, path: str):
        """Carrega metadados do LAS e atualiza a UI."""
        if getattr(self, "_loading_las", False):
            self.logger.debug(
                "Carregamento ja em andamento, ignorando chamada",
                code="LASCHECK_LAS_ALREADY_LOADING",
                path=path,
            )
            return
        self._loading_las = True

        self.logger.info(
            "Carregando LAS",
            code="LASCHECK_LAS_LOAD",
            path=path,
            ext=os.path.splitext(path)[1].lower(),
            filesize=os.path.getsize(path) if os.path.isfile(path) else 0,
        )

        try:
            info = LasLayerSource.get_info(path, tool_key=self.tool_key)
            if info.get("error"):
                raise RuntimeError(info["error"])

            n_pontos = info["point_count"]
            has_rgb = info["has_rgb"]

            self._current_path = path
            self._las_info = {
                "path": path,
                "n_pontos": n_pontos,
                "has_rgb": has_rgb,
            }

            # Atualiza UI com bloqueio de sinais
            sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
            sel_entrada.edit.blockSignals(True)
            sel_entrada.set_path(path)
            sel_entrada.edit.blockSignals(False)

            self._result_label.set("total_pontos", f"{n_pontos:,}")

            bbox = LasLayerSource.get_bounding_box(path, tool_key=self.tool_key)
            if bbox:
                self._result_label.set(
                    "bbox",
                    f"X[{bbox['x_min']:.1f}, {bbox['x_max']:.1f}] "
                    f"Y[{bbox['y_min']:.1f}, {bbox['y_max']:.1f}]",
                )
                self.logger.debug(
                    "Bounding box obtida",
                    code="LASCHECK_BBOX_OK",
                    **bbox,
                )
            else:
                self._result_label.set("bbox", "—")
                self.logger.warning(
                    "Bounding box nao disponivel",
                    code="LASCHECK_BBOX_UNAVAILABLE",
                )

            self._btns.set_enabled("executar", True)
            self.page.set_badge(self.page.PRONTA)

            SignalManager.instance().console_message.emit(
                f"[LasCheck] Carregado: {os.path.basename(path)} "
                f"({n_pontos:,} pontos, RGB: {'sim' if has_rgb else 'nao'})"
            )

            self.logger.info(
                "LAS carregado com sucesso",
                code="LASCHECK_LAS_LOADED",
                path=path,
                points=n_pontos,
                has_rgb=has_rgb,
            )

        except FileNotFoundError as e:
            self.logger.error(
                "Arquivo nao encontrado",
                code="LASCHECK_FILE_NOT_FOUND",
                error=str(e),
                path=path,
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Arquivo nao encontrado:\n{path}",
                title="LAS Quality Check",
            )

        except RuntimeError as e:
            self.logger.error(
                "Erro de metadados do LAS",
                code="LASCHECK_META_ERR",
                error=str(e),
                path=path,
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao ler metadados do LAS:\n{str(e)}",
                title="LAS Quality Check",
                detail=traceback.format_exc(),
            )

        except Exception as e:
            self.logger.critical(
                "Erro inesperado ao carregar LAS",
                code="LASCHECK_LAS_LOAD_ERR",
                error=str(e),
                path=path,
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar arquivo LAS:\n{str(e)}",
                title="LAS Quality Check",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False
            self.logger.debug(
                "Flag _loading_las resetada",
                code="LASCHECK_LOADING_FLAG_RESET",
            )

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferencias", code="LASCHECK_PREFS_LOAD")
        last_path = self.preferences.get("last_path", "")
        checks_enabled = self.preferences.get("checks_enabled", {})

        if last_path:
            self._carregar_las(last_path)

        if checks_enabled:
            self._grid_checks.set_all(checks_enabled)

        self.logger.info("Preferencias carregadas", code="LASCHECK_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        self.preferences["checks_enabled"] = self._grid_checks.all
        self.logger.info("Preferencias salvas no cache", code="LASCHECK_PREFS_SAVED")