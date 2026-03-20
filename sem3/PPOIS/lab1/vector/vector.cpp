/**
 * @file vector.cpp
 * @brief Реализация класса `Vector` (трёхмерный вектор).
 * @details
 * В этом файле реализованы конструкторы и методы класса Vector: поэлементные
 * операции сложения, вычитания, скалярное и векторное произведения, сравнения
 * по длине, масштабирование и операции ввода/вывода.
 *
 * Реализованы методы:
 * - Vector()
 * - Vector(double x, double y, double z)
 * - Vector(const Vector& sample)
 * - get_coords()
 * - get_lenth()
 * - operator+(), operator+=()
 * - operator-(), operator-=()
 * - operator^() (скалярное произведение)
 * - operator*(const Vector&), operator*=(const Vector&) (векторное произведение)
 * - operator*(double), operator*=(double)
 * - operator/(const Vector&), operator/=(const Vector&)
 * - operator>, operator>=, operator<, operator<=
 * - operator!=, operator==
 * - operator=(), operator<<(), operator>>()
 *
 * @author Дождиков Александр, гр. 421702
 * @see Vector
 */

#include <iostream>
#include "vector.h"

/**
 * @brief Конструктор по умолчанию — создаёт нулевой вектор фиксированной длины.
 */
Vector::Vector() : coords(lenth){}

/**
 * @brief Конструктор по трём компонентам.
 */
Vector::Vector(double x, double y, double z){
    coords.push_back(x);
    coords.push_back(y);
    coords.push_back(z);
}

/**
 * @brief Конструктор копирования.
 */
Vector::Vector(const Vector& sample) : coords(sample.coords){}

/**
 * @brief Печатает компоненты вектора в stdout.
 */
void Vector::get_coords(){
    for (size_t i = 0; i < coords.size(); ++i) {
            std::cout << coords[i] << " ";
        }
        std::cout << std::endl;
}

/**
 * @brief Возвращает евклидову норму (длину) вектора.
 */
double Vector::get_lenth() const{
    return sqrt((pow(coords[0], 2) + pow(coords[1], 2) + pow(coords[2], 2)));
}

/**
 * @brief Поэлементное сложение — возвращает новый вектор.
 */
Vector Vector::operator+(const Vector& term) const {
    Vector sum;
    for (int i = 0; i < coords.size(); i++){
        sum.coords[i] = coords[i] + term.coords[i];
    }
    return sum;
}

/**
 * @brief Сложение с присваиванием (покомпонентно).
 */
Vector& Vector::operator+=(const Vector& term){
    for (int i = 0; i < coords.size(); i++){
        coords[i] += term.coords[i];
    }
    return *this;
}

/**
 * @brief Поэлементное вычитание — возвращает новый вектор.
 */
Vector Vector::operator-(const Vector& subtrahend) const{
    Vector diff;
    for (int i = 0; i < coords.size(); i++){
        diff.coords[i] = coords[i] - subtrahend.coords[i];
    }
    return diff;
}

/**
 * @brief Вычитание с присваиванием (покомпонентно).
 */
Vector& Vector::operator-=(const Vector& subtrahend){
    for (int i = 0; i < coords.size(); i++){
        coords[i] -= subtrahend.coords[i];
    }
    return *this;
}

/**
 * @brief Скалярное произведение, возвращает косинус угла между векторами.
 * @throw std::runtime_error если одна из норм равна нулю.
 */
double Vector::operator^(const Vector& second_component) const{
    double cos, dividend = 0.0, lenth_1, lenth_2;

    lenth_1 = this->get_lenth();
    lenth_2 = second_component.get_lenth();

    for(int i = 0; i < this->coords.size(); i++){
        dividend += (coords[i] * second_component.coords[i]);
    }

    if(lenth_1 == 0 || lenth_2 == 0){
        throw std::runtime_error("Division by zero in Vector operator^: divider component is 0");
    }
    else cos = dividend / (lenth_1 * lenth_2);

    return cos;
}

/**
 * @brief Векторное произведение (по формуле).
 */
Vector Vector::operator*(const Vector& factor) const{
    Vector composition;
    composition.coords[0] = coords[1]*factor.coords[2] - coords[2]*factor.coords[1];
    composition.coords[1] = 0 - (coords[0]*factor.coords[2] - coords[2]*factor.coords[0]);
    composition.coords[2] = coords[0]*factor.coords[1] - coords[1]*factor.coords[0];

    return composition;
}

/**
 * @brief Векторное произведение с присваиванием.
 */
Vector& Vector::operator*=(const Vector& factor){
    Vector composition;
    composition.coords[0] = coords[1]*factor.coords[2] - coords[2]*factor.coords[1];
    composition.coords[1] = 0 - (coords[0]*factor.coords[2] - coords[2]*factor.coords[0]);
    composition.coords[2] = coords[0]*factor.coords[1] - coords[1]*factor.coords[0];

    coords[0] = composition.coords[0];
    coords[1] = composition.coords[1];
    coords[2] = composition.coords[2];
    return *this;
}

/**
 * @brief Масштабирование на скаляр (новый вектор).
 */
Vector Vector::operator*(double factor) const{
    Vector composition;
    for(int i = 0; i < coords.size(); i++){
        composition.coords[i] = coords[i] * factor;
    }
    return composition;
}

/**
 * @brief Масштабирование с присваиванием.
 */
Vector& Vector::operator*=(double factor){
    for(int i = 0; i < coords.size(); i++){
        coords[i] = coords[i] * factor;
    }
    return *this;
}

/**
 * @brief Поэлементное деление — генерирует исключение при делении на ноль.
 */
Vector Vector::operator/(const Vector& divider) const{
    Vector quotient;
    for(int i = 0; i < coords.size(); i++){
        if(divider.coords[i] == 0) {
            throw std::runtime_error("Division by zero in Vector operator/: divider component is 0");
        }
        quotient.coords[i] = coords[i] / divider.coords[i];
    } 
    return quotient;
}

/**
 * @brief Поэлементное деление с присваиванием.
 */
Vector& Vector::operator/=(const Vector& divider){
    for(int i = 0; i < coords.size(); i++){
        if(divider.coords[i] == 0) {
            throw std::runtime_error("Division by zero in Vector operator/: divider component is 0");
        }
        coords[i] = coords[i] / divider.coords[i];
    } 
    return *this;
}

/**
 * @brief Сравнение по длине: больше.
 */
bool Vector::operator>(const Vector& second_component) const{
    double lenth_1, lenth_2;
    lenth_1 = this->get_lenth();
    lenth_2 = second_component.get_lenth();

    if(lenth_1 > lenth_2) return true;
    else return false;
}

/**
 * @brief Сравнение по длине: больше или равно.
 */
bool Vector::operator>=(const Vector& second_component) const{
    double lenth_1, lenth_2;
    lenth_1 = this->get_lenth();
    lenth_2 = second_component.get_lenth();

    if(lenth_1 >= lenth_2) return true;
    else return false;
}

/**
 * @brief Сравнение по длине: меньше.
 */
bool Vector::operator<(const Vector& second_component) const{
    double lenth_1, lenth_2;
    lenth_1 = this->get_lenth();
    lenth_2 = second_component.get_lenth();

    if(lenth_1 < lenth_2) return true;
    else return false;
}

/**
 * @brief Сравнение по длине: меньше или равно.
 */
bool Vector::operator<=(const Vector& second_component) const{
    double lenth_1, lenth_2;
    lenth_1 = this->get_lenth();
    lenth_2 = second_component.get_lenth();

    if(lenth_1 <= lenth_2) return true;
    else return false;
}

/**
 * @brief Проверяет поэлементное неравенство.
 */
bool Vector::operator!=(const Vector& second_component) const{
    for(int i = 0; i < coords.size(); i++){
        if(coords[i] != second_component.coords[i]) return true;
    }
    return false;
}

/**
 * @brief Проверяет поэлементное равенство.
 */
bool Vector::operator==(const Vector& second_component) const{
    for(int i = 0; i < coords.size(); i++){
        if(coords[i] != second_component.coords[i]) return false;
    }
    return true;
}

/**
 * @brief Оператор присваивания.
 */
Vector& Vector::operator=(const Vector& second_component){
    for(int i = 0; i < coords.size(); i++){
        coords[i] = second_component.coords[i];
    }
    return *this;
}

/**
 * @brief Выводит компоненты вектора в поток.
 */
std::ostream& operator<<(std::ostream& output, const Vector& component){
    output << component.coords[0] << " " << component.coords[1] << " " << component.coords[2] << std::endl;
    return output; 
}

/**
 * @brief Считывает три компоненты вектора из потока.
 */
std::istream& operator>>(std::istream& input, Vector& component){
    input >> component.coords[0] >> component.coords[1] >> component.coords[2];
    return input;
}