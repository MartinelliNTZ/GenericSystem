# -*- coding: utf-8 -*-
"""
ScanAngleFilterPlugin — Filtro de scan angle em nuvens LAS/LAZ
=================================================================
Permite ao usuário definir valores mínimo e máximo de scan angle.
Gera dois arquivos: cloud_filtered.las (pontos dentro do range)
e cloud_remaining.las (pontos fora do range).

Usa GridComplexSelector com 1 input e 2 outputs (com parent linking):
  - Input: arquivo LAS/LAZ
  - Output Filtered: cloud_filtered.las
  - Output Remaining: cloud_remaining.las

Fluxo:
  - ComplexSelector de entrada (input)
  - 2 ComplexSelectors de saída (output) com parent linking
  - GridDoubleSpinBox para min/max scan angle
  - ExecutionButtons: USAR ORIGEM + EXECUTAR
  - PipelineRunner em background.
"""

from __future__ import annotations

import os
import traceback

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.GroupPainel import GroupPainel
from utils.ExplorerUtils import ExplorerUtils
from utils.las.LasLayerSource import LasLayerSource
from utils.MessageBox import MessageBox
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil


class ScanAngleFilterPlugin(BasePlugin):
    """
    Plugin para filtrar pontos de nuvens LAS/LAZ por scan angle.
    Gera cloud_filtered.las e cloud_remaining.las.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._las_info: dict = {}
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.SCAN_ANGLE_FILTER.value,
            parent=parent,
            title="Filtro Scan Angle",
        )
        self.logger.info("Ferramenta inicializada", code="TOOL_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Constrói a interface completa do plugin."""
        super()._build_ui()

        # ── ExecutionButtons ────────────────────────────────────────
        self._btns = ExecutionButtons(self, {
            "usar_origem": {
                "text": "USAR ORIGEM",
                "callback": self._on_usar_origem,
                "type": "secondary",
                "description": "Salvar na pasta do arquivo LAS original",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executar filtro de scan angle",
            },
        })
        self._btns.set_enabled("executar", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Entrada e Saída" ───────────────────────────
        grupo_io = GroupPainel("Arquivos")
        self.main_layout.addWidget(grupo_io)

        self._grid = GridComplexSelector({
            "Entrada": {
                "file_filter": self._LAS_FILTER,
                "mode_type": "input",
                "allow_file": True,
                "allow_folder": False,
                "multiple": False,
                "show_project_button": True,
                "label_text": "LAS/LAZ de Entrada",
                "placeholder": "Selecione o arquivo LAS/LAZ...",
            },
            "Filtrado": {
                "mode_type": "output",
                "parent": "Entrada",
                "dynamic_parent": True,
                "allow_file": True,
                "allow_folder": False,
                "show_suggest_button": True,
                "fixed_name": "cloud_filtered.las",
                "subfolder": "scan_angle_filter",
                "label_text": "LAS Filtrado",
                "placeholder": "cloud_filtered.las",
                "suffix": "_filtered",
                "extension": "las",
            },
            "Remanescente": {
                "mode_type": "output",
                "parent": "Entrada",
                "dynamic_parent": True,
                "allow_file": True,
                "allow_folder": False,
                "show_suggest_button": True,
                "fixed_name": "cloud_remaining.las",
                "subfolder": "scan_angle_filter",
                "label_text": "LAS Remanescente",
                "placeholder": "cloud_remaining.las",
                "suffix": "_remaining",
                "extension": "las",
            },
        })
        grupo_io.group_layout.addWidget(self._grid)

        # Conecta callback de mudança de entrada
        self._grid.set_on_input_changed(self._on_input_changed)

        # ── GroupPainel "Configurações" ─────────────────────────────
        grupo_config = GroupPainel("Configurações")
        self.main_layout.addWidget(grupo_config)

        self._spin_scan = GridDoubleSpinBox(
            {
                "min_angle": {
                    "label": "Ângulo Mínimo",
                    "description": "Valor mínimo do scan angle (graus)",
                    "decimal": 1,
                    "default": -15.0,
                    "min": -180.0,
                    "max": 180.0,
                    "step": 0.5,
                    "suffix": "°",
                },
                "max_angle": {
                    "label": "Ângulo Máximo",
                    "description": "Valor máximo do scan angle (graus)",
                    "decimal": 1,
                    "default": 15.0,
                    "min": -180.0,
                    "max": 180.0,
                    "step": 0.5,
                    "suffix": "°",
                },
            },
        )
        grupo_config.group_layout.addWidget(self._spin_scan)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_input_changed(self, label: str, paths: list[str]):
        """Disparado quando o path de entrada muda."""
        path = paths[0] if paths else ""
        if not path or getattr(self, "_loading_prefs", False):
            return

        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz") or not os.path.isfile(path):
            return
        if path == self._current_path:
            return
        self._carregar_las(path)

    def _on_usar_origem(self):
        """Preenche caminhos de saída usando a origem do LAS."""
        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS selecionado.\nSelecione primeiro.",
                title="Filtro Scan Angle",
            )
            return

        self._grid.use_origin_all()
        self._btns.set_enabled("executar", True)
        SignalManager.instance().console_message.emit(
            "[ScanAngleFilter] Destinos configurados a partir da origem"
        )

    def _on_executar(self):
        """Executa o filtro de scan angle via processamento interno."""
        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Já existe um filtro em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS selecionado.", title="Filtro Scan Angle",
            )
            return

        if not self._las_info.get("has_scan_angle", False):
            MessageBox.show_warning(
                "O arquivo LAS não possui o campo scan_angle.\n"
                "Não é possível filtrar por scan angle.",
                title="Filtro Scan Angle",
            )
            return

        min_angle = self._spin_scan.get("min_angle")
        max_angle = self._spin_scan.get("max_angle")

        if min_angle >= max_angle:
            MessageBox.show_warning(
                "O ângulo mínimo deve ser menor que o ângulo máximo.",
                title="Filtro Scan Angle",
            )
            return

        output_filtered = self._grid["Filtrado"].path()
        output_remaining = self._grid["Remanescente"].path()

        if not output_filtered:
            MessageBox.show_warning(
                "Defina o caminho do LAS filtrado.\nUse USAR ORIGEM ou preencha manualmente.",
                title="Filtro Scan Angle",
            )
            return

        if not output_remaining:
            MessageBox.show_warning(
                "Defina o caminho do LAS remanescente.\nUse USAR ORIGEM ou preencha manualmente.",
                title="Filtro Scan Angle",
            )
            return

        n_total = self._las_info.get("point_count", 0)

        self.statistics.start(
            n=0,
            ntype=ProcessStatisticsUtil.POINTS,
            ntotal=n_total,
        )

        SignalManager.instance().console_message.emit(
            f"[ScanAngleFilter] {self.statistics.summary}"
        )

        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)

        total_estimate_seconds = max(
            self.statistics.remaining_time,
            self.statistics.total_time,
            30.0,
        )

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({
            "message": "Filtrando por scan angle...",
            "stages": [total_estimate_seconds, 4],
        })
        SignalManager.instance().console_message.emit(
            f"[ScanAngleFilter] Iniciando filtro "
            f"(min={min_angle}°, max={max_angle}°)..."
        )

        self.logger.info(
            "Iniciando filtro de scan angle",
            code="FILTER_START",
            path=self._current_path,
            min_angle=min_angle,
            max_angle=max_angle,
            output_filtered=output_filtered,
            output_remaining=output_remaining,
            n_total=n_total,
            eta=self.statistics.eta_str,
            total_estimate_seconds=round(total_estimate_seconds, 1),
        )

        # Executa o filtro em background via QTimer para não travar a UI
        # Processamento síncrono simples: lê o LAS, aplica máscara, salva 2 arquivos
        QTimer.singleShot(0, lambda: self._process_in_background(
            self._current_path,
            min_angle,
            max_angle,
            output_filtered,
            output_remaining,
            n_total,
        ))

    def _process_in_background(
        self,
        path: str,
        min_angle: float,
        max_angle: float,
        output_filtered: str,
        output_remaining: str,
        n_total: int,
    ):
        """Processa o filtro de scan angle em background."""
        import laspy
        import numpy as np

        try:
            self.logger.info("Lendo LAS", code="LAS_READ", path=path)

            las = laspy.read(path)
            scan_angle = np.asarray(las.scan_angle_rank if hasattr(las, 'scan_angle_rank') else 
                                     las.scan_angle if hasattr(las, 'scan_angle') else 
                                     las.scanAngleRank if hasattr(las, 'scanAngleRank') else None)

            if scan_angle is None:
                raise RuntimeError("Campo scan_angle não encontrado no LAS")

            mask_filtered = (scan_angle >= min_angle) & (scan_angle <= max_angle)
            mask_remaining = ~mask_filtered

            n_filtered = int(np.sum(mask_filtered))
            n_remaining = int(np.sum(mask_remaining))

            self.logger.info(
                "Máscaras calculadas",
                code="MASK_CALC",
                n_total=n_total,
                n_filtered=n_filtered,
                n_remaining=n_remaining,
            )

            SignalManager.instance().console_message.emit(
                f"[ScanAngleFilter] Pontos no range: {n_filtered:,}"
            )

            # Salva filtrado
            if n_filtered > 0:
                LasLayerSource.create_filtered_las(
                    las, mask_filtered, output_filtered, tool_key=self.tool_key,
                )

            # Salva remanescente
            if n_remaining > 0:
                LasLayerSource.create_filtered_las(
                    las, mask_remaining, output_remaining, tool_key=self.tool_key,
                )

            self._on_done({
                "n_total": n_total,
                "n_filtered": n_filtered,
                "n_remaining": n_remaining,
                "output_filtered": output_filtered,
                "output_remaining": output_remaining,
            })

        except Exception as e:
            self._on_error(str(e))
            self.logger.error(
                "Erro no filtro de scan angle",
                code="FILTER_ERR",
                error=str(e),
                path=path,
            )

    # ══════════════════════════════════════════════════════════════════
    # Callbacks
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, results: dict):
        """Callback de sucesso do processamento."""
        n_total = results.get("n_total", 0)
        n_filtered = results.get("n_filtered", 0)
        n_remaining = results.get("n_remaining", 0)
        output_filtered = results.get("output_filtered", "")
        output_remaining = results.get("output_remaining", "")

        elapsed = self.statistics.end()
        self.logger.info(
            "Tempo de processamento registrado",
            code="STATS_RECORDED",
            elapsed_s=round(elapsed, 3),
            usages=self.statistics.usages,
        )

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[ScanAngleFilter] Filtro concluído! "
            f"{n_filtered:,} pontos no range, "
            f"{n_remaining:,} remanescentes."
        )

        self.logger.info(
            "Filtro concluído com sucesso",
            code="FILTER_DONE",
            total=n_total,
            filtrados=n_filtered,
            remanescentes=n_remaining,
            output_filtered=output_filtered,
            output_remaining=output_remaining,
        )

        msg = (
            f"Filtro por scan angle concluído!\n\n"
            f"Total de pontos: {n_total:,}\n"
            f"Pontos no range: {n_filtered:,}\n"
            f"Pontos remanescentes: {n_remaining:,}\n\n"
            f"Filtrado salvo em:\n{output_filtered}\n\n"
            f"Remanescente salvo em:\n{output_remaining}"
        )
        MessageBox.show_info(msg, title="Filtro Scan Angle")
        self._finish_execution()

    def _on_error(self, message: str):
        """Callback de erro do processamento."""
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[ScanAngleFilter] ERRO: {message}"
        )
        self.logger.error(
            "Erro no filtro de scan angle",
            code="FILTER_ERR",
            error=message,
            path=self._current_path,
        )
        MessageBox.show_error(
            f"Erro durante o filtro:\n{message}",
            title="Filtro Scan Angle",
        )
        self._finish_execution()

    def _finish_execution(self):
        """Restaura UI após execução (sucesso ou erro)."""
        self._runner = None
        self._btns.set_all_enabled(True)
        self._btns.set_enabled("executar", bool(self._current_path))
        self.page.set_badge(self.page.PRONTA)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_las(self, path: str):
        """Carrega metadados do LAS e verifica se tem scan_angle."""
        if getattr(self, "_loading_las", False):
            return
        self._loading_las = True

        self.logger.info("Carregando LAS", code="LAS_LOAD", path=path)

        try:
            info = LasLayerSource.get_info(path, tool_key=self.tool_key)
            if info.get("error"):
                raise RuntimeError(info["error"])

            n_pontos = info["point_count"]
            dim_names = info["dimension_names"]

            # Verifica scan_angle
            has_scan_angle = any(
                name in dim_names
                for name in ("scan_angle", "scan_angle_rank", "scanAngleRank")
            )

            self._current_path = path
            self._las_info = {
                "path": path,
                "point_count": n_pontos,
                "has_scan_angle": has_scan_angle,
            }

            self._btns.set_enabled("executar", has_scan_angle)
            self.page.set_badge(self.page.PRONTA if has_scan_angle else self.page.ERROR)

            if not has_scan_angle:
                SignalManager.instance().console_message.emit(
                    "[ScanAngleFilter] AVISO: LAS não possui campo scan_angle"
                )
                MessageBox.show_warning(
                    "O arquivo LAS não possui o campo scan_angle / scan_angle_rank.\n"
                    "O filtro de scan angle não será executado.",
                    title="Filtro Scan Angle",
                )

            self.logger.info(
                "LAS carregado",
                code="LAS_LOADED",
                path=path,
                points=n_pontos,
                has_scan_angle=has_scan_angle,
            )

        except Exception as e:
            self.logger.error(
                "Erro ao carregar LAS",
                code="LAS_LOAD_ERR",
                error=str(e),
                path=path,
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar arquivo LAS:\n{str(e)}",
                title="Filtro Scan Angle",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferências", code="PREFS_LOAD")

        self._loading_prefs = True

        file_path = self.preferences.get("file_path", "")
        min_angle = self.preferences.get("min_angle", -15.0)
        max_angle = self.preferences.get("max_angle", 15.0)

        if file_path:
            self._grid["Entrada"].set_path(file_path)

        self._spin_scan.set_values({"min_angle": min_angle, "max_angle": max_angle})

        # Restaura outputs após um pequeno delay para o linking funcionar
        output_filtered = self.preferences.get("output_filtered", "")
        output_remaining = self.preferences.get("output_remaining", "")
        if output_filtered:
            QTimer.singleShot(100, lambda: self._grid["Filtrado"].set_path(output_filtered))
        if output_remaining:
            QTimer.singleShot(100, lambda: self._grid["Remanescente"].set_path(output_remaining))

        self._loading_prefs = False

        self.logger.info("Preferências carregadas", code="PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["file_path"] = self._current_path
        self.preferences["min_angle"] = self._spin_scan.get("min_angle")
        self.preferences["max_angle"] = self._spin_scan.get("max_angle")
        self.preferences["output_filtered"] = self._grid["Filtrado"].path()
        self.preferences["output_remaining"] = self._grid["Remanescente"].path()
        self.logger.info("Preferências salvas no cache", code="PREFS_SAVED")