"""
Лабораторная работа №4. Открытое распространение ключей (протокол Диффи - Хеллмана).
Вариант 9: P = 7489.

Функции программы:
  1) быстрое возведение в степень по модулю методом последовательного возведения
     в квадрат и умножения (взятие по модулю на каждом шаге);
  2) поиск первообразного корня g поля GF(P) перебором по возрастанию:
     g принимается, если его степени g^1..g^(P-1) mod P принимают все значения 1..P-1;
  3) генерация общего секрета Алисой и Бобом;
  4) демонстрация атаки «человек посередине»;
  5) оценка стойкости: подбор секрета дискретным логарифмированием (полный перебор).

Запуск:
  python3 lab4_diffie_hellman.py              # P = 7489, случайные секреты a и b
  python3 lab4_diffie_hellman.py -a 1234 -b 5678
"""

import argparse
import secrets
import time

P = 7489


# ---------------------------------------------------------------------------
# 1. Быстрое возведение в степень по модулю
# ---------------------------------------------------------------------------
def mod_pow(x, a, n, trace=False):
    """x^a mod n методом «возведение в квадрат и умножение» (справа налево по битам a).
    a = a_{j-1}2^{j-1} + ... + a_1*2 + a_0,  x^a = П x^(2^i) по битам a_i = 1."""
    result = 1
    base = x % n                       # x^(2^0)
    i = 0
    steps = []
    while a > 0:
        bit = a & 1
        if bit:
            result = (result * base) % n          # умножение, mod на каждом шаге
        steps.append((i, bit, base, result))
        base = (base * base) % n                  # x^(2^(i+1)) = (x^(2^i))^2 mod n
        a >>= 1
        i += 1
    if trace:
        print(f"  {'i':>2} {'a_i':>3} {'x^(2^i) mod n':>14} {'результат':>10}")
        for i, bit, b, r in steps:
            print(f"  {i:>2} {bit:>3} {b:>14} {r:>10}")
    return result


# ---------------------------------------------------------------------------
# 2. Проверка простоты и поиск первообразного корня
# ---------------------------------------------------------------------------
def is_prime(n):
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def is_primitive_root(g, p):
    """Метод из задания: перебрать степени g^1..g^(p-1) mod p (каждая следующая = предыдущая*g mod p)
    и проверить, что получены все значения 1..p-1 без повторов."""
    seen = set()
    value = 1
    for k in range(1, p):
        value = (value * g) % p
        if value in seen:          # повтор раньше времени: порядок g меньше p-1
            return False, k - 1
        seen.add(value)
    return len(seen) == p - 1, p - 1


def find_primitive_root(p, verbose=True):
    for g in range(2, p):
        ok, order = is_primitive_root(g, p)
        if verbose:
            status = "первообразный корень" if ok else f"не подходит, порядок = {order}"
            print(f"  g = {g}: {status}")
        if ok:
            return g
    return None


def factorize(n):
    f, d = [], 2
    while d * d <= n:
        while n % d == 0:
            f.append(d)
            n //= d
        d += 1
    if n > 1:
        f.append(n)
    return f


def check_by_factors(g, p):
    """Контрольная проверка: g — первообразный корень, если g^((p-1)/q) != 1 для каждого простого q | p-1."""
    return all(mod_pow(g, (p - 1) // q, p) != 1 for q in set(factorize(p - 1)))


# ---------------------------------------------------------------------------
# 3. Протокол Диффи - Хеллмана
# ---------------------------------------------------------------------------
def diffie_hellman(p, g, a, b):
    print(f"\nОткрытые параметры: P = {p}, g = {g}")
    print(f"1) Алиса выбирает секрет a = {a} и вычисляет A = g^a mod P:")
    A = mod_pow(g, a, p, trace=True)
    print(f"   A = {g}^{a} mod {p} = {A}  -> отправляет Бобу")
    print(f"2) Боб выбирает секрет b = {b} и вычисляет B = g^b mod P:")
    B = mod_pow(g, b, p, trace=True)
    print(f"   B = {g}^{b} mod {p} = {B}  -> отправляет Алисе")
    print("3) Алиса вычисляет K = B^a mod P:")
    K_alice = mod_pow(B, a, p, trace=True)
    print(f"   K_A = {B}^{a} mod {p} = {K_alice}")
    print("4) Боб вычисляет K = A^b mod P:")
    K_bob = mod_pow(A, b, p, trace=True)
    print(f"   K_B = {A}^{b} mod {p} = {K_bob}")
    print(f"Проверка g^(ab) mod P = {mod_pow(g, a * b, p)}; общий секрет совпадает: {K_alice == K_bob}")
    return A, B, K_alice


# ---------------------------------------------------------------------------
# 4. Атака «человек посередине» и 5. дискретное логарифмирование
# ---------------------------------------------------------------------------
def mitm_demo(p, g, a, b):
    j = secrets.randbelow(p - 3) + 2
    A, B, J = mod_pow(g, a, p), mod_pow(g, b, p), mod_pow(g, j, p)
    print(f"\nАтака «человек посередине»: Джо выбирает j = {j}, J = g^j mod P = {J}")
    print(f"  Алиса -> A = {A} -> перехвачено Джо; Бобу Джо отправляет J = {J}")
    print(f"  Боб   -> B = {B} -> перехвачено Джо; Алисе Джо отправляет J = {J}")
    k_aj, k_ja = mod_pow(J, a, p), mod_pow(A, j, p)
    k_bj, k_jb = mod_pow(J, b, p), mod_pow(B, j, p)
    print(f"  Ключ Алиса-Джо: у Алисы {k_aj}, у Джо {k_ja}")
    print(f"  Ключ Боб-Джо:   у Боба {k_bj}, у Джо {k_jb}")
    print("  Алиса и Боб уверены, что общаются друг с другом, но ключи у них разные, "
          "и Джо расшифровывает и перешифровывает весь трафик.")


def discrete_log_bruteforce(g, A, p):
    """Пассивный атакующий: найти x, при котором g^x mod P = A, полным перебором."""
    value = 1
    for x in range(0, p - 1):
        if value == A:
            return x
        value = (value * g) % p
    return None


def main():
    parser = argparse.ArgumentParser(description="ЛР4: протокол Диффи - Хеллмана")
    parser.add_argument("-p", type=int, default=P)
    parser.add_argument("-a", type=int, help="секрет Алисы")
    parser.add_argument("-b", type=int, help="секрет Боба")
    args = parser.parse_args()
    p = args.p

    print(f"P = {p}, простое: {is_prime(p)}")
    print(f"P - 1 = {p - 1} = {' * '.join(map(str, factorize(p - 1)))}")
    print("\nПоиск первообразного корня перебором по возрастанию:")
    t0 = time.perf_counter()
    g = find_primitive_root(p)
    print(f"Найден g = {g} за {(time.perf_counter() - t0) * 1000:.1f} мс")
    print(f"Контроль через делители P-1: {check_by_factors(g, p)}")
    print(f"Сравнение mod_pow со встроенной pow: "
          f"{all(mod_pow(g, e, p) == pow(g, e, p) for e in range(0, 3 * p, 7))}")

    a = args.a if args.a else secrets.randbelow(p - 3) + 2
    b = args.b if args.b else secrets.randbelow(p - 3) + 2
    A, B, K = diffie_hellman(p, g, a, b)

    mitm_demo(p, g, a, b)

    print("\nПассивная атака: дискретный логарифм полным перебором")
    t0 = time.perf_counter()
    a_found = discrete_log_bruteforce(g, A, p)
    dt = time.perf_counter() - t0
    print(f"  найдено a = {a_found} (настоящее a = {a}), K = B^a mod P = {mod_pow(B, a_found, p)}, "
          f"время {dt * 1000:.2f} мс")


if __name__ == "__main__":
    main()
