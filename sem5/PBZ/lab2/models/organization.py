import sqlite3
from .database import get_connection, transaction, records
from .validation import required_text

class Organization:
    @staticmethod
    def list_all():
        return records("SELECT * FROM Organization ORDER BY id")

    def __init__(self, organization_code: int, full_name: str, brief_name: str, address: str, bank_details: str, specialization: str, id: int | None = None):
        self._id = id
        self.organization_code = organization_code
        self.full_name = full_name
        self.brief_name = brief_name
        self.address = address
        self.bank_details = bank_details
        self.specialization = specialization

    @classmethod
    def from_row(cls, row):
        return cls(
            id = row['id'],
            organization_code = row['organization_code'],
            full_name = row['full_name'],
            brief_name = row['brief_name'],
            address = row['address'],
            bank_details = row['bank_details'],
            specialization = row['specialization']
        )

    @classmethod
    def get_by_id(cls, id: int):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM Organization WHERE id = ?", (id,)).fetchone()
        finally:
            conn.close()
        return cls.from_row(row) if row else None

    def validate(self):
        if type(self.organization_code) is not int or self.organization_code <= 0:
            raise ValueError("Incorrect data type!")
        for name in ("full_name", "brief_name", "address", "bank_details", "specialization"):
            setattr(self, name, required_text(getattr(self, name), name))
        conn = get_connection()
        try:
            if conn.execute("SELECT 1 FROM Organization WHERE full_name=? AND id!=?", (self.full_name, self._id or 0)).fetchone():
                raise ValueError("Организация с таким названием уже существует")
        finally:
            conn.close()

    def add(self):
        if self._id is not None:
            raise ValueError("Organization is already exists!")
        self.validate()

        conn = get_connection()
        try:
            cur = conn.execute('''INSERT INTO Organization (organization_code, full_name, brief_name, address, bank_details, specialization)
                VALUES (?, ?, ?, ?, ?, ?)''', (self.organization_code, self.full_name, self.brief_name, self.address, self.bank_details, self.specialization))
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
            cur = conn.execute('''UPDATE Organization SET organization_code = ?, full_name = ?, brief_name = ?, address = ?, bank_details = ?, specialization = ?
                WHERE id = ?''', (self.organization_code, self.full_name, self.brief_name, self.address, self.bank_details, self.specialization, self._id))
            if cur.rowcount == 0:
                raise ValueError(f"Organization with this id: {self._id} doesn't exist!")
            conn.commit()
        finally:
            conn.close()

    def delete(self):
        if self._id is None:
            raise ValueError("There is missing id!")
        
        with transaction() as conn:
            if conn.execute("SELECT 1 FROM Employee WHERE organization_id=?", (self._id,)).fetchone() or conn.execute("SELECT 1 FROM Contract WHERE organization_id=?", (self._id,)).fetchone():
                raise ValueError("Организация связана с сотрудниками или договорами")
            cur = conn.execute('''DELETE FROM Organization WHERE id = ?''', (self._id,))
            if cur.rowcount == 0:
                raise ValueError(f"Organization with this id: {self._id} doesn't exist!")
        self._id = None
