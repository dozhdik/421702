"""Insurance-company scoped queries and access checks."""
from hmac import compare_digest

from .database import records, transaction
from .contract import Contract
from .validation import required_text

DEFAULT_PASSWORD = "1234"


def authenticate(login, password):
    if not isinstance(login, str) or not isinstance(password, str):
        raise ValueError("Неверное название страховой компании или пароль")
    name = login.strip()
    rows = records("SELECT name FROM InsuranceCompany WHERE name=? UNION SELECT insurance_company FROM Agent WHERE insurance_company=?", (name, name))
    if not rows or not compare_digest(password.encode("utf-8"), DEFAULT_PASSWORD.encode("utf-8")):
        raise ValueError("Неверное название страховой компании или пароль")
    return Tenant(rows[0]["name"])


def register_company(name, password):
    name = required_text(name, "название страховой компании")
    if not isinstance(password, str) or not compare_digest(password.encode("utf-8"), DEFAULT_PASSWORD.encode("utf-8")):
        raise ValueError("Для учебной регистрации используйте пароль 1234")
    with transaction() as conn:
        if conn.execute("SELECT 1 FROM InsuranceCompany WHERE name=?", (name,)).fetchone() or conn.execute(
            "SELECT 1 FROM Agent WHERE insurance_company=?", (name,)
        ).fetchone():
            raise ValueError("Такая страховая компания уже зарегистрирована")
        conn.execute("INSERT INTO InsuranceCompany(name) VALUES (?)", (name,))
    return Tenant(name)


class Tenant:
    def __init__(self, name):
        self.name = name

    def organizations(self):
        return records("""SELECT DISTINCT o.* FROM Organization o JOIN Contract c ON c.organization_id=o.id
            JOIN Agent a ON a.id=c.agent_id WHERE a.insurance_company=? ORDER BY o.id""", (self.name,))

    def employees(self):
        return records("""SELECT DISTINCT e.* FROM Employee e JOIN ContractEmployee ce ON ce.employee_id=e.id
            JOIN Contract c ON c.id=ce.contract_id JOIN Agent a ON a.id=c.agent_id
            WHERE a.insurance_company=? ORDER BY e.id""", (self.name,))

    def employees_for_organization(self, organization_id):
        return records("""SELECT DISTINCT e.id,e.full_name,e.risk_category FROM Employee e
            JOIN ContractEmployee ce ON ce.employee_id=e.id JOIN Contract c ON c.id=ce.contract_id
            JOIN Agent a ON a.id=c.agent_id WHERE a.insurance_company=? AND e.organization_id=?
            ORDER BY e.full_name""", (self.name, organization_id))

    def agents(self):
        return records("SELECT * FROM Agent WHERE insurance_company=? ORDER BY id", (self.name,))

    def contracts(self):
        return records("""SELECT c.id,c.contract_number,o.full_name,a.full_name AS agent,c.conclusion_date,c.end_date
            FROM Contract c JOIN Organization o ON o.id=c.organization_id JOIN Agent a ON a.id=c.agent_id
            WHERE a.insurance_company=? ORDER BY c.id""", (self.name,))

    def individual_contracts(self):
        return records("""SELECT ic.* FROM IndividualContract ic JOIN Agent a ON a.id=ic.agent_id
            WHERE a.insurance_company=? ORDER BY ic.id""", (self.name,))

    def claims(self):
        return records("""SELECT ic.id,ic.contract_id,ic.employee_id,ic.claim_date,ic.amount,ic.description
            FROM InsuranceClaim ic JOIN Contract c ON c.id=ic.contract_id JOIN Agent a ON a.id=c.agent_id
            WHERE a.insurance_company=? ORDER BY ic.id""", (self.name,))

    def clear_data(self):
        """Remove this insurer's records while preserving shared records and its login."""
        with transaction() as conn:
            exists = conn.execute("SELECT 1 FROM InsuranceCompany WHERE name=?", (self.name,)).fetchone()
            if not exists:
                if not conn.execute("SELECT 1 FROM Agent WHERE insurance_company=?", (self.name,)).fetchone():
                    raise ValueError("Страховая компания не найдена")
                conn.execute("INSERT INTO InsuranceCompany(name) VALUES (?)", (self.name,))
            contract_ids = [row[0] for row in conn.execute("""SELECT c.id FROM Contract c
                JOIN Agent a ON a.id=c.agent_id WHERE a.insurance_company=?""", (self.name,))]
            employee_ids = set()
            organization_ids = set()
            for contract_id in contract_ids:
                employee_ids.update(row[0] for row in conn.execute(
                    "SELECT employee_id FROM ContractEmployee WHERE contract_id=?", (contract_id,)))
                organization_ids.update(row[0] for row in conn.execute(
                    "SELECT organization_id FROM Contract WHERE id=?", (contract_id,)))
                conn.execute("DELETE FROM InsuranceClaim WHERE contract_id=?", (contract_id,))
                conn.execute("DELETE FROM Contract WHERE id=?", (contract_id,))
            conn.execute("DELETE FROM IndividualContract WHERE agent_id IN (SELECT id FROM Agent WHERE insurance_company=?)", (self.name,))
            conn.execute("DELETE FROM Agent WHERE insurance_company=?", (self.name,))
            for employee_id in employee_ids:
                conn.execute("""DELETE FROM Employee WHERE id=? AND NOT EXISTS
                    (SELECT 1 FROM ContractEmployee WHERE employee_id=?) AND NOT EXISTS
                    (SELECT 1 FROM InsuranceClaim WHERE employee_id=?)""", (employee_id, employee_id, employee_id))
            for organization_id in organization_ids:
                conn.execute("""DELETE FROM Organization WHERE id=? AND NOT EXISTS
                    (SELECT 1 FROM Contract WHERE organization_id=?) AND NOT EXISTS
                    (SELECT 1 FROM Employee WHERE organization_id=?)""", (organization_id, organization_id, organization_id))
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'").fetchone():
                for table in ("Organization", "Employee", "Agent", "Contract", "Payout"):
                    if not conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone():
                        conn.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))

    def require_contract(self, contract_id):
        if not records("""SELECT c.id FROM Contract c JOIN Agent a ON a.id=c.agent_id
            WHERE c.id=? AND a.insurance_company=?""", (contract_id, self.name)):
            raise ValueError("Договор не найден")

    def require_organization(self, organization_id):
        if not any(row["id"] == organization_id for row in self.organizations()):
            raise ValueError("Организация не найдена")

    def require_employee(self, employee_id):
        if not any(row["id"] == employee_id for row in self.employees()):
            raise ValueError("Сотрудник не найден")

    def require_agent(self, agent_id):
        if not records("SELECT id FROM Agent WHERE id=? AND insurance_company=?", (agent_id, self.name)):
            raise ValueError("Агент не относится к вашей страховой компании")

    def require_individual(self, contract_id):
        if not any(row["id"] == contract_id for row in self.individual_contracts()):
            raise ValueError("Договор не найден")

    def require_claim(self, claim_id):
        if not any(row["id"] == claim_id for row in self.claims()):
            raise ValueError("Страховой случай не найден")

    def list_items(self, kind):
        methods = {"organizations": self.organizations, "employees": self.employees,
                   "agents": self.agents, "individuals": self.individual_contracts}
        if kind not in methods:
            raise ValueError("Раздел недоступен")
        return methods[kind]()

    def report_contracts(self, selected_date, code=None):
        Contract.validate_date(selected_date)
        query = """SELECT o.full_name AS organization,o.address,c.contract_number,c.conclusion_date,c.end_date
            FROM Contract c JOIN Agent a ON a.id=c.agent_id JOIN Organization o ON o.id=c.organization_id
            WHERE a.insurance_company=? AND c.conclusion_date<=? AND c.end_date>=?"""
        params = [self.name, selected_date, selected_date]
        if code is not None:
            query += " AND o.organization_code=?"
            params.append(code)
        return records(query + " ORDER BY o.full_name,c.contract_number", params)

    def report_agents(self, selected_date, code=None):
        Contract.validate_date(selected_date)
        query = """SELECT DISTINCT a.id,a.insurance_company,a.full_name,a.phone_number
            FROM Agent a JOIN Contract c ON c.agent_id=a.id JOIN Organization o ON o.id=c.organization_id
            WHERE a.insurance_company=? AND c.conclusion_date<=? AND c.end_date>=?"""
        params = [self.name, selected_date, selected_date]
        if code is not None:
            query += " AND o.organization_code=?"
            params.append(code)
        return records(query + " ORDER BY a.full_name,a.id", params)

    def report_payouts(self, selected_date, code=None):
        Contract.validate_date(selected_date)
        query = """SELECT o.full_name AS organization,c.contract_number,p.risk_category,p.payout_amount,
            c.conclusion_date,c.end_date FROM Payout p JOIN Contract c ON c.id=p.contract_id
            JOIN Agent a ON a.id=c.agent_id JOIN Organization o ON o.id=c.organization_id
            WHERE a.insurance_company=? AND c.conclusion_date<=? AND c.end_date>=?"""
        params = [self.name, selected_date, selected_date]
        if code is not None:
            query += " AND o.organization_code=?"
            params.append(code)
        return records(query + " ORDER BY o.full_name,c.contract_number,p.risk_category", params)
