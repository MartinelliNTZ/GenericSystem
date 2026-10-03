# -*- coding: utf-8 -*-
"""
BaseStep — Abstract contract that defines a pipeline step
============================================================
Each pipeline step implements this contract.
The step can either execute an async task (via create_task) or
execute synchronously inline (via run_inline).

New attributes:
    subfolder: str     — Output subfolder name (e.g. 'lascheck', 'lasblackfilter')
    advance_input: bool — If True, automatically advances input_path in on_success()

New methods:
    advance_input(context)   — Updates input_path to point to step's output subfolder
    resolve_files(context, *extensions) — Returns list of files to process
    output_subdir(context)    — Returns full output subfolder path, creates if needed

Required methods:
    name() -> str
    create_task(context) -> BaseTask | None
    on_success(context, result) -> None

Optional methods:
    should_run(context) -> bool
    on_error(context, exception) -> None
    rollback(context) -> None
    run_inline(context) -> Any
"""

from __future__ import annotations

import glob as _glob
import os as _os
from abc import ABC, abstractmethod
from typing import Any, Optional

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from .ExecutionContext import ExecutionContext
from .BaseTask import BaseTask


class BaseStep(ABC):
    """Contract that defines a pipeline step."""

    # ── Step configuration attributes ──────────────────────────
    subfolder: str = ""
    """Output subfolder name (e.g. 'lascheck', 'lasblackfilter').
    Used to create output_path/subfolder/ automatically."""

    _advance_input: bool = True
    """
    If True (default): step TRANSFORMS data -> calls advance_input() in on_success()
    If False: step only ANALYZES -> does NOT call advance_input()
    """

    # ── Logger ─────────────────────────────────────────────────

    def get_logger(self, context: ExecutionContext) -> LogUtils:
        """
        Returns a LogUtils configured with the context's tool_key.
        The class_name used is the concrete step's class name.
        """
        tool_key = context.tool_key or ToolKey.UNTRACEABLE.value
        return LogUtils(tool=tool_key, class_name=self.__class__.__name__)

    # ── Step flow methods ──────────────────────────────────────

    def advance_input(self, context: ExecutionContext) -> None:
        """
        Updates input_path to point to the step's output subfolder.
        Called automatically in on_success() if advance_input == True.
        """
        if self.subfolder:
            context.input_path = _os.path.join(context.output_path, self.subfolder)

    def resolve_files(self, context: ExecutionContext, *extensions: str) -> list[str]:
        """
        Returns the list of files to process.
        - If context.files is set, returns context.files
        - Otherwise, lists all files with given extensions in context.input_path
        """
        if context.files is not None:
            return context.files
        files = []
        for ext in extensions:
            pattern = _os.path.join(context.input_path, f"*{ext}")
            files.extend(_glob.glob(pattern))
        return sorted(files)

    def output_subdir(self, context: ExecutionContext) -> str:
        """
        Returns the full output subfolder path.
        E.g.: output_path + "/" + subfolder
        Creates the folder if it doesn't exist.
        """
        if not self.subfolder:
            return context.output_path
        subdir = _os.path.join(context.output_path, self.subfolder)
        _os.makedirs(subdir, exist_ok=True)
        return subdir

    # ── Required abstract methods ──────────────────────────────

    @abstractmethod
    def name(self) -> str:
        """Unique identifier for logs/debug."""
        ...

    @abstractmethod
    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """
        Creates and returns a BaseTask instance for async work.
        Can return None if the step executes inline via run_inline().
        """
        ...

    @abstractmethod
    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """
        Callback executed after the task finishes successfully.
        Default: if advance_input == True, advances input_path.
        Override to map task results to context.
        """
        if self._advance_input:
            self.advance_input(context)

    # ── Optional methods ───────────────────────────────────────

    def should_run(self, context: ExecutionContext) -> bool:
        """
        If returns False, the step is skipped automatically.
        Useful for conditional steps.
        """
        return True

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        """
        Step-specific error handling before pipeline fails.
        Optional - default implementation is empty.
        """
        pass

    def rollback(self, context: ExecutionContext) -> None:
        """
        Logic to undo changes in case of error.
        Not called automatically - up to the implementer.
        """
        pass

    def run_inline(self, context: ExecutionContext) -> Optional[Any]:
        """
        Synchronous inline execution when create_task() returns None.
        If not implemented, the pipeline raises RuntimeError when
        create_task() returns None and there's no run_inline().
        """
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name()}'>"