"""
Тесты для анализатора фиктивных переменных в логике высказываний.
Проверяют: лексер, парсер, вычислитель, определение фиктивных переменных.
"""

import pytest
from fictitious_analyzer import (
    Lexer, LexerError,
    Parser, ParserError,
    parse_formula,
    evaluate,
    collect_vars,
    is_fictitious,
    find_fictitious_vars,
    analyze_formula
)


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
        lexer = Lexer(r"!/\V->~")
        tokens = lexer.tokenize()
        assert [t.type.name for t in tokens[:-1]] == ['NOT', 'AND', 'OR', 'IMPL', 'EQUIV']

    def test_complex_formula(self):
        lexer = Lexer("(P -> Q) /\\ R")
        tokens = lexer.tokenize()
        assert len(tokens) == 8  # (, P, ->, Q, ), /\, R, END

    def test_whitespace_ignored(self):
        lexer = Lexer("P   /\\    Q")
        tokens = lexer.tokenize()
        assert tokens[0].value == "P"
        assert tokens[1].type.name == "AND"
        assert tokens[2].value == "Q"

    def test_unknown_symbol(self):
        lexer = Lexer("P & Q")
        with pytest.raises(LexerError):
            lexer.tokenize()

    def test_invalid_implication(self):
        lexer = Lexer("P - Q")
        with pytest.raises(LexerError):
            lexer.tokenize()

    def test_invalid_conjunction(self):
        lexer = Lexer("P / Q")
        with pytest.raises(LexerError):
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
        assert ast.op == "V"

    def test_priority_and_or(self):
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
        with pytest.raises(ParserError):
            parse_formula("(P -> Q")

    def test_missing_opening_paren(self):
        with pytest.raises(ParserError):
            parse_formula("P -> Q)")

    def test_empty_formula(self):
        with pytest.raises(ParserError):
            parse_formula("")

    def test_trailing_chars(self):
        with pytest.raises(ParserError):
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
        ast = parse_formula("P -> Q")
        assert evaluate(ast, {"P": False, "Q": False}) is True

    def test_implication_true_when_consequent_true(self):
        ast = parse_formula("P -> Q")
        assert evaluate(ast, {"P": True, "Q": True}) is True

    def test_implication_false(self):
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


# ============================================================
# Тесты фиктивных переменных
# ============================================================

class TestFictitiousVars:
    """Тесты определения фиктивных переменных."""

    def test_no_fictitious_simple(self):
        ast = parse_formula("P /\\ Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_disjunction(self):
        ast = parse_formula("P V Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_implication(self):
        ast = parse_formula("P -> Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_three_vars(self):
        ast = parse_formula("P /\\ Q /\\ R")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_no_fictitious_complex(self):
        ast = parse_formula("(P -> Q) /\\ (R V S)")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_tautology_excluded_middle(self):
        ast = parse_formula("P V !P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]
        assert is_fictitious(ast, "P", ["P"]) is True

    def test_contradiction(self):
        ast = parse_formula("P /\\ !P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_double_negation(self):
        ast = parse_formula("!!P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_tautology_reflexive_implication(self):
        ast = parse_formula("P -> P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_two_fictitious_tautology(self):
        ast = parse_formula("(P V !P) /\\ (Q V !Q)")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P", "Q"}

    def test_tautology_complex(self):
        ast = parse_formula("(P V !P) V Q")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P", "Q"}

    def test_contradiction_complex(self):
        ast = parse_formula("(P /\\ !P) /\\ Q")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"P", "Q"}

    def test_single_variable(self):
        ast = parse_formula("P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_negated_single_var(self):
        ast = parse_formula("!P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_implication_chain(self):
        ast = parse_formula("P -> Q -> R")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_peirce_law(self):
        # ((P -> Q) -> P) -> P: закон Пирса, Q фиктивна
        ast = parse_formula("((P -> Q) -> P) -> P")
        fictitious = find_fictitious_vars(ast)
        assert "Q" in fictitious

    def test_var_with_redundant_conjunct(self):
        # P V (Q /\ P) эквивалентно P, Q фиктивна
        ast = parse_formula("P V (Q /\\ P)")
        fictitious = find_fictitious_vars(ast)
        assert "Q" in fictitious
        assert "P" not in fictitious

    def test_equivalence_no_fictitious(self):
        ast = parse_formula("P ~ Q")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == []

    def test_equivalence_reflexive(self):
        ast = parse_formula("P ~ P")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["P"]

    def test_implication_definition_tautology(self):
        # (A -> B) ~ (!A V B) — тавтология
        ast = parse_formula("(A -> B) ~ (!A V B)")
        fictitious = find_fictitious_vars(ast)
        assert set(fictitious) == {"A", "B"}

    def test_collect_vars(self):
        ast = parse_formula("(P -> Q) /\\ R /\\ S")
        vars = collect_vars(ast)
        assert vars == {"P", "Q", "R", "S"}

    def test_partial_fictitious(self):
        # (P /\ Q) V (P /\ !Q) упрощается до P, Q фиктивна
        ast = parse_formula("(P /\\ Q) V (P /\\ !Q)")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["Q"]

    def test_partial_fictitious_disjunction(self):
        # (P V Q) /\ (P V !Q) упрощается до P, Q фиктивна
        ast = parse_formula("(P V Q) /\\ (P V !Q)")
        fictitious = find_fictitious_vars(ast)
        assert fictitious == ["Q"]


# ============================================================
# Интеграционные тесты
# ============================================================

class TestIntegration:
    """Интеграционные тесты всего конвейера."""

    def test_end_to_end_simple(self):
        all_vars, fictitious = analyze_formula("P /\\ Q")
        assert set(all_vars) == {"P", "Q"}
        assert fictitious == []

    def test_end_to_end_tautology(self):
        all_vars, fictitious = analyze_formula("P V !P")
        assert all_vars == ["P"]
        assert fictitious == ["P"]

    def test_end_to_end_complex(self):
        all_vars, fictitious = analyze_formula("(P /\\ Q) V (P /\\ !Q)")
        assert set(all_vars) == {"P", "Q"}
        assert fictitious == ["Q"]

    def test_end_to_end_mixed(self):
        all_vars, fictitious = analyze_formula("(P V !P) V R")
        assert set(all_vars) == {"P", "R"}
        assert set(fictitious) == {"P", "R"}

    def test_end_to_end_no_fictitious(self):
        all_vars, fictitious = analyze_formula("(P -> Q) /\\ (Q -> R)")
        assert set(all_vars) == {"P", "Q", "R"}
        assert fictitious == []
