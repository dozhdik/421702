import itertools
from sympy.logic import SOPform, POSform
from sympy import symbols

# Определение символов (входных переменных)
x1, x2, x3, x4 = symbols('x1 x2 x3 x4')

def generate_perfect_forms(vars_sym, minterms, maxterms):
    """
    Генерирует строковое представление СДНФ и СКНФ для вывода.
    """
    sdnf_terms = []
    for term in minterms:
        # Для СДНФ: 1 это переменная, 0 это инверсия
        vars_str = [str(vars_sym[i]) if val == 1 else f"~{vars_sym[i]}" for i, val in enumerate(term)]
        sdnf_terms.append("(" + " * ".join(vars_str) + ")")
    sdnf_str = " + ".join(sdnf_terms) if sdnf_terms else "0"

    sknf_terms = []
    for term in maxterms:
        # Для СКНФ: 0 это переменная, 1 это инверсия
        vars_str = [str(vars_sym[i]) if val == 0 else f"~{vars_sym[i]}" for i, val in enumerate(term)]
        sknf_terms.append("(" + " + ".join(vars_str) + ")")
    sknf_str = " * ".join(sknf_terms) if sknf_terms else "1"

    return sdnf_str, sknf_str

def task1_3input_device(device_type="ОДВ-3"):
    """
    Задание 1: Синтез 3-входового устройства (ОДС-3 или ОДВ-3)
    """
    print(f"\n{'='*50}")
    print(f"ЗАДАНИЕ 1. Синтез устройства: {device_type}")
    print(f"{'='*50}")
    
    inputs = list(itertools.product([0, 1], repeat=3))
    
    # Списки для хранения наборов (минтермы и макстермы)
    minterms_out1, maxterms_out1 = [], []
    minterms_out2, maxterms_out2 = [], []
    
    print("Таблица истинности:")
    print("x1 | x2 | x3 || OUT1 | OUT2")
    print("-" * 30)
    
    for x1_val, x2_val, x3_val in inputs:
        if device_type == "ОДВ-3":
            # Вычитатель (d_i, b_i+1)
            out1 = x1_val ^ x2_val ^ x3_val
            out2 = int((not x1_val and x2_val) or (not x1_val and x3_val) or (x2_val and x3_val))
        else:
            # Сумматор ОДС-3 (S_i, P_i+1)
            out1 = x1_val ^ x2_val ^ x3_val
            out2 = int((x1_val and x2_val) or (x1_val and x3_val) or (x2_val and x3_val))
            
        print(f" {x1_val} |  {x2_val} |  {x3_val} ||  {out1}   |   {out2}")
        
        # Записываем наборы
        term = [x1_val, x2_val, x3_val]
        (minterms_out1 if out1 == 1 else maxterms_out1).append(term)
        (minterms_out2 if out2 == 1 else maxterms_out2).append(term)

    # Получение СДНФ и СКНФ
    vars_sym = [x1, x2, x3]
    sdnf1, sknf1 = generate_perfect_forms(vars_sym, minterms_out1, maxterms_out1)
    sdnf2, sknf2 = generate_perfect_forms(vars_sym, minterms_out2, maxterms_out2)
    
    print("\n--- Совершенные формы ---")
    print(f"OUT1 СДНФ: {sdnf1}")
    print(f"OUT1 СКНФ: {sknf1}")
    print(f"OUT2 СДНФ: {sdnf2}")
    print(f"OUT2 СКНФ: {sknf2}")

    # Минимизация с помощью SymPy
    min_sdnf1 = SOPform(vars_sym, minterms_out1)
    min_sknf1 = POSform(vars_sym, minterms_out1)
    min_sdnf2 = SOPform(vars_sym, minterms_out2)
    min_sknf2 = POSform(vars_sym, minterms_out2)

    print("\n--- Результаты минимизации (Схемы уравнений) ---")
    print(f"OUT1 минимизированная (МДНФ): {min_sdnf1}")
    print(f"OUT1 минимизированная (МКНФ): {min_sknf1}")
    print(f"OUT2 минимизированная (МДНФ): {min_sdnf2}")
    print(f"OUT2 минимизированная (МКНФ): {min_sknf2}")


def task2_code_converter(n_variant=3):
    """
    Задание 2: Преобразователь кода 8421 в 8421 + n
    """
    print(f"\n{'='*50}")
    print(f"ЗАДАНИЕ 2. Синтез преобразователя: 8421 -> 8421 + {n_variant}")
    print(f"{'='*50}")
    
    inputs = list(itertools.product([0, 1], repeat=4))
    
    # 4 выхода: y4, y3, y2, y1
    minterms = {i: [] for i in range(4)}
    dontcares = [] # Избыточные наборы (10-15)
    
    print("Таблица истинности (с избыточными наборами):")
    print("№ | x4 x3 x2 x1 || y4 y3 y2 y1")
    print("-" * 32)
    
    for idx, (x4_val, x3_val, x2_val, x1_val) in enumerate(inputs):
        if idx > 9:
            # Наборы 10-15 избыточны (не полностью определенные)
            dontcares.append([x4_val, x3_val, x2_val, x1_val])
            print(f"{idx:<2}|  {x4_val}  {x3_val}  {x2_val}  {x1_val} ||  -  -  -  -")
            continue
            
        # Логика 8421 + n (с ограничением по модулю 16 для 4 бит)
        val = (idx + n_variant) % 16
        # Превращаем число в список 4 бит (y4, y3, y2, y1)
        y_bits = [int(b) for b in format(val, '04b')]
        
        print(f"{idx:<2}|  {x4_val}  {x3_val}  {x2_val}  {x1_val} ||  {y_bits[0]}  {y_bits[1]}  {y_bits[2]}  {y_bits[3]}")
        
        for i in range(4):
            if y_bits[i] == 1:
                minterms[i].append([x4_val, x3_val, x2_val, x1_val])

    print("\n--- Результаты минимизации с учетом избыточных наборов ---")
    vars_sym = [x4, x3, x2, x1]
    
    for i in range(4):
        # SymPy учитывает dontcares для оптимального доопределения "0" или "1"
        minimized = SOPform(vars_sym, minterms[i], dontcares)
        print(f"y{4-i} минимизированная функция: {minimized}")

if __name__ == "__main__":
    # Запуск 1 задания (можно передать "ОДС-3" или "ОДВ-3")
    task1_3input_device("ОДВ-3")
    
    # Запуск 2 задания (передайте свой вариант n, например n=5)
    task2_code_converter(n_variant=3)