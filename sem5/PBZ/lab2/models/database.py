import sqlite3

def get_connection():
    conn = sqlite3.connect('../data/insurance.db')
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
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        FullName                TEXT NOT NULL,
        PassportDetails        TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Employee(
        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
        organization_id        INTEGER NOT NULL,
        FullName               TEXT NOT NULL,
        Age                    INTEGER NOT NULL,
        RiskCategory           TEXT NOT NULL,
        FOREIGN KEY (organization_id) REFERENCES Organization(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Contract(
        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
        ContractNumber         TEXT UNIQUE NOT NULL,
        organization_id        INTEGER NOT NULL,
        AgentId                INTEGER NOT NULL,
        ConclusionDate         DATE NOT NULL,
        EndDate                DATE NOT NULL,
        FOREIGN KEY (organization_id) REFERENCES Organization(id),
        FOREIGN KEY (AgentId) REFERENCES Agent(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Payout(
        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
        ContractId             INTEGER NOT NULL,
        RiskCategory           TEXT NOT NULL,
        PayoutAmount           REAL NOT NULL,
        FOREIGN KEY (ContractId) REFERENCES Contract(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ContractEmployee(
        ContractId             INTEGER NOT NULL,
        EmployeeId             INTEGER NOT NULL,
        PRIMARY KEY (ContractId, EmployeeId),
        FOREIGN KEY (ContractId) REFERENCES Contract(id),
        FOREIGN KEY (EmployeeId) REFERENCES Employee(id)
        )
    ''')

    connection.commit()
    connection.close()