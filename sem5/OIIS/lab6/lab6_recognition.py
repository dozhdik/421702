"""ЛР 6. Поиск заданного условного знака на растровой карте по шаблону.

python lab6_recognition.py --output results_lab6
python lab6_recognition.py map.png template.png --threshold 0.82 --show

Метод: собственная нормированная корреляция, перебор масштабов/поворотов,
локальные максимумы и подавление перекрывающихся обнаружений (NMS).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import maximum_filter
from scipy.signal import fftconvolve


def load_rgb(path: str | Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def gray(image: np.ndarray) -> np.ndarray:
    return np.asarray(image, dtype=np.float64) @ np.array([0.299, 0.587, 0.114])


def normalized_correlation(image: np.ndarray, template: np.ndarray) -> np.ndarray:
    """ZNCC: центрирование шаблона и каждого окна, диапазон [-1, 1]."""
    height, width = template.shape
    if height > image.shape[0] or width > image.shape[1]:
        raise ValueError("Шаблон не должен быть больше изображения.")
    centered = template - template.mean()
    energy = np.sum(centered**2)
    if energy < 1e-8:
        raise ValueError("Постоянный шаблон не содержит различимого рисунка.")
    kernel = np.ones((height, width), np.float64)
    sums = fftconvolve(image, kernel, mode="valid")
    squares = fftconvolve(image**2, kernel, mode="valid")
    variance_sum = np.maximum(squares - sums**2 / template.size, 0)
    numerator = fftconvolve(image, centered[::-1, ::-1], mode="valid")
    denominator = np.sqrt(variance_sum * energy)
    score = np.zeros(numerator.shape, np.float64)
    np.divide(numerator, denominator, out=score, where=denominator > 1e-8)
    return np.clip(score, -1, 1)


def transform_template(template: np.ndarray, scale: float, angle: int) -> np.ndarray:
    if scale <= 0 or angle % 90:
        raise ValueError("Масштаб должен быть положительным, поворот кратным 90 градусам.")
    image = Image.fromarray(template)
    size = (max(3, round(image.width*scale)), max(3, round(image.height*scale)))
    resized = np.asarray(image.resize(size, Image.Resampling.BICUBIC))
    return np.rot90(resized, angle//90).copy()


def intersection_over_union(first: dict, second: dict) -> float:
    x0, y0 = max(first["x"], second["x"]), max(first["y"], second["y"])
    x1 = min(first["x"]+first["width"], second["x"]+second["width"])
    y1 = min(first["y"]+first["height"], second["y"]+second["height"])
    intersection = max(0, x1-x0) * max(0, y1-y0)
    union = first["width"]*first["height"] + second["width"]*second["height"] - intersection
    return intersection / union if union else 0.0


def suppress_overlaps(candidates: list[dict], threshold: float = 0.3) -> list[dict]:
    selected = []
    for candidate in sorted(candidates, key=lambda item: item["score"], reverse=True):
        if all(intersection_over_union(candidate, other) <= threshold for other in selected):
            selected.append(candidate)
    return selected


def detect(
    image: np.ndarray, template: np.ndarray, threshold: float = 0.82,
    scales: tuple[float, ...] = (0.8, 1.0, 1.2),
    angles: tuple[int, ...] = (0, 90, 180, 270), nms_iou: float = 0.3,
) -> tuple[list[dict], np.ndarray, list[dict]]:
    if not -1 <= threshold <= 1 or not 0 <= nms_iou <= 1:
        raise ValueError("Некорректный порог корреляции или IoU.")
    source_gray = gray(image)
    candidates = []
    reference_score = None
    for scale in scales:
        for angle in angles:
            transformed = transform_template(template, scale, angle)
            height, width = transformed.shape[:2]
            if height > image.shape[0] or width > image.shape[1]:
                continue
            score = normalized_correlation(source_gray, gray(transformed))
            if reference_score is None or (scale == 1.0 and angle == 0):
                reference_score = score
            peaks = maximum_filter(score, size=7, mode="constant", cval=-2)
            yy, xx = np.where((score >= threshold) & (score == peaks))
            for y, x in zip(yy, xx):
                candidates.append({"x": int(x), "y": int(y), "width": width,
                                   "height": height, "score": float(score[y, x]),
                                   "scale": scale, "angle_deg": angle})
    if reference_score is None:
        raise ValueError("Ни один вариант шаблона не помещается в изображении.")
    return suppress_overlaps(candidates, nms_iou), reference_score, candidates


def make_demo(directory: Path) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    width, height = 800, 560
    image = Image.new("RGB", (width, height), (237, 232, 215))
    draw = ImageDraw.Draw(image)
    rng = np.random.default_rng(9)
    draw.polygon([(0, 390), (210, 350), (430, 430), (800, 365), (800, 430),
                  (430, 495), (210, 405), (0, 450)], fill=(148, 196, 220))
    draw.rectangle((585, 25, 775, 160), fill=(176, 205, 154))
    for x in [45, 175, 310, 460, 595, 755]:
        draw.line((x, 0, x, height), fill=(180, 177, 166), width=19)
        draw.line((x, 0, x, height), fill=(250, 248, 237), width=13)
    for y in [55, 175, 300, 510]:
        draw.line((0, y, width, y), fill=(180, 177, 166), width=19)
        draw.line((0, y, width, y), fill=(250, 248, 237), width=13)
    # Отвлекающие знаки: здания, деревья, парковки и круги с крестом.
    for x, y in [(225, 70), (355, 205), (500, 60), (80, 205), (630, 330), (200, 455)]:
        draw.rectangle((x, y, x+43, y+30), fill=(181, 170, 151), outline=(85, 85, 80), width=2)
        draw.line((x, y, x+43, y+30), fill=(130, 120, 105), width=2)
    for x, y in [(620, 70), (665, 115), (700, 60), (735, 120)]:
        draw.ellipse((x-12, y-12, x+12, y+12), fill=(70, 135, 70))
    for x, y in [(255, 245), (520, 220), (680, 470)]:
        draw.rectangle((x, y, x+30, y+30), fill=(40, 105, 190))
        draw.text((x+9, y+8), "P", fill="white")
    for x, y in [(110, 460), (410, 330)]:
        draw.ellipse((x, y, x+30, y+30), fill="white", outline=(70, 70, 70), width=2)
        draw.line((x+15, y+5, x+15, y+25), fill=(190, 45, 45), width=5)
        draw.line((x+5, y+15, x+25, y+15), fill=(190, 45, 45), width=5)
    draw.text((600, 32), "PARK", fill=(45, 90, 45))
    draw.text((335, 447), "RIVER", fill=(35, 85, 120))
    icon = Image.new("RGB", (35, 35), (245, 243, 233))
    painter = ImageDraw.Draw(icon)
    painter.rectangle((1, 1, 33, 33), fill=(252, 252, 250), outline=(45, 65, 80), width=2)
    painter.rectangle((14, 5, 20, 23), fill=(210, 35, 45))
    painter.rectangle((8, 11, 26, 17), fill=(210, 35, 45))
    for x in [7, 15, 23]:
        painter.rectangle((x, 27, x+4, 30), fill=(55, 125, 190))
    template = np.asarray(icon)
    placements = [(90, 90, 1.0, 0), (360, 92, 0.8, 90),
                  (640, 210, 1.2, 180), (220, 320, 1.0, 270),
                  (485, 450, 1.2, 0), (700, 465, 0.8, 180)]
    truth = []
    for x, y, scale, angle in placements:
        transformed = transform_template(template, scale, angle)
        image.paste(Image.fromarray(transformed), (x, y))
        truth.append({"x": x, "y": y, "width": transformed.shape[1],
                      "height": transformed.shape[0], "scale": scale, "angle_deg": angle})
    array = np.asarray(image).astype(np.float64)
    array = np.clip(np.rint(array*0.94 + 7 + rng.normal(0, 3, array.shape)), 0, 255).astype(np.uint8)
    Image.fromarray(array).save(directory / "map.png")
    Image.fromarray(template).save(directory / "template.png")
    (directory / "ground_truth.json").write_text(json.dumps(truth, indent=2), encoding="utf-8")
    return array, template, truth


def evaluate(detections: list[dict], truth: list[dict], iou_threshold: float = 0.5) -> dict:
    matched = set()
    true_positive = 0
    for detection in sorted(detections, key=lambda item: item["score"], reverse=True):
        choices = [(intersection_over_union(detection, target), index)
                   for index, target in enumerate(truth) if index not in matched]
        overlap, index = max(choices, default=(0, -1))
        if overlap >= iou_threshold:
            matched.add(index)
            true_positive += 1
    false_positive, false_negative = len(detections)-true_positive, len(truth)-true_positive
    precision = true_positive/len(detections) if detections else 0.0
    recall = true_positive/len(truth) if truth else 0.0
    return {"tp": true_positive, "fp": false_positive, "fn": false_negative,
            "precision": precision, "recall": recall,
            "f1": 2*precision*recall/(precision+recall) if precision+recall else 0.0,
            "matching_iou": iou_threshold}


def process(image: np.ndarray, template: np.ndarray, output: Path,
            threshold: float = 0.82, scales: tuple = (0.8, 1.0, 1.2),
            angles: tuple = (0, 90, 180, 270), truth: list[dict] | None = None,
            show: bool = False) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    detections, score, candidates = detect(image, template, threshold, scales, angles)
    annotated = Image.fromarray(image.copy())
    draw = ImageDraw.Draw(annotated)
    for index, item in enumerate(detections, 1):
        x, y, width, height = (item[key] for key in ["x", "y", "width", "height"])
        draw.rectangle((x, y, x+width-1, y+height-1), outline=(220, 20, 20), width=3)
        draw.text((x, max(0, y-13)), f"{index}: {item['score']:.3f}", fill=(140, 0, 0))
    annotated.save(output / "detections.png")
    np.save(output / "correlation.npy", score)
    summary = {"width": image.shape[1], "height": image.shape[0],
               "threshold": threshold, "scales": scales, "angles_deg": angles,
               "candidate_count": len(candidates), "detection_count": len(detections),
               "detections": detections}
    if truth is not None:
        summary["metrics"] = evaluate(detections, truth)
        sweep = []
        for value in [0.45, 0.65, 0.82, 0.97, 0.99965, 0.9999]:
            found, _, _ = detect(image, template, value, scales, angles)
            sweep.append({"threshold": value, **evaluate(found, truth)})
        summary["threshold_sweep"] = sweep
        single, _, _ = detect(image, template, threshold, (1.0,), (0,))
        summary["single_template_metrics"] = evaluate(single, truth)
    columns = ["x", "y", "width", "height", "score", "scale", "angle_deg"]
    with (output / "detections.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(detections)
    (output / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    axes[0].imshow(image)
    axes[0].set_title("Исходная учебная карта")
    axes[1].imshow(annotated)
    axes[1].set_title(f"Найдено объектов: {len(detections)}")
    for ax in axes:
        ax.axis("off")
    fig.savefig(output / "recognition_overview.png", dpi=170)
    fig2, axes2 = plt.subplots(1, 2, figsize=(10, 4), layout="constrained",
                               gridspec_kw={"width_ratios": [1, 4]})
    axes2[0].imshow(template, interpolation="nearest")
    axes2[0].set_title("Шаблон")
    axes2[0].axis("off")
    artist = axes2[1].imshow(score, cmap="magma", vmin=-1, vmax=1)
    axes2[1].set_title("Корреляция для масштаба 1 и поворота 0°")
    axes2[1].set_xlabel("x верхнего левого угла окна")
    axes2[1].set_ylabel("y")
    fig2.colorbar(artist, ax=axes2[1], fraction=0.035)
    fig2.savefig(output / "correlation.png", dpi=170)
    print(f"Размер карты: {image.shape[1]} × {image.shape[0]}")
    print(f"Кандидатов до NMS: {len(candidates)}; объектов после NMS: {len(detections)}")
    print(" №    x    y    ширина высота  корреляция масштаб поворот")
    for index, item in enumerate(detections, 1):
        print(f"{index:2} {item['x']:4} {item['y']:4} {item['width']:7} {item['height']:6} "
              f"{item['score']:11.4f} {item['scale']:7.1f} {item['angle_deg']:6}")
    if truth is not None:
        print("Оценка:", "; ".join(f"{key}={value:.3f}" for key, value in summary["metrics"].items()))
    print(f"Результаты: {output.resolve()}")
    if show:
        plt.show()
    plt.close("all")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", nargs="?")
    parser.add_argument("template", nargs="?")
    parser.add_argument("--output", type=Path, default=Path("results_lab6"))
    parser.add_argument("--threshold", type=float, default=0.82)
    parser.add_argument("--scales", type=float, nargs="+", default=[0.8, 1.0, 1.2])
    parser.add_argument("--angles", type=int, nargs="+", default=[0, 90, 180, 270])
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        if args.image is None and args.template is None:
            image, template, truth = make_demo(args.output)
        elif args.image is None or args.template is None:
            raise ValueError("Укажите и карту, и шаблон либо запустите демонстрацию без аргументов.")
        else:
            image, template = load_rgb(args.image), load_rgb(args.template)
            truth = None
        process(image, template, args.output, args.threshold, tuple(args.scales),
                tuple(args.angles), truth, args.show)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
