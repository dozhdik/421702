import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

np.random.seed(42)          # фиксируем генератор для воспроизводимости
plt.rcParams['figure.dpi'] = 110

N = 500                     # объём выборок (п. 1 задания)
LAM_EXP = 1.0               # параметр экспоненциального распределения
LAM_POIS = 3.0              # параметр распределения Пуассона

# ======================================================================
# 1. Генерация выборок
# ======================================================================

x_exp = np.random.exponential(scale=1/LAM_EXP, size=N)
x_pois = np.random.poisson(lam=LAM_POIS, size=N)

print('Экспоненциальная, первые 10 значений:', np.round(x_exp[:10], 3))
print('Пуассон, первые 10 значений:        ', x_pois[:10])

# ======================================================================
# 2. Собственные функции для выборочных характеристик
# ======================================================================

def my_mean(x):
    x = np.asarray(x, dtype=float)
    return np.sum(x) / len(x)

def my_var(x, ddof=1):
    """Дисперсия. ddof=1 — несмещённая (делим на n-1), ddof=0 — смещённая (на n)."""
    x = np.asarray(x, dtype=float)
    m = my_mean(x)
    return np.sum((x - m) ** 2) / (len(x) - ddof)

def my_std(x, ddof=1):
    return np.sqrt(my_var(x, ddof))

def my_quantile(x, p):
    """Квантиль уровня p (0..1), линейная интерполяция как в np.percentile."""
    xs = np.sort(np.asarray(x, dtype=float))
    h = (len(xs) - 1) * p
    lo = int(h)                       # floor для h >= 0
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (h - lo) * (xs[hi] - xs[lo])

def my_median(x):
    return my_quantile(x, 0.5)

def my_skew(x, ddof=0):
    x = np.asarray(x, dtype=float)
    z = (x - my_mean(x)) / my_std(x, ddof)
    return np.sum(z ** 3) / len(x)

def my_kurtosis(x, ddof=0):
    """Избыточный эксцесс (минус 3), как scipy.stats.kurtosis по умолчанию."""
    x = np.asarray(x, dtype=float)
    z = (x - my_mean(x)) / my_std(x, ddof)
    return np.sum(z ** 4) / len(x) - 3

def my_stats(x):
    return {
        'Среднее': my_mean(x),
        'Дисперсия': my_var(x),
        'Ст. отклонение': my_std(x),
        'Медиана': my_median(x),
        'Q1 (25%)': my_quantile(x, 0.25),
        'Q3 (75%)': my_quantile(x, 0.75),
        'Асимметрия': my_skew(x),
        'Эксцесс': my_kurtosis(x),
    }

# ======================================================================
# 2.1. Проверка собственных функций против встроенных
# ======================================================================

def builtin_stats(x):
    return {
        'Среднее': np.mean(x),
        'Дисперсия': np.var(x, ddof=1),
        'Ст. отклонение': np.std(x, ddof=1),
        'Медиана': np.median(x),
        'Q1 (25%)': np.percentile(x, 25),
        'Q3 (75%)': np.percentile(x, 75),
        'Асимметрия': stats.skew(x),
        'Эксцесс': stats.kurtosis(x),
    }

for name, x in [('Экспоненциальное', x_exp), ('Пуассона', x_pois)]:
    mine, ref = my_stats(x), builtin_stats(x)
    print(f'--- {name} ---')
    print(f'{"Статистика":<16}{"Своя функция":>14}{"numpy/scipy":>14}{"|разница|":>12}')
    for k in mine:
        print(f'{k:<16}{mine[k]:>14.6f}{ref[k]:>14.6f}{abs(mine[k]-ref[k]):>12.1e}')
    assert all(np.isclose(mine[k], ref[k]) for k in mine)
    print('Все значения совпадают (np.isclose = True)\n')

# ======================================================================
# 3. Сравнение выборочных и теоретических характеристик
# ======================================================================

def theory(dist):
    m, v, s, k = dist.stats(moments='mvsk')
    return {
        'Среднее': float(m), 'Дисперсия': float(v), 'Ст. отклонение': float(np.sqrt(v)),
        'Медиана': float(dist.median()),
        'Q1 (25%)': float(dist.ppf(0.25)), 'Q3 (75%)': float(dist.ppf(0.75)),
        'Асимметрия': float(s), 'Эксцесс': float(k),
    }

exp_dist = stats.expon(scale=1/LAM_EXP)
pois_dist = stats.poisson(mu=LAM_POIS)

def print_table(name, x, dist):
    emp, th = my_stats(x), theory(dist)
    print(f'=== {name} (n = {len(x)}) ===')
    print(f'{"Статистика":<16}{"Выборка":>10}{"Теория":>10}{"Отклонение":>12}')
    for k in emp:
        print(f'{k:<16}{emp[k]:>10.4f}{th[k]:>10.4f}{emp[k]-th[k]:>12.4f}')
    print()
    return emp, th

emp_exp, th_exp = print_table('Экспоненциальное, λ = 1', x_exp, exp_dist)
emp_pois, th_pois = print_table('Пуассона, λ = 3', x_pois, pois_dist)

# ======================================================================
# 4. Визуализация
# ======================================================================

# ======================================================================
# 4.1. Экспоненциальное распределение: гистограмма и плотность
# ======================================================================

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(x_exp, bins=30, density=True, alpha=0.6, color='steelblue', edgecolor='white',
        label='Эмпирическая гистограмма (n = 500)')
grid = np.linspace(0, x_exp.max(), 300)
ax.plot(grid, exp_dist.pdf(grid), 'r-', lw=2, label='Теоретическая плотность $\\lambda e^{-\\lambda x}$')
ax.axvline(my_mean(x_exp), color='k', ls='--', lw=1.2, label=f'Выборочное среднее = {my_mean(x_exp):.3f}')
ax.axvline(my_median(x_exp), color='orange', ls=':', lw=1.8, label=f'Выборочная медиана = {my_median(x_exp):.3f}')
ax.set_xlabel('x')
ax.set_ylabel('Плотность')
ax.set_title('Экспоненциальное распределение, λ = 1')
ax.legend()
plt.tight_layout()
plt.savefig('fig1_exponential.png', dpi=130)
plt.show()

# ======================================================================
# 4.2. Распределение Пуассона: столбчатая диаграмма и функция вероятности
# ======================================================================

k_vals = np.arange(0, x_pois.max() + 1)
counts = np.array([np.sum(x_pois == k) for k in k_vals])
rel_freq = counts / N

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(k_vals, rel_freq, width=0.6, alpha=0.6, color='seagreen', label='Относительные частоты (n = 500)')
ax.plot(k_vals, pois_dist.pmf(k_vals), 'ro-', lw=1.5, ms=6, label='Теоретические $P(X=k)$')
ax.set_xticks(k_vals)
ax.set_xlabel('k')
ax.set_ylabel('Вероятность / относительная частота')
ax.set_title('Распределение Пуассона, λ = 3')
ax.legend()
plt.tight_layout()
plt.savefig('fig2_poisson.png', dpi=130)
plt.show()

print(f'{"k":>3}{"частота":>10}{"P(X=k)":>10}')
for k, f, p in zip(k_vals, rel_freq, pois_dist.pmf(k_vals)):
    print(f'{k:>3}{f:>10.3f}{p:>10.3f}')

# ======================================================================
# 5. Имитационное моделирование: закон больших чисел
# ======================================================================

ns = np.arange(1, 1001, 10)     # 1, 11, ..., 991 -> 100 значений
R = 100                          # число повторений
MU = 1 / LAM_EXP                 # теоретическое матожидание
SIGMA = 1 / LAM_EXP              # теоретическое ст. отклонение

means = np.empty((R, len(ns)))
for j, n in enumerate(ns):
    for r in range(R):
        means[r, j] = my_mean(np.random.exponential(scale=1/LAM_EXP, size=n))

fig, ax = plt.subplots(figsize=(9, 5))
for r in range(R):
    ax.plot(ns, means[r], color='steelblue', alpha=0.12, lw=0.8)
ax.axhline(MU, color='red', lw=2, label=f'Теоретическое матожидание μ = {MU:g}')
ax.plot(ns, MU + 2 * SIGMA / np.sqrt(ns), 'k--', lw=1.2, label='μ ± 2σ/√n')
ax.plot(ns, MU - 2 * SIGMA / np.sqrt(ns), 'k--', lw=1.2)
ax.set_ylim(0, 2.5)
ax.set_xlabel('Объём выборки n')
ax.set_ylabel('Выборочное среднее')
ax.set_title('Закон больших чисел: 100 траекторий выборочного среднего, Exp(λ = 1)')
ax.legend()
plt.tight_layout()
plt.savefig('fig3_lln.png', dpi=130)
plt.show()

# ======================================================================
# 5.1. Стандартная ошибка среднего и 1/√n
# ======================================================================

se_emp = np.array([my_std(means[:, j]) for j in range(len(ns))])
se_th = SIGMA / np.sqrt(ns)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].plot(ns, se_emp, 'o', ms=3, label='Эмпирическая SE (по 100 повторениям)')
axes[0].plot(ns, se_th, 'r-', lw=2, label='Теоретическая SE = σ/√n')
axes[0].set_xlabel('n'); axes[0].set_ylabel('Стандартная ошибка')
axes[0].set_title('SE в зависимости от n'); axes[0].legend()

axes[1].plot(1/np.sqrt(ns), se_emp, 'o', ms=3, label='Эмпирическая SE')
axes[1].plot(1/np.sqrt(ns), se_th, 'r-', lw=2, label='Прямая σ·(1/√n)')
axes[1].set_xlabel('1/√n'); axes[1].set_ylabel('Стандартная ошибка')
axes[1].set_title('SE против 1/√n'); axes[1].legend()
plt.tight_layout()
plt.savefig('fig4_se.png', dpi=130)
plt.show()

slope = np.sum((1/np.sqrt(ns)) * se_emp) / np.sum((1/np.sqrt(ns))**2)
print(f'Наклон прямой SE = k / sqrt(n), МНК без свободного члена: k = {slope:.4f} (теория: σ = {SIGMA})')
for n_check in [1, 101, 501, 991]:
    j = list(ns).index(n_check)
    print(f'n = {n_check:>4}: SE эмп. = {se_emp[j]:.4f}, σ/√n = {se_th[j]:.4f}')

# ======================================================================
# 6. Дополнительно: центральная предельная теорема
# ======================================================================

fig, axes = plt.subplots(1, 4, figsize=(14, 3.4))
M = 5000
for ax, n in zip(axes, [1, 5, 30, 200]):
    sample_means = np.random.exponential(scale=1/LAM_EXP, size=(M, n)).sum(axis=1) / n
    ax.hist(sample_means, bins=40, density=True, alpha=0.6, color='slateblue')
    g = np.linspace(sample_means.min(), sample_means.max(), 200)
    ax.plot(g, stats.norm.pdf(g, MU, SIGMA/np.sqrt(n)), 'r-', lw=2)
    ax.set_title(f'n = {n}, асимм. = {my_skew(sample_means):.2f}')
    ax.set_xlabel('выборочное среднее')
axes[0].set_ylabel('Плотность')
fig.suptitle('ЦПТ: распределение среднего Exp(1) (гистограмма) и N(μ, σ²/n) (красная кривая)', y=1.03)
plt.tight_layout()
plt.savefig('fig5_clt.png', dpi=130, bbox_inches='tight')
plt.show()