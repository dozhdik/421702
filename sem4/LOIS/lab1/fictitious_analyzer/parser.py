"""Синтаксический анализатор (Recursive Descent)."""

from .ast import ASTNode, VarNode, NotNode, BinOpNode
from .tokens import Lexer, Token, TokenType


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


def parse_formula(formula: str) -> ASTNode:
    """Строка → AST."""
    lexer = Lexer(formula)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
