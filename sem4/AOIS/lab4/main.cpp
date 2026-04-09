#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <set>
#include <sstream>

using namespace std;

// ============================================================
//  Вспомогательные утилиты
// ============================================================
string decToBinary(int n, int bits) {
    string r = "";
    for (int i = bits - 1; i >= 0; i--)
        r += ((n >> i) & 1) ? '1' : '0';
    return r;
}

bool canCombine(const string& a, const string& b) {
    int diff = 0;
    for (size_t i = 0; i < a.size(); i++) {
        if (a[i] != b[i]) {
            if (a[i] == '-' || b[i] == '-') return false;
            diff++;
        }
    }
    return diff == 1;
}

string combineImpl(const string& a, const string& b) {
    string r = a;
    for (size_t i = 0; i < a.size(); i++)
        if (a[i] != b[i]) r[i] = '-';
    return r;
}

bool covers(const string& impl, int set_val, int num_vars) {
    for (int b = 0; b < num_vars; b++) {
        if (impl[b] == '-') continue;
        int bit = (set_val >> (num_vars - 1 - b)) & 1;
        if (impl[b] == '0' && bit != 0) return false;
        if (impl[b] == '1' && bit != 1) return false;
    }
    return true;
}

// Строковое представление импликанты КНФ: '0'->xi, '1'->!xi, '-'->skip
string implToKNF(const string& impl, int num_vars) {
    string r = "";
    for (int i = 0; i < num_vars; i++) {
        if (impl[i] == '-') continue;
        if (!r.empty()) r += " + ";
        if (impl[i] == '1') r += "!x" + to_string(i + 1);
        else                 r += "x"  + to_string(i + 1);
    }
    return r.empty() ? "0" : "(" + r + ")";
}

// ============================================================
//  Выбор существенных импликант (таблица покрытия)
// ============================================================
vector<string> selectEssential(const vector<string>& implicants,
                                const vector<int>& sets, int num_vars) {
    int n = (int)sets.size();
    vector<bool> covered(n, false);
    vector<bool> used(implicants.size(), false);
    vector<string> result;

    // 1) существенные импликанты
    for (int si = 0; si < n; si++) {
        int only = -1;
        for (size_t ii = 0; ii < implicants.size(); ii++) {
            if (covers(implicants[ii], sets[si], num_vars)) {
                if (only == -1) only = (int)ii;
                else { only = -2; break; }
            }
        }
        if (only >= 0 && !used[only]) {
            used[only] = true;
            result.push_back(implicants[only]);
            for (int k = 0; k < n; k++)
                if (covers(implicants[only], sets[k], num_vars)) covered[k] = true;
        }
    }
    // 2) жадно добираем непокрытые
    bool progress = true;
    while (progress) {
        progress = false;
        bool any = false;
        for (bool c : covered) if (!c) { any = true; break; }
        if (!any) break;
        int best = -1, bestCnt = 0;
        for (size_t ii = 0; ii < implicants.size(); ii++) {
            if (used[ii]) continue;
            int cnt = 0;
            for (int k = 0; k < n; k++)
                if (!covered[k] && covers(implicants[ii], sets[k], num_vars)) cnt++;
            if (cnt > bestCnt) { bestCnt = cnt; best = (int)ii; }
        }
        if (best >= 0) {
            used[best] = true;
            result.push_back(implicants[best]);
            for (int k = 0; k < n; k++)
                if (covers(implicants[best], sets[k], num_vars)) covered[k] = true;
            progress = true;
        }
    }
    return result.empty() ? implicants : result;
}

// ============================================================
//  Минимизация КНФ (все три метода → одна функция selectEssential)
// ============================================================

// Сокращённая форма (первый этап склейки)
vector<string> reduceKNF(const vector<int>& zero_sets, int num_vars) {
    vector<string> implicants;
    set<string> seen;
    for (size_t i = 0; i < zero_sets.size(); i++) {
        for (size_t j = i + 1; j < zero_sets.size(); j++) {
            string a = decToBinary(zero_sets[i], num_vars);
            string b = decToBinary(zero_sets[j], num_vars);
            if (canCombine(a, b)) {
                string c = combineImpl(a, b);
                if (!seen.count(c)) { seen.insert(c); implicants.push_back(c); }
            }
        }
    }
    if (implicants.empty())
        for (int s : zero_sets) implicants.push_back(decToBinary(s, num_vars));
    return implicants;
}

// Квайн-Мак-Класки: итеративная склейка → таблица покрытия
vector<string> quineMcKNF(const vector<int>& zero_sets, int num_vars) {
    vector<string> current;
    for (int s : zero_sets) current.push_back(decToBinary(s, num_vars));

    vector<string> all_prime;
    bool changed = true;
    while (changed) {
        changed = false;
        vector<string> next;
        vector<bool> used(current.size(), false);
        for (size_t i = 0; i < current.size(); i++)
            for (size_t j = i+1; j < current.size(); j++)
                if (canCombine(current[i], current[j])) {
                    string c = combineImpl(current[i], current[j]);
                    if (find(next.begin(), next.end(), c) == next.end()) next.push_back(c);
                    used[i] = used[j] = true;
                    changed = true;
                }
        for (size_t i = 0; i < current.size(); i++)
            if (!used[i] && find(all_prime.begin(), all_prime.end(), current[i]) == all_prime.end())
                all_prime.push_back(current[i]);
        current = next;
    }
    for (auto& c : current)
        if (find(all_prime.begin(), all_prime.end(), c) == all_prime.end())
            all_prime.push_back(c);

    return selectEssential(all_prime, zero_sets, num_vars);
}

// ============================================================
//  Вычисление КНФ на наборе
// ============================================================
int evalKNF(const vector<string>& impl, int set_val, int num_vars) {
    for (auto& s : impl) {
        bool zero = true;
        for (int b = 0; b < num_vars; b++) {
            if (s[b] == '-') continue;  // переменная исключена — пропускаем
            int bit = (set_val >> (num_vars - 1 - b)) & 1;
            if (s[b] == '0' && bit != 0) { zero = false; break; }
            if (s[b] == '1' && bit != 1) { zero = false; break; }
        }
        if (zero) return 0;
    }
    return 1;
}

// ============================================================
//  Печать таблицы истинности с проверкой
// ============================================================
void printTruthTable(const vector<string>& impl, const vector<int>& one_sets,
                     int num_vars, const string& method) {
    int total = 1 << num_vars;
    cout << "\n  Tablitsa istinnosti (" << method << "):\n";
    cout << "  +";
    for (int v = 0; v < num_vars; v++) cout << "----+";
    cout << "--------+--------+\n";
    cout << "  |";
    for (int v = 1; v <= num_vars; v++) cout << " x" << v << " |";
    cout << " f(isx) | f(KNF) |\n";
    cout << "  +";
    for (int v = 0; v < num_vars; v++) cout << "----+";
    cout << "--------+--------+\n";

    bool ok = true;
    for (int s = 0; s < total; s++) {
        int f_orig = find(one_sets.begin(), one_sets.end(), s) != one_sets.end() ? 1 : 0;
        int f_knf  = evalKNF(impl, s, num_vars);
        bool match = (f_orig == f_knf);
        if (!match) ok = false;
        cout << "  |";
        for (int b = num_vars - 1; b >= 0; b--)
            cout << "  " << ((s >> b) & 1) << " |";
        cout << "   " << f_orig << "    |   " << f_knf << "    |";
        if (!match) cout << " !!!";
        cout << "\n";
    }
    cout << "  +";
    for (int v = 0; v < num_vars; v++) cout << "----+";
    cout << "--------+--------+\n";
    cout << "  Proverka: " << (ok ? "OK" : "OSHIBKA") << "\n";
}

void sep() {
    cout << "\n";
    for (int i = 0; i < 70; i++) cout << "=";
    cout << "\n";
}

// ============================================================
//  ОДС-3: таблица истинности сумматора
// ============================================================
struct SumResult { int s, p; };  // s - сумма, p - перенос

SumResult odc3(int x1, int x2, int x3) {
    int total = x1 + x2 + x3;
    return { total % 2, total / 2 };
}

// ============================================================
//  ГЛАВНАЯ ПРОГРАММА
// ============================================================
int main() {
    const int NUM_VARS = 3;

    sep();
    cout << "  LABORATORNAYA RABOTA #4: SINTEZ ODS-3 (SKNF)\n";
    sep();

    // 1. Таблица истинности ОДС-3
    cout << "\n1. TABLITSA ISTINNOSTI ODS-3\n";
    cout << "  (X1 - slagaemoe 1, X2 - slagaemoe 2, X3 - perenos vhoda)\n";
    cout << "  (Si - cifra summy, Pi+1 - perenos vyhoda)\n\n";
    cout << "  +----+----+----+----+------+\n";
    cout << "  | X1 | X2 | X3 | Si |Pi+1  |\n";
    cout << "  +----+----+----+----+------+\n";

    vector<int> s_ones, s_zeros;   // наборы где Si=1 и Si=0
    vector<int> p_ones, p_zeros;   // наборы где Pi+1=1 и Pi+1=0

    for (int set = 0; set < 8; set++) {
        int x1 = (set >> 2) & 1;
        int x2 = (set >> 1) & 1;
        int x3 =  set       & 1;
        auto res = odc3(x1, x2, x3);
        cout << "  |  " << x1 << " |  " << x2 << " |  " << x3
             << " |  " << res.s << " |   " << res.p << "    |\n";
        if (res.s == 1) s_ones.push_back(set);  else s_zeros.push_back(set);
        if (res.p == 1) p_ones.push_back(set);  else p_zeros.push_back(set);
    }
    cout << "  +----+----+----+----+------+\n";

    // 2. СКНФ
    cout << "\n2. SKNF (nabori s nulyami):\n";
    cout << "  Si   = 0 na naborah: ";
    for (int s : s_zeros) cout << s << " ";
    cout << "\n  Pi+1 = 0 na naborah: ";
    for (int s : p_zeros) cout << s << " ";
    cout << "\n";

    // Формируем СКНФ строки для вывода
    auto printSKNF = [&](const vector<int>& zero_sets, const string& fname) {
        cout << "\n  " << fname << " SKNF:\n  f = ";
        for (size_t i = 0; i < zero_sets.size(); i++) {
            int s = zero_sets[i];
            string r = "";
            for (int b = NUM_VARS - 1; b >= 0; b--) {
                if (!r.empty()) r += " + ";
                int bit = (s >> b) & 1;
                r += (bit == 0) ? "x" + to_string(NUM_VARS - b) : "!x" + to_string(NUM_VARS - b);
            }
            cout << "(" << r << ")";
            if (i + 1 < zero_sets.size()) cout << " * ";
        }
        cout << "\n";
    };
    printSKNF(s_zeros, "Si");
    printSKNF(p_zeros, "Pi+1");

    // 3. Минимизация тремя методами
    auto doMinimize = [&](const vector<int>& zero_sets, const vector<int>& one_sets,
                          const string& fname) {
        sep();
        cout << "  MINIMIZATSIYA: " << fname << "\n";
        sep();

        // Метод 1: расчётный
        auto r1 = selectEssential(reduceKNF(zero_sets, NUM_VARS), zero_sets, NUM_VARS);
        cout << "\n[Metod 1 - Raschetniy]\n  f = ";
        for (size_t i = 0; i < r1.size(); i++) {
            cout << implToKNF(r1[i], NUM_VARS);
            if (i + 1 < r1.size()) cout << " * ";
        }
        cout << "\n";
        printTruthTable(r1, one_sets, NUM_VARS, "Raschetniy");

        // Метод 2: Квайн-Мак-Класки
        auto r2 = quineMcKNF(zero_sets, NUM_VARS);
        cout << "\n[Metod 2 - Kvayn-Mak-Klaski]\n  f = ";
        for (size_t i = 0; i < r2.size(); i++) {
            cout << implToKNF(r2[i], NUM_VARS);
            if (i + 1 < r2.size()) cout << " * ";
        }
        cout << "\n";
        printTruthTable(r2, one_sets, NUM_VARS, "Kvayn-Mak-Klaski");

        // Метод 3: Вейча-Карно (те же импликанты что расчётный — один проход)
        auto r3 = r1;
        cout << "\n[Metod 3 - Veycha-Karno]\n";
        cout << "  Karta (nulli):\n";
        cout << "  x1\\x2x3 | 00 | 01 | 11 | 10\n";
        cout << "  --------+----+----+----+----\n";
        for (int x1 = 0; x1 < 2; x1++) {
            cout << "     " << x1 << "    |";
            int order[] = {0, 1, 3, 2}; // порядок Грея
            for (int idx : order) {
                int x2 = (idx >> 1) & 1, x3 = idx & 1;
                int set = x1 * 4 + x2 * 2 + x3;
                int val = find(zero_sets.begin(), zero_sets.end(), set) != zero_sets.end() ? 0 : 1;
                cout << "  " << val << " |";
            }
            cout << "\n";
        }
        cout << "  f = ";
        for (size_t i = 0; i < r3.size(); i++) {
            cout << implToKNF(r3[i], NUM_VARS);
            if (i + 1 < r3.size()) cout << " * ";
        }
        cout << "\n";
        printTruthTable(r3, one_sets, NUM_VARS, "Veycha-Karno");

        // Сравнение
        bool same12 = (r1 == r2), same23 = (r2 == r3);
        cout << "\n  Sravnenie: ";
        cout << (same12 && same23 ? "VSE METODY SOVPALI" : "RASHOZHDENIYA");
        cout << "\n  TKNF: f = ";
        for (size_t i = 0; i < r1.size(); i++) {
            cout << implToKNF(r1[i], NUM_VARS);
            if (i + 1 < r1.size()) cout << " * ";
        }
        cout << "\n";

        return r1;
    };

    auto tknf_s = doMinimize(s_zeros, s_ones, "Si (cifra summy)");
    auto tknf_p = doMinimize(p_zeros, p_ones, "Pi+1 (perenos vyhoda)");

    // 4. Устройство с несколькими выходами
    sep();
    cout << "  SINTEZ KAK USTROYSTVO S NESKOLKIMI VYHODAMI\n";
    sep();
    cout << "\n  Sravnim SKNF funktsiy Si i Pi+1:\n";
    cout << "  Nulli Si:   ";
    for (int s : s_zeros) cout << s << " ";
    cout << "\n  Nulli Pi+1: ";
    for (int s : p_zeros) cout << s << " ";

    // Общие нули
    vector<int> common;
    for (int s : s_zeros)
        if (find(p_zeros.begin(), p_zeros.end(), s) != p_zeros.end())
            common.push_back(s);
    cout << "\n  Obschie nulli: ";
    for (int s : common) cout << s << " ";
    cout << "\n";

    // 5. Итог
    sep();
    cout << "  ITOGOVYE FORMULY\n";
    sep();
    cout << "\n  Si   TKNF = ";
    for (size_t i = 0; i < tknf_s.size(); i++) {
        cout << implToKNF(tknf_s[i], NUM_VARS);
        if (i + 1 < tknf_s.size()) cout << " * ";
    }
    cout << "\n  Pi+1 TKNF = ";
    for (size_t i = 0; i < tknf_p.size(); i++) {
        cout << implToKNF(tknf_p[i], NUM_VARS);
        if (i + 1 < tknf_p.size()) cout << " * ";
    }

    // Оценка оборудования
    cout << "\n\n  Otsenka oborudovaniya (razdelnaya realizatsiya):\n";
    // Считаем литералы
    set<string> not_gates;
    int or2 = 0, or3 = 0, and_inputs = 0;
    auto countGates = [&](const vector<string>& impl) {
        for (auto& s : impl) {
            int lits = 0;
            for (int i = 0; i < NUM_VARS; i++) {
                if (s[i] == '-') continue;
                if (s[i] == '1') not_gates.insert("x" + to_string(i+1));
                lits++;
            }
            if (lits == 2) or2++;
            else if (lits == 3) or3++;
        }
        and_inputs += (int)impl.size();
    };
    countGates(tknf_s);
    countGates(tknf_p);
    cout << "  NOT: " << not_gates.size() << "\n";
    cout << "  OR-2: " << or2 << "\n";
    cout << "  OR-3: " << or3 << "\n";
    cout << "  AND (vhodov): " << and_inputs << "\n";

    sep();
    cout << "  Programma zavershila rabotu uspeshno.\n";
    sep();
    return 0;
}