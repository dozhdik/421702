"""Узлы абстрактного синтаксического дерева."""

from dataclasses import dataclass


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
