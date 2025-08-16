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

# Define o nome do arquivo do banco de dados
DB_FILE = "atendimentos.db"

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = sqlite3.connect(DB_FILE)
    # Configura o banco de dados para o modo WAL para permitir concorrência
    conn.execute("PRAGMA journal_mode = WAL;")
    cursor = conn.cursor()

    # Tabela para os atendimentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_number INTEGER NOT NULL,
            nome TEXT,
            login TEXT,
            gestor TEXT,
            turno TEXT,
            setor TEXT,
            processo TEXT,
            tenure TEXT,
            queixa_principal TEXT,
            hqa TEXT,
            tax TEXT,
            pa TEXT,
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

    # Tabela para as condutas, com chave estrangeira para atendimentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS condutas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atendimento_id INTEGER NOT NULL,
            hipotese_diagnostica TEXT,
            conduta_adotada TEXT,
            resumo_conduta TEXT,
            medicamento_administrado TEXT,
            medicamento TEXT,
            posologia TEXT,
            horario_medicacao TEXT,
            observacoes TEXT,
            FOREIGN KEY (atendimento_id) REFERENCES atendimentos (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def save_atendimento(atendimento: Atendimento):
    """Salva um novo atendimento e suas condutas no banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode = WAL;")
    cursor = conn.cursor()

    # Insere o atendimento principal
    cursor.execute("""
        INSERT INTO atendimentos (
            badge_number, nome, login, gestor, turno, setor, processo, tenure,
            queixa_principal, hqa, tax, pa, fc, sat, doencas_preexistentes,
            alergias, medicamentos_em_uso, observacoes, data_atendimento,
            hora_atendimento, semana_iso
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        atendimento.badge_number, atendimento.nome, atendimento.login, atendimento.gestor,
        atendimento.turno, atendimento.setor, atendimento.processo, atendimento.tenure,
        atendimento.queixa_principal, atendimento.hqa, atendimento.tax, atendimento.pa,
        atendimento.fc, atendimento.sat, atendimento.doencas_preexistentes,
        atendimento.alergias, atendimento.medicamentos_em_uso, atendimento.observacoes,
        atendimento.data_atendimento, atendimento.hora_atendimento, atendimento.semana_iso
    ))
    atendimento_id = cursor.lastrowid

    # Insere todas as condutas associadas
    for conduta in atendimento.condutas:
        cursor.execute("""
            INSERT INTO condutas (
                atendimento_id, hipotese_diagnostica, conduta_adotada, resumo_conduta,
                medicamento_administrado, medicamento, posologia, horario_medicacao,
                observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            atendimento_id, conduta.hipotese_diagnostica, conduta.conduta_adotada,
            conduta.resumo_conduta, conduta.medicamento_administrado, conduta.medicamento,
            conduta.posologia, conduta.horario_medicacao, conduta.observacoes
        ))

    conn.commit()
    conn.close()
    return atendimento_id

def get_atendimento_by_id(atendimento_id):
    """Busca um atendimento e suas condutas pelo ID."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode = WAL;")
    cursor = conn.cursor()

    # Busca o atendimento
    cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,))
    atendimento_data = cursor.fetchone()
    if not atendimento_data:
        conn.close()
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
        queixa_principal=atendimento_data[9],
        hqa=atendimento_data[10],
        tax=atendimento_data[11],
        pa=atendimento_data[12],
        fc=atendimento_data[13],
        sat=atendimento_data[14],
        doencas_preexistentes=atendimento_data[15],
        alergias=atendimento_data[16],
        medicamentos_em_uso=atendimento_data[17],
        observacoes=atendimento_data[18],
        data_atendimento=atendimento_data[19],
        hora_atendimento=atendimento_data[20],
        semana_iso=atendimento_data[21]
    )

    # Busca as condutas associadas
    cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
    condutas_data = cursor.fetchall()
    atendimento.condutas = [
        Conduta(
            hipotese_diagnostica=c[2],
            conduta_adotada=c[3],
            resumo_conduta=c[4],
            medicamento_administrado=c[5],
            medicamento=c[6],
            posologia=c[7],
            horario_medicacao=c[8],
            observacoes=c[9]
        ) for c in condutas_data
    ]

    conn.close()
    return atendimento

def get_last_atendimento_by_badge(badge_number):
    """Busca o último atendimento de um paciente pelo número do crachá."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode = WAL;")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM atendimentos WHERE badge_number = ? ORDER BY data_atendimento DESC, hora_atendimento DESC LIMIT 1", (badge_number,))
    atendimento_data = cursor.fetchone()
    conn.close()
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

def get_atendimentos_by_badge(badge_number, days_ago=15):
    """Busca atendimentos recentes para um paciente."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode = WAL;")
    cursor = conn.cursor()
    
    date_limit = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT id, badge_number, nome, login, data_atendimento, hora_atendimento
        FROM atendimentos
        WHERE badge_number = ? AND data_atendimento >= ?
        ORDER BY data_atendimento DESC, hora_atendimento DESC
    """, (badge_number, date_limit))
    
    result = cursor.fetchall()
    conn.close()
    return result

def update_atendimento(atendimento: Atendimento):
    """Atualiza um atendimento existente no banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode = WAL;")
    cursor = conn.cursor()

    # Atualiza o atendimento principal
    cursor.execute("""
        UPDATE atendimentos SET
            nome = ?, login = ?, gestor = ?, turno = ?, setor = ?, processo = ?,
            tenure = ?, queixa_principal = ?, hqa = ?, tax = ?, pa = ?, fc = ?,
            sat = ?, doencas_preexistentes = ?, alergias = ?, medicamentos_em_uso = ?,
            observacoes = ?
        WHERE id = ?
    """, (
        atendimento.nome, atendimento.login, atendimento.gestor, atendimento.turno,
        atendimento.setor, atendimento.processo, atendimento.tenure,
        atendimento.queixa_principal, atendimento.hqa, atendimento.tax, atendimento.pa,
        atendimento.fc, atendimento.sat, atendimento.doencas_preexistentes,
        atendimento.alergias, atendimento.medicamentos_em_uso,
        atendimento.observacoes, atendimento.id
    ))

    # Remove as condutas antigas e insere as novas
    cursor.execute("DELETE FROM condutas WHERE atendimento_id = ?", (atendimento.id,))
    for conduta in atendimento.condutas:
        cursor.execute("""
            INSERT INTO condutas (
                atendimento_id, hipotese_diagnostica, conduta_adotada, resumo_conduta,
                medicamento_administrado, medicamento, posologia, horario_medicao,
                observacoes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            atendimento.id, conduta.hipotese_diagnostica, conduta.conduta_adotada,
            conduta.resumo_conduta, conduta.medicamento_administrado, conduta.medicamento,
            conduta.posologia, conduta.horario_medicacao, conduta.observacoes
        ))

    conn.commit()
    conn.close()

def export_to_csv(filepath, start_date=None, end_date=None, week_iso=None):
    """Exporta os dados de atendimentos e condutas para um arquivo CSV."""
    conn = sqlite3.connect(DB_FILE)
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
    else: # Dia atual
        query_str += " AND data_atendimento = ?"
        query_params.append(datetime.now().strftime("%Y-%m-%d"))

    cursor.execute(query_str, query_params)
    atendimentos = cursor.fetchall()

    fieldnames = [
        "id_atendimento", "badge_number", "nome", "login", "gestor", "turno", "setor", "processo", "tenure",
        "queixa_principal", "hqa", "tax", "pa", "fc", "sat", "doencas_preexistentes",
        "alergias", "medicamentos_em_uso", "observacoes_atendimento", "data_atendimento",
        "hora_atendimento", "semana_iso", "id_conduta", "hipotese_diagnostica",
        "conduta_adotada", "resumo_conduta", "medicamento_administrado", "medicamento",
        "posologia", "horario_medicao", "observacoes_conduta"
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)

        for row in atendimentos:
            atendimento_id = row[0]
            cursor.execute("SELECT * FROM condutas WHERE atendimento_id = ?", (atendimento_id,))
            condutas = cursor.fetchall()
            if not condutas:
                # Escreve o atendimento principal mesmo sem conduta
                writer.writerow(row + (None,) * 10)
            else:
                for conduta in condutas:
                    writer.writerow(row + conduta[1:])

    conn.close()
