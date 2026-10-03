# -*- coding: utf-8 -*-
"""
CommonCrs — Enum de Sistemas de Referência de Coordenadas (CRS) comuns
======================================================================
Centraliza os EPSGs mais utilizados no contexto brasileiro (WGS84 e
SIRGAS 2000 UTM) em um Enum para uso no CrsSelectorWidget.

Cada item contém:
    - code (int)       — código numérico EPSG (ex: 4326)
    - name (str)       — nome descritivo (ex: "WGS 84")
    - authority (str)  — autoridade (sempre "EPSG")
"""

from __future__ import annotations

from enum import Enum


class CommonCrs(str, Enum):
    """Enum com os CRS/EPSG mais comuns pré-configurados."""
    BLANK = ""                    # Nenhum CRS selecionado
    EPSG_4326 = "EPSG:4326"      # WGS 84
    EPSG_31980 = "EPSG:31980"    # SIRGAS 2000 / UTM zone 20S
    EPSG_31981 = "EPSG:31981"    # SIRGAS 2000 / UTM zone 21S
    EPSG_31982 = "EPSG:31982"    # SIRGAS 2000 / UTM zone 22S
    EPSG_31983 = "EPSG:31983"    # SIRGAS 2000 / UTM zone 23S
    EPSG_31984 = "EPSG:31984"    # SIRGAS 2000 / UTM zone 24S

    # ── Metadados ──────────────────────────────────────────────────────────

    @property
    def code(self) -> int:
        """Código numérico EPSG (ex: 4326)."""
        return int(self.value.split(":")[1])

    @property
    def name_clean(self) -> str:
        """Nome descritivo sem o prefixo EPSG (ex: 'WGS 84')."""
        # Mapa interno para evitar depender de pyproj só para nomes
        _names = {
            "": "",
            "EPSG:4326": "WGS 84",
            "EPSG:31980": "SIRGAS 2000 / UTM zone 20S",
            "EPSG:31981": "SIRGAS 2000 / UTM zone 21S",
            "EPSG:31982": "SIRGAS 2000 / UTM zone 22S",
            "EPSG:31983": "SIRGAS 2000 / UTM zone 23S",
            "EPSG:31984": "SIRGAS 2000 / UTM zone 24S",
        }
        return _names.get(self.value, self.value)

    @property
    def authority(self) -> str:
        """Autoridade do CRS (sempre 'EPSG')."""
        return "EPSG"

    # ── Métodos de exibição ────────────────────────────────────────────────

    def label(self) -> str:
        """Retorna o texto formatado: 'EPSG:4326 - WGS 84'."""
        return f"{self.value} - {self.name_clean}"

    # ── Métodos utilitários ────────────────────────────────────────────────

    @classmethod
    def display_names(cls) -> list[str]:
        """Retorna lista com labels de todos os CRS."""
        return [item.label() for item in cls]

    @classmethod
    def to_dict(cls) -> dict[str, str]:
        """
        Retorna dicionário {valor_epsg: label_formatada} para uso
        em SimpleComboBox.set_items().

        Exemplo:
            {
                "EPSG:4326": "EPSG:4326 - WGS 84",
                "EPSG:31983": "EPSG:31983 - SIRGAS 2000 / UTM zone 23S",
            }
        """
        return {item.value: item.label() for item in cls}

    def simple_name(self) -> str:
        """
        Nome simplificado sem o prefixo 'EPSG:' e sem 'zone'.
        Ex: 'SIRGAS 2000 23S' ao invés de 'EPSG:31983 - SIRGAS 2000 / UTM zone 23S'.
        """
        _simple = {
            "": "",
            "EPSG:4326": "WGS 84",
            "EPSG:31980": "SIRGAS 2000 20S",
            "EPSG:31981": "SIRGAS 2000 21S",
            "EPSG:31982": "SIRGAS 2000 22S",
            "EPSG:31983": "SIRGAS 2000 23S",
            "EPSG:31984": "SIRGAS 2000 24S",
        }
        return _simple.get(self.value, self.value)

    @classmethod
    def to_simple_dict(cls) -> dict[str, str]:
        """
        Retorna dicionário {valor_epsg: nome_simplificado} para uso
        em CRS embutido no ComplexSelector (modo compacto).

        Exemplo:
            {
                "EPSG:4326": "WGS 84",
                "EPSG:31983": "SIRGAS 2000 23S",
            }
        """
        return {item.value: item.simple_name() for item in cls}

    @classmethod
    def from_code(cls, code: int) -> "CommonCrs | None":
        """
        Retorna o enum correspondente ao código numérico.

        Args:
            code: Código EPSG (ex: 4326).

        Returns:
            CommonCrs ou None se não encontrado.
        """
        for item in cls:
            if item.code == code:
                return item
        return None

    @classmethod
    def contains(cls, epsg_value: str) -> bool:
        """Verifica se um valor EPSG (ex: 'EPSG:4326') está no enum."""
        return any(item.value == epsg_value for item in cls)