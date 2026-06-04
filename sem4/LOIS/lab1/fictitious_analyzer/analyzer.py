"""Анализатор фиктивных переменных."""

from itertools import product

from .ast import ASTNode
from .evaluator import collect_vars, evaluate


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


MAX_VARS = 20


def find_fictitious_vars(formula: ASTNode) -> list[str]:
    """Находит все фиктивные переменные в формуле."""
    all_vars = sorted(collect_vars(formula))
    if len(all_vars) > MAX_VARS:
        raise ValueError(
            f"Слишком много переменных: {len(all_vars)} > {MAX_VARS}. "
            f"Анализ потребовал бы {len(all_vars) * 2 ** (len(all_vars) - 1)} "
            f"вычислений и занял бы слишком много времени."
        )
    fictitious = []
    for var in all_vars:
        if is_fictitious(formula, var, all_vars):
            fictitious.append(var)
    return fictitious
