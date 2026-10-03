# -*- coding: utf-8 -*-
"""
LogCleanup — Limpeza de arquivos de log antigos
=================================================
Mantém apenas os N arquivos de log mais recentes dentro de ``log/``,
removendo os mais antigos automaticamente.

Deve ser chamado uma vez no inicio do programa (ex: no BootStrap).

Uso:
    from core.log.LogCleanup import LogCleanup

    LogCleanup.run(max_files=5)
"""

from __future__ import annotations

from pathlib import Path
from typing import List


class LogCleanup:
    """
    Utilitario estatico para limpeza de logs antigos.
    """

    # core/config/LogCleanup.py → parent.parent.parent = raiz do projeto
    _LOG_DIR: Path = Path(__file__).resolve().parent.parent.parent / "log"

    @classmethod
    def run(cls, max_files: int = 5) -> int:
        """
        Mantém apenas os ``max_files`` arquivos .json mais recentes.

        Parametros:
            max_files : Numero maximo de arquivos de log a manter.

        Retorna:
            Quantidade de arquivos removidos.
        """
        logs = cls._list_logs()
        if len(logs) <= max_files:
            return 0

        # Ordena do mais novo para o mais antigo
        logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        to_remove: List[Path] = logs[max_files:]
        removed = 0

        for path in to_remove:
            try:
                path.unlink(missing_ok=True)
                removed += 1
            except OSError:
                pass  # arquivo pode estar sendo usado, ignora

        return removed

    @classmethod
    def _list_logs(cls) -> List[Path]:
        """Lista todos os arquivos .json dentro do diretorio de log."""
        if not cls._LOG_DIR.is_dir():
            return []
        return sorted(
            p for p in cls._LOG_DIR.iterdir()
            if p.is_file() and p.suffix.lower() == ".json"
        )