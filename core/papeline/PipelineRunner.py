# -*- coding: utf-8 -*-
"""
PipelineRunner — Executes AsyncPipelineEngine in QThread without freezing UI
==============================================================================
QThread wrapper that calls engine.start_non_blocking() in background.
Provides Qt signals for plugins to connect.

Creates an internal ResourceGovernor automatically to monitor
and limit RAM usage, preventing OOM. The plugin doesn't need to know
about the governor's existence.

Usage in plugin:
    runner = PipelineRunner(
        steps=[DoclingConvertStep(columnar=True)],
        context=input_path="/path/to/file",
        parent=self,
    )
    runner.start()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal

from core.governor.RamLimitPolicy import RamLimitPolicy, RamLimitMode
from core.governor.CpuGovernor import CpuGovernor
from core.governor.ResourceGovernor import ResourceGovernor
from .ExecutionContext import ExecutionContext
from .BaseStep import BaseStep
from .AsyncPipelineEngine import AsyncPipelineEngine


class PipelineRunner(QThread):
    """
    Executes a pipeline in QThread, without freezing the UI.

    Creates an internal ResourceGovernor with default policy
    (GLOBAL 90%) that monitors RAM and can block execution
    if resources are insufficient.

    Signals:
        finished_ok(object): ExecutionContext on successful completion.
        failed(str): Error message.
    """

    finished_ok = Signal(object)  # ExecutionContext
    failed = Signal(str)

    # Default governor policy
    _DEFAULT_MODE = RamLimitMode.GLOBAL
    _DEFAULT_FRACTION = 0.90

    def __init__(
        self,
        steps: List[BaseStep],
        *,
        context: Optional[Dict[str, Any]] = None,
        parent=None,
        governor: Optional[ResourceGovernor] = None,
        governor_mode: RamLimitMode = _DEFAULT_MODE,
        governor_fraction: float = _DEFAULT_FRACTION,
        **kwargs,
    ):
        super().__init__(parent)
        self._steps = steps
        # Support both dict context and keyword arguments
        ctx_data = context or {}
        ctx_data.update(kwargs)
        self._context_kwargs = ctx_data
        self._engine: AsyncPipelineEngine | None = None
        self._governor: Optional[ResourceGovernor] = governor
        self._governor_mode = governor_mode
        self._governor_fraction = governor_fraction

    @property
    def engine(self) -> AsyncPipelineEngine | None:
        return self._engine

    def cancel(self) -> None:
        """
        Cancels the running pipeline execution.
        Delegates to AsyncPipelineEngine.cancel() which does cooperative
        cancellation (marks flag + cancels current task).
        """
        if self._engine is not None:
            self._engine.cancel()

    def run(self) -> None:
        """Executes the pipeline in background thread."""
        ctx = ExecutionContext(**self._context_kwargs)

        # Create ResourceGovernor (custom or default GLOBAL 90%)
        if self._governor is None:
            self._governor = ResourceGovernor(
                policy=RamLimitPolicy(
                    mode=self._governor_mode,
                    fraction=self._governor_fraction,
                ),
            )

        # Store governor reference for tasks/steps
        ctx._governor = self._governor
        ctx._cpu_governor = CpuGovernor

        self._engine = AsyncPipelineEngine(
            steps=self._steps,
            context=ctx,
            on_finished=lambda c: self.finished_ok.emit(c),
            on_error=lambda errors: self.failed.emit(
                str(errors[-1] if errors else "Unknown error")
            ),
            governor=self._governor,
        )
        self._engine.start_non_blocking()

        # Keep thread alive until pipeline finishes
        while self._engine.is_running:
            self.msleep(50)

        self._engine = None
        self._governor = None