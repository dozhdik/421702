import argparse
import ctypes
import ctypes.util
import itertools
import os
import sys
import time
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RU_LOWER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
RU_UPPER = RU_LOWER.upper()
DIGITS = "0123456789"
ALPHABET = RU_LOWER + RU_UPPER + DIGITS
N = len(ALPHABET)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


class CRand:

    def __init__(self):
        if sys.platform.startswith("win"):
            self.libc = ctypes.cdll.msvcrt
            self.rand_max = 32767
        else:
            self.libc = ctypes.CDLL(ctypes.util.find_library("c"))
            self.rand_max = 2**31 - 1
        self.libc.rand.restype = ctypes.c_int
        self.libc.srand.argtypes = [ctypes.c_uint]

    def srand_from_timer(self):
        seed = int(time.time())
        self.libc.srand(ctypes.c_uint(seed))
        return seed

    def rand(self):
        return self.libc.rand()

    def randbelow(self, bound):
        if not 1 <= bound <= self.rand_max + 1:
            raise ValueError("Недопустимая граница для randbelow")
        limit = ((self.rand_max + 1) // bound) * bound
        while True:
            value = self.rand()
            if value < limit:
                return value % bound


def generate_string(length, rng):
    if length < 1:
        raise ValueError("Длина строки должна быть положительной")
    return "".join(ALPHABET[rng.randbelow(N)] for _ in range(length))


CHI2_CRIT_75_005 = 96.217


def frequency_analysis(sample):
    if not sample or any(ch not in ALPHABET for ch in sample):
        raise ValueError("Нужна непустая строка из символов алфавита")
    counts = Counter(sample)
    freqs = [counts.get(ch, 0) for ch in ALPHABET]
    expected = len(sample) / N
    chi2 = sum((f - expected) ** 2 / expected for f in freqs)
    return freqs, expected, chi2


def plot_histogram(freqs, expected, total, path):
    fig, ax = plt.subplots(figsize=(15, 5))
    colors = (["#4C72B0"] * 33) + (["#DD8452"] * 33) + (["#55A868"] * 10)
    ax.bar(range(N), freqs, color=colors, width=0.8)
    ax.axhline(expected, color="red", linestyle="--", linewidth=1.2,
               label=f"Ожидаемая частота = {expected:.0f}")
    ax.set_xticks(range(N))
    ax.set_xticklabels(list(ALPHABET), fontsize=8)
    ax.set_xlim(-1, N)
    ax.set_ylim(0, max(freqs) * 1.15)
    ax.set_xlabel("Символ алфавита (синие — строчные, оранжевые — прописные, зелёные — цифры)")
    ax.set_ylabel("Количество появлений")
    ax.set_title(f"Частотное распределение символов в строке длиной {total:,} символов".replace(",", " "))
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def brute_force(password):
    if not password or any(ch not in ALPHABET for ch in password):
        raise ValueError("Пароль должен быть непустым и принадлежать алфавиту")
    target = tuple(password)
    attempts = 0
    start = time.perf_counter()
    for attempts, candidate in enumerate(itertools.product(ALPHABET, repeat=len(password)), 1):
        if candidate == target:
            break
    return attempts, time.perf_counter() - start


def measure_speed(seconds=2.0):
    runs = [brute_force(ALPHABET[-1] * 3) for _ in range(3)]
    return sum(a for a, t in runs) / sum(t for a, t in runs)


def experimental_mean_times(rng, source, trials_by_len):
    if not source or any(ch not in ALPHABET for ch in source):
        raise ValueError("Источник должен быть непустой строкой из алфавита")
    results = {}
    for length, trials in trials_by_len.items():
        if not 1 <= length <= len(source) or trials < 1:
            raise ValueError("Недопустимые длина подстроки или число испытаний")
        times, tries = [], []
        for _ in range(trials):
            pos = rng.randbelow(len(source) - length + 1)
            pwd = source[pos:pos + length]
            a, t = brute_force(pwd)
            times.append(t)
            tries.append(a)
        results[length] = (sum(times) / trials, sum(tries) / trials)
        print(f"  L = {length}: {trials} паролей, среднее число попыток = {results[length][1]:.0f}, "
              f"среднее время = {results[length][0]:.4f} с")
    return results


def theoretical_mean_time(length, speed):
    if length < 1 or speed <= 0:
        raise ValueError("Длина и скорость должны быть положительными")
    return (N ** length + 1) / (2 * speed)


def human_time(seconds):
    units = [("лет", 365.25 * 24 * 3600), ("сут", 24 * 3600), ("ч", 3600), ("мин", 60), ("с", 1)]
    if seconds < 1:
        return f"{seconds * 1000:.3g} мс"
    for name, size in units:
        if seconds >= size:
            value = seconds / size
            return f"{value:.3g} {name}" if value < 1e6 else f"{value:.2e} {name}"
    return f"{seconds:.3g} с"


def plot_time_vs_length(speed, experimental, path, max_len=12):
    lengths = list(range(1, max_len + 1))
    fig, ax = plt.subplots(figsize=(10, 6))
    attackers = [(speed, f"Этот ПК, Python ({speed:.2e} пар./с)", "#4C72B0"),
                 (1e9, "Модель V = 10⁹ пар./с", "#DD8452"),
                 (1e12, "Модель V = 10¹² пар./с", "#C44E52")]
    for v, label, color in attackers:
        ax.plot(lengths, [theoretical_mean_time(L, v) for L in lengths], marker="o", label=label, color=color)
    ex_l = sorted(experimental)
    ax.scatter(ex_l, [experimental[L][0] for L in ex_l], s=110, facecolors="none", edgecolors="black",
               linewidths=2, zorder=5, label="Эксперимент (реальный перебор)")
    for t, name in [(60, "1 минута"), (86400, "1 сутки"), (365.25 * 86400, "1 год"), (100 * 365.25 * 86400, "100 лет")]:
        ax.axhline(t, color="grey", linestyle=":", linewidth=0.8)
        ax.text(max_len + 0.1, t, name, va="center", fontsize=8, color="grey")
    ax.set_yscale("log")
    ax.set_xticks(lengths)
    ax.set_xlabel("Длина пароля L, символов")
    ax.set_ylabel("Среднее время подбора, с (логарифмическая шкала)")
    ax.set_title(f"Зависимость среднего времени подбора пароля от длины (алфавит N = {N})")
    ax.grid(True, which="major", alpha=0.3)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="ЛР1: генерация паролей, вариант 9")
    parser.add_argument("--length", type=int, help="длина генерируемой строки")
    parser.add_argument("--sample", type=int, default=200_000,
                        help="длина строки для проверки равномерности (по умолчанию 200000)")
    args = parser.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"Алфавит варианта 9 (N = {N}):\n{ALPHABET}\n")
    rng = CRand()
    seed = rng.srand_from_timer()
    print(f"srand(time(NULL)): seed = {seed}")

    length = args.length if args.length is not None else int(input("Введите длину генерируемой строки: "))
    if length < 1 or args.sample < 5 * N:
        parser.error("Длина должна быть >= 1, --sample должен быть >= 380 для критерия хи-квадрат")
    s = generate_string(length, rng)
    print(f"Сгенерированная строка ({length} символов): {s}\n")

    big = generate_string(args.sample, rng)
    freqs, expected, chi2 = frequency_analysis(big)
    hist_path = os.path.join(OUT_DIR, "lab1_histogram.png")
    plot_histogram(freqs, expected, args.sample, hist_path)
    print(f"Проверка равномерности на строке из {args.sample} символов:")
    print(f"  ожидаемая частота символа: {expected:.1f}")
    print(f"  min = {min(freqs)}, max = {max(freqs)}, отклонение от ожидаемой: "
          f"{(min(freqs) - expected) / expected * 100:+.2f}% … {(max(freqs) - expected) / expected * 100:+.2f}%")
    verdict = "гипотеза о равномерности НЕ отвергается" if chi2 < CHI2_CRIT_75_005 else "гипотеза отвергается"
    print(f"  хи-квадрат = {chi2:.2f} (критическое значение {CHI2_CRIT_75_005} при alpha = 0.05) -> {verdict}")
    print(f"  гистограмма: {hist_path}\n")

    print("Измерение скорости перебора...")
    speed = measure_speed()
    print(f"  скорость перебора: {speed:,.0f} паролей/с\n".replace(",", " "))

    print("Экспериментальный подбор паролей, выбранных из сгенерированной строки:")
    experimental = experimental_mean_times(rng, s, {L: n for L, n in {1: 200, 2: 100, 3: 20, 4: 5}.items() if L <= len(s)})

    print("\nСравнение эксперимента и расчёта T = (N^L + 1) / (2V):")
    for L, (t, _) in experimental.items():
        print(f"  L = {L}: эксперимент {t:.4f} с, расчёт {theoretical_mean_time(L, speed):.4f} с")

    print("\nРасчётное среднее время подбора:")
    print(f"{'L':>3} | {'N^L':>12} | {'этот ПК':>14} | {'10^9 пар./с':>14} | {'10^12 пар./с':>14}")
    for L in range(1, 13):
        print(f"{L:>3} | {N ** L:>12.3e} | {human_time(theoretical_mean_time(L, speed)):>14} | "
              f"{human_time(theoretical_mean_time(L, 1e9)):>14} | {human_time(theoretical_mean_time(L, 1e12)):>14}")

    import csv
    with open(os.path.join(OUT_DIR, "lab1_experiment.csv"), "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["length", "mean_time_s", "mean_attempts", "model_time_s", "speed_per_s"])
        for L, (t, attempts) in experimental.items():
            writer.writerow([L, t, attempts, theoretical_mean_time(L, speed), speed])
    with open(os.path.join(OUT_DIR, "lab1_frequency.csv"), "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f);writer.writerow(["symbol", "count", "expected"])
        writer.writerows(zip(ALPHABET, freqs, [expected] * N))
    graph_path = os.path.join(OUT_DIR, "lab1_time_vs_length.png")
    plot_time_vs_length(speed, experimental, graph_path)
    print(f"\nГрафик: {graph_path}")


if __name__ == "__main__":
    main()
