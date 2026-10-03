# -*- coding: utf-8 -*-
"""
DoclingPipelineTask — Task para conversão Docling no padrão BaseTask
=====================================================================
Única classe para conversão Docling. Usada tanto na pipeline assíncrona
quanto diretamente pelo DoclingPlugin (via thread própria do pipeline engine).

Uso na pipeline:
    class DoclingConvertStep(BaseStep):
        def create_task(self, context):
            return DoclingPipelineTask(...)
"""

from __future__ import annotations

from pathlib import Path

from ..BaseTask import BaseTask


class DoclingPipelineTask(BaseTask):
    """
    Task para conversão de documentos via Docling.
    Herda de BaseTask para uso no sistema de pipeline assíncrono.

    Args:
        file_path: Caminho do arquivo a converter.
        columnar: Se True, preserva layout colunar.
        manual_columns: Número manual de colunas (0 = automático).
    """
    def __init__(
        self,
        file_path: str,
        *,
        columnar: bool = False,
        manual_columns: int = 0,
    ):
        super().__init__(description=f"Converter: {Path(file_path).name}")
        self._file_path = file_path
        self._columnar = columnar
        self._manual_columns = manual_columns

    # ── BaseTask ─────────────────────────────────────────────────────

    def _run(self) -> bool:
        """Executa a conversão Docling em background."""
        try:
            from plugins.docling.DoclingEngine import DoclingEngine

            md = DoclingEngine.convert(
                self._file_path,
                columnar=self._columnar,
                manual_columns=self._manual_columns,
                tool_key="DoclingPipeline",
            )
            self.result = {
                "path": self._file_path,
                "markdown": md,
                "output_name": Path(self._file_path).stem + ".md",
            }
            return True
        except FileNotFoundError as e:
            self.exception = e
            return False
        except RuntimeError as e:
            self.exception = e
            return False
        except MemoryError as e:
            self.exception = RuntimeError(f"Memória insuficiente: {e}")
            return False
        except Exception as e:
            self.exception = RuntimeError(f"Erro inesperado: {e}")
            return False