#!/usr/bin/env python3
"""
Анализатор фиктивных переменных в логике высказываний.

Лабораторная работа: Семантический анализ формул логики высказываний.
Задача: Определить, какие пропозициональные переменные являются фиктивными.

Определение: Переменная X фиктивна в формуле F, если значение истинности F
не меняется при изменении X с True на False на любых фиксированных наборах
значений остальных переменных.

Ограничения: ЗАПРЕЩЕНО использовать re, eval(), exec(), sympy, lark, ply, pandas.
Разрешено: itertools, dataclasses.
"""

from fictitious_analyzer import (
    LexerError,
    ParserError,
    analyze_formula,
)


def main():
    """Основной цикл программы."""
    print("=" * 60)
    print("АНАЛИЗАТОР ФИКТИВНЫХ ПЕРЕМЕННЫХ")
    print("Логика высказываний")
    print("=" * 60)
    print("\nПоддерживаемый синтаксис:")
    print("  Переменные: заглавные латинские буквы (P, Q, A1, ...)")
    print("  Операции:")
    print("    !   - отрицание")
    print("    /\\  - конъюнкция")
    print("    V   - дизъюнкция")
    print("    ->  - импликация")
    print("    ~   - эквиваленция")
    print("\nВведите пустую строку для выхода\n")

    while True:
        try:
            formula = input("Формула: ").strip()

            if not formula:
                print("Выход.")
                break

            all_vars, fictitious = analyze_formula(formula)

            print(f"\nФормула: {formula}")
            print(f"Все переменные: {', '.join(all_vars) if all_vars else 'нет'}")

            if fictitious:
                print(f"Фиктивные переменные: {', '.join(fictitious)}")
            else:
                print("Фиктивных переменных нет")
            print()

        except (LexerError, ParserError, ValueError) as e:
            print(f"Ошибка разбора: {e}\n")
        except Exception as e:
            print(f"Ошибка: {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    main()
