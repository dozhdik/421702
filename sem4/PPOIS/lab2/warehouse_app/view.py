"""
Модуль View - содержит все элементы пользовательского интерфейса
"""
import tkinter as tk
import tkinter.font
from tkinter import ttk, messagebox, filedialog
from typing import List, Callable, Dict, Any, Optional
from model import Record


class WarehouseView:
    """Представление приложения складских товаров"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Управление складскими товарами")
        self.root.geometry("1400x750")

        self.current_page = 1
        self.records_per_page = 10
        self.total_pages = 1
        self.total_records = 0

        self.callbacks: Dict[str, Callable] = {}

        # Настройка стиля для увеличения высоты строк
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=('TkDefaultFont', 10))

        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_view()
        self._setup_pagination()
        self._setup_statusbar()

    def _setup_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый", command=lambda: self._trigger_callback("new"))
        file_menu.add_command(label="Открыть...", command=lambda: self._trigger_callback("open"))
        file_menu.add_command(label="Сохранить...", command=lambda: self._trigger_callback("save"))
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=lambda: self._trigger_callback("exit"))

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Добавить запись", command=lambda: self._trigger_callback("add"))
        edit_menu.add_command(label="Поиск", command=lambda: self._trigger_callback("search"))
        edit_menu.add_command(label="Удалить", command=lambda: self._trigger_callback("delete"))

        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Данные", menu=data_menu)
        data_menu.add_command(label="Генерировать тестовые данные",
                             command=lambda: self._trigger_callback("generate_test_data"))

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)

    def _setup_toolbar(self):
        """Создание панели инструментов"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Новый", command=lambda: self._trigger_callback("new")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Открыть", command=lambda: self._trigger_callback("open")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Сохранить", command=lambda: self._trigger_callback("save")).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Добавить", command=lambda: self._trigger_callback("add")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Поиск", command=lambda: self._trigger_callback("search")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Удалить", command=lambda: self._trigger_callback("delete")).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Тестовые данные",
                  command=lambda: self._trigger_callback("generate_test_data")).pack(side=tk.LEFT, padx=2)

    def _setup_main_view(self):
        """Создание основного представления с таблицей"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("product_name", "manufacturer_name", "unp_manufacturer",
                  "quantity_in_stock", "warehouse_address")

        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)

        self.tree.heading("product_name", text="Название товара")
        self.tree.heading("manufacturer_name", text="Производитель")
        self.tree.heading("unp_manufacturer", text="УНП")
        self.tree.heading("quantity_in_stock", text="Количество")
        self.tree.heading("warehouse_address", text="Адрес склада")

        self.tree.column("product_name", width=350, stretch=True, minwidth=200)
        self.tree.column("manufacturer_name", width=250, stretch=True, minwidth=150)
        self.tree.column("unp_manufacturer", width=120, stretch=False, minwidth=100)
        self.tree.column("quantity_in_stock", width=150, stretch=False, minwidth=100)
        self.tree.column("warehouse_address", width=400, stretch=True, minwidth=200)

        vsb = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

    def _setup_pagination(self):
        """Создание элементов управления пагинацией"""
        pagination_frame = ttk.Frame(self.root)
        pagination_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(pagination_frame, text="<<", width=5,
                  command=lambda: self._trigger_callback("first_page")).pack(side=tk.LEFT, padx=2)
        ttk.Button(pagination_frame, text="<", width=5,
                  command=lambda: self._trigger_callback("prev_page")).pack(side=tk.LEFT, padx=2)

        self.page_label = ttk.Label(pagination_frame, text="Страница 1 из 1")
        self.page_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(pagination_frame, text=">", width=5,
                  command=lambda: self._trigger_callback("next_page")).pack(side=tk.LEFT, padx=2)
        ttk.Button(pagination_frame, text=">>", width=5,
                  command=lambda: self._trigger_callback("last_page")).pack(side=tk.LEFT, padx=2)

        ttk.Label(pagination_frame, text="Записей на странице:").pack(side=tk.LEFT, padx=(20, 5))

        self.per_page_var = tk.StringVar(value="10")
        per_page_spinbox = ttk.Spinbox(pagination_frame, from_=1, to=100, width=10,
                                       textvariable=self.per_page_var,
                                       command=lambda: self._trigger_callback("per_page_changed"))
        per_page_spinbox.pack(side=tk.LEFT, padx=2)

        self.records_label = ttk.Label(pagination_frame, text="Всего записей: 0")
        self.records_label.pack(side=tk.RIGHT, padx=10)

    def _setup_statusbar(self):
        """Создание строки состояния"""
        self.statusbar = ttk.Label(self.root, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_callback(self, event_name: str, callback: Callable):
        """Установить колбэк для события"""
        self.callbacks[event_name] = callback

    def _trigger_callback(self, event_name: str, *args, **kwargs):
        """Вызвать колбэк"""
        if event_name in self.callbacks:
            self.callbacks[event_name](*args, **kwargs)

    def auto_resize_columns(self):
        """Автоматическое изменение размера колонок на основе содержимого"""
        try:
            # Создаем шрифт с явными параметрами для точного измерения
            font = tkinter.font.Font(family="TkDefaultFont", size=10)

            for col in self.tree['columns']:
                # Получаем текст заголовка
                header_text = self.tree.heading(col)['text']
                # Увеличиваем padding для заголовка
                header_width = font.measure(header_text) + 120

                max_width = header_width

                # Проверяем ширину всех значений в колонке
                for item in self.tree.get_children():
                    item_text = str(self.tree.set(item, col))
                    # Измеряем ширину текста и добавляем значительный padding
                    # Используем коэффициент 1.3 для дополнительного запаса
                    item_width = int(font.measure(item_text) * 1.3) + 120
                    if item_width > max_width:
                        max_width = item_width

                # Устанавливаем ширину колонки
                # Не ограничиваем максимальную ширину, чтобы весь текст поместился
                self.tree.column(col, width=max_width, minwidth=150)
        except Exception as e:
            # Если что-то пошло не так, устанавливаем широкие значения по умолчанию
            print(f"Ошибка при изменении размера колонок: {e}")
            self.tree.column("product_name", width=450)
            self.tree.column("manufacturer_name", width=350)
            self.tree.column("unp_manufacturer", width=150)
            self.tree.column("quantity_in_stock", width=150)
            self.tree.column("warehouse_address", width=500)

    def display_records(self, records: List[Record], page: int, total_pages: int, total_records: int):
        """Отобразить записи в таблице"""
        self.tree.delete(*self.tree.get_children())

        for record in records:
            self.tree.insert("", tk.END, values=(
                record.product_name,
                record.manufacturer_name,
                record.unp_manufacturer,
                str(record.quantity_in_stock),
                record.warehouse_address
            ))

        self.auto_resize_columns()

        self.current_page = page
        self.total_pages = total_pages
        self.total_records = total_records

        self.page_label.config(text=f"Страница {page} из {total_pages}")
        self.records_label.config(text=f"Всего записей: {total_records}")

    def get_records_per_page(self) -> int:
        """Получить количество записей на странице"""
        try:
            val = self.per_page_var.get()
            if not val or val == "":
                return 10
            return int(val)
        except (ValueError, tk.TclError):
            return 10

    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """Показать сообщение"""
        if msg_type == "info":
            messagebox.showinfo(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        elif msg_type == "error":
            messagebox.showerror(title, message)

    def ask_file_open(self) -> Optional[str]:
        """Диалог открытия файла"""
        return filedialog.askopenfilename(
            title="Открыть файл",
            filetypes=[("XML файлы", "*.xml"), ("Все файлы", "*.*")]
        )

    def ask_file_save(self) -> Optional[str]:
        """Диалог сохранения файла"""
        return filedialog.asksaveasfilename(
            title="Сохранить файл",
            defaultextension=".xml",
            filetypes=[("XML файлы", "*.xml"), ("Все файлы", "*.*")]
        )

    def set_status(self, text: str):
        """Установить текст в строке состояния"""
        self.statusbar.config(text=text)

    def _show_about(self):
        """Показать окно О программе"""
        messagebox.showinfo(
            "О программе",
            "Управление складскими товарами\n\n"
            "Лабораторная работа №2\n"
            "Вариант 6\n\n"
            "Архитектура: MVC\n"
            "Python 3.10+ | tkinter"
        )


class AddRecordDialog:
    """Диалог добавления/редактирования записи"""

    def __init__(self, parent: tk.Tk, record: Optional[Record] = None):
        self.result: Optional[Record] = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить запись" if record is None else "Редактировать запись")
        self.dialog.geometry("850x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Центрирование окна
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (850 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.dialog.geometry(f"850x500+{x}+{y}")

        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Название товара:").grid(row=0, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.product_name_var = tk.StringVar(value=record.product_name if record else "")
        ttk.Entry(main_frame, textvariable=self.product_name_var, width=60).grid(row=0, column=1, pady=8, sticky=tk.EW)

        ttk.Label(main_frame, text="Производитель:").grid(row=1, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.manufacturer_name_var = tk.StringVar(value=record.manufacturer_name if record else "")
        ttk.Entry(main_frame, textvariable=self.manufacturer_name_var, width=60).grid(row=1, column=1, pady=8, sticky=tk.EW)

        ttk.Label(main_frame, text="УНП производителя:").grid(row=2, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.unp_var = tk.StringVar(value=record.unp_manufacturer if record else "")
        ttk.Entry(main_frame, textvariable=self.unp_var, width=60).grid(row=2, column=1, pady=8, sticky=tk.EW)

        ttk.Label(main_frame, text="Количество:").grid(row=3, column=0, sticky=tk.W, pady=8, padx=(0, 10))

        quantity_frame = ttk.Frame(main_frame)
        quantity_frame.grid(row=3, column=1, sticky=tk.W, pady=8)

        self.quantity_var = tk.StringVar()
        self.out_of_stock_var = tk.BooleanVar(value=False)

        if record and record.quantity_in_stock == "нет на складе":
            self.out_of_stock_var.set(True)
            self.quantity_var.set("")
        elif record:
            self.quantity_var.set(str(record.quantity_in_stock))

        self.quantity_entry = ttk.Entry(quantity_frame, textvariable=self.quantity_var, width=15)
        self.quantity_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Checkbutton(quantity_frame, text="Нет на складе",
                       variable=self.out_of_stock_var,
                       command=self._toggle_quantity).pack(side=tk.LEFT)

        ttk.Label(main_frame, text="Адрес склада:").grid(row=4, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.warehouse_address_var = tk.StringVar(value=record.warehouse_address if record else "")
        ttk.Entry(main_frame, textvariable=self.warehouse_address_var, width=60).grid(row=4, column=1, pady=8, sticky=tk.EW)

        main_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self._on_cancel).pack(side=tk.LEFT, padx=5)

        self._toggle_quantity()

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _toggle_quantity(self):
        """Переключение состояния поля количества"""
        if self.out_of_stock_var.get():
            self.quantity_entry.config(state="disabled")
            self.quantity_var.set("")
        else:
            self.quantity_entry.config(state="normal")

    def _on_ok(self):
        """Обработка нажатия OK"""
        product_name = self.product_name_var.get().strip()
        manufacturer_name = self.manufacturer_name_var.get().strip()
        unp = self.unp_var.get().strip()
        warehouse_address = self.warehouse_address_var.get().strip()

        if not product_name:
            messagebox.showerror("Ошибка", "Название товара не может быть пустым")
            return

        if not manufacturer_name:
            messagebox.showerror("Ошибка", "Название производителя не может быть пустым")
            return

        if unp and not unp.isdigit():
            messagebox.showerror("Ошибка", "УНП должен содержать только цифры")
            return

        if self.out_of_stock_var.get():
            quantity = "нет на складе"
        else:
            quantity_str = self.quantity_var.get().strip()
            if not quantity_str:
                messagebox.showerror("Ошибка", "Укажите количество или отметьте 'Нет на складе'")
                return
            try:
                quantity = int(quantity_str)
                if quantity < 0:
                    messagebox.showerror("Ошибка", "Количество не может быть отрицательным")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Количество должно быть целым числом")
                return

        if not warehouse_address:
            messagebox.showerror("Ошибка", "Адрес склада не может быть пустым")
            return

        self.result = Record(
            product_name=product_name,
            manufacturer_name=manufacturer_name,
            unp_manufacturer=unp,
            quantity_in_stock=quantity,
            warehouse_address=warehouse_address
        )

        self.dialog.destroy()

    def _on_cancel(self):
        """Обработка отмены"""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Record]:
        """Показать диалог и вернуть результат"""
        self.dialog.wait_window()
        return self.result


class SearchDialog:
    """Диалог поиска записей"""

    def __init__(self, parent: tk.Tk, search_callback: Callable):
        self.search_callback = search_callback
        self.all_results = []
        self.current_page = 1
        self.results_per_page = 10

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Поиск записей")
        self.dialog.geometry("1400x750")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)

        # Центрирование окна
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (1400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (750 // 2)
        self.dialog.geometry(f"1400x750+{x}+{y}")

        criteria_frame = ttk.LabelFrame(self.dialog, text="Критерии поиска", padding=10)
        criteria_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(criteria_frame, text="Название товара:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.product_name_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.product_name_var, width=30).grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(criteria_frame, text="Количество:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.quantity_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.quantity_var, width=20).grid(row=0, column=3, pady=5, padx=5)

        ttk.Label(criteria_frame, text="Производитель:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.manufacturer_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.manufacturer_var, width=30).grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(criteria_frame, text="УНП:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.unp_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.unp_var, width=20).grid(row=1, column=3, pady=5, padx=5)

        ttk.Label(criteria_frame, text="Адрес склада:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.address_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.address_var, width=30).grid(row=2, column=1, pady=5, padx=5)

        ttk.Button(criteria_frame, text="Найти", command=self._perform_search).grid(row=2, column=3, pady=5, padx=5)

        results_frame = ttk.LabelFrame(self.dialog, text="Результаты поиска", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("product_name", "manufacturer_name", "unp_manufacturer",
                  "quantity_in_stock", "warehouse_address")

        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)

        self.results_tree.heading("product_name", text="Название товара")
        self.results_tree.heading("manufacturer_name", text="Производитель")
        self.results_tree.heading("unp_manufacturer", text="УНП")
        self.results_tree.heading("quantity_in_stock", text="Количество")
        self.results_tree.heading("warehouse_address", text="Адрес склада")

        self.results_tree.column("product_name", width=180, stretch=True)
        self.results_tree.column("manufacturer_name", width=150, stretch=True)
        self.results_tree.column("unp_manufacturer", width=100, stretch=False)
        self.results_tree.column("quantity_in_stock", width=100, stretch=False)
        self.results_tree.column("warehouse_address", width=250, stretch=True)

        vsb = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.results_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Пагинация для результатов поиска
        pagination_frame = ttk.Frame(self.dialog)
        pagination_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(pagination_frame, text="<", width=5, command=self._prev_page).pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(pagination_frame, text="Страница 1 из 1")
        self.page_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(pagination_frame, text=">", width=5, command=self._next_page).pack(side=tk.LEFT, padx=2)

        self.results_count_label = ttk.Label(pagination_frame, text="Найдено: 0")
        self.results_count_label.pack(side=tk.RIGHT, padx=10)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Закрыть", command=self.dialog.destroy).pack(side=tk.RIGHT)

    def _auto_resize_search_columns(self):
        """Автоматическое изменение размера колонок результатов поиска"""
        try:
            font = tkinter.font.Font(family='TkDefaultFont', size=10)

            for col in self.results_tree['columns']:
                header_text = self.results_tree.heading(col)['text']
                header_width = int(font.measure(header_text) * 1.3) + 100

                max_width = header_width

                for item in self.results_tree.get_children():
                    item_text = str(self.results_tree.set(item, col))
                    item_width = int(font.measure(item_text) * 1.3) + 100
                    if item_width > max_width:
                        max_width = item_width

                self.results_tree.column(col, width=max_width, minwidth=100)
        except Exception:
            pass

    def _prev_page(self):
        """Предыдущая страница результатов"""
        if self.current_page > 1:
            self.current_page -= 1
            self._display_results_page()

    def _next_page(self):
        """Следующая страница результатов"""
        total_pages = (len(self.all_results) + self.results_per_page - 1) // self.results_per_page
        if total_pages == 0:
            total_pages = 1
        if self.current_page < total_pages:
            self.current_page += 1
            self._display_results_page()

    def _display_results_page(self):
        """Отобразить текущую страницу результатов"""
        self.results_tree.delete(*self.results_tree.get_children())

        start_idx = (self.current_page - 1) * self.results_per_page
        end_idx = start_idx + self.results_per_page
        page_results = self.all_results[start_idx:end_idx]

        for record in page_results:
            self.results_tree.insert("", tk.END, values=(
                record.product_name,
                record.manufacturer_name,
                record.unp_manufacturer,
                str(record.quantity_in_stock),
                record.warehouse_address
            ))

        self._auto_resize_search_columns()

        total_pages = (len(self.all_results) + self.results_per_page - 1) // self.results_per_page
        if total_pages == 0:
            total_pages = 1
        self.page_label.config(text=f"Страница {self.current_page} из {total_pages}")
        self.results_count_label.config(text=f"Найдено: {len(self.all_results)}")

    def _perform_search(self):
        """Выполнить поиск"""
        criteria = {
            "product_name": self.product_name_var.get().strip(),
            "quantity_in_stock": self.quantity_var.get().strip(),
            "manufacturer_name": self.manufacturer_var.get().strip(),
            "unp_manufacturer": self.unp_var.get().strip(),
            "warehouse_address": self.address_var.get().strip()
        }

        criteria = {k: v for k, v in criteria.items() if v}

        self.all_results = self.search_callback(criteria)
        self.current_page = 1
        self._display_results_page()

    def show(self):
        """Показать диалог"""
        self.dialog.wait_window()


class DeleteDialog:
    """Диалог удаления записей"""

    def __init__(self, parent: tk.Tk, delete_callback: Callable):
        self.delete_callback = delete_callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Удаление записей")
        self.dialog.geometry("850x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Центрирование окна
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (850 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.dialog.geometry(f"850x500+{x}+{y}")

        criteria_frame = ttk.LabelFrame(self.dialog, text="Критерии удаления (Вариант 6)", padding=15)
        criteria_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(criteria_frame, text="Название товара:").grid(row=0, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.product_name_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.product_name_var, width=60).grid(row=0, column=1, pady=8, sticky=tk.EW)

        ttk.Label(criteria_frame, text="Количество:").grid(row=1, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.quantity_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.quantity_var, width=60).grid(row=1, column=1, pady=8, sticky=tk.EW)

        ttk.Label(criteria_frame, text="Производитель:").grid(row=2, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.manufacturer_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.manufacturer_var, width=60).grid(row=2, column=1, pady=8, sticky=tk.EW)

        ttk.Label(criteria_frame, text="УНП:").grid(row=3, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.unp_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.unp_var, width=60).grid(row=3, column=1, pady=8, sticky=tk.EW)

        ttk.Label(criteria_frame, text="Адрес склада:").grid(row=4, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.address_var = tk.StringVar()
        ttk.Entry(criteria_frame, textvariable=self.address_var, width=60).grid(row=4, column=1, pady=8, sticky=tk.EW)

        criteria_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Удалить", command=self._perform_delete, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def _perform_delete(self):
        """Выполнить удаление"""
        criteria = {
            "product_name": self.product_name_var.get().strip(),
            "quantity_in_stock": self.quantity_var.get().strip(),
            "manufacturer_name": self.manufacturer_var.get().strip(),
            "unp_manufacturer": self.unp_var.get().strip(),
            "warehouse_address": self.address_var.get().strip()
        }

        criteria = {k: v for k, v in criteria.items() if v}

        if not criteria:
            messagebox.showwarning("Предупреждение", "Укажите хотя бы один критерий для удаления")
            return

        count = self.delete_callback(criteria)

        if count > 0:
            messagebox.showinfo("Удаление", f"Удалено записей: {count}")
        else:
            messagebox.showinfo("Удаление", "Записи не найдены")

        self.dialog.destroy()

    def show(self):
        """Показать диалог"""
        self.dialog.wait_window()
