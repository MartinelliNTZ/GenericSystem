# -*- coding: utf-8 -*-
"""
CloudProjectDatabase — Banco de OS oficial (Firebase-first) + backup JSON
=========================================================================
CLASSE DE BANCO central do sistema de OS. É a ÚNICA porta de entrada para os
registros de OS/SubOS: as ferramentas (plugins) **nunca** leem/escrevem o JSON
de dados — elas chamam esta classe, que:

- LÊ/grava os documentos no **Cloud Firestore** (coleção ``banco_dados``) — a
  FONTE OFICIAL. A leitura é SEMPRE do Firestore: se a base estiver vazia (ou
  offline), a ferramenta simplesmente não exibe dados — é **proibido** cair para
  o JSON local;
- gera os **backups JSON** locais (um por OS + o consolidado) em
  ``<pasta-mãe>/.BancoDados`` como CONSEQUÊNCIA da escrita (Contrato 28) — ou
  seja, o JSON só é ESCRITO (nunca lido pela aplicação).

Uso:
    from core.firebase.CloudProjectDatabase import CloudProjectDatabase

    orders = CloudProjectDatabase.load_orders()                # lê a fonte oficial
    CloudProjectDatabase.save_order(record, mother)            # Firestore + backup JSON
    CloudProjectDatabase.rebuild_consolidated(orders, mother)  # snapshot + prune
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.database.ProjectDatabaseStore import ProjectDatabaseStore
from core.enum.ToolKey import ToolKey
from core.firebase.FirestoreService import FirestoreService
from utils.BaseUtil import BaseUtil
from utils.ProjectStructureUtil import ProjectStructureUtil

_TOOL_KEY = ToolKey.PROJECT_DATABASE.value


class CloudProjectDatabase(BaseUtil):
    """Fonte oficial (Firestore) dos registros de OS + geração dos backups JSON."""

    COLLECTION = "banco_dados"
    CONSOLIDATED_DOC_ID = "banco_dados"

    # ── Leitura ─────────────────────────────────────────────────────

    @classmethod
    def load_orders(
        cls, tool_key: str = _TOOL_KEY
    ) -> List[Dict[str, Any]]:
        """Lista os registros de OS da FONTE OFICIAL (Firestore).

        O documento consolidado é ignorado (é apenas um snapshot). A leitura é
        EXCLUSIVAMENTE do Firestore — se a base estiver vazia/offline, retorna
        ``[]`` (a aplicação **nunca** lê o JSON de backup — Contrato 28).
        """
        documents = FirestoreService.list_documents(
            cls.COLLECTION, tool_key=tool_key
        )
        return [
            data
            for doc_id, data in documents.items()
            if doc_id != cls.CONSOLIDATED_DOC_ID and isinstance(data, dict)
        ]

    @classmethod
    def get_order(
        cls, os_number: str, tool_key: str = _TOOL_KEY
    ) -> Optional[Dict[str, Any]]:
        """Busca o registro de UMA OS na fonte oficial (``None`` se não existir)."""
        return FirestoreService.get_document(
            cls.COLLECTION, cls._doc_id(os_number), tool_key=tool_key
        )

    # ── Escrita (Firestore + backup JSON) ───────────────────────────

    @classmethod
    def save_order(
        cls,
        record: Dict[str, Any],
        mother: str | Path = "",
        tool_key: str = _TOOL_KEY,
    ) -> bool:
        """Grava UMA OS na fonte oficial e gera o backup JSON individual.

        O timestamp ``updated_at`` é atualizado. O JSON local é gerado por esta
        classe (a ferramenta nunca toca no JSON — Contrato 28).
        """
        doc_id = cls._doc_id(record.get("os", ""))
        payload = dict(record)
        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        ok = FirestoreService.save_document(
            cls.COLLECTION, doc_id, payload, tool_key=tool_key
        )
        cls._write_backup(mother, payload, tool_key=tool_key)
        return ok

    @classmethod
    def save_orders(
        cls,
        records: List[Dict[str, Any]],
        mother: str | Path = "",
        tool_key: str = _TOOL_KEY,
    ) -> int:
        """Grava VÁRIAS OS (Firestore + backup JSON) e reconstrói o consolidado."""
        saved = 0
        for record in records:
            if cls.save_order(record, mother=mother, tool_key=tool_key):
                saved += 1
        cls.rebuild_consolidated(records, mother=mother, tool_key=tool_key)
        return saved

    @classmethod
    def rebuild_consolidated(
        cls,
        records: List[Dict[str, Any]],
        mother: str | Path = "",
        tool_key: str = _TOOL_KEY,
    ) -> Dict[str, Any]:
        """Regrava o documento consolidado (nuvem) + o backup JSON + poda órfãos."""
        data = {
            "db_schema": ProjectDatabaseStore.DB_SCHEMA,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "total_projects": len(records),
            "projects": records,
        }
        FirestoreService.save_document(
            cls.COLLECTION, cls.CONSOLIDATED_DOC_ID, data, tool_key=tool_key
        )
        if mother:
            ProjectDatabaseStore.save_consolidated(
                str(mother), data, tool_key=tool_key
            )
            ProjectDatabaseStore.prune_projects(
                str(mother),
                [str(record.get("os", "")) for record in records],
                tool_key=tool_key,
            )
        return data

    # ── Backups JSON (gerados exclusivamente por esta classe) ────────

    @classmethod
    def _write_backup(
        cls, mother: str | Path, record: Dict[str, Any], tool_key: str
    ) -> None:
        """Gera o backup JSON individual de uma OS (se houver pasta-mãe)."""
        if not mother:
            return
        ProjectDatabaseStore.save_project(str(mother), record, tool_key=tool_key)

    # ── Internos ────────────────────────────────────────────────────

    @classmethod
    def _doc_id(cls, os_number: str | Any) -> str:
        """``doc_id``/nome do backup de uma OS (número normalizado + sanitizado)."""
        return cls._safe_name(ProjectStructureUtil.normalize_os(str(os_number)))

    @staticmethod
    def _safe_name(name: str) -> str:
        """Sanitiza ``name`` para uso como ``doc_id``/nome de arquivo no Windows."""
        return re.sub(r'[<>:"/\\|?*]', "_", str(name)).strip() or "os"

