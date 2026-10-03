# -*- coding: utf-8 -*-
"""
IcoConverterPlugin — Conversor de imagens para formato ICO
=============================================================
Converte imagens (PNG, JPG, BMP, etc.) para ícones Windows (.ico)
com múltiplos tamanhos (16, 32, 48, 64, 128, 256 pixels).

Usa:
- PIL (Pillow) para processamento de imagens
- SignalManager para progresso e console (Contrato 20)
- HUD Loader para feedback visual durante carregamento/conversão
- FileListView + PreviewPanel para gestão de arquivos
- ExecutionButtons (Contrato 18) para botão CONVERTER
"""

from __future__ import annotations

import os
from typing import Dict, Any

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.enum.DefaultPathCategory import DefaultPathCategory
from core.manager.SignalManager import SignalManager
from core.ui.HudCircularRingsLoader import HudCircularRingsLoader
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.FileListView import FileListView
from resources.widgets.PreviewPanel import PreviewPanel
from resources.widgets.simple.SimpleSelector import SimpleSelector
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.simple.SimpleLabel import SimpleLabel
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.GroupPainel import GroupPainel
from utils.DictManager import IMAGE_EXTENSIONS
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox


ICO_SIZES: Dict[str, Dict[str, Any]] = {
    "16":   {"label": "16 pixels",   "description": "16x16", "default": True},
    "32":   {"label": "32 pixels",   "description": "32x32", "default": True},
    "48":   {"label": "48 pixels",   "description": "48x48", "default": True},
    "64":   {"label": "64 pixels",   "description": "64x64", "default": True},
    "128":  {"label": "128 pixels",  "description": "128x128", "default": True},
    "256":  {"label": "256 pixels",  "description": "256x256", "default": False},
}


class IcoConverterPlugin(BasePlugin):

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.ICO_CONVERTER.value,
            parent=parent,
            sys_prefs=True,
            title="Conversor ICO",
            show_project_path=True,
        )
        self.logger.info("Conversor ICO inicializado", code="ICO_READY")
        self.page.set_badge(self.page.PRONTA)

    def _build_ui(self):
        super()._build_ui()

        # ── HUD Loader (overlay) ──────────────────────────────────────
        self._loader = HudCircularRingsLoader(self)
        self._loader.setGeometry(0, 0, self.width(), self.height())

        # ── Preview ───────────────────────────────────────────────────
        self._preview = PreviewPanel(fixed_size=None)

        # ── FileListView ──────────────────────────────────────────────
        self._file_list = FileListView(
            file_filter=IMAGE_EXTENSIONS,
            accept_dirs=True,
            preview_widget=self._preview,
        )
        self._file_list.files_changed.connect(self._on_files_changed)

        # ── ExecutionButtons ──────────────────────────────────────────
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "convert": {
                "text": "CONVERTER",
                "callback": self._on_convert,
                "type": "primary",
                "description": "Converte todas as imagens para ICO",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Grid: Arquivos + Preview ──────────────────────────────────
        grp_arquivos = GroupPainel("Arquivos")
        grp_arquivos.group_layout.addWidget(self._file_list)
        grp_preview = GroupPainel("Pré-Visualização")
        grp_preview.group_layout.addWidget(self._preview)
        self.main_layout.addWidget(GridGroupPainel(grp_arquivos, grp_preview))

        # ── Tamanhos + Opções lado a lado ─────────────────────────────
        self._grid_sizes = GridCheckBox(ICO_SIZES, num_columns=3)
        grp_tamanhos = GroupPainel("Tamanhos do Ícone")
        grp_tamanhos.group_layout.addWidget(self._grid_sizes)
        grp_tamanhos.group_layout.addWidget(SimpleLabel("Profundidade: 32 bits (RGBA com alpha)"))

        self._grid_opts = GridCheckBox(
            config={
                "subfolders": {
                    "label": "Vasculhar subpastas",
                    "description": "Inclui arquivos de subpastas recursivamente",
                    "default": False,
                },
                "save_in_origin": {
                    "label": "Salvar ICOs na origem",
                    "description": "Ignora pasta de saída",
                    "default": False,
                },
            },
            num_columns=1,
        )
        grp_opts = GroupPainel("Opções")
        grp_opts.group_layout.addWidget(self._grid_opts)
        self.main_layout.addWidget(GridGroupPainel(grp_tamanhos, grp_opts))

        # ── Pasta de Saída ────────────────────────────────────────────
        suggested_ico = ""
        default_output = ""
        if self.sys_preferences:
            root = self.sys_preferences.get("root_folder", "")
            if root:
                suggested_ico = ExplorerUtils.get_default_path(DefaultPathCategory.ICO, root)
                default_output = ExplorerUtils.ensure_directory(suggested_ico)

        # Se já tem output salvo nas preferências, usa ele. Senão, usa o default.
        saved_output = self.preferences.get("output_dir", default_output)

        self._sel_output = SimpleSelector(
            label_text="Pasta de Saída:",
            placeholder="Onde salvar os .ICO...",
            default_path=saved_output,
            browse_mode="directory",
            label_width=120,
            suggested_path=suggested_ico if suggested_ico != saved_output else "",
        )
        grp_saida = GroupPainel("Pasta de Saída")
        grp_saida.group_layout.addWidget(self._sel_output)
        self.main_layout.addWidget(grp_saida)

        # ── Carrega pasta do projeto ──────────────────────────────────
        if self.sys_preferences:
            root = self.sys_preferences.get("root_folder", "")
            if root:
                for folder in [os.path.join(root, d) for d in ("image", "images", "raster")] + [root]:
                    if os.path.isdir(folder):
                        self._loader.show_loader()
                        self._loader.set_progress(30, "Carregando imagens do projeto...")
                        QTimer.singleShot(50, lambda f=folder: self._load_project_folder(f))
                        break

    def _load_project_folder(self, folder: str):
        """Carrega imagens da pasta do projeto com loader."""
        try:
            self._file_list.add_files([folder])
        finally:
            self._loader.hide_loader()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._loader.setGeometry(0, 0, self.width(), self.height())

    # ── Signals ─────────────────────────────────────────────────────

    def _on_files_changed(self, count: int):
        if count > 0:
            self.page.set_badge(self.page.PRONTA)

    # ── Conversão ───────────────────────────────────────────────────

    def _on_convert(self):
        paths = self._file_list.get_ordered_paths()
        if not paths:
            MessageBox.show_warning("Nenhuma imagem na lista.", title="Aviso")
            return

        sizes_checked = self._grid_sizes.checked
        if not sizes_checked:
            MessageBox.show_warning("Selecione ao menos um tamanho.", title="Aviso")
            return

        sizes = sorted(int(k) for k in sizes_checked)
        save_in_origin = self._grid_opts.is_item_checked("save_in_origin")
        output_dir = "" if save_in_origin else self._sel_output.path()

        if not save_in_origin and not output_dir:
            MessageBox.show_warning(
                "Selecione pasta de saída ou marque 'Salvar ICOs na origem'.",
                title="Aviso",
            )
            return

        result = MessageBox.show_question(
            f"Converter {len(paths)} imagem(ns) para ICO?\n"
            f"Tamanhos: {', '.join(str(s) for s in sizes)}px\n"
            f"{'Salvando na origem' if save_in_origin else f'Pasta: {output_dir}'}",
            title="Confirmar",
        )
        if result != MessageBox.YES:
            self.logger.info("Conversão cancelada", code="ICO_CONVERT_CANCELLED")
            return

        self.logger.info("Iniciando conversão", code="ICO_CONVERT_START", count=len(paths), sizes=sizes)
        SignalManager.instance().console_message.emit(f"Convertendo {len(paths)} imagem(ns)...")
        self.page.set_badge(self.page.RUNNING)
        self._btns.set_enabled("convert", False)
        self._loader.set_progress(0, "Convertendo imagens...")
        self._loader.show_loader()
        QTimer.singleShot(0, lambda: self._run_conversion(paths, sizes, output_dir, save_in_origin))

    def _run_conversion(self, paths, sizes, output_dir, save_in_origin):
        from PIL import Image

        total = len(paths)
        ok_count = 0
        err_count = 0

        try:
            for idx, img_path in enumerate(paths, start=1):
                try:
                    out_dir = os.path.dirname(img_path) if save_in_origin else output_dir
                    ExplorerUtils.ensure_directory(out_dir)
                    self._generate_ico(img_path, sizes, out_dir)
                    ok_count += 1
                    self.logger.info(f"ICO gerado: {img_path}", code="ICO_GENERATED")
                except Exception as e:
                    err_count += 1
                    self.logger.error(f"Erro {img_path}", code="ICO_CONVERT_ERR", error=str(e))
                    SignalManager.instance().console_message.emit(
                        f"Erro: {os.path.basename(img_path)} — {e}"
                    )

                pct = (idx / total) * 100.0
                SignalManager.instance().progress_update.emit(pct)
                self._loader.set_progress(pct, f"Convertendo {idx}/{total}...")

            self.logger.info("Conversão finalizada", code="ICO_CONVERT_DONE", ok=ok_count, err=err_count)
            msg = f"Conversão finalizada! {ok_count} ícone(s) gerado(s)."
            if err_count:
                msg += f" {err_count} erro(s)."
            SignalManager.instance().console_message.emit(msg)

            if err_count == 0:
                self.page.set_badge(self.page.PRONTA)
                MessageBox.show_info(f"Sucesso! {ok_count} ícone(s) gerado(s).", title="Concluído")
            else:
                self.page.set_badge(self.page.ERROR)
        except Exception as e:
            self.logger.error("Erro fatal", code="ICO_CONVERT_FATAL", error=str(e))
            SignalManager.instance().console_message.emit(f"Erro fatal: {e}")
            self.page.set_badge(self.page.ERROR)
        finally:
            self._loader.hide_loader()
            self._btns.set_enabled("convert", True)
            SignalManager.instance().progress_update.emit(0.0)
            self.save_prefs()

    @staticmethod
    def _generate_ico(image_path: str, sizes: list[int], output_dir: str) -> str:
        from PIL import Image
        img = Image.open(image_path).convert("RGBA")
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        out_path = os.path.join(output_dir, f"{base_name}.ico")
        img.save(out_path, format="ICO", sizes=[(s, s) for s in sorted(sizes)])
        return out_path

    # ── Preferências ─────────────────────────────────────────────────

    def load_prefs(self):
        states = self.preferences.get("sizes", {})
        if states:
            self._grid_sizes.set_all(states)
        out = self.preferences.get("output_dir", "")
        if out:
            self._sel_output.set_path(out)
        opts = self.preferences.get("options", {})
        if opts:
            self._grid_opts.set_all(opts)

    def save_prefs(self):
        self.preferences["sizes"] = self._grid_sizes.all
        self.preferences["output_dir"] = self._sel_output.path()
        self.preferences["options"] = self._grid_opts.all