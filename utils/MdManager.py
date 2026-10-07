# -*- coding: utf-8 -*-
"""
MdManager — Exportação de DoclingDocument para Markdown multi-coluna
====================================================================
Reconstrói o Markdown de um ``DoclingDocument`` respeitando a leitura em
COLUNAS (telas / diagramas multi-painel): cada bloco de texto é agrupado pela
coluna em que está posicionado na página (posição horizontal do ``bbox``) e
cada coluna é lida de cima para baixo, da esquerda para a direita.

- ``manual_columns`` (2..6) força o número de colunas por divisão uniforme.
- ``manual_columns`` 0 tenta detectar as colunas automaticamente pelas lacunas
  horizontais entre os blocos; se não encontrar 2+ colunas, retorna ``""``
  (o consumidor faz o fallback para o Markdown padrão do Docling).

Sem dependências Qt — usa apenas LogUtils. É consumido pelo ``DoclingEngine``.
"""

from __future__ import annotations

import bisect
from typing import Any, Dict, List, Tuple

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class MdManager(BaseUtil):
    """Exporta um ``DoclingDocument`` em Markdown separado por colunas."""

    # Lacuna mínima (fração da largura da página) para separar colunas no modo
    # automático.
    MIN_COLUMN_GAP = 0.15
    # Número máximo de colunas suportado.
    MAX_COLUMNS = 6

    @classmethod
    def export_by_columns(
        cls,
        doc: Any,
        *,
        page_no: int = 0,
        manual_columns: int = 0,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Exporta ``doc`` em Markdown agrupado por colunas.

        Args:
            doc: ``DoclingDocument`` convertido.
            page_no: Página específica (1-based). ``0`` ou negativo = todas.
            manual_columns: ``0`` = automático; ``2..6`` = força o número.
            tool_key: Chave da ferramenta para logging (Contrato 26).

        Returns:
            Markdown separado por colunas, ou ``""`` quando não há 2+ colunas
            (layout de coluna única) ou quando o documento é inválido.
        """
        logger = cls._get_logger(tool_key, "MdManager")
        if doc is None:
            return ""

        try:
            items_by_page = cls._collect_items(doc)
        except Exception as e:  # noqa: BLE001 - API externa do Docling
            logger.warning(
                "Falha ao iterar o documento",
                code="MDM_ITER_ERR",
                error=str(e),
            )
            return ""

        if not items_by_page:
            return ""

        only_page = page_no if page_no and page_no > 0 else None
        blocks: List[str] = []
        for number in sorted(items_by_page):
            if only_page is not None and number != only_page:
                continue
            block = cls._export_page(
                doc, number, items_by_page[number], manual_columns, logger
            )
            if block:
                blocks.append(block)

        return "\n\n".join(blocks).strip()

    # ── Coleta ───────────────────────────────────────────────────────

    @staticmethod
    def _collect_items(doc: Any) -> Dict[int, List[Any]]:
        """Agrupa os itens com ``prov`` pelo número da página."""
        items_by_page: Dict[int, List[Any]] = {}
        for item, _level in doc.iterate_items(traverse_pictures=True):
            prov = getattr(item, "prov", None)
            if not prov:
                continue
            page_number = prov[0].page_no
            items_by_page.setdefault(page_number, []).append(item)
        return items_by_page

    # ── Render de uma página ─────────────────────────────────────────

    @classmethod
    def _export_page(
        cls,
        doc: Any,
        page_number: int,
        items: List[Any],
        manual_columns: int,
        logger: LogUtils,
    ) -> str:
        """Renderiza uma página agrupada por colunas (``""`` se coluna única)."""
        width = cls._page_width(doc, page_number)
        entries = cls._measure(items, width)
        if len(entries) < 2:
            return ""

        lefts = [left for left, _top, _center, _item in entries]
        boundaries = cls._column_boundaries(lefts, manual_columns)
        if not boundaries:
            return ""

        columns: Dict[int, List[Tuple[float, Any]]] = {}
        for _left, top, center, item in entries:
            index = bisect.bisect_right(boundaries, center)
            columns.setdefault(index, []).append((top, item))

        serializer = cls._make_serializer(doc, logger)

        parts: List[str] = []
        for index in sorted(columns):
            column_md = cls._render_column(serializer, columns[index])
            if not column_md:
                continue
            parts.append(f"### Coluna {index + 1}\n\n{column_md}")

        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return f"## Página {page_number}\n\n" + "\n\n".join(parts)

    @staticmethod
    def _measure(
        items: List[Any], width: float
    ) -> List[Tuple[float, float, float, Any]]:
        """Converte itens em ``(left, top, center, item)`` normalizados."""
        entries: List[Tuple[float, float, float, Any]] = []
        for item in items:
            bbox = item.prov[0].bbox
            left = bbox.l / width
            center = ((bbox.l + bbox.r) / 2.0) / width
            entries.append((left, bbox.t, center, item))
        return entries

    @staticmethod
    def _page_width(doc: Any, page_number: int) -> float:
        """Largura da página (fallback 1.0 para evitar divisão por zero)."""
        try:
            return float(doc.pages[page_number].size.width) or 1.0
        except Exception:  # noqa: BLE001 - estrutura externa do Docling
            return 1.0

    @classmethod
    def _column_boundaries(
        cls, lefts: List[float], manual_columns: int
    ) -> List[float]:
        """Retorna as fronteiras (x normalizado) entre colunas.

        ``[]`` significa "coluna única" (sem separação a fazer).
        """
        if manual_columns and manual_columns >= 2:
            count = min(int(manual_columns), cls.MAX_COLUMNS)
            return [i / count for i in range(1, count)]

        if len(lefts) < 2:
            return []

        ordered = sorted(lefts)
        gaps: List[Tuple[float, float]] = []
        for previous, current in zip(ordered, ordered[1:]):
            gap = current - previous
            if gap >= cls.MIN_COLUMN_GAP:
                gaps.append((gap, (previous + current) / 2.0))
        if not gaps:
            return []

        gaps.sort(reverse=True)
        return sorted(boundary for _gap, boundary in gaps[: cls.MAX_COLUMNS - 1])

    @staticmethod
    def _make_serializer(doc: Any, logger: LogUtils) -> Any:
        """Cria o serializer Markdown do Docling (``None`` se indisponível)."""
        try:
            from docling_core.transforms.serializer.markdown import (
                MarkdownDocSerializer,
            )

            return MarkdownDocSerializer(doc=doc)
        except Exception as e:  # noqa: BLE001 - API externa do Docling
            logger.warning(
                "Serializer Markdown indisponível",
                code="MDM_SER_ERR",
                error=str(e),
            )
            return None

    @classmethod
    def _render_column(
        cls, serializer: Any, entries: List[Tuple[float, Any]]
    ) -> str:
        """Renderiza uma coluna (itens já em ordem de cima para baixo)."""
        blocks: List[str] = []
        for _top, item in sorted(entries, key=lambda entry: entry[0]):
            markdown = cls._item_markdown(serializer, item)
            if markdown:
                blocks.append(markdown)
        return "\n\n".join(blocks)

    @staticmethod
    def _item_markdown(serializer: Any, item: Any) -> str:
        """Markdown de um item; cai para o texto cru se o serializer falhar."""
        if serializer is not None:
            try:
                return serializer.serialize(item=item).text.strip()
            except Exception:  # noqa: BLE001 - item pode não ser serializável
                pass
        return str(getattr(item, "text", "") or "").strip()

