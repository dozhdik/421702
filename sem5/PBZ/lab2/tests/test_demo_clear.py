import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from models.database import clear_database, get_connection, init_database
from models.seed import seed_database
from models import demo_data
from models.contract import Contract
from ui.app import App, is_clear_phrase


class DemoAndClearTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = os.environ.get("INSURANCE_DB_PATH")
        os.environ["INSURANCE_DB_PATH"] = str(Path(self.temp.name) / "insurance.db")
        init_database()

    def tearDown(self):
        if self.old_path is None:
            os.environ.pop("INSURANCE_DB_PATH", None)
        else:
            os.environ["INSURANCE_DB_PATH"] = self.old_path
        self.temp.cleanup()

    def test_demo_integrity_repeat_and_reports(self):
        counts = seed_database()
        for field, expected in (("organizations", 30), ("agents", 40), ("employees", 250),
                                ("contracts", 100), ("individual_contracts", 40), ("claims", 120)):
            self.assertEqual(counts[field], expected)
        self.assertTrue(all(value == 0 for value in seed_database().values()))
        conn = get_connection()
        try:
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            mismatches = conn.execute("""SELECT count(*) FROM ContractEmployee ce
                JOIN Contract c ON c.id=ce.contract_id JOIN Employee e ON e.id=ce.employee_id
                WHERE c.organization_id != e.organization_id""").fetchone()[0]
            self.assertEqual(mismatches, 0)
            missing = conn.execute("""SELECT count(*) FROM ContractEmployee ce
                JOIN Employee e ON e.id=ce.employee_id WHERE NOT EXISTS
                (SELECT 1 FROM Payout p WHERE p.contract_id=ce.contract_id
                 AND p.risk_category=e.risk_category)""").fetchone()[0]
            self.assertEqual(missing, 0)
            invalid = conn.execute("""SELECT count(*) FROM InsuranceClaim ic
                JOIN Contract c ON c.id=ic.contract_id JOIN Employee e ON e.id=ic.employee_id
                LEFT JOIN ContractEmployee ce ON ce.contract_id=ic.contract_id AND ce.employee_id=ic.employee_id
                LEFT JOIN Payout p ON p.contract_id=ic.contract_id AND p.risk_category=e.risk_category
                WHERE ce.employee_id IS NULL OR p.id IS NULL OR ic.claim_date<c.conclusion_date
                   OR ic.claim_date>c.end_date OR CAST(ic.amount AS REAL)>p.payout_amount""").fetchone()[0]
            self.assertEqual(invalid, 0)
        finally:
            conn.close()
        self.assertEqual(len(Contract.report_contracts(9001, "2026-11-03")["contracts"]), 2)
        self.assertEqual(len(Contract.report_agents(9001, "2026-11-03")["agents"]), 1)
        self.assertEqual(len(Contract.report_payouts("2026-11-03", 9001)["payouts"]), 5)
        self.assertEqual(Contract.report_payouts("2035-01-01")["payouts"], [])
        self.assertTrue(Contract.report_payouts("2027-06-01")["payouts"])

    def test_clear_atomic_schema_and_reseed(self):
        seed_database()
        conn = get_connection()
        try:
            conn.execute("CREATE TABLE ExtraParent (id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE ExtraChild (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES ExtraParent(id))")
            conn.execute("INSERT INTO ExtraParent VALUES (1)")
            conn.execute("INSERT INTO ExtraChild VALUES (1, 1)")
            conn.commit()
            schema_before = conn.execute("SELECT count(*) FROM sqlite_master WHERE type IN ('table','index')").fetchone()[0]
        finally:
            conn.close()
        clear_database()
        conn = get_connection()
        try:
            self.assertEqual(conn.execute("SELECT count(*) FROM ExtraChild").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT count(*) FROM Organization").fetchone()[0], 0)
            for table in ("Employee", "Agent", "Contract", "ContractEmployee", "Payout",
                          "IndividualContract", "InsuranceClaim", "ExtraParent"):
                self.assertEqual(conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT count(*) FROM sqlite_master WHERE type IN ('table','index')").fetchone()[0], schema_before)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            conn.close()
        init_database()
        self.assertEqual(Contract.report_payouts("2026-11-03")["payouts"], [])
        result = subprocess.run([sys.executable, "-c", "from models.database import init_database, records; init_database(); print(len(records('SELECT id FROM Organization')))"] , capture_output=True, text=True, env=os.environ.copy(), timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "0")
        self.assertEqual(seed_database()["contracts"], 100)

    def test_seed_skips_conflicts_and_preserves_user_data(self):
        conn = get_connection()
        try:
            conn.execute("""INSERT INTO Organization
                (organization_code,full_name,brief_name,address,bank_details,specialization)
                VALUES (9100,'Своя организация','Своя','Адрес','Банк','Дело')""")
            conn.commit()
        finally:
            conn.close()

        counts = seed_database()
        self.assertGreater(counts["organizations"], 0)
        conn = get_connection()
        try:
            row = conn.execute("SELECT full_name FROM Organization WHERE organization_code=9100").fetchone()
            self.assertEqual(row[0], "Своя организация")
            self.assertEqual(conn.execute("SELECT count(*) FROM Employee WHERE organization_id=(SELECT id FROM Organization WHERE organization_code=9100)").fetchone()[0], 0)
            conn.execute("UPDATE Organization SET organization_code=8001 WHERE organization_code=9100")
            conn.commit()
        finally:
            conn.close()
        seed_database()
        self.assertEqual(seed_database()["organizations"], 0)
        conn = get_connection()
        try:
            self.assertEqual(conn.execute("SELECT full_name FROM Organization WHERE organization_code=8001").fetchone()[0], "Своя организация")
        finally:
            conn.close()

    def test_legacy_demo_seed_is_not_duplicated(self):
        legacy_organizations = tuple(
            (f"Белорусское предприятие «Орион-{index + 1:02d}»", f"Орион-{index + 1:02d}", "услуги")
            for index in range(27)
        )
        with patch.object(demo_data, "ORGANIZATIONS", legacy_organizations), patch.object(
            demo_data, "person", demo_data.legacy_person
        ), patch.object(demo_data, "agent_passport", lambda index: f"DEMO-AGENT-{index+1:03d}"):
            seed_database()
        self.assertTrue(all(value == 0 for value in seed_database().values()))
        conn = get_connection()
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM Employee").fetchone()[0], 250)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM Contract").fetchone()[0], 100)
        finally:
            conn.close()

    def test_clear_rolls_back_on_trigger_error(self):
        seed_database()
        conn = get_connection()
        try:
            sequences_before = conn.execute("SELECT name,seq FROM sqlite_sequence ORDER BY name").fetchall()
            conn.execute("""CREATE TRIGGER prevent_agent_delete BEFORE DELETE ON Agent
                BEGIN SELECT RAISE(ABORT, 'blocked'); END""")
            conn.commit()
        finally:
            conn.close()
        with self.assertRaises(sqlite3.IntegrityError):
            clear_database()
        conn = get_connection()
        try:
            self.assertEqual(conn.execute("SELECT count(*) FROM Organization").fetchone()[0], 30)
            self.assertEqual(conn.execute("SELECT count(*) FROM InsuranceClaim").fetchone()[0], 120)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual([tuple(row) for row in conn.execute("SELECT name,seq FROM sqlite_sequence ORDER BY name")],
                             [tuple(row) for row in sequences_before])
        finally:
            conn.close()

    def test_clear_confirmation_flow(self):
        app = Mock()
        clear = app.tenant.clear_data
        with patch("ui.app.messagebox.showinfo"):
            app.confirm_clear_warning.return_value = False
            App.request_clear(app)
            app.confirm_clear_phrase.assert_not_called()
            clear.assert_not_called()
            app.confirm_clear_warning.return_value = True
            app.confirm_clear_phrase.return_value = False
            App.request_clear(app)
            clear.assert_not_called()
            app.confirm_clear_phrase.return_value = True
            app.guard.side_effect = lambda action: action()
            app.report_tree.get_children.return_value = ()
            App.request_clear(app)
            clear.assert_called_once_with()
        for value in ("", "удалить всё", "УДАЛИТЬ ВСЕ", " УДАЛИТЬ ВСЁ", "УДАЛИТЬ ВСЁ "):
            self.assertFalse(is_clear_phrase(value))
        self.assertTrue(is_clear_phrase("УДАЛИТЬ ВСЁ"))


if __name__ == "__main__":
    unittest.main()
