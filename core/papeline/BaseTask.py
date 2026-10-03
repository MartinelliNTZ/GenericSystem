# -*- coding: utf-8 -*-
"""
BaseTask — Wrapper para execucao de trabalho pesado em background
==================================================================
Classe base para tasks que executam trabalho em thread separada.
Fornece mecanismo de captura de excecoes, callbacks de sucesso/erro
e resultado tipado.

Melhorias:
- estimated_ram: subclasses podem fornecer estimativa de RAM
- _check_during_execution(): verificacao periodica durante task
- can_execute() agora usa estimated_ram
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.governor.ResourceGovernor import ResourceGovernor


class BaseTask(ABC):
    """
    Wrapper para execucao de trabalho pesado em background thread.

    Fluxo interno:
        1. run() eh executado em thread separada
        2. run() chama _run() com a logica real
        3. Se _run() lanca excecao, captura em self.exception, retorna False
        4. Se _run() retornar True, self.result contem o resultado
        5. finished(success) eh chamado na thread principal
        6. success=True -> dispara on_success(self.result)
        7. success=False -> dispara on_error(self.exception)

    Para tasks longas, chamar _check_during_execution() dentro de _run().
    """

    def __init__(
        self,
        description: str,
        governor: Optional[ResourceGovernor] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ):
        self.description: str = description
        self.exception: Optional[Exception] = None
        self.result: Any = None
        self.on_success: Optional[Callable[[Any], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self._is_cancelled: bool = False
        self._governor: Optional[ResourceGovernor] = governor
        self._estimated_ram: int = 0  # bytes, subclasse pode setar
        self._tool_key: str = tool_key

    def get_logger(self) -> LogUtils:
        """
        Retorna um LogUtils configurado com a tool_key da task.

        A tool_key é definida no __init__ (default ToolKey.UNTRACEABLE).
        O class_name usado é o nome da classe concreta da task.
        """
        return LogUtils(tool=self._tool_key, class_name=self.__class__.__name__)

    @property
    def estimated_ram(self) -> int:
        """
        RAM estimada para esta task (bytes).
        Subclasses podem sobrescrever para fornecer estimativa real.
        0 = sem estimativa (usa apenas headroom basico).
        """
        return self._estimated_ram

    def _check_during_execution(self) -> bool:
        """
        Verifica recursos DURANTE execucao da task.
        Use dentro de _run() em loops longos:
            if not self._check_during_execution():
                self.cancel()
                return False
        """
        if self._is_cancelled:
            return False
        if self._governor is not None and not self._governor.check_during_execution():
            return False
        return True

    @abstractmethod
    def _run(self) -> bool:
        """
        Logica pesada executada em background.
        Deve retornar True se bem-sucedido, False se falhou.
        Define self.result com o resultado produzido.

        Para tasks longas com loops, chamar _check_during_execution()
        periodicamente para evitar OOM.
        """
        ...

    def run(self) -> bool:
        """
        Metodo principal executado em thread separada.
        Nao sobrescrever — sobrescreva _run().
        Verifica governor (com estimated_ram) e cancelamento antes de executar.
        """
        try:
            if self._is_cancelled:
                return False

            if self._governor is not None:
                can, reason = self._governor.can_execute(estimated_ram=self.estimated_ram)
                if not can:
                    self.exception = RuntimeError(reason)
                    return False

            success = self._run()
            return success
        except Exception as e:
            self.exception = e
            return False

    def finished(self, success: bool) -> None:
        if success:
            if self.on_success:
                self.on_success(self.result)
        else:
            if self.on_error:
                self.on_error(self.exception)
            else:
                import logging
                logging.warning(
                    f"[BaseTask] Task '{self.description}' error "
                    f"sem callback: {self.exception}"
                )

    def cancel(self) -> None:
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def __repr__(self) -> str:
        status = "ok" if self.exception is None else f"error: {self.exception}"
        ram = self._estimated_ram
        ram_str = f" | RAM: {ram}B" if ram > 0 else ""
        return f"<BaseTask '{self.description}' [{status}]{ram_str}>"
