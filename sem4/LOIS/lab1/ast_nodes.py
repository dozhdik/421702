"""
Модуль описания узлов абстрактного синтаксического дерева (AST).
Каждый тип формулы представлен соответствующим классом.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ASTNode:
    """Базовый класс для всех узлов AST."""
    pass


@dataclass
class VarNode(ASTNode):
    """Узел пропозициональной переменной."""
    name: str  # имя переменной, например "P", "Q1"


@dataclass
class NotNode(ASTNode):
    """Узел отрицания. Унарная операция."""
    operand: ASTNode


@dataclass
class BinOpNode(ASTNode):
    r"""Узел бинарной операции: /\ (конъюнкция), V (дизъюнкция), -> (импликация), ~ (эквиваленция)."""
    op: str          # символ операции
    left: ASTNode    # левый операнд
    right: ASTNode   # правый операнд


# Паттерн Посетитель для обхода дерева (для извлечения переменных)
def collect_vars(node: ASTNode) -> set[str]:
    """
    Собирает все пропозициональные переменные из AST.
    Использует рекурсивный обход дерева.
    
    Args:
        node: корень AST (или поддерева)
        
    Returns:
        Множество имён переменных
    """
    match node:
        case VarNode(name):
            return {name}
        case NotNode(operand):
            return collect_vars(operand)
        case BinOpNode(_, left, right):
            return collect_vars(left) | collect_vars(right)
    return set()