# -*- coding: utf-8 -*-
"""
ConsoleTool — Console de execução compartilhado
================================================
Widget de console independente com botões de ação padronizados.
Registrado como uma aba no Workspace.
"""

from __future__ import annotations

from datetime import datetime

from plugins.BasePlugin import BasePlugin
from core.manager.SignalManager import SignalManager
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.ReadOnlyTextBrowser import ReadOnlyTextBrowser
from PySide6.QtGui import QDesktopServices
from utils.ColorProvider import ColorProvider


class ConsolePlugin(BasePlugin):
    """
    Console de execução compartilhado.
    Exibe logs formatados com HTML, suporte a links.
    Inclui botões "Selecionar Tudo", "Copiar Tudo" e "Limpar Console".
    """

    def __init__(self, parent=None):
        super().__init__(tool_key="Console", parent=parent)
        self._connect_signals()
        self.logger.info("ConsoleTool carregada", code="TOOL_READY")

    def _build_ui(self):
        """Constrói a UI usando o layout padrão do BasePlugin + ExecutionButtons."""
        super()._build_ui()

        # Botões de ação padronizados
        self.buttons = ExecutionButtons(self, {
            "select_all": {
                "text": "SELECIONAR TUDO",
                "callback": self._on_select_all,
                "type": "secondary",
                "description": "Seleciona todo o texto do console",
            },
            "copy_all": {
                "text": "COPIAR TUDO",
                "callback": self._on_copy_all,
                "type": "secondary",
                "description": "Copia todo o texto do console para a área de transferência",
            },
            "clear_console": {
                "text": "LIMPAR CONSOLE",
                "callback": self.clear_log,
                "type": "secondary",
                "description": "Limpa todo o conteúdo do console",
            },
        })
        self.main_layout.addWidget(self.buttons)

        # Text browser do log
        self.txt_log = ReadOnlyTextBrowser(
            placeholder="Console compartilhado — mensagens de execucao aparecem aqui..."
        )
        self.main_layout.addWidget(self.txt_log, 1)

    def _on_select_all(self) -> None:
        """Seleciona todo o texto do console."""
        self.txt_log.select_all()

    def _on_copy_all(self) -> None:
        """Copia todo o conteúdo do console para a área de transferência."""
        self.txt_log.copy_all()

    def append_log(self, html: str) -> None:
        """Adiciona uma mensagem formatada em HTML ao console."""
        self.txt_log.append_html(html)

    def clear_log(self) -> None:
        """Limpa o console."""
        self.txt_log.clear_content()
        self.logger.info("Console limpo", code="CONSOLE_CLEAR")

    def set_placeholder(self, text: str) -> None:
        self.txt_log.setPlaceholderText(text)

    # ── Conexão com sinais do sistema ─────────────────────────────

    def _connect_signals(self) -> None:
        """Conecta sinais globais do SignalManager aos handlers do console."""
        SignalManager.instance().console_message.connect(self._on_console_message)
        SignalManager.instance().console_html.connect(self._on_console_html)
        self.txt_log.anchorClicked.connect(self._on_anchor_clicked)

    def _on_console_message(self, message: str) -> None:
        """Recebe uma mensagem de texto do SignalManager (escapada)."""
        import html as html_mod

        timestamp = datetime.now().strftime("%H:%M:%S")
        safe = html_mod.escape(message)
        text_color = ColorProvider.text_primary()
        ts_color = ColorProvider.tool_color("System")
        self.append_log(
            f'<span style="color:{text_color};font-family:Consolas,monospace;">'
            f'<span style="color:{ts_color};">[{timestamp}]</span> '
            f'{safe}</span>'
        )

    def _on_console_html(self, html: str) -> None:
        """Recebe HTML formatado do SignalManager (sem escapar)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        text_color = ColorProvider.text_primary()
        ts_color = ColorProvider.tool_color("System")
        self.append_log(
            f'<span style="color:{text_color};font-family:Consolas,monospace;">'
            f'<span style="color:{ts_color};">[{timestamp}]</span> '
            f'{html}</span>'
        )

    def _on_anchor_clicked(self, url):
        """Abre links clicados no console usando o sistema (Explorer/padrao)."""
        QDesktopServices.openUrl(url)

    @property
    def anchorClicked(self):
        """Expoe o sinal para conexao externa."""
        return self.txt_log.anchorClicked

    # ── Preferences ─────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Carrega preferencias do Console (vazio por enquanto)."""
        pass

    def save_prefs(self) -> None:
        """Salva preferencias do Console (vazio por enquanto)."""
        pass