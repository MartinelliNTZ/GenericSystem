# -*- coding: utf-8 -*-
"""
ExecutionContext — Shared state between pipeline steps
=========================================================
Container that allows steps to share data without direct coupling.
Also carries cancellation and error state.

Canonical attributes (direct access):
    context.input_path = "/path/to/data"
    context.output_path = "/path/to/output"
    context.tool_key = "my_tool"
    context.files = ["file1.las", "file2.las"]

Step results (dict access for flexibility):
    context.results["idw_result"] = {...}
    context.results["split_result"] = {...}
"""

from __future__ import annotations

from typing import Any


class ExecutionContext:
    """
    Shared state container between all pipeline steps.

    Canonical attributes (direct access):
        input_path: str           — Input directory with files to process
        output_path: str          — Base directory to save results
        files: list[str] | None   — Specific file list (None = all in input_path)
        tool_key: str             — ToolKey for logging
        errors: list[Exception]   — Error accumulator
        is_cancelled: bool        — Cancellation flag
        results: dict             — Step results storage (key: step name)
    """

    input_path: str = ""
    """Input directory with files to process."""

    output_path: str = ""
    """Base directory where results will be saved."""

    files: list[str] | None = None
    """Specific file list to process. None = all files in input_path."""

    tool_key: str = ""
    """ToolKey for logging."""

    def __init__(self, **kwargs):
        self.errors: list[Exception] = []
        self.is_cancelled: bool = False
        self.results: dict[str, Any] = {}

        # Set canonical attributes from keyword arguments
        for key in ("input_path", "output_path", "files", "tool_key"):
            if key in kwargs:
                setattr(self, key, kwargs[key])

    def set_result(self, key: str, value: Any) -> None:
        """Stores a step result."""
        self.results[key] = value

    def get_result(self, key: str, default: Any = None) -> Any:
        """Retrieves a step result."""
        return self.results.get(key, default)

    # ── Errors ────────────────────────────────────────────────────

    def add_error(self, exc: Exception) -> None:
        """Adds error to the error list."""
        self.errors.append(exc)

    def add_errors(self, excs: list[Exception]) -> None:
        """Adds multiple errors to the error list."""
        self.errors.extend(excs)

    def has_errors(self) -> bool:
        """True if there were any errors."""
        return len(self.errors) > 0

    # ── Cancellation ──────────────────────────────────────────────

    def cancel(self) -> None:
        """Marks context as cancelled."""
        self.is_cancelled = True

    # ── Reset ─────────────────────────────────────────────────────

    def clear(self) -> None:
        """Resets all state."""
        self.input_path = ""
        self.output_path = ""
        self.files = None
        self.tool_key = ""
        self.errors.clear()
        self.is_cancelled = False
        self.results.clear()

    def __repr__(self) -> str:
        n_files = len(self.files) if self.files else 0
        return (
            f"<ExecutionContext "
            f"input_path='{self.input_path}', "
            f"output_path='{self.output_path}', "
            f"files={n_files}, "
            f"results={len(self.results)} keys, "
            f"errors={len(self.errors)}, "
            f"cancelled={self.is_cancelled}>"
        )