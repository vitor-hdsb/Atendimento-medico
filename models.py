"""
models.py
---------
Define as estruturas de dados para a aplicação de atendimentos médicos.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

# --- Estrutura de dados para Conduta de Enfermagem ---
@dataclass
class Conduta:
    """Representa uma conduta médica ou de enfermagem."""
    hipotese_diagnostica: str
    conduta_adotada: str
    resumo_conduta: str
    medicamento_administrado: str
    medicamento: str
    posologia: str
    horario_medicacao: str
    observacoes: str

# --- Estrutura de dados para Atendimento Completo ---
@dataclass
class Atendimento:
    """Representa um registro de atendimento completo de um paciente."""
    id: Optional[int] = None
    badge_number: int = 0
    nome: str = ""
    login: str = ""
    gestor: str = ""
    turno: str = ""
    setor: str = ""
    processo: str = ""
    tenure: str = ""
    queixa_principal: str = ""
    hqa: str = ""
    tax: str = ""
    pa: str = ""
    fc: str = ""
    sat: str = ""
    doencas_preexistentes: str = ""
    alergias: str = ""
    medicamentos_em_uso: str = ""
    observacoes: str = ""
    data_atendimento: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    hora_atendimento: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    semana_iso: int = field(default_factory=lambda: datetime.now().isocalendar()[1])
    condutas: List[Conduta] = field(default_factory=list)

