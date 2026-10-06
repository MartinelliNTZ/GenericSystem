# -*- coding: utf-8 -*-
"""
FirebaseCredentialManager — Gerenciador de credenciais criptografadas
====================================================================
Armazena e recupera credenciais locais (e-mail e senha) de forma
criptografada usando PBKDF2 e derivação de chave vinculada à máquina,
evitando texto plano em disco.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class FirebaseCredentialManager(BaseUtil):
    """Gerencia armazenamento criptografado de credenciais Firebase."""

    _CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
    _CREDENTIALS_FILE = _CONFIG_DIR / ".firebase_auth.enc"

    @classmethod
    def get_credentials_path(cls) -> Path:
        """Retorna o caminho do arquivo criptografado de credenciais."""
        return cls._CREDENTIALS_FILE

    @classmethod
    def has_saved_credentials(cls) -> bool:
        """Verifica se o arquivo de credenciais criptografadas existe e não está vazio."""
        return cls._CREDENTIALS_FILE.is_file() and cls._CREDENTIALS_FILE.stat().st_size > 0

    @classmethod
    def _derive_key(cls, salt: bytes) -> bytes:
        """Gera chave a partir de semente do sistema operacional e salt."""
        machine_seed = (
            f"{os.getenv('COMPUTERNAME', 'Aetheris')}_"
            f"{os.getenv('USERNAME', 'User')}_"
            "AetherisToolBox_Firebase_SecureKey_2026"
        )
        return hashlib.pbkdf2_hmac("sha256", machine_seed.encode("utf-8"), salt, 100000)

    @classmethod
    def _keystream(cls, key: bytes, length: int) -> bytes:
        """Gera fluxo de chave pseudo-aleatório via HMAC/SHA256."""
        stream = bytearray()
        counter = 0
        while len(stream) < length:
            stream.extend(hashlib.sha256(key + counter.to_bytes(4, "big")).digest())
            counter += 1
        return bytes(stream[:length])

    @classmethod
    def save_credentials(cls, email: str, password: str, name: str = "") -> bool:
        """Criptografa e salva as credenciais no arquivo seguro."""
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseCredentialManager")
        cls._CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        payload = json.dumps({"name": name, "email": email, "password": password})
        data_bytes = payload.encode("utf-8")
        salt = os.urandom(16)
        key = cls._derive_key(salt)
        keystream = cls._keystream(key, len(data_bytes))
        ciphertext = bytes([b ^ k for b, k in zip(data_bytes, keystream)])

        token = base64.b64encode(salt + ciphertext).decode("utf-8")

        try:
            with open(cls._CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                f.write(token)
            logger.info("Credenciais Firebase criptografadas e salvas com sucesso", code="FB_CREDS_STORED")
            return True
        except OSError as e:
            logger.error("Falha ao salvar credenciais criptografadas", code="FB_CREDS_SAVE_ERR", error=str(e))
            return False

    @classmethod
    def load_credentials(cls) -> Optional[Dict[str, str]]:
        """Lê e descriptografa as credenciais do arquivo seguro."""
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseCredentialManager")
        if not cls.has_saved_credentials():
            return None

        try:
            with open(cls._CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                token = f.read().strip()

            raw = base64.b64decode(token.encode("utf-8"))
            salt = raw[:16]
            ciphertext = raw[16:]
            key = cls._derive_key(salt)
            keystream = cls._keystream(key, len(ciphertext))
            data_bytes = bytes([b ^ k for b, k in zip(ciphertext, keystream)])

            data = json.loads(data_bytes.decode("utf-8"))
            logger.info("Credenciais Firebase carregadas e descriptografadas", code="FB_CREDS_LOADED")
            return data
        except Exception as e:
            logger.error("Falha ao descriptografar credenciais Firebase", code="FB_CREDS_DECRYPT_ERR", error=str(e))
            return None

    @classmethod
    def get_user_name(cls) -> str:
        """Retorna o nome do usuário salvo ou fallback amigável a partir do e-mail."""
        creds = cls.load_credentials()
        if not creds:
            return ""
        name = creds.get("name", "").strip()
        if name:
            return name
        email = creds.get("email", "")
        return email.split("@")[0].replace(".", " ").title() if email else ""

    @classmethod
    def delete_credentials(cls) -> bool:
        """Remove o arquivo de credenciais criptografadas."""
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseCredentialManager")
        if not cls._CREDENTIALS_FILE.is_file():
            return True
        try:
            cls._CREDENTIALS_FILE.unlink()
            logger.info("Arquivo de credenciais removido", code="FB_CREDS_DELETED")
            return True
        except OSError as e:
            logger.error("Erro ao deletar credenciais", code="FB_CREDS_DEL_ERR", error=str(e))
            return False
