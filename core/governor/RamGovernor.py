# -*- coding: utf-8 -*-
"""
RamGovernor — Monitoramento de RAM do sistema e processo
===========================================================
Fornece dados de RAM via psutil.

Melhorias:
- Cache: total_system_ram cacheada, virtual_memory com TTL 0.5s
- SWAP: total_swap, used_swap, percent_swap
- memory_pressure(): combina RAM + SWAP
- process_growth_rate(): detecta vazamento de memoria
- Snapshot com 1 chamada psutil (vs 4 antes)
"""

from __future__ import annotations

import os
import time
from typing import Dict, Optional

import psutil

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from utils.FormatUtils import FormatUtils


class RamGovernor:
    """
    Monitora RAM do sistema inteiro e do processo atual.

    Cache (otimizacao):
        - total_system_ram: cacheada no __init__ (nunca muda)
        - virtual_memory: cacheada por cache_ttl (default 0.5s)

    SWAP:
        - memory_pressure() combina RAM + SWAP

    Tendencias:
        - Historico de amostras para detectar crescimento de memoria
    """

    DEFAULT_CACHE_TTL: float = 0.5

    def __init__(self, cache_ttl: float = DEFAULT_CACHE_TTL) -> None:
        self._process = psutil.Process(os.getpid())
        self._cache_ttl = cache_ttl
        self._cached_vmem = None  # type: ignore[assignment]
        self._cached_vmem_time: float = 0
        self._cached_total: int = psutil.virtual_memory().total
        self._history: list[dict] = []
        self._max_history: int = 10

    def _get_vmem(self):
        now = time.monotonic()
        if (self._cached_vmem is None
                or (now - self._cached_vmem_time) >= self._cache_ttl):
            self._cached_vmem = psutil.virtual_memory()
            self._cached_vmem_time = now
        return self._cached_vmem

    def total_system_ram(self) -> int:
        """RAM total instalada (bytes) — cacheada."""
        return self._cached_total

    def used_system_ram(self) -> int:
        """RAM usada pelo sistema (bytes)."""
        return self._get_vmem().used

    def available_system_ram(self) -> int:
        """RAM disponivel (bytes)."""
        return self._get_vmem().available

    @staticmethod
    def total_swap() -> int:
        return psutil.swap_memory().total

    @staticmethod
    def used_swap() -> int:
        return psutil.swap_memory().used

    @staticmethod
    def percent_swap() -> float:
        return psutil.swap_memory().percent

    def process_ram(self) -> int:
        return self._process.memory_info().rss

    def percent_used(self) -> float:
        return self._get_vmem().percent

    def percent_process(self) -> float:
        if self._cached_total == 0:
            return 0.0
        return (self.process_ram() / self._cached_total) * 100.0

    def memory_pressure(self) -> float:
        """Pressao de memoria (0.0 a 1.0+). Combina RAM + SWAP."""
        vmem = self._get_vmem()
        ram_pressure = vmem.used / max(1, vmem.total)
        try:
            swap = psutil.swap_memory()
            if swap.total > 0:
                swap_pressure = swap.used / swap.total
                pressure = ram_pressure * (1.0 + swap_pressure * 0.5)
            else:
                pressure = ram_pressure
        except Exception as e:
            pressure = ram_pressure
            LogUtils(
                tool=ToolKey.SYSTEM.value, class_name="RamGovernor",
            ).warning(
                "Erro ao ler swap para memory_pressure", code="RAM_SWAP_ERR",
                error=str(e),
            )
        return pressure

    def process_growth_rate(self, samples: int = 3) -> float:
        """Taxa de crescimento (bytes/s). Positivo = vazamento."""
        if len(self._history) < 2:
            return 0.0
        recent = self._history[-samples:]
        if len(recent) < 2:
            return 0.0
        elapsed = recent[-1]["time"] - recent[0]["time"]
        if elapsed <= 0:
            return 0.0
        return (recent[-1]["process_bytes"] - recent[0]["process_bytes"]) / elapsed

    def _record_history(self) -> None:
        now = time.monotonic()
        self._history.append({
            "time": now,
            "process_bytes": self.process_ram(),
            "system_percent": self.percent_used(),
        })
        if len(self._history) > self._max_history:
            self._history.pop(0)

    def snapshot(self, include_history: bool = False) -> Dict[str, object]:
        """Snapshot completo. Otimizado: 1 chamada virtual_memory + 1 swap (reutilizada para pressure)."""
        vmem = self._get_vmem()
        proc = self.process_ram()
        try:
            swap = psutil.swap_memory()
            s_total, s_used, s_pct = swap.total, swap.used, swap.percent
        except Exception as e:
            s_total = s_used = 0
            s_pct = 0.0
            LogUtils(
                tool=ToolKey.SYSTEM.value, class_name="RamGovernor",
            ).warning(
                "Erro ao ler swap para snapshot", code="RAM_SWAP_SNAP_ERR",
                error=str(e),
            )

        # Calcula memory_pressure com os dados de swap ja obtidos (evita 2a chamada)
        ram_pressure = vmem.used / max(1, vmem.total)
        if s_total > 0:
            swap_pressure = s_used / s_total
            pressure = ram_pressure * (1.0 + swap_pressure * 0.5)
        else:
            pressure = ram_pressure

        result: Dict[str, object] = {
            "total_bytes": self._cached_total,
            "total_human": FormatUtils.format_size(self._cached_total),
            "used_system_bytes": vmem.used,
            "used_system_human": FormatUtils.format_size(vmem.used),
            "available_bytes": vmem.available,
            "available_human": FormatUtils.format_size(vmem.available),
            "process_bytes": proc,
            "process_human": FormatUtils.format_size(proc),
            "percent_system": round(vmem.percent, 1),
            "percent_process": round(self.percent_process(), 1),
            "swap_total_bytes": s_total,
            "swap_total_human": FormatUtils.format_size(s_total),
            "swap_used_bytes": s_used,
            "swap_used_human": FormatUtils.format_size(s_used),
            "swap_percent": round(s_pct, 1),
            "memory_pressure": round(pressure, 3),
        }

        if include_history:
            rate = self.process_growth_rate()
            result["process_growth_rate_bps"] = round(rate, 1)
            abs_rate = abs(int(rate))
            sign = "-" if rate < 0 else ""
            result["process_growth_rate_human"] = f"{sign}{FormatUtils.format_size(abs_rate)}/s"
            self._record_history()

        return result
