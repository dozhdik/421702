import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from main import run_sessions
from models.company_seed import seed_company
from models.database import clear_database, get_connection, init_database
from models.seed import seed_database
from models.tenant import authenticate, register_company


class CompanySeedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("INSURANCE_DB_PATH")
        os.environ["INSURANCE_DB_PATH"] = str(Path(self.temp.name) / "insurance.db")
        init_database()
        seed_database()

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("INSURANCE_DB_PATH", None)
        else:
            os.environ["INSURANCE_DB_PATH"] = self.previous
        self.temp.cleanup()

    def test_seed_affects_only_selected_company_and_is_repeatable(self):
        company = authenticate("БелСтрах", "1234")
        other = authenticate("Надёжный полис", "1234")
        before = (other.organizations(), other.agents(), other.employees(), other.contracts(),
                  other.individual_contracts(), other.claims())
        counts = seed_company(company.name)
        self.assertEqual(counts["organizations"], 3)
        self.assertEqual(counts["agents"], 3)
        self.assertEqual(counts["contracts"], 6)
        self.assertEqual(counts["individual_contracts"], 3)
        self.assertEqual(counts["claims"], 6)
        self.assertTrue(all(value == 0 for value in seed_company(company.name).values()))
        self.assertEqual(before, (other.organizations(), other.agents(), other.employees(),
                                  other.contracts(), other.individual_contracts(), other.claims()))
        self.assertTrue(any(row["contract_number"].startswith("КД-") for row in company.report_contracts("2026-06-01")))
        with get_connection() as conn:
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            other_count = conn.execute("SELECT count(*) FROM Agent WHERE insurance_company=?", ("Надёжный полис",)).fetchone()[0]
        self.assertEqual(other_count, len(other.agents()))

    def test_new_company_can_fill_samples(self):
        conn = get_connection()
        try:
            conn.execute("INSERT INTO Agent(full_name,passport_details,phone_number,insurance_company) VALUES (?,?,?,?)",
                         ("Петров Иван Сергеевич", "ID0000001", "+375291234567", "Моя страховая"))
            conn.commit()
        finally:
            conn.close()
        counts = seed_company("Моя страховая")
        self.assertEqual(counts["contracts"], 6)
        self.assertEqual(len(authenticate("Моя страховая", "1234").individual_contracts()), 3)
        self.assertTrue(all(value == 0 for value in seed_company("Моя страховая").values()))
        with self.assertRaises(ValueError):
            seed_company("Несуществующая")

    def test_full_clear_resets_autoincrement(self):
        clear_database()
        seed_database()
        conn = get_connection()
        try:
            for table in ("Organization", "Employee", "Agent", "Contract", "Payout", "IndividualContract", "InsuranceClaim"):
                self.assertEqual(conn.execute(f'SELECT min(id) FROM "{table}"').fetchone()[0], 1, table)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            conn.close()

    def test_logout_reopens_login_and_window_close_exits(self):
        first_login = Mock(tenant="first")
        second_login = Mock(tenant="second")
        first_app = Mock(logout_requested=True)
        second_app = Mock(logout_requested=False)
        login_class = Mock(side_effect=[first_login, second_login])
        app_class = Mock(side_effect=[first_app, second_app])
        run_sessions(login_class, app_class)
        self.assertEqual(login_class.call_count, 2)
        self.assertEqual([call.args[0] for call in app_class.call_args_list], ["first", "second"])

    def test_cancel_login_exits_without_opening_session(self):
        login_class = Mock(return_value=Mock(tenant=None))
        app_class = Mock()
        run_sessions(login_class, app_class)
        app_class.assert_not_called()

    def test_register_company_without_agent_and_seed_after_login(self):
        registered = register_company("Новая страховая", "1234")
        self.assertEqual(authenticate("Новая страховая", "1234").name, registered.name)
        self.assertEqual(registered.agents(), [])
        with self.assertRaises(ValueError):
            register_company("Новая страховая", "1234")
        with self.assertRaises(ValueError):
            register_company("Ещё одна", "неверный пароль")
        self.assertEqual(seed_company(registered.name)["contracts"], 6)

    def test_clear_company_preserves_other_company_and_login(self):
        company = authenticate("БелСтрах", "1234")
        other = authenticate("Надёжный полис", "1234")
        before = (other.organizations(), other.agents(), other.employees(), other.contracts(),
                  other.individual_contracts(), other.claims())
        company.clear_data()
        self.assertEqual(company.agents(), [])
        self.assertEqual(company.contracts(), [])
        self.assertEqual(company.claims(), [])
        self.assertEqual(company.individual_contracts(), [])
        self.assertEqual(before, (other.organizations(), other.agents(), other.employees(), other.contracts(),
                                  other.individual_contracts(), other.claims()))
        self.assertEqual(authenticate("БелСтрах", "1234").name, "БелСтрах")
        self.assertEqual(seed_company("БелСтрах")["contracts"], 6)
        conn = get_connection()
        try:
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
