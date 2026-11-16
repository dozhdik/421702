import sqlite3
from .database import get_connection, transaction, records
from decimal import Decimal

class Employee:
    @staticmethod
    def list_all():
        return records("SELECT * FROM Employee ORDER BY id")

    def __init__(self, organization_id: int,full_name: str, age: int, risk_category: str, id: int | None = None):
        self._id = id
        self._organization_id = organization_id
        self.full_name = full_name
        self.age = age
        self.risk_category = risk_category

    @property
    def organization_id(self):
        return self._organization_id

    @classmethod
    def from_row(cls, row):
        return cls(
            id = row['id'],
            organization_id = row['organization_id'],
            full_name = row['full_name'],
            age = row['age'],
            risk_category = row['risk_category']
        )
    
    @classmethod
    def get_by_id(cls, id: int):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM Employee WHERE id = ?", (id,)).fetchone()
        finally:
            conn.close()
        return cls.from_row(row) if row else None

    def validate(self):
        for name in ('organization_id', 'age'):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError("Incorrect data type!")
        for name in ('full_name', 'risk_category'):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"The variable {name} cannot be empty!")

    def add(self):
        if self._id is not None:
            raise ValueError("Employee already exists!")
        self.validate()

        conn = get_connection()
        try:
            org = conn.execute("SELECT id FROM Organization WHERE id = ?", (self.organization_id,)).fetchone()
            if org is None:
                raise ValueError("The employee is not listed in any organization.")
            cur = conn.execute("INSERT INTO Employee (organization_id, full_name, age, risk_category) VALUES (?, ?, ?, ?)", (self.organization_id, self.full_name, self.age, self.risk_category))
            conn.commit()
            self._id = cur.lastrowid
        finally:
            conn.close()

    def update(self):
        if self._id is None:
            raise ValueError("There is missing id!")
        self.validate()
        
        with transaction() as conn:
            old = conn.execute("SELECT organization_id, risk_category FROM Employee WHERE id=?", (self._id,)).fetchone()
            if old is None:
                raise ValueError("Сотрудник не найден")
            if old['organization_id'] != self.organization_id:
                raise ValueError("Нельзя изменить организацию сотрудника")
            if old['risk_category'] != self.risk_category:
                missing = conn.execute("""SELECT 1 FROM ContractEmployee ce WHERE ce.employee_id=? AND NOT EXISTS
                    (SELECT 1 FROM Payout p WHERE p.contract_id=ce.contract_id AND p.risk_category=?)""", (self._id, self.risk_category)).fetchone()
                if missing:
                    raise ValueError("Для новой категории нет суммы в одном из договоров сотрудника")
                claims = conn.execute("""SELECT ic.amount, p.payout_amount FROM InsuranceClaim ic
                    JOIN Payout p ON p.contract_id=ic.contract_id AND p.risk_category=? WHERE ic.employee_id=?""", (self.risk_category, self._id)).fetchall()
                if any(Decimal(row['amount']) > Decimal(str(row['payout_amount'])) for row in claims):
                    raise ValueError("Новая сумма категории меньше выплаты по страховому случаю")
            cur = conn.execute("UPDATE Employee SET full_name = ?, age = ?, risk_category = ? WHERE id = ?", (self.full_name, self.age, self.risk_category, self._id))
            if cur.rowcount == 0:
                raise ValueError(f"Employee with this id: {self._id} doesn't exist!")

    def delete(self):
        if self._id is None:
            raise ValueError("There is missing id!")

        with transaction() as conn:
            if conn.execute("SELECT 1 FROM ContractEmployee WHERE employee_id=?", (self._id,)).fetchone():
                raise ValueError("Сотрудник включён в договор")
            cur = conn.execute("DELETE FROM Employee WHERE id = ?", (self._id,))
            if cur.rowcount == 0:
                raise ValueError(f"Employee with this id: {self._id} doesn't exist!")
        self._id = None
