# config_manager.py
import configparser
import os
import sys

# Define o nome do arquivo de configuração
CONFIG_FILENAME = "atendimento_config.ini"

def get_config_path():
    """Retorna o caminho completo para o arquivo de configuração."""
    # Tenta salvar na mesma pasta do executável
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como um executável PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Se estiver rodando como script Python normal
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, CONFIG_FILENAME)

def save_db_path(db_path):
    """Salva o caminho do banco de dados no arquivo de configuração."""
    config = configparser.ConfigParser()
    config['Database'] = {'Path': db_path}
    
    config_filepath = get_config_path()
    try:
        with open(config_filepath, 'w') as configfile:
            config.write(configfile)
        print(f"Configuração salva em: {config_filepath}") # Log
        return True
    except IOError as e:
        print(f"Erro ao salvar configuração em {config_filepath}: {e}")
        return False

def load_db_path():
    """Carrega o caminho do banco de dados do arquivo de configuração."""
    config = configparser.ConfigParser()
    config_filepath = get_config_path()
    
    if os.path.exists(config_filepath):
        try:
            config.read(config_filepath)
            if 'Database' in config and 'Path' in config['Database']:
                db_path = config['Database']['Path']
                # Verifica se o caminho ainda é válido
                if db_path and os.path.exists(db_path):
                    print(f"Banco de dados carregado de: {db_path}") # Log
                    return db_path
                else:
                     print(f"Caminho do banco de dados salvo ({db_path}) não é mais válido.") # Log
            else:
                 print("Arquivo de configuração não contém seção/chave do banco de dados.") # Log
        except configparser.Error as e:
            print(f"Erro ao ler arquivo de configuração {config_filepath}: {e}")
            # Considerar apagar/renomear o arquivo corrompido
    else:
         print(f"Arquivo de configuração não encontrado em: {config_filepath}") # Log

    return None # Retorna None se não encontrar, for inválido ou erro
