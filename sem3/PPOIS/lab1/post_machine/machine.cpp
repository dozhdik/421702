/**
 * @file machine.cpp
 * @brief Реализация класса `Machine` — абстрактная машина Поста.
 * @details
 * В этом файле реализованы конструктор и методы управления выполнением правил:
 * выбор стартового правила, выполнение отдельного правила и цикл исполнения.
 *
 * Реализованы методы:
 * - Machine()
 * - resolveStartRule()
 * - executeRule()
 * - setLogging()
 * - getRibbon()
 * - getRules()
 * - setStartRuleId()
 * - loadRulesFromFile()
 * - run()
 * - runFrom()
 *
 * @author Дождиков Александр, гр. 421702
 * @see Machine
 */

#include "machine.h"
#include <iostream>

/**
 * @brief Конструктор по умолчанию.
 * @details Инициализирует ленту и набор правил, выключает логирование.
 */
Machine::Machine() : ribbon(), rules(), logging(false), startRuleId(-1){}

/**
 * @brief Определяет стартовое правило для выполнения.
 * @return id стартового правила или -1 при отсутствии правил.
 */
int Machine::resolveStartRule() const {
    if(startRuleId != -1) return startRuleId;

    auto all = rules.allRules();
    if(all.empty()) return -1;

    return all.front().id; 
}

/**
 * @brief Выполняет одно правило на ленте.
 * @param rule Ссылка на правило для выполнения.
 * @return Идентификатор следующего правила (или -1 для HALT).
 */
int Machine::executeRule(const Rule& rule){
    switch(rule.action){
        case ActionType::SET:        ribbon.setLabel(); break;
        case ActionType::CLR:        ribbon.removeLabel(); break;
        case ActionType::MOVE_LEFT:  ribbon.moveLeft(); break;
        case ActionType::MOVE_RIGHT: ribbon.moveRight(); break;
        case ActionType::NOP:        break;
    }

    if(!rule.conditional)
        return rule.next;

    int val = ribbon.getValue();
    return (val == 0 ? rule.nextIf0 : rule.nextIf1);
}

/**
 * @brief Включает/выключает логирование выполнения.
 */
void Machine::setLogging(bool isTrue){ 
    logging = isTrue; 
}

/**
 * @brief Возвращает ссылку на внутреннюю ленту.
 */
Ribbon& Machine::getRibbon() { 
    return ribbon; 
}

/**
 * @brief Возвращает ссылку на объект правил.
 */
Rules& Machine::getRules() { 
    return rules; 
}

/**
 * @brief Устанавливает идентификатор стартового правила.
 */
void Machine::setStartRuleId(int id) { 
    startRuleId = id; 
}

/**
 * @brief Загружает правила из файла, делегируя `Rules`.
 */
bool Machine::loadRulesFromFile(const std::string& path, std::string& error){
    return rules.loadFromFile(path, error);
}

/**
 * @brief Запускает выполнение машины с определённого стартового правила.
 * @return true при успешном завершении, иначе false и `error` содержит сообщение.
 */
bool Machine::run(std::string& error){
    int start = resolveStartRule();
    if(start == -1){
        error = "Нет правил для выполнения.";
        return false;
    }
    return runFrom(start, error);
}

/**
 * @brief Запускает выполнение начиная с указанного правила.
 * @param startId Идентификатор правила, с которого начать.
 * @param error Строка для сообщения об ошибке.
 * @return true при успешном завершении, иначе false.
 */
bool Machine::runFrom(int startId, std::string& error){
    int current = startId;
    int step = 0;

    while(current != -1){
        const Rule* r = rules.getRule(current);
        if(!r){
            error = "Правило " + std::to_string(current) + " не найдено.";
            return false;
        }

        if(logging){
            std::cout << "=== Step " << step << " ; rule " << r->id << " ===\n";
            std::cout << ribbon;
        }

        int next = executeRule(*r);
        ++step;

        if(logging){
            std::cout << "После выполнения:\n" << ribbon;
            std::cout << "Следующее правило: " 
                      << (next == -1 ? "HALT" : std::to_string(next)) 
                      << "\n";
        }

        current = next;
    }

    if(logging) std::cout << "Выполнение завершено (HALT).\n";
    return true;
}