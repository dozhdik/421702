# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path('results')
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans',
                     'font.size': 10, 'figure.dpi': 150})

def u8(a):
    return np.rint(np.clip(a, 0, 255)).astype(np.uint8)

def test_image():
    y, x = np.mgrid[:256, :256]
    a = 35 + 150*x/255 + 12*np.sin(y/8)
    im = Image.fromarray(u8(a))
    d = ImageDraw.Draw(im)
    d.rectangle((18, 24, 108, 110), fill=55, outline=240,
                width=3)
    d.ellipse((139, 22, 232, 115), fill=215, outline=20,
              width=3)
    d.polygon([(28, 211), (79, 130), (126, 211)], fill=170)
    for k in range(8):
        d.rectangle((143+10*k, 144, 147+10*k, 220), fill=25)
    d.line((12, 238, 243, 238), fill=250, width=2)
    return np.asarray(im).copy()

def load_gray(path=None):
    if path is None:
        return test_image()
    with Image.open(path) as im:
        return np.asarray(im.convert('L')).copy()

def grid(images, titles, path, cols=3):
    rows = (len(images)+cols-1)//cols
    fig, axes = plt.subplots(rows, cols,
                             figsize=(3*cols, 3*rows))
    for ax, a, title in zip(np.ravel(axes), images, titles):
        ax.imshow(a, cmap='gray', vmin=0, vmax=255)
        ax.set_title(title)
        ax.axis('off')
    for ax in np.ravel(axes)[len(images):]:
        ax.axis('off')
    fig.tight_layout()
    fig.savefig(OUT/path, bbox_inches='tight')
    plt.close(fig)


import sys
import json
import numpy as np
from PIL import Image

def equalize(a):
    hist = np.bincount(a.ravel(), minlength=256)
    cdf = hist.cumsum()
    occupied = np.flatnonzero(hist)
    if len(occupied) <= 1:
        return a.copy()
    first = cdf[occupied[0]]
    lut = u8(255*(cdf-first)/(a.size-first))
    return lut[a]

def match_mean(a, target=128.):
    if not 0 <= target <= 255:
        raise ValueError('Target must be in [0, 255]')
    x = a.astype(float)
    lo, hi = -255., 255.
    for _ in range(60):
        shift = (lo+hi)/2
        if np.clip(x+shift, 0, 255).mean() < target:
            lo = shift
        else:
            hi = shift
    return u8(x+(lo+hi)/2)

def stats(a):
    h = np.bincount(a.ravel(), minlength=256)/a.size
    p = h[h > 0]
    return dict(mean=float(a.mean()), std=float(a.std()),
                min=int(a.min()), max=int(a.max()),
                entropy=float(-np.sum(p*np.log2(p))))

def main(paths=None):
    if paths:
        a, b = map(load_gray, paths)
    else:
        base = load_gray().astype(float)
        a, b = u8(0.45*base+10), u8(0.55*base+100)
    images, labels, result = [], [], {}
    fig, axes = plt.subplots(2, 3, figsize=(10, 5))
    for row, (name, x) in enumerate([('A', a), ('B', b)]):
        stages = [x, match_mean(x), match_mean(equalize(x))]
        titles = ['До обработки', 'Средняя яркость 128',
                  'Эквализация и яркость 128']
        result[name] = {}
        for col, (title, y) in enumerate(zip(titles, stages)):
            result[name][str(col)] = stats(y)
            images.append(y)
            labels.append(f'{name}: {title}')
            Image.fromarray(y).save(OUT/f'brightness_{name}_{col}.png')
            axes[row, col].hist(y.ravel(), bins=256,
                                range=(0, 256), color='#315d7c')
            axes[row, col].set(title=f'{name}: этап {col}',
                               xlim=(0, 255), xlabel='Яркость')
            if col:
                assert abs(y.mean()-128) <= .5+1e-9
    fig.tight_layout()
    fig.savefig(OUT/'histograms.png')
    plt.close(fig)
    grid(images, labels, 'brightness.png')
    flat = np.full((8, 8), 50, dtype=np.uint8)
    assert np.array_equal(equalize(flat), flat)
    (OUT/'lab3.json').write_text(json.dumps(result, indent=2))
    print('Лабораторная работа 3. Выравнивание яркости и контраста')
    stage_names = {'0': 'До обработки',
                   '1': 'Сдвиг яркости к 128',
                   '2': 'Эквализация и сдвиг к 128'}
    for name, stages in result.items():
        print(f'\nИзображение {name}')
        print(f"{'Этап обработки':<28} {'Среднее':>10} {'СКО':>10} "
              f"{'Мин.':>5} {'Макс.':>6} {'Энтропия':>10}")
        for stage, values in stages.items():
            print(f"{stage_names[stage]:<28} {values['mean']:>10.6f} "
                  f"{values['std']:>10.6f} {values['min']:>5} "
                  f"{values['max']:>6} {values['entropy']:>10.6f}")

if __name__ == '__main__':
    if len(sys.argv) not in (1, 3):
        raise SystemExit('Usage: python lab3.py [image1 image2]')
    main(sys.argv[1:] or None)
