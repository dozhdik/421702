"""
Модуль определения фиктивных пропозициональных переменных.

Переменная X фиктивна в формуле F, если:
  F|_{X=True} ≡ F|_{X=False} для всех assignments остальных переменных.

Алгоритм: для каждой переменной V из множества переменных формулы:
  1. Извлекаем все assignments остальных переменных (без V).
  2. Для каждого assignment фиксируем V = True и V = False.
  3. Сравниваем результаты. Если совпадают для всех — V фиктивна.
"""

from ast_nodes import ASTNode, VarNode, NotNode, BinOpNode, collect_vars
from evaluator import evaluate, generate_assignments


def is_fictitious(formula: ASTNode, var_name: str) -> bool:
    """
    Проверяет, является ли переменная фиктивной в формуле.
    
    Алгоритм:
      1. Собрать все переменные формулы, кроме var_name.
      2. Сгенерировать все assignments для оставшихся переменных.
      3. Для каждого assignment сравнить evaluate с Var=True и Var=False.
      4. Если все совпадают → фиктивная.
    
    Args:
        formula: AST формулы
        var_name: имя проверяемой переменной
        
    Returns:
        True если переменная фиктивна, иначе False
    """
    # Получаем все переменные из формулы
    all_vars = sorted(collect_vars(formula))
    
    if var_name not in all_vars:
        raise ValueError(f"Переменная '{var_name}' отсутствует в формуле")

    # Переменные без текущей
    other_vars = [v for v in all_vars if v != var_name]

    # Перебираем все комбинации значений остальных переменных
    for assignment in generate_assignments(other_vars):
        # Подставляем Var = True
        assign_true = dict(assignment)
        assign_true[var_name] = True
        val_true = evaluate(formula, assign_true)

        # Подставляем Var = False
        assign_false = dict(assignment)
        assign_false[var_name] = False
        val_false = evaluate(formula, assign_false)

        # Если значения различаются — переменная существенная
        if val_true != val_false:
            return False

    return True


def find_fictitious_vars(formula: ASTNode) -> list[str]:
    """
    Находит все фиктивные переменные в формуле.
    
    Args:
        formula: AST формулы
        
    Returns:
        Список имён фиктивных переменных (в алфавитном порядке)
    """
    all_vars = sorted(collect_vars(formula))
    fictitious = []
    for var in all_vars:
        if is_fictitious(formula, var):
            fictitious.append(var)
    return fictitious


def format_result(formula: str, fictitious: list[str]) -> str:
    """Форматирует вывод результата."""
    if fictitious:
        return f"Фиктивные переменные: {', '.join(fictitious)}"
    return "Фиктивных переменных нет"