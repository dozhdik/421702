from decimal import Decimal

from .database import transaction
from .contract import Contract
from .payout import money
from .validation import required_text


class InsuranceClaim:
    @staticmethod
    def save_claim(contract_id, employee_id, claim_date, amount, description, claim_id=None):
        Contract.validate_date(claim_date)
        amount = money(amount)
        description = required_text(description, "описание")
        with transaction() as conn:
            row = conn.execute("""SELECT c.conclusion_date, c.end_date, p.payout_amount
                FROM Contract c JOIN ContractEmployee ce ON ce.contract_id=c.id
                JOIN Employee e ON e.id=ce.employee_id
                JOIN Payout p ON p.contract_id=c.id AND p.risk_category=e.risk_category
                WHERE c.id=? AND e.id=?""", (contract_id, employee_id)).fetchone()
            if not row:
                raise ValueError("Сотрудник не застрахован по договору или нет суммы для его категории")
            if not row["conclusion_date"] <= claim_date <= row["end_date"]:
                raise ValueError("Дата случая вне срока действия договора")
            if Decimal(amount) > Decimal(str(row["payout_amount"])):
                raise ValueError("Выплата превышает сумму по категории")
            if claim_id is None:
                return conn.execute("INSERT INTO InsuranceClaim(contract_id,employee_id,claim_date,amount,description) VALUES (?,?,?,?,?)", (contract_id, employee_id, claim_date, amount, description)).lastrowid
            cur = conn.execute("UPDATE InsuranceClaim SET contract_id=?,employee_id=?,claim_date=?,amount=?,description=? WHERE id=?", (contract_id,employee_id,claim_date,amount,description,claim_id))
            if not cur.rowcount:
                raise ValueError("Страховой случай не найден")
            return claim_id

    @staticmethod
    def delete_claim(claim_id):
        with transaction() as conn:
            if not conn.execute("DELETE FROM InsuranceClaim WHERE id=?", (claim_id,)).rowcount:
                raise ValueError("Страховой случай не найден")

