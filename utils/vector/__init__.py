# -*- coding: utf-8 -*-
"""
Vector — Pacote de utilitarios para dados vetoriais
====================================================
Fornece classes para manipulacao de camadas vetoriais:
- VectorLayerSource: I/O, validacao, salvamento e carregamento
- VectorLayerAttributes: Campos, atributos e dados tabulares
- VectorLayerGeometry: Transformacoes geometricas (buffer, explode, merge)
- VectorLayerMetrics: Metricas espaciais (comprimento, area, perimetro)
- VectorLayerProjection: CRS, reprojecao, conversao de unidades
"""

from __future__ import annotations

from utils.vector.VectorLayerAttributes import VectorLayerAttributes
from utils.vector.VectorLayerGeometry import VectorLayerGeometry
from utils.vector.VectorLayerMetrics import VectorLayerMetrics
from utils.vector.VectorLayerProjection import VectorLayerProjection
from utils.vector.VectorLayerSource import VectorLayerSource

__all__ = [
    "VectorLayerAttributes",
    "VectorLayerGeometry",
    "VectorLayerMetrics",
    "VectorLayerProjection",
    "VectorLayerSource",
]