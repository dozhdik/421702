"""
Точка входа приложения управления складскими товарами
Лабораторная работа №2, Вариант 6
Архитектура: MVC
"""
import tkinter as tk
from model import WarehouseModel
from view import WarehouseView
from controller import WarehouseController


def main():
    """Главная функция запуска приложения"""
    root = tk.Tk()

    model = WarehouseModel()
    view = WarehouseView(root)
    controller = WarehouseController(model, view)

    controller.run()


if __name__ == "__main__":
    main()
