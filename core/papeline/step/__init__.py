# -*- coding: utf-8 -*-
"""
core/async/step — Implementações concretas de BaseStep
========================================================
Steps que compõem a pipeline, seguindo o padrão BaseStep.

Disponíveis:
    - MrkLoadDataStep: Carrega dados vetoriais
    - MrkLoadDataStep: Valida que o arquivo de dados existe (carga feita pelo MrkProcessStep)
    - MrkProcessStep: Processa arquivo MRK contra dados
    - MrkFindDataStep: Busca dados automaticamente pelo nome
    - DoclingConvertStep: Converte documento para Markdown
    - DoclingSaveStep: Salva Markdown em arquivo
"""

from .MrkSteps import MrkLoadDataStep, MrkProcessStep, MrkFindDataStep
from .DoclingSteps import DoclingConvertStep, DoclingSaveStep
from .LasBlackFilterSteps import LasBlackFilterStep
from .LasCheckStep import LasCheckStep
from .LasTilerStep import LasTilerStep
from .LasToVectorStep import LasToVectorStep
from .VectorToLasStep import VectorToLasStep
from .FootballFetchStep import FootballFetchStep

__all__ = [
    "MrkLoadDataStep",
    "MrkProcessStep",
    "MrkFindDataStep",
    "DoclingConvertStep",
    "DoclingSaveStep",
    "LasBlackFilterStep",
    "LasCheckStep",
    "LasTilerStep",
    "LasToVectorStep",
    "VectorToLasStep",
    "FootballFetchStep",
]
