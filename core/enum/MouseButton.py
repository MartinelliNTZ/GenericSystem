# -*- coding: utf-8 -*-
"""
MouseButton — Enum de botões do mouse
======================================
Centraliza os nomes dos botões do mouse em um Enum para evitar
strings soltas no código e facilitar manutenção.

Compatível com pyautogui.click(button=...).
"""

from __future__ import annotations

from enum import Enum


class MouseButton(str, Enum):
    """Enum com os botões do mouse suportados pelo sistema."""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    X1 = "x1"
    X2 = "x2"

    # ── Métodos utilitários ──────────────────────────────────────────

    @classmethod
    def display_names(cls) -> list[str]:
        """Retorna lista com os nomes de exibição amigáveis."""
        return ["Left", "Right", "Middle", "X1", "X2"]

    @classmethod
    def _build_value_map(cls) -> dict[str, "MouseButton"]:
        """Mapeia nome minúsculo → enum."""
        return {member.value: member for member in cls}
    @classmethod
    def _value2member_map_(cls) -> dict[str, "MouseButton"]:
        """Mapeia nome minúsculo → enum."""
        return {member.value: member for member in cls}

    @classmethod
    def from_name(cls, name: str) -> "MouseButton":
        """
        Retorna o enum correspondente ao nome, ou levanta ValueError.

        Exemplo:
            MouseButton.from_name("left")   # MouseButton.LEFT
            MouseButton.from_name("RIGHT")  # MouseButton.RIGHT
        """
        try:
            return cls(name.lower())
        except ValueError:
            raise ValueError(
                f"'{name}' não é um MouseButton válido. "
                f"Opções: {', '.join(m.value for m in cls)}"
            )