import sqlite3
from .database import get_connection

class Employee:
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
        
        conn = get_connection()
        try:
            cur = conn.execute("UPDATE Employee SET full_name = ?, age = ?, risk_category = ? WHERE id = ?", (self.full_name, self.age, self.risk_category, self._id))
            if cur.rowcount == 0:
                raise ValueError(f"Employee with this id: {self._id} doesn't exist!")
            conn.commit()
        finally:
            conn.close()

    def delete(self):
        if self._id is None:
            raise ValueError("There is missing id!")

        conn = get_connection()
        try:
            cur = conn.execute("DELETE FROM Employee WHERE id = ?", (self._id,))
            if cur.rowcount == 0:
                raise ValueError(f"Employee with this id: {self._id} doesn't exist!")
            conn.commit()
            self._id = None
        finally:
            conn.close()