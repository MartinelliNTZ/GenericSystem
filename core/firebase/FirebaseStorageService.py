# -*- coding: utf-8 -*-
"""
FirebaseStorageService — Upload e Download de arquivos no Firebase Storage
==========================================================================
Permite transferência de arquivos grandes (backups ZIP, projetos .mtl)
usando a Firebase Storage REST API com autorização por token.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Callable, Optional
import requests

from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseAuthService import FirebaseAuthService
from core.firebase.FirebaseConfig import FirebaseConfig
from core.manager.SignalManager import SignalManager
from utils.BaseUtil import BaseUtil
from utils.Preferences import Preferences


class FirebaseStorageService(BaseUtil):
    """Serviço para upload e download de arquivos no Cloud Storage."""

    @classmethod
    def _get_token(cls) -> str:
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        return prefs.get("id_token", "")

    @classmethod
    def upload_file(
        cls,
        local_path: str,
        remote_path: str,
        content_type: str = "application/octet-stream",
        progress_cb: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Faz upload de um arquivo local para o Firebase Storage."""
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseStorageService")
        if not os.path.isfile(local_path):
            logger.error(f"Arquivo local não encontrado: {local_path}", code="STG_FILE_NOT_FOUND")
            return False

        bucket = FirebaseConfig.get_storage_bucket()
        if not bucket:
            logger.error("Bucket do Firebase Storage não configurado", code="STG_NO_BUCKET")
            return False

        encoded_name = urllib.parse.quote(remote_path, safe="")
        url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o?uploadType=media&name={encoded_name}"
        token = cls._get_token()
        headers = {"Content-Type": content_type}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            SignalManager.instance().cloud_sync_status.emit({
                "status": "uploading",
                "message": f"Enviando {os.path.basename(local_path)}...",
                "progress": 0.0,
            })

            file_size = os.path.getsize(local_path)
            with open(local_path, "rb") as f:
                data = f.read()

            resp = requests.post(url, data=data, headers=headers, timeout=120)
            if resp.status_code == 401:
                token = FirebaseAuthService.refresh_id_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    resp = requests.post(url, data=data, headers=headers, timeout=120)

            if resp.status_code in (200, 201):
                logger.info("Upload Firebase Storage concluído", code="STG_UPLOAD_OK", remote=remote_path)
                SignalManager.instance().cloud_sync_status.emit({
                    "status": "completed",
                    "message": "Upload concluído",
                    "progress": 100.0,
                })
                if progress_cb:
                    progress_cb(100.0)
                return True

            logger.error("Falha ao enviar arquivo para o Storage", code="STG_UPLOAD_ERR", error=resp.text)
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede no upload: {local_path}", code="STG_NET_ERR", error=str(e))
            return False
        except Exception as e:
            logger.error("Erro inesperado no upload Firebase", code="STG_UNEXPECTED", error=str(e))
            return False

    @classmethod
    def download_file(
        cls,
        remote_path: str,
        dest_local_path: str,
        progress_cb: Optional[Callable[[float], None]] = None,
    ) -> bool:
        """Baixa um arquivo do Firebase Storage para o caminho local informado."""
        logger = cls._get_logger(ToolKey.FIREBASE.value, "FirebaseStorageService")
        bucket = FirebaseConfig.get_storage_bucket()
        if not bucket:
            logger.error("Bucket do Firebase Storage não configurado", code="STG_NO_BUCKET")
            return False

        encoded_name = urllib.parse.quote(remote_path, safe="")
        url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{encoded_name}?alt=media"
        token = cls._get_token()
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=120)
            if resp.status_code == 401:
                token = FirebaseAuthService.refresh_id_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    resp = requests.get(url, headers=headers, stream=True, timeout=120)

            if resp.status_code != 200:
                logger.error("Falha ao baixar arquivo do Storage", code="STG_DL_ERR", status=resp.status_code)
                return False

            os.makedirs(os.path.dirname(os.path.abspath(dest_local_path)), exist_ok=True)
            with open(dest_local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

            logger.info("Download concluído com sucesso", code="STG_DL_OK", local=dest_local_path)
            if progress_cb:
                progress_cb(100.0)
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ao baixar {remote_path}", code="STG_DL_NET_ERR", error=str(e))
            return False
        except Exception as e:
            logger.error("Erro inesperado no download Firebase", code="STG_DL_UNEXPECTED", error=str(e))
            return False
