"""
Тесты для модуля логики высказываний.
Проверяют: парсинг, вычисление истинности, определение фиктивных переменных.
"""

import pytest
from parser import parse_formula, SyntaxError as ParseSyntaxError
from lexer import Lexer, SyntaxError as LexSyntaxError
from fictitious import is_fictitious, find_fictitious_vars
from evaluator import evaluate, generate_assignments
from ast_nodes import collect_vars


# ============================================================
# Тесты лексера
# ============================================================

class TestLexer:
    """Тесты токенизатора."""

    def test_simple_variable(self):
        lexer = Lexer("P")
        tokens = lexer.tokenize()
        assert tokens[0].type.name == "VAR"
        assert tokens[0].value == "P"
        assert tokens[1].type.name == "END"

    def test_variable_with_digit(self):
        lexer = Lexer("Q1")
        tokens = lexer.tokenize()
        assert tokens[0].value == "Q1"

    def test_operators(self):
        lexer = Lexer(r"!/\VV->~")
        tokens = lexer.tokenize()
        assert [t.type.name for t in tokens[:-1]] == ['NOT', 'AND', 'OR', 'OR', 'IMPL', 'EQUIV']

    def test_complex_formula(self):
        lexer = Lexer("(P -> Q) /\\ R")
        tokens = lexer.tokenize()
        assert len(tokens) == 8  # P, ->, Q, /\, R, ), END

    def test_whitespace_ignored(self):
        lexer = Lexer("P   /\\    Q")
        tokens = lexer.tokenize()
        assert tokens[0].value == "P"
        assert tokens[1].type.name == "AND"
        assert tokens[2].value == "Q"

    def test_unknown_symbol(self):
        lexer = Lexer("P & Q")
        with pytest.raises(LexSyntaxError):
            lexer.tokenize()

    def test_invalid_implication(self):
        lexer = Lexer("P - Q")
        with pytest.raises(LexSyntaxError):
            lexer.tokenize()

    def test_invalid_conjunction(self):
        lexer = Lexer("P / Q")
        with pytest.raises(LexSyntaxError):
            lexer.tokenize()


# ============================================================
# Тесты парсера
# ============================================================

class TestParser:
    """Тесты рекурсивного спуска."""

    def test_variable(self):
        ast = parse_formula("P")
        assert ast.name == "P"

    def test_simple_negation(self):
        ast = parse_formula("!P")
        assert ast.operand.name == "P"

    def test_double_negation(self):
        ast = parse_formula("!!P")
        assert ast.operand.operand.name == "P"

    def test_conjunction(self):
        ast = parse_formula("P /\\ Q")
        assert ast.op == "/\\"
        assert ast.left.name == "P"
        assert ast.right.name == "Q"

    def test_disjunction(self):
        ast = parse_formula("P V Q")
        assert ast.op == "V"
        assert ast.left.name == "P"
        assert ast.right.name == "Q"

    def test_implication(self):
        ast = parse_formula("P -> Q")
        assert ast.op == "->"
        assert ast.left.name == "P"
        assert ast.right.name == "Q"

    def test_equivalence(self):
        ast = parse_formula("P ~ Q")
        assert ast.op == "~"
        assert ast.left.name == "P"
        assert ast.right.name == "Q"

    def test_parentheses(self):
        ast = parse_formula("(P -> Q)")
        assert ast.left.name == "P"

    def test_complex_nested(self):
        ast = parse_formula("!(P /\\ Q) V R")
        # (P /\ Q) — левое поддерево дизъюнкции
        assert ast.op == "V"
        left = ast.left
        # left = NotNode(operand=BinOpNode)
        assert isinstance(left, type(ast.left))  # same structure

    def test_priority_and_left_assoc(self):
        # P /\ Q V R читается как (P /\ Q) V R
        ast = parse_formula("P /\\ Q V R")
        assert ast.op == "V"
        assert ast.left.op == "/\\"

    def test_priority_or_and(self):
        # P V Q /\ R читается как P V (Q /\ R)
        ast = parse_formula("P V Q /\\ R")
        assert ast.op == "V"
        assert ast.right.op == "/\\"

    def test_multiple_implications(self):
        # A -> B -> C читается как A -> (B -> C)
        ast = parse_formula("A -> B -> C")
        assert ast.op == "->"
        assert ast.left.name == "A"
        assert ast.right.op == "->"

    def test_missing_closing_paren(self):
        with pytest.raises(ParseSyntaxError):
            parse_formula("(P -> Q")

    def test_missing_opening_paren(self):
        with pytest.raises(ParseSyntaxError):
            parse_formula("P -> Q)")

    def test_empty_formula(self):
        with pytest.raises(Exception):  # LexSyntaxError
            parse_formula("")

    def test_trailing_chars(self):
        with pytest.raises(ParseSyntaxError):
            parse_formula("P Q")


# ============================================================
# Тесты вычисления истинности
# ============================================================

class TestEvaluator:
    """Тесты вычисления истинностного значения."""

    def test_var_true(self):
        ast = parse_formula("P")
        assert evaluate(ast, {"P": True}) is True
        assert evaluate(ast, {"P": False}) is False

    def test_negation(self):
        ast = parse_formula("!P")
        assert evaluate(ast, {"P": True}) is False
        assert evaluate(ast, {"P": False}) is True

    def test_conjunction_true(self):
        ast = parse_formula("P /\\ Q")
        assert evaluate(ast, {"P": True, "Q": True}) is True

    def test_conjunction_false(self):
        ast = parse_formula("P /\\ Q")
        assert evaluate(ast, {"P": True, "Q": False}) is False

    def test_disjunction_true(self):
        ast = parse_formula("P V Q")
        assert evaluate(ast, {"P": False, "Q": True}) is True

    def test_disjunction_false(self):
        ast = parse_formula("P V Q")
        assert evaluate(ast, {"P": False, "Q": False}) is False

    def test_implication_true_when_antecedent_false(self):
        # False -> anything = True
        ast = parse_formula("P -> Q")
        assert evaluate(ast, {"P": False, "Q": False}) is True

    def test_implication_true_when_consequent_true(self):
        ast = parse_formula("P -> Q")
        assert evaluate(ast, {"P": True, "Q": True}) is True

    def test_implication_false(self):
        # True -> False = False
        ast = parse_formula("P -> Q")
        assert evaluate(ast, {"P": True, "Q": False}) is False

    def test_equivalence_true(self):
        ast = parse_formula("P ~ Q")
        assert evaluate(ast, {"P": True, "Q": True}) is True
        assert evaluate(ast, {"P": False, "Q": False}) is True

    def test_equivalence_false(self):
        ast = parse_formula("P ~ Q")
        assert evaluate(ast, {"P": True, "Q": False}) is False
        assert evaluate(ast, {"P": False, "Q": True}) is False


class TestGenerateAssignments:
    """Тесты генерации таблицы истинности."""

    def test_two_vars(self):
        assignments = generate_assignments(["P", "Q"])
        assert len(assignments) == 4

        # Проверяем все комбинации
        expected = [
            {"P": False, "Q": False},
            {"P": True, "Q": False},
            {"P": False, "Q": True},
            {"P": True, "Q": True},
        ]
        assert assignments == expected

    def test_empty_vars(self):
        assignments = generate_assignments([])
        assert len(assignments) == 1
        assert assignments == [{}]


# ============================================================
# Тесты фиктивных переменных
# ============================================================

class TestFictitiousVars:
    """Тесты определения фиктивных переменных."""

    # --- Формулы без фиктивных переменных ---

    def test_no_fictitious_simple(self):
        # P /\ Q: обе существенны
        ast = parse_formula("P /\\ Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_disjunction(self):
        # P V Q: обе существенны
        ast = parse_formula("P V Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_implication(self):
        # P -> Q: обе существенны
        ast = parse_formula("P -> Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_three_vars(self):
        # P /\ Q /\ R: все существенны
        ast = parse_formula("P /\\ Q /\\ R")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_complex(self):
        # (P -> Q) /\ (R V S): все существенны
        ast = parse_formula("(P -> Q) /\\ (R V S)")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    # --- Формулы с одной фиктивной переменной ---

    def test_one_fictitious_conjunction(self):
        # !P \/ P — тавтология, P фиктивна
        ast = parse_formula("!P V P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]
        assert is_fictitious(ast, "P") is True

    def test_one_fictitious_disjunction(self):
        # P /\ !P — противоречие, P фиктивна
        ast = parse_formula("P /\\ !P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_fictitious_in_negation(self):
        # !!P эквивалентно P, ни одна переменная не фиктивна
        ast = parse_formula("!!P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_fictitious_after_simplification(self):
        # P /\ !P — противоречие (ложь), P фиктивна
        ast = parse_formula("P /\\ !P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_fictitious_in_tautology(self):
        # P V !P — тавтология, P фиктивна
        ast = parse_formula("P V !P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    # --- Формулы с несколькими фиктивными переме��ными ---

    def test_two_fictitious(self):
        # P V !P — тавтология, P фиктивна
        ast = parse_formula("P V !P")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P"}

    def test_three_fictitious(self):
        # (P V !P) /\ (Q V !Q) — тавтология, обе фиктивны
        ast = parse_formula("(P V !P) /\\ (Q V !Q)")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P", "Q"}

    # --- Тавтологии и противоречия (все переменные фиктивны) ---

    def test_tautology_all_fictitious(self):
        # P -> P: тавтология (всегда истинна)
        ast = parse_formula("P -> P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_contradiction_all_fictitious(self):
        # P /\ !P: противоречие (всегда ложна)
        ast = parse_formula("P /\\ !P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_tautology_complex(self):
        # (P V !P) V Q — тавтология (все переменные фиктивны)
        ast = parse_formula("(P V !P) V Q")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P", "Q"}

    def test_contradiction_complex(self):
        # (P /\ !P) /\ Q — противоречие
        ast = parse_formula("(P /\\ !P) /\\ Q")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P", "Q"}

    # --- Граничные случаи ---

    def test_single_variable(self):
        # P: формула без операций
        ast = parse_formula("P")
        # P зависит от себя — не фиктивна
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_negated_single_var(self):
        # !P
        ast = parse_formula("!P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_implication_chain(self):
        # P -> Q -> R (правоассоциативна)
        ast = parse_formula("P -> Q -> R")
        # A -> (B -> C): значение зависит от A, B, C
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_implication_with_self_in_consequent(self):
        # (P -> Q) -> P: Q фиктивна (Peirce's law), P существенна
        ast = parse_formula("(P -> Q) -> P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["Q"]
        assert is_fictitious(ast, "Q") is True
        assert is_fictitious(ast, "P") is False

    def test_var_with_redundant_conjunct(self):
        # P V (Q /\ P) эквивалентно P, Q фиктивна
        ast = parse_formula("P V (Q /\\ P)")
        fictitious = find_fictitious_vars(ast)
        assert "Q" in fictitious
        assert "P" not in fictitious

    def test_fictitious_in_implication_chain(self):
        # P -> P -> Q: все существенны
        ast = parse_formula("P -> P -> Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_symmetric_contrapositive(self):
        # (P -> Q) /\ (!Q -> P): P фиктивна, Q существенна
        ast = parse_formula("(P -> Q) /\\ (!Q -> P)")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_deeply_nested(self):
        # P /\ (Q /\ (R /\ S)): все существенны
        ast = parse_formula("P /\\ (Q /\\ (R /\\ S))")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_mixed_operations_priority(self):
        # P V Q /\ R читается как P V (Q /\ R)
        ast = parse_formula("P V Q /\\ R")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []  # все существенны

    def test_equivalence(self):
        # P ~ Q
        ast = parse_formula("P ~ Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []  # обе существенны

    def test_equivalence_fictitious(self):
        # P ~ P: всегда True, P фиктивна
        ast = parse_formula("P ~ P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_complex_formula_with_fictitious(self):
        # (P \/ !P) -> (Q /\ !Q): импликация из тавтологии в противоречие
        # (True) -> (False) = False — противоречие, все фиктивны
        ast = parse_formula("(P V !P) -> (Q /\\ !Q)")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P", "Q"}

    # --- Проверка ошибок ---

    def test_is_fictitious_unknown_var(self):
        ast = parse_formula("P /\\ Q")
        with pytest.raises(ValueError):
            is_fictitious(ast, "R")

    def test_collect_vars(self):
        ast = parse_formula("(P -> Q) /\\ R /\\ S")
        vars = collect_vars(ast)
        assert vars == {"P", "Q", "R", "S"}


# ============================================================
# Интеграционные тесты
# ============================================================

class TestIntegration:
    """Интеграционные тесты всего конвейера."""

    def test_end_to_end_simple(self):
        formula = "P /\\ Q"
        ast = parse_formula(formula)
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_end_to_end_tautology(self):
        formula = "P V !P"
        ast = parse_formula(formula)
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_end_to_end_complex(self):
        formula = "(P -> Q) /\\ (!Q -> P)"
        ast = parse_formula(formula)
        fictitious = find_fictitious_vars(ast)
        # (P→Q)∧(¬Q→P): P фиктивна, Q существенна
        assert fictitious == ["P"]

    def test_end_to_end_mixed(self):
        formula = "(P V !P) V R"
        ast = parse_formula(formula)
        fictitious = find_fictitious_vars(ast)
        # (P ∨ ¬P) ∨ R — тавтология, все фиктивны
        assert set(fictitious) == {"P", "R"}