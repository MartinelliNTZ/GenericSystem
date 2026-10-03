# -*- coding: utf-8 -*-
"""
core/governor — Sistema de Governança de Recursos
===================================================
Monitoramento de RAM e controle de limite para evitar OOM.

ATENÇÃO: Este __init__.py NÃO importa classes internas para evitar
circular imports. Faça imports diretos dos módulos:
    from core.governor.RamGovernor import RamGovernor
    from core.governor.RamLimitPolicy import RamLimitPolicy, RamLimitMode
    from core.governor.ResourceGovernor import ResourceGovernor, ResourceExceededError
    from core.governor.CpuGovernor import CpuGovernor

"""