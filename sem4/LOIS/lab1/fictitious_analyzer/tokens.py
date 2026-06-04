"""Токены и лексический анализатор."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TokenType(Enum):
    """Типы токенов для логических формул."""
    VAR = auto()      # переменная (P, Q, A1, ...)
    NOT = auto()      # отрицание !
    AND = auto()      # конъюнкция /\
    OR = auto()       # дизъюнкция V
    IMPL = auto()     # импликация ->
    EQUIV = auto()    # эквиваленция ~
    LPAR = auto()     # левая скобка (
    RPAR = auto()     # правая скобка )
    END = auto()      # конец строки


@dataclass
class Token:
    """Токен с типом и значением."""
    type: TokenType
    value: str = ""

    def __repr__(self):
        if self.value:
            return f"Token({self.type.name}, '{self.value}')"
        return f"Token({self.type.name})"


class LexerError(Exception):
    """Ошибка лексического разбора."""
    pass


class Lexer:
    """
    Лексический анализатор формулы.
    Преобразует строку в последовательность токенов.
    """

    ALPHABET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    ALPHANUMERIC = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self._peek()

    def _peek(self) -> Optional[str]:
        """Возвращает текущий символ без продвижения."""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def _advance(self) -> Optional[str]:
        """Сдвигает позицию и возвращает текущий символ."""
        ch = self.current_char
        self.pos += 1
        self.current_char = self._peek()
        return ch

    def _skip_whitespace(self):
        """Пропускает пробелы."""
        while self.current_char is not None and self.current_char.isspace():
            self._advance()

    def _read_var(self) -> str:
        """Читает имя переменной: заглавная буква + необязательные цифры."""
        name = ""
        while self.current_char is not None and self.current_char in self.ALPHANUMERIC:
            if not name and self.current_char not in self.ALPHABET:
                raise LexerError(
                    f"Ожидалась заглавная латинская буква, найден '{self.current_char}'"
                )
            name += self._advance()
        return name

    def get_next_token(self) -> Token:
        """Возвращает следующий токен."""
        self._skip_whitespace()

        if self.current_char is None:
            return Token(TokenType.END)

        ch = self.current_char

        if ch == '!':
            self._advance()
            return Token(TokenType.NOT, '!')

        if ch == '(':
            self._advance()
            return Token(TokenType.LPAR, '(')

        if ch == ')':
            self._advance()
            return Token(TokenType.RPAR, ')')

        if ch == '-':
            self._advance()
            if self.current_char != '>':
                raise LexerError(f"После '-' ожидалось '>', найден '{self.current_char}'")
            self._advance()
            return Token(TokenType.IMPL, '->')

        if ch == '/':
            self._advance()
            if self.current_char != '\\':
                raise LexerError(f"Ожидалось '/\\', найден '/{self.current_char}'")
            self._advance()
            return Token(TokenType.AND, '/\\')

        if ch == 'V':
            self._advance()
            return Token(TokenType.OR, 'V')

        if ch == '~':
            self._advance()
            return Token(TokenType.EQUIV, '~')

        if ch in self.ALPHABET:
            name = self._read_var()
            return Token(TokenType.VAR, name)

        raise LexerError(f"Неизвестный символ '{ch}' в позиции {self.pos}")

    def tokenize(self) -> list[Token]:
        """Токенизирует всю строку."""
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.END:
                break
        return tokens
