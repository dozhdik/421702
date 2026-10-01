#!/usr/bin/env python3
"""
Лабораторная работа 3 — Прямой нечёткий логический вывод
Вариант 5: треугольная норма произведения Хамахера
           + соответствующая R-импликация (остаточная)

Дисциплина: Логические основы интеллектуальных систем (ЛОИС)
БГУИР, группа 421702
"""

import re
import sys
from collections import OrderedDict


# ════════════════════════════════════════════════════════════════
# 1. Треугольная норма и импликация Хамахера
# ════════════════════════════════════════════════════════════════

def hamacher_tnorm(a: float, b: float) -> float:
    """
    Произведение Хамахера (t-норма):
        T_H(a, b) = a·b / (a + b − a·b),  если (a,b) ≠ (0,0)
        T_H(0, 0) = 0
    """
    if a == 0.0 or b == 0.0:
        return 0.0
    return (a * b) / (a + b - a * b)


def hamacher_implication(a: float, b: float) -> float:
    """
    R-импликация (остаточная) произведения Хамахера:
        I_H(a, b) = 1,                    если a ≤ b
        I_H(a, b) = a·b / (a − b + a·b),  если a > b
    Особый случай: I_H(a, 0) = 0 при a > 0.
    """
    if a <= b + 1e-12:
        return 1.0
    if b < 1e-12:
        return 0.0
    return (a * b) / (a - b + a * b)


# ════════════════════════════════════════════════════════════════
# 2. Структуры данных
# ════════════════════════════════════════════════════════════════

class FuzzySet:
    """Нечёткое множество: имя = {<элемент, степень>, ...}."""

    def __init__(self, name: str, elements: list[tuple[str, float]]):
        self.name = name
        self.elements = OrderedDict(elements)

    def keys(self) -> list[str]:
        return list(self.elements.keys())

    def vals(self) -> list[float]:
        return list(self.elements.values())

    def domain_matches(self, other: "FuzzySet") -> bool:
        """Совпадает ли набор элементов (домен) с другим множеством."""
        return self.keys() == other.keys()

    def approx_eq(self, other: "FuzzySet", tol: float = 1e-6) -> bool:
        if self.keys() != other.keys():
            return False
        return all(
            abs(self.elements[k] - other.elements[k]) < tol
            for k in self.elements
        )

    def format_short(self) -> str:
        parts = []
        for k, v in self.elements.items():
            # Целые .0 значения показываем кратко, иначе 4 знака
            if v == int(v):
                parts.append(f"<{k},{v:.1f}>")
            else:
                parts.append(f"<{k},{v:.4f}>")
        return "{" + ",".join(parts) + "}"

    def __repr__(self):
        return f"{self.name}={self.format_short()}"


class Rule:
    """Правило нечёткой импликации: Premise(var) -> Conclusion(var)."""

    def __init__(self, premise: str, conclusion: str):
        self.premise = premise
        self.conclusion = conclusion

    def __repr__(self):
        return f"{self.premise}->{self.conclusion}"


# ════════════════════════════════════════════════════════════════
# 3. Парсер базы знаний (по грамматике из задания)
# ════════════════════════════════════════════════════════════════

def parse_knowledge_base(text: str) -> tuple[dict[str, FuzzySet], list[Rule]]:
    """
    Разбор файла базы знаний.

    Факт:    Имя(перем)={<эл1,ст1>,<эл2,ст2>,...}
    Правило: Имя1(перем)->Имя2(перем)
    """
    facts: dict[str, FuzzySet] = {}
    rules: list[Rule] = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue

        # --- факт ---
        m = re.match(r"([A-Za-z]\w*)\s*\(\s*\w+\s*\)\s*=\s*\{(.+)\}", line)
        if m:
            name = m.group(1)
            body = m.group(2)
            pairs = re.findall(r"<\s*(\w+)\s*,\s*([01](?:\.\d+)?)\s*>", body)
            if pairs:
                elems = [(e, float(d)) for e, d in pairs]
                facts[name] = FuzzySet(name, elems)
            continue

        # --- правило ---
        m = re.match(
            r"([A-Za-z]\w*)\s*\(\s*\w+\s*\)\s*->\s*"
            r"([A-Za-z]\w*)\s*\(\s*\w+\s*\)",
            line,
        )
        if m:
            rules.append(Rule(m.group(1), m.group(2)))
            continue

    return facts, rules


# ════════════════════════════════════════════════════════════════
# 4. Построение матрицы импликации
# ════════════════════════════════════════════════════════════════

def build_implication_matrix(
    premise: FuzzySet, conclusion: FuzzySet
) -> list[list[float]]:
    """R[i][j] = I_H(premise[i], conclusion[j])."""
    return [
        [hamacher_implication(a, b) for b in conclusion.vals()]
        for a in premise.vals()
    ]


def format_matrix(
    matrix: list[list[float]],
    row_keys: list[str],
    col_keys: list[str],
) -> str:
    """Красивое текстовое представление матрицы."""
    cw = 8
    lines: list[str] = []
    header = " " * (cw + 1) + "".join(f"{k:>{cw}}" for k in col_keys)
    lines.append(header)
    for i, row in enumerate(matrix):
        vals = "".join(f"{v:{cw}.4f}" for v in row)
        lines.append(f"{row_keys[i]:>{cw}} {vals}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════
# 5. Прямой нечёткий вывод (обобщённый modus ponens)
# ════════════════════════════════════════════════════════════════

def direct_inference(
    fact: FuzzySet,
    impl_matrix: list[list[float]],
    conclusion_template: FuzzySet,
) -> list[tuple[str, float]]:
    """
    B'(y_j) = sup_i [ T_H( A'(x_i), R[i][j] ) ]
    """
    c_keys = conclusion_template.keys()
    n_rows = len(fact.vals())
    result: list[tuple[str, float]] = []

    for j, key in enumerate(c_keys):
        sup = 0.0
        for i in range(n_rows):
            val = hamacher_tnorm(fact.vals()[i], impl_matrix[i][j])
            if val > sup:
                sup = val
        result.append((key, sup))

    return result


# ════════════════════════════════════════════════════════════════
# 6. Поиск дубликатов
# ════════════════════════════════════════════════════════════════

def find_duplicate(
    elems: list[tuple[str, float]],
    all_facts: dict[str, FuzzySet],
    tol: float = 1e-6,
) -> str | None:
    """Если множество с такими же значениями уже есть — вернуть его имя."""
    keys = [e[0] for e in elems]
    vals = {e[0]: e[1] for e in elems}
    for name, fs in all_facts.items():
        if fs.keys() != keys:
            continue
        if all(abs(fs.elements[k] - vals[k]) < tol for k in keys):
            return name
    return None


# ════════════════════════════════════════════════════════════════
# 7. Главный цикл вывода
# ════════════════════════════════════════════════════════════════

def run_inference(facts: dict[str, FuzzySet], rules: list[Rule]):
    """Полный цикл прямого нечёткого логического вывода."""

    # ── Вывод исходных данных ──
    print("=" * 62)
    print("  БАЗА ЗНАНИЙ")
    print("=" * 62)
    print("\n  Факты:")
    for fs in facts.values():
        print(f"    {fs}")
    print("\n  Правила:")
    for r in rules:
        print(f"    {r}")

    # ── Построение матриц импликаций ──
    print("\n" + "=" * 62)
    print("  МАТРИЦЫ ИМПЛИКАЦИЙ  (Хамахер)")
    print("=" * 62)

    rule_data: list[dict] = []
    for rule in rules:
        if rule.premise not in facts:
            print(f"  [!] предикат «{rule.premise}» не найден в фактах")
            continue
        if rule.conclusion not in facts:
            print(f"  [!] предикат «{rule.conclusion}» не найден в фактах")
            continue

        p = facts[rule.premise]
        c = facts[rule.conclusion]
        matrix = build_implication_matrix(p, c)

        rule_data.append(
            {
                "rule": rule,
                "matrix": matrix,
                "premise_tmpl": p,
                "conclusion_tmpl": c,
            }
        )

        print(f"\n  {rule.premise}(x)->{rule.conclusion}(y) :")
        print(format_matrix(matrix, p.keys(), c.keys()))

    # ── Цикл вывода ──
    print("\n" + "=" * 62)
    print("  ПРЯМОЙ НЕЧЁТКИЙ ВЫВОД")
    print("=" * 62)

    all_facts: dict[str, FuzzySet] = dict(facts)
    derived_counter = 0
    processed: set[tuple[str, str]] = set()
    changed = True

    while changed:
        changed = False
        for rd in rule_data:
            rule = rd["rule"]
            impl_m = rd["matrix"]
            p_tmpl = rd["premise_tmpl"]
            c_tmpl = rd["conclusion_tmpl"]

            for fname in list(all_facts):
                pair = (fname, str(rule))
                if pair in processed:
                    continue

                f = all_facts[fname]
                if not f.domain_matches(p_tmpl):
                    continue

                processed.add(pair)

                result_elems = direct_inference(f, impl_m, c_tmpl)
                derived_counter += 1
                new_name = f"_{derived_counter}"

                dup = find_duplicate(result_elems, all_facts)
                new_fs = FuzzySet(new_name, result_elems)

                if dup is not None:
                    print(f"  {{{fname}, {rule}}} ~ {new_fs} = {dup}")
                else:
                    print(f"  {{{fname}, {rule}}} ~ {new_fs}")
                    all_facts[new_name] = new_fs
                    changed = True

    # ── Итоговые результаты ──
    derived = {n: fs for n, fs in all_facts.items() if n.startswith("_")}
    print("\n" + "=" * 62)
    print("  ВЫВЕДЕННЫЕ ФАКТЫ")
    print("=" * 62)
    if derived:
        for fs in derived.values():
            print(f"    {fs}")
    else:
        print("    (новых фактов не выведено)")

    return all_facts


# ════════════════════════════════════════════════════════════════
# 8. Точка входа
# ════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = input("Имя файла базы знаний: ").strip()

    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except FileNotFoundError:
        print(f"Ошибка: файл «{path}» не найден.")
        sys.exit(1)

    facts, rules = parse_knowledge_base(text)

    if not facts:
        print("Ошибка: в базе знаний не найдено ни одного факта.")
        sys.exit(1)
    if not rules:
        print("Ошибка: в базе знаний не найдено ни одного правила.")
        sys.exit(1)

    run_inference(facts, rules)


if __name__ == "__main__":
    main()
