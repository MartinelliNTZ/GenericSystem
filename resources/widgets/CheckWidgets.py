# -*- coding: utf-8 -*-
"""
CheckWidgets — Verificador de stylesheets dos widgets
=======================================================
Importa todos os widgets de resources/widgets/ (e subpastas),
instancia cada um dentro de um QApplication e chama .styleSheet()
para capturar o CSS real resolvido.

Gera um arquivo .txt com o resultado.

Uso:
    python resources/widgets/CheckWidgets.py

    # Ou via import:
    from resources.widgets.CheckWidgets import CheckWidgets
    checker = CheckWidgets()
    checker.run()
"""

from __future__ import annotations

import importlib
import inspect
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

# ── PySide6 imports (precisa de QApplication antes de qualquer widget) ──
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QStyle


class CheckWidgets:
    """
    Escaneia, importa e instancia widgets para capturar .styleSheet() real.

    Attributes:
        output_path: Caminho do arquivo .txt de saída.
        widgets_dir: Diretório raiz dos widgets (resources/widgets).
    """

    # Classes que sabemos que não são widgets ou dão problema
    SKIP_CLASSES = {
        "_BadgeState",  # Enum
        "ToastNotification",  # Classe estática
    }

    # Classes abstratas do Qt que não podem ser instanciadas
    QT_ABSTRACT_CLASSES = {
        "QAbstractItemView",
        "QHeaderView",
    }

    # Widgets que precisam de argumentos especiais no construtor
    SPECIAL_ARGS: Dict[str, dict] = {
        "HorizontalTab": {"closable": True},
        "VerticalTab": {"title": "Tab"},
        "HotkeyCaptureLine": {"default_key": "f"},
        "Badge": {"text": "BADGE"},
        "PluginPage": {"title": "Plugin"},
        "CollapsibleParams": {"title": "Params"},
        "GroupPainel": {"title": "Group"},
        "ItemTable": {"columns": []},
        "GridLabel": {"config": {}, "columns": 1},
        "SimpleDangerButton": {"text": "Danger"},
        "SimpleGhostButton": {"text": "Ghost"},
        "SimpleLabel": {"text": "Label"},
        "SimplePrimaryButton": {"text": "Primary"},
        "SimpleRemoveButton": {"text": "Remove"},
        "SimpleSecondaryButton": {"text": "Secondary"},
        "_RecentProjectItem": {"name": "Projeto", "path": "/tmp", "last_modified": "", "active": True},
        "_ToastWidget": {"text": "Toast"},
        # ── Correções dos widgets que estavam dando erro ──
        "ToolbarButton": {"tool": None},  # Será tratado com mock
        "ListFileDialog": {"extensions": []},
        "GridComplexSelector": {"specs": []},
        "SimpleComboBox": {"items": []},
        "FileContextMenu": {"actions": [], "callbacks": {}},
        "FootballMatchWidget": {"fixture": None},  # Será tratado com mock
        "GridCheckBox": {"config": {}},
        "GridDoubleSpinBox": {"config": {}},
        "GridFieldMapping": {"config": {}},
        "GridLineEdit": {"config": {}},
        "GridPercentView": {"config": {}},
        "GridPreferenceItem": {"config": {}, "section": "test"},
        "PreferenceRow": {"key": "test", "config": {}, "current_value": ""},
        "GridRadio": {"config": {}},
        "GridSelector": {"specs": []},
        "GridSlider": {"config": {}},
        "ToolGroup": {"tool_type": None, "tools": []},  # Será tratado com mock
    }

    def __init__(
        self,
        output_path: str = "widgets_stylesheets.txt",
        widgets_dir: Optional[str] = None,
    ) -> None:
        self._script_dir = Path(__file__).parent.resolve()  # resources/widgets
        self._project_root = self._script_dir.parent.parent.resolve()  # raiz do projeto

        self.output_path = output_path
        self.widgets_dir = Path(widgets_dir or self._script_dir)
        self._app: Optional[QApplication] = None
        self._results: List[Dict[str, Any]] = []

        # Garante que a raiz do projeto está no sys.path
        project_root_str = str(self._project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

    # ── API Pública ─────────────────────────────────────────────

    def run(self) -> str:
        """
        Executa a verificação e gera o arquivo .txt.

        Returns:
            Caminho absoluto do arquivo gerado.
        """
        self._ensure_app()
        self._results = self._scan_all()
        content = self._format_report()
        abs_path = os.path.abspath(self.output_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Relatório gerado: {abs_path}")
        return abs_path

    # ── QApplication ────────────────────────────────────────────

    def _ensure_app(self) -> QApplication:
        """Garante que existe um QApplication (cria um se necessário)."""
        if self._app is None:
            self._app = QApplication.instance()
            if self._app is None:
                self._app = QApplication([])
        return self._app

    # ── Escaneamento ────────────────────────────────────────────

    def _scan_all(self) -> List[Dict[str, Any]]:
        """
        Escaneia, importa e instancia todos os widgets.

        Returns:
            Lista de dicts com resultados de cada widget.
        """
        results: List[Dict[str, Any]] = []
        py_files = sorted(self.widgets_dir.rglob("*.py"))

        for py_file in py_files:
            if py_file.name == "__init__.py":
                continue
            if "__pycache__" in py_file.parts:
                continue

            rel_path = str(py_file.relative_to(self.widgets_dir))
            file_results = self._analyze_file(py_file, rel_path)
            results.extend(file_results)

        return results

    def _analyze_file(self, file_path: Path, rel_path: str) -> List[Dict[str, Any]]:
        """Analisa um arquivo .py: importa, acha classes widget, instancia."""
        results: List[Dict[str, Any]] = []

        # Converte path relativo pra módulo Python
        module_path = self._path_to_module(file_path)
        if not module_path:
            return results

        try:
            mod = importlib.import_module(module_path)
        except Exception as e:
            results.append({
                "file": rel_path,
                "class_name": f"<ERRO AO IMPORTAR>",
                "error": f"{e.__class__.__name__}: {e}",
                "stylesheet": "",
                "has_stylesheet": False,
            })
            return results

        # Acha classes widget no módulo
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if name.startswith("_"):
                continue
            if name in self.SKIP_CLASSES:
                continue

            # Verifica se herda de QWidget
            try:
                if not issubclass(obj, QWidget):
                    continue
            except TypeError:
                continue

            # Pula classes abstrutas ou base
            if obj is QWidget:
                continue

            # Pula classes abstratas do Qt
            if name in self.QT_ABSTRACT_CLASSES:
                continue

            result = self._try_instantiate(obj, rel_path)
            results.append(result)

        return results

    def _path_to_module(self, file_path: Path) -> Optional[str]:
        """Converte path do arquivo para nome de módulo Python importável."""
        try:
            # Path relativo à raiz do projeto
            rel = file_path.relative_to(self._project_root)
        except ValueError:
            return None

        # Remove extensão .py
        parts = list(rel.parts)
        parts[-1] = parts[-1].replace(".py", "")
        return ".".join(parts)

    def _try_instantiate(self, cls: Type, rel_path: str) -> Dict[str, Any]:
        """
        Tenta instanciar um widget e capturar .styleSheet().

        Returns:
            Dict com file, class_name, stylesheet, has_stylesheet, error.
        """
        class_name = cls.__name__
        result: Dict[str, Any] = {
            "file": rel_path,
            "class_name": class_name,
            "stylesheet": "",
            "has_stylesheet": False,
            "error": "",
        }

        # Args especiais
        args = self.SPECIAL_ARGS.get(class_name, {})

        try:
            instance = cls(**args)
            ss = instance.styleSheet()
            if ss and ss.strip():
                result["stylesheet"] = ss.strip()
                result["has_stylesheet"] = True
            instance.deleteLater()
        except Exception as e:
            # Tenta sem argumentos
            try:
                instance = cls()
                ss = instance.styleSheet()
                if ss and ss.strip():
                    result["stylesheet"] = ss.strip()
                    result["has_stylesheet"] = True
                instance.deleteLater()
            except Exception as e2:
                result["error"] = f"{e2.__class__.__name__}: {e2}"

        return result

    # ── Formatação ──────────────────────────────────────────────

    def _format_report(self) -> str:
        """Formata os resultados em relatório textual com stylesheets."""
        lines: list[str] = []
        lines.append("=" * 100)
        lines.append("  RELATÓRIO DE STYLESHEETS — Aetheris ToolBox Widgets")
        lines.append("=" * 100)
        lines.append(f"  Diretório: {self.widgets_dir}")
        lines.append(f"  Data: {self._get_timestamp()}")
        lines.append("=" * 100)
        lines.append("")

        total = len(self._results)
        with_ss = sum(1 for r in self._results if r["has_stylesheet"])
        errors = sum(1 for r in self._results if r["error"])

        for result in self._results:
            lines.append(f"📁 {result['file']}")
            lines.append(f"   🏷️  {result['class_name']}")

            if result["error"]:
                lines.append(f"   ❌ ERRO: {result['error']}")
                lines.append("")
                continue

            if result["has_stylesheet"]:
                lines.append(f"   🎨 STYLESHEET:")
                ss = result["stylesheet"]
                for ss_line in ss.split("\n"):
                    lines.append(f"      {ss_line}")
            else:
                lines.append(f"   ⬜ Sem stylesheet (vazio)")

            lines.append("")

        # Sumário
        lines.append("=" * 100)
        lines.append("  RESUMO")
        lines.append("=" * 100)
        lines.append(f"  Widgets encontrados:  {total}")
        lines.append(f"  Com stylesheet:       {with_ss}")
        lines.append(f"  Sem stylesheet:       {total - with_ss - errors}")
        lines.append(f"  Com erro:             {errors}")
        lines.append("=" * 100)

        return "\n".join(lines)

    @staticmethod
    def _get_timestamp() -> str:
        from datetime import datetime
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


# ── Execução direta ─────────────────────────────────────────────

if __name__ == "__main__":
    checker = CheckWidgets()
    checker.run()