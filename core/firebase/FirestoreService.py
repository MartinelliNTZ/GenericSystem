# -*- coding: utf-8 -*-
"""
FirestoreService — Serviço de acesso ao Cloud Firestore
======================================================
Permite leitura, gravação e listagem de documentos via Firestore REST API v1.
Inclui conversão automática entre tipos Python e Firestore fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseConfig import FirebaseConfig
from core.firebase.FirebaseTokenProvider import FirebaseTokenProvider
from utils.BaseUtil import BaseUtil


class FirestoreService(BaseUtil):
    """Serviço de manipulação de documentos no Cloud Firestore."""

    # Limite de segurança de páginas ao listar uma coleção (300 docs/página).
    _MAX_PAGES = 50

    @classmethod
    def _base_url(cls) -> str:
        project_id = FirebaseConfig.get_project_id()
        return f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"

    @classmethod
    def _auth_headers(cls) -> Dict[str, str]:
        token = FirebaseTokenProvider.get_token()
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
                new_token = FirebaseTokenProvider.refresh()
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
                new_token = FirebaseTokenProvider.refresh()
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
        """Lista TODOS os documentos da coleção (pagina até o fim).

        O Firestore pode devolver MENOS documentos que o ``pageSize`` pedido
        (resposta grande) e sinaliza o restante em ``nextPageToken``. Ignorar o
        token fazia coleções grandes parecerem vazias/incompletas.
        """
        logger = cls._get_logger(tool_key, "FirestoreService", channel=LogUtils.DATABASE_CHANNEL)
        size = max(1, min(int(page_size), 1000))
        base = f"{cls._base_url()}/{collection}?pageSize={size}"
        result: Dict[str, Dict[str, Any]] = {}
        token = ""

        for _ in range(cls._MAX_PAGES):
            url = f"{base}&pageToken={quote(token)}" if token else base
            try:
                resp = requests.get(url, headers=cls._auth_headers(), timeout=20)
                if resp.status_code == 401:
                    if FirebaseTokenProvider.refresh():
                        resp = requests.get(url, headers=cls._auth_headers(), timeout=20)
                if resp.status_code != 200:
                    logger.warning(f"Falha ao listar coleção {collection}", code="FS_LIST_FAIL", status=resp.status_code)
                    return result
                data = resp.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro ao listar coleção {collection}", code="FS_LIST_NET_ERR", error=str(e))
                return result

            for doc in data.get("documents", []):
                doc_id = str(doc.get("name", "")).rsplit("/", 1)[-1]
                if doc_id:
                    result[doc_id] = cls.firestore_to_dict(doc)
            token = str(data.get("nextPageToken", "") or "")
            if not token:
                break

        logger.info(f"Coleção {collection} listada: {len(result)} documento(s)", code="FS_LIST_OK")
        return result

    @classmethod
    def query_documents(
        cls,
        collection: str,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        descending: bool = True,
        equals: Optional[Dict[str, str]] = None,
        tool_key: str = ToolKey.FIREBASE.value,
    ) -> List[Dict[str, Any]]:
        """Consulta documentos por igualdade e/ou ordem (``documents:runQuery``).

        Diferente de ``list_documents`` (ordem por ``doc_id``), aqui a ordem vem
        do Firestore — necessário para obter os registros mais recentes de
        coleções grandes.

        Args:
            order_by: campo de ordenação (``None`` = sem ordenação).
            limit: limite aplicado NO SERVIDOR (``None`` = sem limite).
            equals: filtros de igualdade ``{campo: string}`` (usa índice de campo
                único automático). Evite combinar com ``order_by`` em outro campo:
                o Firestore exigiria um índice composto.

        Returns:
            Lista de ``{"doc_id": ..., **campos}`` na ordem solicitada.
        """
        logger = cls._get_logger(tool_key, "FirestoreService", channel=LogUtils.DATABASE_CHANNEL)
        url = f"{cls._base_url()}:runQuery"
        payload = {"structuredQuery": cls._build_query(collection, order_by, limit, descending, equals)}

        try:
            resp = requests.post(url, headers=cls._auth_headers(), json=payload, timeout=20)
            if resp.status_code == 401:
                if FirebaseTokenProvider.refresh():
                    resp = requests.post(
                        url, headers=cls._auth_headers(), json=payload, timeout=20
                    )

            if resp.status_code != 200:
                logger.warning(
                    f"Falha na consulta da coleção {collection}",
                    code="FS_QUERY_FAIL",
                    status=resp.status_code,
                )
                return []

            rows = cls._documents_from_query(resp.json())
            logger.info(
                f"Consulta da coleção {collection} retornou {len(rows)} documento(s)",
                code="FS_QUERY_OK",
            )
            return rows
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Erro ao consultar a coleção {collection}",
                code="FS_QUERY_NET_ERR",
                error=str(e),
            )
            return []

    @staticmethod
    def _build_query(
        collection: str,
        order_by: Optional[str],
        limit: Optional[int],
        descending: bool,
        equals: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Monta a ``structuredQuery`` do ``runQuery``."""
        query: Dict[str, Any] = {"from": [{"collectionId": collection}]}
        if order_by:
            query["orderBy"] = [
                {
                    "field": {"fieldPath": order_by},
                    "direction": "DESCENDING" if descending else "ASCENDING",
                }
            ]
        if limit:
            query["limit"] = max(1, int(limit))
        filters = [
            {
                "fieldFilter": {
                    "field": {"fieldPath": field},
                    "op": "EQUAL",
                    "value": {"stringValue": str(value)},
                }
            }
            for field, value in (equals or {}).items()
            if field
        ]
        if len(filters) == 1:
            query["where"] = filters[0]
        elif filters:
            query["where"] = {
                "compositeFilter": {"op": "AND", "filters": filters}
            }
        return query

    @classmethod
    def _documents_from_query(
        cls, payload: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extrai ``{"doc_id", **campos}`` da resposta do ``runQuery``."""
        rows: List[Dict[str, Any]] = []
        for item in payload:
            document = item.get("document") if isinstance(item, dict) else None
            if not document:
                continue
            data = cls.firestore_to_dict(document)
            data["doc_id"] = str(document.get("name", "")).rsplit("/", 1)[-1]
            rows.append(data)
        return rows

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
                new_token = FirebaseTokenProvider.refresh()
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
