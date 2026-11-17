import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from models.database import get_connection, init_database
from models.seed import seed_database
from models.tenant import authenticate, register_company
from models.validation import phone_number, required_text
from ui.app import App


class TenantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_path = os.environ.get("INSURANCE_DB_PATH")
        os.environ["INSURANCE_DB_PATH"] = str(Path(self.temp.name) / "insurance.db")
        init_database()
        seed_database()

    def tearDown(self):
        if self.old_path is None:
            os.environ.pop("INSURANCE_DB_PATH", None)
        else:
            os.environ["INSURANCE_DB_PATH"] = self.old_path
        self.temp.cleanup()

    def test_authentication_and_tenant_filter(self):
        first = authenticate("БелСтрах", "1234")
        other = authenticate("Надёжный полис", "1234")
        with self.assertRaises(ValueError):
            authenticate("БелСтрах", "12345")
        with self.assertRaises(ValueError):
            authenticate("Нет такой организации", "1234")
        self.assertTrue(first.organizations())
        self.assertTrue(all(r["insurance_company"] == "БелСтрах" for r in first.agents()))
        self.assertTrue(all(r["id"] not in {c["id"] for c in other.contracts()} for r in first.contracts()))
        own_ids = {r["id"] for r in first.employees()}
        foreign = next(r["id"] for r in other.employees() if r["id"] not in own_ids)
        with self.assertRaises(ValueError):
            first.require_employee(foreign)
        with self.assertRaises(ValueError):
            first.require_contract(other.contracts()[0]["id"])
        with self.assertRaises(ValueError):
            first.require_agent(other.agents()[0]["id"])
        with self.assertRaises(ValueError):
            first.require_individual(other.individual_contracts()[0]["id"])
        with self.assertRaises(ValueError):
            first.require_claim(other.claims()[0]["id"])
        self.assertTrue(all(r["contract_id"] in {c["id"] for c in first.contracts()} for r in first.claims()))

    def test_company_crud_before_contract_and_isolation(self):
        company = register_company('Новая страховая', '1234')
        other = authenticate('БелСтрах', '1234')
        organization = dict(organization_code=99981, full_name='ООО Горизонт', brief_name='Горизонт',
                            address='Минск, ул. Лесная, 5', bank_details='BY123456', specialization='Торговля')
        org_id = company.save_organization(organization)
        employee = dict(organization_id=org_id, full_name='Иванов Иван Иванович', age=32, risk_category='Первая')
        emp_id = company.save_employee(employee)
        self.assertIn(org_id, {r['id'] for r in company.organizations()})
        self.assertIn(emp_id, {r['id'] for r in company.employees_for_organization(org_id)})
        self.assertNotIn(org_id, {r['id'] for r in other.organizations()})
        self.assertNotIn(emp_id, {r['id'] for r in other.employees()})
        with self.assertRaises(ValueError):
            other.save_employee(employee, emp_id)
        organization['address'] = 'Минск, ул. Лесная, 7'
        company.save_organization(organization, org_id)
        employee['age'] = 33
        company.save_employee(employee, emp_id)
        self.assertEqual(company.organizations()[0]['address'], organization['address'])
        self.assertEqual(company.employees()[0]['age'], 33)
        with self.assertRaises(ValueError):
            company.delete_organization(org_id)
        company.delete_employee(emp_id)
        company.delete_organization(org_id)
        self.assertEqual(company.organizations(), [])

    def test_clear_includes_unattached_records(self):
        company = register_company('Страхование города', '1234')
        org_id = company.save_organization(dict(organization_code=99982, full_name='ООО Заря',
            brief_name='Заря', address='Минск', bank_details='BY123456', specialization='Торговля'))
        employee_id = company.save_employee(dict(organization_id=org_id, full_name='Петров Пётр Петрович',
                                                 age=40, risk_category='Вторая'))
        company.clear_data()
        self.assertEqual(authenticate(company.name, '1234').organizations(), [])
        with get_connection() as conn:
            self.assertIsNone(conn.execute('SELECT id FROM Employee WHERE id=?', (employee_id,)).fetchone())
            self.assertIsNone(conn.execute('SELECT id FROM Organization WHERE id=?', (org_id,)).fetchone())

    def test_shared_records_cannot_be_modified(self):
        first = authenticate('БелСтрах', '1234')
        other = authenticate('Надёжный полис', '1234')
        shared = next(row for row in first.organizations() if row['id'] in {r['id'] for r in other.organizations()})
        values = {k: v for k, v in shared.items() if k != 'id'}
        with self.assertRaisesRegex(ValueError, 'другой страховой'):
            first.save_organization(values, shared['id'])
        with self.assertRaisesRegex(ValueError, 'другой страховой'):
            first.delete_organization(shared['id'])

    def test_same_organization_does_not_leak_other_insurer_contracts(self):
        with get_connection() as conn:
            conn.execute("UPDATE Contract SET conclusion_date='2026-01-01',end_date='2026-12-31' WHERE contract_number='КД-0003'")
            conn.commit()
        first = authenticate("БелСтрах", "1234")
        other = authenticate("Надёжный полис", "1234")
        first_rows = first.report_contracts("2026-11-03", 9001)
        other_rows = other.report_contracts("2026-11-03", 9001)
        self.assertEqual({r["contract_number"] for r in first_rows}, {"КД-0001", "КД-0002"})
        self.assertEqual({r["contract_number"] for r in other_rows}, {"КД-0003"})
        self.assertEqual({r["contract_number"] for r in other.report_payouts("2026-11-03", 9001)}, {"КД-0003"})
        self.assertEqual(len(first.report_agents("2026-11-03", 9001)), 1)
        self.assertTrue(all(r["agent_id"] in {a["id"] for a in first.agents()} for r in first.individual_contracts()))

    def test_formats_and_new_demo_data(self):
        self.assertEqual(phone_number("+375 (29) 123-45-67"), "+375291234567")
        self.assertEqual(required_text("  Иванов   Иван Иванович ", "ФИО"), "Иванов Иван Иванович")
        with self.assertRaises(ValueError):
            phone_number("123")
        with self.assertRaises(ValueError):
            required_text("DEMO-01", "номер")
        with get_connection() as conn:
            for table, column in (("Contract", "contract_number"), ("IndividualContract", "contract_number"),
                                  ("Agent", "passport_details"), ("Organization", "bank_details")):
                self.assertEqual(conn.execute(f"SELECT count(*) FROM {table} WHERE upper({column}) LIKE '%DEMO%'").fetchone()[0], 0)
        self.assertEqual(App.table_values(["Иванов", 50], ("ФИО", "Сумма")), ("  Иванов  ", "  50.00  "))

    def test_report_uses_logged_in_company(self):
        app = Mock()
        app.tenant = authenticate("БелСтрах", "1234")
        app.report_code.get.return_value = "9001"
        app.report_date.get.return_value = "2026-11-03"
        app.report_tree.get_children.return_value = ()
        with patch.object(app.tenant, "report_payouts", return_value=[]) as report:
            App.report(app, 3)
        report.assert_called_once_with("2026-11-03", 9001)

    def test_migration_saves_backup_and_does_not_lose_relations(self):
        with get_connection() as conn:
            conn.execute("UPDATE Contract SET contract_number='DEMO-001' WHERE contract_number='КД-0001'")
            conn.commit()
        init_database()
        with get_connection() as conn:
            row = conn.execute("SELECT id FROM Contract WHERE contract_number='КД-0001'").fetchone()
            self.assertIsNotNone(row)
            self.assertGreater(conn.execute("SELECT count(*) FROM ContractEmployee WHERE contract_id=?", (row["id"],)).fetchone()[0], 0)
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
        backups = list(Path(self.temp.name).glob("insurance.before-format-*.db"))
        self.assertEqual(len(backups), 1)
        with sqlite3.connect(backups[0]) as backup:
            self.assertIsNotNone(backup.execute("SELECT id FROM Contract WHERE contract_number='DEMO-001'").fetchone())


if __name__ == "__main__":
    unittest.main()
