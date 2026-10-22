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



import json
import numpy as np

def fft(x):
    x = np.asarray(x, dtype=complex)
    n = x.size
    if x.ndim != 1 or n == 0 or n & (n-1):
        raise ValueError('Length must be a power of two')
    if n == 1:
        return x.copy()
    even, odd = fft(x[::2]), fft(x[1::2])
    w = np.exp(-2j*np.pi*np.arange(n//2)/n)
    return np.concatenate((even+w*odd, even-w*odd))

def ifft(x):
    x = np.asarray(x, dtype=complex)
    return np.conj(fft(np.conj(x)))/len(x)

def dft(x):
    n = len(x)
    k = np.arange(n)
    return np.exp(-2j*np.pi*np.outer(k, k)/n) @ x

def main():
    n, fs = 1024, 1024
    t = np.arange(n)/fs
    cases = [('sin 5', np.sin(2*np.pi*5*t)),
             ('sin 17', np.sin(2*np.pi*17*t)),
             ('cos 80', np.cos(2*np.pi*80*t)),
             ('sum', np.sin(2*np.pi*5*t)
              + 0.6*np.cos(2*np.pi*17*t)
              + 0.3*np.sin(2*np.pi*80*t))]
    rows = []
    fig, axes = plt.subplots(4, 2, figsize=(10, 9))
    for i, (name, x) in enumerate(cases):
        X = fft(x)
        a = np.abs(X[:n//2+1])/n
        a[1:-1] *= 2
        peaks = np.flatnonzero(a > 0.1)
        err = float(np.max(np.abs(X-np.fft.fft(x))))
        rec = float(np.max(np.abs(ifft(X)-x)))
        energy = abs(np.sum(abs(x)**2)
                     - np.sum(abs(X)**2)/n)
        rows.append(dict(name=name, peaks=peaks.tolist(),
                         amplitudes=a[peaks].tolist(),
                         error=err, reconstruction=rec,
                         parseval=float(energy)))
        assert err < 1e-10 and rec < 1e-12
        axes[i, 0].plot(t[:256], x[:256], lw=1)
        axes[i, 0].set(title=name, xlabel='Время, с')
        axes[i, 1].stem(np.arange(101), a[:101])
        axes[i, 1].set(xlabel='Частота, Гц',
                       ylabel='Амплитуда', ylim=(0, 1.15))
    fig.tight_layout()
    fig.savefig(OUT/'fft.png')
    plt.close(fig)
    rng = np.random.default_rng(9)
    z = rng.normal(size=32)+1j*rng.normal(size=32)
    direct_error = float(np.max(np.abs(fft(z)-dft(z))))
    assert direct_error < 1e-10
    for bad in [[], [1, 2, 3]]:
        try:
            fft(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid length accepted')
    result = dict(cases=rows, dft_error=direct_error)
    (OUT/'lab1.json').write_text(json.dumps(result, indent=2))
    print('Лабораторная работа 1. Быстрое преобразование Фурье')
    signal_names = {'sin 5': 'Синус 5 Гц',
                    'sin 17': 'Синус 17 Гц',
                    'cos 80': 'Косинус 80 Гц',
                    'sum': 'Сумма трёх сигналов'}
    for case in result['cases']:
        print(f"\nСигнал: {signal_names[case['name']]}")
        print('  Найденные частоты, Гц: '
              + ', '.join(f'{value:g}' for value in case['peaks']))
        print('  Амплитуды: '
              + ', '.join(f'{value:.12g}' for value in case['amplitudes']))
        print(f"  Ошибка относительно NumPy: {case['error']:.6e}")
        print(f"  Ошибка восстановления: {case['reconstruction']:.6e}")
        print(f"  Невязка равенства Парсеваля: {case['parseval']:.6e}")
    print('\nОшибка относительно прямого ДПФ '
          f"на 32 комплексных отсчётах: {result['dft_error']:.6e}")

if __name__ == '__main__':
    main()