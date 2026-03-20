/**
 * @file ribbon.cpp
 * @brief Реализация класса `Ribbon` (лента для модели Поста).
 * @details
 * В этом файле реализованы конструктор и методы управления лентой: чтение
 * и запись значений, установка/удаление метки, сдвиги головки, очистка и
 * вывод в поток.
 *
 * Реализованы методы:
 * - Ribbon()
 * - getValue()
 * - setValue()
 * - setLabel()
 * - removeLabel()
 * - moveRight()
 * - moveLeft()
 * - clear()
 * - operator<<
 *
 * @author Дождиков Александр, гр. 421702
 * @see Ribbon
 */

#include "ribbon.h"

/**
 * @brief Конструктор по умолчанию.
 * @details Инициализирует позицию каретки нулём и пустую карту меток.
 */
Ribbon::Ribbon() : position(0), ribbon(){}

/**
 * @brief Возвращает значение в текущей позиции ленты.
 * @return Значение в текущей ячейке (0, если метки нет).
 */
int Ribbon::getValue() const{
    auto it = ribbon.find(position);
    if(it != ribbon.end()){
        return it->second;
    } else {
        return 0;
    }
}

/**
 * @brief Устанавливает или удаляет значение в указанной позиции ленты.
 * @param userPosition Позиция на ленте.
 * @param userValue Значение для записи (0 — удалить метку, иначе записать значение).
 * @details Если `userValue` равен 0, удаляет ключ из контейнера; иначе записывает
 * значение по индексу `userPosition`.
 */
void Ribbon::setValue(int userPosition, int userValue){
    if(userValue == 0){
        auto it = ribbon.find(userPosition);
        if(it != ribbon.end()) ribbon.erase(it);
    } else {
        ribbon[userPosition] = userValue;
    }
}

/**
 * @brief Устанавливает метку в текущей позиции (записывает значение 1).
 */
void Ribbon::setLabel(){
    setValue(position, 1);
}

/**
 * @brief Удаляет метку в текущей позиции (удаляет запись).
 */
void Ribbon::removeLabel(){
    setValue(position, 0);
}

/**
 * @brief Сдвигает головку ленты вправо (увеличивает `position`).
 */
void Ribbon::moveRight(){
    ++position;
}

/**
 * @brief Сдвигает головку ленты влево (уменьшает `position`).
 */
void Ribbon::moveLeft(){
    --position;
}

/**
 * @brief Очищает ленту и сбрасывает позицию в начало (0).
 */
void Ribbon::clear(){
    ribbon.clear();
    position = 0;
}

/**
 * @brief Выводит ленту в поток в компактном виде и помечает текущую позицию '^'.
 * @param os Поток вывода.
 * @param rb Объект `Ribbon` для печати.
 * @return Ссылка на поток `os`.
 * @details Если лента пуста, выводит одну ячейку со значением 0 и маркер позиции.
 */
std::ostream& operator<<(std::ostream& os, const Ribbon& rb)
{
    if (rb.ribbon.empty()) {
        os << 0 << "\n^\n";
        return os;
    }

    int minPos = std::min(rb.position, rb.ribbon.begin()->first);
    int maxPos = std::max(rb.position, rb.ribbon.rbegin()->first);

    for (int i = minPos; i <= maxPos; ++i) {
        auto it = rb.ribbon.find(i);
        if (it == rb.ribbon.end())
            os << 0;
        else
            os << it->second;
    }
    os << "\n";

    for (int i = minPos; i < rb.position; ++i) {
        os << " ";
    }
    os << "^\n";

    return os;
}