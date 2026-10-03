# -*- coding: utf-8 -*-
"""
HotkeyPlugin — Plugin de automação de teclado
===============================================
Ao pressionar a tecla configurada, executa a operação configurada:
- Modo "Teclar Texto": digita automaticamente uma string caractere por caractere
- Modo "Teclar Atalho": executa uma sequência de teclas/atalhos N vezes

Uso:
    1. Abra o plugin no Workspace
    2. Configure o modo, valor, atraso inicial, intervalo e tecla de atalho
    3. Clique em "EXECUTAR" para ativar
    4. Pressione a tecla configurada (padrão: F) para executar
    5. Clique em "PARAR" para interromper
"""

from __future__ import annotations

import random
import time
from PySide6.QtCore import QTimer
from utils.ExplorerUtils import ExplorerUtils
from core.dialogs.ConfigSalvarDialog import ConfigSalvarDialog
from core.dialogs.ConfigCarregarDialog import ConfigCarregarDialog

from core.enum.ToolKey import ToolKey
from plugins.BasePlugin import BasePlugin
from core.manager.SignalManager import SignalManager
from utils.MessageBox import MessageBox
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine, _to_display
from resources.widgets.HotkeySequenceCapture import HotkeySequenceCapture
from resources.widgets.MouseButtonCapture import MouseButtonCapture
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SectionPanel import SectionPanel
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.simple.SimpleComboBox import SimpleComboBox


class HotkeyPlugin(BasePlugin):
    """
    Plugin de automação: executa ação ao pressionar uma tecla.
    Usa keyboard library diretamente (sem QThread) — a biblioteca
    já gerencia suas próprias threads para hooks globais.
    """

    # ── Valores padrão ────────────────────────────────────────────────
    DEFAULT_VALUE = "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"
    DEFAULT_HOTKEY = "f"
    DEFAULT_STARTUP_DELAY = 0.15
    DEFAULT_INTERVAL_DELAY = 0.01
    DEFAULT_SEQUENCE_INTERVAL = 1.0
    DEFAULT_SEQUENCE_REPEAT = 3

    MODE_TEXT = "Teclar Texto"
    MODE_HOTKEY = "Teclar Atalho"
    MODE_MOUSE = "Multi Clique Mouse"

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.HOTKEY_PLUGIN.value,
            parent=parent,
            title="Teclador F — Automação de Teclado",
        )
        self._running = False
        self._hotkey_handler = None
        self._update_mode_visibility()
        self.logger.info("HotkeyPlugin carregado", code="TOOL_READY")

    def _build_ui(self):
        """Sobrescreve _build_ui do BasePlugin."""
        super()._build_ui()

        # ── Botões de Ação ────────────────────────────────────────────
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "salvar": {
                "text": "SALVAR CONFIG",
                "callback": self._on_salvar_config,
                "type": "secondary",
                "description": "Salva a configuração atual em disco",
            },
            "ler": {
                "text": "LER CONFIG",
                "callback": self._on_ler_config,
                "type": "secondary",
                "description": "Carrega uma configuração salva anteriormente",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Inicia a execução com a tecla configurada",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Seletor de Modo (SimpleComboBox) ──────────────────────────
        self._combo_mode = SimpleComboBox(
            items={
                self.MODE_TEXT: self.MODE_TEXT,
                self.MODE_HOTKEY: self.MODE_HOTKEY,
                self.MODE_MOUSE: self.MODE_MOUSE,
            },
            on_item_changed=self._on_mode_changed,
            parent=self,
        )
        self.main_layout.addWidget(self._combo_mode)

        # ── Configurações ─────────────────────────────────────────────
        config_group = GroupPainel("Configurações")

        # ── Stack de modos ────────────────────────────────────────────
        self._stack_text = SectionPanel(object_name="stack_text")

        # Modo Texto — GridLineEdit
        self._grid_text = GridLineEdit(
            config={
                "valor": {
                    "label": "Valor",
                    "description": "Texto a ser digitado",
                    "default": self.DEFAULT_VALUE,
                    "placeholder": "Texto a ser digitado...",
                },
            },
        )
        self._grid_text.changed.connect(self._mark_dirty)
        self._stack_text.section_layout.addWidget(self._grid_text)

        # Modo Texto — GridDoubleSpinBox (atraso inicial e intervalo)
        self._grid_text_numbers = GridDoubleSpinBox(
            config={
                "atraso": {
                    "label": "Atraso inicial",
                    "description": "Tempo de espera antes de começar (s)",
                    "decimal": 1,
                    "default": self.DEFAULT_STARTUP_DELAY,
                    "suffix": "s",
                },
                "intervalo": {
                    "label": "Intervalo entre caracteres",
                    "description": "Tempo entre digitar cada caractere (s)",
                    "decimal": 2,
                    "default": self.DEFAULT_INTERVAL_DELAY,
                    "suffix": "s",
                },
            },
        )
        self._grid_text_numbers.changed.connect(self._mark_dirty)
        self._stack_text.section_layout.addWidget(self._grid_text_numbers)

        # ── Stack: Modo Atalho ────────────────────────────────────────
        self._stack_hotkey = SectionPanel(object_name="stack_hotkey", spacing=6)

        # Sequência de teclas (com title embutido)
        self._edit_sequence = HotkeySequenceCapture(
            title="Sequência de Teclas:",
        )
        self._edit_sequence.sequenceChanged.connect(self._on_sequence_changed)
        self._edit_sequence.setObjectName("sequence_capture")
        self._stack_hotkey.section_layout.addWidget(self._edit_sequence)

        # Modo Atalho — GridDoubleSpinBox: atraso, intervalo, aleatoriedade, repetições
        self._grid_hotkey_numbers = GridDoubleSpinBox(
            config={
                "atraso": {
                    "label": "Atraso inicial",
                    "description": "Tempo de espera antes de começar (s)",
                    "decimal": 1,
                    "default": self.DEFAULT_STARTUP_DELAY,
                    "suffix": "s",
                },
                "intervalo": {
                    "label": "Intervalo entre teclas",
                    "description": "Tempo base entre pressionar cada tecla (s). "
                                   "O valor final será intervalo + aleatório(0, aleatoriedade).",
                    "decimal": 2,
                    "default": self.DEFAULT_SEQUENCE_INTERVAL,
                    "suffix": "s",
                },
                "aleatoriedade": {
                    "label": "Aleatoriedade",
                    "description": "Fator aleatório adicionado ao intervalo (0 = desligado). "
                                   "Ex: intervalo=1, aleatoriedade=1 → delay entre 1.00 e 2.00s.",
                    "decimal": 2,
                    "default": 0.0,
                    "suffix": "s",
                },
                "repeticoes": {
                    "label": "Número de vezes",
                    "description": "Quantas vezes repetir a sequência inteira",
                    "decimal": 0,
                    "default": self.DEFAULT_SEQUENCE_REPEAT,
                },
            },
        )
        self._grid_hotkey_numbers.changed.connect(self._mark_dirty)
        self._grid_hotkey_numbers.setObjectName("grid_hotkey_numeric")
        self._stack_hotkey.section_layout.addWidget(self._grid_hotkey_numbers)

        # ── Stack: Modo Mouse ──────────────────────────────────────────
        self._stack_mouse = SectionPanel(object_name="stack_mouse")

        # MouseButtonCapture
        self._mouse_button_capture = MouseButtonCapture(
            default_button="left",
            label="Botão do mouse:",
        )
        self._mouse_button_capture.buttonChanged.connect(self._mark_dirty)
        self._stack_mouse.section_layout.addWidget(self._mouse_button_capture)

        # GridDoubleSpinBox para modo mouse
        self._grid_mouse_numbers = GridDoubleSpinBox(
            config={
                "atraso": {
                    "label": "Atraso inicial",
                    "description": "Tempo de espera antes de começar (s)",
                    "decimal": 1,
                    "default": self.DEFAULT_STARTUP_DELAY,
                    "suffix": "s",
                },
                "intervalo": {
                    "label": "Intervalo entre cliques",
                    "description": "Tempo entre cada clique (s)",
                    "decimal": 2,
                    "default": 0.04,
                    "suffix": "s",
                },
                "repeticoes": {
                    "label": "Número de cliques",
                    "description": "Quantos cliques por acionamento (0 = contínuo enquanto segurar)",
                    "decimal": 0,
                    "default": 1,
                    "min": 0,
                    "max": 99999,
                },
            },
        )
        self._grid_mouse_numbers.changed.connect(self._mark_dirty)
        self._grid_mouse_numbers.setObjectName("grid_mouse_numeric")
        self._stack_mouse.section_layout.addWidget(self._grid_mouse_numbers)

        # Adiciona stacks ao config group
        config_group.group_layout.addWidget(self._stack_text)
        config_group.group_layout.addWidget(self._stack_hotkey)
        config_group.group_layout.addWidget(self._stack_mouse)

        # ── Tecla de atalho (comum aos dois modos) ────────────────────
        self._edit_hotkey = HotkeyCaptureLine(
            default_key=self.DEFAULT_HOTKEY,
            label="Tecla gatilho:",
        )
        self._edit_hotkey.keyChanged.connect(self._mark_dirty)
        config_group.group_layout.addWidget(self._edit_hotkey)

        # ── Grid: Bloquear propagação ────────────────────────────────
        self._grid_suppress = GridCheckBox(
            config={
                "suppress": {
                    "label": "Bloquear propagação (suppress)",
                    "description": (
                        "Impede que a tecla de atalho seja transmitida "
                        "para outros programas. Ative se a tecla estiver "
                        "acionando comandos indesejados no app em foco."
                    ),
                    "default": True,
                },
            },
            num_columns=1,
        )
        self._grid_suppress.setObjectName("group_suppress")
        self._grid_suppress.changed.connect(self._mark_dirty)
        config_group.group_layout.addWidget(self._grid_suppress)

        self.main_layout.addWidget(config_group, 1)

    # ── Modo ──────────────────────────────────────────────────────────

    def _on_sequence_changed(self, keys: list[str]):
        """Quando a sequência de teclas muda, exibe no console."""
        if not keys:
            SignalManager.instance().console_message.emit(
                "HotkeyPlugin sequência limpa"
            )
        else:
            display = ", ".join(_to_display(k) for k in keys)
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin sequência ({len(keys)}): {display}"
            )
        self._mark_dirty()

    def _on_mode_changed(self, mode: str):
        """Atualiza visibilidade dos stacks conforme o modo."""
        self._update_mode_visibility()
        self._mark_dirty()

    def _update_mode_visibility(self):
        """Exibe/esconde os stacks conforme o modo selecionado."""
        mode = self._combo_mode.current_value
        self._stack_text.setVisible(mode == self.MODE_TEXT)
        self._stack_hotkey.setVisible(mode == self.MODE_HOTKEY)
        self._stack_mouse.setVisible(mode == self.MODE_MOUSE)

    # ── Ações ─────────────────────────────────────────────────────────

    def _on_executar(self):
        """Inicia ou para o worker."""
        if self._running:
            self._stop_worker()
        else:
            self._start_worker()

    def _start_worker(self):
        """Valida e registra o hook de teclado global."""
        mode = self._combo_mode.current_value

        # Validação conforme o modo
        if mode == self.MODE_MOUSE:
            button = self._mouse_button_capture.captured_button()
            if not button:
                MessageBox.show_warning(
                    "Selecione um botão do mouse.", title="Aviso"
                )
                return

            startup_delay = self._grid_mouse_numbers.get("atraso")
            interval_delay = self._grid_mouse_numbers.get("intervalo")
            repeat_count = int(self._grid_mouse_numbers.get("repeticoes"))

        if mode == self.MODE_TEXT:
            value = self._grid_text.get("valor").strip()
            if not value:
                MessageBox.show_warning("Valor não pode estar vazio.", title="Aviso")
                return

        hotkey = self._edit_hotkey.captured_key()
        if not hotkey:
            MessageBox.show_warning("Tecla gatilho não pode estar vazia.", title="Aviso")
            return

        if mode == self.MODE_HOTKEY:
            sequence = self._edit_sequence.captured_sequence()
            if not sequence:
                MessageBox.show_warning(
                    "Sequência de teclas não pode estar vazia. "
                    "Adicione pelo menos uma tecla.",
                    title="Aviso",
                )
                return

        suppress = bool(self._grid_suppress.all.get("suppress", True))

        # Fecha hooks anteriores se houver
        self._clean_hooks()

        # Reseta a barra de progresso
        SignalManager.instance().progress_update.emit(0.0)

        # Monta callback conforme o modo
        if mode == self.MODE_MOUSE:
            pass  # já tratado acima

        elif mode == self.MODE_TEXT:
            value = self._grid_text.get("valor").strip()
            startup_delay = self._grid_text_numbers.get("atraso")
            interval_delay = self._grid_text_numbers.get("intervalo")
        else:
            startup_delay = self._grid_hotkey_numbers.get("atraso")
            interval_delay = self._grid_hotkey_numbers.get("intervalo")
            aleatoriedade = self._grid_hotkey_numbers.get("aleatoriedade")
            repeat_count = int(self._grid_hotkey_numbers.get("repeticoes"))

        def type_value():
            """Callback chamado pela keyboard library na thread de hook."""
            if not self._running:
                return
            time.sleep(startup_delay)

            if mode == self.MODE_MOUSE:
                import pyautogui
                total_clicks = repeat_count
                interval = interval_delay
                continuous = (total_clicks == 0)
                count = 0
                while self._running:
                    if not continuous and count >= total_clicks:
                        break
                    pyautogui.click(button=button)
                    count += 1
                    if not continuous:
                        progress = (count / total_clicks) * 100.0
                        SignalManager.instance().progress_update.emit(progress)
                    time.sleep(interval)
                QTimer.singleShot(
                    0,
                    lambda: self._on_mouse_done(count, button, hotkey),
                )

            elif mode == self.MODE_TEXT:
                count = 0
                total_chars = len(value)
                for ch in value:
                    if not self._running:
                        break
                    try:
                        import pyautogui
                        pyautogui.typewrite(ch, interval=0)
                    except Exception:
                        break
                    count += 1
                    progress = (count / total_chars) * 100.0
                    SignalManager.instance().progress_update.emit(progress)
                    time.sleep(interval_delay)
                QTimer.singleShot(0, lambda: self._on_typed(count, hotkey))
            else:
                import pyautogui

                total_steps = repeat_count * len(sequence)
                step_index = 0

                for rep in range(repeat_count):
                    if not self._running:
                        break
                    for key_name in sequence:
                        if not self._running:
                            break
                        try:
                            display_name = _to_display(key_name)
                            SignalManager.instance().console_message.emit(
                                f"HotkeyPlugin pressionando: {display_name} "
                                f"(loop {rep + 1}/{repeat_count})"
                            )
                            if "+" in key_name.strip("+"):
                                parts = key_name.replace(" ", "").split("+")
                                pyautogui.hotkey(*parts)
                            else:
                                pyautogui.press(key_name)
                        except Exception as e:
                            self.logger.error(
                                "Erro ao pressionar tecla",
                                code="KEY_SEND_ERR",
                                key=key_name,
                                error=str(e),
                            )
                            SignalManager.instance().console_message.emit(
                                f"HotkeyPlugin erro ao pressionar {key_name}: {e}"
                            )
                            break
                        step_index += 1
                        progress = (step_index / total_steps) * 100.0
                        SignalManager.instance().progress_update.emit(progress)
                        actual_delay = interval_delay + random.uniform(0.0, aleatoriedade)
                        time.sleep(actual_delay)
                    if not self._running:
                        break

                QTimer.singleShot(
                    0,
                    lambda: self._on_sequence_done(repeat_count, len(sequence), hotkey),
                )

        try:
            import keyboard
            self._hotkey_handler = keyboard.add_hotkey(
                hotkey,
                type_value,
                suppress=suppress,
                trigger_on_release=False,
            )
        except ImportError as e:
            self.logger.error("Bibliotecas nao encontradas", code="IMPORT_ERR", error=str(e))
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin erro: {e}. Instale: pip install pyautogui keyboard"
            )
            SignalManager.instance().progress_update.emit(0.0)
            return
        except Exception as e:
            self.logger.error("Falha ao registrar hotkey", code="HOTKEY_ERR", error=str(e))
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin erro ao registrar hotkey: {e}"
            )
            SignalManager.instance().progress_update.emit(0.0)
            return

        self._running = True
        self._btns["executar"].setText("PARAR")
        self._set_inputs_enabled(False)
        self.save_prefs()

        SignalManager.instance().console_message.emit(
            f"HotkeyPlugin iniciado — modo {mode}, "
            f"tecla {hotkey.upper()}"
        )
        self.logger.info(
            "HotkeyPlugin iniciado",
            code="WORKER_START",
            mode=mode,
            hotkey=hotkey.upper(),
            startup_delay=startup_delay,
            suppress=suppress,
        )

    def _on_mouse_done(self, count: int, button: str, hotkey: str) -> None:
        """Recebe notificação na thread da UI após execução de cliques (modo mouse)."""
        if count > 0:
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin executou {count} cliques ({button}) "
                f"via tecla {hotkey.upper()}"
            )

    def _on_typed(self, count: int, hotkey: str) -> None:
        """Recebe notificação na thread da UI após digitação (modo texto)."""
        if count > 0:
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin digitou {count} caracteres (tecla {hotkey.upper()})"
            )

    def _on_sequence_done(self, repeats: int, keys_count: int, hotkey: str) -> None:
        """Recebe notificação na thread da UI após executar sequência (modo atalho)."""
        if repeats > 0:
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin executou {repeats}x sequência de {keys_count} teclas "
                f"(tecla {hotkey.upper()})"
            )

    def _stop_worker(self):
        """Remove o hook de teclado."""
        self._running = False
        self._clean_hooks()
        self._on_executar_finished()

    def _clean_hooks(self):
        """Remove hooks registrados."""
        try:
            import keyboard
            if self._hotkey_handler is not None:
                try:
                    keyboard.remove_hotkey(self._hotkey_handler)
                except Exception:
                    pass
                self._hotkey_handler = None
            keyboard.unhook_all()
        except ImportError:
            pass

    def _on_executar_finished(self):
        """Callback quando a execução termina."""
        self._btns["executar"].setText("EXECUTAR")
        self._set_inputs_enabled(True)
        SignalManager.instance().progress_update.emit(100.0)
        QTimer.singleShot(500, lambda: SignalManager.instance().progress_update.emit(0.0))

        SignalManager.instance().console_message.emit("HotkeyPlugin parado")
        self.logger.info("HotkeyPlugin parado", code="WORKER_STOP")

    def _set_inputs_enabled(self, enabled: bool):
        """Habilita/desabilita inputs durante execução."""
        self._grid_text.setEnabled(enabled)
        self._grid_text_numbers.setEnabled(enabled)
        self._edit_hotkey.setEnabled(enabled)
        self._edit_sequence.setEnabled(enabled)
        self._grid_hotkey_numbers.setEnabled(enabled)
        self._grid_suppress.setEnabled(enabled)
        self._combo_mode.setEnabled(enabled)
        self._grid_mouse_numbers.setEnabled(enabled)
        self._mouse_button_capture.setEnabled(enabled)
        self._stack_mouse.setEnabled(enabled)

    # ── Preferences ─────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Carrega preferências salvas e aplica nos widgets."""
        saved_mode = self.preferences.get("mode")
        if saved_mode is not None:
            self._combo_mode.current_value = saved_mode

        value = self.preferences.get("value")
        if value is not None:
            self._grid_text.set("valor", value, block_signals=True)

        hotkey = self.preferences.get("hotkey")
        if hotkey is not None:
            self._edit_hotkey.set_captured_key(hotkey)

        sequence = self.preferences.get("sequence")
        if sequence is not None and isinstance(sequence, list):
            self._edit_sequence.set_captured_sequence(sequence)

        seq_interval = self.preferences.get("seq_interval")
        if seq_interval is not None:
            self._grid_hotkey_numbers.set("intervalo", float(seq_interval), block_signals=True)

        aleatoriedade = self.preferences.get("aleatoriedade")
        if aleatoriedade is not None:
            self._grid_hotkey_numbers.set("aleatoriedade", float(aleatoriedade), block_signals=True)

        seq_repeat = self.preferences.get("seq_repeat")
        if seq_repeat is not None:
            self._grid_hotkey_numbers.set("repeticoes", float(seq_repeat), block_signals=True)

        atraso = self.preferences.get("atraso")
        if atraso is not None:
            self._grid_text_numbers.set("atraso", float(atraso), block_signals=True)
            self._grid_hotkey_numbers.set("atraso", float(atraso), block_signals=True)

        suppress = self.preferences.get("suppress")
        if suppress is not None:
            self._grid_suppress.set_all({"suppress": bool(suppress)})

        # ── Preferências do modo mouse ───────────────────────────────
        mouse_button = self.preferences.get("mouse_button")
        if mouse_button is not None:
            self._mouse_button_capture.set_captured_button(mouse_button)

        mouse_interval = self.preferences.get("mouse_interval")
        if mouse_interval is not None:
            self._grid_mouse_numbers.set("intervalo", float(mouse_interval), block_signals=True)

        mouse_repeat = self.preferences.get("mouse_repeat")
        if mouse_repeat is not None:
            self._grid_mouse_numbers.set("repeticoes", float(mouse_repeat), block_signals=True)

        # Sincroniza atraso do modo mouse com os demais modos
        if atraso is not None:
            self._grid_mouse_numbers.set("atraso", float(atraso), block_signals=True)

    def save_prefs(self) -> None:
        """Lê os widgets e persiste as preferências."""
        self.preferences["mode"] = self._combo_mode.current_value
        self.preferences["value"] = self._grid_text.get("valor")
        self.preferences["hotkey"] = self._edit_hotkey.captured_key()
        self.preferences["suppress"] = bool(
            self._grid_suppress.all.get("suppress", True)
        )

        vals = self._grid_hotkey_numbers.values
        text_vals = self._grid_text_numbers.values
        self.preferences["atraso"] = vals.get("atraso", self.DEFAULT_STARTUP_DELAY)
        self.preferences["text_intervalo"] = text_vals.get("intervalo", self.DEFAULT_INTERVAL_DELAY)
        self.preferences["seq_interval"] = vals.get("intervalo", self.DEFAULT_SEQUENCE_INTERVAL)
        self.preferences["aleatoriedade"] = vals.get("aleatoriedade", 0.0)
        self.preferences["seq_repeat"] = vals.get("repeticoes", self.DEFAULT_SEQUENCE_REPEAT)

        self.preferences["sequence"] = self._edit_sequence.captured_sequence()

        # ── Preferências do modo mouse ───────────────────────────────
        self.preferences["mouse_button"] = self._mouse_button_capture.captured_button()

        mouse_vals = self._grid_mouse_numbers.values
        self.preferences["mouse_interval"] = mouse_vals.get("intervalo", 0.04)
        self.preferences["mouse_repeat"] = mouse_vals.get("repeticoes", 1)

    def _collect_config_data(self) -> dict:
        """Coleta todos os parâmetros atuais do plugin em um dicionário."""
        hotkey_vals = self._grid_hotkey_numbers.values
        mouse_vals = self._grid_mouse_numbers.values
        return {
            "mode": self._combo_mode.current_value,
            "value": self._grid_text.get("valor"),
            "hotkey": self._edit_hotkey.captured_key(),
            "suppress": bool(self._grid_suppress.all.get("suppress", True)),
            "atraso": hotkey_vals.get("atraso", self.DEFAULT_STARTUP_DELAY),
            "intervalo": hotkey_vals.get("intervalo", self.DEFAULT_SEQUENCE_INTERVAL),
            "aleatoriedade": hotkey_vals.get("aleatoriedade", 0.0),
            "repeticoes": int(hotkey_vals.get("repeticoes", self.DEFAULT_SEQUENCE_REPEAT)),
            "sequence": self._edit_sequence.captured_sequence(),
            # ── Dados do modo mouse ──────────────────────────────────
            "mouse_button": self._mouse_button_capture.captured_button(),
            "mouse_interval": mouse_vals.get("intervalo", 0.04),
            "mouse_repeat": mouse_vals.get("repeticoes", 1),
        }

    def _apply_config_data(self, data: dict):
        """Aplica os parâmetros de um dicionário nos widgets do plugin."""
        mode = data.get("mode", self.MODE_TEXT)
        self._combo_mode.current_value = mode

        value = data.get("value")
        if value is not None:
            self._grid_text.set("valor", value, block_signals=True)

        hotkey = data.get("hotkey")
        if hotkey is not None:
            self._edit_hotkey.set_captured_key(hotkey)

        suppress = data.get("suppress")
        if suppress is not None:
            self._grid_suppress.set_all({"suppress": bool(suppress)})

        atraso = data.get("atraso")
        if atraso is not None:
            self._grid_text_numbers.set("atraso", float(atraso), block_signals=True)
            self._grid_hotkey_numbers.set("atraso", float(atraso), block_signals=True)

        intervalo = data.get("intervalo")
        if intervalo is not None:
            self._grid_hotkey_numbers.set("intervalo", float(intervalo), block_signals=True)

        aleatoriedade_val = data.get("aleatoriedade")
        if aleatoriedade_val is not None:
            self._grid_hotkey_numbers.set("aleatoriedade", float(aleatoriedade_val), block_signals=True)

        repeticoes = data.get("repeticoes")
        if repeticoes is not None:
            self._grid_hotkey_numbers.set("repeticoes", float(repeticoes), block_signals=True)

        sequence = data.get("sequence")
        if sequence is not None and isinstance(sequence, list):
            self._edit_sequence.set_captured_sequence(sequence)

        # ── Config do modo mouse ─────────────────────────────────────
        mouse_button = data.get("mouse_button")
        if mouse_button is not None:
            self._mouse_button_capture.set_captured_button(mouse_button)

        mouse_interval = data.get("mouse_interval")
        if mouse_interval is not None:
            self._grid_mouse_numbers.set("intervalo", float(mouse_interval), block_signals=True)

        mouse_repeat = data.get("mouse_repeat")
        if mouse_repeat is not None:
            self._grid_mouse_numbers.set("repeticoes", float(mouse_repeat), block_signals=True)

        # Sincroniza atraso do modo mouse
        if atraso is not None:
            self._grid_mouse_numbers.set("atraso", float(atraso), block_signals=True)

    # ── Salvar / Ler Config ────────────────────────────────────────

    def _on_salvar_config(self):
        """
        Salva a configuração atual em disco via ConfigSalvarDialog.
        """
        ConfigSalvarDialog.exec_save(
            config_dir=ExplorerUtils.get_plugin_config_dir("hotkey"),
            data=self._collect_config_data(),
            parent=self,
            logger=self.logger,
            console_message_fn=SignalManager.instance().console_message.emit,
            plugin_tag="HotkeyPlugin",
        )

    def _on_ler_config(self):
        """
        Carrega uma configuração do disco via ConfigCarregarDialog.
        """
        data = ConfigCarregarDialog.exec_load(
            config_dir=ExplorerUtils.get_plugin_config_dir("hotkey"),
            parent=self,
            logger=self.logger,
            console_message_fn=SignalManager.instance().console_message.emit,
            plugin_tag="HotkeyPlugin",
        )
        if data is not None:
            self._apply_config_data(data)
            self.save_prefs()

    # ── Dirty tracking ──────────────────────────────────────────────

    _dirty: bool = False

    def _mark_dirty(self) -> None:
        """Marca que as preferências precisam ser salvas."""
        self._dirty = True