import json
import os
import sys # Necessário para encontrar o caminho do .exe

# Define o nome do arquivo de configuração das opções
OPTIONS_FILE = "options_config.json"

# --- CORREÇÃO: Encontra o caminho absoluto para o arquivo de config ---
# Isso garante que o .exe encontre o options_config.json
def get_base_path():
    """Retorna o diretório base para encontrar arquivos de dados."""
    if getattr(sys, 'frozen', False):
        # Estamos rodando em um .exe (PyInstaller)
        base_path = os.path.dirname(sys.executable)
    else:
        # Estamos rodando como .py
        # Assume que constants.py está em 'gui/', e o .json está na raiz
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return base_path

OPTIONS_FILE_PATH = os.path.join(get_base_path(), OPTIONS_FILE)
# --- Fim da Correção ---


# --- Funções para carregar e salvar opções ---
def load_options():
    """Carrega as opções do arquivo JSON."""
    default_options = {
        "gestores": [],
        "turnos": ["Blue Day", "Blue Night", "Red Day", "Red Night", "MID", "ADM", "12X36 - Ímpar", "12X36 - Par"],
        "setores": [],
        "processos": [],
        # --- MELHORIA: Adiciona tipo_atendimento ---
        "tipo_atendimento": ["Ocupacional", "Não Ocupacional", "N/A"],
        # Mantém as opções fixas aqui
        "resumo_conduta": ["Em observação", "Liberado para operação", "Liberado para atendimento externo c/ brigadista", "Liberado para atendimento externo s/ brigadista", "Apto para trabalho em altura", "Inapto para trabalho em altura"],
        "medicamento_admin": ["Paracetamol", "Dipirona", "Ibuprofeno", "Outros", "N/A"]
    }
    try:
        # --- CORREÇÃO: Usa o caminho absoluto ---
        if os.path.exists(OPTIONS_FILE_PATH):
            with open(OPTIONS_FILE_PATH, 'r', encoding='utf-8') as f:
            # --- Fim da Correção ---
                loaded_options = json.load(f)
                
                # Garante que todas as chaves (novas e antigas) existam
                for key, default_value in default_options.items():
                    if key not in loaded_options:
                        loaded_options[key] = default_value # Usa o default se faltar
                        
                # Ordena as listas carregadas (exceto as de ordem específica)
                for key in ["gestores", "setores", "processos"]:
                    if key in loaded_options:
                         loaded_options[key] = sorted(loaded_options[key])
                return loaded_options
        else:
             # Se o arquivo não existe, cria com defaults e retorna
             save_options(default_options) # Salva no caminho absoluto
             print(f"Arquivo '{OPTIONS_FILE_PATH}' não encontrado. Criado com valores padrão.")
             # Ordena defaults antes de retornar
             for key in ["gestores", "setores", "processos"]:
                  default_options[key] = sorted(default_options[key])
             return default_options
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar '{OPTIONS_FILE_PATH}': {e}. Usando valores padrão.")
        # Ordena defaults antes de retornar em caso de erro
        for key in ["gestores", "setores", "processos"]:
             default_options[key] = sorted(default_options[key])
        return default_options

def save_options(options_dict):
    """Salva as opções no arquivo JSON."""
    try:
        options_to_save = {}
        # Salva apenas as chaves que são editáveis
        editable_keys = ["gestores", "turnos", "setores", "processos"] 
        
        for key in editable_keys:
             if key in options_dict:
                 # Ordena se não for 'turnos' (que tem ordem específica)
                 options_to_save[key] = sorted(options_dict[key]) if key != "turnos" else options_dict[key]
        
        # --- CORREÇÃO: Usa o caminho absoluto ---
        with open(OPTIONS_FILE_PATH, 'w', encoding='utf-8') as f:
        # --- Fim da Correção ---
            json.dump(options_to_save, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Erro ao salvar '{OPTIONS_FILE_PATH}': {e}")
        return False

# --- Carrega as opções quando o módulo é importado ---
OPTIONS = load_options()

# --- Listas de Sintomas e Regiões (mantidas) ---
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

