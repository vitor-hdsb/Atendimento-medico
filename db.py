"""
db.py
-----
Módulo para gerenciamento do banco de dados SQLite.
"""
import sqlite3
from datetime import datetime, timedelta
import csv
from models import Atendimento, Conduta
import os
import json # Importa json
# --- CORREÇÃO ERRO EXPORTAÇÃO ---
# Importa SINTOMAS e REGIOES para a função de exportar CSV
from gui.constants import SINTOMAS, REGIOES
# --- FIM CORREÇÃO ---


# Variável global para armazenar o caminho do DB
_db_path = None

def set_db_path(filepath):
    """Define o caminho do banco de dados a ser usado."""
    global _db_path
    if filepath and os.path.exists(os.path.dirname(filepath)):
        _db_path = filepath
        return True
    return False

def _get_connection():
    """Retorna uma conexão com o banco de dados usando o caminho definido."""
    if _db_path is None:
        raise ValueError("Caminho do banco de dados não foi definido. Chame set_db_path() primeiro.")
    try:
        conn = sqlite3.connect(_db_path)
        conn.execute("PRAGMA journal_mode = WAL;")
        # Habilita chaves estrangeiras
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.OperationalError as e:
        print(f"Erro ao conectar ao DB em {_db_path}: {e}")
        return None

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return False
        cursor = conn.cursor()

        # Tabela para os atendimentos
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
                -- MELHORIA: Adiciona tipo_atendimento
                tipo_atendimento TEXT,
                -- Campos de Queixa Atualizados
                qp_sintoma TEXT,
                qp_regiao TEXT,
                qs_sintomas TEXT,
                qs_regioes TEXT,
                -- Fim Campos de Queixa
                hqa TEXT,
                tax TEXT,
                pa_sistolica TEXT,
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
        
        # --- Verificação de Colunas Faltando (Migração Simples) ---
        colunas_atendimento = [col[1] for col in cursor.execute("PRAGMA table_info(atendimentos)").fetchall()]
        colunas_necessarias = ['tipo_atendimento', 'qp_sintoma', 'qp_regiao', 'qs_sintomas', 'qs_regioes']
        
        for col in colunas_necessarias:
            if col not in colunas_atendimento:
                try:
                    cursor.execute(f"ALTER TABLE atendimentos ADD COLUMN {col} TEXT DEFAULT 'N/A'")
                    print(f"Coluna '{col}' adicionada à tabela 'atendimentos'.")
                except sqlite3.OperationalError as e:
                    print(f"Aviso: Não foi possível adicionar a coluna {col}: {e}")

        # Remove coluna antiga 'queixas_principais' se existir e novas colunas existirem
        if 'queixas_principais' in colunas_atendimento and 'qp_sintoma' in colunas_atendimento:
             try:
                 # Renomeia para backup, em vez de apagar
                 cursor.execute("ALTER TABLE atendimentos RENAME COLUMN queixas_principais TO queixas_principais_old")
                 print("Coluna 'queixas_principais' antiga renomeada para 'queixas_principais_old'.")
             except sqlite3.OperationalError as e:
                 print(f"Aviso: Não foi possível renomear a coluna 'queixas_principais': {e}")
        # --- Fim Migração Simples ---


        # Tabela para as condutas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS condutas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atendimento_id INTEGER NOT NULL,
                hipotese_diagnostica TEXT,
                -- conduta_adotada TEXT, -- Removido
                resumo_conduta TEXT,
                medicamento_administrado TEXT,
                posologia TEXT,
                horario_medicacao TEXT,
                observacoes TEXT,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos (id) ON DELETE CASCADE
            )
        """)
        
        # Verifica coluna 'conduta_adotada' e remove se existir
        colunas_conduta = [col[1] for col in cursor.execute("PRAGMA table_info(condutas)").fetchall()]
        if 'conduta_adotada' in colunas_conduta:
            try:
                # Renomeia para backup
                cursor.execute("ALTER TABLE condutas RENAME COLUMN conduta_adotada TO conduta_adotada_old")
                print("Coluna 'conduta_adotada_old' antiga renomeada.")
            except sqlite3.OperationalError as e:
                 print(f"Aviso: Não foi possível renomear a coluna 'conduta_adotada': {e}")


        conn.commit()
        return True
    except Exception as e:
        print(f"Erro em init_db: {e}")
        return False
    finally:
        if conn:
            conn.close()

def save_atendimento(atendimento: Atendimento):
    """Salva um novo atendimento e suas condutas no banco de dados."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return None
        cursor = conn.cursor()

        # Insere o atendimento principal
        cursor.execute("""
            INSERT INTO atendimentos (
                badge_number, nome, login, gestor, turno, setor, processo, tenure,
                tipo_atendimento, qp_sintoma, qp_regiao, qs_sintomas, qs_regioes,
                hqa, tax, pa_sistolica, pa_diastolica, fc, sat, doencas_preexistentes,
                alergias, medicamentos_em_uso, observacoes, data_atendimento,
                hora_atendimento, semana_iso
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            atendimento.badge_number, atendimento.nome, atendimento.login, atendimento.gestor,
            atendimento.turno, atendimento.setor, atendimento.processo, atendimento.tenure,
            # --- MELHORIA: Salva tipo_atendimento e novas queixas ---
            atendimento.tipo_atendimento, atendimento.qp_sintoma, atendimento.qp_regiao,
            atendimento.qs_sintomas, atendimento.qs_regioes,
            # --- Fim ---
            atendimento.hqa, atendimento.tax, atendimento.pa_sistolica,
            atendimento.pa_diastolica, atendimento.fc, atendimento.sat, atendimento.doencas_preexistentes,
            atendimento.alergias, atendimento.medicamentos_em_uso, atendimento.observacoes,
            atendimento.data_atendimento, atendimento.hora_atendimento, atendimento.semana_iso
        ))
        atendimento_id = cursor.lastrowid

        # Insere todas as condutas associadas
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
    except Exception as e:
        print(f"Erro ao salvar atendimento: {e}")
        if conn: conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def get_atendimento_by_id(atendimento_id):
    """Busca um atendimento e suas condutas pelo ID."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return None
        # Configura a conexão para retornar dicionários
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Busca o atendimento
        cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,))
        atendimento_data = cursor.fetchone()
        if not atendimento_data:
            return None

        # Converte sqlite3.Row para dict para passar como kwargs
        atendimento_dict = dict(atendimento_data)

        # Remove 'queixas_principais_old' se existir
        atendimento_dict.pop('queixas_principais_old', None)
        
        atendimento = Atendimento(**atendimento_dict)

        # Busca as condutas associadas
        cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
        condutas_data = cursor.fetchall()
        
        atendimento.condutas = []
        for conduta_row in condutas_data:
            conduta_dict = dict(conduta_row)
            # Remove 'conduta_adotada_old' se existir
            conduta_dict.pop('conduta_adotada_old', None)
            atendimento.condutas.append(Conduta(**conduta_dict))

        return atendimento
    except Exception as e:
        print(f"Erro em get_atendimento_by_id: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_last_atendimento_by_badge(badge_number):
    """Busca os dados de identificação do último atendimento de um paciente."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return None
        conn.row_factory = sqlite3.Row # Retorna como dict
        cursor = conn.cursor()
        
        # Seleciona apenas os campos de identificação
        cursor.execute("""
            SELECT nome, login, gestor, turno, setor, processo, tenure
            FROM atendimentos
            WHERE badge_number = ?
            ORDER BY data_atendimento DESC, hora_atendimento DESC
            LIMIT 1
        """, (badge_number,))
        
        data = cursor.fetchone()
        if data:
            return dict(data) # Retorna um dicionário
        return None
    except Exception as e:
        print(f"Erro em get_last_atendimento_by_badge: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_atendimentos_by_badge(badge_number=None, days_ago=15):
    """Busca atendimentos recentes para um paciente por período em dias."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        
        date_limit = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        query_params = [date_limit]
        # --- MELHORIA: Adiciona qp_sintoma e resumo_conduta (via subquery) ---
        query_str = """
            SELECT
                a.id, a.badge_number, a.nome, a.login,
                a.data_atendimento, a.hora_atendimento,
                a.qp_sintoma,
                (SELECT c.resumo_conduta FROM condutas c
                 WHERE c.atendimento_id = a.id LIMIT 1) as resumo_conduta
            FROM atendimentos a
            WHERE a.data_atendimento >= ?
        """
        # --- Fim Melhoria ---
        
        if badge_number is not None:
            query_str += " AND a.badge_number = ?"
            query_params.append(badge_number)
        
        query_str += " ORDER BY a.data_atendimento DESC, a.hora_atendimento DESC"
        
        cursor.execute(query_str, query_params)
        
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"Erro em get_atendimentos_by_badge: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_atendimentos_by_datetime_range(start_datetime_str, end_datetime_str, badge_number=None):
    """Busca atendimentos dentro de um intervalo de data e hora."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        
        query_params = [start_datetime_str, end_datetime_str]
        # --- MELHORIA: Adiciona qp_sintoma e resumo_conduta (via subquery) ---
        query_str = """
            SELECT
                a.id, a.badge_number, a.nome, a.login,
                a.data_atendimento, a.hora_atendimento,
                a.qp_sintoma,
                (SELECT c.resumo_conduta FROM condutas c
                 WHERE c.atendimento_id = a.id LIMIT 1) as resumo_conduta
            FROM atendimentos a
            WHERE (a.data_atendimento || ' ' || a.hora_atendimento) BETWEEN ? AND ?
        """
        # --- Fim Melhoria ---
        
        if badge_number is not None:
            query_str += " AND a.badge_number = ?"
            query_params.append(badge_number)
        
        query_str += " ORDER BY a.data_atendimento DESC, a.hora_atendimento DESC"
        
        cursor.execute(query_str, query_params)
        
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"Erro em get_atendimentos_by_datetime_range: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_atendimento(atendimento: Atendimento):
    """Atualiza um atendimento existente no banco de dados."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return
        cursor = conn.cursor()

        # Atualiza o atendimento principal
        cursor.execute("""
            UPDATE atendimentos SET
                nome = ?, login = ?, gestor = ?, turno = ?, setor = ?, processo = ?,
                tenure = ?, 
                tipo_atendimento = ?, qp_sintoma = ?, qp_regiao = ?, qs_sintomas = ?, qs_regioes = ?,
                hqa = ?, tax = ?, pa_sistolica = ?,
                pa_diastolica = ?, fc = ?, sat = ?, doencas_preexistentes = ?, alergias = ?,
                medicamentos_em_uso = ?, observacoes = ?
            WHERE id = ?
        """, (
            atendimento.nome, atendimento.login, atendimento.gestor, atendimento.turno,
            atendimento.setor, atendimento.processo, atendimento.tenure,
            # --- MELHORIA: Salva tipo_atendimento e novas queixas ---
            atendimento.tipo_atendimento, atendimento.qp_sintoma, atendimento.qp_regiao,
            atendimento.qs_sintomas, atendimento.qs_regioes,
            # --- Fim ---
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
    except Exception as e:
        print(f"Erro ao atualizar atendimento: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            conn.close()

def delete_atendimento(atendimento_id: int):
    """Apaga um atendimento do banco de dados pelo seu ID."""
    conn = None
    try:
        conn = _get_connection()
        if conn is None: return
        cursor = conn.cursor()
        cursor.execute("DELETE FROM atendimentos WHERE id = ?", (atendimento_id,))
        conn.commit()
    except Exception as e:
        print(f"Erro ao deletar atendimento: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            conn.close()

def export_to_csv(filepath, start_date=None, end_date=None, week_iso=None):
    """Exporta os dados de atendimentos e condutas para um arquivo CSV."""
    conn = None
    
    # --- CORREÇÃO ERRO EXPORTAÇÃO: Garante que SINTOMAS e REGIOES estão disponíveis ---
    # (Eles já estão importados no topo do arquivo)
    # --- FIM CORREÇÃO ---
    
    try:
        conn = _get_connection()
        if conn is None: return
        conn.row_factory = sqlite3.Row # Facilita acesso por nome de coluna
        cursor = conn.cursor()

        query_params = []
        query_str = "SELECT * FROM atendimentos WHERE 1=1"

        if start_date and end_date:
            query_str += " AND data_atendimento BETWEEN ? AND ?"
            query_params.extend([start_date, end_date])
        elif week_iso:
            query_str += " AND semana_iso = ?"
            query_params.append(week_iso)
        # Se nenhum filtro, exporta TUDO (removido filtro de "Dia atual"
        # else: # Dia atual
        #     query_str += " AND data_atendimento = ?"
        #     query_params.append(datetime.now().strftime("%Y-%m-%d"))

        cursor.execute(query_str, query_params)
        atendimentos = cursor.fetchall() # Lista de sqlite3.Row (dicts)

        fieldnames_atendimento = [
            "id", "badge_number", "nome", "login", "gestor", "turno", "setor", "processo", "tenure",
            "tipo_atendimento", "qp_sintoma", "qp_regiao",
            "hqa", "tax", "pa_sistolica", "pa_diastolica", "fc", "sat",
            "doencas_preexistentes", "alergias", "medicamentos_em_uso", "observacoes",
            "data_atendimento", "hora_atendimento", "semana_iso"
        ]
        
        # Campos de Queixa Secundária (One-Hot)
        # Remove "Absorvente" e "Trabalho em altura" da exportação One-Hot? Não, deixa
        qs_sintoma_headers = [f"qs_sintoma_{s.replace(' ', '_').replace('/', '_')}" for s in SINTOMAS]
        qs_regiao_headers = [f"qs_regiao_{r.replace(' ', '_').replace('/', '_')}" for r in REGIOES]
        
        fieldnames_conduta = [
            "conduta_id", "hipotese_diagnostica",
            "resumo_conduta", "medicamento_administrado",
            "posologia", "horario_medicacao", "observacoes_conduta"
        ]
        
        # Junta todos os cabeçalhos
        fieldnames = fieldnames_atendimento + qs_sintoma_headers + qs_regiao_headers + fieldnames_conduta

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for atendimento_row in atendimentos:
                atendimento_dict = dict(atendimento_row)
                atendimento_id = atendimento_dict.get("id")

                # --- Processa One-Hot para Queixas Secundárias ---
                try:
                    qs_sintomas_list = json.loads(atendimento_dict.get('qs_sintomas', '[]'))
                except: qs_sintomas_list = []
                try:
                    qs_regioes_list = json.loads(atendimento_dict.get('qs_regioes', '[]'))
                except: qs_regioes_list = []

                for s in SINTOMAS:
                    col_name = f"qs_sintoma_{s.replace(' ', '_').replace('/', '_')}"
                    atendimento_dict[col_name] = 1 if s in qs_sintomas_list else 0
                for r in REGIOES:
                    col_name = f"qs_regiao_{r.replace(' ', '_').replace('/', '_')}"
                    atendimento_dict[col_name] = 1 if r in qs_regioes_list else 0
                # --- Fim One-Hot ---

                # Busca condutas para este atendimento
                cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
                condutas = cursor.fetchall()
                
                if not condutas:
                    # Escreve o atendimento principal mesmo sem conduta
                    writer.writerow(atendimento_dict)
                else:
                    # Escreve uma linha para CADA conduta
                    for conduta_row in condutas:
                        conduta_dict = dict(conduta_row)
                        # Renomeia chaves de conduta para evitar conflitos
                        conduta_renamed = {
                            "conduta_id": conduta_dict.get("id"),
                            "hipotese_diagnostica": conduta_dict.get("hipotese_diagnostica"),
                            "resumo_conduta": conduta_dict.get("resumo_conduta"),
                            "medicamento_administrado": conduta_dict.get("medicamento_administrado"),
                            "posologia": conduta_dict.get("posologia"),
                            "horario_medicacao": conduta_dict.get("horario_medicacao"),
                            "observacoes_conduta": conduta_dict.get("observacoes")
                        }
                        # Combina dict do atendimento com o da conduta e escreve
                        combined_row = {**atendimento_dict, **conduta_renamed}
                        writer.writerow(combined_row)
    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

