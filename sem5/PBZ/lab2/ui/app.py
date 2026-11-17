"""Tkinter interface for the insurance application."""
import sqlite3
import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkfont

from models.company_seed import seed_company
from models.database import records
from models.contract import Contract
from models.insurance_claim import InsuranceClaim
from models.tenant import authenticate, register_company
from cli import save_item, delete_item, FIELDS


def is_clear_phrase(value):
    return value == "УДАЛИТЬ ВСЁ"


class App(tk.Tk):
    def __init__(self, tenant):
        super().__init__()
        self.tenant = tenant
        self.logout_requested = False
        self.title("Учёт договоров страхования")
        self.geometry("1150x650")
        self.minsize(850, 500)
        self.configure_table_style()
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)
        self.views = {}
        definitions = [
            ("organizations", "Организации", ("Код", "Полное название", "Краткое название", "Адрес", "Банк", "Специализация")),
            ("employees", "Сотрудники", ("ID организации", "ФИО", "Возраст", "Категория")),
            ("agents", "Агенты", ("ФИО", "Паспорт", "Телефон", "Страховая фирма")),
            ("individuals", "Физические лица", ("Номер", "ФИО", "ID агента", "Начало", "Окончание", "Сумма")),
        ]
        for kind, title, labels in definitions:
            self.entity_tab(kind, title, labels)
        self.contract_tab()
        self.claim_tab()
        self.report_tab()
        actions = ttk.Frame(self, padding=6)
        actions.pack(fill="x")
        ttk.Label(actions, text=f"Страховая компания: {tenant.name}").pack(side="left", padx=(0, 12))
        ttk.Button(actions, text="Заполнить данные компании", command=self.seed_current_company).pack(side="left")
        ttk.Button(actions, text="Очистить данные компании", command=self.request_clear).pack(side="left", padx=8)
        ttk.Button(actions, text="Выйти из учётной записи", command=self.logout).pack(side="right")

    def guard(self, callback):
        try:
            callback()
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)

    def configure_table_style(self):
        style = ttk.Style(self)
        font_name = style.lookup("Treeview", "font") or "TkDefaultFont"
        heading_name = style.lookup("Treeview.Heading", "font") or "TkHeadingFont"
        self.table_font = tkfont.Font(root=self, font=font_name)
        self.heading_font = tkfont.Font(root=self, font=heading_name)
        self.table_font.configure(size=11, weight="normal")
        self.heading_font.configure(size=10, weight="bold")
        padding = max(3, round(self.winfo_fpixels("3p")))
        row_height = max(28, self.table_font.metrics("linespace") + 2 * padding)
        style.configure("Insurance.Treeview", font=self.table_font, rowheight=row_height)
        style.configure("Insurance.Treeview.Heading", font=self.heading_font)

    def configure_columns(self, tree, columns, rows=()):
        """Fit initial column sizes while keeping them bounded and resizable."""
        tree.configure(columns=[key for key, _ in columns])
        padding = max(12, round(self.winfo_fpixels("12p")), self.table_font.measure("    ") + 8)
        for index, (key, label) in enumerate(columns):
            short = label in ("ID", "Код", "ID организации", "ID агента", "Возраст")
            minimum = self.heading_font.measure(label) + padding
            # Limit samples and text length so a single value cannot dominate the layout.
            values = [str(row[index])[:200] for row in rows[:250] if index < len(row)]
            content_width = max((self.table_font.measure(value) + padding for value in values), default=0)
            preferred = max(minimum, content_width, 65 if short else 110)
            maximum = max(minimum, 130 if short else 320)
            tree.heading(key, text=label)
            tree.column(key, width=min(preferred, maximum), minwidth=minimum,
                        stretch=not short, anchor="w")

    def tree(self, frame, columns):
        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True)
        tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse",
                            style="Insurance.Treeview")
        vertical = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.configure_columns(tree, [(col, col) for col in columns])
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        return tree

    @staticmethod
    def table_values(values, columns=()):
        result = []
        for index, value in enumerate(values):
            if value is not None and index < len(columns) and columns[index] == "Сумма":
                try:
                    value = format(Decimal(str(value)), ".2f")
                except InvalidOperation:
                    pass
            result.append(f"  {value}  " if value is not None else "")
        return tuple(result)

    def selected(self, tree):
        selection = tree.selection()
        if not selection:
            raise ValueError("Выберите запись")
        return int(selection[0])

    def entity_tab(self, kind, title, labels):
        frame = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(frame, text=title)
        tree = self.tree(frame, ("ID", *labels))
        buttons = ttk.Frame(frame); buttons.pack(fill="x", pady=6)
        self.views[kind] = tree
        actions = (("Добавить", lambda: self.entity_form(kind, labels)),
                              ("Изменить", lambda: self.entity_form(kind, labels, self.selected(tree))),
                              ("Удалить", lambda: self.delete_entity(kind, self.selected(tree))),
                              ("Обновить", lambda: self.refresh(kind)))
        if kind in ("organizations", "employees"):
            actions = actions[-1:]
        for label, action in actions:
            ttk.Button(buttons, text=label, command=lambda a=action: self.guard(a)).pack(side="left", padx=3)
        self.refresh(kind)

    def refresh(self, kind):
        tree = self.views[kind]
        tree.delete(*tree.get_children())
        rows = self.tenant.list_items(kind)
        if not getattr(tree, "_initial_widths_set", False) and rows:
            self.configure_columns(tree, [(col, col) for col in tree["columns"]],
                                   [tuple(row.values()) for row in rows])
            tree._initial_widths_set = True
        for row in rows:
            tree.insert("", "end", iid=row["id"], values=self.table_values(row.values(), tree["columns"]))

    def entity_form(self, kind, labels, item_id=None):
        if kind not in ("individuals", "agents"):
            raise ValueError("Редактирование общих справочников недоступно")
        if item_id is not None:
            if kind == "agents":
                self.tenant.require_agent(item_id)
            else:
                self.tenant.require_individual(item_id)
        fields = tuple(field for field, _ in FIELDS[kind])
        row = next((r for r in self.tenant.list_items(kind) if r["id"] == item_id), {}) if item_id else {}
        if item_id and not row:
            raise ValueError("Запись не найдена")
        win = tk.Toplevel(self); win.title("Изменить" if item_id else "Добавить"); win.transient(self)
        entries = {}
        for index, (field, label) in enumerate(zip(fields, labels)):
            ttk.Label(win, text=label).grid(row=index, column=0, padx=8, pady=4, sticky="w")
            if field in ("organization_id", "agent_id"):
                related = self.tenant.list_items("organizations" if field == "organization_id" else "agents")
                if not related:
                    win.destroy()
                    raise ValueError("Сначала добавьте организацию или агента")
                values = [f'{item["id"]}: {item["full_name"]}' for item in related]
                entry = ttk.Combobox(win, values=values, state="readonly", width=42)
                entry.current(next((i for i, item in enumerate(related) if item["id"] == row.get(field)), 0))
            else:
                entry = ttk.Entry(win, width=45)
                entry.insert(0, self.tenant.name if kind == "agents" and field == "insurance_company" else str(row.get(field, "")))
            entry.grid(row=index, column=1, padx=8, pady=4)
            if kind == "agents" and field == "insurance_company":
                entry.configure(state="readonly")
            entries[field] = entry
        def save():
            try:
                values = {f: e.get() for f,e in entries.items()}
                for field in ("organization_id", "agent_id"):
                    if field in values:
                        values[field] = values[field].split(":", 1)[0]
                if kind == "individuals":
                    if item_id is not None:
                        self.tenant.require_individual(item_id)
                    self.tenant.require_agent(int(values["agent_id"]))
                else:
                    if item_id is not None:
                        self.tenant.require_agent(item_id)
                    values["insurance_company"] = self.tenant.name
                save_item(kind, values, item_id)
                self.refresh_all(); win.destroy()
                messagebox.showinfo("Успех", "Запись сохранена", parent=self)
            except (ValueError, sqlite3.Error) as exc:
                messagebox.showerror("Ошибка", str(exc), parent=win)
        ttk.Button(win, text="Сохранить", command=save).grid(columnspan=2, pady=8)

    def delete_entity(self, kind, item_id):
        if kind not in ("agents", "individuals"):
            raise ValueError("Удаление недоступно")
        if kind == "agents":
            self.tenant.require_agent(item_id)
        else:
            self.tenant.require_individual(item_id)
        if messagebox.askyesno("Удаление", "Удалить выбранную запись?", parent=self):
            delete_item(kind, item_id)
            self.refresh_all()
            messagebox.showinfo("Успех", "Запись удалена", parent=self)

    def refresh_all(self):
        for kind in self.views: self.refresh(kind)
        self.refresh_contracts()
        self.refresh_claims()

    def contract_tab(self):
        frame=ttk.Frame(self.tabs,padding=8); self.tabs.add(frame,text="Договоры")
        self.contracts=self.tree(frame,("ID","Номер","Организация","Агент","Начало","Окончание"))
        bar=ttk.Frame(frame); bar.pack(fill="x",pady=6)
        for label,action in (("Добавить",lambda:self.contract_form()),
                             ("Изменить",lambda:self.contract_form(self.selected(self.contracts))),
                             ("Удалить",lambda:self.delete_contract()),
                             ("Поиск по номеру",self.find_contract),
                             ("Обновить",self.refresh_contracts)):
            ttk.Button(bar,text=label,command=lambda a=action:self.guard(a)).pack(side="left",padx=3)
        self.refresh_contracts()

    def refresh_contracts(self):
        self.contracts.delete(*self.contracts.get_children())
        rows = self.tenant.contracts()
        if not getattr(self.contracts, "_initial_widths_set", False) and rows:
            self.configure_columns(self.contracts, [(col, col) for col in self.contracts["columns"]],
                                   [tuple(row.values()) for row in rows])
            self.contracts._initial_widths_set = True
        for r in rows:
            self.contracts.insert("","end",iid=r["id"],values=self.table_values(r.values()))

    def find_contract(self):
        number=simpledialog.askstring("Поиск","Номер договора:",parent=self)
        if number is None: return
        for iid in self.contracts.get_children():
            if self.contracts.item(iid,"values")[1].strip() == number:
                self.contracts.selection_set(iid); self.contracts.see(iid); return
        messagebox.showinfo("Поиск","Договор не найден",parent=self)

    def delete_contract(self):
        cid=self.selected(self.contracts)
        self.tenant.require_contract(cid)
        if messagebox.askyesno("Удаление","Удалить договор, его состав и суммы?",parent=self):
            Contract.delete_contract(cid); self.refresh_all()
            messagebox.showinfo("Успех", "Договор удалён", parent=self)

    def contract_form(self, cid=None):
        if cid is not None:
            self.tenant.require_contract(cid)
        win=tk.Toplevel(self); win.title("Коллективный договор"); win.geometry("750x650")
        rows=records("SELECT * FROM Contract WHERE id=?", (cid,)) if cid else []
        old=rows[0] if rows else {}
        orgs=self.tenant.organizations(); agents=self.tenant.agents()
        if not orgs or not agents:
            win.destroy(); raise ValueError("Сначала добавьте организацию и агента")
        fields={}
        for n,(key,label) in enumerate((("contract_number","Номер"),("organization_id","Организация"),("agent_id","Агент"),("conclusion_date","Начало YYYY-MM-DD"),("end_date","Окончание YYYY-MM-DD"))):
            ttk.Label(win,text=label).grid(row=n,column=0,sticky="w",padx=8,pady=3)
            if key in ("organization_id","agent_id"):
                data=orgs if key=="organization_id" else agents
                values=[f'{x["id"]}: {x["full_name"]}' for x in data]
                widget=ttk.Combobox(win,values=values,state="readonly",width=48)
                index=next((i for i,x in enumerate(data) if x["id"]==old.get(key)),0)
                widget.current(index)
                if cid and key=="organization_id": widget.configure(state="disabled")
            else:
                widget=ttk.Entry(win,width=50); widget.insert(0,old.get(key,""))
            widget.grid(row=n,column=1,sticky="ew",padx=8,pady=3); fields[key]=widget
        ttk.Label(win,text="Сотрудники (можно выбрать несколько)").grid(row=5,column=0,columnspan=2,sticky="w",padx=8)
        employees=tk.Listbox(win,selectmode="multiple",height=8,exportselection=False)
        employees.grid(row=6,column=0,columnspan=2,sticky="nsew",padx=8)
        ttk.Label(win,text="Суммы по категориям: категория = сумма, каждая с новой строки").grid(row=7,column=0,columnspan=2,sticky="w",padx=8)
        amounts=tk.Text(win,height=7,width=70); amounts.grid(row=8,column=0,columnspan=2,sticky="nsew",padx=8)
        existing_ids={r["employee_id"] for r in records("SELECT employee_id FROM ContractEmployee WHERE contract_id=?",(cid,))} if cid else set()
        if cid:
            for p in records("SELECT risk_category,payout_amount FROM Payout WHERE contract_id=?",(cid,)):
                amounts.insert("end",f'{p["risk_category"]} = {p["payout_amount"]}\n')
        available=[]
        def load_employees(event=None):
            available.clear(); employees.delete(0,"end")
            oid=int(fields["organization_id"].get().split(":",1)[0])
            for r in self.tenant.employees_for_organization(oid):
                available.append(r["id"])
                employees.insert("end",f'{r["id"]}: {r["full_name"]} ({r["risk_category"]})')
                if r["id"] in existing_ids: employees.selection_set("end")
        fields["organization_id"].bind("<<ComboboxSelected>>",load_employees); load_employees()
        def save():
            try:
                payouts={}
                for line in amounts.get("1.0","end").splitlines():
                    if line.strip():
                        if "=" not in line: raise ValueError("Формат суммы: категория = сумма")
                        category,amount=line.split("=",1)
                        if category.strip() in payouts: raise ValueError("Категория указана дважды")
                        payouts[category.strip()]=amount.strip()
                agent_id = int(fields["agent_id"].get().split(":",1)[0])
                org_id = int(fields["organization_id"].get().split(":",1)[0])
                self.tenant.require_organization(org_id)
                self.tenant.require_agent(agent_id)
                if cid is not None:
                    self.tenant.require_contract(cid)
                Contract.save_contract(fields["contract_number"].get(),org_id,agent_id,fields["conclusion_date"].get(),fields["end_date"].get(),[available[i] for i in employees.curselection()],payouts,cid)
                self.refresh_all(); win.destroy()
                messagebox.showinfo("Успех", "Договор сохранён", parent=self)
            except (ValueError,sqlite3.Error) as exc: messagebox.showerror("Ошибка",str(exc),parent=win)
        ttk.Button(win,text="Сохранить договор",command=save).grid(row=9,column=0,columnspan=2,pady=8)
        win.columnconfigure(1,weight=1); win.rowconfigure(6,weight=1); win.rowconfigure(8,weight=1)

    def claim_tab(self):
        frame=ttk.Frame(self.tabs,padding=8); self.tabs.add(frame,text="Страховые случаи")
        self.claims=self.tree(frame,("ID","Договор","Сотрудник","Дата","Сумма","Описание"))
        bar=ttk.Frame(frame); bar.pack(fill="x",pady=6)
        for label,action in (("Добавить",lambda:self.claim_form()),("Изменить",lambda:self.claim_form(self.selected(self.claims))),("Удалить",self.remove_claim),("Обновить",self.refresh_claims)):
            ttk.Button(bar,text=label,command=lambda a=action:self.guard(a)).pack(side="left",padx=3)
        self.refresh_claims()

    def refresh_claims(self):
        self.claims.delete(*self.claims.get_children())
        rows = self.tenant.claims()
        if not getattr(self.claims, "_initial_widths_set", False) and rows:
            self.configure_columns(self.claims, [(col, col) for col in self.claims["columns"]],
                                   [tuple(row.values()) for row in rows])
            self.claims._initial_widths_set = True
        for r in rows:
            self.claims.insert("","end",iid=r["id"],values=self.table_values(r.values(), self.claims["columns"]))

    def remove_claim(self):
        cid=self.selected(self.claims)
        self.tenant.require_claim(cid)
        if messagebox.askyesno("Удаление","Удалить страховой случай?",parent=self):
            InsuranceClaim.delete_claim(cid); self.refresh_claims()
            messagebox.showinfo("Успех", "Страховой случай удалён", parent=self)

    def claim_form(self, claim_id=None):
        if claim_id is not None:
            self.tenant.require_claim(claim_id)
        rows=records("SELECT * FROM InsuranceClaim WHERE id=?",(claim_id,)) if claim_id else []
        old=rows[0] if rows else {}
        win=tk.Toplevel(self); win.title("Страховой случай")
        entries={}
        contract_rows = [{"id": row["id"], "contract_number": row["contract_number"]} for row in self.tenant.contracts()]
        if not contract_rows:
            win.destroy()
            raise ValueError("Сначала добавьте договор")
        for i,(key,label) in enumerate((("contract_id","ID договора"),("employee_id","ID сотрудника"),("claim_date","Дата YYYY-MM-DD"),("amount","Сумма"),("description","Описание"))):
            ttk.Label(win,text=label).grid(row=i,column=0,padx=8,pady=4)
            if key in ("contract_id", "employee_id"):
                entry = ttk.Combobox(win, state="readonly", width=42)
            else:
                entry=ttk.Entry(win,width=45)
                entry.insert(0,str(old.get(key,"")))
            entry.grid(row=i,column=1,padx=8,pady=4); entries[key]=entry
        entries["contract_id"]["values"] = [f'{r["id"]}: {r["contract_number"]}' for r in contract_rows]
        entries["contract_id"].current(next((i for i, r in enumerate(contract_rows) if r["id"] == old.get("contract_id")), 0))
        def load_claim_employees(event=None):
            contract_id = int(entries["contract_id"].get().split(":", 1)[0])
            self.tenant.require_contract(contract_id)
            employees = records("""SELECT e.id,e.full_name FROM Employee e JOIN ContractEmployee ce
                ON ce.employee_id=e.id WHERE ce.contract_id=? ORDER BY e.full_name""", (contract_id,))
            entries["employee_id"]["values"] = [f'{r["id"]}: {r["full_name"]}' for r in employees]
            entries["employee_id"].set("")
            if employees:
                entries["employee_id"].current(next((i for i, r in enumerate(employees) if r["id"] == old.get("employee_id")), 0))
        entries["contract_id"].bind("<<ComboboxSelected>>", load_claim_employees)
        load_claim_employees()
        def save():
            try:
                contract_id = int(entries["contract_id"].get().split(":", 1)[0])
                employee_id = int(entries["employee_id"].get().split(":", 1)[0])
                self.tenant.require_contract(contract_id)
                self.tenant.require_employee(employee_id)
                InsuranceClaim.save_claim(contract_id,employee_id,entries["claim_date"].get(),entries["amount"].get(),entries["description"].get(),claim_id)
                self.refresh_claims(); win.destroy()
                messagebox.showinfo("Успех", "Страховой случай сохранён", parent=self)
            except (ValueError,sqlite3.Error) as exc: messagebox.showerror("Ошибка",str(exc),parent=win)
        ttk.Button(win,text="Сохранить",command=save).grid(columnspan=2,pady=8)

    def report_tab(self):
        frame=ttk.Frame(self.tabs,padding=8); self.tabs.add(frame,text="Отчёты")
        controls=ttk.Frame(frame); controls.pack(fill="x")
        ttk.Label(controls,text="Дата YYYY-MM-DD:").pack(side="left")
        self.report_date=ttk.Entry(controls,width=12); self.report_date.pack(side="left",padx=5)
        ttk.Label(controls,text="Код организации (необязательно):").pack(side="left",padx=5)
        self.report_code=ttk.Entry(controls,width=10); self.report_code.pack(side="left",padx=5)
        for label,kind in (("Договоры",1),("Агенты",2),("Суммы по категориям",3)):
            ttk.Button(controls,text=label,command=lambda k=kind:self.guard(lambda:self.report(k))).pack(side="left",padx=4)
        self.report_info = ttk.Label(frame, text="Выберите дату и постройте отчёт")
        self.report_info.pack(anchor="w", pady=8)
        self.report_tree = self.tree(frame, ("result",))

    def report(self, kind):
        selected_date=self.report_date.get()
        code_text=self.report_code.get().strip()
        code=int(code_text) if code_text else None
        if code is not None and code <= 0:
            raise ValueError("Код организации должен быть положительным")
        if kind==1:
            rows=self.tenant.report_contracts(selected_date,code)
            info=f"Дата: {selected_date} | Страховая компания: {self.tenant.name}"
            columns = (("organization", "Организация"), ("address", "Адрес"), ("contract_number", "Номер договора"), ("conclusion_date", "Начало"), ("end_date", "Окончание"))
        elif kind==2:
            rows=self.tenant.report_agents(selected_date,code)
            info=f"Дата: {selected_date} | Страховая компания: {self.tenant.name}"
            columns = (("insurance_company", "Страховая фирма"), ("full_name", "ФИО"), ("phone_number", "Телефон"))
        else:
            rows=self.tenant.report_payouts(selected_date,code)
            info=f"Дата: {selected_date}"
            columns = (("organization", "Организация"), ("contract_number", "Договор"),
                       ("risk_category", "Категория"), ("payout_amount", "Сумма"),
                       ("conclusion_date", "Действует с"), ("end_date", "Действует по"))
        self.report_info.configure(text=info + (" | Нет данных" if not rows else ""))
        self.report_tree.delete(*self.report_tree.get_children())
        column_keys = tuple(key for key, _ in columns)
        if (getattr(self.report_tree, "_report_columns", None) != column_keys
                or (rows and not getattr(self.report_tree, "_report_has_data", False))):
            self.configure_columns(self.report_tree, columns,
                                   [tuple(row[key] for key, _ in columns) for row in rows])
            self.report_tree._report_columns = column_keys
            self.report_tree._report_has_data = bool(rows)
        for row in rows:
            self.report_tree.insert("", "end", values=self.table_values(
                (row[key] for key, _ in columns), tuple(label for _, label in columns)))

    def seed_current_company(self):
        def run():
            result = seed_company(self.tenant.name)
            self.refresh_all()
            self.report_tree.delete(*self.report_tree.get_children())
            self.report_info.configure(text="Данные обновлены. Постройте отчёт заново.")
            labels = {"organizations": "Организации", "agents": "Агенты", "employees": "Сотрудники",
                      "contracts": "Коллективные договоры", "contract_employees": "Связи с сотрудниками",
                      "payouts": "Суммы по категориям", "individual_contracts": "Индивидуальные договоры",
                      "claims": "Страховые случаи"}
            messagebox.showinfo("Данные компании", "Создано записей:\n" + "\n".join(
                f"{labels[key]}: {value}" for key, value in result.items()), parent=self)
        self.guard(run)

    def logout(self):
        self.logout_requested = True
        self.destroy()

    def confirm_clear_warning(self):
        dialog = tk.Toplevel(self)
        dialog.title("Очистка базы данных")
        dialog.transient(self)
        dialog.grab_set()
        result = tk.BooleanVar(dialog, value=False)
        ttk.Label(dialog, text=(f"Вы собираетесь удалить данные страховой компании «{self.tenant.name}»: "
                  "агентов, договоры, страховые случаи и выплаты.\n\n"
                  "Общие с другими компаниями записи будут сохранены. Это действие затронет "
                  "как демонстрационные, так и введённые вручную данные.\n\nПродолжить?"),
                  wraplength=470, justify="left").pack(padx=20, pady=16)
        buttons = ttk.Frame(dialog)
        buttons.pack(pady=(0, 16))
        ttk.Button(buttons, text="Отмена", command=dialog.destroy).pack(side="left", padx=8)
        def proceed():
            result.set(True)
            dialog.destroy()
        ttk.Button(buttons, text="Продолжить", command=proceed).pack(side="left", padx=8)
        dialog.wait_window()
        return result.get()

    def confirm_clear_phrase(self):
        dialog = tk.Toplevel(self)
        dialog.title("Окончательное подтверждение")
        dialog.transient(self)
        dialog.grab_set()
        result = tk.BooleanVar(dialog, value=False)
        phrase = tk.StringVar(dialog)
        ttk.Label(dialog, text="Для окончательного подтверждения удаления введите фразу: УДАЛИТЬ ВСЁ",
                  wraplength=480).pack(padx=20, pady=(16, 8))
        entry = ttk.Entry(dialog, textvariable=phrase, width=40)
        entry.pack(padx=20, pady=8)
        buttons = ttk.Frame(dialog)
        buttons.pack(pady=(0, 16))
        ttk.Button(buttons, text="Отмена", command=dialog.destroy).pack(side="left", padx=8)
        def proceed():
            if is_clear_phrase(phrase.get()):
                result.set(True)
                dialog.destroy()
        delete_button = ttk.Button(buttons, text="Удалить все данные", state="disabled", command=proceed)
        delete_button.pack(side="left", padx=8)
        phrase.trace_add("write", lambda *_: delete_button.configure(
            state="normal" if is_clear_phrase(phrase.get()) else "disabled"))
        entry.focus_set()
        dialog.wait_window()
        return result.get()

    def request_clear(self):
        if not self.confirm_clear_warning() or not self.confirm_clear_phrase():
            return
        def run():
            self.tenant.clear_data()
            self.refresh_all()
            self.report_tree.delete(*self.report_tree.get_children())
            self.report_info.configure(text="Данные компании очищены. Постройте отчёт заново.")
            messagebox.showinfo("Очистка данных", "Данные страховой компании успешно очищены", parent=self)
        self.guard(run)


class Login(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Вход в систему")
        self.resizable(False, False)
        self.tenant = None
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Название страховой компании:").grid(row=0, column=0, sticky="w", pady=5)
        self.login = ttk.Entry(frame, width=48)
        self.login.grid(row=1, column=0, sticky="ew", pady=5)
        ttk.Label(frame, text="Пароль:").grid(row=2, column=0, sticky="w", pady=5)
        self.password = ttk.Entry(frame, show="*", width=48)
        self.password.grid(row=3, column=0, sticky="ew", pady=5)
        ttk.Button(frame, text="Войти", command=self.sign_in).grid(row=4, column=0, pady=10)
        ttk.Button(frame, text="Зарегистрироваться", command=self.register).grid(row=5, column=0, pady=5)
        self.bind("<Return>", lambda event: self.sign_in())
        self.login.focus_set()

    def sign_in(self):
        try:
            self.tenant = authenticate(self.login.get(), self.password.get())
        except ValueError as exc:
            messagebox.showerror("Вход", str(exc), parent=self)
            return
        self.destroy()

    def register(self):
        try:
            self.tenant = register_company(self.login.get(), self.password.get())
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror("Регистрация", str(exc), parent=self)
            return
        self.destroy()
