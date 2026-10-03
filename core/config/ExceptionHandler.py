# -*- coding: utf-8 -*-
"""
ExceptionHandler — Sistema global de captura de exceções
=========================================================
Previne crashes não tratados instalando hooks em três níveis:

1. **sys.excepthook** — Captura exceções Python não tratadas
2. **Qt message handler** — Captura warnings/errors do Qt (qInstallMessageHandler)
3. **Decorator @safe_exec** — Protege callbacks específicos contra crash

Todas as exceções são:
  - Logadas via LogUtils com traceback completo
  - Exibidas em um QMessageBox amigável (quando possível)
  - Impedidas de propagar (evita crash) sempre que seguro

Uso:
    from core.config.ExceptionHandler import ExceptionHandler

    # Instala os hooks globais (chamar uma vez no startup)
    ExceptionHandler.install()

    # Decorator para proteger callbacks específicos
    @ExceptionHandler.safe_exec
    def meu_callback():
        ...
"""

from __future__ import annotations

import sys
import traceback
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from core.config.LogUtils import LogUtils

F = TypeVar("F", bound=Callable[..., Any])

_logger = LogUtils(tool="System", class_name="ExceptionHandler")


class ExceptionHandler:
    """
    Gerenciador global de exceções não tratadas.

    Métodos de classe:
        install()           — Instala todos os hooks
        uninstall()         — Remove os hooks (para testes)
        safe_exec(func)     — Decorator que envolve função em try/except

    Atributos de classe:
        show_dialog         — Se True (padrão), exibe QMessageBox no excepthook
        last_exception      — Armazena a última exceção (evita loop recursivo)
    """

    _installed: bool = False
    _original_excepthook: Any = None
    _original_qt_handler: Any = None
    _recursion_guard: bool = False
    _systray_active: bool = False

    show_dialog: bool = True
    max_traceback_lines: int = 50

    # ═════════════════════════════════════════════════════════════════
    # Instalação dos hooks
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def install(cls) -> None:
        """Instala hooks globais de exceção. Chamar uma vez no startup."""
        if cls._installed:
            return

        _logger.info("Instalando hooks globais de exceção", code="EXC_HOOK_INSTALL")

        cls._original_excepthook = sys.excepthook
        sys.excepthook = cls._python_excepthook

        try:
            from PySide6.QtCore import qInstallMessageHandler
            cls._original_qt_handler = qInstallMessageHandler(None)
            qInstallMessageHandler(cls._qt_message_handler)
        except Exception as exc:
            _logger.warning("Falha ao instalar Qt message handler", code="QT_HOOK_FAIL", error=str(exc))

        cls._installed = True
        _logger.info("Hooks de exceção instalados com sucesso", code="EXC_HOOK_OK")

    @classmethod
    def uninstall(cls) -> None:
        """Remove os hooks instalados (útil para testes)."""
        if not cls._installed:
            return
        if cls._original_excepthook is not None:
            sys.excepthook = cls._original_excepthook
        if cls._original_qt_handler is not None:
            try:
                from PySide6.QtCore import qInstallMessageHandler
                qInstallMessageHandler(cls._original_qt_handler)
            except Exception:
                pass
        cls._installed = False
        _logger.info("Hooks de exceção removidos", code="EXC_HOOK_REMOVED")

    # ═════════════════════════════════════════════════════════════════
    # sys.excepthook
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def _python_excepthook(cls, exc_type: type, exc_value: BaseException, exc_tb: Optional[Any]) -> None:
        if cls._recursion_guard:
            import io
            buf = io.StringIO()
            traceback.print_exception(exc_type, exc_value, exc_tb, file=buf) if exc_tb else \
                traceback.print_exception(exc_type, exc_value, None, file=buf)
            print(f"[EXCEPTION GUARD] {buf.getvalue()}", file=sys.stderr)
            return

        cls._recursion_guard = True
        try:
            tb_lines = traceback.format_tb(exc_tb) if exc_tb else []
            tb_text = "".join(tb_lines)
            _logger.critical(
                f"Exceção não tratada: {exc_type.__name__}: {exc_value}",
                code="UNHANDLED_EXCEPTION",
                exception_type=exc_type.__name__,
                exception_message=str(exc_value),
                traceback=tb_text,
            )
            if cls.show_dialog:
                cls._show_error_dialog(
                    title="Erro Inesperado",
                    message=(
                        f"Ocorreu um erro inesperado.\n\nTipo: {exc_type.__name__}\n"
                        f"Detalhes: {exc_value}\n\nO erro foi registrado no log."
                    ),
                    detailed_text=f"Exceção: {exc_type.__name__}: {exc_value}\n\nTraceback:\n{tb_text}",
                )
        except Exception as inner_exc:
            print(f"[EXCEPTION HANDLER ERROR] {inner_exc}", file=sys.stderr)
            traceback.print_exception(exc_type, exc_value, exc_tb) if exc_tb else None
        finally:
            cls._recursion_guard = False

    # ═════════════════════════════════════════════════════════════════
    # Qt Message Handler
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def _qt_message_handler(cls, msg_type: Any, context: Any, message: str) -> None:
        from PySide6.QtCore import QtMsgType

        type_map = {
            QtMsgType.QtDebugMsg: "DEBUG", QtMsgType.QtInfoMsg: "INFO",
            QtMsgType.QtWarningMsg: "WARNING", QtMsgType.QtCriticalMsg: "ERROR",
            QtMsgType.QtFatalMsg: "CRITICAL",
        }
        level = type_map.get(msg_type, "WARNING")

        if cls._is_qt_noise(level, message):
            return

        from core.config.LogUtils import LogUtils
        qt_logger = LogUtils(tool="Qt", class_name="QtMessageHandler")
        log_method = getattr(qt_logger, level.lower(), qt_logger.warning)
        log_method(message, code=f"QT_{level}")

        if msg_type == QtMsgType.QtFatalMsg:
            cls._show_error_dialog(
                title="Erro Interno (Qt)",
                message=f"O sistema gráfico reportou um erro grave.\n\n{message}",
                detailed_text=f"Qt Fatal Error\n\nMensagem: {message}",
            )

    @classmethod
    def _is_qt_noise(cls, level: str, message: str) -> bool:
        noise = ["libpng warning", "QFont::setPixelSize", "setFeature is not available",
                 "Window surface was destroyed", "does not have a composition"]
        return any(p.lower() in message.lower() for p in noise)

    # ═════════════════════════════════════════════════════════════════
    # Decorators
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def safe_exec(cls, func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                tb_text = "".join(traceback.format_exc())
                _logger.error(f"safe_exec em {func.__name__}: {exc}", code="SAFE_EXEC_CAUGHT",
                              function=func.__name__, error=str(exc), traceback=tb_text)
                if cls.show_dialog:
                    from PySide6.QtCore import QTimer
                    from PySide6.QtWidgets import QApplication
                    if QApplication.instance() is not None:
                        QTimer.singleShot(0, lambda: cls._show_error_dialog(
                            title="Erro em Operação",
                            message=f"Erro ao executar '{func.__name__}'.\n\n{exc}",
                            detailed_text=tb_text,
                        ))
                return None
        return wrapper  # type: ignore[return-value]

    @classmethod
    def safe_slot(cls, func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except (Exception, SystemExit, KeyboardInterrupt) as exc:
                _logger.error(f"safe_slot em {func.__name__}: {exc}", code="SAFE_SLOT_CAUGHT",
                              function=func.__name__, error=str(exc))
                return None
        return wrapper  # type: ignore[return-value]

    # ═════════════════════════════════════════════════════════════════
    # Diálogo de erro (importa MessageBox sob demanda)
    # ═════════════════════════════════════════════════════════════════

    @classmethod
    def _show_error_dialog(cls, title: str, message: str, detailed_text: str = "") -> None:
        from PySide6.QtWidgets import QApplication
        if QApplication.instance() is None:
            return
        try:
            from utils.MessageBox import MessageBox
            MessageBox.show_error(text=message, title=title, detail=detailed_text)
        except Exception as dlg_exc:
            _logger.error("Falha ao exibir diálogo de erro", code="DLG_FAIL", dialog_error=str(dlg_exc))

    # ═════════════════════════════════════════════════════════════════
    # Utilitários
    # ═════════════════════════════════════════════════════════════════

    @staticmethod
    def try_exec(func: Callable[..., Any], *args: Any, fallback_return: Any = None,
                 log_as_warning: bool = False, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            tb_text = "".join(traceback.format_exc())
            log_method = _logger.warning if log_as_warning else _logger.error
            log_method(f"try_exec ({func.__name__}): {exc}", code="TRY_EXEC_CAUGHT",
                       function=func.__name__, error=str(exc), traceback=tb_text)
            return fallback_return

    @staticmethod
    def report_error(message: str, exc_info: Optional[Any] = None, code: str = "MANUAL_REPORT", **extra: Any) -> None:
        if exc_info is None:
            exc_info = sys.exc_info()
        tb_text = "".join(traceback.format_tb(exc_info[2])) if exc_info and exc_info[2] else ""
        _logger.error(message, code=code, traceback=tb_text, **extra)


# ═══════════════════════════════════════════════════════════════════════
# Atalhos
# ═══════════════════════════════════════════════════════════════════════

def safe_exec(func: F) -> F:
    return ExceptionHandler.safe_exec(func)


def safe_slot(func: F) -> F:
    return ExceptionHandler.safe_slot(func)