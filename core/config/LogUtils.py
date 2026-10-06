# -*- coding: utf-8 -*-

"""
LogUtils — Logger estruturado em JSON para o Aetheris ToolBox
==============================================================
Cada **canal** gera um arquivo JSON por execução do programa. Todas as
instâncias de LogUtils do mesmo canal escrevem no MESMO arquivo.
O canal padrão (``main``) usa a raiz ``log/``; canais nomeados usam uma
subpasta própria (ex: ``log/database/``), mantendo o registro do banco de
dados desacoplado do log geral.

Suporta multiprocessamento: processos filhos (joblib.Parallel)
escrevem no MESMO arquivo que o processo principal, usando
append mode + formato JSONL (um JSON por linha).

O arquivo é criado no primeiro `log()` / `info()` / etc. chamado.
Nome do arquivo: ``YYYYMMDD-HHMMSS_<slug>.json`` (slug = APP_SLUG no canal
padrão, ou o próprio nome do canal).

Uso:
    from core.config.LogUtils import LogUtils

    logger = LogUtils(tool="Console", class_name="ConsoleTool")
    logger.info("Sistema inicializado")

    db_logger = LogUtils(tool="Firebase", class_name="FirestoreService",
                         channel=LogUtils.DATABASE_CHANNEL)
    db_logger.info("Documento salvo", code="FS_SAVE_OK")
"""

from __future__ import annotations

import json
import os as _os
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from utils.StringUtils import StringUtils


class LogUtils:
    """
    Logger que escreve eventos estruturados em JSON, por canal.

    **Compartilhado por canal**: todas as instancias de LogUtils do mesmo
    canal escrevem no mesmo arquivo JSON da execucao atual. Cada execucao
    gera um novo arquivo por canal. O canal padrao (``main``) mantem o
    comportamento historico (arquivo unico em ``log/``).

    Suporta multiprocessamento via variavel de ambiente: o processo
    principal define a variavel do canal no environ, e os processos
    filhos (joblib.Parallel) usam o mesmo caminho.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    # Canais conhecidos. O canal ``main`` e o log geral; ``database``
    # desacopla o registro do banco de dados em arquivo proprio.
    DEFAULT_CHANNEL: ClassVar[str] = "main"
    DATABASE_CHANNEL: ClassVar[str] = "database"

    LEVEL_COLORS = {
        "DEBUG": "#9CA3AF",
        "INFO": "#10B981",
        "WARNING": "#F59E0B",
        "ERROR": "#DC2626",
        "CRITICAL": "#991B1B",
    }

    LEVEL_ORDER = [DEBUG, INFO, WARNING, ERROR, CRITICAL]

    _LOG_DIR: Path = Path(__file__).resolve().parent.parent.parent / "log"

    # Estado por canal: {canal: {"path": Path, "events": list[dict]}}
    _sessions: ClassVar[dict[str, dict]] = {}
    _LOG_FILE_ENV: ClassVar[str] = f"_{StringUtils.APP_ID.upper()}_LOG_FILE"

    def __new__(
        cls,
        *,
        tool: str,
        class_name: str,
        level: str | None = None,
        channel: str | None = None,
    ) -> "LogUtils":
        instance = super().__new__(cls)
        instance._tool = tool
        instance._class_name = class_name
        instance._level = level if level is not None else cls.INFO
        instance._channel = channel or cls.DEFAULT_CHANNEL
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

    @property
    def channel(self) -> str:
        return self._channel

    def log(self, msg: str, *, level: str | None = None,
            code: str | None = None, **data: Any) -> None:
        level = level if level is not None else self.INFO
        if not self._allow(level):
            return
        self._ensure_session(self._channel)
        event = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "tool": self._tool,
            "class": self._class_name,
            "channel": self._channel,
            "message": msg,
        }
        if code is not None:
            event["code"] = code
        if data:
            event["data"] = data
        self._sessions[self._channel]["events"].append(event)
        self._flush(self._channel)

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
    def _ensure_session(cls, channel: str | None = None) -> Path:
        channel = channel or cls.DEFAULT_CHANNEL
        session = cls._sessions.get(channel)
        if session is not None:
            return session["path"]

        env_key = cls._env_key(channel)
        env_path = _os.environ.get(env_key)
        if env_path:
            path = Path(env_path)
        else:
            directory = cls._channel_dir(channel)
            directory.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            path = directory / f"{ts}_{cls._channel_slug(channel)}.json"
            _os.environ[env_key] = str(path)

        cls._sessions[channel] = {"path": path, "events": []}
        return path

    @classmethod
    def _env_key(cls, channel: str) -> str:
        if channel == cls.DEFAULT_CHANNEL:
            return cls._LOG_FILE_ENV
        return f"{cls._LOG_FILE_ENV}_{channel.upper()}"

    @classmethod
    def _channel_dir(cls, channel: str) -> Path:
        if channel == cls.DEFAULT_CHANNEL:
            return cls._LOG_DIR
        return cls._LOG_DIR / channel

    @classmethod
    def _channel_slug(cls, channel: str) -> str:
        if channel == cls.DEFAULT_CHANNEL:
            return StringUtils.APP_SLUG
        return channel

    @classmethod
    def _flush(cls, channel: str | None = None) -> None:
        channel = channel or cls.DEFAULT_CHANNEL
        session = cls._sessions.get(channel)
        if session is None or not session["events"]:
            return
        with open(session["path"], "a", encoding="utf-8") as f:
            for event in session["events"]:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        session["events"] = []

    @classmethod
    def session_file(cls, channel: str | None = None) -> Path | None:
        session = cls._sessions.get(channel or cls.DEFAULT_CHANNEL)
        return session["path"] if session else None

    @classmethod
    def read_session_events(cls, channel: str | None = None) -> list[dict]:
        path = cls.session_file(channel)
        if path is None or not path.exists():
            return []
        events: list[dict] = []
        with open(path, "r", encoding="utf-8") as f:
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
