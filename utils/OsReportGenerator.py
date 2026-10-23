# -*- coding: utf-8 -*-
"""
OsReportGenerator — Relatório da OS gerado a partir de um template Word
=======================================================================
Preenche o TEMPLATE Word (``core/template/MODELO_RELATORIO_OS.docx``) com os
valores recebidos e salva o relatório dentro da pasta da OS.

O template é a FONTE do layout: ele fica **pré-preenchido** com os campos no
formato ``{{chave}}`` e o gerador apenas troca cada campo pelo valor. Para mudar
o relatório (textos, ordem, tabelas), basta editar o ``.DOCX`` do template —
nenhuma alteração de código é necessária.

**Destino** (uma pasta por TIPO de relatório):

```
<pasta da OS>/14_RELATORIOS/<TIPO>/OS_<chave>_<TIPO>_<AAAAMMDDHHMMSS>.DOCX
```

O tipo e as pastas que ainda não existirem são criados na hora. Ex.:
``OS_220_Relatorio Geral Projeto_20261023134420.DOCX``.

A substituição cobre o corpo, as TABELAS (recursivamente, inclusive aninhadas) e
o cabeçalho/rodapé. Quando o Word divide um campo entre vários ``runs`` do mesmo
parágrafo, o texto é remontado antes da troca (preservando a formatação do
primeiro run).

Uso:
    from utils.OsReportGenerator import OsReportGenerator

    path = OsReportGenerator.generate(
        {"os": "169A", "cliente": "Fulano"},
        os_folder="C:/.../OS_169A_AGUA_VIVA",
        os_key="169A",
        tool_key=ToolKey.OS_TRACKER.value,
    )
    # path -> ".../OS_169A_AGUA_VIVA/14_RELATORIOS/Relatorio Geral Projeto/
    #          OS_169A_Relatorio Geral Projeto_20261023134420.DOCX"
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils


class OsReportGenerator(BaseUtil):
    """Gera o relatório Word de uma OS a partir do template pré-preenchido."""

    # Template com os campos ``{{chave}}`` (editável — é a fonte do layout).
    TEMPLATE_PATH: Path = (
        Path(__file__).resolve().parent.parent
        / "core" / "template" / "MODELO_RELATORIO_OS.docx"
    )
    # Pasta dos relatórios na estrutura do projeto (ver PROJECT_STRUCTURE).
    REPORTS_FOLDER = "14_RELATORIOS"
    # TIPO do relatório: subpasta criada em 14_RELATORIOS e sufixo do arquivo.
    REPORT_TYPE = "Relatorio Geral Projeto"
    OUTPUT_SUFFIX = ".DOCX"
    FILE_PREFIX = "OS"
    # Pasta de fallback (temp do sistema) quando a OS não tem pasta em disco.
    TEMP_SUBFOLDER = f"aetheris/{REPORTS_FOLDER}/{REPORT_TYPE}"
    _TOKEN = re.compile(r"\{\{\s*([A-Za-z0-9_.]+)\s*\}\}")
    _UNSAFE = re.compile(r'[<>:"/\\|?*]')

    # ── API pública ─────────────────────────────────────────────────

    @classmethod
    def generate(
        cls,
        values: Dict[str, Any],
        os_folder: str | Path = "",
        os_key: str = "",
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> str:
        """Preenche o template e salva o relatório na pasta da OS.

        Args:
            values: Mapa ``chave -> valor`` dos campos do template.
            os_folder: Pasta da OS (destino: ``14_RELATORIOS/<TIPO>``).
            os_key: Chave da OS (entra no nome do arquivo).
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho absoluto do ``.DOCX`` gerado.

        Raises:
            FileNotFoundError: se o template não existir.
        """
        logger = cls._get_logger(tool_key, "OsReportGenerator")
        template = Path(cls.TEMPLATE_PATH)
        if not template.exists():
            logger.error(
                "Template do relatório não encontrado",
                code="OSREP_TEMPLATE_MISSING",
                path=str(template),
            )
            raise FileNotFoundError(f"Template do relatório não encontrado: {template}")

        document = Document(str(template))
        replaced = cls._replace(document, cls._normalize(values))
        target = cls.report_path(os_folder, os_key, tool_key)
        document.save(str(target))
        logger.info(
            "Relatório da OS gerado",
            code="OSREP_GENERATED",
            path=str(target),
            fields=replaced,
        )
        return str(target)

    # ── Substituição dos campos ─────────────────────────────────────

    @classmethod
    def _replace(cls, document: Document, values: Dict[str, str]) -> int:
        """Troca os campos em todo o documento e devolve quantos foram trocados."""
        total = 0
        for paragraph in cls._paragraphs(document):
            total += cls._replace_paragraph(paragraph, values)
        return total

    @classmethod
    def _replace_paragraph(
        cls, paragraph: Paragraph, values: Dict[str, str]
    ) -> int:
        """Troca os campos de UM parágrafo (remontando os runs quando necessário)."""
        text = paragraph.text
        if "{{" not in text:
            return 0

        new_text, replaced = cls._TOKEN.subn(
            lambda match: values.get(match.group(1), match.group(0)), text
        )
        if not replaced:
            return 0

        cls._write_paragraph(paragraph, new_text)
        return replaced

    @staticmethod
    def _write_paragraph(paragraph: Paragraph, text: str) -> None:
        """Escreve o texto no primeiro run e limpa os demais (mantém o estilo)."""
        runs = paragraph.runs
        if not runs:
            paragraph.add_run(text)
            return
        runs[0].text = text
        for run in runs[1:]:
            run.text = ""

    # ── Varredura do documento ──────────────────────────────────────

    @classmethod
    def _paragraphs(cls, document: Document) -> Iterable[Paragraph]:
        """Percorre os parágrafos do corpo, das tabelas e do cabeçalho/rodapé."""
        yield from document.paragraphs
        for table in document.tables:
            yield from cls._table_paragraphs(table)
        for section in document.sections:
            for container in (section.header, section.footer):
                yield from container.paragraphs
                for table in container.tables:
                    yield from cls._table_paragraphs(table)

    @classmethod
    def _table_paragraphs(cls, table: Table) -> Iterable[Paragraph]:
        """Percorre recursivamente os parágrafos de uma tabela."""
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs
                for nested in cell.tables:
                    yield from cls._table_paragraphs(nested)

    # ── Destino ─────────────────────────────────────────────────────

    @classmethod
    def report_folder(
        cls,
        os_folder: str | Path | None,
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Path:
        """Pasta do relatório: ``<pasta da OS>/14_RELATORIOS/<TIPO>`` (garantida).

        Sem pasta de OS (registro sem pasta em disco), usa o temp do sistema.
        """
        if not os_folder:
            return Path(
                ExplorerUtils.get_system_temp_dir(
                    cls.TEMP_SUBFOLDER, tool_key=tool_key
                )
            )
        folder = Path(os_folder) / cls.REPORTS_FOLDER / cls._safe_name(cls.REPORT_TYPE)
        return Path(ExplorerUtils.ensure_directory(str(folder), tool_key=tool_key))

    @classmethod
    def report_path(
        cls,
        os_folder: str | Path | None,
        os_key: str = "",
        tool_key: str = ToolKey.OS_TRACKER.value,
    ) -> Path:
        """Caminho do relatório: ``OS_<chave>_<TIPO>_<AAAAMMDDHHMMSS>.DOCX``."""
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        parts = (
            cls.FILE_PREFIX,
            cls._safe_name(os_key),
            cls._safe_name(cls.REPORT_TYPE),
            stamp,
        )
        name = "_".join(part for part in parts if part)
        return cls.report_folder(os_folder, tool_key) / f"{name}{cls.OUTPUT_SUFFIX}"

    @classmethod
    def _safe_name(cls, name: str) -> str:
        """Sanitiza o nome do arquivo para uso no Windows."""
        return cls._UNSAFE.sub("_", str(name or "")).strip()

    @staticmethod
    def _normalize(values: Dict[str, Any]) -> Dict[str, str]:
        """Converte os valores para texto (``None`` vira string vazia)."""
        return {
            str(key): ("" if value is None else str(value))
            for key, value in values.items()
        }
