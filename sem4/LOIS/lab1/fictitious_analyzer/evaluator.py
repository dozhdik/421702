"""Вычислитель истинностных значений AST."""

from .ast import ASTNode, VarNode, NotNode, BinOpNode


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
