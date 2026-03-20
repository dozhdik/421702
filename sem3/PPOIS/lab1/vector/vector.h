#pragma once

#include <iostream>
#include <math.h>
#include <vector>
#include <stdexcept>
#include <ostream>

/**
 * @class Vector
 * @brief Пространственный вектор фиксированной размерности (3 компоненты).
 * @details Класс предоставляет базовые векторные операции: сложение,
 * вычитание, скалярное произведение (через оператор ^ возвращает косинус
 * угла), векторное произведение, масштабирование и операции сравнения по длине.
 */
class Vector{
private:
    static const int lenth = 3;       
    std::vector<double> coords;      
public:
    /**
     * @brief Конструктор по умолчанию — нулевой вектор.
     */
    Vector();

    /**
     * @brief Конструктор по компонентам.
     * @param x Первая компонента (x).
     * @param y Вторая компонента (y).
     * @param z Третья компонента (z).
     */
    Vector(double x, double y, double z);

    /**
     * @brief Конструктор копирования.
     * @param sample Объект для копирования.
     */
    Vector(const Vector& sample);

    /**
     * @brief Выводит компоненты вектора в stdout (форма: "x y z").
     */
    void get_coords();

    /**
     * @brief Возвращает длину вектора (евклидова норма).
     * @return Длина вектора.
     */
    double get_lenth() const;

    /**
     * @brief Оператор сложения векторов (покомпонентно).
     * @param term Второй операнд сложения.
     * @return Новый объект `Vector` — результат суммы.
     */
    Vector operator+(const Vector& term) const;

    /**
     * @brief Сложение с присваиванием (покомпонентно).
     * @param term Второй операнд.
     * @return Ссылка на текущий объект после изменения.
     */
    Vector& operator+=(const Vector& term);

    /**
     * @brief Оператор вычитания (покомпонентно).
     * @param subtrahend Вычитаемый вектор.
     * @return Новый объект `Vector` — результат вычитания.
     */
    Vector operator-(const Vector& subtrahend) const;

    /**
     * @brief Вычитание с присваиванием (покомпанентно).
     * @param subtrahend Вычитаемый вектор.
     * @return Ссылка на текущий объект после изменения.
     */
    Vector& operator-=(const Vector& subtrahend);

    /**
     * @brief Скалярное произведение (возвращает косинус угла между векторами).
     * @param second_component Второй операнд для вычисления скалярного произведения.
     * @return Косинус угла между векторами (double).
     * @throw std::runtime_error при попытке деления на ноль в норме одного из векторов.
     */
    double operator^(const Vector& second_component) const;

    /**
     * @brief Векторное произведение.
     * @param factor Второй операнд.
     * @return Новый `Vector` — результат векторного произведения.
     */
    Vector operator*(const Vector& factor) const;

    /**
     * @brief Векторное произведение с присваиванием.
     * @param factor Второй операнд.
     * @return Ссылка на текущий объект после изменения.
     */
    Vector& operator*=(const Vector& factor);

    /**
     * @brief Масштабирование вектора на скаляр.
     * @param factor Множитель.
     * @return Новый `Vector` — результат масштабирования.
     */
    Vector operator*(double factor) const;

    /**
     * @brief Масштабирование с присваиванием.
     * @param factor Множитель.
     * @return Ссылка на текущий объект после изменения.
     */
    Vector& operator*=(double factor);

    /**
     * @brief Поэлементное деление (требует ненулевых компонент делителя).
     * @param divider Делитель (вектор).
     * @return Результирующий вектор после деления.
     * @throw std::runtime_error при делении на ноль в компонентах делителя.
     */
    Vector operator/(const Vector& divider) const;

    /**
     * @brief Поэлементное деление с присваиванием.
     * @param divider Делитель (вектор).
     * @return Ссылка на текущий объект после изменения.
     * @throw std::runtime_error при делении на ноль в компонентах делителя.
     */
    Vector& operator/=(const Vector& divider);

    /**
     * @brief Сравнение по длине: больше.
     * @param second_component Второй вектор для сравнения.
     * @return true, если длина текущего вектора больше длины второго.
     */
    bool operator>(const Vector& second_component) const;

    /**
     * @brief Сравнение по длине: больше или равно.
     */
    bool operator>=(const Vector& second_component) const;

    /**
     * @brief Сравнение по длине: меньше.
     */
    bool operator<(const Vector& second_component) const;

    /**
     * @brief Сравнение по длине: меньше или равно.
     */
    bool operator<=(const Vector& second_component) const;

    /**
     * @brief Проверяет неравенство по компонентам.
     * @return true, если хотя бы одна компонента отличается.
     */
    bool operator!=(const Vector& second_component) const;

    /**
     * @brief Проверяет равенство по всем компонентам.
     * @return true, если все компоненты равны.
     */
    bool operator==(const Vector& second_component) const;

    /**
     * @brief Оператор присваивания.
     * @return Ссылка на текущий объект после присваивания.
     */
    Vector& operator=(const Vector& second_component);

    /**
     * @brief Оператор вывода в поток (печать компонентов в строку).
     */
    friend std::ostream& operator<<(std::ostream& output, const Vector& component);

    /**
     * @brief Оператор ввода из потока (чтение трёх компонент).
     */
    friend std::istream& operator>>(std::istream& input, Vector& component);
};