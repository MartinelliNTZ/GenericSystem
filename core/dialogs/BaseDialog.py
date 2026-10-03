# -*- coding: utf-8 -*-
"""
BaseDialog — Classe base para todos os diálogos do Aetheris ToolBox
====================================================================
Fornece:
  - AppBar no topo (mesmo padrão do MainWindow)
  - main_layout pronto com margins e spacing padronizados
  - Helper _add_button_bar() para botões no final do diálogo
  - Helper _add_title() para títulos centralizados
  - Helper _add_centered_text() para textos centralizados
  - Hook _build_ui() chamado automaticamente no final do __init__

Uso:
    class MyDialog(BaseDialog):
        def _build_ui(self):
            self._add_title("Título")
            self.main_layout.addWidget(QLabel("conteúdo específico"))
            self._add_button_bar(["cancel", "ok"])
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from resources.styles.AppStyles import AppStyles
from resources.widgets.app_bar import AppBar


# Margens e espaçamento padrão para o conteúdo do diálogo
_DEFAULT_MARGINS: Tuple[int, int, int, int] = (16, 16, 16, 16)
_DEFAULT_SPACING: int = 8


class BaseDialog(QDialog):
    """
    Classe base para diálogos do Aetheris ToolBox.

    Fornece:
    - AppBar no topo (mesmo padrão do MainWindow) com min/max/close
    - main_layout (QVBoxLayout) pronto com margins e spacing padronizados
    - Helper _add_button_bar() para botões no final do diálogo
    - Helper _add_title() para títulos centralizados
    - Helper _add_centered_text() para textos centralizados
    - Hook _build_ui() chamado automaticamente no final do __init__

    Args:
        parent: Widget pai.
        title: Título da janela e da AppBar.
        object_name: Nome do objeto (para estilização via QSS).
        fixed_size: Tupla (largura, altura) para tamanho fixo.
        min_size: Tupla (largura, altura) para tamanho mínimo.
        modal: Se True, setModal(True).
        has_appbar: Se True, exibe AppBar no topo (frameless). Default True.
    """

    def __init__(
        self,
        parent=None,
        title: str = "",
        object_name: str = "",
        fixed_size: Optional[Tuple[int, int]] = None,
        min_size: Optional[Tuple[int, int]] = None,
        modal: bool = True,
        has_appbar: bool = True,
    ):
        super().__init__(parent)

        # Deve ser definido ANTES de setWindowTitle (a override usa _has_appbar)
        self._has_appbar = has_appbar

        if title:
            self.setWindowTitle(title)
        if object_name:
            self.setObjectName(object_name)
        if fixed_size:
            self.setFixedSize(*fixed_size)
        if min_size:
            self.setMinimumSize(*min_size)
        if modal:
            self.setModal(True)

        # Aplica stylesheet genérico do diálogo (background, border, border-radius)
        self.setStyleSheet(AppStyles.dialog_stylesheet())

        # ── Root layout (sem margins, igual MainWindow) ──
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── AppBar no topo (edge-to-edge, igual MainWindow) ──
        if has_appbar:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)

            self.appbar = AppBar()
            self.appbar.set_title(title)
            self.appbar.minimize_clicked.connect(self.showMinimized)
            self.appbar.maximize_restore_clicked.connect(self._toggle_maximize_restore)
            self.appbar.close_clicked.connect(self.reject)
            root_layout.addWidget(self.appbar)

        # ── Container de conteúdo com margins padronizadas ──
        content = QWidget()
        content.setObjectName("dialog_content")
        content.setStyleSheet(AppStyles.dialog_content_border_style())
        self.main_layout = QVBoxLayout(content)
        self.main_layout.setContentsMargins(*_DEFAULT_MARGINS)
        self.main_layout.setSpacing(_DEFAULT_SPACING)
        root_layout.addWidget(content, 1)

        self._build_ui()

    # ────────────────────────────────────────────────────────────
    # HOOK DE CONSTRUÇÃO
    # ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Hook chamado ao final do __init__. Subclasses devem sobrescrever."""
        pass

    # ────────────────────────────────────────────────────────────
    # HELPERS DE UI
    # ────────────────────────────────────────────────────────────

    def _add_title(self, text: str, object_name: str = "") -> QLabel:
        """Adiciona um título centralizado ao layout (abaixo da AppBar)."""
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(label)
        return label

    def _add_centered_text(self, text: str, object_name: str = "",
                           word_wrap: bool = False) -> QLabel:
        """Adiciona um texto centralizado (descrição, copyright, etc.)."""
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if word_wrap:
            label.setWordWrap(True)
        self.main_layout.addWidget(label)
        return label

    # ────────────────────────────────────────────────────────────
    # HELPERS DE LAYOUT
    # ────────────────────────────────────────────────────────────

    def _add_button_bar(
        self,
        buttons: Union[
            List[str],
            Dict[str, Dict[str, Union[str, Callable[[], None]]]],
        ],
        default_width: int = 80,
    ) -> Dict[str, QPushButton]:
        """
        Adiciona uma barra de botões no final do diálogo.

        Args:
            buttons: Lista de strings com chaves padrão ou Dict completo.
                Strings suportadas:
                - "ok"      → texto "OK", accept()
                - "cancel"  → texto "Cancelar", reject()
                - "save"    → texto "Salvar", accept()
                - "close"   → texto "Fechar", accept()
                - "carregar"→ texto "Carregar", accept()
                Dict completo:
                    {"chave": {"text": "OK", "callback": self._fn}}
            default_width: Largura padrão dos botões.

        Returns:
            Dict[str, QPushButton] — botões criados.
        """
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        created: Dict[str, QPushButton] = {}

        if isinstance(buttons, list):
            for key in buttons:
                meta = self._button_meta(key)
                btn = self._create_button(
                    text=meta["text"],
                    callback=meta["callback"],
                    width=meta.get("width", default_width),
                )
                btn_layout.addWidget(btn)
                created[key] = btn
        else:
            for key, config in buttons.items():
                btn = self._create_button(
                    text=str(config.get("text", key)),
                    callback=config.get("callback", self.accept),  # type: ignore[arg-type]
                    width=int(config.get("width", default_width)),
                )
                btn_layout.addWidget(btn)
                created[key] = btn

        self.main_layout.addLayout(btn_layout)
        return created

    def _button_meta(self, key: str) -> Dict[str, object]:
        """Retorna metadados para chaves de botão conhecidas."""
        meta: Dict[str, object] = {
            "ok": {"text": "OK", "callback": self.accept},
            "cancel": {"text": "Cancelar", "callback": self.reject},
            "save": {"text": "Salvar", "callback": self.accept},
            "close": {"text": "Fechar", "callback": self.accept},
            "carregar": {"text": "Carregar", "callback": self.accept},
        }
        return dict(meta.get(key, {"text": key, "callback": self.accept}))

    @staticmethod
    def _create_button(
        text: str,
        callback: Callable[[], None],
        width: int = 80,
    ) -> QPushButton:
        """Cria um QPushButton padronizado."""
        btn = QPushButton(text)
        btn.setFixedWidth(width)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    # ────────────────────────────────────────────────────────────
    # CONTROLE DE JANELA (AppBar)
    # ────────────────────────────────────────────────────────────

    def _toggle_maximize_restore(self) -> None:
        """Alterna entre maximizado e normal (chamado pelo AppBar)."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ────────────────────────────────────────────────────────────
    # OVERRIDE setWindowTitle — sincroniza com AppBar
    # ────────────────────────────────────────────────────────────

    def setWindowTitle(self, title: str) -> None:
        """Sobrescreve para manter AppBar sincronizada com o título."""
        super().setWindowTitle(title)
        if self._has_appbar and hasattr(self, "appbar"):
            self.appbar.set_title(title)