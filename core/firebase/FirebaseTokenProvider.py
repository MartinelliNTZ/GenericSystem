# -*- coding: utf-8 -*-
"""
FirebaseTokenProvider — Resolve o token de acesso (Bearer) do Firebase
======================================================================
Centraliza a obtenção do token usado nas chamadas REST (Firestore/Storage):

1. Se houver **conta de serviço** configurada, usa o token OAuth2 dela
   (server-side — dispensa Web API Key e login de usuário).
2. Caso contrário, usa o ``id_token`` da sessão do usuário (Preferences).

Uso:
    from core.firebase.FirebaseTokenProvider import FirebaseTokenProvider

    if FirebaseTokenProvider.has_credentials():
        token = FirebaseTokenProvider.get_token()
"""

from __future__ import annotations

from typing import Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.Preferences import Preferences


class FirebaseTokenProvider(BaseUtil):
    """Resolve o token de acesso do Firebase (conta de serviço ou usuário)."""

    @classmethod
    def _service_account(cls):
        """Importa o provedor de conta de serviço sob demanda (evita ciclo)."""
        from core.firebase.FirebaseServiceAccountAuth import FirebaseServiceAccountAuth
        return FirebaseServiceAccountAuth

    @classmethod
    def has_credentials(cls) -> bool:
        """True se há conta de serviço configurada ou sessão de usuário ativa."""
        if cls._service_account().is_configured():
            return True
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        return bool(prefs.get("id_token"))

    @classmethod
    def get_token(cls) -> str:
        """Retorna o token Bearer atual (conta de serviço tem prioridade)."""
        service_account = cls._service_account()
        if service_account.is_configured():
            token = service_account.get_token()
            if token:
                return token
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        return str(prefs.get("id_token", "") or "")

    @classmethod
    def refresh(cls) -> Optional[str]:
        """Força a renovação do token (conta de serviço ou usuário)."""
        service_account = cls._service_account()
        if service_account.is_configured():
            return service_account.refresh()
        from core.firebase.FirebaseAuthService import FirebaseAuthService
        return FirebaseAuthService.refresh_id_token()
