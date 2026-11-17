import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

def get_connection():
    DB_PATH = Path(os.environ.get('INSURANCE_DB_PATH', Path(__file__).resolve().parent.parent / 'data' / 'insurance.db'))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS InsuranceCompany(
        name TEXT PRIMARY KEY NOT NULL
        )''')

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

    cursor.execute('''CREATE TABLE IF NOT EXISTS IndividualContract (
        id INTEGER PRIMARY KEY, contract_number TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL, agent_id INTEGER NOT NULL REFERENCES Agent(id),
        conclusion_date TEXT NOT NULL, end_date TEXT NOT NULL, amount TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS InsuranceClaim (
        id INTEGER PRIMARY KEY, contract_id INTEGER NOT NULL REFERENCES Contract(id),
        employee_id INTEGER NOT NULL REFERENCES Employee(id), claim_date TEXT NOT NULL,
        amount TEXT NOT NULL, description TEXT NOT NULL)''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contract_org_dates ON Contract(organization_id, conclusion_date, end_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contract_agent ON Contract(agent_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_employee_org ON Employee(organization_id)')
    cursor.execute("INSERT OR IGNORE INTO InsuranceCompany(name) SELECT DISTINCT insurance_company FROM Agent WHERE trim(insurance_company) != ''")
    connection.commit()
    connection.close()
    from .format_migration import migrate_legacy_samples
    migrate_legacy_samples()


@contextmanager
def transaction():
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def records(query, params=()):
    conn = get_connection()
    try:
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def clear_database():
    """Delete all user table rows atomically, keeping the schema and foreign keys."""
    with transaction() as conn:
        tables = [row["name"] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND substr(name, 1, 7) != 'sqlite_'"
        )]
        remaining = set(tables)
        while remaining:
            parents = set()
            for table in remaining:
                quoted = '"' + table.replace('"', '""') + '"'
                for row in conn.execute(f"PRAGMA foreign_key_list({quoted})"):
                    if row["table"] in remaining and row["table"] != table:
                        parents.add(row["table"])
            leaves = sorted(remaining - parents)
            if not leaves:
                raise sqlite3.IntegrityError("Невозможно очистить таблицы с циклическими внешними ключами")
            for table in leaves:
                quoted = '"' + table.replace('"', '""') + '"'
                conn.execute(f"DELETE FROM {quoted}")
                remaining.remove(table)
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'").fetchone():
            conn.execute("DELETE FROM sqlite_sequence")
