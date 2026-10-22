"""
Лабораторная работа №5. Асимметричное шифрование и электронная цифровая подпись (RSA).

Реализовано без криптографических библиотек:
  - генерация простых чисел p, q заданной длины (по умолчанию 1024 бита) тестом Миллера - Рабина;
  - генерация ключей: n = p*q, phi(n) = (p-1)(q-1), e = 65537, d = e^(-1) mod phi(n)
    (расширенный алгоритм Евклида);
  - зашифрование c = m^e mod n и расшифрование m = c^d mod n (поблочно);
  - цифровая подпись s = h^d mod n и проверка h* = s^e mod n, где h = SHA-256(сообщение);
  - возведение в степень по модулю — методом последовательного возведения в квадрат и умножения.

Обмен данными через файлы: открытый ключ, секретный ключ, исходное сообщение,
зашифрованное сообщение (а также расшифрованное сообщение и файл подписи).

Команды:
  python3 lab5_rsa.py keygen  --bits 1024 --pub public.key --priv private.key
  python3 lab5_rsa.py encrypt --pub public.key  --in message.txt   --out encrypted.txt
  python3 lab5_rsa.py decrypt --priv private.key --in encrypted.txt --out decrypted.txt
  python3 lab5_rsa.py sign    --priv private.key --in message.txt   --out signature.txt
  python3 lab5_rsa.py verify  --pub public.key  --in message.txt   --sig signature.txt
  python3 lab5_rsa.py test                     # 10 наборов тестовых данных -> tests/
"""

import argparse
import hashlib
import os
import secrets
import sys
import time

E_DEFAULT = 65537


# ---------------------------------------------------------------------------
# Арифметика
# ---------------------------------------------------------------------------
def mod_pow(x, a, n):
    """x^a mod n методом последовательного возведения в квадрат и умножения."""
    result = 1
    base = x % n
    while a > 0:
        if a & 1:
            result = (result * base) % n
        base = (base * base) % n
        a >>= 1
    return result


def extended_gcd(a, b):
    """Возвращает (g, x, y): a*x + b*y = g = НОД(a, b)."""
    old_r, r = a, b
    old_x, x = 1, 0
    old_y, y = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_x, x = x, old_x - q * x
        old_y, y = y, old_y - q * y
    return old_r, old_x, old_y


def mod_inverse(e, m):
    g, x, _ = extended_gcd(e, m)
    if g != 1:
        raise ValueError("обратного элемента не существует")
    return x % m


SMALL_PRIMES = [p for p in range(3, 2000) if all(p % d for d in range(2, int(p ** 0.5) + 1))]


def is_probable_prime(n, rounds=40):
    """Тест Миллера - Рабина: вероятность ошибки не более 4^(-rounds)."""
    if n < 2:
        return False
    for p in SMALL_PRIMES:                      # быстрый отсев делением на малые простые
        if n == p:
            return True
        if n % p == 0:
            return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = mod_pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits):
    """Случайное простое ровно из bits бит (старшие 2 бита = 1, чтобы n имело 2*bits бит)."""
    while True:
        candidate = secrets.randbits(bits) | (0b11 << (bits - 2)) | 1
        if is_probable_prime(candidate):
            return candidate


# ---------------------------------------------------------------------------
# Ключи
# ---------------------------------------------------------------------------
def generate_keys(bits=1024, e=E_DEFAULT):
    while True:
        p = generate_prime(bits)
        q = generate_prime(bits)
        if p == q:
            continue
        phi = (p - 1) * (q - 1)
        if extended_gcd(e, phi)[0] != 1:        # e должно быть взаимно просто с phi(n)
            continue
        n = p * q
        d = mod_inverse(e, phi)
        return {"n": n, "e": e}, {"n": n, "d": d, "p": p, "q": q}


def save_key(path, key, kind):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# RSA {kind} key, n = {key['n'].bit_length()} bit\n")
        for name, value in key.items():
            f.write(f"{name} = {value:x}\n")          # числа в шестнадцатеричном виде


def load_key(path):
    key = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                name, value = (s.strip() for s in line.split("=", 1))
                key[name] = int(value, 16)
    return key


# ---------------------------------------------------------------------------
# Шифрование (поблочное: блок открытого текста k-1 байт < n, блок шифртекста k байт)
# ---------------------------------------------------------------------------
def byte_len(n):
    return (n.bit_length() + 7) // 8


def encrypt(data, pub):
    n, e = pub["n"], pub["e"]
    k = byte_len(n)
    block = k - 1
    blocks = []
    for i in range(0, len(data), block):
        m = int.from_bytes(data[i:i + block], "big")      # m < 256^(k-1) <= n
        blocks.append(mod_pow(m, e, n))
    return len(data), blocks


def decrypt(length, blocks, priv):
    n, d = priv["n"], priv["d"]
    k = byte_len(n)
    block = k - 1
    out = bytearray()
    for idx, c in enumerate(blocks):
        m = mod_pow(c, d, n)
        size = min(block, length - idx * block)           # последний блок может быть короче
        out += m.to_bytes(size, "big")
    return bytes(out)


def save_encrypted(path, length, blocks):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"length = {length}\n")
        for c in blocks:
            f.write(f"{c:x}\n")


def load_encrypted(path):
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    length = int(lines[0].split("=")[1])
    return length, [int(l, 16) for l in lines[1:]]


# ---------------------------------------------------------------------------
# Цифровая подпись (подписывается хеш SHA-256 сообщения)
# ---------------------------------------------------------------------------
def message_hash(data, n):
    return int.from_bytes(hashlib.sha256(data).digest(), "big") % n


def sign(data, priv):
    return mod_pow(message_hash(data, priv["n"]), priv["d"], priv["n"])


def verify(data, s, pub):
    return mod_pow(s, pub["e"], pub["n"]) == message_hash(data, pub["n"])


# ---------------------------------------------------------------------------
# Командная строка
# ---------------------------------------------------------------------------
def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def cmd_keygen(a):
    t0 = time.perf_counter()
    pub, priv = generate_keys(a.bits)
    save_key(a.pub, pub, "public")
    save_key(a.priv, priv, "private")
    print(f"Ключи созданы за {time.perf_counter() - t0:.2f} с: n = {pub['n'].bit_length()} бит, "
          f"e = {pub['e']}\n  открытый ключ: {a.pub}\n  секретный ключ: {a.priv}")


def cmd_encrypt(a):
    length, blocks = encrypt(read_bytes(a.inp), load_key(a.pub))
    save_encrypted(a.out, length, blocks)
    print(f"Зашифровано {length} байт в {len(blocks)} блок(ов): {a.out}")


def cmd_decrypt(a):
    length, blocks = load_encrypted(a.inp)
    write_bytes(a.out, decrypt(length, blocks, load_key(a.priv)))
    print(f"Расшифровано {length} байт: {a.out}")


def cmd_sign(a):
    s = sign(read_bytes(a.inp), load_key(a.priv))
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(f"{s:x}\n")
    print(f"Подпись сохранена: {a.out}")


def cmd_verify(a):
    with open(a.sig, encoding="utf-8") as f:
        s = int(f.read().strip(), 16)
    ok = verify(read_bytes(a.inp), s, load_key(a.pub))
    print("Подпись ВЕРНА" if ok else "Подпись НЕВЕРНА")
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------------------
# 10 наборов тестовых данных
# ---------------------------------------------------------------------------
TEST_MESSAGES = [
    ("Короткий текст (латиница)", b"Hello, RSA!"),
    ("Русский текст в UTF-8", "Защита информации: асимметричное шифрование RSA.".encode()),
    ("Один байт 0x00", b"\x00"),
    ("Ведущие нулевые байты", b"\x00\x00\x00\x01\x02 leading zeros"),
    ("Ровно один блок (255 байт)", bytes(range(255))),
    ("Один блок + 1 байт (256 байт)", bytes(range(256))),
    ("Длинный текст, 5 000 байт", ("Лабораторная работа №5. " * 250).encode()[:5000]),
    ("Случайные двоичные данные, 1 024 байта", None),
    ("Все байты 0xFF, 600 байт", b"\xff" * 600),
    ("Сеансовый ключ AES-256 (32 байта)", None),
]


def run_tests(base_dir, bits):
    os.makedirs(base_dir, exist_ok=True)
    rows = []
    for i, (title, msg) in enumerate(TEST_MESSAGES, 1):
        if msg is None:
            msg = secrets.token_bytes(1024 if i == 8 else 32)
        d = os.path.join(base_dir, f"test_{i:02d}")
        os.makedirs(d, exist_ok=True)
        f = {name: os.path.join(d, name) for name in
             ["public.key", "private.key", "message.bin", "encrypted.txt", "decrypted.bin", "signature.txt"]}

        t0 = time.perf_counter()
        pub, priv = generate_keys(bits)
        t_key = time.perf_counter() - t0
        save_key(f["public.key"], pub, "public")
        save_key(f["private.key"], priv, "private")
        write_bytes(f["message.bin"], msg)

        # проверка ключей
        keys_ok = (pub["e"] * priv["d"]) % ((priv["p"] - 1) * (priv["q"] - 1)) == 1 \
            and priv["p"] * priv["q"] == pub["n"]

        # шифрование -> файл -> расшифрование -> файл (всё через файлы)
        t0 = time.perf_counter()
        length, blocks = encrypt(read_bytes(f["message.bin"]), load_key(f["public.key"]))
        t_enc = time.perf_counter() - t0
        save_encrypted(f["encrypted.txt"], length, blocks)
        t0 = time.perf_counter()
        l2, b2 = load_encrypted(f["encrypted.txt"])
        write_bytes(f["decrypted.bin"], decrypt(l2, b2, load_key(f["private.key"])))
        t_dec = time.perf_counter() - t0
        dec_ok = read_bytes(f["decrypted.bin"]) == msg

        # подпись и проверка
        s = sign(msg, load_key(f["private.key"]))
        with open(f["signature.txt"], "w") as fh:
            fh.write(f"{s:x}\n")
        sig_ok = verify(msg, s, load_key(f["public.key"]))
        tampered = bytearray(msg) if msg else bytearray(b"\x00")
        tampered[0] ^= 0x01                                    # изменён 1 бит сообщения
        tamper_detected = not verify(bytes(tampered), s, pub)
        other_pub, _ = generate_keys(256)                      # чужой открытый ключ
        wrong_key_detected = not verify(msg, s, other_pub)

        # самопроверка mod_pow против встроенной pow
        pow_ok = all(mod_pow(c, priv["d"], priv["n"]) == pow(c, priv["d"], priv["n"]) for c in blocks[:2])

        rows.append((i, title, len(msg), len(blocks), t_key, t_enc, t_dec,
                     keys_ok and dec_ok and pow_ok, sig_ok, tamper_detected and wrong_key_detected))
        print(f"Тест {i:2d}: {title:<40} {len(msg):>5} Б, {len(blocks):>2} бл., ключи {t_key:6.2f} с, "
              f"шифр. {t_enc * 1000:7.1f} мс, расшифр. {t_dec * 1000:7.1f} мс | "
              f"расшифровка {'OK' if dec_ok else 'ОШИБКА'}, подпись {'OK' if sig_ok else 'ОШИБКА'}, "
              f"подделка {'обнаружена' if tamper_detected and wrong_key_detected else 'НЕ обнаружена'}")
    passed = sum(1 for r in rows if r[7] and r[8] and r[9])
    print(f"\nПройдено тестов: {passed} из {len(rows)}")

    # сравнение скорости: метод квадрата и умножения против наивного умножения
    n, d = priv["n"], priv["d"]
    print(f"\nКоличество операций для d ({d.bit_length()} бит): "
          f"возведений в квадрат {d.bit_length() - 1}, умножений {bin(d).count('1') - 1}; "
          f"наивный метод потребовал бы ~2^{d.bit_length() - 1} умножений")
    m = secrets.randbelow(n)
    t0 = time.perf_counter()
    for _ in range(20):
        mod_pow(m, d, n)
    t_own = (time.perf_counter() - t0) / 20
    t0 = time.perf_counter()
    for _ in range(20):
        pow(m, d, n)
    t_builtin = (time.perf_counter() - t0) / 20
    print(f"Одна операция с секретным ключом: mod_pow {t_own * 1000:.1f} мс, встроенная pow {t_builtin * 1000:.1f} мс")
    return rows


def main():
    parser = argparse.ArgumentParser(description="ЛР5: RSA — ключи, шифрование, подпись")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("keygen")
    p.add_argument("--bits", type=int, default=1024, help="длина p и q в битах (не менее 1024)")
    p.add_argument("--pub", default="public.key")
    p.add_argument("--priv", default="private.key")
    for name in ("encrypt", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--pub", default="public.key")
        p.add_argument("--in", dest="inp", default="message.txt")
        if name == "encrypt":
            p.add_argument("--out", default="encrypted.txt")
        else:
            p.add_argument("--sig", default="signature.txt")
    for name, default_in, default_out in (("decrypt", "encrypted.txt", "decrypted.txt"),
                                          ("sign", "message.txt", "signature.txt")):
        p = sub.add_parser(name)
        p.add_argument("--priv", default="private.key")
        p.add_argument("--in", dest="inp", default=default_in)
        p.add_argument("--out", default=default_out)
    p = sub.add_parser("test")
    p.add_argument("--bits", type=int, default=1024)
    p.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests"))
    a = parser.parse_args()

    if a.cmd == "keygen" and a.bits < 1024:
        print("Внимание: по заданию длина p и q должна быть не менее 1024 бит")
    {"keygen": cmd_keygen, "encrypt": cmd_encrypt, "decrypt": cmd_decrypt, "sign": cmd_sign,
     "verify": cmd_verify, "test": lambda x: run_tests(x.dir, x.bits)}[a.cmd](a)


if __name__ == "__main__":
    main()
