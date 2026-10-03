# -*- coding: utf-8 -*-
"""
SystemMonitorService — Serviço de polling de CPU/RAM via ResourceGovernor
==========================================================================
Polling de CPU e RAM em intervalo configurável, delegando a coleta
de dados ao ResourceGovernor (que centraliza chamadas psutil).

Uso:
    from core.governor.ResourceGovernor import ResourceGovernor
    from core.governor.RamLimitPolicy import RamLimitPolicy, RamLimitMode

    policy = RamLimitPolicy(mode=RamLimitMode.GLOBAL, fraction=0.90)
    governor = ResourceGovernor(policy=policy)
    monitor = SystemMonitorService(governor=governor, interval_ms=2000)
    monitor.stats_updated.connect(self._on_stats)
    monitor.start()
    # ...
    monitor.stop()

Sinais:
    stats_updated(dict) — emitido a cada ciclo:
        {
            "cpu": 45.2,
            "ram": 72.8,
            "cpu_tooltip": "CPU: 45.2% (8 cores físicos, 16 lógicos)",
            "ram_tooltip": "RAM: 72.8% (23.4 GB / 32.0 GB usados)",
        }
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.governor.ResourceGovernor import ResourceGovernor
from core.manager.SignalManager import SignalManager


class SystemMonitorService(QObject):
    """
    Serviço de monitoramento do sistema via ResourceGovernor.

    Polla CPU e RAM em background via QTimer e emite stats_updated
    com os valores formatados. Também propaga via SignalManager
    para outros componentes interessados.

    A coleta de dados é delegada ao ResourceGovernor, que centraliza
    todas as chamadas psutil do sistema (evita duplicação).
    """

    stats_updated = Signal(dict)

    def __init__(
        self,
        governor: ResourceGovernor,
        interval_ms: int = 2000,
        parent=None,
    ):
        super().__init__(parent)
        self._governor = governor
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._interval = interval_ms
        self._logger = LogUtils(
            tool=ToolKey.SYSTEM_MONITOR.value,
            class_name="SystemMonitorService",
        )
        # Cache de valores imutaveis (nunca mudam durante execucao)
        self._cached_phys: int = governor.cpu_count_physical()
        self._cached_log: int = governor.cpu_count_logical()
        self._cached_total_human: str = ""
        self._cached_total_bytes: int = 0

    # ── API pública ────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia o polling periódico."""
        self._poll()  # primeira execução imediata
        self._timer.start(self._interval)
        self._logger.info(
            "System monitor started",
            code="MONITOR_START",
            interval_ms=self._interval,
        )

    def stop(self) -> None:
        """Para o polling."""
        self._timer.stop()
        self._logger.info("System monitor stopped", code="MONITOR_STOP")

    def poll_once(self) -> dict:
        """
        Executa uma leitura manual e retorna o dict.

        Returns:
            dict com cpu, ram, cpu_tooltip, ram_tooltip.
        """
        return dict(self._governor.system_stats())

    @property
    def is_running(self) -> bool:
        """True se o timer está ativo."""
        return self._timer.isActive()

    # ── Internos ───────────────────────────────────────────────────

    def _build_tooltips(self, cpu: float, ram: float) -> tuple[str, str]:
        """Constrói tooltips a partir dos dados brutos do governor."""
        cpu_tip = (
            f"CPU: {cpu:.1f}% "
            f"({self._cached_phys} cores fisicos, {self._cached_log} logicos)"
        )
        snap = self._governor.ram_snapshot()
        ram_tip = (
            f"RAM: {ram:.1f}% "
            f"({snap['used_system_human']} / "
            f"{snap['total_human']} usados)"
        )
        return cpu_tip, ram_tip

    def _poll(self) -> None:
        """Polling interno: coleta via governor, formata e emite sinais."""
        try:
            raw = self._governor.system_stats()
            cpu = raw["cpu"]
            ram = raw["ram"]
            cpu_tip, ram_tip = self._build_tooltips(cpu, ram)
            data = {
                "cpu": cpu,
                "ram": ram,
                "cpu_tooltip": cpu_tip,
                "ram_tooltip": ram_tip,
            }
            self.stats_updated.emit(data)
            SignalManager.instance().system_stats_updated.emit(data)
        except Exception as e:
            self._logger.error(
                "Error polling system stats",
                code="MONITOR_POLL_ERR",
                error=str(e),
            )
