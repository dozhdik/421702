import sqlite3
from .database import get_connection

class Agent:
    def __init__(self, full_name: str, passport_details: str, id: int | None = None):
        self._id = id
        self.full_name = full_name
        self.passport_details = passport_details

    @classmethod
    def from_row(cls, row):
        return cls(
            id = row['id'],
            full_name = row['full_name'],
            passport_details = row['passport_details']
        )

    @classmethod
    def get_by_id(cls, id: int):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM Agent WHERE id = ?", (id,)).fetchone()
        finally:
            conn.close()
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_name(cls, full_name: str):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM Agent WHERE full_name = ?", (full_name,)).fetchall()
        finally:
            conn.close()
        return cls.from_row(row) if row else None

    def validate(self):
        for name in ('full_name', 'passport_details'):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"The variable {name} cannot be empty!")

    def add(self):
        if self._id is not None:
            raise ValueError("Agent is already exists!")
        self.validate()

        conn = get_connection()
        try:
            cur = conn.execute("INSERT INTO Agent (full_name, passport_details) VALUES (?, ?)", (self.full_name, self.passport_details))
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
            cur = conn.execute("UPDATE Agent SET full_name = ?, passport_details = ? WHERE id = ?", (self.full_name, self.passport_details, self._id))
            if cur.rowcount == 0:
                raise ValueError(f"Agent with this id: {self._id} doesn't exist!")
            conn.commit()
        finally:
            conn.close()

    def delete(self):
        if self._id is None:
            raise ValueError("There is missing id!")

        conn = get_connection()
        try: 
            cur = conn.execute("DELETE FROM Agent WHERE id = ?", (self._id,))
            if cur.rowcount == 0:
                raise ValueError(f"Agent with this id: {self._id} doesn't exist!")
            conn.commit()
            self._id = None
        finally:
            conn.close()