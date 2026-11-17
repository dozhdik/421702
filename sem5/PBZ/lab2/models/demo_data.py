"""Deterministic supplemental demonstration data."""
import random
from datetime import date, timedelta

CATEGORIES = ("первая", "вторая", "высшая")
SURNAMES = ("Абрамов", "Беляев", "Волков", "Громов", "Дроздов", "Жуков", "Зайцев",
            "Климов", "Лебедев", "Мельников", "Никитин", "Павлов", "Романов", "Соколов",
            "Тарасов", "Федоров", "Харитонов", "Цветков", "Чернов", "Шилов")
FIRST_NAMES = ("Александр", "Андрей", "Антон", "Артём", "Виктор", "Владимир", "Денис",
               "Евгений", "Игорь", "Кирилл", "Максим", "Михаил", "Николай")
PATRONYMICS = ("Александрович", "Андреевич", "Викторович", "Иванович", "Николаевич")
FEMALE_SURNAMES = ("Абрамова", "Беляева", "Волкова", "Громова", "Дроздова", "Жукова", "Зайцева",
                   "Климова", "Лебедева", "Мельникова", "Никитина", "Павлова", "Романова",
                   "Соколова", "Тарасова", "Фёдорова", "Харитонова", "Цветкова", "Чернова", "Шилова")
FEMALE_NAMES = ("Анастасия", "Анна", "Валерия", "Вера", "Елена", "Ирина", "Ксения",
                "Мария", "Наталья", "Ольга", "Светлана", "Татьяна", "Юлия")
FEMALE_PATRONYMICS = ("Александровна", "Андреевна", "Викторовна", "Ивановна", "Николаевна")
CITIES = ("Минск", "Брест", "Витебск", "Гомель", "Гродно", "Могилёв", "Барановичи")
STREETS = ("Цветочная", "Лесная", "Полевая", "Зелёная", "Школьная", "Заводская", "Солнечная")
ORGANIZATIONS = (
    ("Медицинский центр «Васильковый берег»", "МЦ «Васильковый берег»", "медицинские услуги"),
    ("Транспортная компания «Северная линия»", "ТК «Северная линия»", "пассажирские перевозки"),
    ("Учебный центр «Новый маршрут»", "УЦ «Новый маршрут»", "дополнительное образование"),
    ("Производственное предприятие «Лесная мастерская»", "ПП «Лесная мастерская»", "производство мебели"),
    ("Торговый дом «Городской квартал»", "ТД «Городской квартал»", "розничная торговля"),
    ("Клиника «Тихий сад»", "Клиника «Тихий сад»", "медицинские услуги"),
    ("Логистический центр «Дорожный маяк»", "ЛЦ «Дорожный маяк»", "грузоперевозки"),
    ("Колледж «Истоки мастерства»", "Колледж «Истоки»", "профессиональное образование"),
    ("Завод «Речной механизм»", "Завод «Речной механизм»", "машиностроение"),
    ("Фирма «Домашний рынок»", "Фирма «Домашний рынок»", "оптовая торговля"),
    ("Диагностический центр «Ясный день»", "ДЦ «Ясный день»", "медицинская диагностика"),
    ("Автопарк «Ровный путь»", "Автопарк «Ровный путь»", "автомобильные перевозки"),
    ("Школа «Солнечная аллея»", "Школа «Солнечная аллея»", "общее образование"),
    ("Фабрика «Льняной узор»", "Фабрика «Льняной узор»", "производство текстиля"),
    ("Магазин «Добрая лавка»", "Магазин «Добрая лавка»", "розничная торговля"),
    ("Стоматология «Белая липа»", "Стоматология «Белая липа»", "стоматологические услуги"),
    ("Автосервис «Колесо дорог»", "Автосервис «Колесо дорог»", "ремонт транспорта"),
    ("Центр развития «Первая ступень»", "ЦР «Первая ступень»", "дополнительное образование"),
    ("Пекарня «Утренний хлеб»", "Пекарня «Утренний хлеб»", "пищевое производство"),
    ("Торговая компания «Зелёная корзина»", "ТК «Зелёная корзина»", "оптовая торговля"),
    ("Медицинская лаборатория «Светлая долина»", "Лаборатория «Светлая долина»", "лабораторная диагностика"),
    ("Курьерская служба «Быстрый маршрут»", "Служба «Быстрый маршрут»", "доставка грузов"),
    ("Учебная студия «Открытая книга»", "Студия «Открытая книга»", "обучающие курсы"),
    ("Мастерская «Дубовый лист»", "Мастерская «Дубовый лист»", "обработка древесины"),
    ("Торговый центр «Мирный проспект»", "ТЦ «Мирный проспект»", "розничная торговля"),
    ("Реабилитационный центр «Тёплый ключ»", "РЦ «Тёплый ключ»", "реабилитационные услуги"),
    ("Предприятие «Озёрная пристань»", "ПП «Озёрная пристань»", "транспортные услуги"),
)
DESCRIPTIONS = ("Травма при выполнении работ", "Расходы на лечение", "Восстановление после травмы",
                "Амбулаторное лечение", "Несчастный случай")


def legacy_person(index):
    return f"{SURNAMES[index % len(SURNAMES)]} {FIRST_NAMES[(index // len(SURNAMES)) % len(FIRST_NAMES)]} {PATRONYMICS[(index // (len(SURNAMES) * len(FIRST_NAMES))) % len(PATRONYMICS)]}"


def person(index):
    if index % 2 == 0:
        return legacy_person(index)
    return f"{FEMALE_SURNAMES[index % len(FEMALE_SURNAMES)]} {FEMALE_NAMES[(index // len(FEMALE_SURNAMES)) % len(FEMALE_NAMES)]} {FEMALE_PATRONYMICS[(index // (len(FEMALE_SURNAMES) * len(FEMALE_NAMES))) % len(FEMALE_PATRONYMICS)]}"


def agent_passport(index):
    return f"MP{index+1:07d}"


def add_supplemental_data(conn, added):
    rng = random.Random(421702)
    org_ids, agent_ids = [], []
    employees = {}
    for index in range(27):
        code = 9100 + index
        name, brief_name, specialization = ORGANIZATIONS[index]
        legacy_name = f'Белорусское предприятие «Орион-{index + 1:02d}»'
        row = conn.execute("SELECT id, full_name FROM Organization WHERE organization_code=?", (code,)).fetchone()
        if row and row["full_name"] not in (name, legacy_name):
            org_ids.append(None)
            continue
        if row:
            org_id = row["id"]
        else:
            org_id = conn.execute("""INSERT INTO Organization
                (organization_code,full_name,brief_name,address,bank_details,specialization)
                VALUES (?,?,?,?,?,?)""",
                (code, name, brief_name,
                 f"г. {CITIES[index % len(CITIES)]}, ул. {STREETS[(index // len(CITIES)) % len(STREETS)]}, д. {index * 2 + 3}",
                 f"BY00 TEST 0000 0000 {index+1000:04d} 0000", specialization)).lastrowid
            added["organizations"] += 1
        org_ids.append(org_id)

    for index in range(38):
        passport = agent_passport(index)
        legacy_passport = f"DEMO-AGENT-{index+1:03d}"
        name = person(index + 300)
        row = conn.execute("SELECT id,full_name FROM Agent WHERE passport_details IN (?, ?, ?) ORDER BY id LIMIT 1", (passport, legacy_passport, passport + " (учебный)")).fetchone()
        if row and row["full_name"] not in (name, legacy_person(index + 300)):
            agent_ids.append(None)
            continue
        if row:
            agent_id = row["id"]
        else:
            agent_id = conn.execute("""INSERT INTO Agent
                (full_name,passport_details,phone_number,insurance_company) VALUES (?,?,?,?)""",
                (name, passport, f"+375{('29', '33', '44')[index % 3]}{7000000+index*137:07d}",
                 ("БелСтрах", "Надёжный полис", "Защита") [index % 3])).lastrowid
            added["agents"] += 1
        agent_ids.append(agent_id)

    for index in range(243):
        org_id = org_ids[index % len(org_ids)]
        if org_id is None:
            continue
        name = person(index)
        category = CATEGORIES[(index // len(org_ids)) % len(CATEGORIES)]
        age = rng.randint(21, 63)
        row = conn.execute("SELECT id,risk_category FROM Employee WHERE organization_id=? AND full_name IN (?, ?) ORDER BY id LIMIT 1", (org_id, name, legacy_person(index))).fetchone()
        if row:
            if row["risk_category"] != category:
                continue
            employee_id = row["id"]
        else:
            employee_id = conn.execute("INSERT INTO Employee(organization_id,full_name,age,risk_category) VALUES (?,?,?,?)",
                                       (org_id, name, age, category)).lastrowid
            added["employees"] += 1
        employees.setdefault(org_id, []).append(employee_id)

    for index in range(95):
        number = f"КД-{index+1001:04d}"
        org_id = org_ids[index % len(org_ids)]
        agent_id = agent_ids[index % len(agent_ids)]
        if org_id is None or agent_id is None:
            continue
        if conn.execute("SELECT 1 FROM IndividualContract WHERE contract_number=?", (number,)).fetchone():
            continue
        members = employees.get(org_id, [])
        if len(members) < 3 + index % 4:
            continue
        start_year = (2024, 2025, 2026, 2027, 2028)[index % 5]
        start = date(start_year, (index % 12)+1, 1)
        end = date(start_year+1, start.month, 1) - timedelta(days=1)
        row = conn.execute("SELECT id,organization_id,agent_id FROM Contract WHERE contract_number=?", (number,)).fetchone()
        if row:
            if row["organization_id"] != org_id or row["agent_id"] != agent_id:
                continue
            continue
        contract_id = conn.execute("""INSERT INTO Contract
            (contract_number,organization_id,agent_id,conclusion_date,end_date) VALUES (?,?,?,?,?)""",
            (number, org_id, agent_id, start.isoformat(), end.isoformat())).lastrowid
        added["contracts"] += 1
        selected = rng.sample(members, 3 + index % 4)
        categories = set()
        for employee_id in selected:
            conn.execute("INSERT INTO ContractEmployee(contract_id,employee_id) VALUES (?,?)", (contract_id,employee_id))
            categories.add(conn.execute("SELECT risk_category FROM Employee WHERE id=?", (employee_id,)).fetchone()[0])
            added["contract_employees"] += 1
        for category in sorted(categories):
            conn.execute("INSERT INTO Payout(contract_id,risk_category,payout_amount) VALUES (?,?,?)",
                         (contract_id, category, 10000 + 1000 * CATEGORIES.index(category) + index * 10))
            added["payouts"] += 1
        count = 2 if index < 25 else 1
        for position in range(count):
            claim_date = start + timedelta(days=15 + position * 60)
            conn.execute("""INSERT INTO InsuranceClaim
                (contract_id,employee_id,claim_date,amount,description) VALUES (?,?,?,?,?)""",
                (contract_id, selected[position], claim_date.isoformat(), str(100 + index * 5 + position),
                 DESCRIPTIONS[(index + position) % len(DESCRIPTIONS)]))
            added["claims"] += 1

    for index in range(40):
        number = f"ИД-{index+1:04d}"
        name = person(index+400)
        agent_id = agent_ids[index % len(agent_ids)]
        if agent_id is None:
            continue
        if conn.execute("SELECT 1 FROM Contract WHERE contract_number=?", (number,)).fetchone():
            continue
        row = conn.execute("SELECT full_name,agent_id FROM IndividualContract WHERE contract_number=?", (number,)).fetchone()
        if row:
            if row["full_name"] not in (name, legacy_person(index+400)) or row["agent_id"] != agent_id:
                continue
            continue
        year = 2025 + index % 4
        conn.execute("""INSERT INTO IndividualContract
            (contract_number,full_name,agent_id,conclusion_date,end_date,amount) VALUES (?,?,?,?,?,?)""",
            (number, name, agent_id, f"{year}-01-01", f"{year}-12-31", str(8000 + index * 100)))
        added["individual_contracts"] += 1
