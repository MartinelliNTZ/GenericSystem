#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BootStrap — Singleton de inicialização da aplicação
=====================================================
Responsável por:
  1. Configurações iniciais de ambiente (TF, warnings)
  2. Criar a QApplication e aplicar o tema
  3. Registrar todas as ferramentas no ToolRegistry
  4. Instanciar a MainWindow com as ferramentas registradas
  5. Exibir a janela e iniciar o event loop

Uso:
    from core.config.BootStrap import BootStrap
    BootStrap().run()
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from core.config.ToolRegistry import ToolRegistry
from core.ui.ui_main import MainWindow
from resources.styles.AppStyles import AppStyles


class BootStrap:
    """
    Singleton que centraliza toda a inicialização da aplicação.
    """

    _instance: Optional["BootStrap"] = None

    def __new__(cls) -> "BootStrap":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._app: Optional[QApplication] = None
            cls._instance._window: Optional[MainWindow] = None
        return cls._instance

    # ═══════════════════════════════════════════════════════════════════════
    # Método principal
    # ═══════════════════════════════════════════════════════════════════════

    def run(self) -> None:
        """Executa o bootstrap completo da aplicação."""
        if self._initialized:
            return  # já inicializou, ignora

        self._setup_environment()
        self._init_logging()
        self._create_application()
        self._init_signals()
        self._register_tools()
        self._create_main_window()
        self._initialized = True
        self._show_and_run()

    # ═══════════════════════════════════════════════════════════════════════
    # Etapas internas
    # ═══════════════════════════════════════════════════════════════════════

    def _setup_environment(self) -> None:
        """
        Configura variáveis de ambiente e filtra warnings
        antes de qualquer import das bibliotecas pesadas.
        """
        # Suprime warnings do TensorFlow
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
        os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
        os.environ["TF_CPP_MAX_LOG_LEVEL"] = "3"

        # Suprime warnings de deprecação
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning, module="keras")

        # Instala hooks globais de captura de exceção
        # Deve ser o mais cedo possível para proteger todo o startup
        from core.config.ExceptionHandler import ExceptionHandler
        ExceptionHandler.install()
        ExceptionHandler.show_dialog = True

    def _init_logging(self) -> None:
        """
        Inicializa o sistema de logs: limpa arquivos antigos
        e registra o inicio da execucao.
        """
        from core.config.LogCleanup import LogCleanup
        from core.config.LogUtils import LogUtils

        removed = LogCleanup.run(max_files=5)
        logger = LogUtils(tool="System", class_name="BootStrap")
        logger.info("Inicializacao do sistema", code="BOOT_OK", logs_removidos=removed)

    def _create_application(self) -> None:
        """Cria a QApplication e aplica o tema global."""
        self._app = QApplication(sys.argv)
        self._app.setStyleSheet(AppStyles.global_stylesheet())

        font = QFont("Segoe UI", 10)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        self._app.setFont(font)

    def _init_signals(self) -> None:
        """Inicializa o SignalManager e conecta listeners globais."""
        from core.manager.SignalManager import SignalManager
        from core.config.LogUtils import LogUtils

        mgr = SignalManager.instance()
        mgr.tool_opened.connect(
            lambda name: print(f"[SignalManager] Ferramenta iniciada: {name}")
        )
        log = LogUtils(tool="System", class_name="BootStrap")
        log.info("SignalManager inicializado", code="SIG_MGR_OK")

    def _register_tools(self) -> None:
        """
        Registra todas as ferramentas padrao no ToolRegistry.
        As definicoes estao no metodo register_default_tools().
        """
        registry = ToolRegistry()
        registry.register_default_tools()

    def _create_main_window(self) -> None:
        """Instancia a MainWindow passando as tools registradas."""
        if self._app is None:
            raise RuntimeError("QApplication nao foi criada. Chame run().")
        registry = ToolRegistry()
        self._window = MainWindow(tools=registry.get_all())

    def _show_and_run(self) -> None:
        """Exibe a janela e entra no event loop."""
        if self._window is None:
            raise RuntimeError("MainWindow nao foi criada.")
        self._window.show()
        sys.exit(self._app.exec())

    # ═══════════════════════════════════════════════════════════════════════
    # Acesso à instância (para uso externo)
    # ═══════════════════════════════════════════════════════════════════════

    @property
    def window(self) -> Optional[MainWindow]:
        """Retorna a MainWindow já instanciada."""
        return self._window

    @property
    def application(self) -> Optional[QApplication]:
        """Retorna a QApplication já criada."""
        return self._app