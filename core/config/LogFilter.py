# -*- coding: utf-8 -*-
"""
LogFilter — Filtro e ordenacao de eventos de log
===================================================
Carrega todos os arquivos .json de ``log/``, filtra por texto e nivel,
e ordena por qualquer coluna.

Uso:
    from core.config.LogFilter import LogFilter

    data = LogFilter.load_all()
    data = LogFilter.filter_text(data, "erro")
    data = LogFilter.filter_level(data, "ERROR")
    data = LogFilter.sort(data, "timestamp", ascending=False)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List


class LogFilter:
    """
    Utilitario estatico para carregar, filtrar e ordenar logs.
    """

    _LOG_DIR: Path = Path(__file__).resolve().parent.parent.parent / "log"

    # ── Colunas padrao ──────────────────────────────────────────────
    COLUMNS = ["timestamp", "level", "tool", "class", "message", "code"]

    # ── Niveis para ordenacao natural ───────────────────────────────
    LEVEL_ORDER = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

    # ── API ─────────────────────────────────────────────────────────

    @classmethod
    def load_all(cls) -> List[dict]:
        """
        Carrega todos os eventos de todos os arquivos .json em ``log/``.

        Retorna:
            Lista de dicts (eventos), cada um com pelo menos:
            timestamp, level, tool, class_name, message, code (opcional).
        """
        events: List[dict] = []
        log_dir = cls._LOG_DIR

        if not log_dir.is_dir():
            return events

        for path in sorted(log_dir.iterdir()):
            if path.is_file() and path.suffix.lower() == ".json":
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        events.extend(data)
                except (json.JSONDecodeError, OSError):
                    pass  # ignora arquivo corrompido

        return events

    @classmethod
    def filter_text(cls, events: List[dict], search: str) -> List[dict]:
        """
        Filtra eventos que contenham o texto ``search`` em qualquer campo
        string (message, level, tool, class, code, data).

        Case-insensitive. Se ``search`` for vazio, retorna a lista original.
        """
        if not search or not search.strip():
            return events

        search_lower = search.strip().lower()

        def _matches(event: dict) -> bool:
            # Percorre todos os valores do evento
            for value in event.values():
                if isinstance(value, str) and search_lower in value.lower():
                    return True
                if isinstance(value, dict):
                    # Procura dentro de "data" tambem
                    for v in value.values():
                        if isinstance(v, str) and search_lower in v.lower():
                            return True
            return False

        return [e for e in events if _matches(e)]

    @classmethod
    def filter_level(cls, events: List[dict], level: str | None) -> List[dict]:
        """
        Filtra eventos pelo nivel exato.

        Se ``level`` for None ou "ALL", retorna a lista original.
        """
        if not level or level.upper() == "ALL":
            return events

        target = level.upper()
        return [e for e in events if e.get("level", "").upper() == target]

    @classmethod
    def sort(
        cls,
        events: List[dict],
        column: str = "timestamp",
        ascending: bool = False,
    ) -> List[dict]:
        """
        Ordena a lista de eventos por uma coluna.

        Parametros:
            events    : Lista de dicts
            column    : Nome da coluna (ex: "timestamp", "level", "tool")
            ascending : True para ASC, False para DESC (padrao)

        Retorna:
            Nova lista ordenada.
        """
        if column == "level":
            return sorted(
                events,
                key=lambda e: cls.LEVEL_ORDER.get(e.get("level", ""), 99),
                reverse=not ascending,
            )

        if column == "timestamp":
            return sorted(
                events,
                key=lambda e: e.get("timestamp", ""),
                reverse=not ascending,
            )

        # Qualquer outra coluna (tool, class, message, code)
        return sorted(
            events,
            key=lambda e: e.get(column, "") or "",
            reverse=not ascending,
        )