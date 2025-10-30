import configparser
import os
import sys # Necessário para encontrar o caminho do .exe

CONFIG_FILE = "atendimento_config.ini"

# --- CORREÇÃO: Encontra o caminho absoluto para o .ini ---
def get_config_path():
    """Retorna o caminho absoluto para o .ini, perto do .exe ou .py"""
    if getattr(sys, 'frozen', False):
        # Estamos rodando em um .exe (PyInstaller)
        base_path = os.path.dirname(sys.executable)
    else:
        # Estamos rodando como .py
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, CONFIG_FILE)
# --- Fim da Correção ---

CONFIG_FILE_PATH = get_config_path()

def save_db_path(db_path):
    """Salva o caminho do banco de dados no arquivo de configuração."""
    config = configparser.ConfigParser()
    config['Database'] = {'path': db_path}
    try:
        # --- CORREÇÃO: Usa o caminho absoluto ---
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as configfile:
        # --- Fim da Correção ---
            config.write(configfile)
    except IOError as e:
        print(f"Erro ao salvar configuração em {CONFIG_FILE_PATH}: {e}")

def load_db_path():
    """Lê o caminho do banco de dados do arquivo de configuração."""
    config = configparser.ConfigParser()
    try:
        # --- CORREÇÃO: Usa o caminho absoluto ---
        if not os.path.exists(CONFIG_FILE_PATH):
        # --- Fim da Correção ---
            print(f"Arquivo de configuração não encontrado: {CONFIG_FILE_PATH}")
            return None
            
        config.read(CONFIG_FILE_PATH, encoding='utf-8')
        
        if 'Database' in config and 'path' in config['Database']:
            db_path = config['Database']['path']
            # Verifica se o caminho salvo ainda é válido
            if os.path.exists(db_path):
                return db_path
            else:
                print(f"Caminho do DB salvo é inválido (não encontrado): {db_path}")
                return None
        return None
    except Exception as e:
        print(f"Erro ao ler configuração {CONFIG_FILE_PATH}: {e}")
        return None

