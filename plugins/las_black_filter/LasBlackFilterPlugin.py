# -*- coding: utf-8 -*-
"""
LasBlackFilterPlugin — Filtro de pontos pretos em nuvens LAS/LAZ
==================================================================
Remove pontos onde R, G e B estão todos abaixo de um limiar configurável.
Gera novo arquivo com sufixo _filtrado.las/.laz sem alterar o original.
Opção de salvar os pontos pretos removidos em arquivo separado.

Modos de operação:
  - "file"   (padrão): seleciona 1 arquivo LAS, mostra info, executa filtro
  - "folder": seleciona pasta, processa todos os LAS da pasta em lote

Fluxo:
  - SimpleSelector de entrada com mode_selector (Arquivo/Pasta)
  - SimpleSelectors de saída com botão 📂 para pasta do projeto
  - ExecutionButtons: USAR ORIGEM + EXECUTAR
  - PipelineRunner + LasBlackFilterStep para execução em background
"""

from __future__ import annotations

import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step import LasBlackFilterStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.grid.GridSelector import GridSelector
from resources.widgets.simple.SimpleSelector import SimpleSelector
from utils.ExplorerUtils import ExplorerUtils
from utils.las.LasLayerSource import LasLayerSource
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil


class LasBlackFilterPlugin(BasePlugin):
    """
    Plugin para filtrar pontos pretos de arquivos LAS/LAZ.
    Suporta modo arquivo único ou pasta (lote).
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        # -- Inicializa atributos ANTES de super().__init__() --
        # pois BasePlugin.__init__() chama load_prefs() que acessa estes atributos
        self._current_path: str = ""
        self._las_info: dict = {}
        self._runner: PipelineRunner | None = None
        self._mode: str = "file"  # "file" ou "folder"
        super().__init__(
            tool_key=ToolKey.LAS_BLACK_FILTER.value,
            parent=parent,
            title="Filtro Pontos Pretos",
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
                "description": "Salvar na pasta do arquivo/pasta LAS original",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executar filtro de pontos pretos",
            },
        })
        self._btns.set_enabled("executar", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Entrada" ───────────────────────────────────
        grupo_entrada = GroupPainel("Entrada")
        self.main_layout.addWidget(grupo_entrada)

        # SimpleSelector com mode_selector (Arquivo / Pasta)
        self._sel_entrada = SimpleSelector(
            label_text="LAS/LAZ de Entrada",
            file_filter=self._LAS_FILTER,
            browse_mode="open_file",
            placeholder="Selecione o arquivo LAS/LAZ...",
            mode_selector={
                "file": {
                    "label": "Arquivo",
                    "description": "Processar 1 arquivo LAS",
                    "default": True,
                },
                "folder": {
                    "label": "Pasta",
                    "description": "Processar todos os LAS de uma pasta",
                },
            },
        )
        grupo_entrada.group_layout.addWidget(self._sel_entrada)

        # Conecta mudança de path e modo
        self._sel_entrada.on_path_change = self._on_input_path_changed
        self._sel_entrada.on_mode_change = self._on_mode_changed

        # Info label (só aparece no modo file)
        self._info_label = GridLabel(
            {
                "pontos": {"label": "Total de Pontos", "value": "—"},
                "has_rgb": {"label": "Possui RGB", "value": "—"},
                "bbox": {"label": "Bounding Box", "value": "—"},
            },
            columns=1,
        )
        grupo_entrada.group_layout.addWidget(self._info_label)

        # ── GroupPainel "Configurações" ─────────────────────────────
        grupo_config = GroupPainel("Configurações")
        self.main_layout.addWidget(grupo_config)

        self._spin_limiar = GridDoubleSpinBox(
            {
                "limiar": {
                    "label": "Limiar de Preto",
                    "description": "Valor maximo de R/G/B para considerar preto (0–255)",
                    "decimal": 0,
                    "default": 0,
                    "min": 0,
                    "max": 255,
                    "step": 1,
                },
            },
        )
        grupo_config.group_layout.addWidget(self._spin_limiar)

        self._ckb_salvar_pretos = GridCheckBox(
            {
                "salvar_pretos": {
                    "label": "Salvar pontos pretos removidos",
                    "description": "Gera arquivo separado com os pontos filtrados",
                    "default": False,
                },
            },
            num_columns=1,
        )
        grupo_config.group_layout.addWidget(self._ckb_salvar_pretos)

        # ── GroupPainel "Saída" ─────────────────────────────────────
        grupo_saida = GroupPainel("Saída")
        self.main_layout.addWidget(grupo_saida)

        # Modo file: dois SimpleSelectors (filtrado + pretos)
        # Modo folder: um SimpleSelector para pasta de saída
        self._sel_limpo = SimpleSelector(
            label_text="LAS Filtrado",
            file_filter=self._LAS_FILTER,
            browse_mode="save_file",
            placeholder="Caminho do LAS filtrado...",
        )
        grupo_saida.group_layout.addWidget(self._sel_limpo)

        self._sel_pretos = SimpleSelector(
            label_text="LAS Pretos",
            file_filter=self._LAS_FILTER,
            browse_mode="save_file",
            placeholder="Caminho do LAS de pontos pretos...",
        )
        grupo_saida.group_layout.addWidget(self._sel_pretos)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _aplicar_ui_do_modo(self, mode_key: str):
        """Aplica a UI visual conforme o modo (sem alterar _current_path)."""
        if mode_key == "folder":
            self._info_label.setVisible(False)
            self._sel_entrada.edit.setPlaceholderText("Selecione uma pasta com LAS...")
            self._sel_limpo.label.setText("Pasta de Saída")
            self._sel_limpo._browse_mode = "directory"
            self._sel_limpo.edit.setPlaceholderText("Pasta para salvar resultados...")
            self._sel_pretos.setVisible(False)
        else:
            self._info_label.setVisible(True)
            self._sel_entrada.edit.setPlaceholderText("Selecione o arquivo LAS/LAZ...")
            self._sel_limpo.label.setText("LAS Filtrado")
            self._sel_limpo._browse_mode = "save_file"
            self._sel_limpo.edit.setPlaceholderText("Caminho do LAS filtrado...")
            self._sel_pretos.setVisible(True)

    def _on_mode_changed(self, mode_key: str):
        """Disparado quando o usuário alterna entre Arquivo/Pasta."""
        self._mode = mode_key

        # Se está carregando preferências, não limpa nem restaura nada
        if getattr(self, "_loading_prefs", False):
            return

        self._current_path = ""
        self._las_info = {}

        self._aplicar_ui_do_modo(mode_key)

        # Limpa campos
        self._sel_entrada.set_path("")
        self._sel_limpo.set_path("")
        self._sel_pretos.set_path("")

        # Restaura path salvo nas preferências para o modo selecionado.
        # O set_path() já dispara textChanged → _on_input_path_changed automaticamente.
        if mode_key == "folder":
            saved_folder = self.preferences.get("folder_path", "")
            if saved_folder:
                self._sel_entrada.set_path(saved_folder)
        else:
            saved_file = self.preferences.get("file_path", "")
            self.logger.info(f"Modo alterado, restaurando arquivo salvo nas preferências. Path: {saved_file}")
            if saved_file:
                self._sel_entrada.set_path(saved_file)

        self._btns.set_enabled("executar", False)
        self.page.set_badge(self.page.PRONTA)

        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] Modo alterado para: {'Pasta' if mode_key == 'folder' else 'Arquivo'}"
        )

    def _on_input_path_changed(self, text: str):
        """
        Disparado quando o texto do selector de entrada muda.
        No modo file: carrega metadados do LAS.
        No modo folder: apenas valida se é uma pasta válida.
        """
        path = text.strip()
        if not path:
            return

        if self._mode == "folder":
            # Modo pasta: valida se é uma pasta com arquivos LAS
            if os.path.isdir(path):
                self._current_path = path
                self._las_info = {"path": path, "n_pontos": 0, "has_rgb": True}
                self._btns.set_enabled("executar", True)
                self.page.set_badge(self.page.PRONTA)
                self.logger.info(
                    "Pasta selecionada",
                    code="FOLDER_SELECTED",
                    path=path,
                )
            return

        # Modo file: valida arquivo LAS
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz") or not os.path.isfile(path):
            return
        if getattr(self, "_loading_las", False):
            return
        if path == self._current_path:
            return
        self._carregar_las(path)

    def _on_usar_origem(self):
        """
        Preenche caminhos de saída na pasta do arquivo/pasta LAS original.
        """
        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo/pasta LAS selecionado.\nSelecione primeiro.",
                title="Filtro Pontos Pretos",
            )
            return

        if self._mode == "folder":
            # Modo pasta: saída = pasta de origem + /lasblackfilter
            output_dir = os.path.join(self._current_path, "lasblackfilter")
            self._sel_limpo.set_path(output_dir)
            self._btns.set_enabled("executar", True)
            SignalManager.instance().console_message.emit(
                f"[LasBlackFilter] Destino: {output_dir}"
            )
            return

        # Modo file: comportamento original
        caminhos = self._resolver_caminhos_saida(modo="origem")
        self._sel_limpo.set_path(caminhos["limpo"])
        self._sel_pretos.set_path(caminhos["pretos"])
        self._atualizar_suggested_path(modo="origem")
        self._btns.set_enabled("executar", True)
        SignalManager.instance().console_message.emit(
            "[LasBlackFilter] Destino: pasta do LAS original"
        )

    def _on_executar(self):
        """Executa o filtro de pontos pretos via PipelineRunner em background."""
        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Já existe um filtro em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo/pasta LAS selecionado.", title="Filtro Pontos Pretos",
            )
            return

        if self._mode == "file" and not self._las_info.get("has_rgb", False):
            MessageBox.show_warning(
                "O arquivo LAS não possui bandas RGB.\n"
                "Não é possível filtrar pontos pretos.",
                title="Filtro Pontos Pretos",
            )
            return

        limiar = self._spin_limiar.get("limiar")
        salvar_pretos = self._ckb_salvar_pretos.checked.get("salvar_pretos", False)

        if self._mode == "folder":
            # Modo pasta: saída é uma pasta
            output_dir = self._sel_limpo.path()
            if not output_dir:
                MessageBox.show_warning(
                    "Defina a pasta de saída.\nUse USAR ORIGEM ou preencha manualmente.",
                    title="Filtro Pontos Pretos",
                )
                return

            # Conta total de LAS na pasta para o statistics
            las_files = [
                f for f in os.listdir(self._current_path)
                if f.lower().endswith((".las", ".laz"))
            ]
            n_total = len(las_files)

            self.statistics.start(
                n=0,
                ntype=ProcessStatisticsUtil.POINTS,
                ntotal=n_total,
            )

            SignalManager.instance().console_message.emit(
                f"[LasBlackFilter] {self.statistics.summary}"
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
                "message": "Filtrando pontos pretos (pasta)...",
                "stages": [total_estimate_seconds, 4],
            })
            SignalManager.instance().console_message.emit(
                f"[LasBlackFilter] Iniciando filtro em pasta (limiar={limiar})..."
            )

            self.logger.info(
                "Iniciando filtro em pasta",
                code="FILTER_START",
                path=self._current_path,
                limiar=limiar,
                salvar_pretos=salvar_pretos,
                output_dir=output_dir,
                n_arquivos=n_total,
            )

            # Cria step com input_path = pasta
            step = LasBlackFilterStep(
                threshold=limiar,
                save_black_points=salvar_pretos,
                input_path=self._current_path,
            )
            runner = PipelineRunner(
                steps=[step],
                input_path=self._current_path,
                output_path=output_dir,
                tool_key=self.tool_key,
                parent=self,
            )
            runner.finished_ok.connect(self._on_done_folder)
            runner.failed.connect(self._on_error)
            runner.finished.connect(self._on_runner_finished)
            self._runner = runner
            runner.start()
            return

        # ── Modo file (comportamento original) ──────────────────────
        output_limpo = self._sel_limpo.path()
        if not output_limpo:
            MessageBox.show_warning(
                "Defina o caminho do arquivo de saída (LAS Filtrado).\n"
                "Use USAR ORIGEM ou preencha manualmente.",
                title="Filtro Pontos Pretos",
            )
            return

        output_pretos = self._sel_pretos.path() if salvar_pretos else ""

        n_total = LasLayerSource.get_point_count(
            self._current_path, tool_key=self.tool_key
        )

        self.statistics.start(
            n=0,
            ntype=ProcessStatisticsUtil.POINTS,
            ntotal=n_total,
        )

        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] {self.statistics.summary}"
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
            "message": "Filtrando pontos pretos...",
            "stages": [total_estimate_seconds, 4],
        })
        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] Iniciando filtro (limiar={limiar})..."
        )

        self.logger.info(
            "Iniciando filtro",
            code="FILTER_START",
            path=self._current_path,
            limiar=limiar,
            salvar_pretos=salvar_pretos,
            output_limpo=output_limpo,
            n_total=n_total,
            eta=self.statistics.eta_str,
            total_estimate_seconds=round(total_estimate_seconds, 1),
        )

        step = LasBlackFilterStep(
            threshold=limiar,
            save_black_points=salvar_pretos,
        )
        runner = PipelineRunner(
            steps=[step],
            input_path=os.path.dirname(self._current_path),
            output_path=os.path.dirname(self._current_path),
            files=[self._current_path],  # Processa APENAS o arquivo selecionado
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
        """Callback de sucesso da pipeline (modo file)."""
        results = context.results
        n_removidos = results.get("n_removed", 0)
        n_mantidos = results.get("n_kept", 0)
        n_total = results.get("n_total", 0)
        n_pretos = results.get("n_black", 0)
        output_clean_list = results.get("output_clean", [])
        output_black_list = results.get("output_black", [])
        output_limpo = output_clean_list[0] if output_clean_list else ""
        output_pretos = output_black_list[0] if output_black_list else ""

        elapsed = self.statistics.end()
        self.logger.info(
            "Tempo de processamento registrado",
            code="STATS_RECORDED",
            elapsed_s=round(elapsed, 3),
            usages=self.statistics.usages,
        )

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] Filtro concluído! "
            f"{n_removidos:,} pontos removidos, "
            f"{n_mantidos:,} mantidos."
        )

        self.logger.info(
            "Filtro concluído com sucesso",
            code="FILTER_DONE",
            removidos=n_removidos,
            restantes=n_mantidos,
            total=n_total,
            output_limpo=output_limpo,
            output_pretos=output_pretos or None,
        )

        msg = (
            f"Filtro concluído!\n\n"
            f"Total de pontos: {n_total:,}\n"
            f"Pontos removidos: {n_removidos:,}\n"
            f"Pontos mantidos: {n_mantidos:,}\n\n"
            f"LAS filtrado salvo em:\n{output_limpo}"
        )
        if n_pretos > 0 and output_pretos:
            msg += f"\n\nPontos pretos salvos em:\n{output_pretos}"

        MessageBox.show_info(msg, title="Filtro Pontos Pretos")

    def _on_done_folder(self, context):
        """Callback de sucesso da pipeline (modo pasta)."""
        results = context.results
        n_removidos = results.get("n_removed", 0)
        n_mantidos = results.get("n_kept", 0)
        n_total = results.get("n_total", 0)
        n_pretos = results.get("n_black", 0)
        output_clean_list = results.get("output_clean", [])
        output_black_list = results.get("output_black", [])

        elapsed = self.statistics.end()
        self.logger.info(
            "Tempo de processamento registrado",
            code="STATS_RECORDED",
            elapsed_s=round(elapsed, 3),
            usages=self.statistics.usages,
        )

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] Filtro em pasta concluído! "
            f"{len(output_clean_list)} arquivos processados, "
            f"{n_removidos:,} pontos removidos."
        )

        self.logger.info(
            "Filtro em pasta concluído com sucesso",
            code="FILTER_DONE",
            removidos=n_removidos,
            restantes=n_mantidos,
            total=n_total,
            arquivos=len(output_clean_list),
        )

        msg = (
            f"Filtro em pasta concluído!\n\n"
            f"Arquivos processados: {len(output_clean_list)}\n"
            f"Total de pontos: {n_total:,}\n"
            f"Pontos removidos: {n_removidos:,}\n"
            f"Pontos mantidos: {n_mantidos:,}\n\n"
            f"Resultados salvos em:\n{os.path.dirname(output_clean_list[0]) if output_clean_list else '—'}"
        )
        if n_pretos > 0 and output_black_list:
            msg += f"\n\nPontos pretos salvos em:\n{os.path.dirname(output_black_list[0])}"

        MessageBox.show_info(msg, title="Filtro Pontos Pretos")

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] ERRO: {message}"
        )
        self.logger.error(
            "Erro no filtro de pontos pretos",
            code="FILTER_ERR",
            error=message,
            path=self._current_path,
        )
        MessageBox.show_error(
            f"Erro durante o filtro:\n{message}",
            title="Filtro Pontos Pretos",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
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
        """Carrega metadados do LAS e atualiza a UI."""
        if getattr(self, "_loading_las", False):
            return
        self._loading_las = True

        self.logger.info("Carregando LAS", code="LAS_LOAD", path=path)

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

            # Atualiza UI
            self._info_label.set("pontos", f"{n_pontos:,}")
            self._info_label.set("has_rgb", "Sim" if has_rgb else "Não")

            bbox = LasLayerSource.get_bounding_box(path, tool_key=self.tool_key)
            if bbox:
                self._info_label.set(
                    "bbox",
                    f"X[{bbox['x_min']:.1f}, {bbox['x_max']:.1f}] "
                    f"Y[{bbox['y_min']:.1f}, {bbox['y_max']:.1f}]",
                )
            else:
                self._info_label.set("bbox", "—")

            self._btns.set_enabled("executar", has_rgb)
            self.page.set_badge(self.page.PRONTA if has_rgb else self.page.ERROR)

            if not has_rgb:
                SignalManager.instance().console_message.emit(
                    "[LasBlackFilter] AVISO: LAS sem bandas RGB"
                )
                MessageBox.show_warning(
                    "O arquivo LAS não possui bandas RGB.\n"
                    "O filtro de pontos pretos não será executado.",
                    title="Filtro Pontos Pretos",
                )

            self.logger.info(
                "LAS carregado",
                code="LAS_LOADED",
                path=path,
                points=n_pontos,
                has_rgb=has_rgb,
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
                title="Filtro Pontos Pretos",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False

    def _resolver_caminhos_saida(self, modo: str) -> dict[str, str]:
        """
        Resolve os caminhos de saída para os arquivos filtrados (modo file).

        Args:
            modo: "origem" → pasta do LAS original
                  "projeto" → root_folder/las/black_points_filter/

        Returns:
            Dict com "limpo" e "pretos" (caminhos completos).
        """
        if not self._current_path:
            return {"limpo": "", "pretos": ""}

        dir_origem = os.path.dirname(self._current_path)
        basename = os.path.splitext(os.path.basename(self._current_path))[0]
        ext = os.path.splitext(self._current_path)[1].lower()

        if modo == "projeto":
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            root_folder = sys_prefs.get("root_folder", "")
            if root_folder and os.path.isdir(root_folder):
                base_dir = os.path.join(root_folder, "las", "black_points_filter")
            else:
                base_dir = dir_origem
        else:
            base_dir = dir_origem

        limpo = os.path.join(base_dir, f"{basename}_filtrado{ext}")
        pretos = os.path.join(base_dir, f"{basename}_pretos{ext}")

        return {"limpo": limpo, "pretos": pretos}

    def _atualizar_suggested_path(self, modo: str):
        """
        Atualiza o botao 📂 dos selectors de saida com o PATH RELATIVO.

        modo "projeto" → "las/black_points_filter"
        modo "origem"  → caminho vazio (esconde o botão)
        """
        if modo == "projeto":
            rel_path = "las/black_points_filter"
            self._sel_limpo.set_suggested_path(rel_path)
            self._sel_pretos.set_suggested_path(rel_path)
            SignalManager.instance().console_message.emit(
                f"[LasBlackFilter] Botão 📂 configurado para: {rel_path}"
            )
        else:
            self._sel_limpo.set_suggested_path("")
            self._sel_pretos.set_suggested_path("")

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferências", code="PREFS_LOAD")

        # Desconecta on_mode_change TEMPORARIAMENTE para evitar que o sinal
        # assíncrono do GridRadio dispare _on_mode_changed depois do load
        saved_callback = self._sel_entrada.on_mode_change
        self._sel_entrada.on_mode_change = None

        last_mode = self.preferences.get("mode", "file")
        file_path = self.preferences.get("file_path", "")
        folder_path = self.preferences.get("folder_path", "")
        limiar = self.preferences.get("limiar", 0)
        salvar_pretos = self.preferences.get("salvar_pretos", False)
        last_output_limpo = self.preferences.get("output_limpo", "")
        last_output_pretos = self.preferences.get("output_pretos", "")

        # Aplica UI visual primeiro
        self._aplicar_ui_do_modo(last_mode)

        # Restaura modo (sem callback)
        if last_mode != self._mode:
            self._mode = last_mode
            self._sel_entrada.set_mode(last_mode)

        # Carrega o path correto conforme o modo
        if last_mode == "folder" and folder_path:
            self._current_path = folder_path
            self._las_info = {"path": folder_path, "n_pontos": 0, "has_rgb": True}
            self._sel_entrada.set_path(folder_path)
            self._btns.set_enabled("executar", True)
        elif last_mode == "file" and file_path:
            # Usa set_path() para que o SimpleSelector exiba o path visualmente.
            # O signal textChanged → _on_input_path_changed → _carregar_las()
            # será disparado automaticamente, carregando os metadados.
            self._sel_entrada.set_path(file_path)

        # Reconecta callback
        self._sel_entrada.on_mode_change = saved_callback

        # Restaura outputs salvos
        if last_output_limpo:
            self._sel_limpo.set_path(last_output_limpo)
        if last_output_pretos:
            self._sel_pretos.set_path(last_output_pretos)

        # Atualiza suggested_path
        if last_output_limpo and "black_points_filter" in last_output_limpo:
            self._atualizar_suggested_path(modo="projeto")
        elif self._current_path:
            self._atualizar_suggested_path(modo="origem")

        # Habilita executar se tem LAS carregado com RGB
        if self._current_path and self._las_info.get("has_rgb", False):
            self._btns.set_enabled("executar", True)

        self._spin_limiar.set_values({"limiar": limiar})
        self._ckb_salvar_pretos.set_all({"salvar_pretos": salvar_pretos})
        self.logger.info("Preferências carregadas", code="PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        # Salva path separado por modo
        if self._mode == "file":
            self.preferences["file_path"] = self._current_path
        elif self._mode == "folder":
            self.preferences["folder_path"] = self._current_path

        self.preferences["mode"] = self._mode
        self.preferences["limiar"] = self._spin_limiar.get("limiar")
        self.preferences["salvar_pretos"] = self._ckb_salvar_pretos.checked.get(
            "salvar_pretos", False
        )
        self.preferences["output_limpo"] = self._sel_limpo.path()
        self.preferences["output_pretos"] = self._sel_pretos.path()
        self.logger.info("Preferências salvas no cache", code="PREFS_SAVED")
