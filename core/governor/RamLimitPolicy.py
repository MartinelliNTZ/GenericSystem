# -*- coding: utf-8 -*-
"""
RamLimitPolicy — Estratégias de limite de RAM
===============================================
Define o limite máximo de RAM que o sistema pode usar, com duas estratégias:

  - GLOBAL:   max_ram = total_ram * fraction
              headroom = max_ram - used_system_ram
              (considera todos os processos do sistema)

  - DEDICATED: max_ram = total_ram * fraction
               headroom = max_ram - process_ram
               (considera apenas o processo atual)

Uso:
    from core.governor.RamLimitPolicy import RamLimitPolicy, RamLimitMode

    policy = RamLimitPolicy(mode=RamLimitMode.GLOBAL, fraction=0.90)
    policy = RamLimitPolicy(mode=RamLimitMode.DEDICATED, fraction=0.50)
"""

from __future__ import annotations

from enum import Enum
from typing import Dict

from core.governor.RamGovernor import RamGovernor
from utils.FormatUtils import FormatUtils


class RamLimitMode(Enum):
    """
    Modos de estratégia de limite de RAM.

    GLOBAL:     Limite sobre a RAM total do sistema (todos os processos).
    DEDICATED:  Limite dedicado ao processo atual, independente dos demais.
    """
    GLOBAL = "global"
    DEDICATED = "dedicated"


class RamLimitPolicy:
    """
    Define a estratégia de limite de RAM.

    Args:
        mode: RamLimitMode.GLOBAL ou RamLimitMode.DEDICATED.
        fraction: Fração da RAM total a ser usada como limite (0.0 a 1.0).
                  Ex: 0.90 = 90%, 0.50 = 50%.
    """

    def __init__(self, mode: RamLimitMode, fraction: float) -> None:
        if not 0.0 < fraction <= 1.0:
            raise ValueError(f"fraction deve estar entre 0.0 e 1.0, got {fraction}")

        self._mode = mode
        self._fraction = fraction
        self._ram = RamGovernor()

    # ── Propriedades ─────────────────────────────────────────────────

    @property
    def mode(self) -> RamLimitMode:
        """Modo de estratégia atual."""
        return self._mode

    @property
    def fraction(self) -> float:
        """Fração da RAM total usada como limite."""
        return self._fraction

    # ── Cálculos ─────────────────────────────────────────────────────

    def max_allowed_ram(self) -> int:
        """
        Bytes máximos permitidos pela política.
        max_ram = total_ram * fraction
        """
        return int(self._ram.total_system_ram() * self._fraction)

    def available_headroom(self) -> int:
        """
        Bytes livres dentro do limite (headroom).

        GLOBAL:     headroom = max_allowed_ram - used_system_ram
        DEDICATED:  headroom = max_allowed_ram - process_ram

        Se headroom <= 0, o sistema está no limite ou acima.
        """
        max_ram = self.max_allowed_ram()

        if self._mode == RamLimitMode.GLOBAL:
            consumed = self._ram.used_system_ram()
        else:  # DEDICATED
            consumed = self._ram.process_ram()

        return max_ram - consumed

    def is_available(self, needed_bytes: int = 0) -> bool:
        """
        Verifica se há headroom suficiente para needed_bytes.

        Args:
            needed_bytes: RAM estimada necessária (0 = só verifica headroom).

        Returns:
            True se cabe dentro do limite, False caso contrário.
        """
        return self.available_headroom() >= needed_bytes

    def utilization(self) -> float:
        """
        Percentual de ocupação dentro do limite (0.0 a 100.0+).

        Se > 100.0, significa que o consumo já ultrapassou o limite.
        """
        max_ram = self.max_allowed_ram()
        if max_ram == 0:
            return 0.0

        if self._mode == RamLimitMode.GLOBAL:
            consumed = self._ram.used_system_ram()
        else:  # DEDICATED
            consumed = self._ram.process_ram()

        return (consumed / max_ram) * 100.0

    # ── Diagnóstico ──────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, object]:
        """Retorna dicionário com estado completo da política."""
        max_allowed = self.max_allowed_ram()
        headroom = self.available_headroom()
        return {
            "mode": self._mode.value,
            "fraction": self._fraction,
            "max_allowed_bytes": max_allowed,
            "max_allowed_human": FormatUtils.format_size(max_allowed),
            "headroom_bytes": headroom,
            "headroom_human": FormatUtils.format_size(max(0, headroom)),
            "utilization_pct": round(self.utilization(), 1),
            "can_execute": self.is_available(),
        }
