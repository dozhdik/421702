import sqlite3
from .database import get_connection, transaction, records
from .payout import money
from .validation import required_text
from decimal import Decimal
from .employee import Employee
import re
from datetime import date

class Contract:
    def __init__(self, contract_number: str, organization_id: int, agent_id: int, conclusion_date: str, end_date: str, id: int | None = None):
        self._id = id
        self._organization_id = organization_id
        self._agent_id = agent_id
        self.contract_number = contract_number
        self.conclusion_date = conclusion_date
        self.end_date = end_date

    @property
    def organization_id(self):
        return self._organization_id

    @property
    def agent_id(self):
        return self._agent_id

    @classmethod
    def from_row(cls, row):
        return cls(
            id = row['id'],
            organization_id = row['organization_id'],
            agent_id = row['agent_id'],
            contract_number = row['contract_number'],
            conclusion_date = row['conclusion_date'],
            end_date = row['end_date']
        ) 

    @classmethod
    def get_by_id(cls, id: int):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM Contract WHERE id = ?", (id,)).fetchone()
        finally:
            conn.close()
        return cls.from_row(row) if row else None

    @staticmethod
    def validate_date(value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"The varieble {value} can't be empty!")
        
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Date must have YYYY-MM-DD format!")
        
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValueError("Invalid calendar date!")

    def validate(self):
        for name in ('organization_id', 'agent_id'):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"There is incorrect type of data in varieble {name}!")

        self.contract_number = required_text(self.contract_number, "номер договора")

        Contract.validate_date(self.conclusion_date)
        Contract.validate_date(self.end_date)
        
        if self.conclusion_date > self.end_date:
            raise ValueError("End date cannot be earlier than conclusion date!")
        
    def add(self):
        if self._id is not None:
            raise ValueError("There is contract whith the same id!")
        self.validate()
        conn = get_connection()

        try:
            org = conn.execute("SELECT DISTINCT * FROM Organization WHERE id = ?", (self._organization_id,)).fetchone()
            if org is None:
                raise ValueError("The organization is not listed!")
            agent = conn.execute("SELECT DISTINCT * FROM Agent WHERE id = ?", (self._agent_id,)).fetchone()
            if agent is None: 
                raise ValueError("The agent is not listed!")
            cur = conn.execute("INSERT INTO Contract (contract_number, organization_id, agent_id, conclusion_date, end_date) VALUES (?, ?, ?, ?, ?)", (self.contract_number, self._organization_id, self._agent_id, self.conclusion_date, self.end_date))
            conn.commit()
            self._id = cur.lastrowid
        finally:
            conn.close()

    def update(self):
        if self._id is None:
            raise ValueError("There is missing id!")
        self.validate()
        conn = get_connection()

        try:
            cur = conn.execute("UPDATE Contract SET contract_number = ?, organization_id = ?, agent_id = ?, conclusion_date = ?, end_date = ? WHERE id = ?", (self.contract_number, self._organization_id, self._agent_id, self.conclusion_date, self.end_date, self._id))
            if cur.rowcount == 0:
                raise ValueError(f"There isn't contract with id: {self._id}!")
            conn.commit()
        finally:
            conn.close()

    def delete(self):
        if self._id is None:
            raise ValueError("There is missing id!")
        conn = get_connection()

        try:
            cur = conn.execute("DELETE FROM Contract WHERE id = ?", (self._id,))
            if cur.rowcount == 0:
                raise ValueError(f"There isn't contract with id: {self._id}!")
            conn.commit()
            self._id = None
        finally:
            conn.close()

    
    @classmethod
    def get_by_number(cls, contract_number: str):
        if not isinstance(contract_number, str) or not contract_number.strip():
            raise ValueError("Contract number cannot be empty!")

        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM Contract WHERE contract_number = ?",
                (contract_number,)
            ).fetchone()
        finally:
            conn.close()

        return cls.from_row(row) if row else None


    def add_employee(self, employee_id: int):
        if self._id is None:
            raise ValueError("Contract must be saved first!")

        if type(employee_id) is not int or employee_id <= 0:
            raise ValueError("Incorrect employee ID!")

        conn = get_connection()
        try:
            contract = conn.execute(
                "SELECT organization_id FROM Contract WHERE id = ?",
                (self._id,)
            ).fetchone()

            if contract is None:
                raise ValueError("Contract does not exist!")

            employee = conn.execute(
                "SELECT organization_id FROM Employee WHERE id = ?",
                (employee_id,)
            ).fetchone()

            if employee is None:
                raise ValueError("Employee does not exist!")

            if employee["organization_id"] != contract["organization_id"]:
                raise ValueError(
                    "Employee belongs to another organization!"
                )

            existing = conn.execute(
                """
                SELECT 1 FROM ContractEmployee
                WHERE contract_id = ? AND employee_id = ?
                """,
                (self._id, employee_id)
            ).fetchone()

            if existing is not None:
                raise ValueError("Employee is already insured by this contract!")

            conn.execute(
                """
                INSERT INTO ContractEmployee (contract_id, employee_id)
                VALUES (?, ?)
                """,
                (self._id, employee_id)
            )

            conn.commit()
        finally:
            conn.close()


    def remove_employee(self, employee_id: int):
        if self._id is None:
            raise ValueError("Contract must be saved first!")

        if type(employee_id) is not int or employee_id <= 0:
            raise ValueError("Incorrect employee ID!")

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                DELETE FROM ContractEmployee
                WHERE contract_id = ? AND employee_id = ?
                """,
                (self._id, employee_id)
            )

            if cur.rowcount == 0:
                raise ValueError(
                    "Employee is not insured by this contract!"
                )

            conn.commit()
        finally:
            conn.close()


    def get_employees(self):
        if self._id is None:
            raise ValueError("Contract must be saved first!")

        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT e.*
                FROM Employee AS e
                JOIN ContractEmployee AS ce
                    ON ce.employee_id = e.id
                WHERE ce.contract_id = ?
                ORDER BY e.full_name
                """,
                (self._id,)
            ).fetchall()
        finally:
            conn.close()

        return [Employee.from_row(row) for row in rows]

    @staticmethod
    def dated_org_contract(code: int, selected_date: str):
        Contract.validate_date(selected_date)
        conn = get_connection()
    
        try:
            rows = conn.execute(
                '''
                SELECT o.full_name, o.address,
                    c.contract_number, c.conclusion_date, c.end_date
                FROM Organization AS o
                LEFT JOIN Contract AS c
                    ON c.organization_id = o.id
                    AND c.conclusion_date <= ?
                    AND c.end_date >= ?
                WHERE o.organization_code = ?
                ''',(selected_date, selected_date, code)).fetchall()
        finally:
            conn.close()

        if not rows:
            return None 

        return {
            "organization_name": rows[0]["full_name"],
            "address": rows[0]["address"],
            "date": selected_date,
            "contracts": [
                {
                    "number": row["contract_number"],
                    "start": row["conclusion_date"],
                    "end": row["end_date"],
                }
            for row in rows
            if row["contract_number"] is not None
            ],
        }

    @staticmethod
    def dated_org_agent(code: int, selected_date: str):
        Contract.validate_date(selected_date)
        conn = get_connection()

        try:
            rows = conn.execute(
                '''
                SELECT DISTINCT
                    a.id, a.insurance_company, a.full_name, a.phone_number
                FROM Organization AS o
                JOIN Contract AS c
                    ON c.organization_id = o.id
                JOIN Agent AS a
                    ON a.id = c.agent_id
                WHERE o.organization_code = ?
                    AND c.conclusion_date <= ?
                    AND c.end_date >= ?
                ORDER BY a.full_name
            ''',(code, selected_date, selected_date)
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        return {
            "date": selected_date,
            "agents": [
                {
                    "insurance_company": row["insurance_company"],
                    "full_name": row["full_name"],
                    "phone_number": row["phone_number"]
                }
                for row in rows
            ]
        }

    @staticmethod
    def payout_date(code: int, selected_date: str):
        Contract.validate_date(selected_date)
        conn = get_connection()

        try: 
            rows = conn.execute(
            '''
            SELECT p.payout_amount, p.risk_category
            FROM Payout as p
            JOIN Contract as c
                ON c.id = p.contract_id
            JOIN Organization as o
                ON o.id = c.organization_id
            WHERE o.organization_code = ?
                AND c.conclusion_date <= ?
                AND c.end_date >= ?
            ORDER BY p.payout_amount
            ''', (code ,selected_date, selected_date)).fetchall()
        finally:
            conn.close()

        if not rows:
            return None

        return {
            "date": selected_date,
            "payout": [
                {
                    "payout_amount": row["payout_amount"],
                    "risk_category": row["risk_category"]
                }
                for row in rows
            ]
        }

    @staticmethod
    def save_contract(number, organization_id, agent_id, start, end, employee_ids, payouts, contract_id=None):
        number = required_text(number, "номер договора")
        Contract.validate_date(start); Contract.validate_date(end)
        if start > end:
            raise ValueError("Дата окончания раньше даты начала")
        if not employee_ids or len(employee_ids) != len(set(employee_ids)):
            raise ValueError("Выберите хотя бы одного сотрудника без повторов")
        amounts = {}
        for category, amount in payouts.items():
            amounts[required_text(category, "категория")] = money(amount)
        with transaction() as conn:
            if conn.execute("SELECT 1 FROM IndividualContract WHERE contract_number = ?", (number,)).fetchone():
                raise ValueError("Номер уже используется индивидуальным договором")
            categories = set()
            for employee_id in employee_ids:
                row = conn.execute("SELECT organization_id, risk_category FROM Employee WHERE id = ?", (employee_id,)).fetchone()
                if not row or row["organization_id"] != organization_id:
                    raise ValueError("Сотрудник не принадлежит организации договора")
                categories.add(row["risk_category"])
            if not categories.issubset(amounts):
                raise ValueError("Укажите сумму для каждой категории выбранных сотрудников")
            if contract_id is None:
                cur = conn.execute("INSERT INTO Contract(contract_number, organization_id, agent_id, conclusion_date, end_date) VALUES (?, ?, ?, ?, ?)", (number, organization_id, agent_id, start, end))
                contract_id = cur.lastrowid
            else:
                old = conn.execute("SELECT organization_id FROM Contract WHERE id = ?", (contract_id,)).fetchone()
                if not old:
                    raise ValueError("Договор не найден")
                if old["organization_id"] != organization_id:
                    raise ValueError("Организацию договора изменить нельзя")
                claims = conn.execute("SELECT employee_id, claim_date, amount FROM InsuranceClaim WHERE contract_id = ?", (contract_id,)).fetchall()
                for claim in claims:
                    if claim["employee_id"] not in employee_ids or not start <= claim["claim_date"] <= end:
                        raise ValueError("Изменение противоречит сохранённому страховому случаю")
                    category = conn.execute("SELECT risk_category FROM Employee WHERE id = ?", (claim["employee_id"],)).fetchone()[0]
                    if category not in amounts or Decimal(claim["amount"]) > Decimal(amounts[category]):
                        raise ValueError("Сумма договора меньше выплаты по страховому случаю")
                conn.execute("UPDATE Contract SET contract_number=?, agent_id=?, conclusion_date=?, end_date=? WHERE id=?", (number, agent_id, start, end, contract_id))
                conn.execute("DELETE FROM ContractEmployee WHERE contract_id=?", (contract_id,))
                conn.execute("DELETE FROM Payout WHERE contract_id=?", (contract_id,))
            conn.executemany("INSERT INTO ContractEmployee(contract_id, employee_id) VALUES (?,?)", [(contract_id, i) for i in employee_ids])
            conn.executemany("INSERT INTO Payout(contract_id, risk_category, payout_amount) VALUES (?,?,?)", [(contract_id, k, v) for k, v in amounts.items()])
            return contract_id

    @staticmethod
    def delete_contract(contract_id):
        with transaction() as conn:
            if conn.execute("SELECT 1 FROM InsuranceClaim WHERE contract_id=?", (contract_id,)).fetchone():
                raise ValueError("Договор содержит страховые случаи")
            if not conn.execute("DELETE FROM Contract WHERE id=?", (contract_id,)).rowcount:
                raise ValueError("Договор не найден")

    @staticmethod
    def report_contracts(code, selected_date):
        report = Contract.dated_org_contract(code, selected_date)
        if report is None:
            return {"date": selected_date, "organization": None, "contracts": []}
        rows = [{"contract_number": row["number"], "conclusion_date": row["start"],
                 "end_date": row["end"]} for row in report["contracts"]]
        return {"date": selected_date, "organization": {"full_name": report["organization_name"],
                "address": report["address"]}, "contracts": rows}

    @staticmethod
    def report_agents(code, selected_date):
        report = Contract.dated_org_agent(code, selected_date)
        return {"date": selected_date, "agents": report["agents"] if report else []}

    @staticmethod
    def report_payouts(selected_date, code=None):
        Contract.validate_date(selected_date)
        query = """SELECT o.full_name AS organization, c.contract_number, p.risk_category, p.payout_amount,
                   c.conclusion_date, c.end_date
            FROM Payout p JOIN Contract c ON c.id=p.contract_id JOIN Organization o ON o.id=c.organization_id
            WHERE c.conclusion_date<=? AND c.end_date>=?"""
        params = [selected_date,selected_date]
        if code is not None:
            query += " AND o.organization_code=?"
            params.append(code)
        return {"date":selected_date, "payouts":records(query+" ORDER BY o.full_name,c.contract_number,p.risk_category", params)}
