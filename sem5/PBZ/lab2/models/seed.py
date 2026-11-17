from pathlib import Path

from .database import get_connection, init_database
from .demo_data import add_supplemental_data


ORGANIZATIONS = (
    (9001, "Городская больница № 1", "ГБ № 1", "Минск, ул. Ленина, 10", "BY00 TEST 0000 0000 0001 0000", "медицинское учреждение"),
    (9002, "Автобусный парк № 2", "АП № 2", "Минск, ул. Транспортная, 5", "BY00 TEST 0000 0000 0002 0000", "автотранспортное предприятие"),
    (9003, "Учебный центр", "УЦ", "Минск, ул. Студенческая, 3", "BY00 TEST 0000 0000 0003 0000", "учебное заведение"),
)

AGENTS = (
    ("Смирнова Анна Сергеевна", "MP9000001", "+375291111111", "БелСтрах"),
    ("Ковалёв Дмитрий Игоревич", "MP9000002", "+375292222222", "Надёжный полис"),
)

EMPLOYEES = (
    (9001, "Иванов Иван Иванович", 34, "первая"),
    (9001, "Петров Пётр Петрович", 46, "вторая"),
    (9001, "Сидорова Мария Алексеевна", 52, "высшая"),
    (9001, "Егорова Ольга Николаевна", 29, "первая"),
    (9002, "Кузнецов Александр Павлович", 40, "первая"),
    (9002, "Орлова Наталья Викторовна", 27, "вторая"),
    (9003, "Морозов Сергей Андреевич", 38, "первая"),
)

CONTRACTS = (
    (
        "КД-0001", 9001, "MP9000001", "2026-01-15", "2026-12-31",
        ("Иванов Иван Иванович", "Петров Пётр Петрович", "Сидорова Мария Алексеевна"),
        (("первая", 10000), ("вторая", 15000), ("высшая", 20000)),
    ),
    (
        "КД-0002", 9001, "MP9000001", "2026-09-01", "2026-11-30",
        ("Егорова Ольга Николаевна", "Петров Пётр Петрович"),
        (("первая", 12000), ("вторая", 17000)),
    ),
    (
        "КД-0003", 9001, "MP9000002", "2025-01-01", "2025-12-31",
        ("Иванов Иван Иванович",),
        (("первая", 8000),),
    ),
    (
        "КД-0004", 9002, "MP9000002", "2026-02-01", "2027-02-01",
        ("Кузнецов Александр Павлович", "Орлова Наталья Викторовна"),
        (("первая", 11000), ("вторая", 16000)),
    ),
    (
        "КД-0005", 9002, "MP9000001", "2027-03-01", "2027-12-31",
        ("Кузнецов Александр Павлович",),
        (("первая", 13000),),
    ),
)


def seed_database() -> dict[str, int]:
    """Добавить недостающие примеры и вернуть число новых записей по таблицам.

    Повторный вызов не создаёт дубликаты и не перезаписывает существующие данные.
    Для проверки отчётов удобно использовать код 9001 и дату 2026-11-03.
    """
    (Path(__file__).resolve().parent.parent / "data").mkdir(exist_ok=True)
    init_database()

    added = {
        "organizations": 0,
        "agents": 0,
        "employees": 0,
        "contracts": 0,
        "contract_employees": 0,
        "payouts": 0,
        "individual_contracts": 0,
        "claims": 0,
    }
    organization_ids = {}
    agent_ids = {}
    employee_ids = {}

    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        for code, full_name, brief_name, address, bank_details, specialization in ORGANIZATIONS:
            row = conn.execute(
                "SELECT id, full_name FROM Organization WHERE organization_code = ?", (code,)
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    """INSERT INTO Organization
                       (organization_code, full_name, brief_name, address, bank_details, specialization)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (code, full_name, brief_name, address, bank_details, specialization),
                )
                organization_ids[code] = cur.lastrowid
                added["organizations"] += 1
            else:
                if row["full_name"] != full_name:
                    organization_ids[code] = None
                    continue
                organization_ids[code] = row["id"]

        for full_name, passport, phone, company in AGENTS:
            row = conn.execute(
                "SELECT id, full_name FROM Agent WHERE passport_details = ?", (passport,)
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    """INSERT INTO Agent
                       (full_name, passport_details, phone_number, insurance_company)
                       VALUES (?, ?, ?, ?)""",
                    (full_name, passport, phone, company),
                )
                agent_ids[passport] = cur.lastrowid
                added["agents"] += 1
            else:
                if row["full_name"] != full_name:
                    agent_ids[passport] = None
                    continue
                agent_ids[passport] = row["id"]

        for code, full_name, age, risk_category in EMPLOYEES:
            organization_id = organization_ids[code]
            if organization_id is None:
                continue
            row = conn.execute(
                "SELECT id FROM Employee WHERE organization_id = ? AND full_name = ?",
                (organization_id, full_name),
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    """INSERT INTO Employee
                       (organization_id, full_name, age, risk_category)
                       VALUES (?, ?, ?, ?)""",
                    (organization_id, full_name, age, risk_category),
                )
                employee_ids[(code, full_name)] = cur.lastrowid
                added["employees"] += 1
            else:
                employee_ids[(code, full_name)] = row["id"]

        for number, code, passport, start, end, employees, payouts in CONTRACTS:
            organization_id = organization_ids[code]
            if organization_id is None or agent_ids[passport] is None:
                continue
            if any((code, full_name) not in employee_ids for full_name in employees):
                continue
            if conn.execute("SELECT 1 FROM IndividualContract WHERE contract_number=?", (number,)).fetchone():
                continue
            row = conn.execute(
                "SELECT id, organization_id, agent_id FROM Contract WHERE contract_number = ?",
                (number,),
            ).fetchone()
            if row is None:
                cur = conn.execute(
                    """INSERT INTO Contract
                       (contract_number, organization_id, agent_id, conclusion_date, end_date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (number, organization_id, agent_ids[passport], start, end),
                )
                contract_id = cur.lastrowid
                added["contracts"] += 1
            else:
                continue

            for full_name in employees:
                employee_id = employee_ids[(code, full_name)]
                row = conn.execute(
                    """SELECT 1 FROM ContractEmployee
                       WHERE contract_id = ? AND employee_id = ?""",
                    (contract_id, employee_id),
                ).fetchone()
                if row is None:
                    conn.execute(
                        """INSERT INTO ContractEmployee (contract_id, employee_id)
                           VALUES (?, ?)""",
                        (contract_id, employee_id),
                    )
                    added["contract_employees"] += 1

            for category, amount in payouts:
                row = conn.execute(
                    """SELECT id FROM Payout
                       WHERE contract_id = ? AND risk_category = ?""",
                    (contract_id, category),
                ).fetchone()
                if row is None:
                    conn.execute(
                        """INSERT INTO Payout (contract_id, risk_category, payout_amount)
                           VALUES (?, ?, ?)""",
                        (contract_id, category, amount),
                    )
                    added["payouts"] += 1

        add_supplemental_data(conn, added)
        conn.commit()
        return added
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()