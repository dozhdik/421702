"""Add repeatable sample records for one insurance company."""
import hashlib

from .database import transaction


def seed_company(company):
    if not isinstance(company, str) or not company.strip():
        raise ValueError("Страховая компания не указана")
    company = company.strip()
    token = int.from_bytes(hashlib.sha256(company.encode("utf-8")).digest()[:8], "big") % 9_000_000
    counts = {"organizations": 0, "agents": 0, "employees": 0, "contracts": 0,
              "contract_employees": 0, "payouts": 0, "individual_contracts": 0, "claims": 0}
    org_names = ("ООО «Речной маршрут»", "Медицинский центр «Лесной берег»", "Учебный центр «Новые горизонты»")
    cities = ("Минск", "Гродно", "Брест")
    names = ("Иванов Артём Сергеевич", "Ковалева Ольга Петровна", "Смирнов Павел Викторович",
             "Орлова Анна Игоревна", "Соколов Дмитрий Андреевич")
    agent_names = ("Новикова Марина Сергеевна", "Павлов Андрей Николаевич", "Кузнецова Ирина Павловна")
    categories = ("первая", "вторая", "высшая")
    with transaction() as conn:
        if not conn.execute("SELECT 1 FROM InsuranceCompany WHERE name=?", (company,)).fetchone() and not conn.execute(
            "SELECT 1 FROM Agent WHERE insurance_company=?", (company,)
        ).fetchone():
            raise ValueError("Страховая компания не найдена")
        orgs, agents, employees = [], [], {}
        for index, name in enumerate(org_names):
            code = 300000000 + token * 3 + index
            full_name = name
            row = conn.execute("SELECT id,full_name FROM Organization WHERE organization_code=?", (code,)).fetchone()
            if row and row["full_name"] not in (full_name, f"{name} ({company})"):
                orgs.append(None)
                continue
            if row:
                org_id = row["id"]
            else:
                org_id = conn.execute("""INSERT INTO Organization
                    (organization_code,full_name,brief_name,address,bank_details,specialization)
                    VALUES (?,?,?,?,?,?)""",
                    (code, full_name, name, f"г. {cities[index]}, ул. Садовая, д. {12 + index}",
                     f"BY00 TEST {token:07d} {index:02d}", ("транспорт", "медицинские услуги", "образование")[index])).lastrowid
                counts["organizations"] += 1
            orgs.append(org_id)
        for index, name in enumerate(agent_names):
            passport = f"MP{(token + index) % 10000000:07d}"
            row = conn.execute("SELECT id,full_name,insurance_company FROM Agent WHERE passport_details=?", (passport,)).fetchone()
            if row and (row["full_name"] != name or row["insurance_company"] != company):
                agents.append(None)
                continue
            if row:
                agent_id = row["id"]
            else:
                agent_id = conn.execute("""INSERT INTO Agent
                    (full_name,passport_details,phone_number,insurance_company) VALUES (?,?,?,?)""",
                    (name, passport, f"+37529{(token + index) % 10000000:07d}", company)).lastrowid
                counts["agents"] += 1
            agents.append(agent_id)
        for org_index, org_id in enumerate(orgs):
            if org_id is None:
                continue
            employees[org_id] = []
            for index, name in enumerate(names):
                category = categories[index % len(categories)]
                row = conn.execute("""SELECT id,risk_category FROM Employee
                    WHERE organization_id=? AND full_name=?""", (org_id, name)).fetchone()
                if row and row["risk_category"] != category:
                    continue
                if row:
                    employee_id = row["id"]
                else:
                    employee_id = conn.execute("""INSERT INTO Employee
                        (organization_id,full_name,age,risk_category) VALUES (?,?,?,?)""",
                        (org_id, name, 26 + index * 5 + org_index, category)).lastrowid
                    counts["employees"] += 1
                employees[org_id].append(employee_id)
        for index in range(6):
            org_id, agent_id = orgs[index % 3], agents[index % 3]
            if org_id is None or agent_id is None or not employees.get(org_id):
                continue
            number = f"КД-{token:07d}-{index+1:02d}"
            if conn.execute("SELECT 1 FROM Contract WHERE contract_number=?", (number,)).fetchone() or conn.execute(
                "SELECT 1 FROM IndividualContract WHERE contract_number=?", (number,)
            ).fetchone():
                continue
            year = (2025, 2026, 2027)[index % 3]
            contract_id = conn.execute("""INSERT INTO Contract
                (contract_number,organization_id,agent_id,conclusion_date,end_date) VALUES (?,?,?,?,?)""",
                (number, org_id, agent_id, f"{year}-01-01", f"{year}-12-31")).lastrowid
            counts["contracts"] += 1
            selected = employees[org_id]
            for employee_id in selected:
                conn.execute("INSERT INTO ContractEmployee(contract_id,employee_id) VALUES (?,?)", (contract_id, employee_id))
                counts["contract_employees"] += 1
            for category in categories:
                conn.execute("INSERT INTO Payout(contract_id,risk_category,payout_amount) VALUES (?,?,?)",
                             (contract_id, category, 10000 + categories.index(category) * 5000 + index * 100))
                counts["payouts"] += 1
            conn.execute("""INSERT INTO InsuranceClaim(contract_id,employee_id,claim_date,amount,description)
                VALUES (?,?,?,?,?)""", (contract_id, selected[0], f"{year}-06-15", "250.00", "Расходы на лечение"))
            counts["claims"] += 1
        for index in range(3):
            agent_id = agents[index]
            number = f"ИД-{token:07d}-{index+1:02d}"
            if agent_id is None or conn.execute("SELECT 1 FROM Contract WHERE contract_number=?", (number,)).fetchone() or conn.execute(
                "SELECT 1 FROM IndividualContract WHERE contract_number=?", (number,)
            ).fetchone():
                continue
            conn.execute("""INSERT INTO IndividualContract
                (contract_number,full_name,agent_id,conclusion_date,end_date,amount) VALUES (?,?,?,?,?,?)""",
                (number, names[index], agent_id, "2026-01-01", "2026-12-31", "10000.00"))
            counts["individual_contracts"] += 1
    return counts
