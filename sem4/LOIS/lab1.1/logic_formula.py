r"""
//logic_formula.py
////////////////////////////////////////////
//Лабораторная работа №1 по дисциплине ЛОИС
//Выполнена студентом группы 421702 БГУИР Дождиковым Александром Игоревичем
//Модуль лексического, синтаксического и семантического анализа формул.Реализует определение фиктивных пропозициональных переменных методом битовых масок.
//03.04.2026
//
//Ссылки на использованные источники
/*   [1] Bitwise operations in Python [Электронный ресурс] : Real Python : 
 *   образовательный портал. – Режим доступа: https://realpython.com/python-bitwise-operators/. 
 *   – Дата доступа: 03.04.2026.
 */
/*   [2] Recursive descent parser [Электронный ресурс] : Wikipedia : свободная энциклопедия. 
 *   – Режим доступа: https://en.wikipedia.org/wiki/Recursive_descent_parser. 
 *   – Дата доступа: 03.04.2026.
 */
/*   [3] Битовые операции в Python: как ускорить вычисления и сэкономить память [Электронный ресурс] // 
 *   Habr : IT-платформа. – Режим доступа: https://habr.com/ru/articles/462355/. 
 *   – Дата доступа: 04.06.2026.
 */
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

class TType(Enum):
    VAR        = auto()   
    CONST_TRUE = auto()   
    CONST_FALSE= auto()  
    OP_NOT     = auto()   
    OP_AND     = auto()   
    OP_OR      = auto()   
    OP_IMPL    = auto()   
    OP_EQUIV   = auto()   
    LPAREN     = auto()   
    RPAREN     = auto()  
    EOF        = auto()   


@dataclass(frozen=True)
class Token:
    ttype: TType
    value: str
    pos: int = 0

    def __repr__(self) -> str:
        return f"Token({self.ttype.name}, {self.value!r}, pos={self.pos})"

_SINGLE_CHAR_TOKENS: dict[str, TType] = {
    "!": TType.OP_NOT,
    "~": TType.OP_EQUIV,
    "(": TType.LPAREN,
    ")": TType.RPAREN,
}


class LexerError(Exception):
    pass

class Lexer:
    
    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0

    def tokenize(self) -> list[Token]:

        tokens: list[Token] = []
        src = self._source
        i = 0
        n = len(src)

        while i < n:
            ch = src[i]

            if ch in (" ", "\t", "\n", "\r"):
                raise LexerError(
                    f"Пробелы в формуле запрещены. "
                    f"Неожиданный пробельный символ на позиции {i} "
                    f"в формуле {src!r}"
                )

            if i + 1 < n and src[i] == "/" and src[i + 1] == "\\":
                tokens.append(Token(TType.OP_AND, "/\\", i))
                i += 2
                continue

            if i + 1 < n and src[i] == "-" and src[i + 1] == ">":
                tokens.append(Token(TType.OP_IMPL, "->", i))
                i += 2
                continue

            if ch == "V":
                tokens.append(Token(TType.OP_OR, "V", i))
                i += 1
                continue

            if ch == "1":
                tokens.append(Token(TType.CONST_TRUE, "1", i))
                i += 1
                continue

            if ch == "0":
                tokens.append(Token(TType.CONST_FALSE, "0", i))
                i += 1
                continue

            if ch in _SINGLE_CHAR_TOKENS:
                tokens.append(Token(_SINGLE_CHAR_TOKENS[ch], ch, i))
                i += 1
                continue

            if ch.isupper() and ch.isascii():
                tokens.append(Token(TType.VAR, ch, i))
                i += 1
                continue

            raise LexerError(
                f"Неожиданный символ {ch!r} на позиции {i} "
                f"в формуле {src!r}"
            )

        tokens.append(Token(TType.EOF, "", n))
        return tokens

    @classmethod
    def lex(cls, source: str) -> list[Token]:
        return cls(source).tokenize()

class ASTNode:

    def eval(self, env: dict[str, bool]) -> bool:
        raise NotImplementedError

    def variables(self) -> set[str]:
        raise NotImplementedError


@dataclass
class VarNode(ASTNode):
    name: str

    def eval(self, env: dict[str, bool]) -> bool:
        if self.name not in env:
            raise ValueError(f"Переменная {self.name!r} не найдена в среде означивания")
        return env[self.name]

    def variables(self) -> set[str]:
        return {self.name}

    def __repr__(self) -> str:
        return f"Var({self.name})"


@dataclass
class ConstNode(ASTNode):
    value: bool

    def eval(self, env: dict[str, bool]) -> bool:
        return self.value

    def variables(self) -> set[str]:
        return set()

    def __repr__(self) -> str:
        return f"Const({'1' if self.value else '0'})"


@dataclass
class UnaryOpNode(ASTNode):
    op: str        
    operand: ASTNode

    def eval(self, env: dict[str, bool]) -> bool:
        val = self.operand.eval(env)
        if self.op == "!":
            return not val
        raise ValueError(f"Неизвестная унарная операция: {self.op!r}")

    def variables(self) -> set[str]:
        return self.operand.variables()

    def __repr__(self) -> str:
        return f"({self.op}{self.operand!r})"


@dataclass
class BinaryOpNode(ASTNode):
    op: str         
    left: ASTNode
    right: ASTNode

    def eval(self, env: dict[str, bool]) -> bool:
        lv = self.left.eval(env)
        rv = self.right.eval(env)
        match self.op:
            case "/\\": return lv and rv
            case "V":   return lv or rv
            case "->":  return (not lv) or rv   
            case "~":   return lv == rv          
            case _:
                raise ValueError(f"Неизвестная бинарная операция: {self.op!r}")

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"

class ParseError(Exception):
    pass


class Parser:
    _BINOP_TYPES = frozenset({TType.OP_AND, TType.OP_OR, TType.OP_IMPL, TType.OP_EQUIV})

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if tok.ttype != TType.EOF:
            self._pos += 1
        return tok

    def _expect(self, ttype: TType) -> Token:
        tok = self._peek()
        if tok.ttype != ttype:
            raise ParseError(
                f"Ожидался {ttype.name}, получен {tok.ttype.name} "
                f"({tok.value!r}) на позиции {tok.pos}"
            )
        return self._advance()

    def parse(self) -> ASTNode:
        node = self._parse_atom()
        if self._peek().ttype != TType.EOF:
            tok = self._peek()
            raise ParseError(
                f"Неожиданный токен {tok.value!r} на позиции {tok.pos} "
                f"после конца формулы"
            )
        return node

    def _parse_atom(self) -> ASTNode:
        tok = self._peek()

        if tok.ttype == TType.VAR:
            self._advance()
            return VarNode(tok.value)

        if tok.ttype == TType.CONST_TRUE:
            self._advance()
            return ConstNode(True)

        if tok.ttype == TType.CONST_FALSE:
            self._advance()
            return ConstNode(False)

        if tok.ttype == TType.LPAREN:
            self._advance()                       

            inner = self._peek()

            if inner.ttype == TType.OP_NOT:
                self._advance()                   
                operand = self._parse_atom()
                self._expect(TType.RPAREN)        
                return UnaryOpNode("!", operand)
            
            left = self._parse_atom()
            op_tok = self._peek()
            if op_tok.ttype not in self._BINOP_TYPES:
                raise ParseError(
                    f"Ожидался бинарный оператор (/\\, V, ->, ~), "
                    f"получен {op_tok.ttype.name} ({op_tok.value!r}) "
                    f"на позиции {op_tok.pos}"
                )
            self._advance()                        
            right = self._parse_atom()
            self._expect(TType.RPAREN)             
            return BinaryOpNode(op_tok.value, left, right)

        raise ParseError(
            f"Ожидалась переменная, константа или '(', "
            f"получен {tok.ttype.name} ({tok.value!r}) на позиции {tok.pos}"
        )

    @classmethod
    def parse_formula(cls, source: str) -> ASTNode:
        tokens = Lexer.lex(source)
        return cls(tokens).parse()

def _var_mask(var_index: int, n_vars: int) -> int:
    block = 1 << var_index                    
    mask = ((1 << block) - 1) << block        
    cur_len = block << 1                     
    target = 1 << n_vars                      
    while cur_len < target:
        mask = mask | (mask << cur_len)       
        cur_len <<= 1
    return mask


def _compile_to_bitmask(
    node: "ASTNode",
    var_index: dict[str, int],
    var_masks: list[int],
    full_mask: int,
) -> int:
    if isinstance(node, VarNode):
        return var_masks[var_index[node.name]]

    if isinstance(node, ConstNode):
        return full_mask if node.value else 0

    if isinstance(node, UnaryOpNode):
        operand_mask = _compile_to_bitmask(node.operand, var_index, var_masks, full_mask)
        return (~operand_mask) & full_mask

    if isinstance(node, BinaryOpNode):
        lv = _compile_to_bitmask(node.left,  var_index, var_masks, full_mask)
        rv = _compile_to_bitmask(node.right, var_index, var_masks, full_mask)
        match node.op:
            case "/\\": return lv & rv
            case "V":   return lv | rv
            case "->":  return ((~lv) & full_mask) | rv
            case "~":   return (~(lv ^ rv)) & full_mask
            case _:
                raise ValueError(f"Неизвестная операция: {node.op!r}")

    raise TypeError(f"Неизвестный тип узла: {type(node)}")


class FormulaAnalyzer:
    def __init__(self, ast: ASTNode) -> None:
        self._ast = ast
        self._vars: list[str] = sorted(ast.variables())

        n = len(self._vars)
        self._var_index: dict[str, int] = {v: i for i, v in enumerate(self._vars)}

        if n > 0:
            self._full_mask: int = (1 << (1 << n)) - 1
            self._var_masks: list[int] = [_var_mask(i, n) for i in range(n)]
            self._f_mask: int = _compile_to_bitmask(
                ast, self._var_index, self._var_masks, self._full_mask
            )
        else:
            self._full_mask = 1   
            self._var_masks = []
            val = ast.eval({})
            self._f_mask = 1 if val else 0

    @property
    def variables(self) -> list[str]:
        return self._vars

    def is_dummy(self, var_name: str) -> bool:
        if var_name not in self._var_index:
            raise ValueError(f"Переменная {var_name!r} не входит в формулу")

        i    = self._var_index[var_name]
        vm   = self._var_masks[i]
        step = 1 << i   

        cf0 = self._f_mask & (vm ^ self._full_mask)   

        cf1 = (self._f_mask & vm) >> step              

        return cf0 == cf1

    def find_dummy_variables(self) -> list[str]:
        return [v for v in self._vars if self.is_dummy(v)]

    def analyze(self) -> dict[str, bool]:
        return {v: self.is_dummy(v) for v in self._vars}

    @classmethod
    def from_string(cls, source: str) -> "FormulaAnalyzer":
        ast = Parser.parse_formula(source)
        return cls(ast)
