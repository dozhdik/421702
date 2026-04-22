"""
Главный модуль программы «Анализ формул логики высказываний».

Запускается без аргументов, запрашивает формулу у пользователя
и выводит список фиктивных переменных.
"""

from parser import parse_formula, SyntaxError as ParseSyntaxError
from lexer import Lexer, SyntaxError as LexSyntaxError
from fictitious import find_fictitious_vars, format_result
from ast_nodes import collect_vars


def main():
    """Основной цикл программы."""
    print("=== Анализ фиктивных переменных ===")
    print("Введите формулу сокращённого языка логики высказываний.")
    print("Переменные: заглавные латинские буквы (P, Q, A1, ...)")
    print("Операции:  !  /\\  V  ->  ~")
    print("Введите пустую строку для выхода.\n")

    while True:
        try:
            formula = input("Формула: ").strip()
            if not formula:
                print("Выход.")
                break

            # Парсинг формулы
            ast = parse_formula(formula)

            # Поиск фиктивных переменных
            fictitious = find_fictitious_vars(ast)
            all_vars = sorted(collect_vars(ast))

            # Вывод результата
            print(format_result(formula, fictitious))
            print(f"Все переменные: {', '.join(all_vars) if all_vars else 'нет'}")
            print()

        except (LexSyntaxError, ParseSyntaxError) as e:
            print(f"Ошибка разбора: {e}\n")
        except Exception as e:
            print(f"Ошибка: {e}\n")


if __name__ == "__main__":
    main()