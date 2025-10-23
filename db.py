"""
db.py
-----
Módulo para gerenciamento do banco de dados SQLite.
Utiliza um caminho configurável para o arquivo DB.
"""
import sqlite3
from datetime import datetime, timedelta
import csv
from models import Atendimento, Conduta
import os
import json # Adicionado para queixas

# Variável global para armazenar o caminho do banco de dados atual
_db_path = None

def set_db_path(path):
    """Define o caminho do arquivo de banco de dados a ser usado."""
    global _db_path
    # Validação básica
    if path and os.path.exists(os.path.dirname(path)) and path.lower().endswith(".db"):
         # Verifica se o diretório existe e se termina com .db
        _db_path = path
        print(f"Caminho do banco de dados definido para: {_db_path}") # Log
        return True
    elif path and not os.path.exists(os.path.dirname(path)):
         print(f"Erro: Diretório para o banco de dados não existe: {os.path.dirname(path)}")
         _db_path = None
         return False
    else:
        print(f"Erro: Caminho do banco de dados inválido: {path}")
        _db_path = None
        return False

def get_db_path():
    """Retorna o caminho do banco de dados atualmente configurado."""
    # Idealmente, esta função não deveria existir; as outras deveriam usar _db_path.
    # Mas para mínima alteração, vamos mantê-la por enquanto.
    # Ou melhor: vamos refatorar para usar _db_path diretamente.
    if not _db_path:
        raise ValueError("Caminho do banco de dados não foi definido. Chame set_db_path primeiro.")
    return _db_path

def _get_connection():
    """Retorna uma conexão com o banco de dados configurado."""
    if not _db_path:
        raise ConnectionError("Caminho do banco de dados não definido.")
    try:
        conn = sqlite3.connect(_db_path)
        conn.execute("PRAGMA foreign_keys = ON;") # Habilita chaves estrangeiras
        conn.execute("PRAGMA journal_mode = WAL;") # Mantém WAL mode
        return conn
    except sqlite3.Error as e:
        raise ConnectionError(f"Erro ao conectar ao banco de dados em {_db_path}: {e}") from e


def init_db():
    """Inicializa o banco de dados no caminho configurado."""
    # Não precisa mais verificar _db_path aqui, _get_connection faz isso.
    conn = None
    try:
        # Apenas tenta conectar; se o arquivo não existir, connect cria.
        # Mas precisamos garantir que as tabelas existam.
        conn = _get_connection()
        cursor = conn.cursor()

        # Cria a tabela atendimentos se não existir (com novas colunas de queixa)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atendimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_number TEXT NOT NULL,
                nome TEXT,
                login TEXT,
                gestor TEXT,
                turno TEXT,
                setor TEXT,
                processo TEXT,
                tenure TEXT,
                qp_sintoma TEXT DEFAULT 'N/A',      -- Queixa Principal Sintoma
                qp_regiao TEXT DEFAULT 'N/A',       -- Queixa Principal Região
                qs_sintomas TEXT DEFAULT '[]',      -- Queixa Secundária Sintomas (JSON)
                qs_regioes TEXT DEFAULT '[]',       -- Queixa Secundária Regiões (JSON)
                hqa TEXT,
                tax TEXT,
                pa_sintolica TEXT,
                pa_diastolica TEXT,
                fc TEXT,
                sat TEXT,
                doencas_preexistentes TEXT,
                alergias TEXT,
                medicamentos_em_uso TEXT,
                observacoes TEXT,
                data_atendimento TEXT NOT NULL,
                hora_atendimento TEXT NOT NULL,
                semana_iso INTEGER NOT NULL
            )
        """)
        # Adiciona colunas se não existirem (para migração simples)
        _add_column_if_not_exists(cursor, 'atendimentos', 'qp_sintoma', 'TEXT', 'N/A')
        _add_column_if_not_exists(cursor, 'atendimentos', 'qp_regiao', 'TEXT', 'N/A')
        _add_column_if_not_exists(cursor, 'atendimentos', 'qs_sintomas', 'TEXT', '[]')
        _add_column_if_not_exists(cursor, 'atendimentos', 'qs_regioes', 'TEXT', '[]')
        # Remove coluna antiga se existir (opcional, cuidado com perda de dados)
        # _remove_column_if_exists(cursor, 'atendimentos', 'queixas_principais')


        # Cria a tabela condutas se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS condutas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atendimento_id INTEGER NOT NULL,
                hipotese_diagnostica TEXT,
                -- conduta_adotada TEXT, -- Removido conforme solicitado
                resumo_conduta TEXT,
                medicamento_administrado TEXT,
                posologia TEXT,
                horario_medicacao TEXT,
                observacoes TEXT,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos (id) ON DELETE CASCADE
            )
        """)
        # Remove coluna antiga se existir (opcional)
        # _remove_column_if_exists(cursor, 'condutas', 'conduta_adotada')

        conn.commit()
        print(f"Banco de dados inicializado/verificado em: {_db_path}") # Log
        return True # Indica sucesso
    except (ValueError, ConnectionError, sqlite3.Error) as e:
         print(f"Erro ao inicializar o banco de dados: {e}")
         return False # Indica falha
    finally:
        if conn:
            conn.close()

# Função auxiliar para adicionar coluna (migração simples)
def _add_column_if_not_exists(cursor, table_name, column_name, column_type, default_value=None):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        if column_name not in columns:
            default_clause = f"DEFAULT '{default_value}'" if default_value is not None else ""
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {default_clause}")
            print(f"Coluna '{column_name}' adicionada à tabela '{table_name}'.")
    except sqlite3.Error as e:
        print(f"Erro ao verificar/adicionar coluna {column_name} em {table_name}: {e}")

# Função auxiliar para remover coluna (migração simples, CUIDADO: PERDA DE DADOS)
# def _remove_column_if_exists(cursor, table_name, column_name):
#     try:
#         cursor.execute(f"PRAGMA table_info({table_name})")
#         columns = [info[1] for info in cursor.fetchall()]
#         if column_name in columns:
#             # SQLite < 3.35 não suporta DROP COLUMN diretamente de forma simples
#             # A abordagem segura seria criar nova tabela, copiar dados, dropar antiga, renomear nova
#             # Para simplificar (assumindo SQLite >= 3.35 ou aceitando a complexidade):
#             try:
#                  cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
#                  print(f"Coluna '{column_name}' removida da tabela '{table_name}'.")
#             except sqlite3.OperationalError:
#                  print(f"Aviso: Sua versão do SQLite pode não suportar DROP COLUMN diretamente para '{column_name}'.")
#                  # Implementar a abordagem de recriar a tabela se necessário aqui
#                  pass
#     except sqlite3.Error as e:
#         print(f"Erro ao verificar/remover coluna {column_name} em {table_name}: {e}")


def save_atendimento(atendimento: Atendimento):
    """Salva um novo atendimento e suas condutas no banco de dados."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # Insere o atendimento principal (com novas colunas de queixa)
        cursor.execute("""
            INSERT INTO atendimentos (
                badge_number, nome, login, gestor, turno, setor, processo, tenure,
                qp_sintoma, qp_regiao, qs_sintomas, qs_regioes, -- Novas colunas
                hqa, tax, pa_sistolica, pa_diastolica, fc, sat, doencas_preexistentes,
                alergias, medicamentos_em_uso, observacoes, data_atendimento,
                hora_atendimento, semana_iso
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            atendimento.badge_number, atendimento.nome, atendimento.login, atendimento.gestor,
            atendimento.turno, atendimento.setor, atendimento.processo, atendimento.tenure,
            atendimento.qp_sintoma, atendimento.qp_regiao, atendimento.qs_sintomas, atendimento.qs_regioes, # Valores JSON
            atendimento.hqa, atendimento.tax, atendimento.pa_sistolica,
            atendimento.pa_diastolica, atendimento.fc, atendimento.sat, atendimento.doencas_preexistentes,
            atendimento.alergias, atendimento.medicamentos_em_uso, atendimento.observacoes,
            atendimento.data_atendimento, atendimento.hora_atendimento, atendimento.semana_iso
        ))
        atendimento_id = cursor.lastrowid

        # Insere todas as condutas associadas (sem conduta_adotada)
        for conduta in atendimento.condutas:
            cursor.execute("""
                INSERT INTO condutas (
                    atendimento_id, hipotese_diagnostica, resumo_conduta,
                    medicamento_administrado, posologia, horario_medicacao,
                    observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                atendimento_id, conduta.hipotese_diagnostica,
                conduta.resumo_conduta, conduta.medicamento_administrado,
                conduta.posologia, conduta.horario_medicacao, conduta.observacoes
            ))

        conn.commit()
        return atendimento_id
    except (ValueError, ConnectionError, sqlite3.Error) as e:
         print(f"Erro ao salvar atendimento: {e}")
         if conn: conn.rollback() # Desfaz alterações em caso de erro
         raise # Re-levanta a exceção para a GUI tratar
    finally:
        if conn:
            conn.close()


def get_atendimento_by_id(atendimento_id):
    """Busca um atendimento e suas condutas pelo ID."""
    conn = None
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row # Retorna resultados como dicionários
        cursor = conn.cursor()

        # Busca o atendimento
        cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,))
        atendimento_data = cursor.fetchone()
        if not atendimento_data:
            return None

        # Converte a Row em um dict para passar para o construtor
        atendimento_dict = dict(atendimento_data)

        # Busca as condutas associadas
        cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
        condutas_data = cursor.fetchall()
        
        condutas_list = [
            Conduta(
                hipotese_diagnostica=c["hipotese_diagnostica"],
                resumo_conduta=c["resumo_conduta"],
                medicamento_administrado=c["medicamento_administrado"],
                posologia=c["posologia"],
                horario_medicacao=c["horario_medicacao"],
                observacoes=c["observacoes"]
            ) for c in condutas_data
        ]
        
        # Cria o objeto Atendimento
        atendimento = Atendimento(**atendimento_dict) # Passa o dict desempacotado
        atendimento.condutas = condutas_list # Adiciona a lista de condutas

        return atendimento
    except (ValueError, ConnectionError, sqlite3.Error) as e:
         print(f"Erro ao buscar atendimento por ID ({atendimento_id}): {e}")
         return None # Ou raise? Depende de como a GUI quer tratar
    finally:
        if conn:
            conn.close()

def get_last_atendimento_by_badge(badge_number):
    """Busca o último atendimento de um paciente pelo número do crachá."""
    conn = None
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM atendimentos WHERE badge_number = ? ORDER BY data_atendimento DESC, hora_atendimento DESC LIMIT 1", (badge_number,))
        atendimento_data = cursor.fetchone()
        if atendimento_data:
            # Retorna um dict simples, talvez não precise do objeto Atendimento completo aqui
            return dict(atendimento_data)
        return None
    except (ValueError, ConnectionError, sqlite3.Error) as e:
         print(f"Erro ao buscar último atendimento por badge ({badge_number}): {e}")
         return None
    finally:
        if conn:
            conn.close()


def get_atendimentos_by_badge(badge_number=None, days_ago=15):
    """
    Busca atendimentos recentes para um paciente por período em dias.
    """
    conn = None
    try:
        conn = _get_connection()
        # conn.row_factory = sqlite3.Row # Não necessário, retorna tuplas como antes
        cursor = conn.cursor()
        
        date_limit = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        query_params = [date_limit]
        query_str = """
            SELECT id, badge_number, nome, login, data_atendimento, hora_atendimento
            FROM atendimentos
            WHERE data_atendimento >= ?
        """
        
        if badge_number is not None:
            query_str += " AND badge_number = ?"
            query_params.append(badge_number)
        
        query_str += " ORDER BY data_atendimento DESC, hora_atendimento DESC"
        
        cursor.execute(query_str, query_params)
        
        result = cursor.fetchall()
        return result
    except (ValueError, ConnectionError, sqlite3.Error) as e:
        print(f"Erro ao buscar atendimentos por badge/dias: {e}")
        return [] # Retorna lista vazia em caso de erro
    finally:
        if conn:
            conn.close()

def get_atendimentos_by_datetime_range(start_datetime_str, end_datetime_str, badge_number=None):
    """Busca atendimentos dentro de um intervalo de data e hora."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        query_params = [start_datetime_str, end_datetime_str]
        query_str = """
            SELECT id, badge_number, nome, login, data_atendimento, hora_atendimento
            FROM atendimentos
            WHERE (data_atendimento || ' ' || hora_atendimento) BETWEEN ? AND ?
        """
        
        if badge_number is not None:
            query_str += " AND badge_number = ?"
            query_params.append(badge_number)
        
        query_str += " ORDER BY data_atendimento DESC, hora_atendimento DESC"
        
        cursor.execute(query_str, query_params)
        
        result = cursor.fetchall()
        return result
    except (ValueError, ConnectionError, sqlite3.Error) as e:
        print(f"Erro ao buscar atendimentos por range de data/hora: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_atendimento(atendimento: Atendimento):
    """Atualiza um atendimento existente no banco de dados."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # Atualiza o atendimento principal (com novas colunas de queixa)
        cursor.execute("""
            UPDATE atendimentos SET
                nome = ?, login = ?, gestor = ?, turno = ?, setor = ?, processo = ?,
                tenure = ?,
                qp_sintoma = ?, qp_regiao = ?, qs_sintomas = ?, qs_regioes = ?, -- Novas
                hqa = ?, tax = ?, pa_sistolica = ?,
                pa_diastolica = ?, fc = ?, sat = ?, doencas_preexistentes = ?, alergias = ?,
                medicamentos_em_uso = ?, observacoes = ?
            WHERE id = ?
        """, (
            atendimento.nome, atendimento.login, atendimento.gestor, atendimento.turno,
            atendimento.setor, atendimento.processo, atendimento.tenure,
            atendimento.qp_sintoma, atendimento.qp_regiao, atendimento.qs_sintomas, atendimento.qs_regioes, # Valores JSON
            atendimento.hqa, atendimento.tax, atendimento.pa_sistolica,
            atendimento.pa_diastolica, atendimento.fc, atendimento.sat, atendimento.doencas_preexistentes,
            atendimento.alergias, atendimento.medicamentos_em_uso,
            atendimento.observacoes, atendimento.id
        ))

        # Remove as condutas antigas e insere as novas
        cursor.execute("DELETE FROM condutas WHERE atendimento_id = ?", (atendimento.id,))
        for conduta in atendimento.condutas:
            cursor.execute("""
                INSERT INTO condutas (
                    atendimento_id, hipotese_diagnostica, resumo_conduta,
                    medicamento_administrado, posologia, horario_medicacao,
                    observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                atendimento.id, conduta.hipotese_diagnostica,
                conduta.resumo_conduta, conduta.medicamento_administrado,
                conduta.posologia, conduta.horario_medicacao, conduta.observacoes
            ))

        conn.commit()
    except (ValueError, ConnectionError, sqlite3.Error) as e:
        print(f"Erro ao atualizar atendimento ({atendimento.id}): {e}")
        if conn: conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def delete_atendimento(atendimento_id: int):
    """Apaga um atendimento do banco de dados pelo seu ID."""
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM atendimentos WHERE id = ?", (atendimento_id,))
        conn.commit()
    except (ValueError, ConnectionError, sqlite3.Error) as e:
        print(f"Erro ao deletar atendimento ({atendimento_id}): {e}")
        if conn: conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def export_to_csv(filepath, start_date=None, end_date=None, week_iso=None):
    """Exporta os dados de atendimentos e condutas para um arquivo CSV."""
    conn = None
    try:
        conn = _get_connection()
        conn.row_factory = sqlite3.Row # Facilita acesso por nome de coluna
        cursor = conn.cursor()

        query_params = []
        query_str = "SELECT * FROM atendimentos WHERE 1=1"

        if start_date and end_date:
            # Se for 'hoje', start e end são iguais
            if start_date == end_date:
                 query_str += " AND data_atendimento = ?"
                 query_params.append(start_date)
            else:
                query_str += " AND data_atendimento BETWEEN ? AND ?"
                query_params.extend([start_date, end_date])
        elif week_iso:
            query_str += " AND semana_iso = ?"
            query_params.append(week_iso)
        # else: # Se nenhum filtro for aplicado, exporta tudo? Ou default para hoje?
        #     # Default para hoje se nenhum outro filtro for dado
        #     query_str += " AND data_atendimento = ?"
        #     query_params.append(datetime.now().strftime("%Y-%m-%d"))

        query_str += " ORDER BY data_atendimento, hora_atendimento" # Ordena para o CSV

        cursor.execute(query_str, query_params)
        atendimentos = cursor.fetchall()

        # Define os cabeçalhos do CSV (incluindo novos campos e excluindo antigos)
        fieldnames = [
            "id_atendimento", "badge_number", "nome", "login", "gestor", "turno", "setor", "processo", "tenure",
            "qp_sintoma", "qp_regiao", # Novos campos QP
            "hqa", "tax", "pa_sistolica", "pa_diastolica", "fc", "sat", "doencas_preexistentes",
            "alergias", "medicamentos_em_uso", "observacoes_atendimento", "data_atendimento",
            "hora_atendimento", "semana_iso",
            # Cabeçalhos Conduta (sem conduta_adotada)
            "id_conduta", "hipotese_diagnostica", "resumo_conduta", "medicamento_administrado",
            "posologia", "horario_medicacao", "observacoes_conduta",
             # Cabeçalhos QS (One-Hot Encoding)
            *[f"qs_sintoma_{s.replace('/', '_').replace(' ', '_')}" for s in SINTOMAS if s != 'N/A'],
            *[f"qs_regiao_{r.replace('/', '_').replace(' ', '_')}" for r in REGIOES if r not in ['N/A', 'Menstrual']]
        ]
        # REGIOES e SINTOMAS precisam ser importados ou definidos aqui
        from gui.constants import SINTOMAS, REGIOES # Importa aqui

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore') # Ignora colunas extras
            writer.writeheader()

            for atendimento_row in atendimentos:
                atendimento_dict = dict(atendimento_row) # Converte Row para dict
                atendimento_id = atendimento_dict.get("id")

                # Processa Queixas Secundárias
                qs_sintomas_list = []
                qs_regioes_list = []
                try: qs_sintomas_list = json.loads(atendimento_dict.get("qs_sintomas", "[]"))
                except json.JSONDecodeError: pass
                try: qs_regioes_list = json.loads(atendimento_dict.get("qs_regioes", "[]"))
                except json.JSONDecodeError: pass

                # Prepara dados base da linha do CSV
                csv_row_base = {
                    "id_atendimento": atendimento_id,
                    "badge_number": atendimento_dict.get("badge_number"),
                    "nome": atendimento_dict.get("nome"),
                    "login": atendimento_dict.get("login"),
                    "gestor": atendimento_dict.get("gestor"),
                    "turno": atendimento_dict.get("turno"),
                    "setor": atendimento_dict.get("setor"),
                    "processo": atendimento_dict.get("processo"),
                    "tenure": atendimento_dict.get("tenure"),
                    "qp_sintoma": atendimento_dict.get("qp_sintoma"),
                    "qp_regiao": atendimento_dict.get("qp_regiao"),
                    "hqa": atendimento_dict.get("hqa"),
                    "tax": atendimento_dict.get("tax"),
                    "pa_sistolica": atendimento_dict.get("pa_sistolica"),
                    "pa_diastolica": atendimento_dict.get("pa_diastolica"),
                    "fc": atendimento_dict.get("fc"),
                    "sat": atendimento_dict.get("sat"),
                    "doencas_preexistentes": atendimento_dict.get("doencas_preexistentes"),
                    "alergias": atendimento_dict.get("alergias"),
                    "medicamentos_em_uso": atendimento_dict.get("medicamentos_em_uso"),
                    "observacoes_atendimento": atendimento_dict.get("observacoes"), # Renomeado para evitar conflito
                    "data_atendimento": atendimento_dict.get("data_atendimento"),
                    "hora_atendimento": atendimento_dict.get("hora_atendimento"),
                    "semana_iso": atendimento_dict.get("semana_iso"),
                }
                 # Adiciona One-Hot Encoding para QS
                for s in SINTOMAS:
                     if s != 'N/A':
                         col_name = f"qs_sintoma_{s.replace('/', '_').replace(' ', '_')}"
                         csv_row_base[col_name] = 1 if s in qs_sintomas_list else 0
                for r in REGIOES:
                     if r not in ['N/A', 'Menstrual']:
                         col_name = f"qs_regiao_{r.replace('/', '_').replace(' ', '_')}"
                         csv_row_base[col_name] = 1 if r in qs_regioes_list else 0


                # Busca condutas associadas
                cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
                condutas = cursor.fetchall()

                if not condutas:
                    # Escreve a linha do atendimento sem dados de conduta
                    writer.writerow(csv_row_base)
                else:
                    # Escreve uma linha para cada conduta, repetindo os dados do atendimento
                    for conduta_row in condutas:
                        conduta_dict = dict(conduta_row)
                        csv_row_full = csv_row_base.copy() # Copia dados base
                        csv_row_full.update({
                            "id_conduta": conduta_dict.get("id"),
                            "hipotese_diagnostica": conduta_dict.get("hipotese_diagnostica"),
                            "resumo_conduta": conduta_dict.get("resumo_conduta"),
                            "medicamento_administrado": conduta_dict.get("medicamento_administrado"),
                            "posologia": conduta_dict.get("posologia"),
                            "horario_medicacao": conduta_dict.get("horario_medicacao"),
                            "observacoes_conduta": conduta_dict.get("observacoes"), # Renomeado
                        })
                        writer.writerow(csv_row_full)
    except (ValueError, ConnectionError, sqlite3.Error, IOError) as e:
         print(f"Erro ao exportar para CSV ({filepath}): {e}")
         raise # Re-levanta para a GUI mostrar o erro
    finally:
        if conn:
            conn.close()

# Inicializa o caminho do DB ao importar o módulo (tentativa)
# Isso pode ser movido para main.py para mais controle
# import config_manager
# initial_path = config_manager.load_db_path()
# if initial_path:
#     set_db_path(initial_path)
# else:
#     print("Caminho do banco de dados não encontrado na configuração inicial.")

