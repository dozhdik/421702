"""Лабораторная 2. Запуск: python lab2.py. Графики сохраняются в figures/."""
import matplotlib
matplotlib.use('Agg')
def display(obj):
    print(obj.to_string() if hasattr(obj, 'to_string') else obj)

from pathlib import Path
import io, base64, zlib, hashlib, math, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy
from scipy import stats
from scipy.optimize import minimize
SEED = 9
B = 500
OUT = Path('.')
(OUT / 'figures').mkdir(exist_ok=True)
(OUT / 'results').mkdir(exist_ok=True)
sns.set_theme(style='whitegrid', font='DejaVu Sans', font_scale=0.95)
pd.set_option('display.max_columns', 12)
pd.set_option('display.width', 140)

def savefig(name):
    plt.savefig(OUT / 'figures' / (name + '.png'), dpi=170, bbox_inches='tight')
    plt.show()
    plt.close()

def table(frame, name):
    frame.to_csv(OUT / 'results' / (name + '.csv'), encoding='utf-8-sig')
    display(frame.round(6))

print('Python', sys.version.split()[0])
print('NumPy', np.__version__, '| pandas', pd.__version__, '| SciPy', scipy.__version__)

# Встроенная неизменённая копия исходного CSV, сжатая только для компактности.
CSV_B64 = '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'
source_path = Path('data/penguins_size.csv')
raw_bytes = source_path.read_bytes() if source_path.exists() else zlib.decompress(base64.b64decode(CSV_B64))
print('SHA256:', hashlib.sha256(raw_bytes).hexdigest())
raw = pd.read_csv(io.BytesIO(raw_bytes))
print('Размер исходных данных:', raw.shape)
display(raw.head())
raw.info()
table(pd.DataFrame({'тип': raw.dtypes.astype(str), 'пропусков': raw.isna().sum(),
                    'уникальных': raw.nunique()}), 'structure')
print('Значения пола:', raw['sex'].unique())
print('Полных дубликатов:', raw.duplicated().sum())

features = ['culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'body_mass_g']
labels = {'culmen_length_mm': 'Длина клюва, мм', 'culmen_depth_mm': 'Глубина клюва, мм',
          'flipper_length_mm': 'Длина ласта, мм', 'body_mass_g': 'Масса, г'}
df = raw.copy()
df['sex'] = df['sex'].replace('.', np.nan)
for col in features:
    df[col] = pd.to_numeric(df[col], errors='coerce')
print('Пропуски после нормализации пола:', df.isna().sum().to_dict())
removed_duplicates = int(df.duplicated().sum())
df = df.drop_duplicates()
removed_missing = int(df[features].isna().any(axis=1).sum())
df = df.dropna(subset=features).copy()
for col in ['species', 'island', 'sex']:
    df[col] = df[col].astype('category')
print(f'Удалено дубликатов: {removed_duplicates}; строк без измерений: {removed_missing}')
print('Осталось:', len(df), '; неизвестный пол:', df['sex'].isna().sum())
assert np.isfinite(df[features].to_numpy()).all()
assert (df[features] > 0).all().all()
table(df.groupby('species', observed=True).size().to_frame('n'), 'species_counts')
df.to_csv(OUT / 'results/penguins_clean.csv', index=False, encoding='utf-8-sig')

desc = df[features].describe().T
# Переименование делает смысл столбцов однозначным.
desc = desc.rename(columns={'50%': 'median', 'std': 'std_ddof1'})
desc['skew'] = df[features].skew()
desc['excess'] = df[features].kurt()
table(desc, 'descriptive')
q1, q3 = df[features].quantile(.25), df[features].quantile(.75)
iqr = q3-q1
outliers = pd.DataFrame({'lower': q1-1.5*iqr, 'upper': q3+1.5*iqr})
outliers['count'] = ((df[features] < outliers['lower']) | (df[features] > outliers['upper'])).sum()
table(outliers, 'outliers')
fig, axes = plt.subplots(2, 2, figsize=(11, 7))
for ax, col in zip(axes.flat, features):
    sns.histplot(data=df, x=col, hue='species', bins=22, kde=True,
                 element='step', stat='count', common_norm=False, ax=ax)
    ax.set(xlabel=labels[col], ylabel='Число наблюдений')
fig.suptitle('Распределения четырёх количественных признаков')
plt.tight_layout(); savefig('01_histograms')
fig, axes = plt.subplots(2, 2, figsize=(11, 6))
for ax, col in zip(axes.flat, features):
    sns.boxplot(x=df[col], ax=ax, color='#9cc5df')
    ax.set(xlabel=labels[col])
fig.suptitle('Ящики с усами для полной очищенной выборки')
plt.tight_layout(); savefig('02_boxplots')

corr = df[features].corr()
table(corr, 'correlation')
vif = pd.DataFrame({'VIF': np.diag(np.linalg.inv(corr.to_numpy()))}, index=features)
table(vif, 'vif')
within = df.groupby('species', observed=True).apply(
    lambda g: g['culmen_length_mm'].corr(g['culmen_depth_mm']), include_groups=False)
table(within.to_frame('corr_length_depth'), 'within_species_correlation')
plt.figure(figsize=(7.5, 6))
sns.heatmap(corr.rename(index=labels, columns=labels), annot=True, fmt='.3f',
            cmap='coolwarm', vmin=-1, vmax=1, square=True)
plt.title('Корреляции Пирсона'); plt.tight_layout(); savefig('03_correlation')
g = sns.pairplot(df, vars=features, hue='species', diag_kind='hist',
                 plot_kws={'alpha': .65, 's': 20}, height=2.3)
g.fig.suptitle('Попарные зависимости и видовые группы', y=1.02)
savefig('04_pairplot')

group = df.loc[(df['species']=='Adelie') & (df['sex']=='FEMALE')]
x = group['culmen_length_mm'].to_numpy(dtype=float)
n = len(x)

def log_likelihood(params, sample):
    mu, sigma = params
    sample = np.asarray(sample, dtype=float)
    if sigma <= 0 or not np.isfinite(sigma):
        return -np.inf
    return (-sample.size / 2 * np.log(2*np.pi) - sample.size*np.log(sigma)
            - np.sum((sample-mu)**2)/(2*sigma**2))

def nll_gradient(params, sample):
    mu, sigma = params
    return np.array([np.sum(mu-sample)/sigma**2,
                     len(sample)/sigma-np.sum((sample-mu)**2)/sigma**3])

initial = [float(np.median(x)+1), float(np.std(x, ddof=1)*1.4)]
opt = minimize(lambda p: -log_likelihood(p, x), initial,
               jac=lambda p: nll_gradient(p, x), method='L-BFGS-B',
               bounds=[(None,None),(1e-8,None)],
               options={'ftol': 1e-14, 'gtol': 1e-9, 'maxiter': 10000})
if not opt.success:
    raise RuntimeError(opt.message)
mu_num, sigma_num = opt.x
mu0, sigma0 = float(x.mean()), float(x.std(ddof=0))
W, pvalue = stats.shapiro(x)
print('n =', n, '| начальная точка =', initial)
print('Оптимизация:', opt.message, '| итераций:', opt.nit)
print('ММП численно:', opt.x, '| log L =', log_likelihood(opt.x,x))
print(f'Шапиро–Уилк: W={W:.6f}; p={pvalue:.6f}; alpha=0.05')
print('Асимметрия:', stats.skew(x,bias=False), 'Эксцесс:', stats.kurtosis(x,bias=False))
print('Разность с формулами:', opt.x-np.array([mu0,sigma0]))
assert np.allclose(opt.x, [mu0,sigma0], rtol=1e-7, atol=1e-7)
fig, axes=plt.subplots(1,2,figsize=(11,4))
sns.histplot(x=x, bins=12, stat='density', ax=axes[0], color='#9cc5df')
grid=np.linspace(x.min()-1, x.max()+1, 400)
axes[0].plot(grid, stats.norm.pdf(grid,mu_num,sigma_num), 'r-', label='Нормальная ММП-модель')
axes[0].set(xlabel='Длина клюва, мм', ylabel='Плотность'); axes[0].legend()
stats.probplot(x, dist='norm', plot=axes[1]); axes[1].set_title('Q–Q график исходной подгруппы')
plt.tight_layout(); savefig('05_normal_fit')

import math

def normal_mle_manual(values):
    values = [float(v) for v in values]
    if len(values) < 2 or not all(math.isfinite(v) for v in values):
        raise ValueError('Нужны хотя бы два конечных наблюдения')
    mu = sum(values)/len(values)
    variance = sum((v-mu)**2 for v in values)/len(values)
    if variance <= 0:
        raise ValueError('Для постоянной выборки нет конечного ММП при sigma > 0')
    return mu, math.sqrt(variance)

def exponential_mle_manual(values):
    values = [float(v) for v in values]
    if not values or not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError('Нужна непустая выборка конечных неотрицательных значений')
    total = sum(values)
    if total <= 0:
        raise ValueError('Для всех нулей нет конечного ММП интенсивности')
    return len(values)/total

mu_manual, sigma_manual = normal_mle_manual(x)
m1, m2 = sum(float(v) for v in x)/n, sum(float(v)**2 for v in x)/n
mu_mm, sigma_mm = m1, math.sqrt(m2-m1*m1)
mu_fit, sigma_fit = stats.norm.fit(x)
comparison = pd.DataFrame([
    ['ММП численно',mu_num,sigma_num,sigma_num**2],
    ['ММП вручную',mu_manual,sigma_manual,sigma_manual**2],
    ['Метод моментов',mu_mm,sigma_mm,sigma_mm**2],
    ['scipy.stats.norm.fit',mu_fit,sigma_fit,sigma_fit**2],
    ['Выборочные ddof=0',x.mean(),x.std(ddof=0),x.var(ddof=0)],
    ['Исправленные ddof=1',x.mean(),x.std(ddof=1),x.var(ddof=1)]
],columns=['method','mu','sigma','variance']).set_index('method')
table(comparison,'normal_comparison')
assert np.allclose([mu_manual,sigma_manual],[mu_mm,sigma_mm],atol=1e-10)
assert np.allclose([mu_fit,sigma_fit],[mu_manual,sigma_manual],atol=1e-10)

def c_n(size):
    return math.sqrt(2/size)*math.exp(math.lgamma(size/2)-math.lgamma((size-1)/2))

streams = np.random.SeedSequence(SEED).spawn(3)
rng_main, rng_consistency, rng_exp = [np.random.default_rng(s) for s in streams]
samples = rng_main.normal(mu0,sigma0,size=(B,n))
# Применяем вручную реализованную функцию к каждой выборке.
estimates = np.array([normal_mle_manual(row) for row in samples])
mu_est, sigma_est = estimates.T
var_est = sigma_est**2
cn = c_n(n)
theory_mean = [mu0,cn*sigma0,(n-1)/n*sigma0**2]
theory_sd = [sigma0/math.sqrt(n),sigma0*math.sqrt((n-1)/n-cn**2),
             sigma0**2*math.sqrt(2*(n-1))/n]
mc_rows=[]
for name,vals,true,tm,ts in zip(['mu','sigma','sigma_squared'],
    [mu_est,sigma_est,var_est],[mu0,sigma0,sigma0**2],theory_mean,theory_sd):
    mc_rows.append([name,true,vals.mean(),vals.mean()-true,tm-true,
                   vals.std(ddof=1),ts,np.mean((vals-true)**2),vals.std(ddof=1)/math.sqrt(B)])
mc=pd.DataFrame(mc_rows,columns=['parameter','true','mean','bias','theory_bias',
                                'SD','theory_SD','MSE','MCSE']).set_index('parameter')
table(mc,'monte_carlo_500')
fig,axes=plt.subplots(1,2,figsize=(11,4))
for ax,vals,true,sd,title in zip(axes,[mu_est,sigma_est],[mu0,sigma0],
    [sigma0/np.sqrt(n),sigma0/np.sqrt(2*n)],['Оценка среднего','Оценка σ']):
    ax.hist(vals,bins=25,density=True,alpha=.65,color='#6aa6cf')
    ax.axvline(true,color='red',ls='--',label='Истинное значение')
    grid=np.linspace(vals.min(),vals.max(),300)
    ax.plot(grid,stats.norm.pdf(grid,true,sd),color='black',label='Теоретическая N / асимптотика')
    ax.set(title=title,xlabel='Оценка, мм',ylabel='Плотность'); ax.legend(fontsize=8)
plt.tight_layout();savefig('06_mc_histograms')

sizes=[10,20,30,50,n,100,200,500]
cons_rows=[]; standardized={}
for size in sizes:
    sims=rng_consistency.normal(mu0,sigma0,size=(B,size))
    est=np.array([normal_mle_manual(row) for row in sims])
    cm=c_n(size)
    cons_rows.append([size,est[:,0].std(ddof=1),sigma0/math.sqrt(size),
      est[:,1].std(ddof=1),sigma0*math.sqrt((size-1)/size-cm**2),
      sigma0/math.sqrt(2*size),est[:,0].mean()-mu0,est[:,1].mean()-sigma0,
      np.mean((est[:,0]-mu0)**2),np.mean((est[:,1]-sigma0)**2)])
    if size in [10,500]:
        standardized[size]=(np.sqrt(size)*(est[:,0]-mu0)/sigma0,
                            np.sqrt(2*size)*(est[:,1]-sigma0)/sigma0)
cons=pd.DataFrame(cons_rows,columns=['n','SD_mu','theory_SD_mu','SD_sigma',
    'exact_SD_sigma','asympt_SD_sigma','bias_mu','bias_sigma','MSE_mu','MSE_sigma']).set_index('n')
table(cons,'consistency')
fig,axes=plt.subplots(1,2,figsize=(11,4))
axes[0].plot(cons.index,cons.SD_mu,'o-',label='Монте Карло')
axes[0].plot(cons.index,cons.theory_SD_mu,'--',label='σ / √n')
axes[1].plot(cons.index,cons.SD_sigma,'o-',label='Монте Карло')
axes[1].plot(cons.index,cons.exact_SD_sigma,'--',label='Точная теория')
axes[1].plot(cons.index,cons.asympt_SD_sigma,':',label='σ / √(2n)')
for ax,title in zip(axes,['Разброс оценки среднего','Разброс оценки σ']):
    ax.set(title=title,xlabel='Объём n',ylabel='Стандартное отклонение, мм');ax.legend()
plt.tight_layout();savefig('07_consistency')
fig,axes=plt.subplots(2,2,figsize=(10,7))
normality_rows=[]
for row,size in enumerate([10,500]):
    for j,name in enumerate(['mu','sigma']):
        z=standardized[size][j]
        stats.probplot(z,dist='norm',plot=axes[row,j])
        axes[row,j].set_title(f'Стандартизованная {name}, n={size}')
        normality_rows.append([size,name,z.mean(),z.std(ddof=1),
                              stats.skew(z,bias=False),stats.kurtosis(z,bias=False)])
plt.tight_layout();savefig('08_asymptotic_qq')
table(pd.DataFrame(normality_rows,columns=['n','parameter','mean_Z','SD_Z','skew','excess']),
      'asymptotic_diagnostics')

lambda_true=0.4
y=rng_exp.exponential(scale=1/lambda_true,size=n)
lambda_manual=exponential_mle_manual(y)
def exp_nll_theta(theta,sample):
    rate=np.exp(theta[0])
    return -len(sample)*theta[0]+rate*np.sum(sample)
exp_opt=minimize(exp_nll_theta,[math.log(.8)],args=(y,),method='BFGS',
    jac=lambda theta,sample: np.array([-len(sample)+np.exp(theta[0])*np.sum(sample)]),
    options={'gtol':1e-8})
if not exp_opt.success: raise RuntimeError(exp_opt.message)
lambda_num=float(np.exp(exp_opt.x[0]))
_, exp_scale=stats.expon.fit(y,floc=0)
exp_comparison=pd.DataFrame({'lambda':[lambda_true,lambda_manual,lambda_num,1/exp_scale,1/y.mean()]},
 index=['Истинный параметр','ММП вручную','ММП численно','scipy expon.fit floc=0','Метод моментов'])
table(exp_comparison,'exponential_comparison')
assert np.isclose(lambda_manual,lambda_num,rtol=1e-7)
assert np.isclose(lambda_manual,1/exp_scale,rtol=1e-12)
plt.figure(figsize=(7,4))
plt.hist(y,bins=15,density=True,alpha=.65,label='Синтетические данные')
grid=np.linspace(0,y.max(),300)
plt.plot(grid,lambda_manual*np.exp(-lambda_manual*grid),label='ММП плотность')
plt.plot(grid,lambda_true*np.exp(-lambda_true*grid),'--',label='Истинная плотность')
plt.xlabel('Значение');plt.ylabel('Плотность');plt.legend();plt.tight_layout();savefig('09_exponential')