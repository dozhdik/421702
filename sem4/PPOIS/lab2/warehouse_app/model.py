"""
Модуль Model - содержит бизнес-логику, работу с данными и XML-парсеры
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Union
import xml.sax
import xml.dom.minidom


@dataclass
class Record:
    """Класс записи о складском товаре"""
    product_name: str
    manufacturer_name: str
    unp_manufacturer: str
    quantity_in_stock: Union[int, str]
    warehouse_address: str

    def validate(self) -> tuple[bool, str]:
        """Валидация данных записи"""
        if not self.product_name.strip():
            return False, "Название товара не может быть пустым"

        if not self.manufacturer_name.strip():
            return False, "Название производителя не может быть пустым"

        if self.unp_manufacturer.strip() and not self.unp_manufacturer.isdigit():
            return False, "УНП должен содержать только цифры"

        if isinstance(self.quantity_in_stock, str):
            if self.quantity_in_stock != "нет на складе":
                return False, "Количество должно быть числом или 'нет на складе'"
        elif isinstance(self.quantity_in_stock, int):
            if self.quantity_in_stock < 0:
                return False, "Количество не может быть отрицательным"
        else:
            return False, "Неверный тип для количества"

        if not self.warehouse_address.strip():
            return False, "Адрес склада не может быть пустым"

        return True, ""


class WarehouseSAXHandler(xml.sax.ContentHandler):
    """SAX-обработчик для чтения XML"""

    def __init__(self):
        super().__init__()
        self.records: List[Record] = []
        self.current_record: Dict[str, str] = {}
        self.current_element = ""
        self.current_content = ""

    def startElement(self, name, attrs):
        self.current_element = name
        self.current_content = ""
        if name == "record":
            self.current_record = {}

    def characters(self, content):
        self.current_content += content

    def endElement(self, name):
        if name == "record":
            quantity = self.current_record.get("quantity_in_stock", "")
            if quantity == "нет на складе":
                quantity_value = quantity
            else:
                try:
                    quantity_value = int(quantity)
                except ValueError:
                    quantity_value = 0

            record = Record(
                product_name=self.current_record.get("product_name", ""),
                manufacturer_name=self.current_record.get("manufacturer_name", ""),
                unp_manufacturer=self.current_record.get("unp_manufacturer", ""),
                quantity_in_stock=quantity_value,
                warehouse_address=self.current_record.get("warehouse_address", "")
            )
            self.records.append(record)
        elif name in ["product_name", "manufacturer_name", "unp_manufacturer",
                      "quantity_in_stock", "warehouse_address"]:
            self.current_record[name] = self.current_content.strip()

        self.current_element = ""
        self.current_content = ""


class WarehouseModel:
    """Модель данных складских товаров"""

    def __init__(self):
        self.records: List[Record] = []

    def add_record(self, record: Record) -> tuple[bool, str]:
        """Добавить запись"""
        is_valid, error_msg = record.validate()
        if not is_valid:
            return False, error_msg

        self.records.append(record)
        return True, ""

    def delete_records(self, criteria: Dict[str, Any]) -> int:
        """Удалить записи по критериям"""
        matching_records = self.search_records(criteria)
        count = len(matching_records)

        for record in matching_records:
            if record in self.records:
                self.records.remove(record)

        return count

    def search_records(self, criteria: Dict[str, Any]) -> List[Record]:
        """Поиск записей по критериям (Вариант 6)"""
        if not criteria:
            return self.records.copy()

        results = []

        for record in self.records:
            match = True

            product_name = criteria.get("product_name", "").strip().lower()
            quantity = criteria.get("quantity_in_stock", "").strip()
            if product_name or quantity:
                product_match = product_name in record.product_name.lower() if product_name else False
                quantity_match = False
                if quantity:
                    if quantity == "нет на складе":
                        quantity_match = record.quantity_in_stock == "нет на складе"
                    else:
                        try:
                            qty_val = int(quantity)
                            quantity_match = record.quantity_in_stock == qty_val
                        except ValueError:
                            pass

                if not (product_match or quantity_match):
                    match = False

            manufacturer_name = criteria.get("manufacturer_name", "").strip().lower()
            unp = criteria.get("unp_manufacturer", "").strip()
            if manufacturer_name or unp:
                manufacturer_match = manufacturer_name in record.manufacturer_name.lower() if manufacturer_name else False
                unp_match = unp in record.unp_manufacturer if unp else False

                if not (manufacturer_match or unp_match):
                    match = False

            warehouse_address = criteria.get("warehouse_address", "").strip().lower()
            if warehouse_address:
                if warehouse_address not in record.warehouse_address.lower():
                    match = False

            if match:
                results.append(record)

        return results

    def get_all_records(self) -> List[Record]:
        """Получить все записи"""
        return self.records.copy()

    def clear_all(self):
        """Очистить все записи"""
        self.records.clear()

    def save_to_xml(self, filepath: str) -> tuple[bool, str]:
        """Сохранить в XML используя DOM"""
        try:
            doc = xml.dom.minidom.Document()

            root = doc.createElement("warehouse_db")
            doc.appendChild(root)

            for record in self.records:
                record_elem = doc.createElement("record")

                product_name_elem = doc.createElement("product_name")
                product_name_elem.appendChild(doc.createTextNode(record.product_name))
                record_elem.appendChild(product_name_elem)

                manufacturer_name_elem = doc.createElement("manufacturer_name")
                manufacturer_name_elem.appendChild(doc.createTextNode(record.manufacturer_name))
                record_elem.appendChild(manufacturer_name_elem)

                unp_elem = doc.createElement("unp_manufacturer")
                unp_elem.appendChild(doc.createTextNode(record.unp_manufacturer))
                record_elem.appendChild(unp_elem)

                quantity_elem = doc.createElement("quantity_in_stock")
                quantity_text = str(record.quantity_in_stock)
                quantity_elem.appendChild(doc.createTextNode(quantity_text))
                record_elem.appendChild(quantity_elem)

                address_elem = doc.createElement("warehouse_address")
                address_elem.appendChild(doc.createTextNode(record.warehouse_address))
                record_elem.appendChild(address_elem)

                root.appendChild(record_elem)

            xml_str = doc.toprettyxml(indent="    ", encoding="UTF-8")

            with open(filepath, "wb") as f:
                f.write(xml_str)

            return True, ""

        except Exception as e:
            return False, f"Ошибка сохранения: {str(e)}"

    def load_from_xml(self, filepath: str) -> tuple[bool, str]:
        """Загрузить из XML используя SAX"""
        try:
            handler = WarehouseSAXHandler()
            xml.sax.parse(filepath, handler)

            self.records = handler.records
            return True, ""

        except FileNotFoundError:
            return False, "Файл не найден"
        except xml.sax.SAXException as e:
            return False, f"Ошибка парсинга XML: {str(e)}"
        except Exception as e:
            return False, f"Ошибка загрузки: {str(e)}"
