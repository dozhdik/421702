"""
Рекурсивный спуск — парсер формул логики высказываний.
Преобразует последовательность токенов в абстрактное синтаксическое дерево (AST).

Грамматика (от низкого приоритета к высокому):
  expr    := equiv
  equiv   := impl ('~' impl)*
  impl    := or ('->' or)*
  or      := and ('V' and)*
  and     := not ('/\\' not)*
  not     := '!' not | primary
  primary := VAR | '(' expr ')'

Левые факторизации и левые рекурсии устранены для LL(1)-парсинга.
"""

from tokens import TokenType, Token
from ast_nodes import ASTNode, VarNode, NotNode, BinOpNode


class SyntaxError(Exception):
    """Исключение при ошибке синтаксического разбора."""
    pass


class Parser:
    """
    Рекурсивный спуск с приоритетным предиктивным разбором.
    Использует метод рекурсивного спуска (top-down parsing).
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
        """
        Потребляет токен ожидаемого типа.
        Raises:
            SyntaxError: если тип не совпадает
        """
        token = self._current()
        if token.type != expected_type:
            raise SyntaxError(
                f"Ожидался {expected_type.name}, найден {token.type.name}"
            )
        self.pos += 1
        return token

    # --- Грамматические правила ---

    def parse_expr(self) -> ASTNode:
        """expr := equiv — точка входа."""
        return self.parse_equiv()

    def parse_equiv(self) -> ASTNode:
        """
        equiv := impl ('~' impl)*
        Левый ассоциативный разбор эквиваленции.
        """
        node = self.parse_impl()
        while self._current().type == TokenType.EQUIV:
            self._eat(TokenType.EQUIV)
            right = self.parse_impl()
            node = BinOpNode('~', node, right)
        return node

    def parse_impl(self) -> ASTNode:
        """
        impl := or ('->' or)*
        Правоассоциативная импликация: A -> B -> C трактуется как A -> (B -> C)
        """
        node = self.parse_or()
        while self._current().type == TokenType.IMPL:
            self._eat(TokenType.IMPL)
            right = self.parse_impl()  # рекурсия вправо
            node = BinOpNode('->', node, right)
        return node

    def parse_or(self) -> ASTNode:
        """
        or := and ('V' and)*
        Левая ассоциативность дизъюнкции.
        """
        node = self.parse_and()
        while self._current().type == TokenType.OR:
            self._eat(TokenType.OR)
            right = self.parse_and()
            node = BinOpNode('V', node, right)
        return node

    def parse_and(self) -> ASTNode:
        """
        and := not ('/\\' not)*
        Левая ассоциативность конъюнкции.
        """
        node = self.parse_not()
        while self._current().type == TokenType.AND:
            self._eat(TokenType.AND)
            right = self.parse_not()
            node = BinOpNode('/\\', node, right)
        return node

    def parse_not(self) -> ASTNode:
        """
        not := '!' not | primary
        Унарное отрицание правоассоциативно: !!!A — это !(!(!A)).
        """
        if self._current().type == TokenType.NOT:
            self._eat(TokenType.NOT)
            operand = self.parse_not()
            return NotNode(operand)
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        """
        primary := VAR | '(' expr ')'
        Базовые случаи: переменная или формула в скобках.
        """
        token = self._current()

        if token.type == TokenType.VAR:
            self._eat(TokenType.VAR)
            return VarNode(name=token.value)

        if token.type == TokenType.LPAR:
            self._eat(TokenType.LPAR)
            node = self.parse_expr()
            self._eat(TokenType.RPAR)
            return node

        raise SyntaxError(
            f"Ожидалась переменная или '(' в позиции {self.pos}, "
            f"найден {token.type.name}"
        )

    def parse(self) -> ASTNode:
        """
        Главный метод: разбор формулы с проверкой END.
        """
        node = self.parse_expr()
        if self._current().type != TokenType.END:
            raise SyntaxError(
                f"Лишние символы после формулы: {self._current()}"
            )
        return node


def parse_formula(formula: str) -> ASTNode:
    """
    Внешняя функция: строка → AST.
    Объединяет лексер и парсер.
    
    Args:
        formula: строка с формулой
    Returns:
        Корень AST
    Raises:
        (SyntaxError) при ошибках разбора
    """
    from lexer import Lexer
    lexer = Lexer(formula)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()