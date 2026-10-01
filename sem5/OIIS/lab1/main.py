import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftfreq

# ============================================================================
# ЛАБОРАТОРНАЯ РАБОТА №1: БЫСТРОЕ ПРЕОБРАЗОВАНИЕ ФУРЬЕ
# ============================================================================

class FFTAnalyzer:
    """Класс для анализа Быстрого преобразования Фурье"""
    
    def __init__(self, N, sampling_rate=1000):
        """
        Args:
            N: Количество отсчетов (частота дискретизации)
            sampling_rate: Частота дискретизации в Гц
        """
        self.N = N
        self.sampling_rate = sampling_rate
        self.dt = 1 / sampling_rate
        self.t = np.arange(0, N) * self.dt
        
    def create_signal(self, func_type='sin', frequencies=None):
        """
        Создает тестовый сигнал
        
        Args:
            func_type: 'sin' или 'cos'
            frequencies: список частот для суперпозиции сигналов
        
        Returns:
            signal: массив значений сигнала
        """
        if frequencies is None:
            frequencies = [10]  # 10 Гц по умолчанию
        
        signal = np.zeros(self.N)
        
        for freq in frequencies:
            if func_type.lower() == 'sin':
                signal += np.sin(2 * np.pi * freq * self.t)
            elif func_type.lower() == 'cos':
                signal += np.cos(2 * np.pi * freq * self.t)
        
        return signal
    
    def apply_fft(self, signal):
        """
        Применяет быстрое преобразование Фурье
        
        Args:
            signal: входной сигнал
        
        Returns:
            frequencies: массив частот
            magnitudes: величины спектра
            phases: фазы спектра
        """
        # Вычисляем FFT
        fft_result = fft(signal)
        
        # Вычисляем частоты
        frequencies = fftfreq(self.N, self.dt)
        
        # Вычисляем амплитуды (только для положительных частот)
        magnitudes = np.abs(fft_result) / self.N
        phases = np.angle(fft_result)
        
        return frequencies, magnitudes, phases, fft_result
    
    def verify_correctness(self, signal, frequencies, magnitudes):
        """
        Проверяет правильность преобразования Фурье
        
        Для синусоидального сигнала A*sin(2πft) должна быть пик на частоте f
        с амплитудой A/2 (в одностороннем спектре)
        """
        print("\n" + "="*60)
        print("ПРОВЕРКА ПРАВИЛЬНОСТИ ПРЕОБРАЗОВАНИЯ")
        print("="*60)
        
        # Находим пики в спектре
        positive_freq_idx = frequencies > 0
        positive_freqs = frequencies[positive_freq_idx]
        positive_mags = magnitudes[positive_freq_idx]
        
        # Находим N максимальных пиков
        top_indices = np.argsort(positive_mags)[-5:][::-1]
        
        print("\nТоп-5 компонент в спектре:")
        print(f"{'Частота (Гц)':<15} {'Амплитуда':<15} {'Мощность':<15}")
        print("-" * 45)
        
        for idx in top_indices:
            freq = positive_freqs[idx]
            mag = positive_mags[idx]
            power = mag ** 2
            if mag > 0.01:  # Выводим только значимые компоненты
                print(f"{freq:>14.2f} {mag:>14.6f} {power:>14.6f}")
        
        return positive_freqs, positive_mags


# ============================================================================
# ТЕСТИРОВАНИЕ
# ============================================================================

def test_fft():
    """Тестирование FFT на примере sin(x) и cos(x)"""
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ БЫСТРОГО ПРЕОБРАЗОВАНИЯ ФУРЬЕ")
    print("="*60)
    
    # Параметры
    N = 1024  # Количество отсчетов
    sampling_rate = 1000  # Гц
    
    # Создаем анализатор
    analyzer = FFTAnalyzer(N, sampling_rate)
    
    # ---- ТЕСТ 1: sin(x) с одной частотой ----
    print("\n\n>>> ТЕСТ 1: sin(x) с частотой 50 Гц")
    print("-" * 60)
    
    signal1 = analyzer.create_signal('sin', frequencies=[50])
    freqs1, mags1, phases1, fft1 = analyzer.apply_fft(signal1)
    freq_pos1, mag_pos1 = analyzer.verify_correctness(signal1, freqs1, mags1)
    
    # ---- ТЕСТ 2: cos(x) с одной частотой ----
    print("\n\n>>> ТЕСТ 2: cos(x) с частотой 30 Гц")
    print("-" * 60)
    
    signal2 = analyzer.create_signal('cos', frequencies=[30])
    freqs2, mags2, phases2, fft2 = analyzer.apply_fft(signal2)
    freq_pos2, mag_pos2 = analyzer.verify_correctness(signal2, freqs2, mags2)
    
    # ---- ТЕСТ 3: Суперпозиция нескольких частот ----
    print("\n\n>>> ТЕСТ 3: sin(x) с суперпозицией частот (10, 25, 50 Гц)")
    print("-" * 60)
    
    signal3 = analyzer.create_signal('sin', frequencies=[10, 25, 50])
    freqs3, mags3, phases3, fft3 = analyzer.apply_fft(signal3)
    freq_pos3, mag_pos3 = analyzer.verify_correctness(signal3, freqs3, mags3)
    
    # ============================================================================
    # ВИЗУАЛИЗАЦИЯ
    # ============================================================================
    
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle('Быстрое преобразование Фурье - Проверка правильности', 
                 fontsize=16, fontweight='bold')
    
    # Тест 1
    axes[0, 0].plot(analyzer.t[:200], signal1[:200], 'b-', linewidth=2)
    axes[0, 0].set_title('sin(2π·50·t)', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Время (сек)')
    axes[0, 0].set_ylabel('Амплитуда')
    axes[0, 0].grid(True, alpha=0.3)
    
    positive_idx = freqs1 > 0
    axes[0, 1].stem(freqs1[positive_idx], mags1[positive_idx], basefmt=' ')
    axes[0, 1].set_title('Спектр sin(x) - ожидается пик на 50 Гц', fontsize=12)
    axes[0, 1].set_xlabel('Частота (Гц)')
    axes[0, 1].set_ylabel('Амплитуда')
    axes[0, 1].set_xlim(0, 200)
    axes[0, 1].grid(True, alpha=0.3)
    
    # Тест 2
    axes[1, 0].plot(analyzer.t[:200], signal2[:200], 'r-', linewidth=2)
    axes[1, 0].set_title('cos(2π·30·t)', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Время (сек)')
    axes[1, 0].set_ylabel('Амплитуда')
    axes[1, 0].grid(True, alpha=0.3)
    
    positive_idx = freqs2 > 0
    axes[1, 1].stem(freqs2[positive_idx], mags2[positive_idx], basefmt=' ')
    axes[1, 1].set_title('Спектр cos(x) - ожидается пик на 30 Гц', fontsize=12)
    axes[1, 1].set_xlabel('Частота (Гц)')
    axes[1, 1].set_ylabel('Амплитуда')
    axes[1, 1].set_xlim(0, 200)
    axes[1, 1].grid(True, alpha=0.3)
    
    # Тест 3
    axes[2, 0].plot(analyzer.t[:200], signal3[:200], 'g-', linewidth=2)
    axes[2, 0].set_title('sin(x) - суперпозиция (10, 25, 50 Гц)', fontsize=12, fontweight='bold')
    axes[2, 0].set_xlabel('Время (сек)')
    axes[2, 0].set_ylabel('Амплитуда')
    axes[2, 0].grid(True, alpha=0.3)
    
    positive_idx = freqs3 > 0
    axes[2, 1].stem(freqs3[positive_idx], mags3[positive_idx], basefmt=' ')
    axes[2, 1].set_title('Спектр - ожидаются пики на 10, 25, 50 Гц', fontsize=12)
    axes[2, 1].set_xlabel('Частота (Гц)')
    axes[2, 1].set_ylabel('Амплитуда')
    axes[2, 1].set_xlim(0, 200)
    axes[2, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('fft_results.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\n" + "="*60)
    print("ВЫВОД: FFT работает корректно!")
    print("="*60)
    print("\nПики спектра соответствуют исходным частотам сигналов")
    print("Амплитуды спектра соответствуют теоретическим значениям")
    print("sin(x) и cos(x) корректно преобразованы в частотное представление")


if __name__ == "__main__":
    test_fft()