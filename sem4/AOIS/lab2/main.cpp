#include <iostream>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <sstream>
#include <cctype>

using namespace std;

class LogicParser {
private:
    string expr;
    size_t pos;
    int x1, x2, x3;

    void skipSpaces() {
        while (pos < expr.length() && isspace(expr[pos])) pos++;
    }

    char peek() {
        skipSpaces();
        return (pos < expr.length()) ? expr[pos] : '\0';
    }

    char get() {
        skipSpaces();
        return (pos < expr.length()) ? expr[pos++] : '\0';
    }

    int parseFactor() {
        char c = peek();
        if (c == '!') {
            get();
            return !parseFactor();
        }
        if (c == '(') {
            get();
            int res = parseExpression();
            if (peek() == ')') get();
            return res;
        }
        if (c == 'x') {
            get();
            char num = get();
            if (num == '1') return x1;
            if (num == '2') return x2;
            if (num == '3') return x3;
            throw runtime_error("Nevernaya peremennaya");
        }
        if (c == '0' || c == '1') {
            get();
            return (c == '1') ? 1 : 0;
        }
        throw runtime_error("Oshibka sintaksisa");
    }

    int parseTerm() {
        int left = parseFactor();
        while (peek() == '&') {
            get();
            int right = parseFactor();
            left = left & right;
        }
        return left;
    }

    int parseExpression() {
        int left = parseTerm();
        while (peek() == '|') {
            get();
            int right = parseTerm();
            left = left | right;
        }
        return left;
    }

public:
    int evaluate(const string& expression, int v1, int v2, int v3) {
        this->expr = expression;
        this->pos = 0;
        this->x1 = v1;
        this->x2 = v2;
        this->x3 = v3;
        try {
            int res = parseExpression();
            return res;
        } catch (...) {
            return -1;
        }
    }
    
    bool validate(const string& expression) {
        try {
            evaluate(expression, 0, 0, 0);
            return true;
        } catch (...) {
            return false;
        }
    }
};

class LabSolver {
private:
    string formula;
    vector<int> truthTable;
    LogicParser parser;

    int getWeight(int setIndex) {
        return pow(2, 7 - setIndex);
    }

public:
    LabSolver(string f) : formula(f) {}

    void buildTruthTable() {
        truthTable.clear();
        cout << "\n--- Postroenie tablitsi istinnosti ---\n";
        cout << "No\t|x1\tx2\tx3\t| f\n";
        cout << "----------------------------------------\n";
        
        for (int i = 0; i < 8; i++) {
            int v1 = (i & 4) ? 1 : 0;
            int v2 = (i & 2) ? 1 : 0;
            int v3 = (i & 1) ? 1 : 0;

            int res = parser.evaluate(formula, v1, v2, v3);
            truthTable.push_back(res);

            cout << i << "\t|" << v1 << "\t" << v2 << "\t" << v3 << "\t| " << res << "\n";
        }
        cout << "----------------------------------------\n";
    }

    void generateSDNF() {
        cout << "\n--- Sovershennaya Dizyunktivnaya Normalnaya Forma (SDNF) ---\n";
        vector<int> sets;
        cout << "Nabori, gde f=1: ";
        for (int i = 0; i < 8; i++) {
            if (truthTable[i] == 1) {
                sets.push_back(i);
                cout << i << " ";
            }
        }
        cout << "\nChislovaya forma: f = V(" << join(sets) << ")\n";

        cout << "Analiticheskaya forma (konstituenti edinitsi):\n";
        if (sets.empty()) {
            cout << "f = 0\n";
        } else {
            for (size_t k = 0; k < sets.size(); k++) {
                int i = sets[k];
                int v1 = (i & 4) ? 1 : 0;
                int v2 = (i & 2) ? 1 : 0;
                int v3 = (i & 1) ? 1 : 0;
                
                cout << "\t";
                if (k > 0) cout << " + ";
                cout << "(";
                cout << (v1 ? "x1" : "!x1") << " & ";
                cout << (v2 ? "x2" : "!x2") << " & ";
                cout << (v3 ? "x3" : "!x3") << ")";
            }
            cout << "\n";
        }
    }

    void generateSKNF() {
        cout << "\n--- Sovershennaya Konyunktivnaya Normalnaya Forma (SKNF) ---\n";
        vector<int> sets;
        cout << "Nabori, gde f=0: ";
        for (int i = 0; i < 8; i++) {
            if (truthTable[i] == 0) {
                sets.push_back(i);
                cout << i << " ";
            }
        }
        cout << "\nChislovaya forma: f = ^(" << join(sets) << ")\n";

        cout << "Analiticheskaya forma (konstituenti nulya):\n";
        if (sets.empty()) {
            cout << "f = 1\n";
        } else {
            for (size_t k = 0; k < sets.size(); k++) {
                int i = sets[k];
                int v1 = (i & 4) ? 1 : 0;
                int v2 = (i & 2) ? 1 : 0;
                int v3 = (i & 1) ? 1 : 0;

                cout << "\t";
                if (k > 0) cout << " * ";
                cout << "(";
                cout << (v1 ? "!x1" : "x1") << " | ";
                cout << (v2 ? "!x2" : "x2") << " | ";
                cout << (v3 ? "!x3" : "x3") << ")";
            }
            cout << "\n";
        }
    }

    void calculateIndex() {
        cout << "\n--- Raschet indeksa funktsii ---\n";
        int index = 0;
        cout << "i = ";
        bool first = true;
        for (int i = 0; i < 8; i++) {
            if (truthTable[i] == 1) {
                int w = getWeight(i);
                if (!first) cout << " + ";
                cout << w << " (nabor " << i << ")";
                index += w;
                first = false;
            }
        }
        if (first) cout << "0";
        cout << "\nITOGO indeks i = " << index << "\n";
        cout << "Indeksnaya forma: f_" << index << "(x1, x2, x3)\n";
    }

    void run() {
        cout << "\n========================================================\n";
        cout << "  Laboratornaya rabota No2: Preobrazovanie logicheskikh funktsiy\n";
        cout << "  Variant: Vvod polzovatelem\n";
        cout << "========================================================\n";
        cout << "Iskhodnaya funktsiya: " << formula << "\n";

        buildTruthTable();
        generateSDNF();
        generateSKNF();
        calculateIndex();

        cout << "\n========================================================\n";
        cout <<  "Programma zavershila rabotu uspeshno.\n";
        cout << "========================================================\n";
    }

private:
    string join(const vector<int>& v) {
        stringstream ss;
        for (size_t i = 0; i < v.size(); ++i) {
            if (i != 0) ss << ", ";
            ss << v[i];
        }
        return ss.str();
    }
};

int main() {
    #ifdef _WIN32
        system("chcp 65001 > nul");
    #endif

    cout << "========================================================\n";
    cout << "  Programma preobrazovaniya logicheskikh funktsiy (C++)\n";
    cout << "========================================================\n";
    cout << "Pravila vvoda:\n";
    cout << "  - Peremennie: x1, x2, x3\n";
    cout << "  - Otritsanie (NOT): !\n";
    cout << "  - Konyunktsiya (AND): &\n";
    cout << "  - Dizyunktsiya (OR): |\n";
    cout << "  - Skobki: ( )\n";
    cout << "  - Primer: !((!x1 | !x2) & !(!x2 & !x3))\n";
    cout << "  - Vvedite 'exit' ili 'quit' dlya vivoda\n";
    cout << "========================================================\n\n";

    while (true) {
        cout << "Vvedite logicheskuyu funktsiyu: ";
        string formula;
        getline(cin, formula);

        if (formula == "exit" || formula == "quit" || formula == "vihod") {
            cout << "Zavershenie raboti programmi.\n";
            break;
        }

        if (formula.empty()) {
            cout << "Oshibka: Formula ne mozhet bit pustoy.\n\n";
            continue;
        }

        LogicParser validator;
        bool hasVariables = (formula.find("x1") != string::npos || 
                             formula.find("x2") != string::npos || 
                             formula.find("x3") != string::npos);
        
        if (!hasVariables) {
            cout << "Preduprezhdenie: V formule ne naydeno peremennih (x1, x2, x3).\n";
            cout << "Vipolnenie vse ravno budet prodolzheno...\n";
        }

        try {
            LabSolver solver(formula);
            solver.run();
        } catch (const exception& e) {
            cout << "\n!!! OSHIBKA VIPOLNENIYA: " << e.what() << "\n";
            cout << "Proverte pravilnost skobok i sintaksisa.\n\n";
            continue;
        }

        cout << "\n";
    }

    return 0;
}