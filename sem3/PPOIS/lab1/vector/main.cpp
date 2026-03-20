/**
 * @file main.cpp
 * @brief Программа-демонстрация использования класса `Vector`.
 * @details
 * В этом файле реализована демонстрационная программа, которая создаёт
 * несколько объектов Vector и выполняет с ними ряд операций, демонстрируя
 * функциональность класса.
 *
 * Реализованы функции:
 * - main()
 *
 * @author Дождиков Александр, гр. 421702
 * @see Vector
 */

#include <iostream>
#include "vector.h"

/**
 * @brief Точка входа демонстрационной программы для `Vector`.
 * @details Создаёт несколько векторов и выполняет операции с выводом результатов.
 */
int main(){
    Vector a(2, 1, 5.1);
    Vector b(1, 3, 6);
    Vector c, d, h, i;
    Vector f(1, 2, 3);
    Vector g(4, 5, 6);
    a.get_coords();
    a.get_lenth();
    std::cout << "проверка оператора +" << std::endl;
    a = d + c;
    std::cout << a << std::endl;
    std::cout << "проверка оператора +=" << std::endl;
    for(int i = 0; i < 5; i++){
        c += b;
        c.get_coords();
    }
    std::cout << "проверка оператора -" << std::endl;
    c = a - b;
    c.get_coords();
    std::cout << "проверка оператора -=" << std::endl;
    for(int i = 0; i < 5; i++){
        d -= b;
        d.get_coords();
    }
    std::cout << "проверка оператора ^" <<std::endl;
    double e;
    e = f ^ g;
    std::cout << e << std::endl;
    std::cout << "проверка оператора *" <<std::endl;
    h = f * g;
    h.get_coords();
    std::cout << "проверка оператора *=" <<std::endl;
    h *= f;
    h.get_coords();
    std::cout << "проверка оператора *" <<std::endl;
    i = h * 2;
    i.get_coords();
    std::cout << "проверка оператора *=" <<std::endl;
    i *= 2;
    i.get_coords();
    std::cout << "проверка оператора /=" <<std::endl;
    g /= f;
    g.get_coords();
    std::cout << "Введите значение для проверки вывода в поток: " << std::endl;
    std::cin >> c;
    std::cout << "значение c:" <<std::endl;
    std::cout << c;
}