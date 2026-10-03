# -*- coding: utf-8 -*-
"""
PreferencesManagerTool — Gerenciador de Preferências do Sistema
=================================================================
Ferramenta que exibe todas as preferências salvas no sistema,
permitindo editar, resetar ou remover itens por ToolKey.

Carregamento dinâmico — lê diretamente do preferences.json e
infere tipos automaticamente via Preferences.infer_type().
Não precisa de configuração manual SYSTEM_PREF_CONFIG.

Acessível pelo menu Sistema > Gerenciador de Preferências.
Não aparece na toolbar.
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import QWidget, QVBoxLayout

from core.enum.ToolKey import ToolKey
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridPreferenceItem import GridPreferenceItem
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from utils.Preferences import Preferences


def _build_dynamic_config(section: str) -> Dict[str, Any]:
    """
    Constrói um config dinâmico para uma seção a partir do JSON real.
    Usa Preferences.infer_type() para determinar o tipo de cada campo.
    """
    raw = Preferences.all_data().get(section, {})
    config: Dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            continue
        pref_type = Preferences.infer_type(value)
        safe_default = value if value is not None else (
            0 if pref_type in ("int", "float") else "")
        entry: Dict[str, Any] = {
            "type": pref_type,
            "default": safe_default,
            "label": key.replace("_", " ").title(),
        }
        if pref_type in ("int", "float"):
            entry["min"] = 0
            entry["max"] = 999999
            if pref_type == "float":
                entry["step"] = 0.1
                entry["decimals"] = 2
            else:
                entry["step"] = 1
        config[key] = entry
    return config


class PreferencesPlugin(BasePlugin):
    """
    Gerenciador de preferências do sistema.
    Carrega dinamicamente todas as seções do preferences.json.
    """

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.PREFERENCES,
            parent=parent,
            title="Gerenciador de Preferências",
        )

    def _build_ui(self):
        """Sobrescreve _build_ui do BasePlugin."""
        super()._build_ui()

        self._current_section: str = ""
        self._grid: GridPreferenceItem | None = None

        # ── Action Buttons ──
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "reset": {
                "text": "RESETAR PADRÃO",
                "callback": self._on_reset,
                "type": "secondary",
                "description": "Recarrega valores do disco descartando alterações",
            },
            "clear": {
                "text": "APAGAR TUDO",
                "callback": self._on_clear_all,
                "type": "danger",
                "description": "Remove todas as preferências da seção atual",
            },
            "save": {
                "text": "SALVAR",
                "callback": self._on_save,
                "type": "primary",
                "description": "Salva as preferências da seção atual",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Seletor de seção (SimpleComboBox com Dict) ──
        self._toolkey_dict = self._get_toolkey_dict()
        self._combo = SimpleComboBox(
            items=self._toolkey_dict,
            on_item_changed=self._on_section_changed,
            label="Ferramenta:",
            parent=self,
        )
        self.main_layout.addWidget(self._combo)

        # ── Grid de Preferências ──
        self._grid_container = QWidget()
        self._grid_layout = QVBoxLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self._grid_container, 1)

        # Seleciona o primeiro item e carrega o grid manualmente
        # (select_first pode não disparar sinal se o índice já for 0)
        if self._toolkey_dict:
            first_key = next(iter(self._toolkey_dict.keys()))
            self._current_section = first_key
            self._combo.current_value = first_key
            self._rebuild_grid()

    def _get_toolkey_dict(self) -> Dict[str, str]:
        """
        Lê do preferences.json e retorna Dict {key: key}
        com seções que possuem campos escalares editáveis.
        """
        all_data = Preferences.all_data()
        result: Dict[str, str] = {}
        for key in sorted(all_data.keys()):
            section_data = all_data[key]
            if not isinstance(section_data, dict):
                continue
            has_scalar = any(not isinstance(v, dict)
                             for v in section_data.values())
            if not has_scalar:
                continue
            result[key] = key
        return result

    def _on_section_changed(self, key: str):
        """Troca a seção de preferências exibida."""
        self._current_section = key
        self._rebuild_grid()

    def _rebuild_grid(self):
        """Recria o PreferenceItemGrid para a seção atual com config dinâmico."""
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w:
                self._grid_layout.removeWidget(w)
                w.deleteLater()

        config = _build_dynamic_config(self._current_section)
        self._grid = GridPreferenceItem(config, section=self._current_section)
        self._grid_layout.addWidget(self._grid)

    def _on_save(self):
        """Salva todas as preferências da seção atual."""
        if self._grid:
            self._grid.save_values()
            from utils.MessageBox import MessageBox
            MessageBox.show_info(
                text=f"Preferências salvas para '{self._current_section}'.",
                title="Salvo",
            )

    def _on_reset(self):
        """Recarrega do JSON descartando alterações não salvas."""
        if self._grid:
            Preferences.all_data()  # força refresh do cache
            self._rebuild_grid()

    def _on_clear_all(self):
        """Remove todas as preferências da seção do JSON inteiro."""
        if self._grid:
            from utils.MessageBox import MessageBox
            ok = MessageBox.show_question(
                text=f"Tem certeza que deseja apagar todas as preferências de '{self._current_section}'?",
                title="Confirmar",
            )
            if ok:
                all_data = Preferences.all_data()
                all_data.pop(self._current_section, None)
                Preferences.save_all(all_data)
                # Atualiza dicionário e reseleciona primeiro
                self._toolkey_dict = self._get_toolkey_dict()
                self._combo.set_items(self._toolkey_dict)
                if self._toolkey_dict:
                    first_key = next(iter(self._toolkey_dict.keys()))
                    self._current_section = first_key
                    self._combo.current_value = first_key
                    self._rebuild_grid()
