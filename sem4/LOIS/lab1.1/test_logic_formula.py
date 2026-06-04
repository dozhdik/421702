r"""
test_logic_formula.py
=====================
Tests for logic_formula module (LOIS lab work).

Run:
    pytest test_logic_formula.py -v
or:
    python -m pytest test_logic_formula.py -v

New syntax rules:
  - ALL operations require parentheses:
      Negation:  (!A), (!(!A)), (!(A/\B))
      Binary:    (A/\B), (A->(BVC))
  - Without parentheses: only variables and constants (A, 1, 0)
  - Spaces are forbidden
"""

import pytest
from logic_formula import (
    Lexer, LexerError,
    Parser, ParseError,
    FormulaAnalyzer,
    TType, Token,
    VarNode, ConstNode, UnaryOpNode, BinaryOpNode,
)


# ====== A: Lexer tests ======

class TestLexer:
    def test_simple_variable(self):
        tokens = Lexer.lex("A")
        assert tokens[0].ttype == TType.VAR
        assert tokens[0].value == "A"
        assert tokens[1].ttype == TType.EOF

    def test_variable_single_letter_only(self):
        tokens = Lexer.lex("AB")
        assert tokens[0].ttype == TType.VAR
        assert tokens[0].value == "A"
        assert tokens[1].ttype == TType.VAR
        assert tokens[1].value == "B"

    def test_digit_not_part_of_var(self):
        tokens = Lexer.lex("A1")
        assert tokens[0].ttype == TType.VAR
        assert tokens[0].value == "A"
        assert tokens[1].ttype == TType.CONST_TRUE
        assert tokens[1].value == "1"

    def test_constants(self):
        tokens = Lexer.lex("1")
        assert tokens[0].ttype == TType.CONST_TRUE
        tokens = Lexer.lex("0")
        assert tokens[0].ttype == TType.CONST_FALSE

    def test_all_operators(self):
        r"""All operators recognized correctly."""
        src = "!/\\V->~"
        tokens = Lexer.lex(src)
        expected = [TType.OP_NOT, TType.OP_AND, TType.OP_OR,
                    TType.OP_IMPL, TType.OP_EQUIV]
        for tok, exp in zip(tokens, expected):
            assert tok.ttype == exp

    def test_parentheses(self):
        tokens = Lexer.lex("(A)")
        assert tokens[0].ttype == TType.LPAREN
        assert tokens[1].ttype == TType.VAR
        assert tokens[2].ttype == TType.RPAREN

    def test_spaces_raise_error(self):
        with pytest.raises(LexerError):
            Lexer.lex("A B")
        with pytest.raises(LexerError):
            Lexer.lex("(A/\\B) ")

    def test_unknown_symbol_raises(self):
        with pytest.raises(LexerError):
            Lexer.lex("A+B")

    def test_lowercase_raises(self):
        with pytest.raises(LexerError):
            Lexer.lex("a")

    def test_position_recorded(self):
        tokens = Lexer.lex("(!A)")
        assert tokens[0].pos == 0   # (
        assert tokens[1].pos == 1   # !
        assert tokens[2].pos == 2   # A


# ====== B: Parser tests ======

class TestParser:
    def test_var_node(self):
        ast = Parser.parse_formula("A")
        assert isinstance(ast, VarNode)
        assert ast.name == "A"

    def test_const_true(self):
        ast = Parser.parse_formula("1")
        assert isinstance(ast, ConstNode)
        assert ast.value is True

    def test_const_false(self):
        ast = Parser.parse_formula("0")
        assert isinstance(ast, ConstNode)
        assert ast.value is False

    def test_negation(self):
        ast = Parser.parse_formula("(!A)")
        assert isinstance(ast, UnaryOpNode)
        assert ast.op == "!"
        assert isinstance(ast.operand, VarNode)

    def test_double_negation(self):
        ast = Parser.parse_formula("(!(!A))")
        assert isinstance(ast, UnaryOpNode)
        assert isinstance(ast.operand, UnaryOpNode)

    def test_conjunction(self):
        ast = Parser.parse_formula("(A/\\B)")
        assert isinstance(ast, BinaryOpNode)
        assert ast.op == "/\\"

    def test_negation_of_binary(self):
        ast = Parser.parse_formula("(!(A/\\B))")
        assert isinstance(ast, UnaryOpNode)
        assert ast.op == "!"
        assert isinstance(ast.operand, BinaryOpNode)
        assert ast.operand.op == "/\\"

    def test_nested_parens(self):
        ast = Parser.parse_formula("(!((A/\\B)VC))")
        assert isinstance(ast, UnaryOpNode)
        assert isinstance(ast.operand, BinaryOpNode)
        assert ast.operand.op == "V"

    def test_implication(self):
        ast = Parser.parse_formula("(A->B)")
        assert isinstance(ast, BinaryOpNode)
        assert ast.op == "->"

    def test_equivalence(self):
        ast = Parser.parse_formula("(A~B)")
        assert isinstance(ast, BinaryOpNode)
        assert ast.op == "~"

    def test_variables_collected(self):
        ast = Parser.parse_formula("((A/\\B)V(!C))")
        assert ast.variables() == {"A", "B", "C"}

    def test_unbalanced_paren_raises(self):
        with pytest.raises(ParseError):
            Parser.parse_formula("(A/\\B")

    def test_extra_closing_paren_raises(self):
        with pytest.raises(ParseError):
            Parser.parse_formula("(A/\\B))")

    def test_empty_formula_raises(self):
        with pytest.raises(ParseError):
            Parser.parse_formula("")

    def test_missing_operand_raises(self):
        with pytest.raises(ParseError):
            Parser.parse_formula("(A/\\)")

    # ---- Everything without parens is an error ----

    def test_bare_negation_raises(self):
        """!A without parentheses -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("!A")

    def test_bare_double_negation_raises(self):
        """!!A without parentheses -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("!!A")

    def test_bare_conjunction_raises(self):
        """A/\B without parentheses -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("A/\\B")

    def test_bare_disjunction_raises(self):
        """AVB without parentheses -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("AVB")

    def test_bare_implication_raises(self):
        """A->B without parentheses -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("A->B")

    def test_bare_equivalence_raises(self):
        """A~B without parentheses -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("A~B")

    def test_single_atom_in_parens_raises(self):
        """(A) without operator -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("(A)")

    def test_nested_right_bare_negation_raises(self):
        """(A/\!B) — !B without parens inside binary -> ParseError."""
        with pytest.raises(ParseError):
            Parser.parse_formula("(A/\\!B)")


# ====== C: Evaluation tests ======

F, T = False, True


class TestEvaluation:
    def _eval(self, formula: str, **env: bool) -> bool:
        ast = Parser.parse_formula(formula)
        return ast.eval(env)

    def test_var_true(self):
        assert self._eval("A", A=True) is True

    def test_var_false(self):
        assert self._eval("A", A=False) is False

    def test_const_true(self):
        assert self._eval("1") is True

    def test_const_false(self):
        assert self._eval("0") is False

    def test_negation_true(self):
        assert self._eval("(!A)", A=True) is False

    def test_negation_false(self):
        assert self._eval("(!A)", A=False) is True

    def test_conjunction_truth_table(self):
        cases = [(F, F, F), (F, T, F), (T, F, F), (T, T, T)]
        for a, b, expected in cases:
            assert self._eval("(A/\\B)", A=a, B=b) is expected

    def test_disjunction_truth_table(self):
        cases = [(F, F, F), (F, T, T), (T, F, T), (T, T, T)]
        for a, b, expected in cases:
            assert self._eval("(AVB)", A=a, B=b) is expected

    def test_implication_truth_table(self):
        F, T = False, True
        cases = [(F, F, T), (F, T, T), (T, F, F), (T, T, T)]
        for a, b, expected in cases:
            assert self._eval("(A->B)", A=a, B=b) is expected

    def test_equivalence_truth_table(self):
        F, T = False, True
        cases = [(F, F, T), (F, T, F), (T, F, F), (T, T, T)]
        for a, b, expected in cases:
            assert self._eval("(A~B)", A=a, B=b) is expected

    def test_complex_formula(self):
        for a in (F, T):
            for b in (F, T):
                v1 = self._eval("((A->B)/\\(B->A))", A=a, B=b)
                v2 = self._eval("(A~B)", A=a, B=b)
                assert v1 == v2, f"A={a}, B={b}"


# ====== D: Dummy variable analyzer tests ======

class TestFormulaAnalyzer:

    def test_no_dummy_variables_conjunction(self):
        analyzer = FormulaAnalyzer.from_string("(A/\\B)")
        assert analyzer.find_dummy_variables() == []

    def test_no_dummy_variables_implication(self):
        analyzer = FormulaAnalyzer.from_string("(A->B)")
        assert analyzer.find_dummy_variables() == []

    def test_no_dummy_equivalence(self):
        analyzer = FormulaAnalyzer.from_string("(A~B)")
        assert analyzer.find_dummy_variables() == []

    def test_all_dummy_tautology_not(self):
        analyzer = FormulaAnalyzer.from_string("(AV(!A))")
        assert analyzer.find_dummy_variables() == ["A"]

    def test_all_dummy_contradiction(self):
        analyzer = FormulaAnalyzer.from_string("(A/\\(!A))")
        assert analyzer.find_dummy_variables() == ["A"]

    def test_all_dummy_const_true(self):
        analyzer = FormulaAnalyzer.from_string("1")
        assert analyzer.find_dummy_variables() == []
        assert analyzer.variables == []

    def test_all_dummy_two_vars_tautology(self):
        analyzer = FormulaAnalyzer.from_string("((AV(!A))V(B/\\(!B)))")
        dummies = analyzer.find_dummy_variables()
        assert "A" in dummies
        assert "B" in dummies

    def test_nested_dummy_A_not_B(self):
        analyzer = FormulaAnalyzer.from_string("((A/\\(!A))VB)")
        dummies = analyzer.find_dummy_variables()
        assert dummies == ["A"]
        assert "B" not in dummies

    def test_nested_dummy_mixed(self):
        analyzer = FormulaAnalyzer.from_string("((AV(!A))/\\(BVC))")
        dummies = analyzer.find_dummy_variables()
        assert "A" in dummies
        assert "B" not in dummies
        assert "C" not in dummies

    def test_partially_dummy_implication(self):
        analyzer = FormulaAnalyzer.from_string("((A/\\(!A))->B)")
        dummies = analyzer.find_dummy_variables()
        assert "A" in dummies
        assert "B" in dummies

    def test_three_vars_one_dummy(self):
        analyzer = FormulaAnalyzer.from_string("(((AV(!A))/\\B)/\\C)")
        dummies = analyzer.find_dummy_variables()
        assert dummies == ["A"]

    def test_parse_error_extra_open_paren(self):
        with pytest.raises(ParseError):
            FormulaAnalyzer.from_string("((A/\\B)")

    def test_parse_error_extra_close_paren(self):
        with pytest.raises(ParseError):
            FormulaAnalyzer.from_string("(A/\\B))")

    def test_parse_error_empty(self):
        with pytest.raises(ParseError):
            FormulaAnalyzer.from_string("")

    def test_lex_error_unknown_symbol(self):
        with pytest.raises(LexerError):
            FormulaAnalyzer.from_string("(A&B)")

    def test_lex_error_spaces(self):
        with pytest.raises(LexerError):
            FormulaAnalyzer.from_string("(A/\\B) ")

    def test_single_variable_essential(self):
        analyzer = FormulaAnalyzer.from_string("A")
        assert analyzer.find_dummy_variables() == []

    def test_analyze_returns_dict(self):
        result = FormulaAnalyzer.from_string("((A/\\(!A))VB)").analyze()
        assert result == {"A": True, "B": False}

    def test_two_letters_without_op_raises(self):
        with pytest.raises(ParseError):
            FormulaAnalyzer.from_string("AB")

    def test_complex_with_dummy(self):
        analyzer = FormulaAnalyzer.from_string("(((A->A)/\\B)~B)")
        dummies = analyzer.find_dummy_variables()
        assert "A" in dummies
        assert "B" in dummies

    def test_bare_negation_raises(self):
        with pytest.raises(ParseError):
            FormulaAnalyzer.from_string("!A")

    def test_binary_op_without_parens_raises(self):
        with pytest.raises(ParseError):
            FormulaAnalyzer.from_string("A/\\B")
        with pytest.raises(ParseError):
            FormulaAnalyzer.from_string("AVB")
