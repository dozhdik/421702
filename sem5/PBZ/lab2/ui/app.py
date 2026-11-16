"""Tkinter interface for the insurance application."""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from models.seed import seed_database
from models.database import records
from models.contract import Contract
from models.insurance_claim import InsuranceClaim
from cli import list_items, save_item, delete_item, FIELDS


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учёт договоров страхования")
        self.geometry("1150x650")
        self.minsize(850, 500)
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
        ttk.Button(self, text="Заполнить демонстрационными данными", command=self.seed).pack(pady=4)

    def guard(self, callback):
        try:
            callback()
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)

    def tree(self, frame, columns):
        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True)
        tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        vertical = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=130, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        return tree

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
        for label, action in (("Добавить", lambda: self.entity_form(kind, labels)),
                              ("Изменить", lambda: self.entity_form(kind, labels, self.selected(tree))),
                              ("Удалить", lambda: self.delete_entity(kind, self.selected(tree))),
                              ("Обновить", lambda: self.refresh(kind))):
            ttk.Button(buttons, text=label, command=lambda a=action: self.guard(a)).pack(side="left", padx=3)
        self.refresh(kind)

    def refresh(self, kind):
        tree = self.views[kind]
        tree.delete(*tree.get_children())
        for row in list_items(kind):
            tree.insert("", "end", iid=row["id"], values=tuple(row.values()))

    def entity_form(self, kind, labels, item_id=None):
        fields = tuple(field for field, _ in FIELDS[kind])
        row = next((r for r in list_items(kind) if r["id"] == item_id), {}) if item_id else {}
        win = tk.Toplevel(self); win.title("Изменить" if item_id else "Добавить"); win.transient(self)
        entries = {}
        for index, (field, label) in enumerate(zip(fields, labels)):
            ttk.Label(win, text=label).grid(row=index, column=0, padx=8, pady=4, sticky="w")
            if field in ("organization_id", "agent_id"):
                related = list_items("organizations" if field == "organization_id" else "agents")
                if not related:
                    win.destroy()
                    raise ValueError("Сначала добавьте организацию или агента")
                values = [f'{item["id"]}: {item["full_name"]}' for item in related]
                entry = ttk.Combobox(win, values=values, state="readonly", width=42)
                entry.current(next((i for i, item in enumerate(related) if item["id"] == row.get(field)), 0))
            else:
                entry = ttk.Entry(win, width=45)
                entry.insert(0, str(row.get(field, "")))
            entry.grid(row=index, column=1, padx=8, pady=4)
            if kind == "employees" and field == "organization_id" and item_id:
                entry.configure(state="disabled")
            entries[field] = entry
        def save():
            try:
                values = {f: e.get() for f,e in entries.items()}
                for field in ("organization_id", "agent_id"):
                    if field in values:
                        values[field] = values[field].split(":", 1)[0]
                save_item(kind, values, item_id)
                self.refresh_all(); win.destroy()
                messagebox.showinfo("Успех", "Запись сохранена", parent=self)
            except (ValueError, sqlite3.Error) as exc:
                messagebox.showerror("Ошибка", str(exc), parent=win)
        ttk.Button(win, text="Сохранить", command=save).grid(columnspan=2, pady=8)

    def delete_entity(self, kind, item_id):
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
        for r in records("""SELECT c.id,c.contract_number,o.full_name,a.full_name AS agent,c.conclusion_date,c.end_date
                 FROM Contract c JOIN Organization o ON o.id=c.organization_id JOIN Agent a ON a.id=c.agent_id ORDER BY c.id"""):
            self.contracts.insert("","end",iid=r["id"],values=tuple(r.values()))

    def find_contract(self):
        number=simpledialog.askstring("Поиск","Номер договора:",parent=self)
        if number is None: return
        for iid in self.contracts.get_children():
            if self.contracts.item(iid,"values")[1] == number:
                self.contracts.selection_set(iid); self.contracts.see(iid); return
        messagebox.showinfo("Поиск","Договор не найден",parent=self)

    def delete_contract(self):
        cid=self.selected(self.contracts)
        if messagebox.askyesno("Удаление","Удалить договор, его состав и суммы?",parent=self):
            Contract.delete_contract(cid); self.refresh_all()
            messagebox.showinfo("Успех", "Договор удалён", parent=self)

    def contract_form(self, cid=None):
        win=tk.Toplevel(self); win.title("Коллективный договор"); win.geometry("750x650")
        rows=records("SELECT * FROM Contract WHERE id=?", (cid,)) if cid else []
        old=rows[0] if rows else {}
        orgs=list_items("organizations"); agents=list_items("agents")
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
            for r in records("SELECT id,full_name,risk_category FROM Employee WHERE organization_id=? ORDER BY full_name",(oid,)):
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
                Contract.save_contract(fields["contract_number"].get(),int(fields["organization_id"].get().split(":",1)[0]),int(fields["agent_id"].get().split(":",1)[0]),fields["conclusion_date"].get(),fields["end_date"].get(),[available[i] for i in employees.curselection()],payouts,cid)
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
        for r in records("SELECT id,contract_id,employee_id,claim_date,amount,description FROM InsuranceClaim ORDER BY id"):
            self.claims.insert("","end",iid=r["id"],values=tuple(r.values()))

    def remove_claim(self):
        cid=self.selected(self.claims)
        if messagebox.askyesno("Удаление","Удалить страховой случай?",parent=self):
            InsuranceClaim.delete_claim(cid); self.refresh_claims()
            messagebox.showinfo("Успех", "Страховой случай удалён", parent=self)

    def claim_form(self, claim_id=None):
        rows=records("SELECT * FROM InsuranceClaim WHERE id=?",(claim_id,)) if claim_id else []
        old=rows[0] if rows else {}
        win=tk.Toplevel(self); win.title("Страховой случай")
        entries={}
        contract_rows = records("SELECT id, contract_number FROM Contract ORDER BY contract_number")
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
                InsuranceClaim.save_claim(int(entries["contract_id"].get().split(":", 1)[0]),int(entries["employee_id"].get().split(":", 1)[0]),entries["claim_date"].get(),entries["amount"].get(),entries["description"].get(),claim_id)
                self.refresh_claims(); win.destroy()
                messagebox.showinfo("Успех", "Страховой случай сохранён", parent=self)
            except (ValueError,sqlite3.Error) as exc: messagebox.showerror("Ошибка",str(exc),parent=win)
        ttk.Button(win,text="Сохранить",command=save).grid(columnspan=2,pady=8)

    def report_tab(self):
        frame=ttk.Frame(self.tabs,padding=8); self.tabs.add(frame,text="Отчёты")
        controls=ttk.Frame(frame); controls.pack(fill="x")
        ttk.Label(controls,text="Дата YYYY-MM-DD:").pack(side="left")
        self.report_date=ttk.Entry(controls,width=12); self.report_date.pack(side="left",padx=5)
        ttk.Label(controls,text="Код организации:").pack(side="left")
        self.report_code=ttk.Entry(controls,width=10); self.report_code.pack(side="left",padx=5)
        for label,kind in (("Договоры",1),("Агенты",2),("Суммы по категориям",3)):
            ttk.Button(controls,text=label,command=lambda k=kind:self.guard(lambda:self.report(k))).pack(side="left",padx=4)
        self.report_info = ttk.Label(frame, text="Выберите дату и постройте отчёт")
        self.report_info.pack(anchor="w", pady=8)
        self.report_tree = self.tree(frame, ("result",))

    def report(self, kind):
        selected_date=self.report_date.get()
        code_text=self.report_code.get().strip()
        if kind in (1,2) and not code_text: raise ValueError("Введите код организации")
        code=int(code_text) if code_text else None
        if kind==1:
            result=Contract.report_contracts(code,selected_date)
            if result["organization"]:
                org=result["organization"]; info=f'Дата: {selected_date} | {org["full_name"]} | {org["address"]}'
            else:
                info=f"Дата: {selected_date} | Организация не найдена"
            columns = (("contract_number", "Номер договора"), ("conclusion_date", "Начало"), ("end_date", "Окончание"))
            rows = result["contracts"]
        elif kind==2:
            result=Contract.report_agents(code,selected_date)
            info=f"Дата: {selected_date} | Код организации: {code}"
            columns = (("insurance_company", "Страховая фирма"), ("full_name", "ФИО"), ("phone_number", "Телефон"))
            rows = result["agents"]
        else:
            result=Contract.report_payouts(selected_date,code)
            info=f"Дата: {selected_date}"
            columns = (("organization", "Организация"), ("contract_number", "Договор"), ("risk_category", "Категория"), ("payout_amount", "Сумма"))
            rows = result["payouts"]
        self.report_info.configure(text=info + (" | Нет данных" if not rows else ""))
        self.report_tree.delete(*self.report_tree.get_children())
        self.report_tree.configure(columns=[key for key, _ in columns])
        for key, label in columns:
            self.report_tree.heading(key, text=label)
            self.report_tree.column(key, width=200, anchor="w")
        for row in rows:
            self.report_tree.insert("", "end", values=[row[key] for key, _ in columns])

    def seed(self):
        def run():
            result=seed_database(); self.refresh_all()
            messagebox.showinfo("Демонстрационные данные",str(result),parent=self)
        self.guard(run)
