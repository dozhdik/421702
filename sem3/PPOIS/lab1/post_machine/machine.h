#pragma once

#include "ribbon.h"
#include "rules.h"

/**
 * @class Machine
 * @brief Виртуальная машина для выполнения правил Поста.
 * @details Управляет лентой `Ribbon`, набором правил `Rules` и выполняет
 * пошаговое применение правил, поддерживает опциональное логирование.
 */
class Machine {
private:
    /**
     * @brief Лента, с которой работает машина.
     */
    Ribbon ribbon;   

    /**
     * @brief Набор правил для выполнения.
     */
    Rules rules;     

    /**
     * @brief Флаг включённого логирования ходов.
     */
    bool logging; 

    /**
     * @brief Идентификатор стартового правила.
     */
    int startRuleId;

    /**
     * @brief Определяет стартовое правило, если `startRuleId` не задан.
     * @return Идентификатор стартового правила.
     */
    int resolveStartRule() const;

    /**
     * @brief Выполняет одно правило на ленте.
     * @param rule Правило для выполнения.
     * @return Код результата выполнения (0 — OK, иначе код ошибки).
     */
    int executeRule(const Rule& rule);
public:
    /**
     * @brief Конструктор по умолчанию.
     * @details Инициализирует состояние машины — пустая лента и набор правил.
     */
    Machine();

    /**
     * @brief Включает или выключает логирование выполнения.
     * @param isTrue true — включить логирование, false — выключить.
     */
    void setLogging(bool isTrue);

    /**
     * @brief Получение доступа к ленте машины.
     * @return Ссылка на объект `Ribbon`.
     */
    Ribbon& getRibbon();

    /**
     * @brief Получение доступа к набору правил.
     * @return Ссылка на объект `Rules`.
     */
    Rules& getRules();

    /**
     * @brief Устанавливает идентификатор стартового правила.
     * @param id Идентификатор правила, с которого следует начать выполнение.
     */
    void setStartRuleId(int id);

    /**
     * @brief Загружает правила из файла.
     * @param path Путь к файлу с правилами.
     * @param error Строка для сообщения об ошибке (при неудаче).
     * @return true при успешной загрузке, иначе false и `err` содержит описание ошибки.
     */
    bool loadRulesFromFile(const std::string& path, std::string& error);

    /**
     * @brief Запускает выполнение машины с текущего стартового правила.
     * @param error Строка для сообщения об ошибке (при неудаче).
     * @return true при успешном завершении, иначе false и `err` заполнен.
     */
    bool run(std::string& error);

    /**
     * @brief Запускает выполнение машины начиная с конкретного правила.
     * @param startId Идентификатор правила, с которого начать.
     * @param error Строка для сообщения об ошибке (при неудаче).
     * @return true при успешном завершении, иначе false и `err` заполнен.
     */
    bool runFrom(int startId, std::string& error);
};
