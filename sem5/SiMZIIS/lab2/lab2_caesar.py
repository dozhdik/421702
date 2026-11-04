import argparse
import math
import time

ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
N = len(ALPHABET)
INDEX = {ch: i for i, ch in enumerate(ALPHABET)}

RU_FREQ = {
    "о": .1097, "е": .0845, "а": .0801, "и": .0735, "н": .0670, "т": .0626, "с": .0547,
    "р": .0473, "в": .0454, "л": .0440, "к": .0349, "м": .0321, "д": .0298, "п": .0281,
    "у": .0262, "я": .0201, "ы": .0190, "ь": .0174, "г": .0170, "з": .0165, "б": .0159,
    "ч": .0144, "й": .0121, "х": .0097, "ж": .0094, "ш": .0073, "ю": .0064, "ц": .0048,
    "щ": .0036, "э": .0032, "ф": .0026, "ъ": .0004, "ё": .0004,
}

_freq_sum = sum(RU_FREQ.values())
RU_FREQ = {ch: p / _freq_sum for ch, p in RU_FREQ.items()}


def _shift_char(ch, k):
    low = ch.lower()
    if low not in INDEX:
        return ch
    res = ALPHABET[(INDEX[low] + k) % N]
    return res.upper() if ch.isupper() else res


def caesar_encrypt(text, k):
    return "".join(_shift_char(ch, k) for ch in text)


def caesar_decrypt(text, k):
    return "".join(_shift_char(ch, -k + N) for ch in text)


def brute_force_table(cipher, width=60):
    print(f"{'Ключ':>4} | Расшифрованный текст")
    print("-" * (width + 8))
    for k in range(N):
        print(f"{k:>4} | {caesar_decrypt(cipher, k)[:width]}")


def brute_force_known_plaintext(cipher, plaintext):
    for attempt, k in enumerate(range(N), 1):
        if caesar_decrypt(cipher, k) == plaintext:
            return k, attempt
    return None, N


def chi_squared(text):
    letters = [c for c in text.lower() if c in INDEX]
    total = len(letters)
    if total == 0:
        return math.inf
    counts = {ch: 0 for ch in ALPHABET}
    for c in letters:
        counts[c] += 1
    return sum((counts[ch] - total * RU_FREQ[ch]) ** 2 / (total * RU_FREQ[ch]) for ch in ALPHABET)


def brute_force_frequency(cipher):
    if not any(ch.lower() in INDEX for ch in cipher):
        raise ValueError("В тексте нет русских букв; определить ключ невозможно")
    scores = sorted(((chi_squared(caesar_decrypt(cipher, k)), k) for k in range(N)))
    return scores


def affine_encrypt(text, a, b):
    if math.gcd(a, N) != 1:
        raise ValueError(f"a = {a} должно быть взаимно просто с n = {N}")
    out = []
    for ch in text:
        low = ch.lower()
        if low in INDEX:
            r = ALPHABET[(a * INDEX[low] + b) % N]
            out.append(r.upper() if ch.isupper() else r)
        else:
            out.append(ch)
    return "".join(out)


def affine_decrypt(text, a, b):
    a_inv = pow(a, -1, N)
    out = []
    for ch in text:
        low = ch.lower()
        if low in INDEX:
            r = ALPHABET[(a_inv * (INDEX[low] - b)) % N]
            out.append(r.upper() if ch.isupper() else r)
        else:
            out.append(ch)
    return "".join(out)


def keyword_alphabet(keyword):
    seen = []
    for ch in keyword.lower() + ALPHABET:
        if ch in INDEX and ch not in seen:
            seen.append(ch)
    return "".join(seen)


def keyword_caesar_encrypt(text, keyword, k):
    mixed = keyword_alphabet(keyword)
    out = []
    for ch in text:
        low = ch.lower()
        if low in INDEX:
            r = mixed[(INDEX[low] + k) % N]
            out.append(r.upper() if ch.isupper() else r)
        else:
            out.append(ch)
    return "".join(out)


def keyword_caesar_decrypt(text, keyword, k):
    mixed = keyword_alphabet(keyword)
    pos = {ch: i for i, ch in enumerate(mixed)}
    out = []
    for ch in text:
        low = ch.lower()
        if low in pos:
            r = ALPHABET[(pos[low] - k) % N]
            out.append(r.upper() if ch.isupper() else r)
        else:
            out.append(ch)
    return "".join(out)


DEMO_TEXT = ("Защита информации требует комплексного подхода. Надёжный шифр должен "
             "противостоять атаке полным перебором ключа и частотному анализу, "
             "поэтому простые шифры замены сегодня используются только в учебных целях.")


def demo(text, key):
    print(f"Алфавит (n = {N}): {ALPHABET}\n")
    print("=== 1. Зашифрование и расшифрование ===")
    print(f"Ключ k = {key}")
    print(f"Исходный текст:      {text}")
    cipher = caesar_encrypt(text, key)
    print(f"Зашифрованный текст: {cipher}")
    plain = caesar_decrypt(cipher, key)
    print(f"Расшифрованный текст: {plain}")
    print(f"Совпадает с исходным: {plain == text}\n")

    print("=== 2а. Атака полным перебором: визуальный метод ===")
    brute_force_table(cipher)

    print("\n=== 2б. Атака полным перебором: сравнение с известным исходным текстом ===")
    t0 = time.perf_counter()
    k_found, attempts = brute_force_known_plaintext(cipher, text)
    dt = time.perf_counter() - t0
    print(f"Найден ключ k = {k_found} за {attempts} попыток, время {dt * 1000:.3f} мс")

    print("\n=== 2в. Атака полным перебором: частотный анализ (исходный текст неизвестен) ===")
    t0 = time.perf_counter()
    scores = brute_force_frequency(cipher)
    dt = time.perf_counter() - t0
    for chi, k in scores[:5]:
        print(f"  k = {k:>2}: хи-квадрат = {chi:10.1f} | {caesar_decrypt(cipher, k)[:50]}")
    print(f"Наиболее вероятный ключ: k = {scores[0][1]} (время {dt * 1000:.3f} мс)")

    print("\n=== 3. Усложнённые варианты ===")
    a, b = 7, key
    aff = affine_encrypt(text, a, b)
    print(f"Аффинный шифр (a = {a}, b = {b}):\n  {aff}\n  расшифровано верно: {affine_decrypt(aff, a, b) == text}")
    print(f"  размер ключевого пространства: φ({N}) * {N} = "
          f"{sum(1 for x in range(1, N) if math.gcd(x, N) == 1) * N}")
    kw = "криптография"
    print(f"\nЦезарь с ключевым словом «{kw}», k = {key}:")
    print(f"  перемешанный алфавит: {keyword_alphabet(kw)}")
    kwc = keyword_caesar_encrypt(text, kw, key)
    print(f"  {kwc}\n  расшифровано верно: {keyword_caesar_decrypt(kwc, kw, key) == text}")


def interactive():
    while True:
        print("\n1 — зашифровать, 2 — расшифровать, 3 — взлом перебором, 0 — выход")
        choice = input("> ").strip()
        if choice == "0":
            break
        if choice in ("1", "2"):
            text = input("Текст: ")
            k = int(input(f"Ключ (0..{N - 1}): ")) % N
            print(caesar_encrypt(text, k) if choice == "1" else caesar_decrypt(text, k))
        elif choice == "3":
            cipher = input("Шифртекст: ")
            known = input("Известный исходный текст (Enter — неизвестен): ")
            brute_force_table(cipher)
            if known:
                print("Ключ:", brute_force_known_plaintext(cipher, known)[0])
            else:
                print("Наиболее вероятный ключ:", brute_force_frequency(cipher)[0][1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ЛР2: шифр Цезаря")
    parser.add_argument("-i", "--interactive", action="store_true")
    parser.add_argument("-k", "--key", type=int, default=9)
    args = parser.parse_args()
    interactive() if args.interactive else demo(DEMO_TEXT, args.key % N)
