# -*- coding: utf-8 -*-
"""ЛР 4. Сегментация по затравкам, порогу Оцу и границам Собеля.
Установка: python -m pip install numpy scipy matplotlib Pillow
Запуск: python lab4_segmentation.py
Свой файл: python lab4_segmentation.py photo.png --seed 50 70
Координаты --seed задаются как строка столбец; можно указать несколько.
"""
import argparse
import json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})

def u8(a):
    return np.rint(np.clip(a, 0, 255)).astype(np.uint8)

def scene():
    y, x = np.mgrid[:256, :256]
    clean = 30 + 20*x/255 + 5*np.sin(y/19)
    gt = Image.new('L', (256, 256))
    d = ImageDraw.Draw(gt)
    d.rectangle((20, 25, 105, 110), fill=1)
    d.ellipse((145, 25, 232, 112), fill=2)
    d.polygon([(50, 225), (125, 135), (185, 225)], fill=3)
    gt = np.asarray(gt).copy()
    for label, level in [(1, 150), (2, 205), (3, 175)]:
        clean[gt == label] = level
    rng = np.random.default_rng(9)
    noisy = u8(clean + rng.normal(0, 8, clean.shape))
    return noisy, gt, [(65, 60), (68, 190), (190, 120)]

def otsu(a):
    hist = np.bincount(a.ravel(), minlength=256).astype(float)
    p = hist/a.size
    w = np.cumsum(p)
    m = np.cumsum(p*np.arange(256))
    den = w*(1-w)
    score = np.full(256, -np.inf)
    good = den > 0
    score[good] = (m[-1]*w[good]-m[good])**2/den[good]
    return int(np.argmax(score)) if np.any(good) else int(a.flat[0])

def connected(mask, min_area=40):
    labels, _ = ndi.label(mask, structure=np.ones((3, 3)))
    areas = np.bincount(labels.ravel())
    keep = areas >= min_area
    keep[0] = False
    return ndi.label(keep[labels], structure=np.ones((3, 3)))[0]

def grow(a, seeds, tolerance=35):
    labels = np.zeros(a.shape, dtype=np.int32)
    height, width = a.shape
    for label, (row, col) in enumerate(seeds, 1):
        if not (0 <= row < height and 0 <= col < width):
            raise ValueError('Затравка находится за пределами изображения')
        if labels[row, col]:
            continue
        reference = float(a[row, col])
        labels[row, col] = label
        queue = deque([(row, col)])
        while queue:
            r, c = queue.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == dx == 0:
                        continue
                    nr, nc = r+dy, c+dx
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if labels[nr, nc] != 0:
                        continue
                    if abs(float(a[nr, nc])-reference) <= tolerance:
                        labels[nr, nc] = label
                        queue.append((nr, nc))
    return labels

def overlap(prediction, truth):
    p, t = prediction > 0, truth > 0
    tp = int(np.count_nonzero(p & t))
    fp = int(np.count_nonzero(p & ~t))
    fn = int(np.count_nonzero(~p & t))
    return dict(tp=tp, fp=fp, fn=fn,
                iou=tp/(tp+fp+fn) if tp+fp+fn else 1.,
                dice=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 1.)

def objects(labels):
    result = []
    for label in np.unique(labels):
        if label == 0:
            continue
        r, c = np.nonzero(labels == label)
        result.append(dict(label=int(label), area=int(len(r)),
                           centroid=[float(r.mean()), float(c.mean())],
                           bbox=[int(r.min()), int(c.min()),
                                 int(r.max()+1), int(c.max()+1)]))
    return result

def draw_grid(images, titles, output, colors=None):
    fig, axes = plt.subplots(2, 3, figsize=(10, 6.6))
    for ax, a, title in zip(axes.ravel(), images, titles):
        color = 'gray' if a.ndim == 2 else None
        if colors and title in colors:
            color = colors[title]
        options = dict(vmin=0, vmax=255) if color == 'gray' else {}
        ax.imshow(a, cmap=color, **options)
        ax.set_title(title)
        ax.axis('off')
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', nargs='?')
    parser.add_argument('--seed', nargs=2, type=int, action='append')
    parser.add_argument('--tolerance', type=float, default=35)
    parser.add_argument('--output', type=Path, default=Path('results'))
    args = parser.parse_args()
    if args.tolerance < 0:
        parser.error('Допуск должен быть неотрицательным')
    if args.image:
        with Image.open(args.image) as im:
            image = np.asarray(im.convert('L')).copy()
        truth, seeds = None, args.seed
    else:
        image, truth, seeds = scene()
        seeds = args.seed or seeds
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    smooth = ndi.gaussian_filter(image.astype(float), 1., mode='reflect')
    threshold = otsu(u8(smooth))
    auto = connected(smooth > threshold)
    if seeds is None:
        seeds = []
        for obj in objects(auto):
            distance = ndi.distance_transform_edt(auto == obj['label'])
            seeds.append(tuple(int(x) for x in
                               np.unravel_index(np.argmax(distance), auto.shape)))
    regions = grow(smooth, seeds, args.tolerance)
    gx = ndi.sobel(smooth, axis=1, mode='reflect')/8
    gy = ndi.sobel(smooth, axis=0, mode='reflect')/8
    gradient = np.hypot(gx, gy)
    grad8 = u8(255*gradient/gradient.max()) if gradient.max() else u8(gradient)
    edge_threshold = otsu(grad8)
    edges = grad8 > edge_threshold
    boundary = np.zeros(image.shape, dtype=bool)
    for obj in objects(regions):
        mask = regions == obj['label']
        boundary |= mask & ~ndi.binary_erosion(mask, structure=np.ones((3, 3)))
    overlay = np.repeat(image[..., None], 3, axis=2)
    overlay[boundary] = [255, 40, 40]
    palette = np.array([[0, 0, 0], [40, 160, 230],
                        [240, 150, 40], [70, 190, 90]], dtype=np.uint8)
    colored = palette[regions % len(palette)]
    for r, c in seeds:
        colored[max(0, r-2):r+3, max(0, c-2):c+3] = [255, 255, 255]
    for name, a in [('input', image), ('smooth', u8(smooth)),
                    ('gradient', grad8), ('edges', edges.astype('uint8')*255),
                    ('auto_mask', (auto > 0).astype('uint8')*255),
                    ('region_mask', (regions > 0).astype('uint8')*255),
                    ('regions', colored), ('overlay', overlay)]:
        Image.fromarray(a).save(out/f'{name}.png')
    np.save(out/'labels.npy', regions)
    draw_grid([image, u8(smooth), grad8, edges.astype('uint8')*255,
               colored, overlay],
              ['Исходное изображение', 'Сглаживание σ=1', 'Модуль градиента',
               'Границы Собеля', 'Области и затравки', 'Контуры областей'],
              out/'segmentation.png')
    result = dict(threshold=threshold, edge_threshold=edge_threshold,
                  tolerance=args.tolerance, seeds=seeds,
                  objects=objects(regions), automatic_objects=objects(auto))
    print('Лабораторная работа 4. Сегментация изображений')
    print(f'Порог Оцу: {threshold}; допуск разрастания: {args.tolerance:g}')
    print(f'Найдено областей по затравкам: {len(result["objects"])}')
    print(f'{"Метка":>6} {"Площадь, пикс.":>16} {"Центр (строка, столбец)":>28}')
    for obj in result['objects']:
        r, c = obj['centroid']
        print(f'{obj["label"]:>6} {obj["area"]:>16} {r:>13.2f}, {c:.2f}')
    if truth is not None:
        result['metrics'] = {'seeded': overlap(regions, truth),
                             'otsu': overlap(auto, truth)}
        sensitivity = []
        for tolerance in [10, 20, 30, 35, 40, 60, 100]:
            labels = grow(smooth, seeds, tolerance)
            sensitivity.append(dict(tolerance=tolerance,
                                    count=len(objects(labels)),
                                    **overlap(labels, truth)))
        result['sensitivity'] = sensitivity
        fig, ax = plt.subplots(figsize=(7, 3.5))
        ax.plot([x['tolerance'] for x in sensitivity],
                [x['iou'] for x in sensitivity], 'o-')
        ax.set(xlabel='Допуск яркости', ylabel='IoU', ylim=(0, 1.05))
        ax.grid(alpha=.3)
        fig.tight_layout()
        fig.savefig(out/'sensitivity.png', dpi=160)
        plt.close(fig)
        draw_grid([image, truth*75, (auto > 0).astype('uint8')*255,
                   colored, (regions > 0).astype('uint8')*255,
                   ((regions > 0) != (truth > 0)).astype('uint8')*255],
                  ['Вход', 'Эталонная разметка', 'Маска Оцу',
                   'Метки областей', 'Маска по затравкам', 'Ошибочные пиксели'],
                  out/'comparison.png')
        for method, values in result['metrics'].items():
            print(f'{method}: IoU = {values["iou"]:.6f}; Dice = {values["dice"]:.6f}')
        if not args.seed and args.tolerance == 35:
            assert len(result['objects']) == 3
            assert result['metrics']['seeded']['iou'] > .9
    (out/'lab4.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'Изображения и разметка сохранены: {out}')

if __name__ == '__main__':
    main()
