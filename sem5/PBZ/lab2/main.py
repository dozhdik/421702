"""Entry point for the insurance application."""
import argparse

from models.database import init_database


def main():
    parser = argparse.ArgumentParser(description="Учёт договоров страхования")
    parser.add_argument("--seed", action="store_true", help="загрузить демонстрационные данные и выйти")
    parser.add_argument("--console", action="store_true", help="запустить консольный интерфейс")
    args = parser.parse_args()
    init_database()
    if args.seed:
        from models.seed import seed_database
        print(seed_database())
    elif args.console:
        from cli import menu
        try:
            menu()
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
    else:
        try:
            import tkinter as tk
            from ui.app import App
            App().mainloop()
        except ImportError:
            parser.exit(1, "Не установлен Tkinter. Для Ubuntu/Mint: sudo apt install python3-tk\n")
        except tk.TclError as exc:
            parser.exit(1, f"Не удалось открыть окно: {exc}\n")


if __name__ == "__main__":
    main()
