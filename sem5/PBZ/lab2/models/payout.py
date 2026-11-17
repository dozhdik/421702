import sqlite3
from .database import get_connection
from decimal import Decimal, InvalidOperation
from .validation import required_text

class Payout:
    def __init__(self, contract_id: int, risk_category: str, payout_amount: float | int, id: int | None = None):
        self._id = id
        self._contract_id = contract_id  
        self.risk_category = risk_category
        self.payout_amount = payout_amount

    @property
    def contract_id(self):
        return self._contract_id

    @classmethod
    def from_row(cls, row):
        return cls(
            id = row['id'],
            contract_id = row['contract_id'],
            risk_category = row['risk_category'],
            payout_amount = row['payout_amount']
        )

    @classmethod
    def get_by_id(cls, id: int):
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM Payout WHERE id = ?", (id,)).fetchone()
        finally:
            conn.close()
        return cls.from_row(row) if row else None

    def validate(self):
        if type(self._contract_id) is not int or self._contract_id <= 0:
            raise ValueError("Incorrect data type")

        self.risk_category = required_text(self.risk_category, "категория риска")

        try:
            if isinstance(self.payout_amount, bool):
                raise ValueError()
            amount = Decimal(str(self.payout_amount))
            if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
                raise ValueError()
        except (InvalidOperation, ValueError):
            raise ValueError("Incorrect payout amount") from None

    def add(self):
        if self._id is not None:
            raise ValueError("Payout category already exists")  
        self.validate()
        conn = get_connection()

        try:
            row = conn.execute("SELECT id FROM Contract where id = ?", (self._contract_id,)).fetchone()
            if row is None: 
                raise ValueError("There isn't any contract to payout")
            cur = conn.execute("INSERT INTO Payout (contract_id, risk_category, payout_amount) VALUES (?, ?, ?)", (self._contract_id, self.risk_category, self.payout_amount))
            conn.commit()
            self._id = cur.lastrowid
        finally:
            conn.close()

    def update(self):
        if self._id is None: 
            raise ValueError("There is empty record")
        self.validate()
        conn = get_connection()

        try:
            cur = conn.execute("UPDATE Payout SET risk_category = ?, payout_amount = ? WHERE id = ?", (self.risk_category, self.payout_amount, self._id))
            if cur.rowcount == 0:
                raise ValueError(f"Payout with this id: {self._id} doesn't exist")
            conn.commit()
        finally:
            conn.close()

    def delete(self):
        if self._id is None:
            raise ValueError("There is nothing to delete")
        conn = get_connection()

        try:
            cur = conn.execute("DELETE FROM Payout WHERE id = ?", (self._id,))
            if cur.rowcount == 0:
                raise ValueError(f"Payout with this id: {self._id} doesn't exist")
            conn.commit()
            self._id = None 
        finally:
            conn.close()


def money(value):
    try:
        if isinstance(value, bool):
            raise ValueError()
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValueError()
        return format(amount, ".2f")
    except (InvalidOperation, ValueError):
        raise ValueError("Сумма должна быть неотрицательной, с точностью до двух знаков") from None
