"""Анализатор фиктивных переменных в логике высказываний."""

from .tokens import TokenType, Token, Lexer, LexerError
from .ast import ASTNode, VarNode, NotNode, BinOpNode
from .parser import Parser, ParserError, parse_formula
from .evaluator import collect_vars, evaluate
from .analyzer import is_fictitious, find_fictitious_vars

__all__ = [
    "TokenType", "Token", "Lexer", "LexerError",
    "ASTNode", "VarNode", "NotNode", "BinOpNode",
    "Parser", "ParserError", "parse_formula",
    "collect_vars", "evaluate",
    "is_fictitious", "find_fictitious_vars",
]


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
