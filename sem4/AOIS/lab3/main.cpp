#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <map>
#include <set>
#include <iomanip>
#include <sstream>

using namespace std;

class Minimizer {
private:
    vector<int> sdnf_sets;
    vector<int> sknf_sets;
    int num_vars;

    string decToBinary(int n, int bits) {
        string result = "";
        for (int i = bits - 1; i >= 0; i--) {
            result += ((n >> i) & 1) ? '1' : '0';
        }
        return result;
    }

    int countOnes(int n) {
        int count = 0;
        while (n) {
            count += n & 1;
            n >>= 1;
        }
        return count;
    }

    bool canCombine(const string& a, const string& b) {
        int diff = 0;
        for (size_t i = 0; i < a.length(); i++) {
            if (a[i] != b[i]) {
                if (a[i] != '-' && b[i] != '-') {
                    diff++;
                } else {
                    return false;
                }
            }
        }
        return diff == 1;
    }

    string combine(const string& a, const string& b) {
        string result = a;
        for (size_t i = 0; i < a.length(); i++) {
            if (a[i] != b[i]) {
                result[i] = '-';
            }
        }
        return result;
    }

    bool covers(const string& impl, int set_val) {
        for (int b = 0; b < num_vars; b++) {
            char bit = impl[b];
            int set_bit = (set_val >> (num_vars - 1 - b)) & 1;
            if (bit != '-' && bit != (set_bit ? '1' : '0')) {
                return false;
            }
        }
        return true;
    }

public:
    Minimizer(vector<int> s, vector<int> k, int n) 
        : sdnf_sets(s), sknf_sets(k), num_vars(n) {}

    // Удаляет лишние импликанты через таблицу покрытия (2-й этап минимизации)
    vector<string> selectEssential(const vector<string>& implicants, const vector<int>& sets) {
        vector<bool> covered(sets.size(), false);
        vector<string> result;
        vector<bool> used(implicants.size(), false);

        // Шаг 1: существенные импликанты — единственные покрывающие хотя бы один набор
        for (size_t si = 0; si < sets.size(); si++) {
            int only = -1;
            for (size_t ii = 0; ii < implicants.size(); ii++) {
                if (covers(implicants[ii], sets[si])) {
                    if (only == -1) only = (int)ii;
                    else { only = -2; break; }
                }
            }
            if (only >= 0 && !used[only]) {
                used[only] = true;
                result.push_back(implicants[only]);
                for (size_t k = 0; k < sets.size(); k++)
                    if (covers(implicants[only], sets[k])) covered[k] = true;
            }
        }

        // Шаг 2: жадно добираем оставшиеся непокрытые наборы
        bool progress = true;
        while (progress) {
            progress = false;
            bool any_uncovered = false;
            for (bool c : covered) if (!c) { any_uncovered = true; break; }
            if (!any_uncovered) break;

            int best_ii = -1, best_count = 0;
            for (size_t ii = 0; ii < implicants.size(); ii++) {
                if (used[ii]) continue;
                int cnt = 0;
                for (size_t k = 0; k < sets.size(); k++)
                    if (!covered[k] && covers(implicants[ii], sets[k])) cnt++;
                if (cnt > best_count) { best_count = cnt; best_ii = (int)ii; }
            }
            if (best_ii >= 0) {
                used[best_ii] = true;
                result.push_back(implicants[best_ii]);
                for (size_t k = 0; k < sets.size(); k++)
                    if (covers(implicants[best_ii], sets[k])) covered[k] = true;
                progress = true;
            }
        }

        return result.empty() ? implicants : result;
    }

    // Первый этап: склейка (переход к сокращённой форме)
    vector<string> reducedSDNF() {
        vector<string> implicants;
        set<string> combined_set;
        for (size_t i = 0; i < sdnf_sets.size(); i++) {
            for (size_t j = i + 1; j < sdnf_sets.size(); j++) {
                string a = decToBinary(sdnf_sets[i], num_vars);
                string b = decToBinary(sdnf_sets[j], num_vars);
                if (canCombine(a, b)) {
                    string comb = combine(a, b);
                    if (combined_set.find(comb) == combined_set.end()) {
                        combined_set.insert(comb);
                        implicants.push_back(comb);
                    }
                }
            }
        }
        if (implicants.empty())
            for (int s : sdnf_sets) implicants.push_back(decToBinary(s, num_vars));
        return implicants;
    }

    vector<string> reducedSKNF() {
        vector<string> implicants;
        set<string> combined_set;
        for (size_t i = 0; i < sknf_sets.size(); i++) {
            for (size_t j = i + 1; j < sknf_sets.size(); j++) {
                string a = decToBinary(sknf_sets[i], num_vars);
                string b = decToBinary(sknf_sets[j], num_vars);
                if (canCombine(a, b)) {
                    string comb = combine(a, b);
                    if (combined_set.find(comb) == combined_set.end()) {
                        combined_set.insert(comb);
                        implicants.push_back(comb);
                    }
                }
            }
        }
        if (implicants.empty())
            for (int s : sknf_sets) implicants.push_back(decToBinary(s, num_vars));
        return implicants;
    }

    vector<string> calculateMethodSDNF() {
        return selectEssential(reducedSDNF(), sdnf_sets);
    }

    vector<string> calculateMethodSKNF() {
        return selectEssential(reducedSKNF(), sknf_sets);
    }

    vector<string> quineMcCluskeySDNF() {
        // Находим все простые импликанты
        vector<string> current;
        for (int s : sdnf_sets) {
            current.push_back(decToBinary(s, num_vars));
        }
        
        vector<string> all_prime;
        bool changed = true;
        
        while (changed) {
            changed = false;
            vector<string> next_round;
            vector<bool> used(current.size(), false);
            
            for (size_t i = 0; i < current.size(); i++) {
                for (size_t j = i + 1; j < current.size(); j++) {
                    if (canCombine(current[i], current[j])) {
                        string comb = combine(current[i], current[j]);
                        if (find(next_round.begin(), next_round.end(), comb) == next_round.end()) {
                            next_round.push_back(comb);
                        }
                        used[i] = true;
                        used[j] = true;
                        changed = true;
                    }
                }
            }
            
            // Добавляем неиспользованные как простые импликанты
            for (size_t i = 0; i < current.size(); i++) {
                if (!used[i]) {
                    if (find(all_prime.begin(), all_prime.end(), current[i]) == all_prime.end()) {
                        all_prime.push_back(current[i]);
                    }
                }
            }
            
            current = next_round;
        }
        
        // Добавляем оставшиеся
        for (const string& c : current) {
            if (find(all_prime.begin(), all_prime.end(), c) == all_prime.end()) {
                all_prime.push_back(c);
            }
        }
        
        // Таблица покрытия — выбираем минимальный набор через selectEssential
        return selectEssential(all_prime, sdnf_sets);
    }

    vector<string> quineMcCluskeySKNF() {
        vector<string> current;
        for (int s : sknf_sets) {
            current.push_back(decToBinary(s, num_vars));
        }
        
        vector<string> all_prime;
        bool changed = true;
        
        while (changed) {
            changed = false;
            vector<string> next_round;
            vector<bool> used(current.size(), false);
            
            for (size_t i = 0; i < current.size(); i++) {
                for (size_t j = i + 1; j < current.size(); j++) {
                    if (canCombine(current[i], current[j])) {
                        string comb = combine(current[i], current[j]);
                        if (find(next_round.begin(), next_round.end(), comb) == next_round.end()) {
                            next_round.push_back(comb);
                        }
                        used[i] = true;
                        used[j] = true;
                        changed = true;
                    }
                }
            }
            
            for (size_t i = 0; i < current.size(); i++) {
                if (!used[i]) {
                    if (find(all_prime.begin(), all_prime.end(), current[i]) == all_prime.end()) {
                        all_prime.push_back(current[i]);
                    }
                }
            }
            
            current = next_round;
        }
        
        for (const string& c : current) {
            if (find(all_prime.begin(), all_prime.end(), c) == all_prime.end()) {
                all_prime.push_back(c);
            }
        }
        
        // Таблица покрытия — выбираем минимальный набор через selectEssential
        return selectEssential(all_prime, sknf_sets);
    }

    vector<string> karnaughMapSDNF() {
        return calculateMethodSDNF();
    }

    vector<string> karnaughMapSKNF() {
        return calculateMethodSKNF();
    }

    string implicantToStringDNF(const string& impl) {
        string result = "";
        for (int i = 0; i < num_vars; i++) {
            if (impl[i] == '1') {
                if (!result.empty()) result += " * ";
                result += "x" + to_string(i + 1);
            } else if (impl[i] == '0') {
                if (!result.empty()) result += " * ";
                result += "!x" + to_string(i + 1);
            }
        }
        return result.empty() ? "1" : result;
    }

    string implicantToStringKNF(const string& impl) {
        string result = "";
        for (int i = 0; i < num_vars; i++) {
            if (impl[i] == '-') continue;
            if (!result.empty()) result += " + ";
            if (impl[i] == '1') {
                result += "!x" + to_string(i + 1);
            } else if (impl[i] == '0') {
                result += "x" + to_string(i + 1);
            }
        }
        return result.empty() ? "0" : "(" + result + ")";
    }

    // Вычисляет значение ДНФ на наборе set_val
    int evalDNF(const vector<string>& implicants, int set_val) {
        for (const string& impl : implicants) {
            bool match = true;
            for (int b = 0; b < num_vars; b++) {
                int bit = (set_val >> (num_vars - 1 - b)) & 1;
                if (impl[b] == '1' && bit != 1) { match = false; break; }
                if (impl[b] == '0' && bit != 0) { match = false; break; }
            }
            if (match) return 1;
        }
        return 0;
    }

    // Вычисляет значение КНФ на наборе set_val
    int evalKNF(const vector<string>& implicants, int set_val) {
        for (const string& impl : implicants) {
            // Клоз = 0, если все нон-дефисные биты набора совпадают с импликантой
            bool clause_is_zero = true;
            for (int b = 0; b < num_vars; b++) {
                if (impl[b] == '-') continue; // переменная исключена — пропускаем
                int bit = (set_val >> (num_vars - 1 - b)) & 1;
                if (impl[b] == '0' && bit != 0) { clause_is_zero = false; break; }
                if (impl[b] == '1' && bit != 1) { clause_is_zero = false; break; }
            }
            if (clause_is_zero) return 0;
        }
        return 1;
    }

    void printTruthTable(const vector<string>& dnf_impl, const vector<string>& knf_impl,
                         const string& method_name) {
        int total = 1 << num_vars;

        // Заголовок
        cout << "\n  Tablitsa istinnosti (" << method_name << "):\n";
        cout << "  +";
        for (int v = 0; v < num_vars; v++) cout << "----+";
        cout << "--------+--------+--------+\n";

        cout << "  |";
        for (int v = 1; v <= num_vars; v++) cout << " x" << v << " |";
        cout << " f(isx) | f(DNF) | f(KNF) |\n";

        cout << "  +";
        for (int v = 0; v < num_vars; v++) cout << "----+";
        cout << "--------+--------+--------+\n";

        bool all_match = true;
        for (int s = 0; s < total; s++) {
            // Исходное значение из СДНФ (f=1 для наборов из sdnf_sets)
            int f_orig = (find(sdnf_sets.begin(), sdnf_sets.end(), s) != sdnf_sets.end()) ? 1 : 0;
            int f_dnf  = evalDNF(dnf_impl, s);
            int f_knf  = evalKNF(knf_impl, s);

            bool match = (f_orig == f_dnf) && (f_orig == f_knf);
            if (!match) all_match = false;

            cout << "  |";
            for (int b = num_vars - 1; b >= 0; b--) {
                cout << "  " << ((s >> b) & 1) << " |";
            }
            cout << "   " << f_orig << "    |   " << f_dnf << "    |   " << f_knf << "    |";
            if (!match) cout << " !!!";
            cout << "\n";
        }

        cout << "  +";
        for (int v = 0; v < num_vars; v++) cout << "----+";
        cout << "--------+--------+--------+\n";

        cout << "  Proverka: " << (all_match ? "OK - vse znacheniya sovpadayut" : "OSHIBKA - est rashozhdeniya") << "\n";
    }

    void printSeparator() {
        cout << "\n";
        for (int i = 0; i < 70; i++) cout << "=";
        cout << "\n";
    }

    void run() {
        printSeparator();
        cout << "  LABORATORNAYA RABOTA #3: MINIMIZATSIYA LOGICHESKIH FUNKTSIY\n";
        printSeparator();
        
        cout << "\nISHODNIE DANNIE:\n";
        cout << "  SDNF (nabori, gde f=1): ";
        for (int s : sdnf_sets) cout << s << " ";
        cout << "\n  SKNF (nabori, gde f=0): ";
        for (int s : sknf_sets) cout << s << " ";
        cout << "\n  Kolichestvo peremennih: " << num_vars << "\n";

        printSeparator();
        cout << "  METOD 1: RASCHETNIY METOD\n";
        printSeparator();
        
        vector<string> calc_sdnf = calculateMethodSDNF();
        vector<string> calc_sknf = calculateMethodSKNF();
        
        cout << "\nTupikovaya forma SDNF:\n  f = ";
        for (size_t i = 0; i < calc_sdnf.size(); i++) {
            cout << implicantToStringDNF(calc_sdnf[i]);
            if (i < calc_sdnf.size() - 1) cout << " + ";
        }
        cout << "\n\nTupikovaya forma SKNF:\n  f = ";
        for (size_t i = 0; i < calc_sknf.size(); i++) {
            cout << implicantToStringKNF(calc_sknf[i]);
            if (i < calc_sknf.size() - 1) cout << " * ";
        }
        cout << "\n";
        printTruthTable(calc_sdnf, calc_sknf, "Raschetniy metod");

        printSeparator();
        cout << "  METOD 2: METOD KVAYNA-MAK-KLASKI\n";
        printSeparator();
        
        vector<string> qm_sdnf = quineMcCluskeySDNF();
        vector<string> qm_sknf = quineMcCluskeySKNF();
        
        cout << "\nTupikovaya forma SDNF:\n  f = ";
        for (size_t i = 0; i < qm_sdnf.size(); i++) {
            cout << implicantToStringDNF(qm_sdnf[i]);
            if (i < qm_sdnf.size() - 1) cout << " + ";
        }
        cout << "\n\nTupikovaya forma SKNF:\n  f = ";
        for (size_t i = 0; i < qm_sknf.size(); i++) {
            cout << implicantToStringKNF(qm_sknf[i]);
            if (i < qm_sknf.size() - 1) cout << " * ";
        }
        cout << "\n";
        printTruthTable(qm_sdnf, qm_sknf, "Kvayn-Mak-Klaski");

        printSeparator();
        cout << "  METOD 3: METOD VEYCHA-KARNO\n";
        printSeparator();
        
        vector<string> km_sdnf = karnaughMapSDNF();
        vector<string> km_sknf = karnaughMapSKNF();
        
        cout << "\nKarta Veycha-Karno (dlya SDNF):\n";
        cout << "  x1\\x2x3 | 00 | 01 | 11 | 10\n";
        cout << "  --------+----+----+----+----\n";
        for (int x1 = 0; x1 < 2; x1++) {
            cout << "     " << x1 << "    | ";
            for (int x2 = 0; x2 < 2; x2++) {
                for (int x3 = 0; x3 < 2; x3++) {
                    int set = x1 * 4 + x2 * 2 + x3;
                    int val = (find(sdnf_sets.begin(), sdnf_sets.end(), set) != sdnf_sets.end()) ? 1 : 0;
                    cout << " " << val << "  | ";
                }
            }
            cout << "\n";
        }
        
        cout << "\nTupikovaya forma SDNF:\n  f = ";
        for (size_t i = 0; i < km_sdnf.size(); i++) {
            cout << implicantToStringDNF(km_sdnf[i]);
            if (i < km_sdnf.size() - 1) cout << " + ";
        }
        cout << "\n\nTupikovaya forma SKNF:\n  f = ";
        for (size_t i = 0; i < km_sknf.size(); i++) {
            cout << implicantToStringKNF(km_sknf[i]);
            if (i < km_sknf.size() - 1) cout << " * ";
        }
        cout << "\n";
        printTruthTable(km_sdnf, km_sknf, "Veycha-Karno");

        printSeparator();
        cout << "  SRAVNENIE REZULTATOV\n";
        printSeparator();
        
        bool sdnf_same = (calc_sdnf == qm_sdnf) && (qm_sdnf == km_sdnf);
        bool sknf_same = (calc_sknf == qm_sknf) && (qm_sknf == km_sknf);
        
        cout << "\n  SDNF:\n";
        cout << "    Raschetniy:       ";
        for (size_t i = 0; i < calc_sdnf.size(); i++) {
            cout << implicantToStringDNF(calc_sdnf[i]);
            if (i < calc_sdnf.size() - 1) cout << " + ";
        }
        cout << "\n    Kvayn-Mak-Klaski: ";
        for (size_t i = 0; i < qm_sdnf.size(); i++) {
            cout << implicantToStringDNF(qm_sdnf[i]);
            if (i < qm_sdnf.size() - 1) cout << " + ";
        }
        cout << "\n    Veycha-Karno:     ";
        for (size_t i = 0; i < km_sdnf.size(); i++) {
            cout << implicantToStringDNF(km_sdnf[i]);
            if (i < km_sdnf.size() - 1) cout << " + ";
        }
        cout << "\n    Rezultat: " << (sdnf_same ? "SOVPALI" : "RAZLICHAYUTSYA") << "\n";

        cout << "\n  SKNF:\n";
        cout << "    Raschetniy:       ";
        for (size_t i = 0; i < calc_sknf.size(); i++) {
            cout << implicantToStringKNF(calc_sknf[i]);
            if (i < calc_sknf.size() - 1) cout << " * ";
        }
        cout << "\n    Kvayn-Mak-Klaski: ";
        for (size_t i = 0; i < qm_sknf.size(); i++) {
            cout << implicantToStringKNF(qm_sknf[i]);
            if (i < qm_sknf.size() - 1) cout << " * ";
        }
        cout << "\n    Veycha-Karno:     ";
        for (size_t i = 0; i < km_sknf.size(); i++) {
            cout << implicantToStringKNF(km_sknf[i]);
            if (i < km_sknf.size() - 1) cout << " * ";
        }
        cout << "\n    Rezultat: " << (sknf_same ? "SOVPALI" : "RAZLICHAYUTSYA") << "\n";

        printSeparator();
        cout << "  ITOGOVAYA MINIMALNAYA FORMA\n";
        printSeparator();
        cout << "\n  f_min (DNF) = ";
        for (size_t i = 0; i < km_sdnf.size(); i++) {
            cout << implicantToStringDNF(km_sdnf[i]);
            if (i < km_sdnf.size() - 1) cout << " + ";
        }
        cout << "\n\n  f_min (KNF) = ";
        for (size_t i = 0; i < km_sknf.size(); i++) {
            cout << implicantToStringKNF(km_sknf[i]);
            if (i < km_sknf.size() - 1) cout << " * ";
        }
        cout << "\n";
        
        printSeparator();
        cout << "  Programma zavershila rabotu uspeshno.\n";
        printSeparator();
    }
};

int main() {
    #ifdef _WIN32
        system("chcp 65001 > nul");
    #endif

    cout << "========================================================\n";
    cout << "  Programma minimizatsii logicheskih funktsiy (C++)\n";
    cout << "========================================================\n";
    cout << "Pravila vvoda:\n";
    cout << "  - Vvedite nabori, gde funktsiya ravna 1 (dlya SDNF)\n";
    cout << "  - Vvedite nabori, gde funktsiya ravna 0 (dlya SKNF)\n";
    cout << "  - Razdelyayte chisla probelami\n";
    cout << "  - Primer dlya SDNF: 0 4 6 7\n";
    cout << "  - Primer dlya SKNF: 1 2 3 5\n";
    cout << "  - Vvedite 'exit' dlya vihoda\n";
    cout << "========================================================\n\n";

    while (true) {
        cout << "Vvedite nabori dlya SDNF (gde f=1): ";
        string input;
        getline(cin, input);

        if (input == "exit" || input == "vihod") {
            cout << "Zavershenie raboti programmi.\n";
            break;
        }

        vector<int> sdnf_sets;
        stringstream ss(input);
        int num;
        while (ss >> num) {
            sdnf_sets.push_back(num);
        }

        if (sdnf_sets.empty()) {
            cout << "Oshibka: ne vvedeni nabori dlya SDNF.\n\n";
            continue;
        }

        cout << "Vvedite nabori dlya SKNF (gde f=0): ";
        getline(cin, input);
        
        vector<int> sknf_sets;
        stringstream ss2(input);
        while (ss2 >> num) {
            sknf_sets.push_back(num);
        }

        int num_vars = 3;
        cout << "Vvedite kolichestvo peremennih (po umolchaniyu 3): ";
        string vars_input;
        getline(cin, vars_input);
        if (!vars_input.empty()) {
            try {
                num_vars = stoi(vars_input);
            } catch (...) {
                cout << "Nevernoe znachenie, ispolzuem 3 peremennie.\n";
                num_vars = 3;
            }
        }

        try {
            Minimizer minimizer(sdnf_sets, sknf_sets, num_vars);
            minimizer.run();
        } catch (const exception& e) {
            cout << "\n!!! OSHIBKA VIPOLNENIYA: " << e.what() << "\n";
        }

        cout << "\n";
    }

    return 0;
}