# -*- coding: utf-8 -*-
"""
AsyncPipelineEngine — Orchestrator for sequential step execution
==================================================================
Manages sequential execution of steps, controlling initialization,
success/error callbacks and cancellation.

Two execution modes:
  - Blocking (default): uses thread.join(), suitable for CLI/tests
  - Non-blocking: via PipelineRunner, uses QThread + callbacks
                  without freezing the UI (suitable for Qt plugins)
"""

from __future__ import annotations

import threading
from typing import Any, Callable, List, Optional

from core.governor.ResourceGovernor import ResourceGovernor
from .ExecutionContext import ExecutionContext
from .BaseStep import BaseStep
from .BaseTask import BaseTask


class AsyncPipelineEngine:
    """
    Main orchestrator for the async pipeline.

    Args:
        steps: List of steps to execute sequentially.
        context: Shared ExecutionContext.
        on_finished: Optional callback when pipeline finishes successfully.
        on_error: Optional callback when an error occurs.
        on_cancelled: Optional callback when pipeline is cancelled.
    """
    def __init__(
        self,
        steps: List[BaseStep],
        context: ExecutionContext,
        *,
        on_finished: Optional[Callable[[ExecutionContext], None]] = None,
        on_error: Optional[Callable[[List[Exception]], None]] = None,
        on_cancelled: Optional[Callable[[ExecutionContext], None]] = None,
        governor: Optional[ResourceGovernor] = None,
    ):
        self._steps = steps
        self._context = context
        self._on_finished = on_finished
        self._on_error = on_error
        self._on_cancelled = on_cancelled

        self._current_index: int = 0
        self._current_task: Optional[BaseTask] = None
        self._is_running: bool = False
        self._is_cancelled: bool = False
        self._lock = threading.Lock()
        self._governor = governor

    # ── Properties ───────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def context(self) -> ExecutionContext:
        return self._context

    # ── Start ────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Starts the pipeline in BLOCKING mode.
        Each task runs in a separate thread, but the engine waits
        with join(). Suitable for CLI, tests and scripts.
        """
        if self._is_running:
            raise RuntimeError("Pipeline is already running.")

        self._is_running = True
        self._current_index = 0
        self._is_cancelled = False
        self._run_loop(blocking=True)

    def start_non_blocking(self) -> None:
        """
        Starts the pipeline in NON-BLOCKING mode.
        The engine does NOT join() — tasks fire callbacks
        and the pipeline advances automatically.
        Use with PipelineRunner to run in QThread.
        """
        if self._is_running:
            raise RuntimeError("Pipeline is already running.")

        self._is_running = True
        self._current_index = 0
        self._is_cancelled = False
        self._run_loop(blocking=False)

    # ── Main loop ────────────────────────────────────────────────

    def _run_loop(self, blocking: bool) -> None:
        """
        Executes steps sequentially.

        Args:
            blocking: If True, uses thread.join() (blocks).
                      If False, callbacks trigger automatic advancement.
        """
        while self._is_running and not self._is_cancelled:
            # Check cancellation
            if self._context.is_cancelled:
                self._finish_cancelled()
                return

            # Check resources (governor) — light check without estimated_ram
            if self._governor is not None and not self._governor.check_during_execution():
                    self._context.add_error(RuntimeError("Insufficient memory"))
                    self._finish_error()
                    return

            # Check if all steps are done
            if self._current_index >= len(self._steps):
                self._finish_success()
                return

            step = self._steps[self._current_index]

            # If step has custom input_path, override in context
            custom_path = getattr(step, "_custom_input_path", None)
            if custom_path:
                self._context.input_path = custom_path

            # Check if step should run
            if not step.should_run(self._context):
                self._current_index += 1
                continue

            try:
                task = step.create_task(self._context)

                if task is None:
                    # Synchronous inline step
                    result = step.run_inline(self._context)
                    if result is not None or True:
                        try:
                            step.on_success(self._context, result)
                            self._current_index += 1
                            continue
                        except Exception as e:
                            self._handle_task_error(step, e)
                            return
                    else:
                        raise RuntimeError(
                            f"Step '{step.name()}' returned None from create_task() "
                            f"and does not implement run_inline()."
                        )

                # Async task
                self._current_task = task
                task.on_success = lambda result: self._handle_task_success(step, result)
                task.on_error = lambda exc: self._handle_task_error(step, exc)

                if blocking:
                    # Blocking mode: execute and wait
                    success = task.run()
                    task.finished(success)
                else:
                    # Non-blocking mode: fire thread and return
                    self._run_task_non_blocking(task)
                    return  # Exit while — callbacks resume

            except Exception as e:
                self._handle_task_error(step, e)
                return

    def _run_task_non_blocking(self, task: BaseTask) -> None:
        """
        Fires task in a separate thread WITHOUT doing join().
        When the thread finishes, calls task.finished() which
        fires on_success/on_error, which advance the pipeline.
        """
        def _worker(t: BaseTask, engine: AsyncPipelineEngine):
            try:
                success = t.run()
                t.finished(success)
            except Exception:
                pass

        thread = threading.Thread(target=_worker, args=(task, self), daemon=True,
                                  name=f"task-{task.description}")
        thread.start()

    # ── Task callbacks (used in non-blocking mode) ───────────────

    def _handle_task_success(self, step: BaseStep, result: Any) -> None:
        """Callback when a task finishes successfully."""
        try:
            step.on_success(self._context, result)
            self._current_index += 1
            self._current_task = None
            # Continue the loop
            self._run_loop(blocking=False)
        except Exception as e:
            self._handle_task_error(step, e)

    def _handle_task_error(self, step: Optional[BaseStep], exception: Exception) -> None:
        """Callback when a task fails."""
        if step is not None:
            step.on_error(self._context, exception)

        self._context.add_error(exception)
        self._current_task = None
        self._finish_error()

    # ── Finalizations ────────────────────────────────────────────

    def _finish_success(self) -> None:
        """Pipeline completed successfully."""
        self._is_running = False
        self._current_task = None

        if self._on_finished:
            self._on_finished(self._context)

    def _finish_error(self) -> None:
        """Pipeline interrupted by error."""
        self._is_running = False
        self._current_task = None

        if self._on_error:
            self._on_error(self._context.errors)

    def _finish_cancelled(self) -> None:
        """Pipeline cancelled by user."""
        self._is_running = False
        self._current_task = None

        if self._on_cancelled:
            self._on_cancelled(self._context)

    # ── Cancellation ─────────────────────────────────────────────

    def cancel(self) -> None:
        """Cancels pipeline execution (cooperative cancellation)."""
        self._is_cancelled = True
        self._context.cancel()

        if self._current_task is not None:
            self._current_task.cancel()

    def __repr__(self) -> str:
        return (
            f"<AsyncPipelineEngine "
            f"steps={len(self._steps)}, "
            f"current={self._current_index}, "
            f"running={self._is_running}, "
            f"cancelled={self._is_cancelled}>"
        )