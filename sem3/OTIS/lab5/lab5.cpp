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
    int experts, alts;

    cout << "Введите число экспертов: ";
    cin >> experts;

    cout << "Введите число альтернатив: ";
    cin >> alts;

    vector<vector<int>> ranks(experts, vector<int>(alts));

    cout << "\nВведите ранжирование экспертов.\n"
         << "Каждая строка — ранжирование одного эксперта от лучшей к худшей.\n"
         << "Альтернативы нумеруются с 0.\n\n";

    for (int e = 0; e < experts; e++) {
        cout << "Эксперт " << e + 1 << ": ";
        for (int a = 0; a < alts; a++) {
            cin >> ranks[e][a];
        }
    }

    int w = condorcetWinner(ranks, experts, alts);

    if (w == -1)
        cout << "\nПобедитель Кондорсе отсутствует.\n";
    else
        cout << "\nПобедитель Кондорсе: альтернатива " << w << "\n";

    return 0;
}
