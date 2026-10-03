# -*- coding: utf-8 -*-
"""
ResourceGovernor — Orquestrador de Governanca de Recursos
============================================================
Ponto unico de integracao para plugins/pipelines consultarem
se ha recursos suficientes antes de executar tarefas pesadas.

v3: Adiciona self._cpu (CpuGovernor) como instancia e metodos
genericos de consulta (cpu_percent, ram_percent, cpu_count_*,
ram_snapshot, system_stats) para que qualquer consumidor obtenha
dados sem importar sub-governors diretamente.

ATENCAO: Este orquestrador retorna APENAS dados brutos.
Tooltips sao responsabilidade do consumidor (ex: SystemMonitorService).

Uso:
    from core.governor.ResourceGovernor import ResourceGovernor

    can, reason = governor.can_execute(estimated_ram=8_000_000_000)
    if not can: return

    safe_tile = governor.recommended_tile_size(10_000_000, estimated_ram=4_000_000_000)

    # Durante execucao (periodicamente)
    if not governor.check_during_execution():
        task.cancel()

    # Dados brutos (qualquer consumidor)
    stats = governor.system_stats()            # {"cpu": 45.2, "ram": 72.8}
    pct_cpu = governor.cpu_percent()           # 45.2
    pct_ram = governor.ram_percent()           # 72.8
    n_phys = governor.cpu_count_physical()     # 8
    snap = governor.ram_snapshot()             # {"percent_system": 72.8, ...}
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from core.enum.ToolKey import ToolKey
from core.governor.CpuGovernor import CpuGovernor
from core.governor.RamGovernor import RamGovernor
from core.governor.RamLimitPolicy import RamLimitPolicy
from utils.BaseUtil import BaseUtil
from utils.FormatUtils import FormatUtils


class ResourceExceededError(Exception):
    def __init__(self, message: str, snapshot: Optional[Dict] = None):
        super().__init__(message)
        self.snapshot = snapshot


class ResourceGovernor:
    """
    Orquestrador de decisoes baseadas em recursos.

    Centraliza CpuGovernor e RamGovernor como instancias internas.
    Consumidores (ex: SystemMonitorService) acessam dados APENAS
    via metodos genericos desta classe — nunca importam sub-governors.

    Args:
        policy: RamLimitPolicy com a estrategia de limite.
        tool_key: ToolKey.value para logging (Contrato 26).
    """

    BYTES_PER_POINT: int = 32
    MAX_WARNINGS: int = 3

    def __init__(
        self,
        policy: RamLimitPolicy,
        tool_key: str = ToolKey.SYSTEM.value,
    ) -> None:
        self._policy = policy
        self._cpu = CpuGovernor()
        self._ram = RamGovernor()
        self._tool_key = tool_key
        self._warnings: int = 0
        self._logger = BaseUtil._get_logger(self._tool_key, "ResourceGovernor")
        self._log_snapshot("ResourceGovernor inicializado")

    @property
    def policy(self) -> RamLimitPolicy:
        return self._policy

    @property
    def warnings(self) -> int:
        return self._warnings

    @property
    def is_throttled(self) -> bool:
        """True se excedeu MAX_WARNINGS consecutivos."""
        return self._warnings >= self.MAX_WARNINGS

    # ── Metodos de decisao (RAM) ──────────────────────────────────

    def can_execute(self, estimated_ram: int = 0) -> Tuple[bool, str]:
        """
        Verifica se ha recursos suficientes. AGORA usa estimated_ram.

        3 niveis de protecao:
        1. Headroom < estimated_ram + 10% margem -> bloqueia
        2. memory_pressure > 0.95 -> bloqueia (RAM+SWAP criticos)
        3. 3 warnings consecutivos -> throttled
        """
        headroom = self._policy.available_headroom()
        needed = int(estimated_ram * 1.10) if estimated_ram > 0 else 0

        # Nivel 1: headroom insuficiente para a operacao estimada
        if headroom < needed:
            self._warnings += 1
            snap = self.snapshot(estimated_ram)
            reason = (
                f"Memoria insuficiente. "
                f"Headroom: {snap['headroom_human']}, "
                f"Necessario (c/ margem): {FormatUtils.format_size(needed)}, "
                f"Limite: {snap['max_allowed_human']}, "
                f"Pressao: {snap.get('memory_pressure', 'N/A')}"
            )
            self._log_warning(reason)
            if self.is_throttled:
                self._logger.error(
                    "Sistema sobrecarregado — warnings consecutivos",
                    code="GOV_THROTTLED",
                    warnings=self._warnings,
                )
            return False, reason

        # Nivel 2: pressao de memoria (RAM + SWAP)
        pressure = self._ram.memory_pressure()
        if pressure > 0.95:
            self._warnings += 1
            reason = f"Pressao de memoria critica ({pressure:.1%}). Risco de OOM."
            self._log_warning(reason)
            if self.is_throttled:
                self._logger.error(
                    "Sistema sobrecarregado — pressao critica",
                    code="GOV_THROTTLED",
                    warnings=self._warnings,
                )
            return False, reason

        # Reset warnings se passou
        if self._warnings > 0:
            self._warnings = 0
        return True, ""

    def check_during_execution(self) -> bool:
        """
        Verificacao RAPIDA para uso DURANTE a execucao da task.
        Mais leve que can_execute() — sem log, sem incremento de warnings.
        Retorna False se deve interromper a task.
        """
        if self._policy.available_headroom() <= 0:
            return False
        if self._ram.memory_pressure() > 0.95:
            return False
        if self.is_throttled:
            return False
        return True

    def assert_can_execute(self, estimated_ram: int = 0) -> None:
        can, reason = self.can_execute(estimated_ram)
        if not can:
            raise ResourceExceededError(reason, snapshot=self.snapshot(estimated_ram))

    def recommended_tile_size(self, max_tile_points: int, estimated_ram: int = 0) -> int:
        """
        Ajusta o tamanho do tile baseado na RAM disponivel e estimada.

        2 fatores:
        1. headroom_factor: headroom / max_allowed_ram
        2. estimate_factor: quantos tiles cabem no headroom (min 2)
        Fator final = min dos 2 fatores (mais conservador)
        """
        max_ram = self._policy.max_allowed_ram()
        headroom = self._policy.available_headroom()

        if max_ram <= 0:
            fator = 0.05
        else:
            fator_headroom = headroom / max_ram
            if estimated_ram > 0 and headroom > 0:
                tiles_que_cabem = headroom / max(1, estimated_ram)
                fator_estimativa = min(1.0, tiles_que_cabem / 2.0)
                fator = max(0.05, min(fator_headroom, fator_estimativa))
            else:
                fator = max(0.05, fator_headroom)

        adjusted = int(max_tile_points * fator)
        min_tile = max(1, int(max_tile_points * 0.05))
        return max(min_tile, adjusted)

    # ── Metodos genericos de consulta (CPU + RAM) ─────────────────
    # Apenas dados brutos. Tooltips sao responsabilidade do consumidor.

    def cpu_percent(self) -> float:
        """Uso atual da CPU (0.0 a 100.0)."""
        return self._cpu.percent()

    def ram_percent(self) -> float:
        """Uso atual da RAM (0.0 a 100.0)."""
        return self._ram.percent_used()

    def cpu_count_physical(self) -> int:
        """Numero de nucleos fisicos da CPU."""
        return self._cpu.count_physical()

    def cpu_count_logical(self) -> int:
        """Numero de nucleos logicos (threads) da CPU."""
        return self._cpu.count_logical()

    def ram_snapshot(self) -> Dict[str, object]:
        """
        Snapshot de RAM com dados formatados para display.

        O consumidor usa os campos 'percent_system',
        'used_system_human' e 'total_human' para montar tooltips.

        Returns:
            dict com percent_system, used_system_human, total_human, etc.
        """
        return self._ram.snapshot(include_history=False)

    def system_stats(self) -> Dict[str, object]:
        """
        Retorna estatisticas brutas de CPU e RAM do sistema.

        Apenas dados crus — sem tooltips. O consumidor
        (ex: SystemMonitorService) formata o display.

        Returns:
            dict com cpu (float), ram (float).
        """
        return {
            "cpu": self.cpu_percent(),
            "ram": self.ram_percent(),
        }

    # ── Diagnostico ───────────────────────────────────────────────

    def snapshot(self, estimated_ram: int = 0) -> Dict[str, object]:
        """Estado completo para logging/diagnostico."""
        ram_snap = self._ram.snapshot(include_history=True)
        policy_snap = self._policy.snapshot()
        headroom = self._policy.available_headroom()

        return {
            "policy_mode": self._policy.mode.value,
            "policy_fraction": self._policy.fraction,
            "total_human": ram_snap["total_human"],
            "used_system_human": ram_snap["used_system_human"],
            "process_human": ram_snap["process_human"],
            "max_allowed_human": policy_snap.get("max_allowed_human", ""),
            "headroom_human": FormatUtils.format_size(max(0, headroom)),
            "estimated_human": FormatUtils.format_size(estimated_ram),
            "utilization_pct": policy_snap["utilization_pct"],
            "memory_pressure": ram_snap.get("memory_pressure", 0),
            "swap_percent": ram_snap.get("swap_percent", 0),
            "process_growth_rate": ram_snap.get("process_growth_rate_human", "N/A"),
            "warnings": self._warnings,
            "is_throttled": self.is_throttled,
        }

    def _log_snapshot(self, prefix: str = "") -> None:
        snap = self.snapshot()
        msg = (
            f"{prefix} | "
            f"Sistema: {snap['used_system_human']}/{snap['total_human']} | "
            f"Processo: {snap['process_human']} | "
            f"Headroom: {snap['headroom_human']} | "
            f"Pressao: {snap.get('memory_pressure', 'N/A')} | "
            f"Limite: {snap['policy_mode']} {snap['policy_fraction']*100:.0f}%"
        )
        self._logger.debug(msg, code="GOV_SNAPSHOT")

    def _log_warning(self, reason: str) -> None:
        self._logger.warning(reason, code="GOV_LOW_MEMORY", warnings=self._warnings)