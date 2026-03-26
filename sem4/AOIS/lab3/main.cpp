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

    vector<string> calculateMethodSDNF() {
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

        if (implicants.empty()) {
            for (int s : sdnf_sets) {
                implicants.push_back(decToBinary(s, num_vars));
            }
        }

        return implicants;
    }

    vector<string> calculateMethodSKNF() {
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

        if (implicants.empty()) {
            for (int s : sknf_sets) {
                implicants.push_back(decToBinary(s, num_vars));
            }
        }

        return implicants;
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
        
        // Таблица покрытия - выбираем минимальный набор
        vector<string> result;
        vector<bool> covered(sdnf_sets.size(), false);
        
        // Ищем существенно необходимые импликанты
        for (const string& impl : all_prime) {
            vector<int> covers_list;
            for (size_t i = 0; i < sdnf_sets.size(); i++) {
                if (covers(impl, sdnf_sets[i])) {
                    covers_list.push_back(i);
                }
            }
            
            // Проверяем, покрывает ли эта импликанта хотя бы один непокрытый набор
            bool has_uncovered = false;
            for (int idx : covers_list) {
                if (!covered[idx]) {
                    has_uncovered = true;
                    break;
                }
            }
            
            if (has_uncovered) {
                result.push_back(impl);
                for (int idx : covers_list) {
                    covered[idx] = true;
                }
            }
        }
        
        return result.empty() ? all_prime : result;
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
        
        // Таблица покрытия
        vector<string> result;
        vector<bool> covered(sknf_sets.size(), false);
        
        for (const string& impl : all_prime) {
            vector<int> covers_list;
            for (size_t i = 0; i < sknf_sets.size(); i++) {
                if (covers(impl, sknf_sets[i])) {
                    covers_list.push_back(i);
                }
            }
            
            bool has_uncovered = false;
            for (int idx : covers_list) {
                if (!covered[idx]) {
                    has_uncovered = true;
                    break;
                }
            }
            
            if (has_uncovered) {
                result.push_back(impl);
                for (int idx : covers_list) {
                    covered[idx] = true;
                }
            }
        }
        
        return result.empty() ? all_prime : result;
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
            if (!result.empty()) result += " + ";
            if (impl[i] == '1') {
                result += "!x" + to_string(i + 1);
            } else if (impl[i] == '0') {
                result += "x" + to_string(i + 1);
            } else {
                continue;
            }
        }
        return result.empty() ? "0" : "(" + result + ")";
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