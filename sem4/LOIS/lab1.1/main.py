r"""
//main.py
////////////////////////////////////////////
//Лабораторная работа №1 по дисциплине ЛОИС
//Выполнена студентом группы 421702 БГУИР Дождиковым Александром Игоревичем
//Модуль пользовательского интерфейса (CLI) и управления потоком выполнения программы.
//03.04.2026
//
//Ссылки на использованные источники
/*   [1] Python Software Foundation. Official Python Documentation [Электронный ресурс] : 
 *   документация Python. – Режим доступа: https://docs.python.org/3/. 
 *   – Дата доступа: 04.06.2026.
 */
/*   [2] Python Software Foundation. Built-in Functions [Электронный ресурс] : 
 *   документация Python. – Режим доступа: https://docs.python.org/3/library/functions.html#input. 
 *   – Дата доступа: 04.06.2026.
 */
/*   [3] Создаем удобный CLI и REPL для Python-скриптов [Электронный ресурс] // 
 *   Habr : IT-платформа. – Режим доступа: https://habr.com/ru/articles/450850/. 
 *   – Дата доступа: 04.06.2026.
 */
"""

import sys
from logic_formula import FormulaAnalyzer, LexerError, ParseError


def analyze_and_print(formula: str) -> None:
    print(f"\n{'─'*55}")
    print(f"    Формула: {formula}")
    print(f"{'─'*55}")
    try:
        analyzer = FormulaAnalyzer.from_string(formula)
        result = analyzer.analyze()

        if not result:
            print("  Переменных нет (формула — константа)")
            return

        for var, is_dummy in result.items():
            status = "ФИКТИВНАЯ" if is_dummy else "существенная"
            print(f"  {var:10s} — {status}")

        dummies = [v for v, d in result.items() if d]
        if dummies:
            print(f"\n  Итог: фиктивные переменные → {', '.join(dummies)}")
        else:
            print("\n  Итог: фиктивных переменных нет")

    except LexerError as e:
        print(f"  Ошибка лексического анализа: {e}")
    except ParseError as e:
        print(f"  Ошибка синтаксического анализа: {e}")


def print_help() -> None:
    print("=" * 55)
    print("  Анализатор фиктивных переменных (ЛОИС)")
    print("=" * 55)
    print("  Символы:")
    print("    !   — отрицание")
    print("    /\\  — конъюнкция")
    print("    V   — дизъюнкция")
    print("    ->  — импликация")
    print("    ~   — эквиваленция")
    print("    1   — истина")
    print("    0   — ложь")
    print("  Переменные: одиночные заглавные латинские буквы (A, B, C, ...)")
    print("  Правила:")
    print("    Все операции — только в скобках:")
    print("      Отрицание:    (!A), (!(!A)), (!(A/\\B))")
    print("      Бинарные:     (A/\\B), (A->(BVC))")
    print("    Без скобок допустимы только переменные и константы (A, 1, 0)")
    print("    Пробелы запрещены")
    print("  Выход: q / quit / exit / пустая строка")
    print("=" * 55)


def main() -> None:
    if len(sys.argv) > 1:
        formula = "".join(sys.argv[1:])
        print_help()
        analyze_and_print(formula)
    else:
        print_help()
        while True:
            try:
                formula = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if formula.lower() in ("q", "quit", "exit", ""):
                break
            analyze_and_print(formula)


if __name__ == "__main__":
    main()
