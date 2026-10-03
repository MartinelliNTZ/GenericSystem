# -*- coding: utf-8 -*-
"""
LasReprojectionPlugin — Ferramenta de Reprojeção de Nuvens LAS/LAZ
====================================================================
Permite reprojetar (transformar CRS) nuvens de pontos LAS/LAZ
com detecção automática do CRS de origem e seleção do CRS de destino.

O CRS de origem é detectado automaticamente pelo ComplexSelector (crs_enable)
ao selecionar o arquivo de entrada. O CRS de destino é selecionado manualmente
no próprio seletor de saída (também com crs_enable).

Fluxo:
  - GridComplexSelector com crs_enable=True em ambos selectors
  - ExecutionButtons: EXECUTAR
  - PipelineRunner + LasReprojectionStep para execução em background
  - GridLabel com metadados da reprojeção
"""

from __future__ import annotations

import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from plugins.BasePlugin import BasePlugin
from plugins.las_reprojection.LasReprojectionStep import LasReprojectionStep
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from resources.widgets.GroupPainel import GroupPainel
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil
from utils.MessageBox import MessageBox


class LasReprojectionPlugin(BasePlugin):
    """
    Plugin para reprojetar nuvens LAS/LAZ entre sistemas de coordenadas.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.LAS_REPROJECTION.value,
            parent=parent,
            title="Reprojeção LAS",
        )
        self.logger.info("Ferramenta inicializada", code="LASREPROJ_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Constrói a interface completa do plugin."""
        super()._build_ui()

        # ── ExecutionButtons ────────────────────────────────────────
        self._btns = ExecutionButtons(self, {
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Reprojeta a nuvem LAS/LAZ",
            },
        })
        self._btns.set_enabled("executar", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Arquivos" ──────────────────────────────────
        grupo_arquivos = GroupPainel("Arquivos")
        self.main_layout.addWidget(grupo_arquivos)

        # GridComplexSelector com CRS embutido em entrada e saída
        # Entrada: detecta CRS automaticamente (input + crs_enable)
        # Saída: permite selecionar CRS de destino manualmente (output + crs_enable)
        self._selector_grid = GridComplexSelector(
            {
                "LAS/LAZ de Entrada": {
                    "file_filter": self._LAS_FILTER,
                    "mode_type": "input",
                    "allow_file": True,
                    "allow_folder": False,
                    "multiple": False,
                    "show_project_button": True,
                    "crs_enable": True,  # CRS de origem embutido (detecta automaticamente)
                },
                "Saída": {
                    "mode_type": "output",
                    "parent": "LAS/LAZ de Entrada",
                    "dynamic_parent": True,
                    "allow_file": True,
                    "allow_folder": False,
                    "multiple": False,
                    "show_suggest_button": True,
                    "suffix": "_reproj",
                    "extension": "las",
                    "fixed_name": "Lasreproj.las",
                    "crs_enable": True,  # CRS de destino embutido (seleção manual)
                },
            },
        )
        grupo_arquivos.group_layout.addWidget(self._selector_grid)

        # Conecta callback de mudança na entrada
        self._selector_grid.set_on_input_changed(self._on_input_changed)

        # Conecta mudanças nos CRS embutidos para habilitar botão
        entrada_crs = self._selector_grid["LAS/LAZ de Entrada"].crs_widget
        saida_crs = self._selector_grid["Saída"].crs_widget
        if entrada_crs:
            entrada_crs.crs_changed.connect(self._atualizar_botao_executar)
        if saida_crs:
            saida_crs.crs_changed.connect(self._atualizar_botao_executar)

        # ── GroupPainel "Metadados" ─────────────────────────────────
        grupo_meta = GroupPainel("Metadados")
        self.main_layout.addWidget(grupo_meta)

        self._result_label = GridLabel(
            {
                "arquivo": {"label": "Arquivo", "value": "—"},
                "crs_origem": {"label": "CRS Origem", "value": "—"},
                "crs_destino": {"label": "CRS Destino", "value": "—"},
                "n_pontos": {"label": "Total Pontos", "value": "—"},
                "status": {"label": "Status", "value": "—"},
            },
            columns=2,
        )
        grupo_meta.group_layout.addWidget(self._result_label)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_input_changed(self, label: str, paths: list[str]):
        """Disparado quando o path da entrada muda."""
        if label != "LAS/LAZ de Entrada":
            return
        path = paths[0] if paths else ""
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
        """Executa a reprojeção via PipelineRunner em background."""
        self.logger.info(f"EXECUTAR: {self._current_path}")

        if self._runner is not None and self._runner.isRunning():
            self.logger.warning("Ja em execucao")
            MessageBox.show_warning(
                "Ja existe uma reprojeção em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            self.logger.warning(
                "Tentativa de executar sem LAS carregado",
                code="LASREPROJ_EXEC_NO_FILE",
            )
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="Reprojeção LAS",
            )
            return

        # Obtém CRS dos widgets embutidos nos selectors
        entrada_selector = self._selector_grid["LAS/LAZ de Entrada"]
        saida_selector = self._selector_grid["Saída"]

        source_crs = entrada_selector.crs
        target_crs = saida_selector.crs

        if not source_crs:
            self.logger.warning(
                "CRS de origem nao definido",
                code="LASREPROJ_NO_SRC_CRS",
            )
            MessageBox.show_warning(
                "Defina o CRS de origem.", title="Reprojeção LAS",
            )
            return

        if not target_crs:
            self.logger.warning(
                "CRS de destino nao definido",
                code="LASREPROJ_NO_TGT_CRS",
            )
            MessageBox.show_warning(
                "Defina o CRS de destino.", title="Reprojeção LAS",
            )
            return

        # Resolve output_path do selector de saída
        output_path = saida_selector.path()
        if not output_path:
            # Fallback: mesmo diretório do input
            basename = os.path.splitext(os.path.basename(self._current_path))[0]
            output_dir = os.path.dirname(self._current_path)
            output_path = os.path.join(output_dir, f"{basename}_reproj.las")

        # Prepara UI para execução
        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)
        self._result_label.set("status", "Reprojetando...")

        self.logger.info(f"Reprojetando: {self._current_path} → {output_path} ({source_crs} → {target_crs})")

        # Inicia monitoramento de estatísticas
        self.statistics.start(n=0, ntype=ProcessStatisticsUtil.POINTS, ntotal=0)
        total_estimate = self.get_eta_seconds()

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"Reprojetando: {os.path.basename(self._current_path)} "
            f"{source_crs} → {target_crs}"
        )
        SignalManager.instance().hud_show.emit({
            "message": "Reprojetando nuvem de pontos...",
            "timer": total_estimate,
            "eta": total_estimate,
        })

        # Cria step com os CRS e output_path direto
        step = LasReprojectionStep(
            source_crs=source_crs,
            target_crs=target_crs,
            output_path=output_path,
        )

        runner = PipelineRunner(
            steps=[step],
            input_path=self._current_path,
            output_path=os.path.dirname(output_path),
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
            code="LASREPROJ_RUNNER_STARTED",
            thread_id=id(runner),
        )

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        self.logger.info(
            "Reprojeção concluida com sucesso",
            code="LASREPROJ_PIPELINE_DONE",
        )

        self.statistics.end()

        result = context.get_result("reprojection_result", {})

        n_points = result.get("n_points", 0)
        output_path = result.get("output_path", "")
        source_crs = result.get("source_crs", "")
        target_crs = result.get("target_crs", "")

        self._result_label.set("status", "✅ Concluído")
        self._result_label.set("n_pontos", f"{n_points:,}")
        self._result_label.set("crs_origem", source_crs)
        self._result_label.set("crs_destino", target_crs)

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"Reprojeta concluida! "
            f"{n_points:,} pontos | {source_crs} → {target_crs}"
        )

        self.stats_message(
            n_arquivos=1,
            n_processed=n_points,
            ntype="pontos",
        )
        self.output_message(os.path.dirname(output_path), label="Pasta de Saída")

        self.logger.info(f"Concluido: {n_points} pts → {output_path}")

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        self.logger.critical(
            "Reprojeção falhou",
            code="LASREPROJ_PIPELINE_FAILED",
            error=message,
        )
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"ERRO: {message}"
        )
        self._result_label.set("status", "❌ Erro")
        self.logger.error(
            "Erro na reprojeção",
            code="LASREPROJ_EXEC_ERR",
            error=message,
        )
        MessageBox.show_error(
            f"Erro durante a reprojeção:\n{message}",
            title="Reprojeção LAS",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
        self.logger.info(
            "PipelineRunner finalizado",
            code="LASREPROJ_RUNNER_FINISHED",
        )
        self._runner = None
        self._btns.set_all_enabled(True)
        self._atualizar_botao_executar()
        self.page.set_badge(self.page.PRONTA)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_las(self, path: str):
        """Carrega metadados do LAS e atualiza UI."""
        if getattr(self, "_loading_las", False):
            return
        self._loading_las = True

        self.logger.info(
            "Carregando LAS para reprojeção",
            code="LASREPROJ_LAS_LOAD",
            path=path,
        )

        try:
            from utils.las.LasLayerSource import LasLayerSource

            info = LasLayerSource.get_info(path, tool_key=self.tool_key)
            if info.get("error"):
                raise RuntimeError(info["error"])

            n_pontos = info["point_count"]
            self._current_path = path

            # O CRS de origem é detectado automaticamente pelo ComplexSelector
            # (crs_enable=True no input faz isso internamente via _auto_detect_crs)

            # Atualiza UI
            self._result_label.set("arquivo", os.path.basename(path))
            self._result_label.set("n_pontos", f"{n_pontos:,}")
            self._result_label.set("status", "Carregado")
            self._atualizar_botao_executar()

            # Sincroniza CRS detectado no label de metadados
            entrada_selector = self._selector_grid["LAS/LAZ de Entrada"]
            if entrada_selector.crs:
                self._result_label.set("crs_origem", entrada_selector.crs)
            else:
                self._result_label.set("crs_origem", "Não detectado")

            SignalManager.instance().console_message.emit(
                f"Carregado: {os.path.basename(path)} "
                f"({n_pontos:,} pontos, CRS: {entrada_selector.crs or 'não detectado'})"
            )

            self.logger.info(
                "LAS carregado com sucesso",
                code="LASREPROJ_LAS_LOADED",
                path=path,
                points=n_pontos,
                crs=entrada_selector.crs,
            )

        except Exception as e:
            self.logger.error(
                "Erro ao carregar LAS",
                code="LASREPROJ_LAS_LOAD_ERR",
                error=str(e),
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar LAS:\n{str(e)}",
                title="Reprojeção LAS",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False

    def _atualizar_botao_executar(self):
        """Habilita/desabilita o botão executar conforme estado."""
        entrada_selector = self._selector_grid["LAS/LAZ de Entrada"]
        saida_selector = self._selector_grid["Saída"]
        tem_path = bool(self._current_path)
        tem_crs_origem = bool(entrada_selector.crs)
        tem_crs_destino = bool(saida_selector.crs)
        pode_executar = tem_path and tem_crs_origem and tem_crs_destino
        self._btns.set_enabled("executar", pode_executar)

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferencias", code="LASREPROJ_PREFS_LOAD")
        last_path = self.preferences.get("last_path", "")
        last_target_crs = self.preferences.get("last_target_crs", "")
        last_output_path = self.preferences.get("last_output_path", "")

        if last_path:
            self._selector_grid["LAS/LAZ de Entrada"].set_path(last_path)

        if last_output_path:
            self._selector_grid["Saída"].set_path(last_output_path)

        if last_target_crs:
            saida_crs = self._selector_grid["Saída"].crs_widget
            if saida_crs:
                saida_crs.set_crs(last_target_crs)

        self.logger.info("Preferencias carregadas", code="LASREPROJ_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        saida_crs = self._selector_grid["Saída"].crs_widget
        if saida_crs:
            self.preferences["last_target_crs"] = saida_crs.get_crs()
        self.preferences["last_output_path"] = self._selector_grid["Saída"].path() or ""
        self.logger.info("Preferencias salvas no cache", code="LASREPROJ_PREFS_SAVED")