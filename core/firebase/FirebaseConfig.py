# -*- coding: utf-8 -*-
"""
FirebaseConfig — Gerenciador de configurações e credenciais do Firebase
========================================================================
Centraliza a leitura e gravação das configurações do Firebase usando
Preferences e variáveis de ambiente com suporte a ToolKey.FIREBASE.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil
from utils.Preferences import Preferences


class FirebaseConfig(BaseUtil):
    """Gerenciador central de credenciais e parâmetros do Firebase."""

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Retorna o dicionário completo de configuração do Firebase."""
        return Preferences.load_tool_prefs(ToolKey.FIREBASE)

    @classmethod
    def save_config(cls, data: Dict[str, Any]) -> None:
        """Salva configurações do Firebase via Preferences."""
        Preferences.save_tool_prefs(ToolKey.FIREBASE, data)

    @classmethod
    def get_api_key(cls) -> str:
        """Retorna a Web API Key do projeto Firebase."""
        cfg = cls.get_config()
        return str(cfg.get("api_key") or os.getenv("FIREBASE_API_KEY", "")).strip()

    @classmethod
    def get_project_id(cls) -> str:
        """Retorna o Project ID do projeto Firebase."""
        cfg = cls.get_config()
        return str(cfg.get("project_id") or os.getenv("FIREBASE_PROJECT_ID", "")).strip()

    @classmethod
    def get_storage_bucket(cls) -> str:
        """Retorna o nome do bucket do Firebase Storage."""
        cfg = cls.get_config()
        bucket = str(cfg.get("storage_bucket") or os.getenv("FIREBASE_STORAGE_BUCKET", "")).strip()
        if not bucket and cls.get_project_id():
            return f"{cls.get_project_id()}.appspot.com"
        return bucket

    @classmethod
    def get_service_account_path(cls) -> str:
        """Retorna o caminho do arquivo JSON de credencial de conta de serviço."""
        cfg = cls.get_config()
        return str(cfg.get("service_account_path") or os.getenv("FIREBASE_SERVICE_ACCOUNT", "")).strip()
