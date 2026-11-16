import os
import sqlite3
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from models.database import init_database, get_connection
from models.seed import seed_database
from main import list_items, save_item, delete_item
from models.contract import Contract
from models.payout import money
from models.insurance_claim import InsuranceClaim
from models.organization import Organization
from models.employee import Employee
from models.agent import Agent


class InsuranceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("INSURANCE_DB_PATH")
        os.environ["INSURANCE_DB_PATH"] = str(Path(self.temp.name) / "insurance.db")
        init_database()

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("INSURANCE_DB_PATH", None)
        else:
            os.environ["INSURANCE_DB_PATH"] = self.previous
        self.temp.cleanup()

    def test_seed_and_reports(self):
        first = seed_database()
        self.assertEqual(first["contracts"], 5)
        self.assertFalse(any(seed_database().values()))
        self.assertEqual({r["contract_number"] for r in Contract.report_contracts(9001, "2026-11-03")["contracts"]}, {"DEMO-001", "DEMO-002"})
        self.assertEqual(len(Contract.report_agents(9001, "2026-11-03")["agents"]), 1)
        payouts = Contract.report_payouts("2026-11-03", 9001)["payouts"]
        self.assertEqual({(x["contract_number"], x["risk_category"], x["payout_amount"]) for x in payouts if x["risk_category"] == "первая"}, {("DEMO-001", "первая", 10000), ("DEMO-002", "первая", 12000)})
        self.assertEqual(len(Contract.report_payouts("2026-11-03")["payouts"]), 7)
        self.assertEqual(len(Contract.report_contracts(9001, "2026-11-30")["contracts"]), 2)
        self.assertEqual(len(Contract.report_contracts(9001, "2026-12-01")["contracts"]), 1)
        with get_connection() as conn:
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_validation(self):
        for value in ("2026-02-30", "2026-1-01", "hello"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Contract.validate_date(value)
        self.assertEqual(money("0"), "0.00")
        for value in (True, "NaN", "Infinity", "-5", "1.234"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                money(value)

    def test_model_delete_protection_and_category_change(self):
        seed_database()
        org = Organization.get_by_id(1)
        employee = Employee.get_by_id(1)
        with self.assertRaises(ValueError):
            org.delete()
        with self.assertRaises(ValueError):
            employee.delete()
        employee.risk_category = "несуществующая категория"
        with self.assertRaises(ValueError):
            employee.update()
        self.assertEqual(Employee.get_by_id(1).risk_category, "первая")
        agent = Agent("Другой", "DEMO-PASS-001", "123", "Страхование")
        with self.assertRaises(ValueError):
            agent.add()

    def test_contract_transaction_rolls_back_database_error(self):
        seed_database()
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM Contract WHERE contract_number='DEMO-001'").fetchone()
            before = [tuple(r) for r in conn.execute("SELECT employee_id FROM ContractEmployee WHERE contract_id=?", (row['id'],))]
        with self.assertRaises(sqlite3.IntegrityError):
            Contract.save_contract("DEMO-001", row['organization_id'], 999999,
                                   row['conclusion_date'], row['end_date'], [before[0][0]],
                                   {"первая": "10000"}, row['id'])
        with get_connection() as conn:
            after = [tuple(r) for r in conn.execute("SELECT employee_id FROM ContractEmployee WHERE contract_id=?", (row['id'],))]
        self.assertEqual(before, after)

    def test_contract_claim_and_rollback(self):
        seed_database()
        with get_connection() as conn:
            cid = conn.execute("SELECT id FROM Contract WHERE contract_number='DEMO-001'").fetchone()[0]
            emp = conn.execute("SELECT employee_id FROM ContractEmployee WHERE contract_id=? LIMIT 1", (cid,)).fetchone()[0]
            foreign = conn.execute("SELECT id FROM Employee WHERE organization_id=(SELECT id FROM Organization WHERE organization_code=9002) LIMIT 1").fetchone()[0]
            original = dict(conn.execute("SELECT * FROM Contract WHERE id=?", (cid,)).fetchone())
        with self.assertRaises(ValueError):
            Contract.save_contract("X", original["organization_id"], original["agent_id"], "2026-01-01", "2026-12-31", [foreign], {"первая":100}, cid)
        with get_connection() as conn:
            self.assertEqual(dict(conn.execute("SELECT * FROM Contract WHERE id=?", (cid,)).fetchone()), original)
        claim = InsuranceClaim.save_claim(cid, emp, "2026-06-01", "100.25", "Случай")
        with self.assertRaises(ValueError):
            InsuranceClaim.save_claim(cid, emp, "2027-06-01", "100", "Случай")
        with self.assertRaises(ValueError):
            Contract.delete_contract(cid)
        InsuranceClaim.delete_claim(claim)

    def test_individual_and_uniqueness(self):
        seed_database()
        agent = list_items("agents")[0]["id"]
        fields = dict(contract_number="IND-1", full_name="Иванов", agent_id=agent, conclusion_date="2026-01-01", end_date="2026-12-31", amount="10.50")
        item = save_item("individuals", fields)
        self.assertEqual(list_items("individuals")[0]["id"], item)
        fields["contract_number"] = "DEMO-001"
        with self.assertRaises(ValueError):
            save_item("individuals", fields)
        delete_item("individuals", item)
        self.assertEqual(list_items("individuals"), [])

    def test_empty(self):
        self.assertEqual(Contract.report_contracts(1,"2026-01-01")["contracts"], [])
        self.assertEqual(Contract.report_agents(1,"2026-01-01")["agents"], [])
        self.assertEqual(Contract.report_payouts("2026-01-01")["payouts"], [])

    def test_crud_and_persistence(self):
        org = dict(organization_code=10, full_name="Тест", brief_name="Т", address="Адрес", bank_details="Банк", specialization="Учёба")
        oid = save_item("organizations", org)
        agent = dict(full_name="Агент", passport_details="TEST", phone_number="123", insurance_company="Компания")
        aid = save_item("agents", agent)
        employee = dict(organization_id=oid, full_name="Сотрудник", age=30, risk_category="первая")
        eid = save_item("employees", employee)
        employee["age"] = 31
        save_item("employees", employee, eid)
        self.assertEqual(list_items("employees")[0]["age"], 31)
        with self.assertRaises(ValueError):
            save_item("agents", agent)
        with self.assertRaises(ValueError):
            delete_item("organizations", oid)
        cid = Contract.save_contract("T-1", oid, aid, "2026-01-01", "2026-12-31", [eid], {"первая": "123.45"})
        self.assertEqual(len(Contract.report_contracts(10, "2026-01-01")["contracts"]), 1)
        self.assertEqual(Contract.report_contracts(10, "2025-12-31")["contracts"], [])
        Contract.delete_contract(cid)
        delete_item("employees", eid)
        delete_item("agents", aid)
        delete_item("organizations", oid)
        self.assertEqual(list_items("organizations"), [])

    def test_console_invalid_input_and_cancel_delete(self):
        seed_database()
        commands = "99\n6\n9001\n2026-02-30\n1\n4\n1\nнет\n0\n0\n"
        result = subprocess.run([sys.executable, "main.py"], input=commands, text=True,
                                capture_output=True, env=os.environ.copy(), timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Неизвестный пункт меню", result.stdout)
        self.assertIn("Ошибка:", result.stdout)
        self.assertIn("Удаление отменено", result.stdout)
        self.assertEqual(len(list_items("organizations")), 3)
        self.assertNotIn("Traceback", result.stderr)

    def test_console_eof(self):
        result = subprocess.run([sys.executable, "main.py"], input="", text=True,
                                capture_output=True, env=os.environ.copy(), timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn("До свидания", result.stdout)

    def test_console_contract_and_zero_payout(self):
        seed_database()
        commands = "4\n2\n1\nTEST-CLI\n1\n2026-01-01\n2026-12-31\n1\n0\n0\n8\n9001\n2026-06-01\n0\n"
        result = subprocess.run([sys.executable, "main.py"], input=commands, text=True,
                                capture_output=True, env=os.environ.copy(), timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Договор сохранён", result.stdout)
        self.assertIn("Договор: TEST-CLI | Категория: первая | Сумма: 0.0", result.stdout)
        self.assertNotIn("Ошибка:", result.stdout)


if __name__ == "__main__":
    unittest.main()
