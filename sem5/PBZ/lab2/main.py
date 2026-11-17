"""Entry point for the insurance application."""
import argparse

from models.database import init_database


def run_sessions(login_class, app_class):
    while True:
        login = login_class()
        login.mainloop()
        if login.tenant is None:
            return
        app = app_class(login.tenant)
        app.mainloop()
        if not app.logout_requested:
            return


def main():
    parser = argparse.ArgumentParser(description="Учёт договоров страхования")
    parser.add_argument("--console", action="store_true", help="запустить консольный интерфейс")
    args = parser.parse_args()
    init_database()
    if args.console:
        parser.exit(1, "Консольный режим недоступен: выполните вход в графическом приложении.\n")
    else:
        try:
            import tkinter as tk
        except ImportError:
            parser.exit(1, "Не установлен Tkinter. Для Ubuntu/Mint: sudo apt install python3-tk\n")
        from ui.app import App, Login
        try:
            run_sessions(Login, App)
        except tk.TclError as exc:
            parser.exit(1, f"Не удалось открыть окно: {exc}\n")


if __name__ == "__main__":
    main()
