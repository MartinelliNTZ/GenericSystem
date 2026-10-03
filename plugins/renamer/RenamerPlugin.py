# -*- coding: utf-8 -*-
"""
RenamerPlugin — Renomeador em lote de arquivos
===============================================
Ferramenta do tipo FOLDER que permite renomear arquivos em lote
com 4 modos e filtro de extensões.

Modos:
  1. Adicionar Sufixo    → anexa texto ao final (antes da extensão)
  2. Adicionar Prefixo   → anexa texto ao início
  3. Remover X do Final  → remove N caracteres do final (ignorando extensão)
  4. Remover X do Começo → remove N caracteres do início
  5. Substituir Texto    → busca e substitui com opções de case/trecho
  6. Limpar Extensão     → remove todas as extensões
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from core.enum.ToolKey import ToolKey
from plugins.BasePlugin import BasePlugin
from core.dialogs.PreviewDialog import PreviewDialog
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.simple.SimpleSelector import SimpleSelector
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from utils.DictManager import DictManager
from utils.MessageBox import MessageBox


class RenamerPlugin(BasePlugin):
    """
    Renomeador em lote de arquivos com múltiplos modos e filtro de extensões.
    """

    MODE_PREFIX = "Adicionar Prefixo"
    MODE_SUFFIX = "Adicionar Sufixo"
    MODE_REMOVE_START = "Remover X do Começo"
    MODE_REMOVE_END = "Remover X do Final (ignora extensão)"
    MODE_REPLACE = "Substituir Texto"
    MODE_CLEAR = "Limpar Extensão"

    def __init__(self, parent=None):
        self._ext_config = DictManager.file_extensions()
        super().__init__(
            tool_key=ToolKey.RENAMER.value,
            parent=parent,
            title="Renomeador em Lote",
        )
        self._update_visibility()
        self.logger.info("RenamerPlugin inicializado", code="RENAMER_READY")

    def _build_ui(self):
        super()._build_ui()

        # ── Botões de Ação ────────────────────────────────────────────
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "preview": {
                "text": "PRÉ-VISUALIZAR",
                "callback": self._on_preview,
                "type": "secondary",
                "description": "Exibe prévia das alterações antes de renomear",
            },
            "reset": {
                "text": "RESTAURAR PADRÃO",
                "callback": self._reset_prefs,
                "type": "secondary",
                "description": "Restaura configurações para o valor padrão",
            },
            "executar": {
                "text": "EXECUTAR RENOMEIO",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executa o renomeio em lote dos arquivos",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Widgets ──────────────────────────────────────────────────

        self._sel_origem = SimpleSelector(
            "Pasta Origem:", "",
            placeholder="Caminho da pasta com os arquivos...",
            browse_mode="directory", label_width=120,
        )
        self._sel_destino = SimpleSelector(
            "Pasta Destino:", "",
            placeholder="Deixe vazio para renomear no local",
            browse_mode="directory", label_width=120,
        )
        self._grid_subpastas = GridCheckBox(
            config={
                "subpastas": {
                    "label": "Vasculhar subpastas",
                    "description": "Inclui arquivos de subpastas recursivamente",
                    "default": False,
                },
            },
            num_columns=1,
        )

        self._combo_modo = SimpleComboBox(
            items={
                self.MODE_PREFIX: self.MODE_PREFIX,
                self.MODE_SUFFIX: self.MODE_SUFFIX,
                self.MODE_REMOVE_START: self.MODE_REMOVE_START,
                self.MODE_REMOVE_END: self.MODE_REMOVE_END,
                self.MODE_REPLACE: self.MODE_REPLACE,
                self.MODE_CLEAR: self.MODE_CLEAR,
            },
            on_item_changed=self._on_mode_changed,
            label="Modo:",
        )

        self._grid_texto = GridLineEdit(
            config={
                "texto": {
                    "label": "Texto:",
                    "description": "Texto para adicionar ou buscar",
                    "default": "",
                    "placeholder": "Texto para adicionar ou buscar...",
                },
                "subst": {
                    "label": "Substituir por:",
                    "description": "Texto de substituição",
                    "default": "",
                    "placeholder": "Texto de substituição...",
                },
            },
        )
        self._grid_texto.setObjectName("grid_texto")

        self._grid_qtd = GridDoubleSpinBox(
            config={
                "qtd": {
                    "label": "Quantidade:",
                    "description": "Número de caracteres a remover",
                    "decimal": 0,
                    "default": 1,
                    "min": 1,
                    "max": 9999,
                },
            },
        )
        self._grid_qtd.setObjectName("grid_qtd")

        self._grid_replace_opts = GridCheckBox(
            config={
                "case_sensitive": {
                    "label": "Case Sensitive",
                    "description": "Diferenciar maiúsculas de minúsculas",
                    "default": False,
                },
                "trecho_exato": {
                    "label": "Substituir trecho exato (senão substitui nome todo)",
                    "default": True,
                },
            },
            num_columns=1,
        )
        self._grid_replace_opts.setObjectName("grid_replace_opts")

        # ── Painel Pastas (coluna 0) ─────────────────────────────────
        grp_pastas = GroupPainel("Pastas")
        grp_pastas.group_layout.addWidget(self._sel_origem)
        grp_pastas.group_layout.addWidget(self._sel_destino)
        grp_pastas.group_layout.addWidget(self._grid_subpastas)

        # ── Painel Modo (coluna 1) ───────────────────────────────────
        grp_modo = GroupPainel("Modo de Renomeio")
        grp_modo.group_layout.addWidget(self._combo_modo)
        grp_modo.group_layout.addWidget(self._grid_texto)
        grp_modo.group_layout.addWidget(self._grid_qtd)
        grp_modo.group_layout.addWidget(self._grid_replace_opts)

        # ── Grid: colunas 0 e 1 ──────────────────────────────────────
        grid = GridGroupPainel(grp_pastas, grp_modo)
        self.main_layout.addWidget(grid)

        # ── Filtro de Extensões (full width) ─────────────────────────
        self._grid_ext = GridCheckBox(self._ext_config, num_columns=7)
        grp_ext = GroupPainel("Filtro de Extensões (deschecadas = ignoradas)")
        grp_ext.group_layout.addWidget(self._grid_ext)
        self.main_layout.addWidget(grp_ext)

    # ── Visibilidade por modo ────────────────────────────────────────

    def _on_mode_changed(self, mode: str):
        self.logger.info(f"Modo alterado: {mode}", code="RENAMER_MODE")
        self._update_visibility()

    def _update_visibility(self):
        mode = self._combo_modo.current_value
        is_prefix_suffix = mode in (self.MODE_PREFIX, self.MODE_SUFFIX)
        is_remove = mode in (self.MODE_REMOVE_START, self.MODE_REMOVE_END)
        is_replace = mode == self.MODE_REPLACE

        self._grid_texto.setVisible(is_prefix_suffix or is_replace)
        self._grid_qtd.setVisible(is_remove)
        self._grid_replace_opts.setVisible(is_replace)

    # ── Preferências ──────────────────────────────────────────────────

    def load_prefs(self):
        self._sel_origem.set_path(self.preferences.get("origem", ""))
        self._sel_destino.set_path(self.preferences.get("destino", ""))
        mode = self.preferences.get("modo", self.MODE_PREFIX)
        self._combo_modo.current_value = mode
        texto = self.preferences.get("texto", "")
        subst = self.preferences.get("subst", "")
        self._grid_texto.set_values({"texto": texto, "subst": subst}, block_signals=True)
        qtd = self.preferences.get("qtd", 1)
        self._grid_qtd.set("qtd", float(qtd), block_signals=True)
        self._grid_replace_opts.set_all({
            "case_sensitive": self.preferences.get("case_sensitive", False),
            "trecho_exato": self.preferences.get("trecho_exato", True),
        })
        self._grid_subpastas.set_all({
            "subpastas": self.preferences.get("subpastas", False),
        })
        ext_states = self.preferences.get("extensoes", {})
        if ext_states:
            self._grid_ext.set_all(ext_states)

    def save_prefs(self):
        self.preferences["origem"] = self._sel_origem.path()
        self.preferences["destino"] = self._sel_destino.path()
        self.preferences["modo"] = self._combo_modo.current_text
        self.preferences["texto"] = self._grid_texto.get("texto")
        self.preferences["subst"] = self._grid_texto.get("subst")
        self.preferences["qtd"] = int(self._grid_qtd.get("qtd"))
        self.preferences["case_sensitive"] = bool(self._grid_replace_opts.all.get("case_sensitive", False))
        self.preferences["trecho_exato"] = bool(self._grid_replace_opts.all.get("trecho_exato", True))
        self.preferences["subpastas"] = bool(self._grid_subpastas.all.get("subpastas", False))
        self.preferences["extensoes"] = self._grid_ext.all

    def _reset_prefs(self):
        self.preferences.clear()
        self.force_save_prefs()
        self.load_prefs()
        MessageBox.show_info("Preferências restauradas para o padrão.", title="Restaurado")

    # ── Helpers ──────────────────────────────────────────────────────

    def _get_texto(self) -> str:
        return self._grid_texto.get("texto")
    def _get_subst(self) -> str:
        return self._grid_texto.get("subst")
    def _get_qtd(self) -> int:
        return int(self._grid_qtd.get("qtd"))
    def _get_case_sensitive(self) -> bool:
        return bool(self._grid_replace_opts.all.get("case_sensitive", False))
    def _get_trecho_exato(self) -> bool:
        return bool(self._grid_replace_opts.all.get("trecho_exato", True))
    def _get_subpastas(self) -> bool:
        return bool(self._grid_subpastas.all.get("subpastas", False))

    # ── Preview ──────────────────────────────────────────────────────

    def _get_files(self) -> List[Path]:
        origem = Path(self._sel_origem.path())
        if not origem.is_dir():
            return []
        ext_filter = self._grid_ext.checked
        if not ext_filter:
            return []
        files = []
        if self._get_subpastas():
            for f in origem.rglob("*"):
                if f.is_file() and f.suffix.lower() in ext_filter:
                    files.append(f)
        else:
            for f in origem.iterdir():
                if f.is_file() and f.suffix.lower() in ext_filter:
                    files.append(f)
        return sorted(files)

    def _generate_preview(self) -> List[tuple]:
        files = self._get_files()
        if not files:
            return []
        destino_base = Path(self._sel_destino.path()) if self._sel_destino.path() else None
        if destino_base and not destino_base.is_dir():
            return []
        mode = self._combo_modo.current_value
        texto = self._get_texto()
        subst = self._get_subst()
        qtd = self._get_qtd()
        case_sensitive = self._get_case_sensitive()
        trecho_exato = self._get_trecho_exato()
        results = []
        for f in files:
            stem = f.stem
            ext = f.suffix
            if mode == self.MODE_PREFIX:
                new_stem = texto + stem
            elif mode == self.MODE_SUFFIX:
                new_stem = stem + texto
            elif mode == self.MODE_REMOVE_START:
                new_stem = stem[qtd:]
            elif mode == self.MODE_REMOVE_END:
                new_stem = stem[:-qtd] if qtd < len(stem) else ""
            elif mode == self.MODE_REPLACE:
                if trecho_exato:
                    new_stem = stem.replace(texto, subst) if case_sensitive else _case_insensitive_replace(stem, texto, subst)
                else:
                    found = (texto in stem) if case_sensitive else (texto.lower() in stem.lower())
                    new_stem = subst if found else stem
            elif mode == self.MODE_CLEAR:
                new_stem = stem
                ext = ""
            else:
                new_stem = stem
            new_name = new_stem + ext if ext else new_stem
            if str(f.name) != new_name:
                results.append((str(f.name), new_name))
        return results

    def _on_preview(self):
        preview = self._generate_preview()
        if not preview:
            if not self._sel_origem.path():
                MessageBox.show_warning("Selecione uma pasta de origem primeiro.", title="Aviso")
            else:
                MessageBox.show_info("Nenhum arquivo será modificado.", title="Preview")
            return
        PreviewDialog.exec_preview(items=preview, title="Pré-Visualização", parent=self)

    # ── Execução ─────────────────────────────────────────────────────

    def _on_executar(self):
        self.logger.info("Executando renomeio em lote", code="RENAMER_EXEC_START")
        preview = self._generate_preview()
        if not preview:
            self.logger.warning("Preview vazio — nada a renomear", code="RENAMER_PREVIEW_EMPTY")
            MessageBox.show_warning("Nada a renomear. Verifique a pasta e o filtro.", title="Aviso")
            return
        result = MessageBox.show_question(text=f"Confirmar renomeio de {len(preview)} arquivo(s)?", title="Confirmar")
        if result != MessageBox.YES:
            self.logger.info("Renomeio cancelado pelo usuário", code="RENAMER_CANCELLED")
            return
        self.logger.info(f"Renomeio confirmado para {len(preview)} arquivo(s)", code="RENAMER_CONFIRMED")
        origem_base = Path(self._sel_origem.path())
        destino_base = Path(self._sel_destino.path()) if self._sel_destino.path() else None
        errors = 0
        renamed = 0
        for orig_name, new_name in preview:
            src = origem_base / orig_name
            dst = (destino_base / new_name) if destino_base else (src.parent / new_name)
            try:
                if dst.exists():
                    base, ext = dst.stem, dst.suffix
                    count = 1
                    while dst.exists():
                        dst = dst.parent / f"{base}_{count}{ext}"
                        count += 1
                src.rename(dst)
                renamed += 1
            except Exception as e:
                errors += 1
                self.logger.error(f"Erro ao renomear {orig_name}: {e}", code="RENAMER_RENAME_ERR", error=str(e))
        self.save_prefs()
        msg = f"{renamed} arquivo(s) renomeado(s) com sucesso."
        if errors:
            msg += f" {errors} erro(s)."
        MessageBox.show_info(msg, title="Concluído")


def _case_insensitive_replace(text: str, old: str, new: str) -> str:
    if not old:
        return text
    result = []
    i = 0
    lower_text, lower_old = text.lower(), old.lower()
    while i < len(text):
        pos = lower_text.find(lower_old, i)
        if pos == -1:
            result.append(text[i:])
            break
        result.append(text[i:pos])
        result.append(new)
        i = pos + len(old)
    return "".join(result)