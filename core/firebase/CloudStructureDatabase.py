# -*- coding: utf-8 -*-
"""
CloudStructureDatabase — Banco dos snapshots/changelog da estrutura (Firestore)
===============================================================================
CLASSE DE BANCO dos snapshots da estrutura de pastas das OS. Segue o mesmo
princípio do ``CloudProjectDatabase`` (Contrato 28): as ferramentas NUNCA
acessam o Firestore diretamente — sempre passam por esta classe.

Coleções:

- ``estrutura_projetos`` — um documento por pasta de OS com o último snapshot
  (``scope``, ``os``, ``folders``, ``files`` e ``updated_at``);
- ``estrutura_changelog`` — um documento por evento de alteração detectada
  (``scope``, ``os``, listas de mudanças e ``detected_at``).

Uso:
    from core.firebase.CloudStructureDatabase import CloudStructureDatabase

    previous = CloudStructureDatabase.load_snapshots()
    CloudStructureDatabase.save_snapshots(snapshots, previous.keys())
    CloudStructureDatabase.save_changes(changes)
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.firebase.FirestoreService import FirestoreService
from utils.BaseUtil import BaseUtil


class CloudStructureDatabase(BaseUtil):
    """Persiste snapshots e histórico de alterações da estrutura no Firestore."""

    SNAPSHOT_COLLECTION = "estrutura_projetos"
    CHANGELOG_COLLECTION = "estrutura_changelog"

    # ── Leitura ─────────────────────────────────────────────────────

    @classmethod
    def load_snapshots(
        cls, tool_key: str = ToolKey.PROJECT_DATABASE.value
    ) -> Dict[str, Dict[str, Any]]:
        """Retorna ``{doc_id: snapshot}`` da coleção de snapshots."""
        return FirestoreService.list_documents(
            cls.SNAPSHOT_COLLECTION, tool_key=tool_key
        )

    # ── Escrita ─────────────────────────────────────────────────────

    @classmethod
    def save_snapshots(
        cls,
        snapshots: Dict[str, Dict[str, Any]],
        existing_doc_ids: Iterable[str] = (),
        previous: Optional[Dict[str, Dict[str, Any]]] = None,
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> int:
        """Grava os snapshots atuais e remove os de OS que não existem mais.

        Args:
            snapshots: ``{scope: registro}`` (resultado do scan).
            existing_doc_ids: ``doc_ids`` lidos por ``load_snapshots`` — usados
                para podar os snapshots de pastas removidas do disco.
            previous: snapshots já salvos (``{scope: registro}``). Quando
                informado, só grava as OS cuja estrutura mudou.

        Returns:
            Quantidade de snapshots gravados com sucesso.
        """
        logger = cls._logger(tool_key)
        saved = 0
        keep: set[str] = set()
        updated_at = datetime.now().isoformat(timespec="seconds")
        for scope, data in snapshots.items():
            doc_id = cls._doc_id(scope)
            keep.add(doc_id)
            if cls._unchanged(data, (previous or {}).get(scope)):
                continue
            payload = dict(data)
            payload["scope"] = str(data.get("scope") or scope)
            payload["updated_at"] = updated_at
            if FirestoreService.save_document(
                cls.SNAPSHOT_COLLECTION, doc_id, payload, tool_key=tool_key
            ):
                saved += 1
        cls._prune(set(existing_doc_ids) - keep, tool_key=tool_key, logger=logger)
        return saved

    @staticmethod
    def _unchanged(
        current: Dict[str, Any], previous: Optional[Dict[str, Any]]
    ) -> bool:
        """Indica se a estrutura salva é idêntica à atual (nada a gravar)."""
        if not previous:
            return False
        return (
            list(current.get("folders", [])) == list(previous.get("folders", []))
            and list(current.get("files", [])) == list(previous.get("files", []))
        )

    @classmethod
    def save_changes(
        cls,
        changes: List[Dict[str, Any]],
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> int:
        """Grava um documento por OS alterada na coleção de changelog."""
        saved = 0
        detected_at = datetime.now()
        stamp = detected_at.strftime("%Y%m%d%H%M%S")
        for index, change in enumerate(changes):
            payload = dict(change)
            payload["detected_at"] = detected_at.isoformat(timespec="seconds")
            doc_id = f"{cls._doc_id(change.get('scope', ''))}_{stamp}{index:03d}"
            if FirestoreService.save_document(
                cls.CHANGELOG_COLLECTION, doc_id, payload, tool_key=tool_key
            ):
                saved += 1
        return saved

    # ── Internos ────────────────────────────────────────────────────

    @classmethod
    def _prune(
        cls,
        doc_ids: set[str],
        tool_key: str,
        logger: LogUtils,
    ) -> None:
        """Remove snapshots de OS que não existem mais na pasta-mãe."""
        for doc_id in sorted(doc_ids):
            if FirestoreService.delete_document(
                cls.SNAPSHOT_COLLECTION, doc_id, tool_key=tool_key
            ):
                logger.info(
                    "Snapshot de OS removida",
                    code="CSDB_PRUNE_OK",
                    doc_id=doc_id,
                )

    @classmethod
    def _logger(cls, tool_key: str) -> LogUtils:
        """Logger do canal exclusivo do banco de dados."""
        return cls._get_logger(
            tool_key,
            "CloudStructureDatabase",
            channel=LogUtils.DATABASE_CHANNEL,
        )

    @staticmethod
    def _doc_id(scope: Any) -> str:
        """Gera um ``doc_id`` seguro (URL/Firestore) a partir do ``scope``.

        O nome da pasta da OS pode conter espaços, acentos e ``#`` — caracteres
        que quebrariam a URL do Firestore. O ``scope`` original continua salvo
        no documento; o hash garante que não haja colisão entre nomes
        sanitizados iguais.
        """
        text = str(scope)
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_") or "os"
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
        return f"{safe}_{digest}"
