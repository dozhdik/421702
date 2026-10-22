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
from scipy import ndimage as ndi
from numpy.lib.stride_tricks import sliding_window_view
from PIL import Image

def median_filter(a, size=3):
    if size < 1 or size % 2 == 0:
        raise ValueError('Window must be positive and odd')
    p = np.pad(a, size//2, mode='symmetric')
    w = sliding_window_view(p, (size, size))
    return np.median(w, axis=(-2, -1))

def bilateral(a, radius=3, spatial=2., intensity=30.):
    a = a.astype(float)
    p = np.pad(a, radius, mode='symmetric')
    total, weights = np.zeros_like(a), np.zeros_like(a)
    h, w = a.shape
    for dy in range(-radius, radius+1):
        for dx in range(-radius, radius+1):
            b = p[radius+dy:radius+dy+h,
                  radius+dx:radius+dx+w]
            weight = np.exp(-(dx*dx+dy*dy)/(2*spatial**2)
                            -(b-a)**2/(2*intensity**2))
            total += weight*b
            weights += weight
    return total/weights

def filters(a):
    a = a.astype(float)
    g = ndi.gaussian_filter(a, 1., mode='reflect')
    return {'mean': u8(ndi.uniform_filter(a, 3)),
            'gaussian': u8(g),
            'median': u8(median_filter(a)),
            'bilateral': u8(bilateral(a)),
            'unsharp': u8(a + (a-g))}

def metrics(ref, a):
    mse = float(np.mean((ref.astype(float)-a)**2))
    psnr = float(10*np.log10(255**2/mse)) if mse else None
    return dict(mse=mse, psnr=psnr)

def main(path=None):
    clean = load_gray(path)
    rng = np.random.default_rng(9)
    gaussian = u8(clean + rng.normal(0, 20, clean.shape))
    salt = clean.copy()
    r = rng.random(clean.shape)
    salt[r < .025] = 0
    salt[r > .975] = 255
    result = {}
    labels = ['Средний 3×3', 'Гауссов σ=1', 'Медианный 3×3',
              'Билатеральный', 'Повышение резкости']
    for name, noisy in [('gaussian', gaussian), ('salt', salt)]:
        outputs = filters(noisy)
        expected = ndi.median_filter(noisy, 3, mode='reflect')
        assert np.array_equal(median_filter(noisy), expected)
        result[name] = {'noisy': metrics(clean, noisy)}
        for key, a in outputs.items():
            result[name][key] = metrics(clean, a)
            Image.fromarray(a).save(OUT/f'{name}_{key}.png')
        images = [clean, noisy] + list(outputs.values())
        grid(images, ['Оригинал', 'С шумом']+labels,
             f'filters_{name}.png')
    (OUT/'lab2.json').write_text(json.dumps(result, indent=2))
    print('Лабораторная работа 2. Предварительная обработка изображений')
    noise_names = {'gaussian': 'Гауссов шум', 'salt': 'Шум «соль и перец»'}
    method_names = {'noisy': 'Изображение с шумом',
                    'mean': 'Средний фильтр',
                    'gaussian': 'Гауссов фильтр',
                    'median': 'Медианный фильтр',
                    'bilateral': 'Билатеральный фильтр',
                    'unsharp': 'Повышение резкости'}
    for noise, methods in result.items():
        print(f'\n{noise_names[noise]}')
        print(f"{'Метод':<26} {'MSE':>14} {'PSNR, дБ':>14}")
        for method, values in methods.items():
            psnr = (f"{values['psnr']:.6f}"
                    if values['psnr'] is not None else 'бесконечность')
            print(f"{method_names[method]:<26} "
                  f"{values['mse']:>14.6f} {psnr:>14}")

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)