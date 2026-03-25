#include <iostream>
#include <string>
#include <cmath>
#include <iomanip>
#include <vector>
#include <sstream>
#include <algorithm>

using namespace std;

class NumberConverter {
private:
    int X1, X2;
    int bits;

public:
    NumberConverter(int x1, int x2, int b = 8) : X1(x1), X2(x2), bits(b) {}

    string decToBinary(int n, int b = 8) {
        if (n == 0) return string(b, '0');
        string result = "";
        int num = abs(n);
        while (num > 0) {
            result = (num % 2 == 0 ? "0" : "1") + result;
            num /= 2;
        }
        while (result.length() < b) {
            result = "0" + result;
        }
        return result;
    }

    string getDirectCode(int n) {
        string result = decToBinary(abs(n), bits - 1);
        if (n < 0) {
            result = "1" + result.substr(1);
        } else {
            result = "0" + result.substr(1);
        }
        return result;
    }

    string getInverseCode(int n) {
        if (n >= 0) return getDirectCode(n);
        string direct = getDirectCode(n);
        string inverse = "";
        for (char c : direct) {
            inverse += (c == '0' ? '1' : '0');
        }
        return inverse;
    }

    string getComplementCode(int n) {
        if (n >= 0) return getDirectCode(n);
        string inverse = getInverseCode(n);
        int carry = 1;
        string complement = "";
        for (int i = inverse.length() - 1; i >= 0; i--) {
            int bit = inverse[i] - '0';
            int sum = bit + carry;
            complement = char((sum % 2) + '0') + complement;
            carry = sum / 2;
        }
        return complement;
    }

    string addBinary(string a, string b, int& overflow) {
        string result = "";
        int carry = 0;
        overflow = 0;
        for (int i = a.length() - 1; i >= 0; i--) {
            int bitA = a[i] - '0';
            int bitB = b[i] - '0';
            int sum = bitA + bitB + carry;
            result = char((sum % 2) + '0') + result;
            carry = sum / 2;
        }
        overflow = carry;
        return result;
    }

    void printSeparator() {
        cout << "\n";
        for (int i = 0; i < 64; i++) cout << "=";
        cout << "\n";
    }

    void task1() {
        printSeparator();
        cout << "TASK 1: Addition/subtraction in direct, inverse and complement codes\n";
        cout << "Initial data:\n";
        cout << "    X1 = " << X1 << " = " << decToBinary(X1) << "_2\n";
        cout << "    X2 = " << X2 << " = " << decToBinary(X2) << "_2\n";

        string signs[] = {"+", "-"};
        for (int s1 = 0; s1 < 2; s1++) {
            for (int s2 = 0; s2 < 2; s2++) {
                int num1 = (s1 == 0) ? X1 : -X1;
                int num2 = (s2 == 0) ? X2 : -X2;
                cout << "\nCombination: " << signs[s1] << abs(X1) << " " << signs[s2] << abs(X2) << "\n";

                cout << "DIRECT CODE:\n";
                string dir1 = getDirectCode(num1);
                string dir2 = getDirectCode(num2);
                cout << "    [" << num1 << "]dir = " << dir1 << "\n";
                cout << "    [" << num2 << "]dir = " << dir2 << "\n";
                cout << "    Sum (dec): " << num1 + num2 << "\n";

                cout << "INVERSE CODE:\n";
                string inv1 = getInverseCode(num1);
                string inv2 = getInverseCode(num2);
                cout << "    [" << num1 << "]inv = " << inv1 << "\n";
                cout << "    [" << num2 << "]inv = " << inv2 << "\n";
                int overflow;
                string sumInv = addBinary(inv1, inv2, overflow);
                cout << "    Sum in inv. code = " << sumInv << "\n";
                if (overflow == 1) {
                    cout << "    Circular carry: +1\n";
                    int carry = 1;
                    for (int i = sumInv.length() - 1; i >= 0 && carry; i--) {
                        int bit = sumInv[i] - '0';
                        int sum = bit + carry;
                        sumInv[i] = char((sum % 2) + '0');
                        carry = sum / 2;
                    }
                    cout << "    After correction = " << sumInv << "\n";
                }
                cout << "    Sum (dec): " << num1 + num2 << "\n";

                cout << "COMPLEMENT CODE:\n";
                string comp1 = getComplementCode(num1);
                string comp2 = getComplementCode(num2);
                cout << "    [" << num1 << "]comp = " << comp1 << "\n";
                cout << "    [" << num2 << "]comp = " << comp2 << "\n";
                string sumComp = addBinary(comp1, comp2, overflow);
                cout << "    Sum in comp. code = " << sumComp << "\n";
                if (overflow == 1) {
                    cout << "    Carry discarded\n";
                }
                cout << "    Sum (dec): " << num1 + num2 << "\n";
            }
        }
    }

    void task2() {
        printSeparator();
        cout << "TASK 2: Multiplication of number modules\n";
        int mod1 = abs(X1);
        int mod2 = abs(X2);
        int product = mod1 * mod2;

        string signs[] = {"+", "-"};

        cout << "Initial data:\n";
        cout << "    |X1| = " << mod1 << " = " << decToBinary(mod1, 8) << "_2\n";
        cout << "    |X2| = " << mod2 << " = " << decToBinary(mod2, 8) << "_2\n";

        cout << "Multiplication by column:\n";
        string bin1 = decToBinary(mod1, 8);
        string bin2 = decToBinary(mod2, 8);
        cout << "         " << bin1 << "  (" << mod1 << ")\n";
        cout << "       x " << bin2 << "  (" << mod2 << ")\n";
        cout << "         ----------------\n";

        vector<string> partials;
        for (int i = bin2.length() - 1; i >= 0; i--) {
            string partial = "";
            if (bin2[i] == '1') {
                partial = bin1;
                for (int j = 0; j < (bin2.length() - 1 - i); j++) {
                    partial += "0";
                }
            } else {
                for (int j = 0; j < bin1.length() + (bin2.length() - 1 - i); j++) {
                    partial += "0";
                }
            }
            partials.push_back(partial);
        }

        for (int i = partials.size() - 1; i >= 0; i--) {
            cout << "         ";
            for (int j = 0; j < (partials.size() - 1 - i); j++) cout << " ";
            cout << partials[i] << "\n";
        }
        cout << "         ----------------\n";
        cout << "         " << decToBinary(product, 16) << "  (" << product << ")\n";

        cout << "Product signs for all combinations:\n";
        cout << "Sign X1    Sign X2    XOR    Sign result    Result\n";
        for (int s1 = 0; s1 < 2; s1++) {
            for (int s2 = 0; s2 < 2; s2++) {
                int sign = s1 ^ s2;
                string signStr = (sign == 0) ? "+" : "-";
                int result = (sign == 0) ? product : -product;
                cout << "    " << signs[s1] << "          " << signs[s2] << "         " << sign << "          " << signStr << "              " << result << "\n";
            }
        }
        cout << "Rule: Product sign = Sign_X1 XOR Sign_X2\n";
    }

    void task3() {
        printSeparator();
        cout << "TASK 3: Division of number modules (5 digits after point)\n";
        int mod1 = abs(X1);
        int mod2 = abs(X2);

        string signs[] = {"+", "-"};

        cout << "Initial data:\n";
        cout << "    |X1| = " << mod1 << " = " << decToBinary(mod1) << "_2\n";
        cout << "    |X2| = " << mod2 << " = " << decToBinary(mod2) << "_2\n";

        cout << "Division algorithm (sequential doubling of remainder):\n";
        int remainder = mod1;
        string result = "0.";
        cout << "Step | Remainder | x2 (shift) | >= " << mod2 << "? | Bit | New remainder\n";

        for (int i = 1; i <= 5; i++) {
            int doubled = remainder * 2;
            int bit = (doubled >= mod2) ? 1 : 0;
            int newRemainder = (bit == 1) ? (doubled - mod2) : doubled;
            cout << "  " << i << "  |   " << setw(7) << remainder << " |    " << setw(10) << doubled << " |    " << (bit == 1 ? "Yes" : "No") << "   |   " << bit << "  |    " << newRemainder << "\n";
            result += char(bit + '0');
            remainder = newRemainder;
        }

        cout << "Division result of modules: " << result << "_2\n";
        double decimalResult = 0;
        double power = 0.5;
        for (int i = 2; i < result.length(); i++) {
            if (result[i] == '1') {
                decimalResult += power;
            }
            power /= 2;
        }
        cout << "In decimal: ~= " << fixed << setprecision(4) << decimalResult << "\n";
        cout << "Exact value: " << fixed << setprecision(4) << (double)mod1 / mod2 << "\n";

        cout << "Quotient signs for all combinations:\n";
        cout << "Sign X1    Sign X2    XOR    Sign result    Result\n";
        for (int s1 = 0; s1 < 2; s1++) {
            for (int s2 = 0; s2 < 2; s2++) {
                int sign = s1 ^ s2;
                string signStr = (sign == 0) ? "+" : "-";
                cout << "    " << signs[s1] << "          " << signs[s2] << "         " << sign << "          " << signStr << "              " << signStr << result << "\n";
            }
        }
        cout << "Rule: Quotient sign = Sign_dividend XOR Sign_divisor\n";
    }

    void task4() {
        printSeparator();
        cout << "TASK 4: Addition of numbers in floating point form\n";
        int P1 = 4;
        int P2 = 5;

        cout << "Initial data:\n";
        cout << "    X1 = " << X1 << ", P1 = " << P1 << " (" << decToBinary(P1, 3) << "_2)\n";
        cout << "    X2 = " << X2 << ", P2 = " << P2 << " (" << decToBinary(P2, 3) << "_2)\n";

        cout << "Step 1: Normalization of numbers\n";
        string bin1 = decToBinary(abs(X1));
        string bin2 = decToBinary(abs(X2));
        size_t pos1 = bin1.find('1');
        size_t pos2 = bin2.find('1');
        string mantissa1 = (pos1 != string::npos) ? bin1.substr(pos1) : "0";
        string mantissa2 = (pos2 != string::npos) ? bin2.substr(pos2) : "0";
        int exp1 = (pos1 != string::npos) ? (int)bin1.length() - (int)pos1 : 0;
        int exp2 = (pos2 != string::npos) ? (int)bin2.length() - (int)pos2 : 0;

        cout << "    " << X1 << " = " << bin1 << "_2 = 0." << mantissa1 << " x 2^" << exp1 << "\n";
        cout << "    M1 = 0." << mantissa1 << "\n";
        cout << "    " << X2 << " = " << bin2 << "_2 = 0." << mantissa2 << " x 2^" << exp2 << "\n";
        cout << "    M2 = 0." << mantissa2 << "\n";

        cout << "Step 2: Alignment of orders\n";
        int maxP = max(exp1, exp2);
        int diff = abs(exp1 - exp2);
        cout << "    Larger order: P = " << maxP << "\n";
        cout << "    Difference: " << diff << "\n";

        if (exp1 < exp2) {
            cout << "    Shift M1 right by " << diff << " bit:\n";
            cout << "    M1' = 0.";
            for (int i = 0; i < diff; i++) cout << "0";
            cout << mantissa1 << "\n";
        } else if (exp2 < exp1) {
            cout << "    Shift M2 right by " << diff << " bit:\n";
            cout << "    M2' = 0.";
            for (int i = 0; i < diff; i++) cout << "0";
            cout << mantissa2 << "\n";
        }

        cout << "Step 3: Addition of mantissas\n";
        cout << "    All 4 sign combinations:\n";
        string signs[] = {"+", "-"};
        for (int s1 = 0; s1 < 2; s1++) {
            for (int s2 = 0; s2 < 2; s2++) {
                int num1 = (s1 == 0) ? X1 : -X1;
                int num2 = (s2 == 0) ? X2 : -X2;
                int sum = num1 + num2;
                cout << "    " << signs[s1] << abs(X1) << " + " << signs[s2] << abs(X2) << " = " << sum << "\n";
                int absSum = abs(sum);
                if (absSum > 0) {
                    string sumBin = decToBinary(absSum);
                    size_t pos = sumBin.find('1');
                    string normMantissa = (pos != string::npos) ? sumBin.substr(pos) : "0";
                    int newP = (pos != string::npos) ? (int)sumBin.length() - (int)pos : 0;
                    cout << "        Result: " << (sum < 0 ? "-" : "") << "0." << normMantissa << " x 2^" << newP << "\n";
                }
                cout << "\n";
            }
        }

        cout << "Summary table of results:\n";
        cout << "Operation       Result    In floating point\n";
        int sum1 = X1 + X2;
        int sum2 = X1 + (-X2);
        int sum3 = (-X1) + X2;
        int sum4 = (-X1) + (-X2);

        auto printFloat = [&](int sum, int x1, int x2, string s1, string s2) {
            int absSum = abs(sum);
            if (absSum == 0) {
                cout << "  " << s1 << x1 << " " << s2 << x2 << "        " << setw(5) << sum << "       0.0 x 2^0\n";
                return;
            }
            string sumBin = decToBinary(absSum);
            size_t pos = sumBin.find('1');
            string mantissa = (pos != string::npos) ? sumBin.substr(pos) : "0";
            int exp = (pos != string::npos) ? (int)sumBin.length() - (int)pos : 0;
            cout << "  " << s1 << x1 << " " << s2 << x2 << "        " << setw(5) << sum << "       " << (sum < 0 ? "-" : "") << "0." << mantissa << " x 2^" << exp << "\n";
        };

        printFloat(sum1, abs(X1), abs(X2), "+", "+");
        printFloat(sum2, abs(X1), abs(X2), "+", "-");
        printFloat(sum3, abs(X1), abs(X2), "-", "+");
        printFloat(sum4, abs(X1), abs(X2), "-", "-");
    }

    void run() {
        cout << "\n========================================================\n";
        cout << "  Laboratory Work #1: Representation of numeric information\n";
        cout << "  Variant: User input\n";
        cout << "========================================================\n";
        cout << "Initial data: X1 = " << X1 << ", X2 = " << X2 << "\n";
    }

    void showMenu() {
        cout << "\n";
        cout << "MAIN MENU\n";
        cout << "  1. Task 1: Addition/subtraction in different codes\n";
        cout << "  2. Task 2: Multiplication of modules\n";
        cout << "  3. Task 3: Division of modules\n";
        cout << "  4. Task 4: Addition in floating point\n";
        cout << "  5. Execute all tasks\n";
        cout << "  6. Enter new values X1 and X2\n";
        cout << "  7. Show initial data\n";
        cout << "  0. Exit\n";
        cout << "\nYour choice: ";
    }

    void showVariantInfo() {
        printSeparator();
        cout << "VARIANT INFORMATION\n";
        cout << "    X1 = " << X1 << "\n";
        cout << "    X2 = " << X2 << "\n";
        cout << "    Binary representation:\n";
        cout << "        X1 = " << decToBinary(X1) << "_2\n";
        cout << "        X2 = " << decToBinary(X2) << "_2\n";
    }

    void execute() {
        run();
        int choice;
        do {
            showMenu();
            cin >> choice;
            switch (choice) {
                case 1: task1(); break;
                case 2: task2(); break;
                case 3: task3(); break;
                case 4: task4(); break;
                case 5: task1(); task2(); task3(); task4(); break;
                case 6:
                    cout << "Enter X1: ";
                    cin >> X1;
                    cout << "Enter X2: ";
                    cin >> X2;
                    break;
                case 7: showVariantInfo(); break;
                case 0:
                    cout << "Program termination.\n";
                    break;
                default:
                    cout << "Invalid choice! Try again.\n";
            }
        } while (choice != 0);
        cout << "Thank you for using the program!\n";
    }
};

int main() {
    #ifdef _WIN32
        system("chcp 65001 > nul");
    #endif

    cout << "========================================================\n";
    cout << "  Program for arithmetic operations (C++)\n";
    cout << "========================================================\n";
    cout << "Input rules:\n";
    cout << "  - Enter integers X1 and X2\n";
    cout << "  - Program will execute operations in direct, inverse,\n";
    cout << "    complement codes and floating point form\n";
    cout << "  - Enter '0' to exit menu\n";
    cout << "========================================================\n\n";

    int X1, X2;
    cout << "Enter X1: ";
    cin >> X1;
    cout << "Enter X2: ";
    cin >> X2;

    NumberConverter converter(X1, X2);
    converter.execute();

    return 0;
}