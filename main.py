#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aetheris ToolBox — Ponto de Entrada
====================================
Executável principal. Apenas chama o BootStrap singleton.

Uso:
    python main.py.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path


def main():
    # Garante que a raiz do projeto está no sys.path.
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        from core.config.BootStrap import BootStrap
        BootStrap().run()
    except Exception as exc:
        # ── Última barreira contra crashes no startup ──────────────
        # Se algo falhar antes dos hooks do ExceptionHandler serem
        # instalados (ex: erro no import do PySide6), esta camada
        # garante que o erro seja registrado e visível ao usuário.
        tb_text = "".join(traceback.format_exc())

        # Tenta logar via LogUtils (pode falhar se erro for cedo demais)
        try:
            from core.config.LogUtils import LogUtils
            logger = LogUtils(tool="System", class_name="Main")
            logger.critical(
                f"Falha fatal no bootstrap: {exc}",
                code="BOOTSTRAP_FATAL",
                traceback=tb_text,
            )
        except Exception:
            pass  # LogUtils indisponível — segue para stdout -

        # Mensagem no console
        print("=" * 60, file=sys.stderr)
        print("  AETHERIS TOOLBOX — ERRO FATAL NA INICIALIZAÇÃO", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"\nTipo: {type(exc).__name__}", file=sys.stderr)
        print(f"Erro: {exc}", file=sys.stderr)
        print(f"\nTraceback:\n{tb_text}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("  Verifique o arquivo de log em /log/ para mais detalhes..", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

        # Tenta exibir um message box amigável via MessageBox centralizado
        try:
            from utils.MessageBox import MessageBox
            MessageBox.show_critical(
                text=(
                    f"Não foi possível iniciar o Aetheris ToolBox.\n\n"
                    f"Tipo: {type(exc).__name__}\n"
                    f"Erro: {exc}\n\n"
                    f"Verifique os logs para mais detalhes."
                ),
                title="Erro Fatal na Inicialização",
                detail=tb_text,
            )
        except Exception:
            pass  # Falhou até o MessageBox — não há mais o que fazer

        sys.exit(1)


if __name__ == "__main__":
    main()