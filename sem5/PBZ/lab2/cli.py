import argparse
import sqlite3

from models.database import init_database
from models.seed import seed_database
from models.database import records
from models.organization import Organization
from models.employee import Employee
from models.agent import Agent
from models.contract import Contract
from models.individual_contract import IndividualContract
from models.insurance_claim import InsuranceClaim
from models.payout import money


FIELDS = {
    "organizations": (("organization_code", "Код"), ("full_name", "Полное название"),
                      ("brief_name", "Краткое название"), ("address", "Адрес"),
                      ("bank_details", "Банковские реквизиты"), ("specialization", "Специализация")),
    "employees": (("organization_id", "ID организации"), ("full_name", "ФИО"),
                  ("age", "Возраст"), ("risk_category", "Категория риска")),
    "agents": (("full_name", "ФИО"), ("passport_details", "Паспортные данные"),
               ("phone_number", "Телефон"), ("insurance_company", "Страховая фирма")),
    "individuals": (("contract_number", "Номер договора"), ("full_name", "ФИО страхователя"),
                    ("agent_id", "ID агента"), ("conclusion_date", "Дата начала YYYY-MM-DD"),
                    ("end_date", "Дата окончания YYYY-MM-DD"), ("amount", "Страховая сумма")),
}


MODELS = {
    "organizations": Organization,
    "employees": Employee,
    "agents": Agent,
    "individuals": IndividualContract,
}


def list_items(kind):
    return MODELS[kind].list_all()


def save_item(kind, values, item_id=None):
    if kind == "individuals":
        return IndividualContract.save(values, item_id)
    data = dict(values)
    for field in ("organization_code", "organization_id", "age"):
        if field in data:
            data[field] = int(data[field])
    model = MODELS[kind](**data, id=item_id)
    if item_id is None:
        model.add()
    else:
        model.update()
    return model._id


def delete_item(kind, item_id):
    if kind == "individuals":
        IndividualContract.delete(item_id)
        return
    model = MODELS[kind].get_by_id(item_id)
    if model is None:
        raise ValueError("Запись не найдена")
    model.delete()


def show_rows(rows, labels=None):
    if not rows:
        print("Нет записей.")
        return
    for row in rows:
        print(" | ".join(f"{labels.get(key, key) if labels else key}: {value}" for key, value in row.items()))


def get_id(prompt="ID: "):
    value = int(input(prompt).strip())
    if value <= 0:
        raise ValueError("ID должен быть положительным целым числом")
    return value


def choose_row(rows, prompt="ID: "):
    show_rows(rows)
    if not rows:
        return None
    row_id = get_id(prompt)
    row = next((r for r in rows if r["id"] == row_id), None)
    if row is None:
        raise ValueError("Запись с таким ID не найдена")
    return row


def confirm(row):
    show_rows([row])
    return input("Подтвердить удаление? (да/нет): ").strip().lower() in ("да", "д", "yes", "y")


def entity_menu(kind, title):
    labels = dict(FIELDS[kind])
    labels["id"] = "ID"
    while True:
        print(f"\n--- {title} ---\n1. Список\n2. Добавить\n3. Изменить\n4. Удалить\n0. Назад")
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "0":
                return
            if choice == "1":
                show_rows(list_items(kind), labels)
            elif choice in ("2", "3"):
                old = choose_row(list_items(kind)) if choice == "3" else None
                if choice == "3" and old is None:
                    continue
                if kind == "employees":
                    print("Организации:")
                    show_rows(list_items("organizations"))
                if kind == "individuals":
                    print("Агенты:")
                    show_rows(list_items("agents"))
                values = {}
                for key, label in FIELDS[kind]:
                    if old and kind == "employees" and key == "organization_id":
                        values[key] = old[key]
                        print(f"{label}: {old[key]} (не изменяется)")
                        continue
                    suffix = f" [{old[key]}]" if old else ""
                    value = input(f"{label}{suffix}: ").strip()
                    values[key] = value if value or not old else old[key]
                save_item(kind, values, old["id"] if old else None)
                print("Сохранено.")
            elif choice == "4":
                row = choose_row(list_items(kind))
                if row and confirm(row):
                    delete_item(kind, row["id"])
                    print("Удалено.")
                elif row:
                    print("Удаление отменено.")
            else:
                print("Неизвестный пункт меню.")
        except (ValueError, sqlite3.Error) as exc:
            print(f"Ошибка: {exc}")


def contracts():
    return records("""SELECT c.id,c.contract_number,o.full_name AS organization,
        a.full_name AS agent,c.conclusion_date,c.end_date,c.organization_id,c.agent_id
        FROM Contract c JOIN Organization o ON o.id=c.organization_id
        JOIN Agent a ON a.id=c.agent_id ORDER BY c.id""")


def contract_data(row):
    people = records("SELECT employee_id FROM ContractEmployee WHERE contract_id=? ORDER BY employee_id", (row["id"],))
    payouts = records("SELECT risk_category,payout_amount FROM Payout WHERE contract_id=? ORDER BY risk_category", (row["id"],))
    return [r["employee_id"] for r in people], {r["risk_category"]: r["payout_amount"] for r in payouts}


def save_existing(row, employees, payouts):
    Contract.save_contract(row["contract_number"], row["organization_id"], row["agent_id"],
                      row["conclusion_date"], row["end_date"], employees, payouts, row["id"])


def select_related(kind, prompt):
    row = choose_row(list_items(kind), prompt)
    if row is None:
        raise ValueError("Сначала добавьте необходимые связанные записи")
    return row["id"]


def ask_field(label, old=None):
    suffix = f" [{old}]" if old is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value or old is None else str(old)


def employee_selection(org_id, previous=None):
    rows = records("SELECT id,full_name,risk_category FROM Employee WHERE organization_id=? ORDER BY id", (org_id,))
    show_rows(rows)
    if not rows:
        raise ValueError("У организации нет сотрудников")
    default = ",".join(str(i) for i in previous) if previous is not None else None
    raw = ask_field("ID сотрудников через запятую", default)
    try:
        result = [int(x.strip()) for x in raw.split(",")]
    except ValueError:
        raise ValueError("Введите ID сотрудников через запятую") from None
    if any(i <= 0 for i in result):
        raise ValueError("ID должны быть положительными")
    return result


def ask_payouts(employee_ids, previous=None):
    previous = previous or {}
    result = dict(previous)
    categories = set()
    for employee_id in employee_ids:
        rows = records("SELECT risk_category FROM Employee WHERE id=?", (employee_id,))
        if not rows:
            raise ValueError(f"Сотрудник {employee_id} не найден")
        categories.add(rows[0]["risk_category"])
    for category in sorted(categories):
        result[category] = money(ask_field(f"Сумма для категории «{category}»", previous.get(category)))
    return result


def edit_contract(row=None):
    if row:
        org_id = row["organization_id"]
        people, payouts = contract_data(row)
        print(f"Организация ID {org_id} (не изменяется)")
    else:
        org_id = select_related("organizations", "ID организации: ")
        people, payouts = None, {}
    number = ask_field("Номер договора", row["contract_number"] if row else None)
    print("Агенты:")
    show_rows(list_items("agents"))
    agent_id = int(ask_field("ID агента", row["agent_id"] if row else None))
    start = ask_field("Дата начала YYYY-MM-DD", row["conclusion_date"] if row else None)
    end = ask_field("Дата окончания YYYY-MM-DD", row["end_date"] if row else None)
    selected = employee_selection(org_id, people)
    amounts = ask_payouts(selected, payouts)
    Contract.save_contract(number, org_id, agent_id, start, end, selected, amounts, row["id"] if row else None)
    print("Договор сохранён.")


def contract_menu():
    while True:
        print("\n--- Коллективные договоры ---\n1. Список\n2. Добавить\n3. Изменить\n4. Удалить\n5. Сотрудники договора\n6. Добавить сотрудника\n7. Удалить сотрудника\n0. Назад")
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "0": return
            if choice == "1": show_rows(contracts()); continue
            if choice == "2": edit_contract(); continue
            if choice not in ("3", "4", "5", "6", "7"):
                print("Неизвестный пункт меню."); continue
            row = choose_row(contracts())
            if not row: continue
            if choice == "3":
                edit_contract(row)
            elif choice == "4":
                print("Вместе с договором будут удалены связи с сотрудниками и суммы категорий.")
                if confirm(row):
                    Contract.delete_contract(row["id"]); print("Договор удалён.")
                else:
                    print("Удаление отменено.")
            else:
                employees, payouts = contract_data(row)
                if choice == "5":
                    show_rows(records("""SELECT e.id,e.full_name,e.age,e.risk_category FROM Employee e
                        JOIN ContractEmployee ce ON ce.employee_id=e.id WHERE ce.contract_id=?""", (row["id"],)))
                elif choice == "6":
                    candidates = records("SELECT id,full_name,risk_category FROM Employee WHERE organization_id=? ORDER BY id", (row["organization_id"],))
                    selected = choose_row(candidates, "ID сотрудника: ")
                    if selected:
                        if selected["id"] in employees: raise ValueError("Сотрудник уже включён в договор")
                        employees.append(selected["id"])
                        if selected["risk_category"] not in payouts:
                            payouts[selected["risk_category"]] = money(input("Сумма для категории: ").strip())
                        save_existing(row, employees, payouts); print("Сотрудник добавлен.")
                else:
                    selected = choose_row(records("""SELECT e.id,e.full_name,e.risk_category FROM Employee e
                        JOIN ContractEmployee ce ON ce.employee_id=e.id WHERE ce.contract_id=?""", (row["id"],)), "ID сотрудника: ")
                    if selected and confirm(selected):
                        employees.remove(selected["id"])
                        save_existing(row, employees, payouts); print("Сотрудник удалён из договора.")
                    elif selected: print("Удаление отменено.")
        except (ValueError, sqlite3.Error) as exc:
            print(f"Ошибка: {exc}")


def payout_menu():
    while True:
        print("\n--- Суммы по категориям ---\n1. Показать\n2. Добавить или изменить\n3. Удалить\n0. Назад")
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "0": return
            if choice not in ("1", "2", "3"):
                print("Неизвестный пункт меню."); continue
            row = choose_row(contracts())
            if not row: continue
            employees, payouts = contract_data(row)
            show_rows([{"category": k, "amount": v} for k,v in payouts.items()])
            if choice == "1": continue
            category = input("Категория риска: ").strip()
            if not category: raise ValueError("Укажите категорию")
            if choice == "2":
                payouts[category] = money(input("Сумма: ").strip())
                save_existing(row, employees, payouts); print("Сумма сохранена.")
            else:
                if category not in payouts: raise ValueError("Категория не найдена")
                if confirm({"category":category, "amount":payouts[category]}):
                    del payouts[category]
                    save_existing(row, employees, payouts); print("Сумма удалена.")
                else: print("Удаление отменено.")
        except (ValueError, sqlite3.Error) as exc:
            print(f"Ошибка: {exc}")


def claims_menu():
    while True:
        print("\n--- Страховые случаи ---\n1. Список\n2. Добавить\n3. Изменить\n4. Удалить\n0. Назад")
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "0": return
            rows = records("SELECT id,contract_id,employee_id,claim_date,amount,description FROM InsuranceClaim ORDER BY id")
            if choice == "1": show_rows(rows); continue
            if choice not in ("2", "3", "4"):
                print("Неизвестный пункт меню."); continue
            old = choose_row(rows) if choice in ("3", "4") else None
            if choice in ("3", "4") and not old: continue
            if choice == "4":
                if confirm(old): InsuranceClaim.delete_claim(old["id"]); print("Удалено.")
                else: print("Удаление отменено.")
                continue
            show_rows(contracts())
            cid = int(ask_field("ID договора", old["contract_id"] if old else None))
            show_rows(records("""SELECT e.id,e.full_name FROM Employee e JOIN ContractEmployee ce
                ON ce.employee_id=e.id WHERE ce.contract_id=?""", (cid,)))
            eid = int(ask_field("ID сотрудника", old["employee_id"] if old else None))
            claim_date = ask_field("Дата случая YYYY-MM-DD", old["claim_date"] if old else None)
            amount = ask_field("Сумма", old["amount"] if old else None)
            description = ask_field("Описание", old["description"] if old else None)
            InsuranceClaim.save_claim(cid, eid, claim_date, amount, description, old["id"] if old else None)
            print("Сохранено.")
        except (ValueError, sqlite3.Error) as exc:
            print(f"Ошибка: {exc}")


def report(kind):
    code_text = input("Код организации" + (" (пусто — все)" if kind == 3 else "") + ": ").strip()
    code = int(code_text) if code_text else None
    if kind != 3 and code is None:
        raise ValueError("Укажите код организации")
    if code is not None and code <= 0:
        raise ValueError("Код должен быть положительным")
    selected_date = input("Дата YYYY-MM-DD: ").strip()
    if kind == 1:
        data = Contract.report_contracts(code, selected_date)
        if data["organization"] is None:
            print("Организация не найдена."); return
        print(f"Дата: {selected_date} | Организация: {data['organization']['full_name']} | Адрес: {data['organization']['address']}")
        show_rows(data["contracts"], {"contract_number":"Номер", "conclusion_date":"Начало", "end_date":"Окончание"})
    elif kind == 2:
        data = Contract.report_agents(code, selected_date)
        print(f"Дата: {selected_date}")
        show_rows([{k:v for k,v in row.items() if k != "id"} for row in data["agents"]],
                  {"insurance_company":"Страховая фирма", "full_name":"ФИО", "phone_number":"Телефон"})
    else:
        data = Contract.report_payouts(selected_date, code)
        print(f"Дата: {selected_date}")
        show_rows(data["payouts"], {"organization":"Организация", "contract_number":"Договор",
                                   "risk_category":"Категория", "payout_amount":"Сумма"})


def menu():
    while True:
        print("\n=== УЧЁТ ДОГОВОРОВ СТРАХОВАНИЯ ===")
        print("1. Организации\n2. Страхуемые сотрудники\n3. Страховые агенты\n4. Коллективные договоры\n5. Суммы выплат по категориям\n6. Отчёт: действующие договоры организации\n7. Отчёт: агенты организации\n8. Отчёт: выплаты по категориям\n9. Заполнить БД демонстрационными данными\n10. Индивидуальные договоры\n11. Страховые случаи\n0. Выход")
        choice = input("Выберите пункт: ").strip()
        try:
            if choice == "0": print("До свидания!"); return
            if choice == "1": entity_menu("organizations", "Организации")
            elif choice == "2": entity_menu("employees", "Сотрудники")
            elif choice == "3": entity_menu("agents", "Агенты")
            elif choice == "4": contract_menu()
            elif choice == "5": payout_menu()
            elif choice in ("6", "7", "8"): report(int(choice)-5)
            elif choice == "9": print("Добавлено:", seed_database())
            elif choice == "10": entity_menu("individuals", "Индивидуальные договоры")
            elif choice == "11": claims_menu()
            else: print("Неизвестный пункт меню.")
        except (ValueError, sqlite3.Error) as exc:
            print(f"Ошибка: {exc}")


def main():
    parser = argparse.ArgumentParser(description="Учёт договоров страхования")
    parser.add_argument("--seed", action="store_true", help="загрузить демонстрационные данные и выйти")
    args = parser.parse_args()
    try:
        init_database()
        if args.seed:
            print(seed_database())
        else:
            menu()
    except (EOFError, KeyboardInterrupt):
        print("\nДо свидания!")
    except sqlite3.Error as exc:
        print(f"Ошибка базы данных: {exc}")


if __name__ == "__main__":
    main()
