# -*- coding: utf-8 -*-
"""
FirebaseServiceAccountAuth — Autenticação server-side por conta de serviço
=========================================================================
Obtém tokens OAuth2 (``Bearer``) a partir de um arquivo de conta de serviço do
Firebase (Admin SDK), **dispensando Web API Key e login de usuário**. O token é
cacheado em memória e renovado automaticamente pouco antes de expirar.

Requer o pacote ``google-auth`` (ver ``requirements.txt``).

Uso:
    from core.firebase.FirebaseServiceAccountAuth import FirebaseServiceAccountAuth

    if FirebaseServiceAccountAuth.is_configured():
        token = FirebaseServiceAccountAuth.get_token()
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseConfig import FirebaseConfig
from utils.BaseUtil import BaseUtil

# Escopos necessários para Firestore (datastore) e Storage (devstorage).
_SCOPES = [
    "https://www.googleapis.com/auth/datastore",
    "https://www.googleapis.com/auth/devstorage.read_write",
]


class FirebaseServiceAccountAuth(BaseUtil):
    """Gerencia o token OAuth2 de uma conta de serviço do Firebase."""

    _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    _SAFETY_WINDOW = timedelta(seconds=60)

    _lock = threading.Lock()
    _credentials = None
    _token: Optional[str] = None
    _expiry: Optional[datetime] = None

    @classmethod
    def _account_file(cls) -> Optional[Path]:
        """Resolve o caminho absoluto do arquivo de conta de serviço."""
        raw = FirebaseConfig.get_service_account_path()
        if not raw:
            return None
        path = Path(raw)
        if not path.is_absolute():
            path = cls._PROJECT_ROOT / path
        return path

    @classmethod
    def is_configured(cls) -> bool:
        """True se há um arquivo de conta de serviço válido configurado."""
        path = cls._account_file()
        return bool(path and path.is_file())

    @classmethod
    def get_token(cls) -> Optional[str]:
        """Retorna um token OAuth2 válido (cacheado) ou ``None``."""
        if not cls.is_configured():
            return None
        with cls._lock:
            if cls._is_valid():
                return cls._token
            return cls._refresh_locked()

    @classmethod
    def refresh(cls) -> Optional[str]:
        """Força a renovação do token e retorna o novo valor."""
        if not cls.is_configured():
            return None
        with cls._lock:
            cls._credentials = None
            return cls._refresh_locked()

    # ── Internos ─────────────────────────────────────────────────────

    @classmethod
    def _is_valid(cls) -> bool:
        if not cls._token or cls._expiry is None:
            return False
        expiry = cls._expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < (expiry - cls._SAFETY_WINDOW)

    @classmethod
    def _refresh_locked(cls) -> Optional[str]:
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseServiceAccountAuth")
        path = cls._account_file()
        if path is None or not path.is_file():
            return None
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            if cls._credentials is None:
                cls._credentials = service_account.Credentials.from_service_account_file(
                    str(path), scopes=_SCOPES
                )
            cls._credentials.refresh(Request())
            cls._token = cls._credentials.token
            cls._expiry = cls._credentials.expiry
            logger.info("Token de conta de serviço renovado", code="FB_SA_TOKEN_OK")
            return cls._token
        except ImportError as e:
            logger.error(
                "Pacote google-auth não instalado",
                code="FB_SA_NO_LIB",
                error=str(e),
            )
            return None
        except Exception as e:
            cls._credentials = None
            cls._token = None
            cls._expiry = None
            logger.error(
                "Falha ao obter token da conta de serviço",
                code="FB_SA_TOKEN_ERR",
                error=str(e),
            )
            return None
