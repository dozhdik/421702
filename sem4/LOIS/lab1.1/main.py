import sys
from logic_formula import FormulaAnalyzer, LexerError, ParseError


def analyze_and_print(formula: str) -> None:
    print(f"\n{'─' * 55}")
    print(f"    Формула: {formula}")
    print(f"{'─' * 55}")
    try:
        analyzer = FormulaAnalyzer.from_string(formula)
        result   = analyzer.analyze()

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
    print("  Операции:")
    print("    !    — отрицание")
    print("    /\\   — конъюнкция")
    print("    V    — дизъюнкция")
    print("    ->   — импликация")
    print("    ~    — эквиваленция")
    print("    1    — истина")
    print("    0    — ложь")
    print()
    print("  Переменные: одиночные заглавные буквы A–Z (кроме V)")
    print()
    print("  Синтаксис строго скобочный — каждая операция в скобках:")
    print("    Отрицание : (!A)  (!(!A))  (!(A/\\B))")
    print("    Бинарные  : (A/\\B)  (AVB)  (A->B)  (A~B)")
    print("    Вложение  : ((A/\\B)->C)  ((AVB)/\\(!C))")
    print()
    print("  Пробелы запрещены.")
    print("  Выход: q / quit / exit / пустая строка")
    print("=" * 55)


def main() -> None:
    if len(sys.argv) > 1:
        if len(sys.argv) > 2:
            print("Ошибка: формулу нужно передавать в кавычках.")
            print('Пример: python main.py "(A/\\B)"')
            sys.exit(1)
        print_help()
        analyze_and_print(sys.argv[1])
    else:
        print_help()
        while True:
            try:
                formula = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if formula.lower() in ("q", "quit", "exit", ""):
                break
            analyze_and_print(formula)


if __name__ == "__main__":
    main()