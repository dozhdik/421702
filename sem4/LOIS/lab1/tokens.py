"""
Модуль определения типов токенов для логики высказываний.
Токен — элементарная единица лексического разбора формулы.
"""

from enum import Enum, auto
from typing import Optional


class TokenType(Enum):
    """Перечисление всех типов токенов."""
    VAR = auto()       # пропозициональная переменная (P, Q, A1, ...)
    NOT = auto()       # унарное отрицание !
    AND = auto()       # конъюнкция /\
    OR = auto()        # дизъюнкция V
    IMPL = auto()      # импликация ->
    EQUIV = auto()      # эквиваленция ~
    LPAR = auto()       # левая скобка (
    RPAR = auto()       # правая скобка )
    END = auto()        # конец строки


class Token:
    """Представление токена с типом и значением."""
    __slots__ = ('type', 'value')

    def __init__(self, token_type: TokenType, value: str = ""):
        self.type = token_type
        self.value = value

    def __repr__(self):
        if self.value:
            return f"Token({self.type.name}, '{self.value}')"
        return f"Token({self.type.name})"


# Множество допустимых символов в начале имени переменной
ALPHABET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Множество допустимых символов в имени переменной (после первой буквы)
ALPHANUMERIC = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")