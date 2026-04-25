#!/usr/bin/env python3
"""
Анализатор фиктивных переменных в логике высказываний.

Лабораторная работа: Семантический анализ формул логики высказываний.
Задача: Определить, какие пропозициональные переменные являются фиктивными.

Определение: Переменная X фиктивна в формуле F, если значение истинности F
не меняется при изменении X с True на False на любых фиксированных наборах
значений остальных переменных.

Архитектура:
1. Токенизатор (Lexer) - ручной разбор строки по символам
2. Парсер (Recursive Descent) - построение AST с учетом приоритетов
3. Вычислитель (Evaluator) - рекурсивное вычисление значения формулы
4. Анализатор (Fictitious Checker) - проверка переменных на фиктивность

Ограничения: ЗАПРЕЩЕНО использовать re, eval(), exec(), sympy, lark, ply, pandas.
Разрешено: itertools, dataclasses.
"""

from dataclasses import dataclass
from enum import Enum, auto
from itertools import product
from typing import Optional


# ============================================================================
# ТОКЕНЫ
# ============================================================================

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


# ============================================================================
# ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР
# ============================================================================

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


# ============================================================================
# АБСТРАКТНОЕ СИНТАКСИЧЕСКОЕ ДЕРЕВО
# ============================================================================

@dataclass
class ASTNode:
    """Базовый класс для узлов AST."""
    pass


@dataclass
class VarNode(ASTNode):
    """Узел пропозициональной переменной."""
    name: str


@dataclass
class NotNode(ASTNode):
    """Узел отрицания."""
    operand: ASTNode


@dataclass
class BinOpNode(ASTNode):
    """Узел бинарной операции."""
    op: str
    left: ASTNode
    right: ASTNode


# ============================================================================
# СИНТАКСИЧЕСКИЙ АНАЛИЗАТОР
# ============================================================================

class ParserError(Exception):
    """Ошибка синтаксического разбора."""
    pass


class Parser:
    """
    Рекурсивный спуск с приоритетным разбором.

    Грамматика (от низкого приоритета к высокому):
      expr    := equiv
      equiv   := impl ('~' impl)*
      impl    := or ('->' impl)*
      or      := and ('V' and)*
      and     := not ('/\\' not)*
      not     := '!' not | primary
      primary := VAR | '(' expr ')'
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        """Текущий токен без продвижения."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.END)

    def _eat(self, expected_type: TokenType) -> Token:
        """Потребляет токен ожидаемого типа."""
        token = self._current()
        if token.type != expected_type:
            raise ParserError(
                f"Ожидался {expected_type.name}, найден {token.type.name}"
            )
        self.pos += 1
        return token

    def parse_expr(self) -> ASTNode:
        """expr := equiv"""
        return self.parse_equiv()

    def parse_equiv(self) -> ASTNode:
        """equiv := impl ('~' impl)*"""
        node = self.parse_impl()
        while self._current().type == TokenType.EQUIV:
            self._eat(TokenType.EQUIV)
            right = self.parse_impl()
            node = BinOpNode('~', node, right)
        return node

    def parse_impl(self) -> ASTNode:
        """impl := or ('->' impl)*"""
        node = self.parse_or()
        if self._current().type == TokenType.IMPL:
            self._eat(TokenType.IMPL)
            right = self.parse_impl()
            node = BinOpNode('->', node, right)
        return node

    def parse_or(self) -> ASTNode:
        """or := and ('V' and)*"""
        node = self.parse_and()
        while self._current().type == TokenType.OR:
            self._eat(TokenType.OR)
            right = self.parse_and()
            node = BinOpNode('V', node, right)
        return node

    def parse_and(self) -> ASTNode:
        """and := not ('/\\' not)*"""
        node = self.parse_not()
        while self._current().type == TokenType.AND:
            self._eat(TokenType.AND)
            right = self.parse_not()
            node = BinOpNode('/\\', node, right)
        return node

    def parse_not(self) -> ASTNode:
        """not := '!' not | primary"""
        if self._current().type == TokenType.NOT:
            self._eat(TokenType.NOT)
            operand = self.parse_not()
            return NotNode(operand)
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        """primary := VAR | '(' expr ')'"""
        token = self._current()

        if token.type == TokenType.VAR:
            self._eat(TokenType.VAR)
            return VarNode(name=token.value)

        if token.type == TokenType.LPAR:
            self._eat(TokenType.LPAR)
            node = self.parse_expr()
            self._eat(TokenType.RPAR)
            return node

        raise ParserError(
            f"Ожидалась переменная или '(' в позиции {self.pos}, "
            f"найден {token.type.name}"
        )

    def parse(self) -> ASTNode:
        """Главный метод: разбор формулы с проверкой END."""
        node = self.parse_expr()
        if self._current().type != TokenType.END:
            raise ParserError(
                f"Лишние символы после формулы: {self._current()}"
            )
        return node


# ============================================================================
# ВЫЧИСЛИТЕЛЬ
# ============================================================================

def collect_vars(node: ASTNode) -> set[str]:
    """Собирает все переменные из AST."""
    match node:
        case VarNode(name):
            return {name}
        case NotNode(operand):
            return collect_vars(operand)
        case BinOpNode(_, left, right):
            return collect_vars(left) | collect_vars(right)
    return set()


def evaluate(node: ASTNode, assignment: dict[str, bool]) -> bool:
    r"""
    Вычисляет истинностное значение AST при данном assignment.

    Семантика операций:
      /\ : конъюнкция (AND)
      V  : дизъюнкция (OR)
      -> : импликация (¬A ∨ B)
      ~  : эквиваленция (A ↔ B)
    """
    match node:
        case VarNode(name):
            if name not in assignment:
                raise KeyError(f"Переменная '{name}' не найдена в assignment")
            return assignment[name]

        case NotNode(operand):
            return not evaluate(operand, assignment)

        case BinOpNode(op, left, right):
            left_val = evaluate(left, assignment)
            right_val = evaluate(right, assignment)

            if op == '/\\':
                return left_val and right_val
            elif op == 'V':
                return left_val or right_val
            elif op == '->':
                return (not left_val) or right_val
            elif op == '~':
                return left_val == right_val
            else:
                raise ValueError(f"Неизвестная операция '{op}'")

    raise RuntimeError(f"Неизвестный тип узла: {type(node)}")


# ============================================================================
# АНАЛИЗАТОР ФИКТИВНЫХ ПЕРЕМЕННЫХ
# ============================================================================

def is_fictitious(formula: ASTNode, var_name: str, all_vars: list[str]) -> bool:
    """
    Проверяет, является ли переменная фиктивной в формуле.

    Алгоритм:
      1. Собрать все переменные формулы, кроме var_name.
      2. Сгенерировать все assignments для оставшихся переменных.
      3. Для каждого assignment сравнить evaluate с Var=True и Var=False.
      4. Если все совпадают → фиктивная.
    """
    other_vars = [v for v in all_vars if v != var_name]

    for values in product([False, True], repeat=len(other_vars)):
        assignment = dict(zip(other_vars, values))

        assign_true = dict(assignment)
        assign_true[var_name] = True
        val_true = evaluate(formula, assign_true)

        assign_false = dict(assignment)
        assign_false[var_name] = False
        val_false = evaluate(formula, assign_false)

        if val_true != val_false:
            return False

    return True


def find_fictitious_vars(formula: ASTNode) -> list[str]:
    """Находит все фиктивные переменные в формуле."""
    all_vars = sorted(collect_vars(formula))
    fictitious = []
    for var in all_vars:
        if is_fictitious(formula, var, all_vars):
            fictitious.append(var)
    return fictitious


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def parse_formula(formula: str) -> ASTNode:
    """Строка → AST."""
    lexer = Lexer(formula)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def analyze_formula(formula_str: str) -> tuple[list[str], list[str]]:
    """
    Анализирует формулу и возвращает все переменные и фиктивные переменные.

    Returns:
        (все_переменные, фиктивные_переменные)
    """
    ast = parse_formula(formula_str)
    all_vars = sorted(collect_vars(ast))
    fictitious = find_fictitious_vars(ast)
    return all_vars, fictitious


# ============================================================================
# ИНТЕРАКТИВНЫЙ РЕЖИМ
# ============================================================================

def main():
    """Основной цикл программы."""
    print("=" * 60)
    print("АНАЛИЗАТОР ФИКТИВНЫХ ПЕРЕМЕННЫХ")
    print("Логика высказываний")
    print("=" * 60)
    print("\nПоддерживаемый синтаксис:")
    print("  Переменные: заглавные латинские буквы (P, Q, A1, ...)")
    print("  Операции:")
    print("    !   - отрицание")
    print("    /\\  - конъюнкция")
    print("    V   - дизъюнкция")
    print("    ->  - импликация")
    print("    ~   - эквиваленция")
    print("\nВведите пустую строку для выхода\n")

    while True:
        try:
            formula = input("Формула: ").strip()

            if not formula:
                print("Выход.")
                break

            all_vars, fictitious = analyze_formula(formula)

            print(f"\nФормула: {formula}")
            print(f"Все переменные: {', '.join(all_vars) if all_vars else 'нет'}")

            if fictitious:
                print(f"Фиктивные переменные: {', '.join(fictitious)}")
            else:
                print("Фиктивных переменных нет")
            print()

        except (LexerError, ParserError) as e:
            print(f"Ошибка разбора: {e}\n")
        except Exception as e:
            print(f"Ошибка: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    main()
