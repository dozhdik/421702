"""Common input normalization for newly saved records."""
import re


def required_text(value, label):
    if not isinstance(value, str):
        raise ValueError(f"Поле «{label}» должно быть текстом")
    value = " ".join(value.split())
    if not value:
        raise ValueError(f"Заполните поле «{label}»")
    if "DEMO" in value.upper():
        raise ValueError(f"Поле «{label}» не должно содержать DEMO")
    return value


def phone_number(value):
    value = required_text(value, "телефон")
    if not re.fullmatch(r"[+0-9 ()-]+", value):
        raise ValueError("Введите телефон в формате +375XXXXXXXXX")
    digits = re.sub(r"\D", "", value)
    if len(digits) != 12 or not digits.startswith("375"):
        raise ValueError("Введите телефон в формате +375XXXXXXXXX")
    return "+" + digits
