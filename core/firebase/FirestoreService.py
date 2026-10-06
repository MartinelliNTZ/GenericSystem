# -*- coding: utf-8 -*-
"""
FirestoreService — Serviço de acesso ao Cloud Firestore
======================================================
Permite leitura, gravação e listagem de documentos via Firestore REST API v1.
Inclui conversão automática entre tipos Python e Firestore fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import requests

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseAuthService import FirebaseAuthService
from core.firebase.FirebaseConfig import FirebaseConfig
from utils.BaseUtil import BaseUtil
from utils.Preferences import Preferences


class FirestoreService(BaseUtil):
    """Serviço de manipulação de documentos no Cloud Firestore."""

    @classmethod
    def _base_url(cls) -> str:
        project_id = FirebaseConfig.get_project_id()
        return f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"

    @classmethod
    def _auth_headers(cls) -> Dict[str, str]:
        prefs = Preferences.load_tool_prefs(ToolKey.FIREBASE)
        token = prefs.get("id_token", "")
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def dict_to_firestore(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte dicionário Python para estrutura de campos do Firestore."""
        fields: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, str):
                fields[k] = {"stringValue": v}
            elif isinstance(v, bool):
                fields[k] = {"booleanValue": v}
            elif isinstance(v, int):
                fields[k] = {"integerValue": str(v)}
            elif isinstance(v, float):
                fields[k] = {"doubleValue": v}
            elif isinstance(v, dict):
                fields[k] = {"mapValue": cls.dict_to_firestore(v)}
            elif isinstance(v, list):
                fields[k] = {"arrayValue": {"values": [cls._val_to_firestore(item) for item in v]}}
            elif v is None:
                fields[k] = {"nullValue": None}
            else:
                fields[k] = {"stringValue": str(v)}
        return {"fields": fields}

    @classmethod
    def _val_to_firestore(cls, v: Any) -> Dict[str, Any]:
        if isinstance(v, str):
            return {"stringValue": v}
        if isinstance(v, bool):
            return {"booleanValue": v}
        if isinstance(v, (int, float)):
            return {"doubleValue": float(v)}
        if isinstance(v, dict):
            return {"mapValue": cls.dict_to_firestore(v)}
        return {"stringValue": str(v)}

    @classmethod
    def firestore_to_dict(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Converte documento bruto do Firestore em dicionário Python comum."""
        fields = doc.get("fields", {})
        result: Dict[str, Any] = {}
        for k, v in fields.items():
            result[k] = cls._extract_val(v)
        return result

    @classmethod
    def _extract_val(cls, val_dict: Dict[str, Any]) -> Any:
        if "stringValue" in val_dict:
            return val_dict["stringValue"]
        if "booleanValue" in val_dict:
            return val_dict["booleanValue"]
        if "integerValue" in val_dict:
            return int(val_dict["integerValue"])
        if "doubleValue" in val_dict:
            return float(val_dict["doubleValue"])
        if "mapValue" in val_dict:
            return cls.firestore_to_dict(val_dict["mapValue"])
        if "arrayValue" in val_dict:
            return [cls._extract_val(item) for item in val_dict["arrayValue"].get("values", [])]
        if "nullValue" in val_dict:
            return None
        return None

    @classmethod
    def get_document(
        cls,
        collection: str,
        doc_id: str,
        tool_key: str = ToolKey.FIREBASE.value,
    ) -> Optional[Dict[str, Any]]:
        """Busca um documento específico na coleção informada."""
        logger = cls._get_logger(tool_key, "FirestoreService", channel=LogUtils.DATABASE_CHANNEL)
        url = f"{cls._base_url()}/{collection}/{doc_id}"

        try:
            resp = requests.get(url, headers=cls._auth_headers(), timeout=12)
            if resp.status_code == 401:
                new_token = FirebaseAuthService.refresh_id_token()
                if new_token:
                    resp = requests.get(url, headers=cls._auth_headers(), timeout=12)

            if resp.status_code == 200:
                return cls.firestore_to_dict(resp.json())
            logger.warning(f"Documento não encontrado: {collection}/{doc_id}", code="FS_NOT_FOUND")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar documento {collection}/{doc_id}", code="FS_GET_ERR", error=str(e))
            return None

    @classmethod
    def save_document(
        cls,
        collection: str,
        doc_id: str,
        data: Dict[str, Any],
        tool_key: str = ToolKey.FIREBASE.value,
    ) -> bool:
        """Cria ou substitui um documento no Firestore com dados informados."""
        logger = cls._get_logger(tool_key, "FirestoreService", channel=LogUtils.DATABASE_CHANNEL)
        url = f"{cls._base_url()}/{collection}/{doc_id}"
        payload = cls.dict_to_firestore(data)

        try:
            resp = requests.patch(url, json=payload, headers=cls._auth_headers(), timeout=12)
            if resp.status_code == 401:
                new_token = FirebaseAuthService.refresh_id_token()
                if new_token:
                    resp = requests.patch(url, json=payload, headers=cls._auth_headers(), timeout=12)

            if resp.status_code in (200, 201):
                logger.info(f"Documento salvo: {collection}/{doc_id}", code="FS_SAVE_OK")
                return True
            logger.error(f"Falha ao salvar documento {collection}/{doc_id}", code="FS_SAVE_FAIL", error=resp.text)
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao salvar documento {collection}/{doc_id}", code="FS_SAVE_NET_ERR", error=str(e))
            return False

    @classmethod
    def list_documents(
        cls,
        collection: str,
        page_size: int = 300,
        tool_key: str = ToolKey.FIREBASE.value,
    ) -> Dict[str, Dict[str, Any]]:
        """Lista os documentos da coleção. Retorna ``{doc_id: dados}``."""
        logger = cls._get_logger(tool_key, "FirestoreService", channel=LogUtils.DATABASE_CHANNEL)
        url = f"{cls._base_url()}/{collection}?pageSize={page_size}"

        try:
            resp = requests.get(url, headers=cls._auth_headers(), timeout=20)
            if resp.status_code == 401:
                new_token = FirebaseAuthService.refresh_id_token()
                if new_token:
                    resp = requests.get(url, headers=cls._auth_headers(), timeout=20)

            if resp.status_code != 200:
                logger.warning(f"Falha ao listar coleção {collection}", code="FS_LIST_FAIL", status=resp.status_code)
                return {}

            documents = resp.json().get("documents", [])
            result: Dict[str, Dict[str, Any]] = {}
            for doc in documents:
                doc_id = str(doc.get("name", "")).rsplit("/", 1)[-1]
                if doc_id:
                    result[doc_id] = cls.firestore_to_dict(doc)
            logger.info(f"Coleção {collection} listada: {len(result)} documento(s)", code="FS_LIST_OK")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao listar coleção {collection}", code="FS_LIST_NET_ERR", error=str(e))
            return {}

    @classmethod
    def delete_document(
        cls,
        collection: str,
        doc_id: str,
        tool_key: str = ToolKey.FIREBASE.value,
    ) -> bool:
        """Remove um documento da coleção informada."""
        logger = cls._get_logger(tool_key, "FirestoreService", channel=LogUtils.DATABASE_CHANNEL)
        url = f"{cls._base_url()}/{collection}/{doc_id}"

        try:
            resp = requests.delete(url, headers=cls._auth_headers(), timeout=12)
            if resp.status_code == 401:
                new_token = FirebaseAuthService.refresh_id_token()
                if new_token:
                    resp = requests.delete(url, headers=cls._auth_headers(), timeout=12)

            if resp.status_code in (200, 204):
                logger.info(f"Documento removido: {collection}/{doc_id}", code="FS_DELETE_OK")
                return True
            logger.error(f"Falha ao remover documento {collection}/{doc_id}", code="FS_DELETE_FAIL", error=resp.text)
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao remover documento {collection}/{doc_id}", code="FS_DELETE_NET_ERR", error=str(e))
            return False

    @classmethod
    def save_documents(
        cls,
        collection: str,
        documents: Dict[str, Dict[str, Any]],
        tool_key: str = ToolKey.FIREBASE.value,
    ) -> int:
        """Salva vários documentos (``doc_id`` → dados). Retorna quantos salvaram."""
        saved = 0
        for doc_id, data in documents.items():
            if cls.save_document(collection, doc_id, data, tool_key=tool_key):
                saved += 1
        return saved
