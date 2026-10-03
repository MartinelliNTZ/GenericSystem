# -*- coding: utf-8 -*-
"""
LasVectorConverterPlugin — Conversor bidirecional LAS ↔ Pontos Vetoriais
==========================================================================
Converte nuvens de pontos LAS/LAZ em vetores de pontos (SHP, GPKG, GeoJSON, CSV)
e vice-versa.

Usa GridComplexSelector com ComplexSelector para Entrada + Saída com parent linking.
O botão "USAR ORIGEM" é inline no widget — o plugin só tem EXECUTAR.

REGRAS DE ACOPLAMENTO:
  - O plugin NUNCA acessa atributos privados do widget (ex: _user_callbacks).
  - O plugin NUNCA acessa sub-widgets diretamente (ex: entrada.edit).
  - Toda comunicação com GridComplexSelector é via API pública:
      set_input_placeholder, set_input_file_filter, set_on_input_changed,
      suspend_callbacks / resume_callbacks.
"""

from __future__ import annotations

import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step.LasToVectorStep import LasToVectorStep
from core.papeline.step.VectorToLasStep import VectorToLasStep
from core.papeline.step.LasTilerStep import LasTilerStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridRadio import GridRadio
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from utils.las.LasLayerSource import LasLayerSource
from utils.MessageBox import MessageBox
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil
from utils.ProjectUtil import ProjectUtil


class LasVectorConverterPlugin(BasePlugin):
    """
    Plugin para conversão bidirecional LAS/LAZ ↔ Vetor de pontos.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"
    _VECTOR_FILTER = "Vetor (*.shp *.gpkg *.geojson *.csv *.kml)"
    SULFIX = "_converted"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._file_info: dict = {}
        self._runner: PipelineRunner | None = None
        self._mode: str = "file"
        self._direction: str = "las_to_vector"
        super().__init__(
            tool_key=ToolKey.LAS_VECTOR_CONVERTER.value,
            parent=parent,
            title="Conversor LAS ↔ Pontos",
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
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executar conversão",
            },
        })
        self._btns.set_enabled("executar", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Entrada e Saída" ───────────────────────────
        grupo_io = GroupPainel("Entrada e Saída")
        self.main_layout.addWidget(grupo_io)

        # GridComplexSelector com Entrada (input) + Saída (output com parent)
        #
        # O plugin configura o widget com os specs necessários.
        # O widget gerencia todo o linking interno (dynamic_parent, USAR ORIGEM).
        # O plugin só interage via API pública.
        self._grid_io = GridComplexSelector({
            "Entrada": {
                "file_filter": f"{self._LAS_FILTER};;{self._VECTOR_FILTER}",
                "placeholder": "Selecione o arquivo...",
                "mode_type": "input",
                "allow_file": True,
                "allow_folder": True,
                "multiple": True,
                "show_project_button": True,
                "crs_enable": True,  # CRS embutido na entrada
            },
            "Saída": {
                "placeholder": "Arquivo de saída...",
                "mode_type": "output",
                "parent": "Entrada",
                "allow_file": True,
                "allow_folder": True,
                "multiple": False,
                "dynamic_parent": True,
                "show_suggest_button": True,
                "subfolder": "lasvectorconverter",
                "fixed_name": "lasvectorconverted",
            },
        })
        grupo_io.group_layout.addWidget(self._grid_io)

        # Conecta callback para todas as entradas automaticamente
        # O GridComplexSelector gerencia parent-child internamente.
        # O plugin só reage a mudanças na entrada via set_on_input_changed.
        self._grid_io.set_on_input_changed(self._on_input_changed)

        # Info label (só aparece no modo single file)
        self._info_label = GridLabel(
            {
                "tipo": {"label": "Tipo", "value": "—"},
                "n_itens": {"label": "Qtd. Itens", "value": "—"},
                "info": {"label": "Info", "value": "—"},
            },
            columns=1,
        )
        grupo_io.group_layout.addWidget(self._info_label)

        # ── GroupPainel "Configurações" ─────────────────────────────
        grupo_config = GroupPainel("Configurações")
        self.main_layout.addWidget(grupo_config)

        # GridRadio: direção da conversão
        self._radio_direcao = GridRadio(
            {
                "las_to_vector": {
                    "label": "LAS/LAZ → Vetor",
                    "description": "Converte nuvem de pontos para SHP, GPKG, CSV...",
                    "default": True,
                },
                "vector_to_las": {
                    "label": "Vetor → LAS/LAZ",
                    "description": "Converte vetor de pontos para nuvem LAS/LAZ",
                },
            },
            num_columns=2,
        )
        grupo_config.group_layout.addWidget(self._radio_direcao)
        self._radio_direcao.changed.connect(self._on_direction_changed)

        # SimpleComboBox: formato de saída (só para LAS→Vetor)
        self._combo_formato = SimpleComboBox(
            items={
                "gpkg": "GeoPackage (.gpkg)",
                "shp": "Shapefile (.shp)",
                "geojson": "GeoJSON (.geojson)",
                "csv": "CSV (.csv)",
            },
            on_item_changed=self._on_format_changed,
            label="Formato de Saída:",
        )
        grupo_config.group_layout.addWidget(self._combo_formato)

        # Configura sufixo + extensão dinâmica para o output
        # (suffix + extension substituem fixed_name quando em modo origem)
        self._grid_io.set_output_suffix("Saída", self.SULFIX)
        self._grid_io.set_output_extension("Saída", self._combo_formato.current_value)

        # CRS de saída é herdado do CRS da entrada (embutido no selector)
        # O valor padrão é definido via preferences

        # GridDoubleSpinBox: pontos por tile (opcional)
        self._spin_tile = GridDoubleSpinBox(
            {
                "points_per_tile": {
                    "label": "Pontos por Tile (0 = desligado)",
                    "description": "Se > 0, divide o LAS em tiles de N pontos antes de converter",
                    "decimal": 0,
                    "default": 0,
                    "min": 0,
                    "max": 100_000_000,
                    "step": 1_000_000,
                },
            },
        )
        grupo_config.group_layout.addWidget(self._spin_tile)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _aplicar_ui_da_direcao(self, direction: str):
        """
        Aplica a UI conforme a direção da conversão.

        Usa apenas API pública do GridComplexSelector:
          - set_input_file_filter  (substitui entrada.file_filter = ...)
          - set_input_placeholder  (substitui entrada.edit.setPlaceholderText)
          - set_output_extension   (atualiza extensão dinâmica do output)
        """
        if direction == "las_to_vector":
            self._combo_formato.setVisible(True)
            self._spin_tile.setVisible(True)
            self._grid_io.set_input_file_filter("Entrada", self._LAS_FILTER)
            self._grid_io.set_input_placeholder("Entrada", "Selecione o arquivo LAS/LAZ...")
            self._grid_io.set_output_extension("Saída", self._combo_formato.current_value)
        else:
            self._combo_formato.setVisible(False)
            self._spin_tile.setVisible(False)
            self._grid_io.set_input_file_filter("Entrada", self._VECTOR_FILTER)
            self._grid_io.set_input_placeholder("Entrada", "Selecione o arquivo vetor...")
            self._grid_io.set_output_extension("Saída", "las")

    def _on_direction_changed(self, key: str):
        """Disparado quando o usuário altera a direção da conversão."""
        self._direction = key
        self._aplicar_ui_da_direcao(key)

        # Re-valida o path atual com o novo filtro
        if self._current_path:
            self._on_input_changed("Entrada", [self._current_path])

        SignalManager.instance().console_message.emit(
            f"Direção: {'LAS→Vetor' if key == 'las_to_vector' else 'Vetor→LAS'}"
        )

    def _on_format_changed(self, key: str):
        """
        Disparado quando o formato de saída muda.

        SimpleComboBox chama o callback com apenas 1 argumento (o valor interno).
        O texto de exibição pode ser obtido via self._combo_formato.current_text se necessário.
        """
        self.logger.info("Formato alterado", code="FORMAT_CHANGED", formato=key)
        # Atualiza extensão dinâmica no output via API pública
        self._grid_io.set_output_extension("Saída", key)
        # Se o output já foi gerado, regenera com nova extensão
        saida = self._grid_io["Saída"]
        if saida.get_paths():
            self._grid_io.use_origin("Saída")

    def _on_input_changed(self, label: str, paths: list[str]):
        """
        Disparado quando o path da entrada muda.
        Carrega metadados do arquivo e valida extensão.
        """
        if not paths:
            return

        path = paths[0].strip()
        if not path:
            return

        entrada = self._grid_io["Entrada"]
        path_type = entrada.path_type()

        if path_type in ("folder", "folders"):
            if os.path.isdir(path):
                self._current_path = path
                self._file_info = {"path": path, "n_itens": 0, "tipo": "pasta"}
                self._btns.set_enabled("executar", True)
                self.page.set_badge(self.page.PRONTA)
                self._info_label.setVisible(False)
                self.logger.info("Pasta selecionada", code="FOLDER_SELECTED", path=path)
            return

        # file / files
        if not os.path.isfile(path):
            return
        if getattr(self, "_loading_file", False):
            return
        if path == self._current_path:
            return

        self._info_label.setVisible(True)
        self._carregar_arquivo(path)

    def _on_executar(self):
        """Executa a conversão via PipelineRunner em background."""
        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Já existe uma conversão em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo/pasta selecionado.", title="Conversor LAS ↔ Pontos",
            )
            return

        output_path = self._grid_io["Saída"].path()
        if not output_path:
            MessageBox.show_warning(
                "Defina o caminho de saída.\nUse USAR ORIGEM ou preencha manualmente.",
                title="Conversor LAS ↔ Pontos",
            )
            return

        # Determina diretório de saída
        if self._mode == "folder" or os.path.isdir(output_path):
            output_dir = output_path
        else:
            output_dir = os.path.dirname(output_path)

        crs_str = self._grid_io["Entrada"].crs
        crs_code = self._grid_io["Entrada"].crs_widget.crs_code if self._grid_io["Entrada"].crs_widget else 0
        direction = self._direction
        output_format = self._combo_formato.current_value if direction == "las_to_vector" else "las"
        points_per_tile = self._spin_tile.get("points_per_tile")

        # Contagem de itens
        n_total = 0
        n_files = 1

        if self._mode == "folder":
            if direction == "las_to_vector":
                las_files = [f for f in os.listdir(self._current_path) if f.lower().endswith((".las", ".laz"))]
                n_total = len(las_files)
                n_files = n_total
            else:
                vec_files = [f for f in os.listdir(self._current_path) if f.lower().endswith((".shp", ".gpkg", ".csv", ".geojson"))]
                n_total = len(vec_files)
                n_files = n_total
        elif direction == "las_to_vector":
            n_total = LasLayerSource.get_point_count(self._current_path, tool_key=self.tool_key)
            n_files = 1
        else:
            n_total = 1
            n_files = 1

        ntype = ProcessStatisticsUtil.POINTS if direction == "las_to_vector" else ProcessStatisticsUtil.FEATURES
        self.statistics.start(n=0, ntype=ntype, ntotal=n_total)

        SignalManager.instance().console_message.emit(f"{self.statistics.summary}")

        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)

        total_estimate_seconds = max(
            self.statistics.remaining_time, self.statistics.total_time, 30.0,
        )
        n_stages = max(n_files, 1)
        hud_stages = [total_estimate_seconds, n_stages]

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({
            "message": f"Convertendo {'LAS→Vetor' if direction == 'las_to_vector' else 'Vetor→LAS'} ({n_files} arquivo(s))...",
            "stages": hud_stages,
            "eta": total_estimate_seconds,
        })

        dir_label = "LAS→Vetor" if direction == "las_to_vector" else "Vetor→LAS"
        SignalManager.instance().console_message.emit(
            f"Iniciando conversão "
            f"({dir_label}, formato={output_format}, crs={crs_str}, "
            f"{n_files} arquivo(s), ~{n_total:,} {ntype})..."
        )

        self.logger.info(
            "Iniciando conversão", code="CONV_START",
            path=self._current_path, direction=direction,
            output_format=output_format, crs=crs_str,
            mode=self._mode, n_files=n_files, n_total=n_total,
            eta_seconds=round(total_estimate_seconds, 1),
        )

        # Monta steps
        steps = []
        if direction == "las_to_vector":
            if points_per_tile > 0:
                steps.append(LasTilerStep(points_per_part=points_per_tile, advance_input=True))
            steps.append(LasToVectorStep(output_format=output_format, crs_str=crs_str))
        else:
            steps.append(VectorToLasStep(crs_str=crs_str))

        runner = PipelineRunner(
            steps=steps,
            input_path=os.path.dirname(self._current_path) if self._mode == "file" else self._current_path,
            output_path=output_dir,
            files=[self._current_path] if self._mode == "file" else None,
            tool_key=self.tool_key,
            parent=self,
        )
        runner.finished_ok.connect(self._on_done)
        runner.failed.connect(self._on_error)
        runner.finished.connect(self._on_runner_finished)
        self._runner = runner
        runner.start()

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        results = context.results
        n_input = results.get("n_input", 0)
        n_output = results.get("n_output", 0)
        output_files = results.get("output_files", [])
        output_dir = results.get("output_dir", "")
        direction = results.get("direction", self._direction)

        elapsed = self.statistics.end()
        self.logger.info(
            "Tempo registrado", code="STATS_RECORDED",
            elapsed_s=round(elapsed, 3), usages=self.statistics.usages,
        )

        dir_label = "LAS→Vetor" if direction == "las_to_vector" else "Vetor→LAS"
        n_arquivos = len(output_files)

        self.success_message(
            output_path=output_dir, label="Pasta de Saída",
            summary=f"Conversão {dir_label} concluída!",
            n_input=n_input, n_output=n_output, n_arquivos=n_arquivos,
        )

        self.logger.info(
            "Conversão concluída", code="CONV_DONE",
            direction=direction, n_input=n_input, n_output=n_output,
            n_arquivos=n_arquivos, output_dir=output_dir,
        )

        msg = (
            f"Conversão concluída!\n\n"
            f"Direção: {dir_label}\n"
            f"Pontos de entrada: {n_input:,}\n"
            f"Pontos de saída: {n_output:,}\n"
            f"Arquivos gerados: {n_arquivos}\n\n"
        )
        if output_dir:
            msg += f"Pasta de saída:\n{output_dir}"

        MessageBox.show_info(msg, title="Conversor LAS ↔ Pontos")

    def _on_error(self, message: str):
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(f"ERRO: {message}")
        self.logger.error("Erro na conversão", code="CONV_ERR", error=message)
        MessageBox.show_error(f"Erro:\n{message}", title="Conversor LAS ↔ Pontos")

    def _on_runner_finished(self):
        self._runner = None
        self._btns.set_all_enabled(True)
        self._btns.set_enabled("executar", bool(self._current_path))
        self.page.set_badge(self.page.PRONTA)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_arquivo(self, path: str):
        if getattr(self, "_loading_file", False):
            return
        self._loading_file = True
        self.logger.info("Carregando arquivo", code="FILE_LOAD", path=path)

        try:
            ext = os.path.splitext(path)[1].lower()
            self._current_path = path

            if ext in (".las", ".laz"):
                info = LasLayerSource.get_info(path, tool_key=self.tool_key)
                if info.get("error"):
                    raise RuntimeError(info["error"])
                n_pontos = info["point_count"]
                has_rgb = info["has_rgb"]
                self._file_info = {"path": path, "n_itens": n_pontos, "tipo": "LAS/LAZ", "has_rgb": has_rgb}
                self._info_label.set("tipo", "LAS/LAZ")
                self._info_label.set("n_itens", f"{n_pontos:,} pontos")
                self._info_label.set("info", f"RGB: {'Sim' if has_rgb else 'Não'}")
                self._radio_direcao.set_selected("las_to_vector")

            elif ext in (".shp", ".gpkg", ".csv", ".geojson", ".kml"):
                from utils.vector.VectorLayerSource import VectorLayerSource
                data = VectorLayerSource.read(path, tool_key=self.tool_key)
                n_features = len(data)
                self._file_info = {"path": path, "n_itens": n_features, "tipo": ext.upper()}
                self._info_label.set("tipo", ext.upper())
                self._info_label.set("n_itens", f"{n_features:,} feições")
                self._info_label.set("info", f"Driver: {VectorLayerSource.get_driver_name(path)}")
                self._radio_direcao.set_selected("vector_to_las")

            else:
                raise ValueError(f"Extensão não suportada: {ext}")

            self._btns.set_enabled("executar", True)
            self.page.set_badge(self.page.PRONTA)

        except Exception as e:
            self.logger.error("Erro ao carregar", code="FILE_LOAD_ERR", error=str(e))
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(f"Erro ao carregar:\n{str(e)}", title="Conversor LAS ↔ Pontos", detail=traceback.format_exc())
        finally:
            self._loading_file = False

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """
        Carrega preferências salvas.

        Usa a API pública suspend_callbacks/resume_callbacks para evitar
        que set_path dispare re-avaliação prematura.
        """
        self.logger.info("Carregando preferências", code="PREFS_LOAD")

        # Suspende callbacks para restaurar paths sem disparar re-avaliação
        # (set_path dispara on_path_change internamente, o que causaria
        #  re-load prematuro de metadados)
        saved_callbacks = self._grid_io.suspend_callbacks()

        try:
            last_mode = self.preferences.get("mode", "file")
            file_path = self.preferences.get("file_path", "")
            folder_path = self.preferences.get("folder_path", "")
            direction = self.preferences.get("direction", "las_to_vector")
            output_format = self.preferences.get("output_format", "gpkg")
            crs = self.preferences.get("crs", 31982)
            output_path = self.preferences.get("output_path", "")
            points_per_tile = self.preferences.get("points_per_tile", 0)

            self._mode = last_mode
            self._info_label.setVisible(last_mode == "file")

            if direction != self._direction:
                self._direction = direction
                self._radio_direcao.set_selected(direction)
                self._aplicar_ui_da_direcao(direction)

            entrada = self._grid_io["Entrada"]

            if last_mode == "folder" and folder_path:
                self._current_path = folder_path
                self._file_info = {"path": folder_path, "n_itens": 0, "tipo": "pasta"}
                entrada.set_path(folder_path)
                self._btns.set_enabled("executar", True)
            elif last_mode == "file" and file_path:
                self._current_path = file_path
                entrada.set_path(file_path)
                self._btns.set_enabled("executar", True)

            if output_path:
                self._grid_io["Saída"].set_path(output_path)
            self._combo_formato.current_value = output_format
            entrada_crs = self._grid_io["Entrada"].crs_widget
            if entrada_crs:
                entrada_crs.set_crs(f"EPSG:{crs}")
            self._spin_tile.set_values({"points_per_tile": points_per_tile})
        finally:
            # Restaura callbacks originais
            self._grid_io.resume_callbacks(saved_callbacks)

        self.logger.info("Preferências carregadas", code="PREFS_LOADED")

    def save_prefs(self) -> None:
        if self._mode == "file":
            self.preferences["file_path"] = self._current_path
        elif self._mode == "folder":
            self.preferences["folder_path"] = self._current_path

        self.preferences["mode"] = self._mode
        self.preferences["direction"] = self._direction
        self.preferences["output_format"] = self._combo_formato.current_value
        entrada_crs = self._grid_io["Entrada"].crs_widget
        self.preferences["crs"] = entrada_crs.crs_code if entrada_crs else 0
        self.preferences["output_path"] = self._grid_io["Saída"].path()
        self.preferences["points_per_tile"] = self._spin_tile.get("points_per_tile")
        self.logger.info("Preferências salvas no cache", code="PREFS_SAVED")