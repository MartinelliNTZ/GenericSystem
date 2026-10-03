# -*- coding: utf-8 -*-
"""
core/papeline/task — Tasks concretas de BaseTask
===================================================
Tasks assíncronas que executam trabalho pesado em background,
seguindo o padrão BaseTask do sistema de pipeline.

Tasks disponíveis:
    - MrkSinglePipelineTask: Processa 1 arquivo MRK
    - DoclingPipelineTask:   Converte documento via Docling
"""

from .MrkSinglePipelineTask import MrkSinglePipelineTask
from .DoclingPipelineTask import DoclingPipelineTask
from .LasBlackFilterTask import LasBlackFilterTask
from .LasCheckTask import LasCheckTask
from .LasTilerTask import LasTilerTask
from .LasToVectorTask import LasToVectorTask
from .VectorToLasTask import VectorToLasTask
from .FootballFetchTask import FootballFetchTask

__all__ = [
    "MrkSinglePipelineTask",
    "DoclingPipelineTask",
    "LasBlackFilterTask",
    "LasCheckTask",
    "LasTilerTask",
    "LasToVectorTask",
    "VectorToLasTask",
    "FootballFetchTask",
]
