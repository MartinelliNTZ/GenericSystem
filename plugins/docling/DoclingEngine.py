# -*- coding: utf-8 -*-
"""
DoclingEngine — Abstração do Docling para conversão de documentos para Markdown
=================================================================================
Encapsula DocumentConverter, fallback de colunas e logging.
Sem dependências Qt — usa apenas LogUtils.

Uso:
    from plugins.docling.DoclingEngine import DoclingEngine

    md = DoclingEngine.convert(
        file_path="documento.pdf",
        columnar=True,
        manual_columns=0,
        tool_key="Docling",
    )
"""

from __future__ import annotations

from pathlib import Path

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey


class DoclingEngine:
    """
    Métodos estáticos para conversão de documentos via Docling.
    """

    @staticmethod
    def convert(
        file_path: str,
        *,
        columnar: bool = False,
        manual_columns: int = 0,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Converte um documento para Markdown.

        Args:
            file_path: Caminho do arquivo a converter.
            columnar: Se True, tenta layout multi-coluna.
            manual_columns: 0 = auto, 2-6 = forçar colunas.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Markdown como string.

        Raises:
            FileNotFoundError: Se arquivo não existe.
            RuntimeError: Se a conversão falhar.
        """
        logger = LogUtils(tool=tool_key, class_name="DoclingEngine")
        path = Path(file_path)

        if not path.is_file():
            msg = f"Arquivo não encontrado: {file_path}"
            logger.error(msg, code="FILE_NOT_FOUND", path=file_path)
            raise FileNotFoundError(msg)

        logger.info(
            "Iniciando conversão",
            code="CONVERT_START",
            file=file_path,
            columnar=columnar,
            manual_columns=manual_columns,
        )

        try:
            converter = DoclingEngine._build_converter(columnar=columnar)
            logger.info("Converter criado", code="CONVERTER_READY")

            result = converter.convert(str(path))
            doc = result.document

            # Tenta layout multi-coluna se solicitado
            if columnar:
                try:
                    from utils.MdManager import MdManager

                    col_md = MdManager.export_by_columns(
                        doc,
                        page_no=0,
                        manual_columns=manual_columns,
                    )
                    if col_md:
                        logger.info(
                            "Markdown multi-coluna gerado",
                            code="COLUMN_DONE",
                        )
                        return col_md
                    logger.info(
                        "Fallback para markdown padrão (colunas insuficientes)",
                        code="COLUMN_FALLBACK",
                    )
                except Exception as e:
                    logger.warning(
                        "Erro no layout colunas, usando padrão",
                        code="COLUMN_ERR",
                        error=str(e),
                    )

            # Exportação padrão
            md = doc.export_to_markdown(traverse_pictures=True)
            logger.info("Conversão concluída", code="CONVERT_DONE")
            return md

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Falha na conversão",
                code="CONVERT_ERR",
                error=str(e),
                file=file_path,
            )
            raise RuntimeError(f"Falha na conversão: {e}") from e

    # ══════════════════════════════════════════════════════════════════
    # Métodos Internos
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _build_converter(*, columnar: bool = False):
        """
        Cria e retorna um DocumentConverter configurado.
        Se columnar=True, usa layout Egret para melhor detecção multi-coluna.
        """
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_EGRET_LARGE
        from docling.datamodel.pipeline_options import (
            LayoutOptions,
            PdfPipelineOptions,
        )
        from docling.document_converter import (
            DocumentConverter,
            ImageFormatOption,
            PdfFormatOption,
        )

        if not columnar:
            return DocumentConverter()

        pipe = PdfPipelineOptions(
            layout_options=LayoutOptions(
                model_spec=DOCLING_LAYOUT_EGRET_LARGE
            ),
            images_scale=1.5,
        )
        return DocumentConverter(
            format_options={
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipe),
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipe),
            }
        )