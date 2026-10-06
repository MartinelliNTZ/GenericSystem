# -*- coding: utf-8 -*-
"""
FirebaseAuthService — Serviço de autenticação com Firebase Auth
===============================================================
Executa autenticação client-side usando a REST API do Google Identity Toolkit.
Gerencia tokens JWT (idToken, refreshToken) e sessões em Preferences.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import requests

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseConfig import FirebaseConfig
from core.manager.SignalManager import SignalManager
from utils.BaseUtil import BaseUtil
from utils.Preferences import Preferences


class FirebaseAuthService(BaseUtil):
    """Serviço de autenticação de usuários via Firebase Auth REST API."""

    _SIGNIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    _SIGNUP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
    _TOKEN_URL = "https://securetoken.googleapis.com/v1/token"
    _LOOKUP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:lookup"

    @classmethod
    def sign_in_with_email(cls, email: str, password: str, name: str = "") -> Optional[Dict[str, Any]]:
        """Autentica usuário com e-mail e senha.

        Retorna os dados da sessão ou None em caso de falha.
        """
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseAuthService")
        api_key = FirebaseConfig.get_api_key()
        if not api_key:
            logger.error("API Key do Firebase não configurada", code="FB_NO_APIKEY")
            return None

        url = f"{cls._SIGNIN_URL}?key={api_key}"
        payload = {"email": email, "password": password, "returnSecureToken": True}

        try:
            resp = requests.post(url, json=payload, timeout=12)
            data = resp.json()
            if resp.status_code != 200:
                err_code = data.get("error", {}).get("message", "FALHA_LOGIN")
                logger.error("Falha ao autenticar no Firebase", code="FB_AUTH_FAIL", error=err_code)
                return None

            cls._save_session(data, name=name)
            logger.info("Usuário autenticado no Firebase", code="FB_AUTH_OK", email=email, name=name)
            SignalManager.instance().cloud_auth_changed.emit({
                "logged_in": True,
                "user": cls.get_current_user(),
            })
            return data
        except requests.exceptions.RequestException as e:
            logger.error("Erro de rede ao conectar ao Firebase Auth", code="FB_NET_ERR", error=str(e))
            return None
        except Exception as e:
            logger.error("Erro inesperado no login Firebase", code="FB_AUTH_UNEXPECTED", error=str(e))
            return None

    @classmethod
    def refresh_id_token(cls) -> Optional[str]:
        """Renova o idToken expirado usando o refreshToken salvo."""
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseAuthService")
        api_key = FirebaseConfig.get_api_key()
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        refresh_token = prefs.get("refresh_token", "")

        if not api_key or not refresh_token:
            return None

        url = f"{cls._TOKEN_URL}?key={api_key}"
        payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        try:
            resp = requests.post(url, data=payload, timeout=10)
            data = resp.json()
            if resp.status_code == 200:
                new_id_token = data.get("id_token", "")
                Preferences.save_tool_prefs(ToolKey.FIREBASE, {
                    "id_token": new_id_token,
                    "refresh_token": data.get("refresh_token", refresh_token),
                })
                return new_id_token
            logger.warning("Falha ao renovar token Firebase", code="FB_REFRESH_FAIL")
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Erro de rede ao renovar token", code="FB_REFRESH_NET_ERR", error=str(e))
            return None

    @classmethod
    def sign_out(cls) -> None:
        """Limpa as credenciais salvas e notifica a aplicação."""
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseAuthService")
        Preferences.save_tool_prefs(ToolKey.FIREBASE, {
            "name": "",
            "id_token": "",
            "refresh_token": "",
            "local_id": "",
            "email": "",
        })
        logger.info("Sessão Firebase encerrada", code="FB_SIGNOUT")
        SignalManager.instance().cloud_auth_changed.emit({
            "logged_in": False,
            "user": {},
        })

    @classmethod
    def is_authenticated(cls) -> bool:
        """Verifica se existe id_token registrado nas preferências."""
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        return bool(prefs.get("id_token"))

    @classmethod
    def get_current_user(cls) -> Dict[str, Any]:
        """Retorna dados do usuário atualmente salvo."""
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        email = prefs.get("email", "")
        fallback_name = email.split("@")[0].replace(".", " ").title() if email else ""
        return {
            "name": prefs.get("name") or fallback_name,
            "email": email,
            "local_id": prefs.get("local_id", ""),
            "id_token": prefs.get("id_token", ""),
        }

    @classmethod
    def _save_session(cls, auth_data: Dict[str, Any], name: str = "") -> None:
        """Persiste os dados de autenticação em Preferences."""
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        saved_name = name or prefs.get("name", "")
        Preferences.save_tool_prefs(ToolKey.FIREBASE, {
            "name": saved_name,
            "id_token": auth_data.get("idToken", ""),
            "refresh_token": auth_data.get("refreshToken", ""),
            "local_id": auth_data.get("localId", ""),
            "email": auth_data.get("email", ""),
        })
