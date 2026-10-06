# -*- coding: utf-8 -*-
"""
FirebaseWorker — Executor assíncrono de operações Firebase
==========================================================
Herda de QThread e executa tarefas de I/O em background para evitar
bloqueio da interface gráfica (PySide6). Emite sinais de resultado e falha.
"""

from __future__ import annotations

from typing import Any, Callable
from PySide6.QtCore import QThread, Signal

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class FirebaseWorker(QThread):
    """Worker assíncrono para operações de rede com Firebase."""

    finished_with_result: Signal = Signal(object)
    failed: Signal = Signal(str)
    progress_changed: Signal = Signal(float)

    def __init__(
        self,
        task_fn: Callable[..., Any],
        *args: Any,
        parent=None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        self._task_fn = task_fn
        self._args = args
        self._kwargs = kwargs
        self._logger = BaseUtil._get_logger(ToolKey.FIREBASE.value, "FirebaseWorker")

    def run(self) -> None:
        """Executa a função de tarefa em background."""
        try:
            # Injeta progress_cb se a função esperar
            if "progress_cb" in self._task_fn.__code__.co_varnames:
                self._kwargs["progress_cb"] = self._emit_progress

            res = self._task_fn(*self._args, **self._kwargs)
            self.finished_with_result.emit(res)
        except Exception as e:
            self._logger.error("Falha na execução do worker Firebase", code="FB_WORKER_ERR", error=str(e))
            self.failed.emit(str(e))

    def _emit_progress(self, val: float) -> None:
        """Emite sinal de progresso para a UI."""
        self.progress_changed.emit(val)
