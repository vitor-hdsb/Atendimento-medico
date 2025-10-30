"""
models.py
---------
Módulo para definição das classes de dados.
"""
from typing import List, Optional

class Atendimento:
    """Representa um atendimento médico completo."""
    def __init__(self,
                 badge_number: str,
                 nome: str = "N/A",
                 login: str = "N/A",
                 gestor: str = "N/A",
                 turno: str = "N/A",
                 setor: str = "N/A",
                 processo: str = "N/A",
                 tenure: str = "N/A",
                 # --- MELHORIA: Adiciona tipo_atendimento ---
                 tipo_atendimento: str = "N/A",
                 # --- Fim Melhoria ---
                 qp_sintoma: str = "N/A",
                 qp_regiao: str = "N/A",
                 qs_sintomas: str = "[]", # JSON string
                 qs_regioes: str = "[]",  # JSON string
                 hqa: str = "N/A",
                 tax: str = "N/A",
                 pa_sistolica: str = "N/A",
                 pa_diastolica: str = "N/A",
                 fc: str = "N/A",
                 sat: str = "N/A",
                 doencas_preexistentes: str = "N/A",
                 alergias: str = "N/A",
                 medicamentos_em_uso: str = "N/A",
                 observacoes: str = "N/A",
                 condutas: Optional[List['Conduta']] = None,
                 data_atendimento: Optional[str] = None,
                 hora_atendimento: Optional[str] = None,
                 semana_iso: Optional[int] = None,
                 id: Optional[int] = None, **kwargs): # Aceita kwargs para ignorar extras
        self.id = id
        self.badge_number = badge_number
        self.nome = nome
        self.login = login
        self.gestor = gestor
        self.turno = turno
        self.setor = setor
        self.processo = processo
        self.tenure = tenure
        # --- MELHORIA: Adiciona tipo_atendimento ---
        self.tipo_atendimento = tipo_atendimento
        # --- Fim Melhoria ---
        self.qp_sintoma = qp_sintoma
        self.qp_regiao = qp_regiao
        self.qs_sintomas = qs_sintomas
        self.qs_regioes = qs_regioes
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
                 hipotese_diagnostica: str = "N/A",
                 resumo_conduta: str = "N/A",
                 medicamento_administrado: str = "N/A",
                 posologia: str = "N/A",
                 horario_medicacao: str = "N/A",
                 observacoes: str = "N/A",
                 id: Optional[int] = None, # Adiciona ID para rastreamento
                 atendimento_id: Optional[int] = None, # Adiciona atendimento_id
                 **kwargs): # Aceita kwargs para ignorar extras (como conduta_adotada)
        self.id = id
        self.atendimento_id = atendimento_id
        self.hipotese_diagnostica = hipotese_diagnostica
        # self.conduta_adotada = "N/A" # Campo não é mais usado
        self.resumo_conduta = resumo_conduta
        self.medicamento_administrado = medicamento_administrado
        self.posologia = posologia
        self.horario_medicacao = horario_medicacao
        self.observacoes = observacoes

