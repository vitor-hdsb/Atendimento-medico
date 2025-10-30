import json
import os

# Define o nome do arquivo de configuração das opções
OPTIONS_FILE = "options_config.json"

# --- Funções para carregar e salvar opções ---
def load_options():
    """Carrega as opções do arquivo JSON."""
    default_options = {
        "gestores": [],
        "turnos": ["Blue Day", "Blue Night", "Red Day", "Red Night", "MID", "ADM", "12X36 - Ímpar", "12X36 - Par"],
        "setores": [],
        "processos": [],
        # Mantém as opções fixas aqui
        "resumo_conduta": ["Em observação", "Liberado para operação", "Liberado para atendimento externo c/ brigadista", "Liberado para atendimento externo s/ brigadista", "Apto para trabalho em altura", "Inapto para trabalho em altura"],
        "medicamento_admin": ["Paracetamol", "Dipirona", "Ibuprofeno", "Outros", "N/A"]
    }
    try:
        if os.path.exists(OPTIONS_FILE):
            with open(OPTIONS_FILE, 'r', encoding='utf-8') as f:
                loaded_options = json.load(f)
                # Garante que todas as chaves editáveis existam
                for key in ["gestores", "turnos", "setores", "processos"]:
                    if key not in loaded_options:
                        loaded_options[key] = default_options[key] # Usa o default se faltar
                # Adiciona as chaves fixas que não vêm do JSON
                loaded_options["resumo_conduta"] = default_options["resumo_conduta"]
                loaded_options["medicamento_admin"] = default_options["medicamento_admin"]
                # Ordena as listas carregadas
                for key in ["gestores", "setores", "processos"]:
                    if key in loaded_options:
                         loaded_options[key] = sorted(loaded_options[key])
                return loaded_options
        else:
             # Se o arquivo não existe, cria com defaults e retorna
             save_options(default_options)
             print(f"Arquivo '{OPTIONS_FILE}' não encontrado. Criado com valores padrão.")
             # Ordena antes de retornar
             for key in ["gestores", "setores", "processos"]:
                  default_options[key] = sorted(default_options[key])
             return default_options
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar '{OPTIONS_FILE}': {e}. Usando valores padrão.")
        # Ordena defaults antes de retornar em caso de erro
        for key in ["gestores", "setores", "processos"]:
             default_options[key] = sorted(default_options[key])
        return default_options

def save_options(options_dict):
    """Salva as opções no arquivo JSON."""
    try:
        # Garante a ordenação antes de salvar
        options_to_save = {}
        editable_keys = ["gestores", "turnos", "setores", "processos"]
        for key in editable_keys:
             if key in options_dict:
                 # Ordena se não for 'turnos' (que tem ordem específica)
                 options_to_save[key] = sorted(options_dict[key]) if key != "turnos" else options_dict[key]

        with open(OPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(options_to_save, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Erro ao salvar '{OPTIONS_FILE}': {e}")
        return False

# --- Carrega as opções quando o módulo é importado ---
OPTIONS = load_options()

# --- Listas de Sintomas e Regiões (mantidas aqui por enquanto) ---
SINTOMAS = [
    "Dor", "Ardência/Queimação", "Coçeira/Irritaçao", "Corte",
    "Torção/Distensão", "Vertigem", "Vômito", "Náuseas", "Fraqueza",
    "Confusão mental", "Abrasão/Escoriação", "Ansiedade",
    "Absorvente", "Trabalho em altura"
]

REGIOES = [
    "Cabeça", "Rosto", "Olhos", "Braços", "Mãos/Dedos", "Peitoral/Seios",
    "Barriga/Estômago", "Pernas", "Pé", "Tornozelo", "N/A", "Menstrual"
]

