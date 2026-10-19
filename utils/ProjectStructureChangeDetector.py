# -*- coding: utf-8 -*-
"""
ProjectStructureChangeDetector — Classificação inteligente das alterações
========================================================================
Componente ISOLADO de detecção (sem Qt, sem banco e sem UI). Recebe o snapshot
anterior e o atual de cada pasta de OS e classifica as mudanças em:

- pastas criadas/removidas;
- pastas renomeadas/movidas — validadas por ÁRVORE (estrutura relativa +
  tamanho dos arquivos): só é declarada quando existe UM ÚNICO par de pastas
  com a mesma árvore; se houver ambiguidade, os arquivos são comparados
  individualmente (movimentação);
- arquivos criados/removidos/modificados (data de modificação);
- arquivos RENOMEADOS (mesma pasta, mesmo tamanho e nome diferente);
- arquivos MOVIDOS (mesmo nome e mesmo tamanho, pasta diferente).

Heurística dos arquivos, nesta ordem: renomeação na mesma pasta → movimentação
(mesmo nome) → tamanho único entre o restante. Só pares NÃO AMBÍGUOS
(1 antigo × 1 novo no mesmo grupo) são classificados.

Uso:
    from utils.ProjectStructureChangeDetector import ProjectStructureChangeDetector

    changes = ProjectStructureChangeDetector.detect(previous, current)
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from utils.BaseUtil import BaseUtil

_CHANGE_KEYS = (
    "added_folders",
    "removed_folders",
    "folder_renames",
    "folder_moves",
    "added_files",
    "removed_files",
    "renamed_files",
    "moved_files",
    "modified_files",
)

_Signature = Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[int, ...]]


class ProjectStructureChangeDetector(BaseUtil):
    """Compara snapshots e classifica renomeações/movimentações."""

    @classmethod
    def detect(
        cls,
        previous: Dict[str, Dict[str, Any]],
        current: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Retorna apenas as OS com alterações, já classificadas."""
        changes: List[Dict[str, Any]] = []
        for scope in sorted(set(previous) | set(current), key=str.lower):
            before = previous.get(scope) or {}
            after = current.get(scope) or {}
            change = cls._detect_scope(before, after)
            change["scope"] = str(
                after.get("scope") or before.get("scope") or scope
            )
            change["os"] = str(after.get("os") or before.get("os") or "")
            if any(change[key] for key in _CHANGE_KEYS):
                changes.append(change)
        return changes

    @classmethod
    def _detect_scope(
        cls, before: Dict[str, Any], after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classifica as alterações de uma OS."""
        before_folders = set(before.get("folders") or [])
        after_folders = set(after.get("folders") or [])
        before_files = set(before.get("files") or [])
        after_files = set(after.get("files") or [])

        pairs = cls._match_folders(
            before,
            after,
            before_folders - after_folders,
            after_folders - before_folders,
        )
        old_roots = {old for old, _, _ in pairs}
        new_roots = {new for _, new, _ in pairs}
        common_files = before_files & after_files
        remaining_old = (
            before_files
            - common_files
            - cls._covered_files(before_files, old_roots)
        )
        remaining_new = (
            after_files
            - common_files
            - cls._covered_files(after_files, new_roots)
        )

        renamed, moved, remaining_old, remaining_new = cls._match_files(
            before, after, remaining_old, remaining_new
        )
        folder_renames, folder_moves = cls._folder_lists(pairs)
        modified = cls._modified_files(before, after, common_files)
        modified.extend(cls._modified_inside_pairs(before, after, pairs))

        return {
            "added_folders": cls._leftover_folders(
                after_folders - before_folders, new_roots
            ),
            "removed_folders": cls._leftover_folders(
                before_folders - after_folders, old_roots
            ),
            "folder_renames": folder_renames,
            "folder_moves": folder_moves,
            "added_files": sorted(remaining_new, key=str.lower),
            "removed_files": sorted(remaining_old, key=str.lower),
            "renamed_files": renamed,
            "moved_files": moved,
            "modified_files": sorted(
                modified, key=lambda item: item["path"].lower()
            ),
        }

    # ── Pastas: validação por árvore ────────────────────────────────

    @classmethod
    def _match_folders(
        cls,
        before: Dict[str, Any],
        after: Dict[str, Any],
        removed: Set[str],
        added: Set[str],
    ) -> List[Tuple[str, str, _Signature]]:
        """Pareia pastas removidas/adicionadas com a MESMA árvore.

        Só aceita pares inequívocos (1 removida × 1 adicionada por assinatura).
        Pares aninhados são descartados para não reportar a mesma renomeação
        várias vezes (pasta raiz + subpastas).
        """
        old_groups = cls._group_signatures(
            {path: cls._tree_signature(before, path) for path in removed}
        )
        new_groups = cls._group_signatures(
            {path: cls._tree_signature(after, path) for path in added}
        )
        pairs: List[Tuple[str, str, _Signature]] = []
        for signature, olds in old_groups.items():
            news = new_groups.get(signature, [])
            if len(olds) == 1 and len(news) == 1:
                pairs.append((olds[0], news[0], signature))
        return cls._drop_nested_pairs(pairs)

    @classmethod
    def _tree_signature(
        cls, entry: Dict[str, Any], folder: str
    ) -> Optional[_Signature]:
        """Assinatura da árvore de ``folder``: subpastas + arquivos + tamanhos.

        Retorna ``None`` quando a pasta não tem arquivos ou quando algum
        tamanho é desconhecido — nesses casos não há como validar a
        renomeação por árvore.
        """
        prefix = folder + "/"
        rel_dirs = tuple(
            sorted(
                path[len(prefix):]
                for path in entry.get("folders", [])
                if path.startswith(prefix)
            )
        )
        rel_files = tuple(
            sorted(
                path[len(prefix):]
                for path in entry.get("files", [])
                if path.startswith(prefix)
            )
        )
        if not rel_files:
            return None
        sizes_map = entry.get("sizes") or {}
        sizes: List[int] = []
        for relative in rel_files:
            size = sizes_map.get(prefix + relative)
            if not isinstance(size, int) or size < 0:
                return None
            sizes.append(size)
        return (rel_dirs, rel_files, tuple(sizes))

    @staticmethod
    def _group_signatures(
        signatures: Dict[str, Optional[_Signature]]
    ) -> Dict[_Signature, List[str]]:
        """Agrupa pastas pela assinatura (ignora assinaturas inválidas)."""
        groups: Dict[_Signature, List[str]] = defaultdict(list)
        for path, signature in signatures.items():
            if signature is not None:
                groups[signature].append(path)
        return groups

    @classmethod
    def _drop_nested_pairs(
        cls, pairs: List[Tuple[str, str, _Signature]]
    ) -> List[Tuple[str, str, _Signature]]:
        """Remove pares cuja pasta já está dentro de outro par aceito."""
        kept: List[Tuple[str, str, _Signature]] = []
        ordered = sorted(
            pairs, key=lambda item: (item[0].count("/"), item[0].lower())
        )
        for old, new, signature in ordered:
            nested = any(
                cls._is_inside(old, kept_old) or cls._is_inside(new, kept_new)
                for kept_old, kept_new, _ in kept
            )
            if not nested:
                kept.append((old, new, signature))
        return kept

    @classmethod
    def _folder_lists(
        cls, pairs: List[Tuple[str, str, _Signature]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Separa os pares em pastas RENOMEADAS e pastas MOVIDAS."""
        renamed: List[Dict[str, Any]] = []
        moved: List[Dict[str, Any]] = []
        for old, new, signature in pairs:
            item = {
                "old_path": old,
                "new_path": new,
                "file_count": len(signature[1]),
            }
            target = moved if cls._same_name(old, new) else renamed
            target.append(item)
        return (
            sorted(renamed, key=lambda item: item["old_path"].lower()),
            sorted(moved, key=lambda item: item["old_path"].lower()),
        )

    @staticmethod
    def _same_name(old: str, new: str) -> bool:
        """Indica se as duas pastas têm o mesmo nome (mudou só o pai)."""
        return PurePosixPath(old).name.lower() == PurePosixPath(new).name.lower()

    @classmethod
    def _covered_files(cls, files: Set[str], roots: Set[str]) -> Set[str]:
        """Arquivos que estão dentro de alguma das pastas pareadas."""
        return {
            path
            for path in files
            if any(cls._is_inside(path, root) for root in roots)
        }

    @classmethod
    def _leftover_folders(
        cls, folders: Set[str], covered_roots: Set[str]
    ) -> List[str]:
        """Pastas não cobertas por um par de renomeação/movimentação."""
        return sorted(
            (
                folder
                for folder in folders
                if not any(
                    cls._is_inside(folder, root) for root in covered_roots
                )
            ),
            key=str.lower,
        )

    @staticmethod
    def _is_inside(path: str, root: str) -> bool:
        """Indica se ``path`` é ``root`` ou está dentro de ``root``."""
        return path == root or path.startswith(root + "/")


    # ── Arquivos: renomeação e movimentação ─────────────────────────

    @classmethod
    def _match_files(
        cls,
        before: Dict[str, Any],
        after: Dict[str, Any],
        old_files: Set[str],
        new_files: Set[str],
    ) -> Tuple[
        List[Dict[str, Any]],
        List[Dict[str, Any]],
        Set[str],
        Set[str],
    ]:
        """Classifica os arquivos restantes em renomeados/movidos."""
        old_left = set(old_files)
        new_left = set(new_files)
        renamed: List[Dict[str, Any]] = []
        moved: List[Dict[str, Any]] = []

        same_folder = cls._pair_by(
            old_left,
            new_left,
            before,
            after,
            lambda info: (info["parent"], info["size"]),
        )
        renamed.extend(cls._pair_item(old, new, before, after) for old, new in same_folder)

        same_name = cls._pair_by(
            old_left,
            new_left,
            before,
            after,
            lambda info: (info["name"], info["size"]),
        )
        moved.extend(cls._pair_item(old, new, before, after) for old, new in same_name)

        same_size = cls._pair_by(
            old_left,
            new_left,
            before,
            after,
            lambda info: info["size"],
            skip_zero=True,
        )
        renamed.extend(cls._pair_item(old, new, before, after) for old, new in same_size)

        return (
            sorted(renamed, key=lambda item: item["old_path"].lower()),
            sorted(moved, key=lambda item: item["old_path"].lower()),
            old_left,
            new_left,
        )

    @classmethod
    def _pair_by(
        cls,
        old_files: Set[str],
        new_files: Set[str],
        before: Dict[str, Any],
        after: Dict[str, Any],
        key_fn: Callable[[Dict[str, Any]], Any],
        skip_zero: bool = False,
    ) -> List[Tuple[str, str]]:
        """Pareia arquivos 1×1 pelos grupos de ``key_fn`` (nunca ambíguos)."""
        old_groups = cls._group_files(before, old_files, key_fn, skip_zero)
        new_groups = cls._group_files(after, new_files, key_fn, skip_zero)
        pairs: List[Tuple[str, str]] = []
        for key in old_groups.keys() & new_groups.keys():
            olds = old_groups[key]
            news = new_groups[key]
            if len(olds) != 1 or len(news) != 1:
                continue
            old, new = olds[0], news[0]
            if old == new:
                old_files.discard(old)
                new_files.discard(new)
                continue
            pairs.append((old, new))
        for old, new in pairs:
            old_files.discard(old)
            new_files.discard(new)
        return pairs

    @classmethod
    def _group_files(
        cls,
        entry: Dict[str, Any],
        paths: Set[str],
        key_fn: Callable[[Dict[str, Any]], Any],
        skip_zero: bool,
    ) -> Dict[Any, List[str]]:
        """Agrupa arquivos pela chave informada (ignora tamanho desconhecido)."""
        groups: Dict[Any, List[str]] = defaultdict(list)
        for path in paths:
            info = cls._file_info(entry, path)
            if info["size"] is None:
                continue
            if skip_zero and info["size"] == 0:
                continue
            groups[key_fn(info)].append(path)
        return groups

    @staticmethod
    def _file_info(entry: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Nome, pasta, tamanho e caminho de um arquivo do snapshot."""
        size = (entry.get("sizes") or {}).get(path)
        if not isinstance(size, int) or size < 0:
            size = None
        pure = PurePosixPath(path)
        return {
            "path": path,
            "name": pure.name,
            "parent": str(pure.parent),
            "size": size,
        }

    @staticmethod
    def _pair_item(
        old: str, new: str, before: Dict[str, Any], after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Item de renomeação/movimentação (caminho antigo, novo e tamanho)."""
        size = (before.get("sizes") or {}).get(old)
        if size is None:
            size = (after.get("sizes") or {}).get(new)
        return {"old_path": old, "new_path": new, "size": size}

    # ── Arquivos: modificação ───────────────────────────────────────

    @staticmethod
    def _modified_files(
        before: Dict[str, Any],
        after: Dict[str, Any],
        common_files: Set[str],
    ) -> List[Dict[str, Any]]:
        """Arquivos no mesmo caminho cuja data de modificação mudou."""
        before_dates = before.get("modified") or {}
        after_dates = after.get("modified") or {}
        if not before_dates or not after_dates:
            return []
        result: List[Dict[str, Any]] = []
        for path in common_files:
            old_date = before_dates.get(path)
            new_date = after_dates.get(path)
            if old_date and new_date and old_date != new_date:
                result.append({"path": path, "modified_at": new_date})
        return result

    @staticmethod
    def _modified_inside_pairs(
        before: Dict[str, Any],
        after: Dict[str, Any],
        pairs: List[Tuple[str, str, _Signature]],
    ) -> List[Dict[str, Any]]:
        """Arquivos modificados dentro de uma pasta renomeada/movida."""
        before_dates = before.get("modified") or {}
        after_dates = after.get("modified") or {}
        result: List[Dict[str, Any]] = []
        for old_root, new_root, signature in pairs:
            for relative in signature[1]:
                old_date = before_dates.get(f"{old_root}/{relative}")
                new_date = after_dates.get(f"{new_root}/{relative}")
                if old_date and new_date and old_date != new_date:
                    result.append(
                        {
                            "path": f"{new_root}/{relative}",
                            "modified_at": new_date,
                        }
                    )
        return result

