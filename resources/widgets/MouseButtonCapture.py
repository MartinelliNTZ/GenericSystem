# -*- coding: utf-8 -*-
"""
MouseButtonCapture — Campo de captura de botão do mouse (com label opcional)
=============================================================================
Widget composto que encapsula um QFormLayout com label + QLineEdit
que captura o botão do mouse ao focar, usando pynput.mouse.Listener.

Uso:
    capture = MouseButtonCapture(default_button="left")
    capture.buttonChanged.connect(self._on_button_changed)
    selected = capture.captured_button()  # "left", "right", etc.

    # Com label encapsulado (elimina QFormLayout externo)
    capture = MouseButtonCapture(default_button="left", label="Botão do mouse:")
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit
from pynput import mouse

# ── Display names ────────────────────────────────────────────────────
_DISPLAY_NAMES: dict[str, str] = {
    "left": "Left (Esquerdo)",
    "right": "Right (Direito)",
    "middle": "Middle (Meio)",
    "x1": "X1 (Botão lateral)",
    "x2": "X2 (Botão lateral)",
}

# Mapeamento pynput.Button → string pyautogui
_PYNPUT_BUTTON_MAP: dict = {
    mouse.Button.left: "left",
    mouse.Button.right: "right",
    mouse.Button.middle: "middle",
    mouse.Button.x1: "x1",
    mouse.Button.x2: "x2",
}


def _to_display(button_name: str) -> str:
    """Converte nome interno (ex: 'left', 'x1') para exibição amigável."""
    return _DISPLAY_NAMES.get(button_name, button_name.capitalize())


class _MouseButtonLineEdit(QLineEdit):
    """
    LineEdit interno que captura botão do mouse ao clicar.
    Usa pynput.mouse.Listener para capturar o próximo clique fora do widget.
    """

    buttonChanged = Signal(str)

    def __init__(
        self,
        default_button: str = "left",
        placeholder: str = "Clique e pressione um botão do mouse...",
        parent=None,
    ):
        super().__init__(parent)
        self._captured_raw = default_button
        self._listening = False
        self._listener = None
        self._listener_thread = None

        self.setReadOnly(True)
        self.setPlaceholderText(placeholder)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMaxLength(30)
        self._set_display(default_button)

        self.mousePressEvent = self._on_mouse_press  # type: ignore[method-assign]

    def captured_button(self) -> str:
        return self._captured_raw

    def set_captured_button(self, button_name: str) -> None:
        self._captured_raw = button_name
        self._set_display(button_name)
        self.buttonChanged.emit(button_name)

    def _set_display(self, button_name: str) -> None:
        self.setText(_to_display(button_name))

    def _on_mouse_press(self, event) -> None:
        """Inicia o modo de escuta ao clicar no widget."""
        if self._listening:
            return
        self._listening = True
        self.setFocus()
        self.selectAll()
        self.setText("... clique um botão do mouse")
        self.setStyleSheet("color: #FFD700;")

        # Inicia listener do pynput em uma thread separada
        self._start_listener()

    def _start_listener(self) -> None:
        """Inicia listener do pynput para capturar o próximo clique."""
        def on_click(x, y, button, pressed):
            if not pressed:
                return  # Só captura no pressionar
            if not self._listening:
                return

            mapped = _PYNPT_BUTTON_MAP.get(button)
            if mapped is None:
                return

            # Para o listener imediatamente
            self._stop_listener()

            # Volta para a thread principal via QTimer
            QTimer.singleShot(0, lambda: self._on_button_captured(mapped))

        self._listener = mouse.Listener(on_click=on_click)
        self._listener.daemon = True
        self._listener.start()

    def _stop_listener(self) -> None:
        """Para o listener do pynput."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _on_button_captured(self, button_name: str) -> None:
        """Callback chamado na thread principal após capturar um botão."""
        if not self._listening:
            return
        self._captured_raw = button_name
        self._listening = False
        self.setStyleSheet("")
        self._set_display(button_name)
        self.clearFocus()
        self.buttonChanged.emit(button_name)

    def keyPressEvent(self, event) -> None:
        if not self._listening:
            super().keyPressEvent(event)
            return

        # Tab sai do modo escuta sem capturar
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            self._listening = False
            self._stop_listener()
            self.setStyleSheet("")
            self._set_display(self._captured_raw)
            self.clearFocus()
            return

    def focusOutEvent(self, event) -> None:
        if self._listening:
            self._listening = False
            self._stop_listener()
            self.setStyleSheet("")
            self._set_display(self._captured_raw)
        super().focusOutEvent(event)


class MouseButtonCapture(QWidget):
    """
    Widget composto: label + QLineEdit que captura botão do mouse.

    Se ``label`` for informado, cria um QFormLayout com o label e o campo.
    Caso contrário, age como QLineEdit puro (compatibilidade).

    Uso:
        capture = MouseButtonCapture(default_button="left")
        capture.buttonChanged.connect(self._on_button_changed)
        selected = capture.captured_button()  # "left", "right", etc.

        # Com label encapsulado
        capture = MouseButtonCapture(default_button="left", label="Botão do mouse:")
    """

    buttonChanged = Signal(str)

    def __init__(
        self,
        default_button: str = "left",
        placeholder: str = "Clique e pressione um botão do mouse...",
        label: str | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self._line = _MouseButtonLineEdit(
            default_button=default_button,
            placeholder=placeholder,
        )
        self._line.buttonChanged.connect(self._forward_button_changed)

        if label:
            form = QFormLayout(self)
            form.setContentsMargins(0, 0, 0, 0)
            form.addRow(QLabel(label), self._line)
        else:
            lay = QVBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(self._line)

    def _forward_button_changed(self, button: str):
        self.buttonChanged.emit(button)

    def captured_button(self) -> str:
        return self._line.captured_button()

    def set_captured_button(self, button_name: str) -> None:
        self._line.set_captured_button(button_name)

    def setEnabled(self, enabled: bool) -> None:
        self._line.setEnabled(enabled)