"""ЛР №6, вариант 2: обнаружить красный мяч и заменить его другим предметом.

Демо: python lab6_replace.py
Своё фото: python lab6_replace.py --input photo.jpg --replacement object.png
Проверка: python lab6_replace.py --synthetic --output results_control
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import cv2
import numpy as np

HUE_RANGES = {
    "red": ((0, 11), (170, 179)), "orange": ((12, 22),),
    "yellow": ((23, 37),), "green": ((38, 88),),
    "blue": ((101, 130),),
}


def read_image(path: Path, flags: int = cv2.IMREAD_COLOR) -> np.ndarray:
    if not path.exists():
        raise ValueError(f"Файл не найден: {path}")
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), flags)
    if image is None:
        raise ValueError(f"Не удалось прочитать изображение: {path}")
    return image


def save(path: Path, image: np.ndarray) -> None:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise ValueError(f"Не удалось сохранить: {path}")
    encoded.tofile(str(path))


def synthetic_scene() -> tuple[np.ndarray, np.ndarray]:
    """Контрольный кадр; его истинная маска не поступает в детектор."""
    h, w = 640, 960
    image = np.full((h, w, 3), (215, 205, 191), np.uint8)
    cv2.rectangle(image, (367, 135), (590, 535), (90, 83, 72), -1)
    cv2.circle(image, (478, 95), 58, (130, 180, 212), -1)
    cv2.ellipse(image, (680, 414), (125, 26), 0, 0, 180, (127, 176, 211), -1)
    # Квадрат того же красного цвета проверяет отбор по круглости.
    cv2.rectangle(image, (95, 280), (185, 370), (25, 27, 230), -1)
    truth = np.zeros((h, w), np.uint8)
    cv2.circle(truth, (680, 344), 53, 255, -1)
    image[truth > 0] = (25, 27, 230)
    return image, truth


def candidates_from_color(image: np.ndarray, color: str, saturation: int,
                          min_area: int, roi: tuple[int, int, int, int] | None
                          ) -> tuple[np.ndarray, list[dict]]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    raw = np.zeros(image.shape[:2], np.uint8)
    for low, high in HUE_RANGES[color]:
        raw |= cv2.inRange(hsv, (low, saturation, 35), (high, 255, 255))
    if roi:
        x, y, w, h = roi
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > image.shape[1] or y+h > image.shape[0]:
            raise ValueError("--roi должен лежать в пределах изображения")
        zone = np.zeros_like(raw)
        zone[y:y+h, x:x+w] = 255
        raw &= zone
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    clean = cv2.morphologyEx(raw, cv2.MORPH_OPEN, kernel)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    found = []
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        x, y, w, h = cv2.boundingRect(contour)
        if area < min_area or perimeter == 0:
            continue
        circularity = 4 * np.pi * area / perimeter**2
        aspect = min(w, h) / max(w, h)
        fill = area / (w*h)
        if circularity < .72 or aspect < .72 or not .55 <= fill <= .90:
            continue
        found.append({"contour": contour, "area": area, "circularity": circularity,
                      "bbox": (x, y, w, h), "score": area * circularity * aspect})
    return clean, found


def find_ball(image: np.ndarray, color: str, saturation: int, min_area: int,
              roi: tuple[int, int, int, int] | None
              ) -> tuple[np.ndarray, dict, list[dict]]:
    _, found = candidates_from_color(image, color, saturation, min_area, roi)
    if not found:
        raise ValueError("Круглый предмет выбранного цвета не найден. Проверьте --color, --roi и --saturation.")
    chosen = max(found, key=lambda item: item["score"])
    mask = np.zeros(image.shape[:2], np.uint8)
    cv2.drawContours(mask, [chosen["contour"]], -1, 255, cv2.FILLED)
    return mask, chosen, found


def crop_alpha(asset: np.ndarray) -> np.ndarray:
    if asset.ndim != 3 or asset.shape[2] != 4:
        raise ValueError("Изображение замены должно быть PNG с прозрачным фоном (RGBA)")
    alpha = asset[..., 3]
    points = cv2.findNonZero((alpha > 8).astype(np.uint8))
    if points is None:
        raise ValueError("Изображение замены полностью прозрачное")
    x, y, w, h = cv2.boundingRect(points)
    return asset[y:y+h, x:x+w]


def composite_at(image: np.ndarray, asset: np.ndarray, bbox: tuple[int, int, int, int],
                 scale: float, vertical_offset: float) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    x, y, w, h = bbox
    asset = crop_alpha(asset)
    target_h = max(1, round(max(w, h) * scale))
    target_w = max(1, round(asset.shape[1] * target_h / asset.shape[0]))
    asset = cv2.resize(asset, (target_w, target_h), interpolation=cv2.INTER_AREA)
    # Нижняя грань нового предмета располагается у основания мяча.
    left = round(x+w/2-target_w/2)
    top = round(y+h+vertical_offset*h-target_h)
    x1, y1 = max(0, left), max(0, top)
    x2, y2 = min(image.shape[1], left+target_w), min(image.shape[0], top+target_h)
    if x1 >= x2 or y1 >= y2:
        raise ValueError("Изображение замены выходит за пределы кадра")
    cut = asset[y1-top:y2-top, x1-left:x2-left]
    alpha = cut[..., 3:4].astype(np.float32)/255
    result = image.copy()
    background = result[y1:y2, x1:x2].astype(np.float32)
    result[y1:y2, x1:x2] = np.clip(cut[..., :3]*alpha + background*(1-alpha), 0, 255).astype(np.uint8)
    return result, (left, top, target_w, target_h)


def contact_shadow(image: np.ndarray, bbox: tuple[int, int, int, int],
                   strength: float) -> np.ndarray:
    if strength == 0:
        return image.copy()
    x, y, w, h = bbox
    shadow = np.zeros(image.shape[:2], np.uint8)
    center = (round(x+w/2), round(y+h*.99))
    cv2.ellipse(shadow, center, (round(w*.43), max(3, round(h*.035))),
                0, 0, 360, 255, -1)
    shadow = cv2.GaussianBlur(shadow, (0, 0), max(3, h*.065)).astype(np.float32)/255
    factor = 1-strength*shadow[..., None]
    return np.clip(image.astype(np.float32)*factor, 0, 255).astype(np.uint8)


def annotated(image: np.ndarray, chosen: dict, candidates: list[dict]) -> np.ndarray:
    result = image.copy()
    for item in candidates:
        x, y, w, h = item["bbox"]
        color = (0, 220, 0) if item is chosen else (0, 180, 255)
        cv2.rectangle(result, (x, y), (x+w-1, y+h-1), color, 3)
    return result


def closeup(image: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = bbox
    pad = round(max(w, h)*.8)
    x1, y1, x2, y2 = max(0, x-pad), max(0, y-pad), min(image.shape[1], x+w+pad), min(image.shape[0], y+h+pad)
    left = annotated(image, {"bbox": bbox}, [{"bbox": bbox}])[y1:y2, x1:x2]
    right = cv2.cvtColor(mask[y1:y2, x1:x2], cv2.COLOR_GRAY2BGR)
    return np.concatenate([left, right], axis=1)


def iou(a: np.ndarray, b: np.ndarray) -> float:
    aa, bb = a > 0, b > 0
    return float(np.count_nonzero(aa & bb)/np.count_nonzero(aa | bb))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", type=Path, help="Входная фотография")
    p.add_argument("--replacement", type=Path, help="Прозрачный PNG другого объекта")
    p.add_argument("--output", type=Path, default=Path("results_lab6_variant2"))
    p.add_argument("--synthetic", action="store_true", help="Контрольная сцена с эталонной маской")
    p.add_argument("--color", choices=HUE_RANGES, default="red")
    p.add_argument("--saturation", type=int, default=215)
    p.add_argument("--min-area", type=int, default=500)
    p.add_argument("--roi", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    p.add_argument("--scale", type=float, default=1.15, help="Высота замены относительно диаметра мяча")
    p.add_argument("--vertical-offset", type=float, default=0.0, help="Смещение нижней грани в долях диаметра")
    p.add_argument("--shadow", type=float, default=.32, help="Интенсивность контактной тени 0..1")
    a = p.parse_args()
    if a.synthetic and a.input:
        p.error("--synthetic и --input взаимоисключающие")
    if not 0 <= a.saturation <= 255 or a.min_area < 1 or a.scale <= 0 or not 0 <= a.shadow <= 1:
        p.error("Неверные saturation, min-area, scale или shadow")
    return a


def main() -> None:
    a = parse_args()
    if a.synthetic:
        image, truth = synthetic_scene()
        source = "синтетическая контрольная сцена"
    else:
        source_path = a.input or Path(__file__).with_name("demo_photo.png")
        image, truth = read_image(source_path), None
        source = str(source_path)
    mask, chosen, candidates = find_ball(image, a.color, a.saturation,
                                          a.min_area, tuple(a.roi) if a.roi else None)
    # Восстанавливаем скрытый мячом фон только приближённо.
    dilated = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    background = cv2.inpaint(image, dilated, 5, cv2.INPAINT_TELEA)
    background_with_shadow = contact_shadow(background, chosen["bbox"], a.shadow)
    replacement_path = a.replacement or Path(__file__).with_name("blue_cube.png")
    asset = read_image(replacement_path, cv2.IMREAD_UNCHANGED)
    result, placement = composite_at(background_with_shadow, asset, chosen["bbox"],
                                      a.scale, a.vertical_offset)
    out = a.output
    out.mkdir(parents=True, exist_ok=True)
    tiles = [cv2.resize(frame, (720, 480), interpolation=cv2.INTER_AREA)
             for frame in (image, annotated(image, chosen, candidates),
                           cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), result)]
    frames = {"source.png": image, "detected.png": annotated(image, chosen, candidates),
              "mask.png": mask, "mask_closeup.png": closeup(image, mask, chosen["bbox"]),
              "inpainted.png": background, "replaced.png": result,
              "comparison.png": np.concatenate([np.concatenate(tiles[:2], axis=1),
                                                 np.concatenate(tiles[2:], axis=1)], axis=0)}
    for name, frame in frames.items():
        save(out / name, frame)
    with (out / "detections.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "width", "height", "area_px2", "circularity", "selected"])
        for item in sorted(candidates, key=lambda v: -v["score"]):
            writer.writerow([*item["bbox"], round(item["area"], 1),
                             round(item["circularity"], 3), item is chosen])
    x, y, w, h = chosen["bbox"]
    lines = [f"Источник: {source}", f"Изображение: {image.shape[1]} × {image.shape[0]} пикселей",
             f"Кандидатов: {len(candidates)}; мяч: x={x}, y={y}, размер={w} × {h}",
             f"Площадь: {chosen['area']:.0f} пикселей; круглость: {chosen['circularity']:.3f}",
             f"Куб: x={placement[0]}, y={placement[1]}, размер={placement[2]} × {placement[3]}",
             f"IoU маски с эталоном: {iou(mask, truth):.3f}" if truth is not None
             else "IoU: нет эталонной разметки для демонстрационного кадра"]
    (out/"results.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print("\n".join(lines[1:]))
    print(f"Результаты: {out.resolve()}")


if __name__ == "__main__":
    main()
