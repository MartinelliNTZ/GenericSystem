# -*- coding: utf-8 -*-
"""
CloudDatabaseSync — Espelho offline do banco de dados (Firestore ↔ JSON)
=======================================================================
Mantém cópias offline em JSON de um banco oficial hospedado no Cloud
Firestore. Cada ``*.json`` do diretório local é tratado como o espelho de um
documento de uma coleção do Firestore:

- ``push`` — envia cada ``*.json`` local como um documento da coleção.
- ``pull`` — baixa os documentos da coleção e grava cada um como ``*.json``.

Os metadados da última sincronização ficam em ``<local_dir>/.cloud/meta.json``
(subpasta dedicada — nunca é confundida com um documento do banco). O log é
emitido no canal desacoplado ``LogUtils.DATABASE_CHANNEL``.

Uso:
    from core.firebase.CloudDatabaseSync import CloudDatabaseSync
    from core.enum.ToolKey import ToolKey

    CloudDatabaseSync.push(local_dir, "banco_dados", tool_key=ToolKey.PROJECT_DATABASE.value)
    CloudDatabaseSync.pull(local_dir, "banco_dados", tool_key=ToolKey.PROJECT_DATABASE.value)
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.firebase.FirebaseConfig import FirebaseConfig
from core.firebase.FirestoreService import FirestoreService
from utils.BaseUtil import BaseUtil


class CloudDatabaseSync(BaseUtil):
    """Sincroniza um diretório de JSONs (backup offline) com uma coleção Firestore."""

    CLOUD_DIRNAME = ".cloud"
    META_FILENAME = "meta.json"

    @classmethod
    def _logger(cls, tool_key: str) -> LogUtils:
        """Logger do canal desacoplado de banco de dados."""
        return cls._get_logger(
            tool_key, "CloudDatabaseSync", channel=LogUtils.DATABASE_CHANNEL
        )

    # ── Caminhos / metadados ─────────────────────────────────────────

    @classmethod
    def meta_path(cls, local_dir: str | Path) -> Path:
        """Caminho do arquivo de metadados da sincronização."""
        return Path(local_dir) / cls.CLOUD_DIRNAME / cls.META_FILENAME

    @classmethod
    def read_meta(cls, local_dir: str | Path) -> Dict[str, Any]:
        """Lê os metadados da última sincronização (``{}`` se não existir)."""
        path = cls.meta_path(local_dir)
        if not path.is_file():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    @classmethod
    def _write_meta(
        cls,
        local_dir: str | Path,
        data: Dict[str, Any],
        tool_key: str,
    ) -> None:
        logger = cls._logger(tool_key)
        path = cls.meta_path(local_dir)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error(
                "Falha ao gravar metadados de sincronização",
                code="CSYNC_META_ERR",
                error=str(e),
            )

    # ── Push (local → Firebase) ──────────────────────────────────────

    @classmethod
    def push(
        cls,
        local_dir: str | Path,
        collection: str,
        *,
        skip_names: Optional[Iterable[str]] = None,
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> Dict[str, Any]:
        """Envia cada ``*.json`` local como um documento do Firestore.

        Returns:
            Resumo ``{"pushed": int, "failed": int, "collection": str}``.
        """
        logger = cls._logger(tool_key)
        directory = Path(local_dir)
        if not directory.is_dir():
            logger.warning(
                f"Diretório local inexistente para push: {directory}",
                code="CSYNC_PUSH_NO_DIR",
            )
            return {"pushed": 0, "failed": 0, "collection": collection}

        skip = cls._skip_set(skip_names)
        pushed = 0
        failed = 0
        for path in sorted(directory.glob("*.json")):
            if path.name in skip:
                continue
            data = cls._read_json(path)
            if data is None:
                failed += 1
                logger.error(
                    f"JSON local inválido: {path.name}",
                    code="CSYNC_PUSH_BAD_JSON",
                    path=str(path),
                )
                continue
            if FirestoreService.save_document(collection, path.stem, data, tool_key=tool_key):
                pushed += 1
            else:
                failed += 1

        cls._update_meta(
            directory, collection, direction="push",
            pushed=pushed, pulled=0, tool_key=tool_key,
        )
        logger.info(
            f"Push concluído: {pushed} enviado(s), {failed} falha(s)",
            code="CSYNC_PUSH_DONE",
            collection=collection,
        )
        return {"pushed": pushed, "failed": failed, "collection": collection}

    # ── Pull (Firebase → local) ──────────────────────────────────────

    @classmethod
    def pull(
        cls,
        local_dir: str | Path,
        collection: str,
        *,
        overwrite: bool = True,
        tool_key: str = ToolKey.PROJECT_DATABASE.value,
    ) -> Dict[str, Any]:
        """Baixa os documentos do Firestore e grava cada um como ``*.json``.

        Returns:
            Resumo ``{"pulled": int, "skipped": int, "collection": str}``.
        """
        logger = cls._logger(tool_key)
        directory = Path(local_dir)
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(
                "Falha ao criar diretório local para pull",
                code="CSYNC_PULL_MKDIR_ERR",
                error=str(e),
            )
            return {"pulled": 0, "skipped": 0, "collection": collection}

        documents = FirestoreService.list_documents(collection, tool_key=tool_key)
        pulled = 0
        skipped = 0
        for doc_id, data in documents.items():
            target = directory / f"{cls._safe_name(doc_id)}.json"
            if target.exists() and not overwrite:
                skipped += 1
                continue
            if cls._write_json_atomic(target, data, tool_key=tool_key):
                pulled += 1
            else:
                skipped += 1

        cls._update_meta(
            directory, collection, direction="pull",
            pushed=0, pulled=pulled, tool_key=tool_key,
        )
        logger.info(
            f"Pull concluído: {pulled} baixado(s), {skipped} ignorado(s)",
            code="CSYNC_PULL_DONE",
            collection=collection,
        )
        return {"pulled": pulled, "skipped": skipped, "collection": collection}

    # ── Internos ─────────────────────────────────────────────────────

    @classmethod
    def _skip_set(cls, skip_names: Optional[Iterable[str]]) -> Set[str]:
        base: Set[str] = {cls.META_FILENAME}
        if skip_names:
            base.update(skip_names)
        return base

    @staticmethod
    def _safe_name(name: str) -> str:
        """Sanitiza ``name`` para uso como nome de arquivo no Windows."""
        return str(name).replace("/", "_").replace("\\", "_").strip() or "document"

    @staticmethod
    def _read_json(path: Path) -> Optional[Dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    @classmethod
    def _write_json_atomic(
        cls,
        path: Path,
        data: Dict[str, Any],
        tool_key: str,
    ) -> bool:
        logger = cls._logger(tool_key)
        tmp = path.with_name(path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
            return True
        except OSError as e:
            logger.error(
                f"Falha ao gravar JSON de backup: {path}",
                code="CSYNC_WRITE_ERR",
                error=str(e),
            )
            return False

    @classmethod
    def _update_meta(
        cls,
        local_dir: str | Path,
        collection: str,
        *,
        direction: str,
        pushed: int,
        pulled: int,
        tool_key: str,
    ) -> None:
        meta = cls.read_meta(local_dir)
        now = datetime.now().isoformat(timespec="seconds")
        meta.update({
            "collection": collection,
            "project_id": FirebaseConfig.get_project_id(),
            "last_direction": direction,
            "last_sync": now,
        })
        if direction == "push":
            meta["last_push"] = now
            meta["last_push_count"] = pushed
        else:
            meta["last_pull"] = now
            meta["last_pull_count"] = pulled
        cls._write_meta(local_dir, meta, tool_key)
