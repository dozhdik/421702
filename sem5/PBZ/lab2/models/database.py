import sqlite3
from pathlib import Path

def get_connection():
    DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'insurance.db'
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Organization(
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_code  INTEGER UNIQUE NOT NULL,
        full_name          TEXT NOT NULL,
        brief_name         TEXT NOT NULL,
        address            TEXT NOT NULL,
        bank_details       TEXT NOT NULL,
        specialization     TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Agent(
        id                       INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name                TEXT NOT NULL,
        passport_details         TEXT NOT NULL,
        phone_number             TEXT NOT NULL,
        insurance_company        TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Employee(
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id         INTEGER NOT NULL,
        full_name               TEXT NOT NULL,
        age                     INTEGER NOT NULL,
        risk_category           TEXT NOT NULL,
        FOREIGN KEY (organization_id) REFERENCES Organization(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Contract(
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_number         TEXT UNIQUE NOT NULL,
        organization_id         INTEGER NOT NULL,
        agent_id                INTEGER NOT NULL,
        conclusion_date         DATE NOT NULL,
        end_date                DATE NOT NULL,
        FOREIGN KEY (organization_id) REFERENCES Organization(id) ON DELETE CASCADE,
        FOREIGN KEY (agent_id) REFERENCES Agent(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payout(
        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id            INTEGER NOT NULL,
        risk_category          TEXT NOT NULL,
        payout_amount          REAL NOT NULL,
        FOREIGN KEY (contract_id) REFERENCES Contract(id) ON DELETE CASCADE,
        UNIQUE (contract_id, risk_category)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ContractEmployee(
        contract_id             INTEGER NOT NULL,
        employee_id             INTEGER NOT NULL,
        PRIMARY KEY (contract_id, employee_id),
        FOREIGN KEY (contract_id) REFERENCES Contract(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES Employee(id) ON DELETE CASCADE
        )
    ''')

    connection.commit()
    connection.close()