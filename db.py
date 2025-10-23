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
import json # Importado para lidar com listas de queixas
from gui.constants import SINTOMAS, REGIOES # Importa as listas de constantes

# Define o nome do arquivo do banco de dados
DB_FILE = "atendimentos.db"

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        # Configura o banco de dados para o modo WAL para permitir concorrência
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()

        # Tabela para os atendimentos (MODIFICADA)
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
                
                qp_sintoma TEXT,
                qp_regiao TEXT,
                qs_sintomas TEXT,
                qs_regioes TEXT,
                
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

        # Tabela para as condutas, com chave estrangeira para atendimentos (MODIFICADA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS condutas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                atendimento_id INTEGER NOT NULL,
                hipotese_diagnostica TEXT,
                resumo_conduta TEXT,
                medicamento_administrado TEXT,
                posologia TEXT,
                horario_medicacao TEXT,
                observacoes TEXT,
                FOREIGN KEY (atendimento_id) REFERENCES atendimentos (id) ON DELETE CASCADE
            )
        """)
        
        # --- Verificação de colunas antigas (Migração Simples) ---
        # Tenta remover 'queixas_principais' de 'atendimentos' se existir
        try:
            cursor.execute("ALTER TABLE atendimentos DROP COLUMN queixas_principais")
            print("Coluna 'queixas_principais' removida de 'atendimentos'.")
        except sqlite3.OperationalError:
            pass # Coluna não existe ou erro (ignora)

        # Tenta remover 'conduta_adotada' de 'condutas' se existir
        try:
            cursor.execute("ALTER TABLE condutas DROP COLUMN conduta_adotada")
            print("Coluna 'conduta_adotada' removida de 'condutas'.")
        except sqlite3.OperationalError:
            pass # Coluna não existe ou erro (ignora)
        
        # Tenta adicionar novas colunas de queixa se não existirem
        try:
            cursor.execute("ALTER TABLE atendimentos ADD COLUMN qp_sintoma TEXT")
            cursor.execute("ALTER TABLE atendimentos ADD COLUMN qp_regiao TEXT")
            cursor.execute("ALTER TABLE atendimentos ADD COLUMN qs_sintomas TEXT")
            cursor.execute("ALTER TABLE atendimentos ADD COLUMN qs_regioes TEXT")
            print("Novas colunas de queixa adicionadas a 'atendimentos'.")
        except sqlite3.OperationalError:
            pass # Colunas já existem (ignora)

        conn.commit()
    finally:
        if conn:
            conn.close()

def save_atendimento(atendimento: Atendimento):
    """Salva um novo atendimento e suas condutas no banco de dados."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()

        # Insere o atendimento principal (MODIFICADO)
        cursor.execute("""
            INSERT INTO atendimentos (
                badge_number, nome, login, gestor, turno, setor, processo, tenure,
                qp_sintoma, qp_regiao, qs_sintomas, qs_regioes,
                hqa, tax, pa_sistolica, pa_diastolica, fc, sat, doencas_preexistentes,
                alergias, medicamentos_em_uso, observacoes, data_atendimento,
                hora_atendimento, semana_iso
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            atendimento.badge_number, atendimento.nome, atendimento.login, atendimento.gestor,
            atendimento.turno, atendimento.setor, atendimento.processo, atendimento.tenure,
            atendimento.qp_sintoma, atendimento.qp_regiao, atendimento.qs_sintomas, atendimento.qs_regioes,
            atendimento.hqa, atendimento.tax, atendimento.pa_sistolica,
            atendimento.pa_diastolica, atendimento.fc, atendimento.sat, atendimento.doencas_preexistentes,
            atendimento.alergias, atendimento.medicamentos_em_uso, atendimento.observacoes,
            atendimento.data_atendimento, atendimento.hora_atendimento, atendimento.semana_iso
        ))
        atendimento_id = cursor.lastrowid

        # Insere todas as condutas associadas (MODIFICADO)
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
    finally:
        if conn:
            conn.close()


def get_atendimento_by_id(atendimento_id):
    """Busca um atendimento e suas condutas pelo ID."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()

        # Busca o atendimento (MODIFICADO)
        cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,))
        atendimento_data = cursor.fetchone()
        if not atendimento_data:
            return None

        atendimento = Atendimento(
            id=atendimento_data[0],
            badge_number=atendimento_data[1],
            nome=atendimento_data[2],
            login=atendimento_data[3],
            gestor=atendimento_data[4],
            turno=atendimento_data[5],
            setor=atendimento_data[6],
            processo=atendimento_data[7],
            tenure=atendimento_data[8],
            qp_sintoma=atendimento_data[9],
            qp_regiao=atendimento_data[10],
            qs_sintomas=atendimento_data[11],
            qs_regioes=atendimento_data[12],
            hqa=atendimento_data[13],
            tax=atendimento_data[14],
            pa_sistolica=atendimento_data[15],
            pa_diastolica=atendimento_data[16],
            fc=atendimento_data[17],
            sat=atendimento_data[18],
            doencas_preexistentes=atendimento_data[19],
            alergias=atendimento_data[20],
            medicamentos_em_uso=atendimento_data[21],
            observacoes=atendimento_data[22],
            data_atendimento=atendimento_data[23],
            hora_atendimento=atendimento_data[24],
            semana_iso=atendimento_data[25]
        )

        # Busca as condutas associadas (MODIFICADO)
        cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
        condutas_data = cursor.fetchall()
        atendimento.condutas = [
            Conduta(
                hipotese_diagnostica=c[2],
                resumo_conduta=c[3],
                medicamento_administrado=c[4],
                posologia=c[5],
                horario_medicacao=c[6],
                observacoes=c[7]
            ) for c in condutas_data
        ]

        return atendimento
    finally:
        if conn:
            conn.close()

def get_last_atendimento_by_badge(badge_number):
    """Busca o último atendimento de um paciente pelo número do crachá."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()
        # Seleciona apenas campos de identificação (não afetado pelas mudanças)
        cursor.execute("SELECT id, badge_number, nome, login, gestor, turno, setor, processo, tenure FROM atendimentos WHERE badge_number = ? ORDER BY data_atendimento DESC, hora_atendimento DESC LIMIT 1", (badge_number,))
        atendimento_data = cursor.fetchone()
        if atendimento_data:
            return Atendimento(
                id=atendimento_data[0],
                badge_number=atendimento_data[1],
                nome=atendimento_data[2],
                login=atendimento_data[3],
                gestor=atendimento_data[4],
                turno=atendimento_data[5],
                setor=atendimento_data[6],
                processo=atendimento_data[7],
                tenure=atendimento_data[8]
            )
        return None
    finally:
        if conn:
            conn.close()


def get_atendimentos_by_badge(badge_number=None, days_ago=15):
    """
    Busca atendimentos recentes para um paciente por período em dias.
    (Não afetado pelas mudanças)
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode = WAL;")
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
    finally:
        if conn:
            conn.close()

def get_atendimentos_by_datetime_range(start_datetime_str, end_datetime_str, badge_number=None):
    """
    Busca atendimentos dentro de um intervalo de data e hora.
    (Não afetado pelas mudanças)
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
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
    finally:
        if conn:
            conn.close()

def update_atendimento(atendimento: Atendimento):
    """Atualiza um atendimento existente no banco de dados."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()

        # Atualiza o atendimento principal (MODIFICADO)
        cursor.execute("""
            UPDATE atendimentos SET
                nome = ?, login = ?, gestor = ?, turno = ?, setor = ?, processo = ?,
                tenure = ?, 
                qp_sintoma = ?, qp_regiao = ?, qs_sintomas = ?, qs_regioes = ?,
                hqa = ?, tax = ?, pa_sistolica = ?,
                pa_diastolica = ?, fc = ?, sat = ?, doencas_preexistentes = ?, alergias = ?,
                medicamentos_em_uso = ?, observacoes = ?
            WHERE id = ?
        """, (
            atendimento.nome, atendimento.login, atendimento.gestor, atendimento.turno,
            atendimento.setor, atendimento.processo, atendimento.tenure,
            atendimento.qp_sintoma, atendimento.qp_regiao, atendimento.qs_sintomas, atendimento.qs_regioes,
            atendimento.hqa, atendimento.tax, atendimento.pa_sistolica,
            atendimento.pa_diastolica, atendimento.fc, atendimento.sat, atendimento.doencas_preexistentes,
            atendimento.alergias, atendimento.medicamentos_em_uso,
            atendimento.observacoes, atendimento.id
        ))

        # Remove as condutas antigas e insere as novas (MODIFICADO)
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
    finally:
        if conn:
            conn.close()

def delete_atendimento(atendimento_id: int):
    """Apaga um atendimento do banco de dados pelo seu ID."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()
        # A exclusão em cascata (ON DELETE CASCADE) cuidará da tabela de condutas
        cursor.execute("DELETE FROM atendimentos WHERE id = ?", (atendimento_id,))
        conn.commit()
    finally:
        if conn:
            conn.close()

def export_to_csv(filepath, start_date=None, end_date=None, week_iso=None):
    """Exporta os dados de atendimentos e condutas para um arquivo CSV."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
        conn.execute("PRAGMA journal_mode = WAL;")
        cursor = conn.cursor()

        query_params = []
        query_str = "SELECT * FROM atendimentos WHERE 1=1"

        if start_date and end_date:
            query_str += " AND data_atendimento BETWEEN ? AND ?"
            query_params.extend([start_date, end_date])
        elif week_iso:
            query_str += " AND semana_iso = ?"
            query_params.append(week_iso)
        elif start_date: # Lógica para "hoje"
             query_str += " AND data_atendimento = ?"
             query_params.append(start_date)
        # else: exporta tudo

        cursor.execute(query_str, query_params)
        atendimentos = cursor.fetchall()

        # --- Geração Dinâmica de Cabeçalhos ---
        
        # 1. Campos Padrão de Atendimento
        fieldnames_atendimento = [
            "id_atendimento", "badge_number", "nome", "login", "gestor", "turno", "setor", "processo", "tenure",
            "qp_sintoma", "qp_regiao", # Novas queixas principais
            "hqa", "tax", "pa_sistolica", "pa_diastolica", "fc", "sat", "doencas_preexistentes",
            "alergias", "medicamentos_em_uso", "observacoes_atendimento", "data_atendimento",
            "hora_atendimento", "semana_iso"
        ]
        
        # 2. Campos One-Hot para QS_Sintomas
        # Remove "N/A" da lista de colunas
        sintomas_cols = [s for s in SINTOMAS if s != "N/A"]
        fieldnames_qs_sintomas = [f"qs_sintoma_{s.replace(' ', '_').replace('/', '_')}" for s in sintomas_cols]
        
        # 3. Campos One-Hot para QS_Regioes
        # Remove "N/A" da lista de colunas
        regioes_cols = [r for r in REGIOES if r != "N/A"]
        fieldnames_qs_regioes = [f"qs_regiao_{r.replace(' ', '_').replace('/', '_')}" for r in regioes_cols]

        # 4. Campos Padrão de Conduta
        fieldnames_conduta = [
            "id_conduta", "hipotese_diagnostica",
            "resumo_conduta", "medicamento_administrado",
            "posologia", "horario_medicacao", "observacoes_conduta"
        ]
        
        # 5. Combina todos os cabeçalhos
        fieldnames = fieldnames_atendimento + fieldnames_qs_sintomas + fieldnames_qs_regioes + fieldnames_conduta
        # --- Fim da Geração de Cabeçalhos ---


        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for atendimento_row in atendimentos:
                # 1. Prepara a linha base do atendimento
                row_base = {}
                
                # Mapeia colunas de atendimento
                for col in fieldnames_atendimento:
                    if col == "id_atendimento":
                        row_base[col] = atendimento_row["id"]
                    elif col == "observacoes_atendimento":
                         row_base[col] = atendimento_row["observacoes"]
                    elif col in atendimento_row.keys():
                        row_base[col] = atendimento_row[col]
                
                # 2. Processa QS_Sintomas (One-Hot)
                try:
                    sintomas_salvos = json.loads(atendimento_row["qs_sintomas"] or "[]")
                except json.JSONDecodeError:
                    sintomas_salvos = []
                
                for s in sintomas_cols:
                    col_name = f"qs_sintoma_{s.replace(' ', '_').replace('/', '_')}"
                    row_base[col_name] = 1 if s in sintomas_salvos else 0

                # 3. Processa QS_Regioes (One-Hot)
                try:
                    regioes_salvas = json.loads(atendimento_row["qs_regioes"] or "[]")
                except json.JSONDecodeError:
                    regioes_salvas = []

                for r in regioes_cols:
                    col_name = f"qs_regiao_{r.replace(' ', '_').replace('/', '_')}"
                    row_base[col_name] = 1 if r in regioes_salvas else 0

                # 4. Busca e processa condutas
                atendimento_id = atendimento_row["id"]
                cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
                condutas = cursor.fetchall()
                
                if not condutas:
                    # Escreve o atendimento principal mesmo sem conduta
                    writer.writerow(row_base)
                else:
                    for conduta_row in condutas:
                        row_com_conduta = row_base.copy()
                        row_com_conduta["id_conduta"] = conduta_row["id"]
                        row_com_conduta["hipotese_diagnostica"] = conduta_row["hipotese_diagnostica"]
                        row_com_conduta["resumo_conduta"] = conduta_row["resumo_conduta"]
                        row_com_conduta["medicamento_administrado"] = conduta_row["medicamento_administrado"]
                        row_com_conduta["posologia"] = conduta_row["posologia"]
                        row_com_conduta["horario_medicacao"] = conduta_row["horario_medicacao"]
                        row_com_conduta["observacoes_conduta"] = conduta_row["observacoes"]
                        
                        writer.writerow(row_com_conduta)
    finally:
        if conn:
            conn.close()
