# -*- coding: utf-8 -*-
"""
ExecutionButtons — Container de botões de ação para plugins
=============================================================
Agrupa botões secundários à esquerda e primários/de perigo à direita,
com espaçamento automático entre os grupos.

Todos os botões recebem altura, font-size e padding uniformes.
O botão primary é ligeiramente maior (altura extra + font-size maior)
para destaque visual.

Uso:
    from resources.widgets.ExecutionButtons import ExecutionButtons

    buttons = ExecutionButtons(self, {
        "salvar": {
            "text": "SALVAR CONFIG",
            "callback": self._on_salvar,
            "type": "secondary",
            "description": "Salva a configuração atual em disco",
        },
        "preview": {
            "text": "PRÉ-VISUALIZAR",
            "callback": self._on_preview,
            "type": "secondary",
        },
        "executar": {
            "text": "EXECUTAR",
            "callback": self._on_executar,
            "type": "primary",
            "description": "Inicia o pipeline de execução",
        },
        "cancelar": {
            "text": "CANCELAR",
            "callback": self._on_cancelar,
            "type": "danger",
        },
    })

    # Acessa um botão pela chave
    buttons["executar"].setEnabled(False)
    buttons["executar"].setText("PARAR")

    # Oculta/exibe dinamicamente
    buttons.set_visible("cancelar", True)

    # Altera callback em runtime
    buttons.set_callback("executar", self._on_parar)
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


# ── Alturas e fontes padronizadas ──────────────────────────────────────

_BTN_HEIGHT = 20
_BTN_FONT_SIZE = 10
_BTN_PADDING = "6px 14px"

_PRIMARY_EXTRA_HEIGHT = 0
_PRIMARY_FONT_SIZE = 10


def _apply_uniform_style(btn: QPushButton, btn_type: str) -> None:
    """Aplica styling padronizado: altura, font-size, padding."""
    if btn_type == "primary":
        btn.setMinimumHeight(_BTN_HEIGHT + _PRIMARY_EXTRA_HEIGHT)
        btn.setStyleSheet(
            btn.styleSheet()
            + f"""
            QPushButton {{
                font-size: {_PRIMARY_FONT_SIZE}px;
                padding: {_BTN_PADDING};
                min-height: {_BTN_HEIGHT + _PRIMARY_EXTRA_HEIGHT}px;
            }}
            """
        )
    else:
        btn.setMinimumHeight(_BTN_HEIGHT)
        btn.setStyleSheet(
            btn.styleSheet()
            + f"""
            QPushButton {{
                font-size: {_BTN_FONT_SIZE}px;
                padding: {_BTN_PADDING};
                min-height: {_BTN_HEIGHT}px;
            }}
            """
        )
    btn.setCursor(Qt.CursorShape.PointingHandCursor)


# ── Fábrica de botões ────────────────────────────────────────────────

def _create_button(text: str, btn_type: str) -> QPushButton:
    """Cria um botão do tipo apropriado com o texto dado e styling uniforme."""
    from resources.widgets.simple.SimplePrimaryButton import SimplePrimaryButton
    from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton
    from resources.widgets.simple.SimpleDangerButton import SimpleDangerButton
    from resources.widgets.simple.SimpleGhostButton import SimpleGhostButton

    _CLASSES = {
        "primary": SimplePrimaryButton,
        "secondary": SimpleSecondaryButton,
        "danger": SimpleDangerButton,
        "ghost": SimpleGhostButton,
    }

    cls = _CLASSES.get(btn_type)
    if cls is None:
        raise ValueError(f"Tipo de botão inválido: {btn_type!r}. "
                         f"Use: {', '.join(_CLASSES)}")

    btn = cls(text)
    _apply_uniform_style(btn, btn_type)
    return btn


# ── Widget principal ─────────────────────────────────────────────────

class ExecutionButtons(QWidget):
    """
    Container horizontal de botões organizados em dois grupos:
      - Esquerda: botões secundários (secondary, ghost)
      - Direita:  botões primários/de perigo (primary, danger)

    Um stretch separa os dois grupos automaticamente.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        config: Optional[Dict] = None,
    ):
        super().__init__(parent)
        self._buttons: Dict[str, QPushButton] = {}
        self._callbacks: Dict[str, Callable] = {}

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

        if config:
            self.setup(config)

    def setup(self, config: Dict) -> None:
        """
        Configura os botões a partir de um dicionário.

        Estrutura do config:
            {
                "chave_unica": {
                    "text": str,              # Texto do botão (obrigatório)
                    "callback": callable,     # Função a conectar (obrigatório)
                    "type": str,              # primary | secondary | danger | ghost
                    "description": str,       # Tooltip (opcional)
                },
                ...
            }

        Botões do tipo 'secondary' e 'ghost' vão à esquerda.
        Botões do tipo 'primary' e 'danger' vão à direita.
        """
        # Limpa botões anteriores
        self._clear_buttons()

        # Separa em dois grupos
        left_keys: list[str] = []
        right_keys: list[str] = []

        for key, spec in config.items():
            btn_type = spec.get("type", "secondary")
            if btn_type in ("secondary", "ghost"):
                left_keys.append(key)
            else:
                right_keys.append(key)

        ordem = left_keys + ["__stretch__"] + right_keys

        for key in ordem:
            if key == "__stretch__":
                self._layout.addStretch()
                continue

            spec = config[key]
            text = spec.get("text", "Ação")
            btn_type = spec.get("type", "secondary")
            callback = spec.get("callback")
            description = spec.get("description", "")

            btn = _create_button(text, btn_type)

            if description:
                btn.setToolTip(description)

            if callable(callback):
                btn.clicked.connect(callback)
                self._callbacks[key] = callback

            self._buttons[key] = btn
            self._layout.addWidget(btn)

    def __getitem__(self, key: str) -> QPushButton:
        """Acessa um botão pela chave do config."""
        btn = self._buttons.get(key)
        if btn is None:
            raise KeyError(f"Botão '{key}' não encontrado. "
                           f"Chaves disponíveis: {list(self._buttons)}")
        return btn

    def __contains__(self, key: str) -> bool:
        """Verifica se uma chave existe."""
        return key in self._buttons

    def keys(self) -> list[str]:
        """Retorna lista de chaves de botões configurados."""
        return list(self._buttons.keys())

    def get(self, key: str, default=None) -> Optional[QPushButton]:
        """Retorna o botão pela chave, ou default se não existir."""
        return self._buttons.get(key, default)

    def set_callback(self, key: str, callback: Callable) -> None:
        """Troca o callback de um botão em runtime."""
        btn = self._buttons.get(key)
        if btn is None:
            raise KeyError(f"Botão '{key}' não encontrado")
        try:
            btn.clicked.disconnect()
        except RuntimeError:
            pass
        btn.clicked.connect(callback)
        self._callbacks[key] = callback

    def set_visible(self, key: str, visible: bool) -> None:
        """Mostra ou esconde um botão."""
        btn = self._buttons.get(key)
        if btn is not None:
            btn.setVisible(visible)

    def set_enabled(self, key: str, enabled: bool) -> None:
        """Habilita ou desabilita um botão."""
        btn = self._buttons.get(key)
        if btn is not None:
            btn.setEnabled(enabled)

    def set_all_enabled(self, enabled: bool) -> None:
        """Habilita/desabilita todos os botões."""
        for btn in self._buttons.values():
            btn.setEnabled(enabled)

    def set_all_visible(self, visible: bool) -> None:
        """Mostra/esconde todos os botões."""
        for btn in self._buttons.values():
            btn.setVisible(visible)

    # ── Privados ─────────────────────────────────────────────────────

    def _clear_buttons(self) -> None:
        """Remove todos os botões do layout."""
        for btn in self._buttons.values():
            try:
                btn.clicked.disconnect()
            except RuntimeError:
                pass
            self._layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        self._callbacks.clear()