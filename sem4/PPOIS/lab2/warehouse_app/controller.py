"""
Модуль Controller - связывает Model и View, обрабатывает события
"""
import math
from typing import List
from model import WarehouseModel, Record
from view import WarehouseView, AddRecordDialog, SearchDialog, DeleteDialog


class WarehouseController:
    """Контроллер приложения складских товаров"""

    def __init__(self, model: WarehouseModel, view: WarehouseView):
        self.model = model
        self.view = view
        self.current_page = 1

        self._setup_callbacks()
        self._refresh_display()

    def _setup_callbacks(self):
        """Настройка колбэков для событий View"""
        self.view.set_callback("new", self._on_new)
        self.view.set_callback("open", self._on_open)
        self.view.set_callback("save", self._on_save)
        self.view.set_callback("exit", self._on_exit)
        self.view.set_callback("add", self._on_add)
        self.view.set_callback("search", self._on_search)
        self.view.set_callback("delete", self._on_delete)
        self.view.set_callback("generate_test_data", self._on_generate_test_data)
        self.view.set_callback("first_page", self._on_first_page)
        self.view.set_callback("prev_page", self._on_prev_page)
        self.view.set_callback("next_page", self._on_next_page)
        self.view.set_callback("last_page", self._on_last_page)
        self.view.set_callback("per_page_changed", self._on_per_page_changed)

    def _refresh_display(self):
        """Обновить отображение с учетом пагинации"""
        all_records = self.model.get_all_records()
        total_records = len(all_records)
        records_per_page = self.view.get_records_per_page()

        if records_per_page <= 0:
            records_per_page = 10

        total_pages = math.ceil(total_records / records_per_page) if total_records > 0 else 1

        if self.current_page > total_pages:
            self.current_page = total_pages

        if self.current_page < 1:
            self.current_page = 1

        start_idx = (self.current_page - 1) * records_per_page
        end_idx = start_idx + records_per_page
        page_records = all_records[start_idx:end_idx]

        self.view.display_records(page_records, self.current_page, total_pages, total_records)

    def _on_new(self):
        """Создать новую базу данных"""
        self.model.clear_all()
        self.current_page = 1
        # Сбрасываем переменную пагинации в дефолтное значение
        self.view.per_page_var.set("10")
        self._refresh_display()
        self.view.set_status("Создана новая база данных")

    def _on_open(self):
        """Открыть файл XML"""
        filepath = self.view.ask_file_open()
        if not filepath:
            return

        success, error_msg = self.model.load_from_xml(filepath)

        if success:
            self.current_page = 1
            self._refresh_display()
            self.view.set_status(f"Загружено из {filepath}")
            self.view.show_message("Успех", f"Данные загружены из {filepath}")
        else:
            self.view.show_message("Ошибка", error_msg, "error")
            self.view.set_status("Ошибка загрузки")

    def _on_save(self):
        """Сохранить в файл XML"""
        filepath = self.view.ask_file_save()
        if not filepath:
            return

        success, error_msg = self.model.save_to_xml(filepath)

        if success:
            self.view.set_status(f"Сохранено в {filepath}")
            self.view.show_message("Успех", f"Данные сохранены в {filepath}")
        else:
            self.view.show_message("Ошибка", error_msg, "error")
            self.view.set_status("Ошибка сохранения")

    def _on_exit(self):
        """Выход из приложения"""
        self.view.root.quit()

    def _on_add(self):
        """Добавить новую запись"""
        dialog = AddRecordDialog(self.view.root)
        record = dialog.show()

        if record:
            success, error_msg = self.model.add_record(record)

            if success:
                self.current_page = 1
                self._refresh_display()
                self.view.set_status("Запись добавлена")
            else:
                self.view.show_message("Ошибка", error_msg, "error")

    def _on_search(self):
        """Открыть диалог поиска"""
        dialog = SearchDialog(self.view.root, self.model.search_records)
        dialog.show()

    def _on_delete(self):
        """Открыть диалог удаления"""
        def delete_callback(criteria):
            count = self.model.delete_records(criteria)
            if count > 0:
                self.current_page = 1
                self._refresh_display()
                self.view.set_status(f"Удалено записей: {count}")
            return count

        dialog = DeleteDialog(self.view.root, delete_callback)
        dialog.show()

    def _on_generate_test_data(self):
        """Генерация тестовых данных"""
        from test_data import generate_test_data

        test_records = generate_test_data()

        for record in test_records:
            self.model.add_record(record)

        self.current_page = 1
        self._refresh_display()
        self.view.set_status(f"Сгенерировано {len(test_records)} тестовых записей")
        self.view.show_message("Успех", f"Добавлено {len(test_records)} тестовых записей")

    def _on_first_page(self):
        """Перейти на первую страницу"""
        self.current_page = 1
        self._refresh_display()

    def _on_prev_page(self):
        """Перейти на предыдущую страницу"""
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_display()

    def _on_next_page(self):
        """Перейти на следующую страницу"""
        all_records = self.model.get_all_records()
        records_per_page = self.view.get_records_per_page()
        total_pages = math.ceil(len(all_records) / records_per_page) if len(all_records) > 0 else 1

        if self.current_page < total_pages:
            self.current_page += 1
            self._refresh_display()

    def _on_last_page(self):
        """Перейти на последнюю страницу"""
        all_records = self.model.get_all_records()
        records_per_page = self.view.get_records_per_page()
        total_pages = math.ceil(len(all_records) / records_per_page) if len(all_records) > 0 else 1

        self.current_page = total_pages
        self._refresh_display()

    def _on_per_page_changed(self):
        """Изменено количество записей на странице"""
        self.current_page = 1
        self._refresh_display()

    def run(self):
        """Запустить приложение"""
        self.view.root.mainloop()
