# -*- coding: utf-8 -*-
"""
DoclingPlugin — Conversão de documentos para Markdown via Docling
==================================================================
Usa PipelineRunner + DoclingConvertStep para executar a conversão
em background sem travar a UI.
"""

from __future__ import annotations

import os
from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step import DoclingConvertStep
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.ReadOnlyTextBrowser import ReadOnlyTextBrowser
from resources.widgets.grid.GridSelector import GridSelector
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox


DOCUMENT_FILTER = (
    "Documentos suportados (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.webp "
    "*.docx *.pptx *.xlsx *.html *.htm *.txt *.md);;"
    "PDF (*.pdf);;"
    "Imagens (*.png *.jpg *.jpeg *.tiff *.tif *.webp);;"
    "Office (*.docx *.pptx *.xlsx);;"
    "Todos os arquivos (*.*)"
)


class DoclingPlugin(BasePlugin):

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.DOCLING.value,
            parent=parent,
            title="Docling → Markdown",
            buttons_config={
                "converter": {
                    "text": "CONVERTER",
                    "callback": self._on_converter,
                    "type": "primary",
                    "description": "Converte o documento para Markdown",
                },
                "salvar": {
                    "text": "SALVAR MD",
                    "callback": self._on_salvar,
                    "type": "secondary",
                    "description": "Salva o Markdown gerado em arquivo .md",
                },
            },
        )
        self._runner: PipelineRunner | None = None
        self._current_markdown: str = ""
        self.logger.info("DoclingPlugin inicializado", code="DOCLING_READY")
        self.page.set_badge(self.page.PRONTA)

    def _build_ui(self):
        super()._build_ui()

        self._sel_grid = GridSelector(
            specs={
                "Documento": {
                    "file_filter": DOCUMENT_FILTER,
                    "browse_mode": "open_file",
                    "placeholder": "Selecione um documento para converter...",
                },
            },
            title="Arquivo de Entrada",
        )
        self.main_layout.addWidget(self._sel_grid)

        self._grid_col_opts = GridCheckBox(
            config={
                "columnar": {
                    "label": "Separar por colunas (telas / IDE multi-painéis)",
                    "description": "Usa posição horizontal dos blocos de texto para detectar colunas",
                    "default": False,
                },
            },
            num_columns=1,
        )
        self._grid_col_opts.changed.connect(self._on_columnar_changed)

        self._grid_cols = GridDoubleSpinBox(
            config={
                "num_cols": {
                    "label": "Nº colunas",
                    "description": "0 = automático, 2-6 = forçar número",
                    "decimal": 0,
                    "default": 0,
                    "min": 0,
                    "max": 6,
                    "step": 1,
                    "suffix": "",
                },
            },
        )
        self._grid_cols.set_enabled("num_cols", False)

        grp_opts = GroupPainel("Opções de Layout")
        grp_opts.group_layout.addWidget(self._grid_col_opts)
        grp_opts.group_layout.addWidget(self._grid_cols)
        self.main_layout.addWidget(grp_opts)

        self._txt_preview = ReadOnlyTextBrowser(
            placeholder="Markdown gerado aparece aqui...",
        )
        grp_preview = GroupPainel("Pré-Visualização")
        grp_preview.group_layout.addWidget(self._txt_preview)
        self.main_layout.addWidget(grp_preview, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _on_columnar_changed(self):
        enabled = bool(self._grid_col_opts.all.get("columnar", False))
        self._grid_cols.set_enabled("num_cols", enabled)

    def _on_converter(self):
        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Já existe uma conversão em andamento.", title="Aguarde"
            )
            return

        sel = self._sel_grid.get("Documento")
        file_path = sel.path() if sel else ""

        if not file_path or not os.path.isfile(file_path):
            MessageBox.show_warning(
                "Selecione um arquivo válido primeiro.", title="Arquivo"
            )
            return

        columnar = bool(self._grid_col_opts.all.get("columnar", False))
        manual_cols = int(self._grid_cols.values.get("num_cols", 0))

        self._current_markdown = ""
        self._txt_preview.clear_content()
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("converter", False)

        # ── Estima tempo baseado no tamanho do arquivo (MB) ──────────
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)

        # Inicia statistics: ntotal = MB do arquivo
        self.statistics.start(n=0, ntype="mbytes", ntotal=round(size_mb, 2))

        # Pega ETA do _calculate_eta que calcula time_per_item * ntotal
        total_estimate = self.statistics.remaining_time or 30.0

        SignalManager.instance().hud_show.emit({
            "message": "Convertendo documento...",
            "timer": max(total_estimate, 30.0),
            "eta": max(total_estimate, 30.0),
        })

        SignalManager.instance().console_message.emit(
            f"Convertendo: {os.path.basename(file_path)} "
            f"({size_mb:.1f}MB, ETA ~{total_estimate:.0f}s)"
        )

        step = DoclingConvertStep(columnar=columnar, manual_columns=manual_cols)
        runner = PipelineRunner(
            steps=[step],
            input_path=file_path,
            parent=self,
        )
        runner.finished_ok.connect(self._on_done)
        runner.failed.connect(self._on_error)
        runner.finished.connect(self._on_runner_finished)
        self._runner = runner
        runner.start()

    def _on_done(self, context):
        self._current_markdown = context.get_result("markdown", "")
        self._txt_preview.setPlainText(self._current_markdown)
        self.statistics.end()
        SignalManager.instance().console_message.emit("Conversão concluída com sucesso!")
        SignalManager.instance().progress_update.emit(100.0)
        self.page.set_badge(self.page.PRONTA)
        self.logger.info("Markdown gerado", code="CONVERT_DONE")

    def _on_error(self, message: str):
        self.logger.error("Falha na conversão", code="CONVERT_ERR", error=message)
        self.statistics.end()
        SignalManager.instance().console_message.emit(f"Erro na conversão: {message}")
        self._current_markdown = ""
        self._txt_preview.clear_content()
        self.page.set_badge(self.page.ERROR)
        MessageBox.show_critical(f"Erro na conversão:\n{message}", title="Erro")

    def _on_runner_finished(self):
        self._runner = None
        self.page.buttons.set_enabled("converter", True)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    def _on_salvar(self):
        if not self._current_markdown.strip():
            MessageBox.show_warning("Não há Markdown para salvar.", title="Salvar")
            return

        path = ExplorerUtils.save_file(
            "Salvar Markdown",
            file_filter="Markdown (*.md);;Todos (*.*)",
            parent=self,
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._current_markdown)
            SignalManager.instance().console_message.emit(f"Markdown salvo: {path}")
            self.logger.info("Arquivo salvo", code="SAVE_DONE", path=path)
        except Exception as e:
            self.logger.error("Erro ao salvar", code="SAVE_ERR", error=str(e))
            MessageBox.show_critical(f"Erro ao salvar arquivo:\n{e}", title="Erro")

    def load_prefs(self):
        file_path = self.preferences.get("file_path", "")
        if file_path:
            sel = self._sel_grid.get("Documento")
            if sel:
                sel.set_path(file_path)
        states = self.preferences.get("options", {})
        if states:
            self._grid_col_opts.set_all(states)
        cols = self.preferences.get("num_cols", 0)
        self._grid_cols.set_values({"num_cols": cols})
        if cols > 0 or states.get("columnar", False):
            self._grid_cols.set_enabled("num_cols", True)

    def save_prefs(self):
        sel = self._sel_grid.get("Documento")
        file_path = sel.path() if sel else ""
        self.preferences["file_path"] = file_path
        self.preferences["options"] = self._grid_col_opts.all
        self.preferences["num_cols"] = int(self._grid_cols.values.get("num_cols", 0))