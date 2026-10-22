"""
Лабораторная работа №3. Режимы применения блочных шифров.

Программа заменяет EModes.exe: шифрует изображения пяти типов алгоритмами AES (блок 128 бит)
и DES (блок 64 бита) в режимах ECB, CBC и CTR и показывает шифртекст как изображение
(заголовок файла не шифруется, шифруются только байты пикселей — как в несжатом BMP).

Типы изображений:
  1) компьютерный рисунок            — генерируется программой (заливки, контуры);
  2) диаграмма                        — строится matplotlib;
  3) текстура                         — skimage.data.brick (кирпичная кладка);
  4) фотография с небольшим кол-вом деталей — skimage.data.rocket (ракета на фоне неба);
  5) фотография с большим кол-вом деталей   — skimage.data.astronaut.
Можно добавить свои изображения: python3 lab3_block_modes.py мой_рисунок.png ...

Для каждого результата считаются метрики:
  - доля повторяющихся блоков шифртекста (утечка структуры в ECB);
  - коэффициент корреляции соседних пикселей по горизонтали;
  - энтропия байтов шифртекста (максимум 8 бит/байт).

Зависимости: pip install pycryptodome pillow numpy matplotlib scikit-image
"""

import os
import sys
from collections import Counter

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from PIL import Image, ImageDraw, ImageFont
from Crypto.Cipher import AES, DES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, "images")
OUT_DIR = os.path.join(BASE, "results")

ALGORITHMS = {"AES": (AES, 16), "DES": (DES, 8)}     # модуль, размер блока в байтах
MODES = ["ECB", "CBC", "CTR"]


# ---------------------------------------------------------------------------
# Подготовка изображений
# ---------------------------------------------------------------------------
def make_computer_drawing(path, size=(512, 384)):
    """Рисунок с большими однотонными областями (как в графическом редакторе)."""
    img = Image.new("RGB", size, (135, 206, 235))                       # небо
    d = ImageDraw.Draw(img)
    d.rectangle([0, 270, size[0], size[1]], fill=(80, 170, 70))          # трава
    d.ellipse([400, 30, 480, 110], fill=(255, 215, 0))                   # солнце
    d.rectangle([110, 160, 300, 300], fill=(200, 60, 50), outline=(0, 0, 0), width=4)    # дом
    d.polygon([(90, 165), (205, 70), (320, 165)], fill=(120, 70, 40), outline=(0, 0, 0))  # крыша
    d.rectangle([150, 200, 200, 245], fill=(255, 255, 255), outline=(0, 0, 0), width=3)  # окно
    d.rectangle([230, 220, 275, 300], fill=(90, 50, 20), outline=(0, 0, 0), width=3)     # дверь
    d.rectangle([370, 190, 385, 290], fill=(100, 60, 30))                # ствол
    d.ellipse([335, 120, 420, 210], fill=(30, 120, 40))                  # крона
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 18)
        d.text((20, 20), "ЛР 3: компьютерный рисунок", fill=(0, 0, 0), font=font)
    except OSError:
        d.text((20, 20), "Lab 3: computer drawing", fill=(0, 0, 0))
    img.save(path)


def make_diagram(path):
    """Столбчатая и круговая диаграммы на белом фоне."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 3.84), dpi=80)
    a1.bar(["Q1", "Q2", "Q3", "Q4"], [23, 41, 35, 52], color=["#4C72B0", "#DD8452", "#55A868", "#C44E52"])
    a1.set_title("Продажи по кварталам")
    a2.pie([45, 30, 25], labels=["A", "B", "C"], colors=["#4C72B0", "#DD8452", "#55A868"])
    a2.set_title("Доли рынка")
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def prepare_images():
    os.makedirs(IMG_DIR, exist_ok=True)
    from skimage import data
    items = [
        ("1_computer_drawing", "Компьютерный рисунок", lambda p: make_computer_drawing(p)),
        ("2_diagram", "Диаграмма", lambda p: make_diagram(p)),
        ("3_texture", "Текстура", lambda p: Image.fromarray(data.brick()).convert("RGB").save(p)),
        ("4_photo_low_detail", "Фото, мало деталей", lambda p: Image.fromarray(data.rocket()).save(p)),
        ("5_photo_high_detail", "Фото, много деталей", lambda p: Image.fromarray(data.astronaut()).save(p)),
    ]
    result = []
    for name, title, maker in items:
        path = os.path.join(IMG_DIR, name + ".png")
        if not os.path.exists(path):
            maker(path)
        result.append((name, title, path))
    return result


# ---------------------------------------------------------------------------
# Шифрование
# ---------------------------------------------------------------------------
def encrypt_bytes(data, algo, mode, key, iv):
    module, block = ALGORITHMS[algo]
    if mode == "ECB":
        cipher = module.new(key, module.MODE_ECB)
        return cipher.encrypt(pad(data, block))
    if mode == "CBC":
        cipher = module.new(key, module.MODE_CBC, iv=iv[:block])
        return cipher.encrypt(pad(data, block))
    if mode == "CTR":
        # nonce — половина блока, вторая половина — счётчик блоков
        cipher = module.new(key, module.MODE_CTR, nonce=iv[:block // 2])
        return cipher.encrypt(data)                          # CTR не требует дополнения
    raise ValueError(mode)


def encrypt_image(arr, algo, mode, key, iv):
    """Шифрует байты пикселей и интерпретирует шифртекст как изображение того же размера."""
    raw = arr.tobytes()
    enc = encrypt_bytes(raw, algo, mode, key, iv)
    return np.frombuffer(enc[:len(raw)], dtype=np.uint8).reshape(arr.shape), enc


def repeated_block_share(enc, block):
    blocks = [enc[i:i + block] for i in range(0, len(enc) - block + 1, block)]
    counts = Counter(blocks)
    repeated = sum(c for c in counts.values() if c > 1)
    return repeated / len(blocks)


def neighbour_correlation(arr):
    g = arr.astype(np.float64).mean(axis=2)
    x, y = g[:, :-1].ravel(), g[:, 1:].ravel()
    if x.std() == 0 or y.std() == 0:
        return 1.0
    return float(np.corrcoef(x, y)[0, 1])


def byte_entropy(b):
    counts = np.bincount(np.frombuffer(b, dtype=np.uint8), minlength=256).astype(np.float64)
    p = counts[counts > 0] / counts.sum()
    return float(-(p * np.log2(p)).sum())


# ---------------------------------------------------------------------------
def process(images):
    os.makedirs(OUT_DIR, exist_ok=True)
    keys = {"AES": get_random_bytes(16), "DES": get_random_bytes(8)}
    iv = get_random_bytes(16)
    print(f"Ключ AES-128: {keys['AES'].hex()}")
    print(f"Ключ DES:     {keys['DES'].hex()}")
    print(f"IV / nonce:   {iv.hex()}\n")

    rows = []
    for name, title, path in images:
        arr = np.array(Image.open(path).convert("RGB"))
        raw = arr.tobytes()
        rows.append((title, "—", "исходное", repeated_block_share(raw, 16), repeated_block_share(raw, 8),
                     neighbour_correlation(arr), byte_entropy(raw)))

        fig = plt.figure(figsize=(16, 6.4))
        gs = GridSpec(2, 4, figure=fig, width_ratios=[1.15, 1, 1, 1])
        ax = fig.add_subplot(gs[:, 0])
        ax.imshow(arr)
        ax.set_title(f"Исходное: {title}\n{arr.shape[1]}×{arr.shape[0]}, 24 бит", fontsize=11)
        ax.axis("off")

        for r, algo in enumerate(ALGORITHMS):
            block = ALGORITHMS[algo][1]
            for c, mode in enumerate(MODES):
                enc_img, enc = encrypt_image(arr, algo, mode, keys[algo], iv)
                Image.fromarray(enc_img).save(os.path.join(OUT_DIR, f"{name}_{algo}_{mode}.png"))
                rep = repeated_block_share(enc, block)
                corr = neighbour_correlation(enc_img)
                ent = byte_entropy(enc[:len(raw)])
                rows.append((title, algo, mode, rep if block == 16 else None, rep if block == 8 else None,
                             corr, ent))
                ax = fig.add_subplot(gs[r, c + 1])
                ax.imshow(enc_img)
                ax.set_title(f"{algo}-{mode}: повт. блоков {rep * 100:.1f}%, корр. {corr:.3f}", fontsize=10)
                ax.axis("off")
        fig.tight_layout()
        out = os.path.join(OUT_DIR, f"{name}_all.png")
        fig.savefig(out, dpi=90)
        plt.close(fig)
        print(f"{title}: {out}")

    # Сравнение размера блока: увеличенный фрагмент компьютерного рисунка в ECB
    arr = np.array(Image.open(images[0][2]).convert("RGB"))
    crop = (slice(150, 214), slice(90, 218))
    fig, axs = plt.subplots(1, 3, figsize=(15, 3.6))
    axs[0].imshow(arr[crop], interpolation="nearest")
    axs[0].set_title("Фрагмент исходного рисунка (крыша и стена дома)")
    for ax, algo in zip(axs[1:], ALGORITHMS):
        enc_img, _ = encrypt_image(arr, algo, "ECB", keys[algo], iv)
        ax.imshow(enc_img[crop], interpolation="nearest")
        block = ALGORITHMS[algo][1]
        ax.set_title(f"{algo}-ECB: блок {block * 8} бит = {block / 3:.2f} пикселя")
    for ax in axs:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "block_size_zoom.png"), dpi=110)
    plt.close(fig)

    print("\nМетрики (повт. блоки AES считаются блоками по 16 байт, DES — по 8 байт):")
    print(f"{'Изображение':<22}{'Алг':<5}{'Режим':<10}{'Повт.16Б':>10}{'Повт.8Б':>10}{'Корр.':>8}{'Энтр.':>7}")
    for t, a, m, r16, r8, corr, ent in rows:
        f16 = f"{r16 * 100:.1f}%" if r16 is not None else ""
        f8 = f"{r8 * 100:.1f}%" if r8 is not None else ""
        print(f"{t:<22}{a:<5}{m:<10}{f16:>10}{f8:>10}{corr:>8.3f}{ent:>7.3f}")


if __name__ == "__main__":
    imgs = prepare_images()
    for extra in sys.argv[1:]:
        imgs.append((os.path.splitext(os.path.basename(extra))[0], os.path.basename(extra), extra))
    process(imgs)
