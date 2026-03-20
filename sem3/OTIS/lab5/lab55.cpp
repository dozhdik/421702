#include <iostream>
#include <vector>
using namespace std;

int condorcetWinner(const vector<vector<int>>& ranks, int experts, int alts) {
    vector<vector<int>> pairwise(alts, vector<int>(alts, 0));

    for (int e = 0; e < experts; e++) {
        for (int i = 0; i < alts; i++) {
            for (int j = i + 1; j < alts; j++) {
                int ai = ranks[e][i];   
                int aj = ranks[e][j];  
                pairwise[ai][aj]++;
            }
        }
    }

    for (int a = 0; a < alts; a++) {
        bool winner = true;
        for (int b = 0; b < alts; b++) {
            if (a == b) continue;

            if (pairwise[a][b] <= pairwise[b][a]) {
                winner = false;
                break;
            }
        }
        if (winner) return a;
    }

    return -1;
}

int main() {
    int experts = 0, alts = 0; 
    int value, result;
    vector<vector<int>> ranks; 

    do {
        cout << "Выберите опцию:" << endl;
        cout << "\t1. Задать кол-во экспертов;" << endl;
        cout << "\t2. Задать число альтернатив;" << endl;
        cout << "\t3. Ввести ранжирование альтернатив;" << endl;
        cout << "\t4. Выбрать победителя;" << endl;
        cout << "\t0. Выход" << endl;
        cout << "Ваш выбор: ";
        cin >> value;

        switch (value) {
        case 1:
            cout << "Введите число экспертов: ";
            cin >> experts; 
            ranks.clear();
            break;

        case 2:
            cout << "Введите число альтернатив: ";
            cin >> alts;
            ranks.clear();
            break;

        case 3:
            if (experts <= 0 || alts <= 0) {
                cout << "Сначала задайте количество экспертов и альтернатив!" << endl;
                break;
            }

            ranks = vector<vector<int>>(experts, vector<int>(alts));

            cout << "\nВведите ранжирование экспертов.\n";
            cout << "Каждая строка — ранжирование одного эксперта от лучшей к худшей.\n";
            cout << "Альтернативы нумеруются с 0.\n\n";

            for (int e = 0; e < experts; e++) {
                cout << "Эксперт " << e + 1 << ": ";
                for (int a = 0; a < alts; a++) {
                    cin >> ranks[e][a];
                }
            }
            break;

        case 4:
            if (experts <= 0 || alts <= 0 || ranks.empty()) {
                cout << "Сначала задайте параметры и введите ранжирование!" << endl;
                break;
            }

            result = condorcetWinner(ranks, experts, alts);

            if (result == -1)
                cout << "\nПобедитель Кондорсе отсутствует.\n";
            else
                cout << "\nПобедитель Кондорсе: альтернатива " << result << "\n";
            break;

        case 0:
            cout << "Выход." << endl;
            break;

        default:
            cout << "\nНеверный выбор!\n";
            break;
        }

    } while (value != 0);

    return 0;
}