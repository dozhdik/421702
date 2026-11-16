from .contract import Contract
from .database import records, transaction
from .payout import money


class IndividualContract:
    @staticmethod
    def list_all():
        return records("SELECT * FROM IndividualContract ORDER BY id")

    @staticmethod
    def save(values, item_id=None):
        fields = ("contract_number", "full_name", "agent_id", "conclusion_date", "end_date", "amount")
        data = {}
        for field in fields:
            value = str(values.get(field, "")).strip()
            if not value:
                raise ValueError(f"Заполните поле {field}")
            data[field] = value
        try:
            data["agent_id"] = int(data["agent_id"])
            if data["agent_id"] <= 0:
                raise ValueError()
        except ValueError:
            raise ValueError("ID агента должен быть положительным числом") from None
        Contract.validate_date(data["conclusion_date"])
        Contract.validate_date(data["end_date"])
        if data["conclusion_date"] > data["end_date"]:
            raise ValueError("Дата окончания раньше даты начала")
        data["amount"] = money(data["amount"])
        with transaction() as conn:
            if conn.execute("SELECT 1 FROM Contract WHERE contract_number=?", (data["contract_number"],)).fetchone():
                raise ValueError("Номер уже используется коллективным договором")
            params = tuple(data[field] for field in fields)
            if item_id is None:
                return conn.execute("""INSERT INTO IndividualContract
                    (contract_number,full_name,agent_id,conclusion_date,end_date,amount)
                    VALUES (?,?,?,?,?,?)""", params).lastrowid
            cur = conn.execute("""UPDATE IndividualContract SET contract_number=?,full_name=?,agent_id=?,
                conclusion_date=?,end_date=?,amount=? WHERE id=?""", (*params, item_id))
            if not cur.rowcount:
                raise ValueError("Запись не найдена")
            return item_id

    @staticmethod
    def delete(item_id):
        with transaction() as conn:
            if not conn.execute("DELETE FROM IndividualContract WHERE id=?", (item_id,)).rowcount:
                raise ValueError("Запись не найдена")
