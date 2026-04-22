"""
Лексический анализатор (токенизатор) для формул логики высказываний.
Преобразует строку с формулой в последовательность токенов.

Основной цикл: читаем символ → определяем тип токена → возвращаем токен.
Пробелы пропускаются. Неизвестные символы вызывают ошибку.
"""

from typing import Optional
from tokens import TokenType, ALPHABET, ALPHANUMERIC, Token


class SyntaxError(Exception):
    """Исключение при ошибке лексического разбора."""
    pass


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


class Lexer:
    """Лексический анализатор формулы."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0                     # текущая позиция в строке
        self.current_char = self._peek()  # текущий символ

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
        """
        Читает имя переменной: заглавная буква + необязательные цифры.
        Валидация: первый символ ∈ ALPHABET, последующие ∈ ALPHANUMERIC.
        """
        name = ""
        while self.current_char is not None and self.current_char in ALPHANUMERIC:
            # Первая буква обязательна
            if not name and self.current_char not in ALPHABET:
                raise SyntaxError(
                    f"Ожидалась заглавная латинская буква, найден '{self.current_char}'"
                )
            name += self._advance()
        return name

    def _read_implication(self) -> str:
        """Читает последовательность '-' и '>' для '->'."""
        op = ""
        # Ожидаем: '-' затем '>'
        if self.current_char != '-':
            raise SyntaxError(f"Ожидалось '->', найден '{self.current_char}'")
        op += self._advance()  # читаем '-'
        
        if self.current_char != '>':
            raise SyntaxError(f"После '-' ожидалось '>', найден '{self.current_char}'")
        op += self._advance()  # читаем '>'
        
        return op

    def get_next_token(self) -> Token:
        """
        Основной метод: возвращает следующий токен.
        Реализует детерминированный конечный автомат.
        """
        # Пропускаем пробелы
        self._skip_whitespace()

        if self.current_char is None:
            return Token(TokenType.END)

        ch = self.current_char

        # Отрицание: '!'
        if ch == '!':
            self._advance()
            return Token(TokenType.NOT, '!')

        # Левая скобка
        if ch == '(':
            self._advance()
            return Token(TokenType.LPAR, '(')

        # Правая скобка
        if ch == ')':
            self._advance()
            return Token(TokenType.RPAR, ')')

        # Импликация: '->'
        if ch == '-':
            op = self._read_implication()
            return Token(TokenType.IMPL, op)

        # Бинарные операции (односимвольные)
        if ch == '/':
            self._advance()
            if self.current_char != '\\':
                raise SyntaxError(f"Ожидалось '/\\', найден '/{self.current_char}'")
            self._advance()
            return Token(TokenType.AND, '/\\')

        if ch == 'V':
            self._advance()
            return Token(TokenType.OR, 'V')

        if ch == '~':
            self._advance()
            return Token(TokenType.EQUIV, '~')

        # Переменная: заглавная буква (возможно с цифрами)
        if ch in ALPHABET:
            name = self._read_var()
            return Token(TokenType.VAR, name)

        # Неизвестный символ
        raise SyntaxError(f"Неизвестный символ '{ch}' в позиции {self.pos}")

    def tokenize(self) -> list[Token]:
        """
        Токенизирует всю строку.
        Returns:
            Список токенов, завершающийся токеном END.
        """
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.END:
                break
        return tokens