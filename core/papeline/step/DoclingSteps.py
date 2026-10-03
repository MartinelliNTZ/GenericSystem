# -*- coding: utf-8 -*-
"""
DoclingSteps — Concrete steps for Docling document conversion pipeline
========================================================================
Steps that compose a complete document conversion pipeline via Docling.

Pipeline:
    1. DoclingConvertStep → Converts document to Markdown
    2. DoclingSaveStep → Saves Markdown to .md file
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseTask import BaseTask
from ..BaseStep import BaseStep
from ..task.DoclingPipelineTask import DoclingPipelineTask


class DoclingConvertStep(BaseStep):
    """
    Step that converts a document to Markdown via Docling.

    Context requires:
        - input_path: Path to document to convert

    Context produces:
        - results["markdown"]: Generated Markdown content
        - results["output_name"]: Output file name
    """
    def __init__(self, columnar: bool = False, manual_columns: int = 0):
        super().__init__()
        self._columnar = columnar
        self._manual_columns = manual_columns

    def name(self) -> str:
        return "docling_convert"

    def create_task(self, context: ExecutionContext) -> DoclingPipelineTask:
        return DoclingPipelineTask(
            file_path=str(context.input_path),
            columnar=self._columnar,
            manual_columns=self._manual_columns,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set_result("markdown", result.get("markdown", ""))
            context.set_result("output_name", result.get("output_name", ""))


class DoclingSaveStep(BaseStep):
    """
    Step that saves the generated Markdown to a .md file on disk.

    Context requires:
        - results["markdown"]: Markdown content (produced by DoclingConvertStep)
        - results["output_dir"]: Output directory

    Context produces:
        - results["saved_path"]: Path to saved .md file
    """
    def name(self) -> str:
        return "docling_save"

    def should_run(self, context: ExecutionContext) -> bool:
        return bool(context.get_result("markdown"))

    def create_task(self, context: ExecutionContext) -> None:
        return None  # Synchronous

    def run_inline(self, context: ExecutionContext) -> Optional[str]:
        markdown = str(context.get_result("markdown", ""))
        if not markdown.strip():
            return None

        output_dir = Path(str(context.get_result("output_dir", ".")))
        output_dir.mkdir(parents=True, exist_ok=True)

        output_name = str(context.get_result("output_name", "output.md"))
        output_path = output_dir / output_name

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            return str(output_path)
        except Exception as e:
            context.add_error(e)
            return None

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if result:
            context.set_result("saved_path", result)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)