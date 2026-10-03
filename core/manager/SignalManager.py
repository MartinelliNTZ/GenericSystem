# -*- coding: utf-8 -*-
"""
SignalManager — Orquestrador central de sinais do Aetheris ToolBox
Herda do SignalCatalog para manter o catálogo como fonte única da verdade.
Os sinais são definidos APENAS em SignalCatalog — não redeclarar aqui.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

from core.manager.SignalCatalog import SignalCatalog


class SignalManager(SignalCatalog):
    """
    Singleton que centraliza os sinais do sistema.
    Herda todos os sinais do SignalCatalog (fonte única da verdade).
    """

    _instance: SignalManager | None = None

    def __new__(cls, parent: QObject | None = None) -> SignalManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent: QObject | None = None) -> None:
        if self._initialized:
            return
        self._initialized = True
        super().__init__(parent)
        SignalManager._instance = self

    @classmethod
    def instance(cls) -> SignalManager:
        if cls._instance is None:
            SignalManager()
        return cls._instance  # type: ignore[return-value]
