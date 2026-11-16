"""ЛР 5. Стереопара, красно-циановый анаглиф и блочное стереосопоставление.

python lab5_stereo.py --output results_lab5
python lab5_stereo.py left.png right.png --output results_lab5 --show
python lab5_stereo.py left.png right.png --measure --focal-px 640 --baseline-m 0.12
python lab5_stereo.py --gui

Измерения требуют ректифицированной пары одинакового размера и известной
калибровки. Демонстрационные изображения и их эталон генерируются автоматически.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, uniform_filter


def load_rgb(path: str | Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def gray(image: np.ndarray) -> np.ndarray:
    return np.asarray(image, dtype=np.float32) @ np.array(
        [0.299, 0.587, 0.114], dtype=np.float32
    )


def make_anaglyph(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.shape != right.shape or left.ndim != 3 or left.shape[2] != 3:
        raise ValueError("Требуются два RGB-изображения одинакового размера.")
    result = np.empty_like(left)
    result[:, :, 0] = left[:, :, 0]
    result[:, :, 1:] = right[:, :, 1:]
    return result


def match_blocks(
    reference: np.ndarray,
    other: np.ndarray,
    max_disparity: int = 48,
    block_size: int = 9,
    direction: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """SAD по окнам: reference(x) сопоставляется other(x-direction*d)."""
    if block_size < 3 or block_size % 2 == 0:
        raise ValueError("Размер блока должен быть нечётным и не меньше 3.")
    if reference.shape != other.shape or reference.ndim != 2:
        raise ValueError("Сопоставление требует двух одинаковых полутоновых массивов.")
    height, width = reference.shape
    if max_disparity < 1 or max_disparity + block_size >= width:
        raise ValueError("Диапазон диспаритета слишком велик для ширины изображения.")
    if height < block_size or direction not in (-1, 1):
        raise ValueError("Некорректная высота изображения или направление поиска.")
    radius = block_size // 2
    costs = np.full((max_disparity + 1, height, width), np.inf, np.float32)
    for disparity in range(max_disparity + 1):
        shifted = np.zeros_like(other)
        if disparity == 0:
            shifted[:] = other
        elif direction == 1:
            shifted[:, disparity:] = other[:, :-disparity]
        else:
            shifted[:, :-disparity] = other[:, disparity:]
        difference = np.abs(reference - shifted)
        # Среднее SAD имеет тот же минимум, что и сумма SAD при равных окнах.
        cost = uniform_filter(difference, size=block_size, mode="constant", cval=255)
        start = disparity + radius if direction == 1 else radius
        stop = width - radius if direction == 1 else width - disparity - radius
        costs[disparity, radius:height-radius, start:stop] = cost[
            radius:height-radius, start:stop
        ]
    best = np.argmin(costs, axis=0).astype(np.float32)
    two = np.partition(costs, 1, axis=0)[:2]
    gap = np.zeros(reference.shape, np.float32)
    finite = np.isfinite(two[0]) & np.isfinite(two[1])
    gap[finite] = two[1][finite] - two[0][finite]
    best[~np.isfinite(two[0])] = np.nan
    return best, gap


def estimate_disparity(
    left: np.ndarray, right: np.ndarray, max_disparity: int, block_size: int
) -> tuple[np.ndarray, np.ndarray]:
    left_d, gap = match_blocks(gray(left), gray(right), max_disparity, block_size)
    right_d, _ = match_blocks(gray(right), gray(left), max_disparity, block_size, -1)
    yy, xx = np.indices(left_d.shape)
    right_x = xx - np.nan_to_num(left_d, nan=0).astype(int)
    inside = (right_x >= 0) & (right_x < left_d.shape[1])
    sampled = right_d[yy, np.clip(right_x, 0, left_d.shape[1]-1)]
    valid = inside & np.isfinite(left_d) & (left_d > 0) & (gap > 1.0)
    valid &= np.isfinite(sampled) & (np.abs(left_d - sampled) <= 1.0)
    result = left_d.copy()
    result[~valid] = np.nan
    return result, valid


def make_demo(directory: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    """Три текстурированные фронтопараллельные плоскости с известным d."""
    rng = np.random.default_rng(9)
    height, width = 320, 512
    texture = gaussian_filter(rng.uniform(0, 255, (height, width)), sigma=0.45)
    texture = np.clip(128 + 2.8 * (texture - 128), 0, 255).astype(np.uint8)
    base = np.repeat(texture[:, :, None], 3, axis=2)
    image = Image.fromarray(base)
    draw = ImageDraw.Draw(image)
    draw.rectangle((105, 65, 265, 250), outline=(255, 220, 50), width=4)
    draw.rectangle((320, 100, 445, 230), outline=(40, 230, 240), width=4)
    draw.text((120, 78), "MIDDLE d=16", fill=(255, 255, 255))
    draw.text((332, 112), "NEAR d=32", fill=(255, 255, 255))
    left = np.asarray(image).copy()
    labels = np.zeros((height, width), np.uint8)
    labels[65:251, 105:266] = 1
    labels[100:231, 320:446] = 2
    levels = np.array([8, 16, 32], np.int16)
    truth = levels[labels]
    right = np.zeros_like(left)
    right_labels = np.full(labels.shape, -1, np.int16)
    for label, disparity in enumerate(levels):
        yy, xx = np.where(labels == label)
        keep = xx >= disparity
        yy, xx = yy[keep], xx[keep]
        right[yy, xx-disparity] = left[yy, xx]
        right_labels[yy, xx-disparity] = label
    yy, xx = np.indices(labels.shape)
    target_x = xx - truth
    visible = target_x >= 0
    visible &= right_labels[yy, np.clip(target_x, 0, width-1)] == labels
    Image.fromarray(left).save(directory / "left.png")
    Image.fromarray(right).save(directory / "right.png")
    np.save(directory / "disparity_truth.npy", truth)
    np.save(directory / "visible_truth.npy", visible)
    return left, right, {"truth": truth, "visible": visible, "labels": labels,
                         "focal_px": 640.0, "baseline_m": 0.12}


def process(
    left: np.ndarray, right: np.ndarray, output: Path, measure: bool = False,
    max_disparity: int = 48, block_size: int = 9,
    focal_px: float | None = None, baseline_m: float | None = None,
    demo: dict | None = None, show: bool = False,
) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    anaglyph = make_anaglyph(left, right)
    Image.fromarray(anaglyph).save(output / "anaglyph.png")
    Image.fromarray(np.concatenate((left, right), axis=1)).save(output / "stereo_pair.png")
    summary = {"width": int(left.shape[1]), "height": int(left.shape[0]),
               "anaglyph": "R=left.R, G=right.G, B=right.B"}
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.2), layout="constrained")
    for ax, data, title in zip(axes, [left, right, anaglyph],
                               ["Левый ракурс", "Правый ракурс", "Красно-циановый анаглиф"]):
        ax.imshow(data)
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    fig.savefig(output / "stereo_overview.png", dpi=180)
    if measure:
        if (focal_px is None) != (baseline_m is None):
            raise ValueError("Для глубины задайте и --focal-px, и --baseline-m.")
        if focal_px is not None and (focal_px <= 0 or baseline_m <= 0):
            raise ValueError("Фокусное расстояние и база должны быть положительными.")
        disparity, valid = estimate_disparity(left, right, max_disparity, block_size)
        np.save(output / "disparity.npy", disparity)
        Image.fromarray((valid * 255).astype(np.uint8)).save(output / "valid_mask.png")
        summary.update({"block_size": block_size, "max_disparity": max_disparity,
                        "valid_fraction": float(valid.mean())})
        depth = None
        if focal_px is not None:
            depth = np.full(disparity.shape, np.nan, np.float32)
            depth[valid] = focal_px * baseline_m / disparity[valid]
            np.save(output / "depth_m.npy", depth)
            summary.update({"focal_px": focal_px, "baseline_m": baseline_m})
        plot_count = 3 if demo is not None else (2 if depth is not None else 1)
        fig2, axs = plt.subplots(1, plot_count, figsize=(4.3*plot_count, 3.6),
                                 layout="constrained", squeeze=False)
        panels = [(disparity, "Оценка диспаритета, пиксели", "viridis")]
        if demo is not None:
            panels.insert(0, (demo["truth"], "Эталон диспаритета, пиксели", "viridis"))
        if depth is not None:
            panels.append((depth, "Оценка глубины, м", "magma"))
        for ax, (data, title, cmap) in zip(axs.flat, panels):
            artist = ax.imshow(data, cmap=cmap,
                               vmin=0 if cmap == "viridis" else None,
                               vmax=max_disparity if cmap == "viridis" else None)
            ax.set_title(title, fontsize=11)
            ax.axis("off")
            fig2.colorbar(artist, ax=ax, fraction=0.04)
        fig2.savefig(output / "measurements.png", dpi=170)
        if demo is not None:
            # Эталон определяет только область оценки, а не результат поиска.
            eligible = demo["visible"].copy()
            radius = block_size // 2
            eligible[:radius] = eligible[-radius:] = False
            eligible[:, :max_disparity+radius] = False
            eligible[:, -radius:] = False
            evaluated = eligible & valid
            error = np.abs(disparity[evaluated] - demo["truth"][evaluated])
            summary.update({"eligible_pixels": int(eligible.sum()),
                            "evaluated_pixels": int(evaluated.sum()),
                            "coverage": float(evaluated.sum() / eligible.sum()),
                            "mae_px": float(error.mean()),
                            "bad_1px_fraction": float((error > 1).mean())})
            regions = []
            for label, expected in enumerate([8, 16, 32]):
                mask = evaluated & (demo["labels"] == label)
                regions.append({"region": label, "true_disparity_px": expected,
                                "median_disparity_px": float(np.median(disparity[mask])),
                                "true_depth_m": focal_px*baseline_m/expected,
                                "median_depth_m": float(np.median(depth[mask])),
                                "valid_pixels": int(mask.sum())})
            summary["regions"] = regions
            with (output / "regions.csv").open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(regions[0]))
                writer.writeheader()
                writer.writerows(regions)
    (output / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    print(f"Изображения: {left.shape[1]} × {left.shape[0]} пикселей")
    print("Сохранены стереопара и красно-циановый анаглиф.")
    if "coverage" in summary:
        print(f"Покрытие эталонной области: {summary['coverage']:.2%}")
        print(f"Средняя абсолютная ошибка диспаритета: {summary['mae_px']:.4f} пикс.")
        print(f"Доля ошибок больше 1 пикселя: {summary['bad_1px_fraction']:.2%}")
        for row in summary["regions"]:
            print(f"Область {row['region']}: d={row['median_disparity_px']:.1f} пикс.; "
                  f"Z={row['median_depth_m']:.2f} м")
    print(f"Результаты: {output.resolve()}")
    if show:
        plt.show()
    plt.close("all")
    return summary


def run_gui(output: Path) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from PIL import ImageTk
    root = tk.Tk()
    root.title("ЛР 5 — Стереоскопические изображения")
    paths = [tk.StringVar(), tk.StringVar()]
    preview = tk.Label(root)
    preview.grid(row=4, column=0, columnspan=3, padx=12, pady=12)
    for index, title in enumerate(["Левый ракурс", "Правый ракурс"]):
        tk.Label(root, text=title).grid(row=index, column=0, padx=8, pady=8)
        tk.Entry(root, textvariable=paths[index], width=55).grid(row=index, column=1)
        def choose(i=index):
            filename = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.tif")])
            if filename:
                paths[i].set(filename)
        tk.Button(root, text="Выбрать", command=choose).grid(row=index, column=2, padx=8)
    def build():
        try:
            left, right = (load_rgb(path.get()) for path in paths)
            process(left, right, output)
            image = Image.fromarray(make_anaglyph(left, right))
            image.thumbnail((900, 550))
            photo = ImageTk.PhotoImage(image)
            preview.configure(image=photo)
            preview.image = photo
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка", str(error))
    tk.Button(root, text="Построить и сохранить анаглиф", command=build).grid(
        row=2, column=0, columnspan=3, pady=10)
    tk.Label(root, text="Для объёмного просмотра: красный фильтр слева, циановый справа.").grid(
        row=3, column=0, columnspan=3)
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("left", nargs="?")
    parser.add_argument("right", nargs="?")
    parser.add_argument("--output", type=Path, default=Path("results_lab5"))
    parser.add_argument("--measure", action="store_true", help="Только для ректифицированной пары")
    parser.add_argument("--max-disparity", type=int, default=48)
    parser.add_argument("--block-size", type=int, default=9)
    parser.add_argument("--focal-px", type=float)
    parser.add_argument("--baseline-m", type=float)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()
    if args.gui:
        run_gui(args.output)
        return 0
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        demo = None
        if args.left is None and args.right is None:
            left, right, demo = make_demo(args.output)
            args.measure = True
            args.focal_px, args.baseline_m = demo["focal_px"], demo["baseline_m"]
        elif args.left is None or args.right is None:
            raise ValueError("Укажите оба изображения или не указывайте ни одного для демонстрации.")
        else:
            left, right = load_rgb(args.left), load_rgb(args.right)
        process(left, right, args.output, args.measure, args.max_disparity,
                args.block_size, args.focal_px, args.baseline_m, demo, args.show)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
