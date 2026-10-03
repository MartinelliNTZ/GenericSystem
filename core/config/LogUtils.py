# -*- coding: utf-8 -*-

"""
LogUtils — Logger estruturado em JSON para o Aetheris ToolBox
==============================================================
**Um unico arquivo JSON por execucao do programa.**
Todas as instancias de LogUtils escrevem no mesmo arquivo.

Suporta multiprocessamento: processos filhos (joblib.Parallel)
escrevem no MESMO arquivo que o processo principal, usando
append mode + formato JSONL (um JSON por linha).

O arquivo e criado no primeiro `log()` / `info()` / etc. chamado.
O nome segue o formato: ``YYYYMMDD-HHMMSS_AetherisToolBox.json``

Uso:
    from core.config.LogUtils import LogUtils

    logger = LogUtils(tool="Console", class_name="ConsoleTool")
    logger.info("Sistema inicializado")
    logger.warning("Memoria baixa", code="MEM_LOW", free_mb=128)
"""

from __future__ import annotations

import json
import os as _os
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar


class LogUtils:
    """
    Logger que escreve eventos estruturados em JSON.

    **Compartilhado**: todas as instancias de LogUtils escrevem no mesmo
    arquivo JSON da execucao atual. Cada execucao gera um novo arquivo.

    Suporta multiprocessamento via variavel de ambiente: o processo
    principal define _AETHERIS_LOG_FILE no environ, e os processos
    filhos (joblib.Parallel) usam o mesmo caminho.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    LEVEL_COLORS = {
        "DEBUG": "#9CA3AF",
        "INFO": "#10B981",
        "WARNING": "#F59E0B",
        "ERROR": "#DC2626",
        "CRITICAL": "#991B1B",
    }

    LEVEL_ORDER = [DEBUG, INFO, WARNING, ERROR, CRITICAL]

    _LOG_DIR: Path = Path(__file__).resolve().parent.parent.parent / "log"

    _session_path: ClassVar[Path | None] = None
    _session_events: ClassVar[list[dict]] = []
    _session_started: ClassVar[bool] = False
    _LOG_FILE_ENV: ClassVar[str] = "_AETHERIS_LOG_FILE"

    def __new__(cls, *, tool: str, class_name: str, level: str | None = None) -> "LogUtils":
        instance = super().__new__(cls)
        instance._tool = tool
        instance._class_name = class_name
        instance._level = level if level is not None else cls.INFO
        return instance

    def set_level(self, level: str) -> None:
        self._level = level

    @property
    def level(self) -> str:
        return self._level

    @property
    def tool(self) -> str:
        return self._tool

    @property
    def class_name(self) -> str:
        return self._class_name

    def log(self, msg: str, *, level: str | None = None,
            code: str | None = None, **data: Any) -> None:
        level = level if level is not None else self.INFO
        if not self._allow(level):
            return
        self._ensure_session()
        event = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "tool": self._tool,
            "class": self._class_name,
            "message": msg,
        }
        if code is not None:
            event["code"] = code
        if data:
            event["data"] = data
        self._session_events.append(event)
        self._flush()

    def debug(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        self.log(msg, level=self.DEBUG, code=code, **data)

    def info(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        self.log(msg, level=self.INFO, code=code, **data)

    def warning(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        self.log(msg, level=self.WARNING, code=code, **data)

    def error(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        self.log(msg, level=self.ERROR, code=code, **data)

    def critical(self, msg: str, *, code: str | None = None, **data: Any) -> None:
        self.log(msg, level=self.CRITICAL, code=code, **data)

    def _allow(self, level: str) -> bool:
        if self._level not in self.LEVEL_ORDER:
            return True
        if level not in self.LEVEL_ORDER:
            return True
        return self.LEVEL_ORDER.index(level) >= self.LEVEL_ORDER.index(self._level)

    @classmethod
    def _ensure_session(cls) -> Path:
        if not cls._session_started:
            env_path = _os.environ.get(cls._LOG_FILE_ENV)
            if env_path:
                cls._session_path = Path(env_path)
            else:
                cls._LOG_DIR.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                cls._session_path = cls._LOG_DIR / f"{ts}_AetherisToolBox.json"
                _os.environ[cls._LOG_FILE_ENV] = str(cls._session_path)
            cls._session_started = True
            cls._session_events = []
        return cls._session_path  # type: ignore

    @classmethod
    def _file(cls) -> Path:
        return cls._ensure_session()

    @classmethod
    def _flush(cls) -> None:
        if cls._session_path is None or not cls._session_events:
            return
        with open(cls._session_path, "a", encoding="utf-8") as f:
            for event in cls._session_events:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        cls._session_events = []

    @classmethod
    def session_file(cls) -> Path | None:
        return cls._session_path

    @classmethod
    def read_session_events(cls) -> list[dict]:
        if cls._session_path is None or not cls._session_path.exists():
            return []
        events: list[dict] = []
        with open(cls._session_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return events
            if content.startswith("["):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return events
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("{") and line.endswith("}"):
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return events
