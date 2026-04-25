# Контекст проекта: Управление складскими товарами

## Общая информация

**Название:** Приложение управления складскими товарами  
**Лабораторная работа:** №2, Вариант 6  
**Архитектура:** Model-View-Controller (MVC)  
**Язык:** Python 3.10+  
**GUI Framework:** tkinter с ttk виджетами  
**Формат данных:** XML (SAX для чтения, DOM для записи)

## Структура проекта

```
warehouse_app/
├── main.py           # Точка входа приложения
├── model.py          # Модель данных и XML-парсеры
├── view.py           # Представление (UI компоненты)
├── controller.py     # Контроллер (связка Model-View)
├── test_data.py      # Генератор тестовых данных (54 записи)
└── CONTEXT.md        # Этот файл
```

## Архитектура MVC

### Model (model.py)

**Класс `Record`** (dataclass):
- `product_name: str` — Название товара
- `manufacturer_name: str` — Название производителя
- `unp_manufacturer: str` — УНП производителя (строка, только цифры)
- `quantity_in_stock: Union[int, str]` — Количество (int >= 0 или "нет на складе")
- `warehouse_address: str` — Адрес склада

**Метод `validate() -> tuple[bool, str]`:**
- Проверяет корректность всех полей
- Возвращает (успех, сообщение об ошибке)

**Класс `WarehouseSAXHandler`** (xml.sax.ContentHandler):
- Парсит XML файлы в список объектов Record
- Обрабатывает события: startElement, characters, endElement
- Корректно обрабатывает смешанный тип quantity_in_stock

**Класс `WarehouseModel`:**

Методы:
- `add_record(record: Record) -> tuple[bool, str]` — Добавить запись с валидацией
- `delete_records(criteria: Dict[str, Any]) -> int` — Удалить записи по критериям, возвращает количество
- `search_records(criteria: Dict[str, Any]) -> List[Record]` — Поиск по критериям
- `get_all_records() -> List[Record]` — Получить все записи
- `clear_all()` — Очистить базу
- `save_to_xml(filepath: str) -> tuple[bool, str]` — Сохранить в XML (DOM)
- `load_from_xml(filepath: str) -> tuple[bool, str]` — Загрузить из XML (SAX)

### View (view.py)

**Класс `WarehouseView`:**

Главное окно с компонентами:
- Меню: Файл, Правка, Данные, Справка
- Панель инструментов с кнопками
- `ttk.Treeview` для отображения записей
- Пагинация: кнопки навигации, spinbox для записей на странице
- Строка состояния

Методы:
- `display_records(records, page, total_pages, total_records)` — Отобразить страницу записей
- `get_records_per_page() -> int` — Получить количество записей на странице
- `show_message(title, message, msg_type)` — Показать диалог
- `ask_file_open() -> Optional[str]` — Диалог открытия файла
- `ask_file_save() -> Optional[str]` — Диалог сохранения файла
- `set_status(text)` — Установить текст статуса
- `set_callback(event_name, callback)` — Установить обработчик события

**Класс `AddRecordDialog`:**
- Диалог добавления/редактирования записи
- Специальная обработка quantity_in_stock: чекбокс "Нет на складе" + поле ввода
- Валидация перед возвратом результата
- Метод `show() -> Optional[Record]`

**Класс `SearchDialog`:**
- Диалог поиска с полями критериев
- Отдельный Treeview для результатов
- Метод `show()` — модальное окно

**Класс `DeleteDialog`:**
- Диалог удаления по критериям
- Показывает количество удаленных записей
- Метод `show()` — модальное окно

### Controller (controller.py)

**Класс `WarehouseController`:**

Связывает Model и View, обрабатывает события:
- `_on_new()` — Создать новую БД
- `_on_open()` — Открыть XML файл
- `_on_save()` — Сохранить в XML
- `_on_add()` — Добавить запись
- `_on_search()` — Открыть диалог поиска
- `_on_delete()` — Открыть диалог удаления
- `_on_generate_test_data()` — Генерировать тестовые данные
- `_on_first_page()`, `_on_prev_page()`, `_on_next_page()`, `_on_last_page()` — Навигация по страницам
- `_on_per_page_changed()` — Изменение количества записей на странице
- `_refresh_display()` — Обновить отображение с пагинацией
- `run()` — Запустить главный цикл

## Логика фильтрации (Вариант 6)

Метод `search_records(criteria)` в Model реализует следующую логику:

1. **По названию товара ИЛИ количеству на складе:**
   - Если указано `product_name` — поиск подстроки (case-insensitive)
   - Если указано `quantity_in_stock` — точное совпадение (int или "нет на складе")
   - Условие: хотя бы одно из двух должно совпадать (OR)

2. **По названию производителя ИЛИ УНП:**
   - Если указано `manufacturer_name` — поиск подстроки (case-insensitive)
   - Если указано `unp_manufacturer` — поиск подстроки
   - Условие: хотя бы одно из двух должно совпадать (OR)

3. **По адресу склада:**
   - Если указано `warehouse_address` — поиск подстроки (case-insensitive)

Все группы критериев объединяются логическим **И** (AND).

## Формат XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<warehouse_db>
    <record>
        <product_name>Дрель Bosch Professional GSB 13 RE</product_name>
        <manufacturer_name>Bosch GmbH</manufacturer_name>
        <unp_manufacturer>193567821</unp_manufacturer>
        <quantity_in_stock>45</quantity_in_stock>
        <warehouse_address>Минск, ул. Промышленная, 10</warehouse_address>
    </record>
    <record>
        <product_name>Молоток стальной 500г</product_name>
        <manufacturer_name>ООО Местные Инструменты</manufacturer_name>
        <unp_manufacturer>298765432</unp_manufacturer>
        <quantity_in_stock>нет на складе</quantity_in_stock>
        <warehouse_address>Гомель, ул. Торговая, 5</warehouse_address>
    </record>
</warehouse_db>
```

## Пагинация

Реализована в Controller:
- Вычисление общего количества страниц: `math.ceil(total_records / records_per_page)`
- Извлечение записей для текущей страницы: `records[start_idx:end_idx]`
- При изменении данных (добавление/удаление/загрузка) сброс на страницу 1
- Навигация: первая, предыдущая, следующая, последняя страница
- Изменение количества записей на странице через Spinbox

## Тестовые данные

Файл `test_data.py` содержит функцию `generate_test_data()`, которая возвращает 54 реалистичные записи:
- Различные инструменты (дрели, шуруповерты, пилы, и т.д.)
- Реальные производители (Bosch, Makita, DeWalt, Hitachi, и др.)
- Реалистичные УНП (9-значные числа)
- Различные количества (включая "нет на складе")
- Адреса складов в разных городах Беларуси

## Запуск приложения

```bash
cd warehouse_app
python main.py
```

Или:
```bash
python warehouse_app/main.py
```

## Требования

- Python 3.10 или выше
- tkinter (обычно входит в стандартную установку Python)
- Стандартные библиотеки: xml.sax, xml.dom.minidom, dataclasses, typing, math

## Особенности реализации

1. **Строгое разделение MVC:**
   - Model не импортирует tkinter
   - View не содержит бизнес-логики
   - Controller связывает Model и View через колбэки

2. **Обработка смешанного типа quantity_in_stock:**
   - В UI: чекбокс блокирует/разблокирует поле ввода
   - В Model: валидация проверяет int >= 0 или строку "нет на складе"
   - В XML: сохраняется как текст, при загрузке преобразуется в нужный тип

3. **Обработка ошибок:**
   - Все операции с файлами возвращают tuple[bool, str]
   - Валидация данных перед добавлением
   - Пользовательские сообщения об ошибках через messagebox

4. **UX улучшения:**
   - Строка состояния показывает текущую операцию
   - Диалоги модальные (transient + grab_set)
   - Результаты поиска отображаются в отдельном окне
   - Подтверждение количества удаленных записей

## Возможные расширения

- Редактирование существующих записей (двойной клик на строке)
- Сортировка по столбцам в Treeview
- Экспорт в другие форматы (CSV, JSON)
- Импорт из других форматов
- История операций (undo/redo)
- Расширенные фильтры (диапазоны, регулярные выражения)
