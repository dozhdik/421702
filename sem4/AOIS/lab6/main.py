#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лабораторная работа №6: Моделирование таблиц хеширования
Вариант 9: Тематика "Спорт"
Язык: Python 3
"""

import sys

ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
BASE = 33

class HashCell:
    def __init__(self):
        self.ID = ""
        self.C = 0
        self.U = 0
        self.T = 1
        self.L = 0
        self.D = 0
        self.P0 = 0
        self.Pi = ""

class HashTable:
    def __init__(self, H=20, B=0):
        self.H = H
        self.B = B
        self.table = [HashCell() for _ in range(H)]

    def calc_v(self, keyword: str) -> int:
        if len(keyword) < 2:
            return 0
        i1 = ALPHABET.find(keyword[0].upper())
        i2 = ALPHABET.find(keyword[1].upper())
        if i1 == -1 or i2 == -1:
            return 0
        return i1 * BASE + i2

    def calc_h(self, V: int) -> int:
        return (V % self.H + self.B) % self.H

    def insert(self, keyword: str, data: str) -> bool:
        idx, _ = self.search(keyword)
        if idx != -1:
            print(f"[WARN] Запись с ключом '{keyword}' уже существует.")
            return False

        V = self.calc_v(keyword)
        h = self.calc_h(V)
        idx = h
        steps = 0

        while self.table[idx].U == 1 and steps < self.H:
            idx = (idx + 1) % self.H
            steps += 1

        if steps == self.H:
            print("[ERROR] Таблица заполнена.")
            return False

        cell = self.table[idx]
        cell.ID = keyword
        cell.Pi = data
        cell.U = 1
        cell.D = 0
        cell.P0 = idx

        if idx != h:
            cell.C = 0
            curr = h
            prev_idx = -1
            while curr != idx:
                if self.table[curr].U == 1 and self.table[curr].D == 0:
                    prev_idx = curr
                curr = (curr + 1) % self.H

            if prev_idx != -1:
                self.table[prev_idx].P0 = idx
                self.table[prev_idx].T = 0
            self.table[h].C = 1
        else:
            cell.C = 0
            cell.T = 1

        print(f"[OK] Добавлено: '{keyword}' в ячейку {idx} (h={h})")
        return True

    def search(self, keyword: str) -> tuple:
        V = self.calc_v(keyword)
        h = self.calc_h(V)
        idx = h
        steps = 0
        while steps < self.H:
            cell = self.table[idx]
            if cell.U == 1 and cell.D == 0 and cell.ID == keyword:
                return idx, cell.Pi
            if cell.U == 0 or (cell.T == 1 and cell.P0 == idx):
                break
            idx = (idx + 1) % self.H
            steps += 1
        return -1, None

    def delete(self, keyword: str) -> bool:
        idx, _ = self.search(keyword)
        if idx == -1:
            print("[WARN] Ключ не найден.")
            return False

        cell = self.table[idx]
        h_del = self.calc_h(self.calc_v(keyword))
        cell.D = 1

        # а) Одиночная строка
        if cell.T == 1 and cell.P0 == idx:
            cell.U = 0
        # б) Последняя строка цепочки
        elif cell.T == 1 and cell.P0 != idx:
            cell.U = 0
            curr = h_del
            while curr != idx:
                if self.table[curr].U == 1 and self.table[curr].D == 0 and self.table[curr].P0 == idx:
                    self.table[curr].T = 1
                    break
                curr = (curr + 1) % self.H
        # в) Средняя строка цепочки (T=0, P0 != h_del)
        elif cell.T == 0 and cell.P0 != h_del:
            next_idx = cell.P0
            nxt = self.table[next_idx]
            cell.ID, cell.Pi, cell.C, cell.T, cell.L, cell.P0 = \
                nxt.ID, nxt.Pi, nxt.C, nxt.T, nxt.L, nxt.P0
            nxt.U = 0
            nxt.D = 1
        # г) Первая строка цепочки (T=0, C=1)
        elif cell.T == 0 and cell.C == 1:
            next_idx = cell.P0
            nxt = self.table[next_idx]
            cell.ID, cell.Pi, cell.C, cell.T, cell.L, cell.P0 = \
                nxt.ID, nxt.Pi, nxt.C, nxt.T, nxt.L, nxt.P0
            nxt.U = 0
            nxt.D = 1

        print(f"[OK] Удалено: '{keyword}' (ячейка {idx})")
        return True

    def display(self):
        # Фиксированные ширины столбцов для идеального выравнивания
        header = f"{'№':<5} | {'ID':<16} | {'C':<3} | {'U':<3} | {'T':<3} | {'L':<3} | {'D':<3} | {'P0':<4} | {'Pi':<35} | {'V':<6} | {'h':<4}"
        print(header)
        print("-" * len(header))
        
        for i, c in enumerate(self.table):
            if c.ID:
                V = self.calc_v(c.ID)
                h = self.calc_h(V)
            else:
                V = "-"
                h = "-"
            
            # Обрезаем длинные данные и дополняем пробелами, чтобы столбец не разъезжался
            pi_str = str(c.Pi)[:35].ljust(35)
            print(f"{i:<5} | {c.ID:<16} | {c.C:<3} | {c.U:<3} | {c.T:<3} | {c.L:<3} | {c.D:<3} | {c.P0:<4} | {pi_str} | {str(V):<6} | {str(h):<4}")

        occupied = sum(1 for c in self.table if c.U == 1 and c.D == 0)
        print(f"[STAT] Коэффициент заполнения: {occupied / self.H:.2%}")

def main():
    ht = HashTable(H=20, B=0)
    
    initial_data = [
        ("Футбол", "Командная игра с мячом"),
        ("Баскетбол", "Игра с мячом и корзиной"),
        ("Теннис", "Индивидуальный или парный вид"),
        ("Волейбол", "Игра через сетку"),
        ("Хоккей", "Зимний командный вид спорта"),
        ("Плавание", "Преодоление дистанции в воде"),
        ("Бокс", "Единоборство в перчатках"),
        ("Дзюдо", "Японское боевое искусство"),
        ("Самбо", "Советское боевое искусство"),
        ("Гимнастика", "Упражнения на снарядах"),
        ("Гребля", "Спорт на водной глади"),
        ("Парусный", "Управление судном парусами")
    ]

    print("[INIT] Инициализация хеш-таблицы (Вариант 9: Спорт)...")
    for kw, data in initial_data:
        ht.insert(kw, data)
    ht.display()

    print("\n[SEARCH] Тест поиска: 'Теннис'")
    idx, val = ht.search("Теннис")
    print(f"Результат: ячейка {idx}, данные: {val}" if idx != -1 else "Не найдено")

    print("\n[ADD] Тест добавления: 'Фехтование', 'Бой на мечах'")
    ht.insert("Фехтование", "Бой на мечах")

    print("\n[DELETE] Тест удаления: 'Бокс'")
    ht.delete("Бокс")

    print("\n[STAT] Финальное состояние таблицы:")
    ht.display()

if __name__ == "__main__":
    main()