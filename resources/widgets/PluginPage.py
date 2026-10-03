# -*- coding: utf-8 -*-
"""
PluginPage — Layout padrão para todos os plugins
=================================================
Fornece:
- QVBoxLayout com margins (18, 10, 18, 10) e spacing 8
- Header opcional (QLabel + QFrame separator) se um title for informado
- Badge de status encapsulado — o plugin chama apenas:

      self.page.set_badge(self.page.PRONTA)
      self.page.set_badge(self.page.RUNNING)
      self.page.set_badge(self.page.ERROR)
      self.page.set_badge(self.page.CANCELED)
      self.page.set_badge(self.page.INFO)

  O estilo é aplicado automaticamente conforme o estado.

Uso no BasePlugin (automático):
    class MeuPlugin(BasePlugin):
        def _build_ui(self):
            super()._build_ui()
            self.page.set_badge(self.page.ERROR)

Uso standalone:
    page = PluginPage(title="Meu Plugin")
    page.set_badge(page.PRONTA)
"""

from __future__ import annotations

from enum import Enum
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout

from resources.widgets.BasePage import BasePage
from resources.widgets.ExecutionButtons import ExecutionButtons


class _BadgeState(Enum):
    """Estados internos do badge. Acessados via constantes na classe PluginPage."""
    READY = "PRONTA"
    RUNNING = "EXECUTANDO"
    ERROR = "ERRO"
    CANCELED = "CANCELADO"
    INFO = "INFO"


class Badge(QLabel):
    """
    Selo de status usado nos plugins para indicar estado.
    O estilo visual é aplicado automaticamente via set_badge().
    """

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("section_badge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class PluginPage(BasePage):
    """
    Container base que aplica o layout padrão do sistema.

    Se ``title`` for informado, cria automaticamente:
        - QLabel com objectName "header_title"
        - QFrame separator com objectName "separator"

    O badge de status é configurado via set_badge(estado).
    Use as constantes da própria classe:

        self.page.set_badge(self.page.PRONTA)
        self.page.set_badge(self.page.RUNNING)
        self.page.set_badge(self.page.ERROR)
        self.page.set_badge(self.page.CANCELED)
        self.page.set_badge(self.page.INFO)

    Atributos:
        main_layout : QVBoxLayout — layout principal para adicionar widgets filhos
        header      : QWidget | None — container do header (se title foi informado)
        badge       : Badge | None — badge de status (criado sob demanda)
    """

    # Constantes públicas — o plugin usa self.page.PRONTA, self.page.ERROR etc.
    PRONTA = _BadgeState.READY
    RUNNING = _BadgeState.RUNNING
    ERROR = _BadgeState.ERROR
    CANCELED = _BadgeState.CANCELED
    INFO = _BadgeState.INFO

    # Mapeamento estado -> cor de fundo do badge
    _BADGE_COLORS = {
        _BadgeState.READY: "#27ae60",      # verde
        _BadgeState.RUNNING: "#f39c12",    # laranja
        _BadgeState.ERROR: "#e74c3c",      # vermelho
        _BadgeState.CANCELED: "#95a5a6",   # cinza
        _BadgeState.INFO: "#3498db",       # azul
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str | None = None,
        buttons_config: dict | None = None,
    ) -> None:
        super().__init__(parent)

        self.header: QWidget | None = None
        self.badge: Badge | None = None
        self.buttons: ExecutionButtons | None = None
        self._project_path_label: QLabel | None = None

        if title:
            self._build_header(title)

        if buttons_config:
            self.buttons.setup(buttons_config)
            self.buttons.setVisible(True)
        elif self.buttons is not None:
            self.buttons.setVisible(False)

    def _build_header(self, title: str) -> None:
        """Constrói o header com título, badge e execution buttons alinhados à direita."""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        header_title = QLabel(title)
        header_title.setObjectName("header_title")
        header_layout.addWidget(header_title, 0)
        header_layout.setStretchFactor(header_title, 0)
        header_layout.addStretch(1)
        # Badge de status (ao lado do título)
        self.badge = Badge("")
        self.badge.setVisible(False)
        header_layout.addWidget(self.badge, 0)

        # Espaço elástico empurra buttons para a direita


        # ExecutionButtons alinhados à direita
        self.buttons = ExecutionButtons(header)
        header_layout.addWidget(self.buttons, 0)

        self._header_layout = header_layout
        self._header_title = header_title

        self.main_layout.addWidget(header)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        self.main_layout.addWidget(sep)

        self.header = header

    def set_project_path(self, path: str) -> None:
        """
        Exibe o caminho do projeto ao lado do título, alinhado à direita.
        Se path for vazio ou None, o label fica oculto.
        """
        if not path:
            if self._project_path_label is not None:
                self._project_path_label.setVisible(False)
            return

        if self._project_path_label is None:
            self._project_path_label = QLabel(path)
            self._project_path_label.setObjectName("header_project_path")
            self._project_path_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            # Insere antes do badge se existir
            if self.badge is not None:
                self._header_layout.insertWidget(self._header_layout.indexOf(self.badge), self._project_path_label, 0)
            else:
                self._header_layout.addWidget(self._project_path_label, 0)
        else:
            self._project_path_label.setText(path)
            self._project_path_label.setVisible(True)

    def set_badge(self, state: _BadgeState) -> Badge:
        """
        Define o estado do badge no header, ao lado do título.

        Args:
            state: Uma das constantes da classe:
                   page.PRONTA, page.RUNNING, page.ERROR,
                   page.CANCELED, page.INFO

        Returns:
            Badge: Instância do badge atualizado.
        """
        if not hasattr(self, '_header_layout'):
            raise RuntimeError(
                "PluginPage.set_badge() requires a title to be set. "
                "Pass 'title' to PluginPage constructor."
            )

        text = state.value
        bg_color = self._BADGE_COLORS[state]

        self.badge.setText(text)
        self.badge.setVisible(True)

        # Aplica o estilo encapsulado — plugin não precisa saber de AppStyles
        self.badge.setStyleSheet(
            f"QLabel {{"
            f"  background-color: {bg_color};"
            f"  color: #ffffff;"
            f"  border-radius: 4px;"
            f"  padding: 2px 10px;"
            f"  font-weight: 900;"
            f"  font-size: 10px;"
            f"  letter-spacing: 1.5px;"
            f"}}"
        )

        return self.badge
