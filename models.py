"""
models.py
---------
Módulo para definição das classes de dados.
"""
from typing import List, Optional

class Atendimento:
    """Representa um atendimento médico completo."""
    def __init__(self,
                 badge_number: int,
                 nome: str,
                 login: str,
                 gestor: str,
                 turno: str,
                 setor: str,
                 processo: str,
                 tenure: str,
                 queixas_principais: str,
                 hqa: str,
                 tax: str,
                 pa_sistolica: str,
                 pa_diastolica: str,
                 fc: str,
                 sat: str,
                 doencas_preexistentes: str,
                 alergias: str,
                 medicamentos_em_uso: str,
                 observacoes: str,
                 condutas: List['Conduta'] = None,
                 data_atendimento: Optional[str] = None,
                 hora_atendimento: Optional[str] = None,
                 semana_iso: Optional[int] = None,
                 id: Optional[int] = None):
        self.id = id
        self.badge_number = badge_number
        self.nome = nome
        self.login = login
        self.gestor = gestor
        self.turno = turno
        self.setor = setor
        self.processo = processo
        self.tenure = tenure
        self.queixas_principais = queixas_principais
        self.hqa = hqa
        self.tax = tax
        self.pa_sistolica = pa_sistolica
        self.pa_diastolica = pa_diastolica
        self.fc = fc
        self.sat = sat
        self.doencas_preexistentes = doencas_preexistentes
        self.alergias = alergias
        self.medicamentos_em_uso = medicamentos_em_uso
        self.observacoes = observacoes
        self.condutas = condutas if condutas is not None else []
        self.data_atendimento = data_atendimento
        self.hora_atendimento = hora_atendimento
        self.semana_iso = semana_iso

class Conduta:
    """Representa uma conduta médica."""
    def __init__(self,
                 hipotese_diagnostica: str,
                 conduta_adotada: str,
                 resumo_conduta: str,
                 medicamento_administrado: str,
                 posologia: str,
                 horario_medicacao: str,
                 observacoes: str):
        self.hipotese_diagnostica = hipotese_diagnostica
        self.conduta_adotada = conduta_adotada
        self.resumo_conduta = resumo_conduta
        self.medicamento_administrado = medicamento_administrado
        self.posologia = posologia
        self.horario_medicacao = horario_medicacao
        self.observacoes = observacoes
