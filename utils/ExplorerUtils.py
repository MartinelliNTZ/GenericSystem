# -*- coding: utf-8 -*-
"""
ExplorerUtils — Única classe responsável por buscar arquivos/pastas no SO
==========================================================================
Centraliza todas as chamadas a QFileDialog. Nenhum outro módulo deve
chamar QFileDialog diretamente.

Uso:
    from utils.ExplorerUtils import ExplorerUtils

    path = ExplorerUtils.open_file("Selecionar imagem", filter="GeoTIFF (*.tif)")
    paths = ExplorerUtils.open_files("Selecionar arquivos", filter="CSV (*.csv)")
    save = ExplorerUtils.save_file("Salvar como", filter="JSON (*.json)")
    folder = ExplorerUtils.select_directory("Selecionar pasta")
    folders = ExplorerUtils.select_directories("Selecionar pastas")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import QFileDialog, QWidget

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class ExplorerUtils(BaseUtil):
    """
    Métodos estáticos para todas as operações de seleção de arquivo/pasta.
    """

    # ── Modos únicos ────────────────────────────────────────────────

    @staticmethod
    def open_file(
        title: str = "Selecionar arquivo",
        initial_dir: str = "",
        file_filter: str = "Todos (*.*)",
        parent: Optional[QWidget] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Abre diálogo para selecionar UM arquivo para leitura.

        Args:
            title: Título do diálogo.
            initial_dir: Diretório inicial.
            file_filter: Filtro de arquivos.
            parent: Widget pai.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho do arquivo selecionado, ou string vazia se cancelado.
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        path, _ = QFileDialog.getOpenFileName(
            parent, title, initial_dir, file_filter,
        )
        result = path or ""
        if result:
            logger.info("Arquivo selecionado", code="EXPL_OPEN_FILE", path=result)
        else:
            logger.debug("Selecao de arquivo cancelada", code="EXPL_OPEN_FILE_CANCEL")
        return result

    @staticmethod
    def save_file(
        title: str = "Salvar arquivo",
        initial_dir: str = "",
        file_filter: str = "Todos (*.*)",
        parent: Optional[QWidget] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Abre diálogo para selecionar UM arquivo para salvar.

        Args:
            title: Título do diálogo.
            initial_dir: Diretório inicial.
            file_filter: Filtro de arquivos.
            parent: Widget pai.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho do arquivo, ou string vazia se cancelado.
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        path, _ = QFileDialog.getSaveFileName(
            parent, title, initial_dir, file_filter,
        )
        result = path or ""
        if result:
            logger.info("Arquivo salvo selecionado", code="EXPL_SAVE_FILE", path=result)
        else:
            logger.debug("Selecao de salvamento cancelada", code="EXPL_SAVE_FILE_CANCEL")
        return result

    @staticmethod
    def select_directory(
        title: str = "Selecionar pasta",
        initial_dir: str = "",
        parent: Optional[QWidget] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Abre diálogo para selecionar UMA pasta.

        Args:
            title: Título do diálogo.
            initial_dir: Diretório inicial.
            parent: Widget pai.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho da pasta, ou string vazia se cancelado.
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        path = QFileDialog.getExistingDirectory(
            parent, title, initial_dir,
        )
        result = path or ""
        if result:
            logger.info("Pasta selecionada", code="EXPL_SELECT_DIR", path=result)
        else:
            logger.debug("Selecao de pasta cancelada", code="EXPL_SELECT_DIR_CANCEL")
        return result

    # ── Modos múltiplos ─────────────────────────────────────────────

    @staticmethod
    def open_files(
        title: str = "Selecionar arquivos",
        initial_dir: str = "",
        file_filter: str = "Todos (*.*)",
        parent: Optional[QWidget] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> List[str]:
        """
        Abre diálogo para selecionar MÚLTIPLOS arquivos para leitura.

        Args:
            title: Título do diálogo.
            initial_dir: Diretório inicial.
            file_filter: Filtro de arquivos.
            parent: Widget pai.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Lista de caminhos, ou lista vazia se cancelado.
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        paths, _ = QFileDialog.getOpenFileNames(
            parent, title, initial_dir, file_filter,
        )
        result = list(paths)
        if result:
            logger.info("Multiplos arquivos selecionados", code="EXPL_OPEN_FILES", count=len(result))
        else:
            logger.debug("Selecao multipla cancelada", code="EXPL_OPEN_FILES_CANCEL")
        return result

    @staticmethod
    def select_directories(
        title: str = "Selecionar pastas",
        initial_dir: str = "",
        parent: Optional[QWidget] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> List[str]:
        """
        Abre diálogo para selecionar MÚLTIPLAS pastas.
        Nota: QFileDialog nativo não suporta multi-pasta diretamente.
        Esta implementação retorna uma pasta por vez (usuário escolhe uma).

        Args:
            title: Título do diálogo.
            initial_dir: Diretório inicial.
            parent: Widget pai.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Lista com um caminho de pasta, ou vazia.
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        path = QFileDialog.getExistingDirectory(
            parent, title, initial_dir,
        )
        result = [path] if path else []
        if result:
            logger.info("Pasta selecionada (multi)", code="EXPL_SELECT_DIRS", count=1)
        else:
            logger.debug("Selecao de pastas cancelada", code="EXPL_SELECT_DIRS_CANCEL")
        return result

    # ── Config Directory ────────────────────────────────────────────

    @staticmethod
    def get_plugin_config_dir(
        plugin_name: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Path:
        """
        Retorna e garante a existência do diretório de config de um plugin.

        Estrutura: ``config/data/<plugin_name>/``

        Args:
            plugin_name: Nome do plugin (ex: "hotkey", "renamer").
            tool_key: Chave da ferramenta para logging.

        Returns:
            Path do diretório (já criado).
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        config_dir = Path("config/data") / plugin_name
        config_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Diretorio de config garantido", code="EXPL_CONFIG_DIR", plugin=plugin_name, path=str(config_dir))
        return config_dir

    # ── Busca de Arquivos ───────────────────────────────────────────

    @staticmethod
    def find_files(
        root_path: str,
        extensions: frozenset[str],
        recursive: bool = False,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> List[str]:
        """
        Busca arquivos por extensao em um diretorio (generico).

        Args:
            root_path: Caminho do diretorio raiz.
            extensions: Conjunto de extensoes (ex: frozenset({".mrk", ".MRK"})).
            recursive: Se True, vasculha subpastas recursivamente.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Lista de caminhos absolutos dos arquivos encontrados, ordenados.
            Vazia se diretorio invalido ou nenhum arquivo encontrado.
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        if not root_path:
            logger.debug("root_path vazio em find_files", code="EXPL_FIND_EMPTY_ROOT")
            return []
        root = Path(root_path)
        if not root.is_dir():
            logger.warning("Diretorio invalido em find_files", code="EXPL_FIND_INVALID_DIR", path=root_path)
            return []

        results: List[str] = []
        pattern = "**/*" if recursive else "*"
        for f in root.glob(pattern):
            if f.is_file() and f.suffix.lower() in extensions:
                results.append(str(f.resolve()))

        results.sort()
        logger.info("Busca de arquivos concluida", code="EXPL_FIND_DONE", root=root_path, count=len(results), recursive=recursive)
        return results

    # ── System Temp ────────────────────────────────────────────────

    @staticmethod
    def get_system_temp_dir(
        subfolder: str = "",
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna (e garante) um diretório temporário no sistema.

        Se subfolder for fornecido, cria ``C:\\Users\\<user>\\AppData\\Local\\Temp\\<subfolder>\\``.
        Se vazio, retorna o temp root.

        Args:
            subfolder: Subpasta opcional (ex: "aetheris/football").
            tool_key: Chave da ferramenta para logging.

        Returns:
            Caminho absoluto do diretório (já criado).
        """
        import tempfile
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        base = tempfile.gettempdir()
        if not subfolder:
            result = base
        else:
            result = os.path.join(base, subfolder)
        os.makedirs(result, exist_ok=True)
        logger.info("Diretorio temp do sistema garantido", code="EXPL_TEMP_DIR", path=result)
        return result

    # ── Default Paths ──────────────────────────────────────────────

    @staticmethod
    def get_default_path(
        category: str,
        root_folder: str = "",
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna caminho padrão para uma categoria baseado na root_folder.
        Use DefaultPathCategory enum para evitar strings soltas.

        Categorias: "vector", "raster", "ico", "image", "documents"

        Se root_folder vazio, retorna "" (botão de sugestão não aparece).

        Args:
            category: Categoria do caminho.
            root_folder: Pasta raiz.
            tool_key: Chave da ferramenta para logging.
        """
        from core.enum.DefaultPathCategory import DefaultPathCategory
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        paths = {
            DefaultPathCategory.VECTOR:    "vector",
            DefaultPathCategory.RASTER:    "raster",
            DefaultPathCategory.ICO:       "ico",
            DefaultPathCategory.IMAGE:     "image",
            DefaultPathCategory.DOCUMENTS: "documents",
        }
        sub = paths.get(category, "")
        if not sub or not root_folder:
            logger.debug("Caminho padrao vazio", code="EXPL_DEFAULT_PATH_EMPTY", category=category, has_root=bool(root_folder))
            return ""
        result = os.path.join(root_folder, sub)
        logger.debug("Caminho padrao resolvido", code="EXPL_DEFAULT_PATH", category=category, path=result)
        return result

    @staticmethod
    def ensure_directory(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Garante que um diretório existe. Se não existir, cria.
        Se path for vazio, retorna vazio.

        Args:
            path: Caminho do diretório.
            tool_key: Chave da ferramenta para logging.

        Returns:
            O mesmo path, ou vazio se vazio.
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        if not path:
            logger.debug("Path vazio em ensure_directory", code="EXPL_ENSURE_EMPTY")
            return ""
        os.makedirs(path, exist_ok=True)
        logger.info("Diretorio garantido", code="EXPL_ENSURE_DIR", path=path)
        return path

    # ── Utilitário ──────────────────────────────────────────────────

    @staticmethod
    def format_explorer_link(
        path: str,
        label: str = "Pasta de Saída",
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna HTML de link clicável que abre o caminho no Windows Explorer.

        O link usa 'file:///' com URL-encode para suportar #, espaços e
        caracteres especiais no path.
        A cor do link é definida pelo tema ativo (ACCENT).

        Args:
            path: Caminho do diretório ou arquivo.
            label: Texto exibido no link (padrão: "Pasta de Saída").
            tool_key: Chave da ferramenta para logging.

        Returns:
            HTML string com link formatado, ou string vazia se path vazio.
        """
        from urllib.parse import quote
        # Import lazy para evitar circular imports no startup
        from resources.styles.ThemeManager import theme_manager

        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        if not path:
            logger.debug("Path vazio em format_explorer_link", code="EXPL_LINK_EMPTY")
            return ""

        safe_path = path.replace(chr(92), '/')
        encoded = quote(safe_path, safe='/:@!$&()*+,;=-._~')
        link = (
            f"<a href='file:///{encoded}' "
            f"style='color: {theme_manager.theme.ACCENT}; text-decoration: underline;'>{label}</a>"
        )
        logger.debug("Link do Explorer gerado", code="EXPL_LINK_OK", path=path)
        return link

    @staticmethod
    def resolve_initial_dir(
        current_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna o diretório base de um caminho, se ele existir.
        Útil para definir o initial_dir dos diálogos.

        Args:
            current_path: Caminho atual (arquivo ou pasta).
            tool_key: Chave da ferramenta para logging.

        Returns:
            - Se for um diretório existente → o próprio diretório.
            - Se for um arquivo existente → o diretório pai.
            - Se não existir ou vazio → string vazia (abre em recentes).
        """
        logger = BaseUtil._get_logger(tool_key, "ExplorerUtils")
        if not current_path:
            logger.debug("current_path vazio", code="EXPL_RESOLVE_EMPTY")
            return ""
        if os.path.isdir(current_path):
            logger.debug("Diretorio inicial resolveu para si mesmo", code="EXPL_RESOLVE_DIR", path=current_path)
            return current_path
        parent = os.path.dirname(current_path)
        if parent and os.path.exists(parent):
            logger.debug("Diretorio inicial resolveu para pai", code="EXPL_RESOLVE_PARENT", path=parent)
            return parent
        logger.debug("Diretorio inicial nao encontrado", code="EXPL_RESOLVE_NOT_FOUND", path=current_path)
        return ""