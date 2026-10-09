import sqlite3
from database import get_connection

class Organization:
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
        if not isinstance(self.organization_code, int):
            raise ValueError("Incorrect data type!")
        for name in ("full_name", "brief_name", "address", "bank_details", "specialization"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"The variable {name} cannot be empty!")

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
            conn.execute('''UPDATE Organization SET organization_code = ?, full_name = ?, brief_name = ?, address = ?, bank_details = ?, specialization = ?
                WHERE id = ?''', (self.organization_code, self.full_name, self.brief_name, self.address, self.bank_details, self.specialization, self._id))
            if conn.rowcount == 0:
                raise ValueError(f"Organization with this id: {self._id} doesn't exist!")
            conn.commit()
        finally:
            conn.close()