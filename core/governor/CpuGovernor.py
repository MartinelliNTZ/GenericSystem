# -*- coding: utf-8 -*-
"""
CpuGovernor — Governanca de uso de CPU
========================================
Limita o numero maximo de workers/threads que o software pode usar
simultaneamente, evitando saturacao total da CPU.

Fornece dados BRUTOS de CPU (percentual, contagem de nucleos).
Nao formata tooltips — isso e responsabilidade do consumidor
(ex: SystemMonitorService).

Constante editavel:
    CPU_USAGE_LIMIT = 0.50  # 50% dos CPUs (padrao)

Uso:
    from core.governor.CpuGovernor import CpuGovernor

    cpu = CpuGovernor()
    pct = cpu.percent()          # 45.2
    phys = cpu.count_physical()  # 8
    log = cpu.count_logical()    # 16
    workers = cpu.max_workers()  # int(32 * 0.25) = 8
"""

from __future__ import annotations

import os

import psutil


class CpuGovernor:
    """
    Governa o uso maximo de CPUs pelo software.

    Instanciado pelo ResourceGovernor como self._cpu.

    Attributes:
        CPU_USAGE_LIMIT: Fracao dos CPUs totais que o software pode usar
                         (0.0 a 1.0). Padrao: 0.25 (25%).
    """

    CPU_USAGE_LIMIT: float = 0.50  # <<< EDITAVEL: 0.0 a 1.0

    def __init__(self) -> None:
        # Chamada dummy para psutil.cpu_percent ter baseline
        psutil.cpu_percent(interval=None)

    @classmethod
    def max_workers(cls) -> int:
        """
        Retorna o numero maximo de workers permitido.

        Calculo: int(total_cpus * CPU_USAGE_LIMIT), minimo 1.

        Returns:
            int: Numero maximo de workers (>= 1).
        """
        total = os.cpu_count() or 4
        return max(1, int(total * cls.CPU_USAGE_LIMIT))

    @classmethod
    def n_jobs(cls) -> int:
        """
        Retorna n_jobs para joblib.Parallel (evitar usar -1).

        Returns:
            int: Mesmo valor de max_workers().
        """
        return cls.max_workers()

    # ── Consulta de uso real da CPU ────────────────────────────────

    def percent(self) -> float:
        """
        Uso atual da CPU em percentual (0.0 a 100.0).

        Returns:
            float: Percentual de uso da CPU (ultimo intervalo).
        """
        return psutil.cpu_percent(interval=None)

    def count_physical(self) -> int:
        """Numero de nucleos fisicos da CPU."""
        return psutil.cpu_count(logical=False) or 0

    def count_logical(self) -> int:
        """Numero de nucleos logicos (threads) da CPU."""
        return psutil.cpu_count(logical=True) or 0