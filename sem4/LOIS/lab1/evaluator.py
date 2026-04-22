r"""
Модуль вычисления истинности формулы по заданному assignment.
AST обходится рекурсивно «снизу вверх»: сначала вычисляются поддеревья,
затем применяется операция к их результатам.

Семантика бинарных операций:
  - /\ : конъюнкция (AND)
  - V  : дизъюнкция (OR)
  - -> : импликация (A → B ≡ ¬A ∨ B)
  - ~  : эквиваленция (A ↔ B ≡ (A ∧ B) ∨ (¬A ∧ ¬B))
"""

from ast_nodes import ASTNode, VarNode, NotNode, BinOpNode


def evaluate(node: ASTNode, assignment: dict[str, bool]) -> bool:
    """
    Вычисляет истинностное значение AST при данном assignment.
    
    Args:
        node: корень AST (или поддерево)
        assignment: словарь {имя_переменной: значение}
        
    Returns:
        True или False
        
    Raises:
        KeyError: если переменная из формулы отсутствует в assignment
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


def generate_assignments(variables: list[str]) -> list[dict[str, bool]]:
    """
    Генерирует все возможные assignments для заданного набора переменных.
    Количество: 2^n, где n = число переменных.
    
    Args:
        variables: список имён переменных
        
    Returns:
        Список словарей assignment (лексикографический порядок)
    """
    n = len(variables)
    assignments = []
    for bits in range(2 ** n):
        assignment = {}
        for i, var in enumerate(variables):
            # bit i из binary representation
            assignment[var] = bool((bits >> i) & 1)
        assignments.append(assignment)
    return assignments


def evaluate_all(node: ASTNode, variables: list[str]) -> list[bool]:
    """
    Вычисляет значение формулы для всех 2^n assignments.
    Возвращает список истинностных значений.
    
    Args:
        node: AST формулы
        variables: список всех переменных формулы
        
    Returns:
        Список bool значений для всех assignments
    """
    assignments = generate_assignments(variables)
    return [evaluate(node, a) for a in assignments]