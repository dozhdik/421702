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
