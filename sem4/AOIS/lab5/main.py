import itertools
from sympy.logic import SOPform
from sympy import symbols

# Переменные: 
# v - сигнал разрешения счета
# q3, q2, q1 - текущие состояния выходов Т-триггеров
v, q3, q2, q1 = symbols('v q3 q2 q1')

def synthesize_counter():
    print(f"{'='*60}")
    print("Синтез двоичного накапливающего счетчика на 8 состояний")
    print(f"{'='*60}")
    
    # Генерация всех 16 комбинаций: (v, q3, q2, q1)
    inputs = list(itertools.product([0, 1], repeat=4))
    
    minterms_h1, minterms_h2, minterms_h3 = [], [], []
    
    print(" V | q3 q2 q1 || q3* q2* q1* || h3 h2 h1")
    print("-" * 42)
    
    for v_val, q3_val, q2_val, q1_val in inputs:
        # Переводим текущее состояние в целое число (от 0 до 7)
        current_val = (q3_val << 2) | (q2_val << 1) | q1_val
        
        if v_val == 1:
            # Накапливающий счетчик: прибавляем 1 (с переполнением на 8)
            next_val = (current_val + 1) % 8
        else:
            # Если V=0, счетчик хранит текущее значение
            next_val = current_val
            
        # Разбиваем следующее состояние обратно на биты
        q3_next = (next_val >> 2) & 1
        q2_next = (next_val >> 1) & 1
        q1_next = next_val & 1
        
        # Функция возбуждения Т-триггера: h = q(t) XOR q(t+1)
        h3_val = q3_val ^ q3_next
        h2_val = q2_val ^ q2_next
        h1_val = q1_val ^ q1_next
        
        print(f" {v_val} |  {q3_val}  {q2_val}  {q1_val} ||  {q3_next}   {q2_next}   {q1_next}  ||  {h3_val}  {h2_val}  {h1_val}")
        
        # Сохраняем наборы, где функции возбуждения равны 1
        term = [v_val, q3_val, q2_val, q1_val]
        if h1_val == 1: minterms_h1.append(term)
        if h2_val == 1: minterms_h2.append(term)
        if h3_val == 1: minterms_h3.append(term)

    vars_sym = [v, q3, q2, q1]
    
    print("\n--- Минимизированные функции возбуждения (для схемы) ---")
    print(f"h1 = {SOPform(vars_sym, minterms_h1)}")
    print(f"h2 = {SOPform(vars_sym, minterms_h2)}")
    print(f"h3 = {SOPform(vars_sym, minterms_h3)}")

if __name__ == "__main__":
    synthesize_counter()
