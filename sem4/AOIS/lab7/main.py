import random

class AssociativeProcessor:
    def __init__(self, m=10, n=8):
        self.m = m  # Количество слов
        self.n = n  # Количество разрядов
        # Генерация случайного массива данных (память АЗУ)
        self.memory = [[random.randint(0, 1) for _ in range(n)] for _ in range(m)]

    def bits_to_int(self, bits):
        """Перевод списка битов в целое число"""
        return int("".join(map(str, bits)), 2)

    def int_to_bits(self, value):
        """Перевод числа в список битов длины n"""
        return [int(b) for b in format(value, f'0{self.n}b')]

    def compare_recurrence(self, word, argument):
        """
        Рекуррентное сравнение (g, l) от старшего разряда к младшему.
        g_prev=1, l_prev=0 -> Больше
        g_prev=0, l_prev=1 -> Меньше
        g_prev=0, l_prev=0 -> Равно
        """
        g_prev = 0
        l_prev = 0

        for i in range(self.n):
            a_i = argument[i]
            s_ji = word[i]

            # Отрицания (аппаратные инверторы)
            not_a_i = 1 - a_i
            not_s_ji = 1 - s_ji
            not_g_prev = 1 - g_prev
            not_l_prev = 1 - l_prev

            # Рекуррентные формулы из методички
            g_curr = g_prev | (not_a_i & s_ji & not_l_prev)
            l_curr = l_prev | (a_i & not_s_ji & not_g_prev)

            g_prev, l_prev = g_curr, l_curr

        return g_prev, l_prev

    def search_by_correspondence(self, argument_bits):
        """Поиск по соответствию (Вариант 4)"""
        counters = [0] * self.m
        print(f"\nПоиск по соответствию с аргументом: {''.join(map(str, argument_bits))} ({self.bits_to_int(argument_bits)})")
        print("-" * 70)
        print(f"{'№':<3} | {'Слово (Bin)':<10} | {'Dec':<4} | {'Совпадений':<10} | {'Статус'}")
        print("-" * 70)

        for j in range(self.m):
            word = self.memory[j]
            # Подсчёт совпадающих разрядов
            matches = sum(1 for a, s in zip(argument_bits, word) if a == s)
            counters[j] = matches
            val = self.bits_to_int(word)
            print(f"{j:<3} | {''.join(map(str, word)):<10} | {val:<4} | {matches:<10} | ")

        max_matches = max(counters)
        results = []
        for j in range(self.m):
            if counters[j] == max_matches:
                results.append(self.bits_to_int(self.memory[j]))

        print(f"\nМаксимальное число совпадений: {max_matches}/{self.n}")
        print(f"Найдено слов: {len(results)}")
        print(f"Значения: {results}")
        
        # Демонстрация работы рекуррентных триггеров для первого найденного слова
        if results:
            best_idx = counters.index(max_matches)
            g, l = self.compare_recurrence(self.memory[best_idx], argument_bits)
            print(f"Проверка рекуррентными триггерами для слова №{best_idx}: g={g}, l={l} (0,0 => Равно)")
            
        return results

# --- Запуск ---
if __name__ == "__main__":
    # Создаем процессор: 15 слов по 8 бит
    processor = AssociativeProcessor(m=15, n=8)
    
    # Задаем поисковый аргумент (например, 10101010)
    arg_bits = processor.int_to_bits(170)
    
    # Выполняем поиск по соответствию
    processor.search_by_correspondence(arg_bits)