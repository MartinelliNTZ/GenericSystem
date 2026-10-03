# -*- coding: utf-8 -*-
"""
ImageConverterPlugin — Conversor universal de imagens
=======================================================
Converte imagens entre formatos (PNG, JPG, WEBP, ICO, BMP, GIF, TIFF)
com suporte a redimensionamento, qualidade para formatos lossy
e ICO multi-tamanho.

Usa:
- PIL (Pillow) para processamento de imagens
- SignalManager para progresso, console e HUD (Contrato 20)
- FileListView + PreviewPanel para gestão de arquivos
- ExecutionButtons (Contrato 18) para botão CONVERTER
- SimpleComboBox para seleção de formato de saída
- GridSlider para qualidade (genérico, reutilizável)
- GridDoubleSpinBox para dimensões de redimensionamento
- GridCheckBox para tamanhos ICO e opções
- GridComplexSelector para pasta de saída
"""

from __future__ import annotations

import os
from typing import Dict, Any

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.FileListView import FileListView
from resources.widgets.PreviewPanel import PreviewPanel
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridSlider import GridSlider
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SectionPanel import SectionPanel
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from utils.DictManager import IMAGE_EXTENSIONS, OUTPUT_IMAGE_FORMATS, ICO_SIZES
from utils.MessageBox import MessageBox


class ImageConverterPlugin(BasePlugin):

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.IMAGE_CONVERTER.value,
            parent=parent,
            sys_prefs=True,
            title="Conversor de Imagens",
            show_project_path=False,
            buttons_config={
                "convert": {
                    "text": "CONVERTER",
                    "callback": self._on_convert,
                    "type": "primary",
                    "description": "Converte todas as imagens para o formato selecionado",
                },
            },
        )
        self.logger.info("Conversor de Imagens inicializado", code="IMG_CONV_READY")
        self.page.set_badge(self.page.PRONTA)

    def _build_ui(self):
        super()._build_ui()

        # ── Preview ───────────────────────────────────────────────────
        self._preview = PreviewPanel()

        # ── FileListView ──────────────────────────────────────────────
        self._file_list = FileListView(
            file_filter=IMAGE_EXTENSIONS,
            accept_dirs=True,
            preview_widget=self._preview,
        )
        self._file_list.files_changed.connect(self._on_files_changed)

        # ── Grid: Arquivos + Preview (stretch=2 para mais altura) ─────
        grp_arquivos = GroupPainel("Arquivos")
        grp_arquivos.group_layout.addWidget(self._file_list)
        grp_preview = GroupPainel("Pré-Visualização")
        grp_preview.group_layout.addWidget(self._preview)
        grid_files = GridGroupPainel(grp_arquivos, grp_preview)
        self.main_layout.addWidget(grid_files, 2)

        # ── Formato de Saída + Pasta de Saída ─────────────────────────
        format_items = {
            key: info["label"]
            for key, info in OUTPUT_IMAGE_FORMATS.items()
        }
        self._combo_format = SimpleComboBox(
            items=format_items,
            on_item_changed=self._on_format_changed,
            label="Formato de Saída:",
        )

        self._sel_output = GridComplexSelector({
            "Pasta de Saída": {
                "mode_type": "output",
                "allow_file": False,
                "allow_folder": True,
                "multiple": False,
                "subfolder": "ImageConverter",
                "show_suggest_button": True,
            },
        })

        grp_formato = GroupPainel("Formato e Destino")
        grp_formato.group_layout.addWidget(self._combo_format)
        grp_formato.group_layout.addWidget(self._sel_output)

        # ── Configurações (dinâmico) ──────────────────────────────────
        self._slider_quality = GridSlider(
            config={
                "quality": {
                    "label": "Qualidade:",
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "suffix": "%",
                    "description": "Qualidade para formatos lossy (JPEG, WEBP)",
                },
            },
        )
        self._panel_quality = SectionPanel(object_name="panel_quality")
        self._panel_quality.section_layout.addWidget(self._slider_quality)
        self._panel_quality.setVisible(False)

        self._grid_ico_sizes = GridCheckBox(ICO_SIZES, num_columns=3)
        self._panel_ico = SectionPanel(object_name="panel_ico")
        self._panel_ico.section_layout.addWidget(self._grid_ico_sizes)
        self._panel_ico.setVisible(False)

        self._spin_resize = GridDoubleSpinBox(
            config={
                "width": {
                    "label": "Largura:",
                    "decimal": 0,
                    "default": 1920,
                    "min": 1,
                    "max": 99999,
                    "step": 1,
                    "suffix": "px",
                },
                "height": {
                    "label": "Altura:",
                    "decimal": 0,
                    "default": 1080,
                    "min": 1,
                    "max": 99999,
                    "step": 1,
                    "suffix": "px",
                },
            },
            columns=2,
        )
        self._spin_resize.set_enabled("width", False)
        self._spin_resize.set_enabled("height", False)

        self._grid_opts = GridCheckBox(
            config={
                "resize_enabled": {
                    "label": "Redimensionar",
                    "description": "Habilita redimensionamento da imagem",
                    "default": False,
                },
                "keep_aspect": {
                    "label": "Manter proporção",
                    "description": "Mantém a proporção original ao redimensionar",
                    "default": True,
                },
                "subfolders": {
                    "label": "Vasculhar subpastas",
                    "description": "Inclui arquivos de subpastas recursivamente",
                    "default": False,
                },
                "save_in_origin": {
                    "label": "Salvar na origem",
                    "description": "Ignora pasta de saída",
                    "default": False,
                },
                "overwrite": {
                    "label": "Sobrescrever sem perguntar",
                    "description": "Não pergunta antes de sobrescrever arquivos existentes",
                    "default": False,
                },
            },
            num_columns=3,
        )
        self._grid_opts.changed.connect(self._on_opts_changed)

        grp_config = GroupPainel("Configurações e Opções")
        grp_config.group_layout.addWidget(self._panel_quality)
        grp_config.group_layout.addWidget(self._panel_ico)
        grp_config.group_layout.addWidget(self._spin_resize)
        grp_config.group_layout.addWidget(self._grid_opts)

        # ── Formato + Configurações lado a lado ───────────────────────
        self.main_layout.addWidget(GridGroupPainel(grp_formato, grp_config))

        # ── Carrega pasta do projeto ──────────────────────────────────
        if self.sys_preferences:
            root = self.sys_preferences.get("root_folder", "")
            if root:
                for folder in [os.path.join(root, d) for d in ("image", "images", "raster")] + [root]:
                    if os.path.isdir(folder):
                        self._file_list.add_files([folder])
                        break

    # ── Callbacks ────────────────────────────────────────────────────

    def _on_files_changed(self, count: int):
        if count > 0:
            self.page.set_badge(self.page.PRONTA)

    def _on_format_changed(self, fmt: str):
        fmt_info = OUTPUT_IMAGE_FORMATS.get(fmt, {})
        is_lossy = fmt_info.get("lossy", False)
        is_ico = fmt_info.get("supports_ico_sizes", False)
        self._panel_quality.setVisible(is_lossy)
        self._panel_ico.setVisible(is_ico)
        self.logger.info(f"Formato alterado: {fmt}", code="IMG_CONV_FORMAT")

    def _on_opts_changed(self):
        enabled = self._grid_opts.is_item_checked("resize_enabled")
        self._spin_resize.set_enabled("width", enabled)
        self._spin_resize.set_enabled("height", enabled)

    # ── Conversão ───────────────────────────────────────────────────

    def _on_convert(self):
        paths = self._file_list.get_ordered_paths()
        if not paths:
            MessageBox.show_warning("Nenhuma imagem na lista.", title="Aviso")
            return

        output_format = self._combo_format.current_value
        if not output_format:
            MessageBox.show_warning("Selecione um formato de saída.", title="Aviso")
            return

        fmt_info = OUTPUT_IMAGE_FORMATS.get(output_format, {})
        ext = fmt_info.get("ext", ".png")

        if fmt_info.get("supports_ico_sizes", False):
            sizes_checked = self._grid_ico_sizes.checked
            if not sizes_checked:
                MessageBox.show_warning("Selecione ao menos um tamanho para ICO.", title="Aviso")
                return
            ico_sizes = sorted(int(k) for k in sizes_checked)
        else:
            ico_sizes = None

        quality = self._slider_quality.get("quality") if fmt_info.get("lossy", False) else 95

        resize_enabled = self._grid_opts.is_item_checked("resize_enabled")
        keep_aspect = self._grid_opts.is_item_checked("keep_aspect")
        resize = None
        if resize_enabled:
            resize = {
                "width": int(self._spin_resize.get("width")),
                "height": int(self._spin_resize.get("height")),
                "keep_aspect": keep_aspect,
            }

        save_in_origin = self._grid_opts.is_item_checked("save_in_origin")
        output_dir = "" if save_in_origin else self._sel_output["Pasta de Saída"].path()

        if not save_in_origin and not output_dir:
            MessageBox.show_warning(
                "Selecione pasta de saída ou marque 'Salvar na origem'.",
                title="Aviso",
            )
            return

        overwrite = self._grid_opts.is_item_checked("overwrite")

        result = MessageBox.show_question(
            f"Converter {len(paths)} imagem(ns) para {output_format}?\n"
            f"{'Redimensionar: ' + str(resize['width']) + 'x' + str(resize['height']) if resize else 'Sem redimensionamento'}\n"
            f"{'Salvando na origem' if save_in_origin else f'Pasta: {output_dir}'}",
            title="Confirmar",
        )
        if result != MessageBox.YES:
            self.logger.info("Conversão cancelada", code="IMG_CONV_CANCELLED")
            return

        self.logger.info(
            f"Iniciando conversão: {len(paths)} arquivos → {output_format}",
            code="IMG_CONV_START",
        )
        SignalManager.instance().console_message.emit(
            f"Convertendo {len(paths)} imagem(ns) para {output_format}..."
        )
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("convert", False)

        SignalManager.instance().hud_show.emit({"message": "Convertendo imagens..."})
        SignalManager.instance().execution_started.emit(self.tool_key)

        QTimer.singleShot(
            0,
            lambda: self._run_conversion(
                paths, output_format, ext, quality, resize, ico_sizes,
                output_dir, save_in_origin, overwrite,
            ),
        )

    def _run_conversion(self, paths, output_format, ext, quality, resize,
                        ico_sizes, output_dir, save_in_origin, overwrite):
        total = len(paths)
        ok_count = 0
        err_count = 0

        try:
            for idx, img_path in enumerate(paths, start=1):
                try:
                    out_dir = os.path.dirname(img_path) if save_in_origin else output_dir
                    os.makedirs(out_dir, exist_ok=True)

                    base_name = os.path.splitext(os.path.basename(img_path))[0]
                    out_path = os.path.join(out_dir, f"{base_name}{ext}")

                    if os.path.exists(out_path) and not overwrite:
                        resp = MessageBox.show_question(
                            f"Arquivo já existe:\n{out_path}\n\nDeseja sobrescrever?",
                            title="Sobrescrever?",
                        )
                        if resp != MessageBox.YES:
                            ok_count += 1
                            self.logger.info(f"Pulado (já existe): {out_path}", code="IMG_CONV_SKIPPED")
                            continue

                    self._convert_single_image(
                        img_path, out_path, output_format,
                        quality=quality, resize=resize, ico_sizes=ico_sizes,
                    )
                    ok_count += 1
                    self.logger.info(f"Convertido: {out_path}", code="IMG_CONV_OK")
                except Exception as e:
                    err_count += 1
                    self.logger.error(f"Erro {img_path}", code="IMG_CONV_ERR", error=str(e))
                    SignalManager.instance().console_message.emit(
                        f"Erro: {os.path.basename(img_path)} — {e}"
                    )

                pct = (idx / total) * 100.0
                SignalManager.instance().progress_update.emit(pct)
                SignalManager.instance().hud_update.emit({
                    "message": f"Convertendo {idx}/{total}...",
                    "progress": pct,
                })

            self.logger.info(
                f"Conversão finalizada: {ok_count} ok, {err_count} err",
                code="IMG_CONV_DONE",
            )
            msg = f"Conversão finalizada! {ok_count} arquivo(s) gerado(s)."
            if err_count:
                msg += f" {err_count} erro(s)."
            SignalManager.instance().console_message.emit(msg)

            if err_count == 0:
                self.page.set_badge(self.page.PRONTA)
                MessageBox.show_info(f"Sucesso! {ok_count} arquivo(s) gerado(s).", title="Concluído")
            else:
                self.page.set_badge(self.page.ERROR)
        except Exception as e:
            self.logger.error("Erro fatal na conversão", code="IMG_CONV_FATAL", error=str(e))
            SignalManager.instance().console_message.emit(f"Erro fatal: {e}")
            self.page.set_badge(self.page.ERROR)
        finally:
            SignalManager.instance().hud_hide.emit()
            SignalManager.instance().execution_finished.emit(self.tool_key)
            self.page.buttons.set_enabled("convert", True)
            SignalManager.instance().progress_update.emit(0.0)
            self.save_prefs()

    @staticmethod
    def _convert_single_image(
        input_path: str,
        output_path: str,
        output_format: str,
        quality: int = 95,
        resize: dict | None = None,
        ico_sizes: list[int] | None = None,
    ) -> str:
        from PIL import Image

        img = Image.open(input_path)

        if img.mode in ("P", "PA", "I", "F"):
            img = img.convert("RGBA")
        elif img.mode not in ("RGB", "RGBA", "LA", "L"):
            img = img.convert("RGBA")

        if resize and resize.get("width") and resize.get("height"):
            target_w = resize["width"]
            target_h = resize["height"]
            keep_aspect = resize.get("keep_aspect", True)

            if keep_aspect:
                img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            else:
                img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        if output_format in ("JPEG", "BMP") and img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1])
            img = background
        elif output_format in ("JPEG", "BMP") and img.mode == "RGBA":
            img = img.convert("RGB")

        save_params = {}

        if output_format == "JPEG":
            save_params["format"] = "JPEG"
            save_params["quality"] = quality
            save_params["optimize"] = True
        elif output_format == "PNG":
            save_params["format"] = "PNG"
        elif output_format == "BMP":
            save_params["format"] = "BMP"
        elif output_format == "GIF":
            save_params["format"] = "GIF"
        elif output_format == "TIFF":
            save_params["format"] = "TIFF"
            save_params["compression"] = "tiff_lzw"
        elif output_format == "WEBP":
            save_params["format"] = "WEBP"
            save_params["quality"] = quality
            save_params["lossless"] = False
        elif output_format == "ICO":
            save_params["format"] = "ICO"
            if ico_sizes:
                save_params["sizes"] = [(s, s) for s in sorted(ico_sizes)]
        else:
            raise ValueError(f"Formato não suportado: {output_format}")

        img.save(output_path, **save_params)
        return output_path

    # ── Preferências ─────────────────────────────────────────────────

    def load_prefs(self):
        fmt = self.preferences.get("output_format", "PNG")
        if fmt in OUTPUT_IMAGE_FORMATS:
            self._combo_format.current_value = fmt
            self._on_format_changed(fmt)

        quality = self.preferences.get("quality", 95)
        self._slider_quality.set("quality", quality, block_callbacks=True)

        ico_states = self.preferences.get("ico_sizes", {})
        if ico_states:
            self._grid_ico_sizes.set_all(ico_states)

        resize_enabled = self.preferences.get("resize_enabled", False)
        self._grid_opts.set_all({
            "resize_enabled": resize_enabled,
            "keep_aspect": self.preferences.get("keep_aspect", True),
        })
        self._spin_resize.set_enabled("width", resize_enabled)
        self._spin_resize.set_enabled("height", resize_enabled)

        self._spin_resize.set("width", self.preferences.get("resize_width", 1920), block_signals=True)
        self._spin_resize.set("height", self.preferences.get("resize_height", 1080), block_signals=True)

        out = self.preferences.get("output_dir", "")
        if out:
            self._sel_output["Pasta de Saída"].set_path(out)

        opts = self.preferences.get("options", {})
        if opts:
            self._grid_opts.set_all(opts)

    def save_prefs(self):
        self.preferences["output_format"] = self._combo_format.current_value
        self.preferences["quality"] = self._slider_quality.get("quality")
        self.preferences["ico_sizes"] = self._grid_ico_sizes.all
        self.preferences["resize_enabled"] = self._grid_opts.is_item_checked("resize_enabled")
        self.preferences["resize_width"] = int(self._spin_resize.get("width"))
        self.preferences["resize_height"] = int(self._spin_resize.get("height"))
        self.preferences["keep_aspect"] = self._grid_opts.is_item_checked("keep_aspect")
        self.preferences["output_dir"] = self._sel_output["Pasta de Saída"].path()
        self.preferences["options"] = self._grid_opts.all