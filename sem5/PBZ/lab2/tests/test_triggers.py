import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from models.database import get_connection, init_database
from models.seed import seed_database
from models.contract import Contract


class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old_path = os.environ.get("INSURANCE_DB_PATH")
        os.environ["INSURANCE_DB_PATH"] = str(Path(self.directory.name) / "test.db")
        init_database()
        seed_database()
        self.conn = get_connection()

    def tearDown(self):
        self.conn.close()
        if self.old_path is None:
            os.environ.pop("INSURANCE_DB_PATH", None)
        else:
            os.environ["INSURANCE_DB_PATH"] = self.old_path
        self.directory.cleanup()

    def test_employee_contract_link_insert_and_update(self):
        contract_id = self.conn.execute("SELECT id FROM Contract WHERE contract_number='КД-0001'").fetchone()[0]
        foreign_id = self.conn.execute("""SELECT id FROM Employee WHERE organization_id !=
            (SELECT organization_id FROM Contract WHERE id=?) LIMIT 1""", (contract_id,)).fetchone()[0]
        existing_id = self.conn.execute("SELECT employee_id FROM ContractEmployee WHERE contract_id=? LIMIT 1", (contract_id,)).fetchone()[0]
        for sql, args in (
            ("INSERT INTO ContractEmployee(contract_id,employee_id) VALUES (?,?)", (contract_id, foreign_id)),
            ("UPDATE ContractEmployee SET employee_id=? WHERE contract_id=? AND employee_id=?", (foreign_id, contract_id, existing_id)),
        ):
            with self.subTest(sql=sql), self.assertRaisesRegex(sqlite3.IntegrityError, "другой организации"):
                self.conn.execute(sql, args)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM ContractEmployee WHERE contract_id=? AND employee_id=?",
                                           (contract_id, foreign_id)).fetchone()[0], 0)

    def test_organization_changes_cannot_break_existing_links(self):
        row = self.conn.execute("""SELECT ce.contract_id,ce.employee_id,c.organization_id
            FROM ContractEmployee ce JOIN Contract c ON c.id=ce.contract_id LIMIT 1""").fetchone()
        other = self.conn.execute("SELECT id FROM Organization WHERE id!=? LIMIT 1", (row["organization_id"],)).fetchone()[0]
        with self.assertRaisesRegex(sqlite3.IntegrityError, "другой организации"):
            self.conn.execute("UPDATE Employee SET organization_id=? WHERE id=?", (other, row["employee_id"]))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "другой организации"):
            self.conn.execute("UPDATE Contract SET organization_id=? WHERE id=?", (other, row["contract_id"]))

    def test_dates_and_agent_company(self):
        row = self.conn.execute("SELECT * FROM Contract WHERE contract_number='КД-0001'").fetchone()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "Дата окончания"):
            self.conn.execute("""INSERT INTO Contract(contract_number,organization_id,agent_id,conclusion_date,end_date)
                VALUES ('TEST-DATE',?,?,?,?)""", (row["organization_id"], row["agent_id"], "2027-01-01", "2026-01-01"))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "Дата окончания"):
            self.conn.execute("UPDATE Contract SET end_date='2020-01-01' WHERE id=?", (row["id"],))
        individual = self.conn.execute("SELECT id,agent_id FROM IndividualContract LIMIT 1").fetchone()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "Дата окончания"):
            self.conn.execute("""INSERT INTO IndividualContract
                (contract_number,full_name,agent_id,conclusion_date,end_date,amount)
                VALUES ('TEST-IND','Иванов',?,'2027-01-01','2026-01-01','100')""", (individual["agent_id"],))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "Дата окончания"):
            self.conn.execute("UPDATE IndividualContract SET end_date='2000-01-01' WHERE id=?", (individual["id"],))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "страховую компанию"):
            self.conn.execute("UPDATE Agent SET insurance_company='Чужая компания' WHERE id=?", (row["agent_id"],))

    def test_existing_application_operations_still_work(self):
        row = self.conn.execute("SELECT * FROM Contract WHERE contract_number='КД-0001'").fetchone()
        employees = [r[0] for r in self.conn.execute("SELECT employee_id FROM ContractEmployee WHERE contract_id=?", (row["id"],))]
        payouts = {r[0]: r[1] for r in self.conn.execute("SELECT risk_category,payout_amount FROM Payout WHERE contract_id=?", (row["id"],))}
        self.conn.close()
        Contract.save_contract(row["contract_number"], row["organization_id"], row["agent_id"],
                               row["conclusion_date"], row["end_date"], employees, payouts, row["id"])
        self.conn = get_connection()
        init_database()
        self.assertEqual(self.conn.execute("PRAGMA foreign_key_check").fetchall(), [])


if __name__ == "__main__":
    unittest.main()
