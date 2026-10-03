# -*- coding: utf-8 -*-
"""
ConfigurationPlugin — Plugin de Configuração do Sistema
=========================================================
Ferramenta de sistema para configurações gerais do Aetheris ToolBox.
Exibe seletor de temas e salva/carrega via System Preferences.

Tipo BOTH — pode ser exibido tanto no workspace central quanto no painel lateral.
Acessível pelo menu Sistema > Configuração.
"""

from __future__ import annotations

from utils.MessageBox import MessageBox

from plugins.BasePlugin import BasePlugin
from resources.styles.ThemeManager import THEMES
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleComboBox import SimpleComboBox


class ConfigurationPlugin(BasePlugin):
    """
    Plugin de configuração do sistema.
    Gerencia temas e configurações globais.
    """

    def __init__(self, parent=None):
        super().__init__(
            tool_key="Configuration",
            parent=parent,
            title="Configuração",
            sys_prefs=True,  # carrega self.sys_preferences
        )

    def _build_ui(self):
        """Constrói a UI com seletor de temas."""
        super()._build_ui()

        # ── ExecutionButtons (padrão do sistema) — logo após o título ──
        self._btns = ExecutionButtons(self, {
            "salvar": {
                "text": "SALVAR CONFIG",
                "callback": self._on_salvar,
                "type": "primary",
                "description": "Salva as configurações atuais em disco",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Seletor de Tema ──
        grupo_tema = GroupPainel("Tema Visual")

        # Monta dict {key: label} dos temas disponíveis
        theme_items = {
            key: meta["label"]
            for key, meta in THEMES.items()
        }

        self._theme_combo = SimpleComboBox(
            items=theme_items,
            on_item_changed=self._on_theme_changed,
            label="Tema:",
            parent=self,
        )
        grupo_tema.group_layout.addWidget(self._theme_combo)

        self.main_layout.addWidget(grupo_tema)
        self.main_layout.addStretch()

    def load_prefs(self):
        """Carrega o tema salvo nas system preferences."""
        current = self.sys_preferences.get("theme", "dark_charcoal")
        self._theme_combo.current_value = current

    def save_prefs(self):
        """Salva o tema selecionado nas system preferences.
        
        Atualiza o dict sys_preferences — o closeEvent do BasePlugin
        persiste automaticamente com force_save_prefs().
        """
        theme_key = self._theme_combo.current_value
        if theme_key:
            self.sys_preferences["theme"] = theme_key

    def _on_salvar(self):
        """Callback do botão SALVAR CONFIG — persiste em System preferences."""
        try:
            self.save_prefs()
            from utils.Preferences import Preferences
            from core.enum.ToolKey import ToolKey
            Preferences.save_tool_prefs(ToolKey.SYSTEM, self.sys_preferences)
            self.logger.info(
                "Configurações salvas manualmente pelo usuário",
                code="CONFIG_SAVED",
            )
            MessageBox.show_toast("Configurações salvas com sucesso!")
        except Exception as e:
            self.logger.error(
                "Falha ao salvar configurações",
                code="CONFIG_SAVE_ERR",
                error=str(e),
            )
            MessageBox.show_toast("Falha ao salvar configurações", is_error=True)

    def _on_theme_changed(self, theme_key: str):
        """Callback quando o tema é alterado no combo."""
        self.sys_preferences["theme"] = theme_key
        self.save_prefs()
        self.logger.info(
            "Tema alterado",
            code="THEME_CHANGED",
            theme=theme_key,
        )