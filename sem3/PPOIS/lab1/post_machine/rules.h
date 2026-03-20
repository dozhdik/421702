#pragma once

#include <string>
#include <map>
#include <vector>

/**
 * @enum ActionType
 * @brief Тип действия, выполняемого правилом.
 */
enum class ActionType {
    SET, 
    CLR, 
    MOVE_RIGHT,
    MOVE_LEFT,
    NOP
};

/**
 * @struct Rule
 * @brief Одна запись правила для машины Поста.
 * @param Поля описывают идентификатор, тип действия и переходы для условных правил.
 */
struct Rule {
    /** 
     * @brief Идентификатор правила. 
     */
    int id;     

    /** 
     * @brief Действие, выполняемое правилом.
     */
    ActionType action; 

    /** 
     * @brief Флаг условного перехода.
     */
    bool conditional = false;

    /** 
     * @brief Следующий идентификатор для безусловного правила.
     */
    int next = -1;               

    /** 
     * @brief Следующий идентификатор, если на ленте 0.
     */
    int nextIf0 = -1;       

    /** 
     * @brief Следующий идентификатор, если на ленте 1.
     */
    int nextIf1 = -1;        
};

/**
 * @class Rules
 * @brief Коллекция правил с утилитами загрузки и управления.
 */
class Rules {
private:
    /** 
     * @brief Контейнер правил по идентификатору.
     */
    std::map<int, Rule> rules; 
public:
    /**
     * @brief Конструктор по умолчанию.
     */
    Rules();

    /**
     * @brief Возвращает все правила в виде вектора.
     * @return Вектор всех правил (копия).
     */
    std::vector<Rule> allRules() const;

    /**
     * @brief Проверяет, пуст ли набор правил.
     * @return true, если правил нет.
     */
    bool empty() const;

    /**
     * @brief Очищает все правила.
     */
    void clear();

    /**
     * @brief Добавляет новое правило или заменяет существующее с таким id.
     * @param rule Правило для добавления/замены.
     * @return true при успешном добавлении/замене.
     */
    bool addOrReplaceRule(const Rule& rule);

    /**
     * @brief Удаляет правило по идентификатору.
     * @param id Идентификатор удаляемого правила.
     * @return true, если правило было удалено.
     */
    bool removeRule(int id);

    /**
     * @brief Возвращает указатель на правило по id.
     * @param id Идентификатор правила.
     * @return Указатель на `Rule` или nullptr, если правило не найдено.
     */
    const Rule* getRule(int id) const;

    /**
     * @brief Загружает правила из текстового файла.
     * @param path Путь к файлу с правилами.
     * @param error Строка для сообщения об ошибке при неудаче.
     * @return true при успешной загрузке, иначе false и `errorMsg` заполнен.
     */
    bool loadFromFile(const std::string& path, std::string& error);

    /**
     * @brief Разбирает одну строку описания правила.
     * @param line Входная строка.
     * @param outRule Выходной объект `Rule` для заполнения.
     * @param error Строка для сообщения об ошибке при неудаче.
     * @return true при успешном парсинге, иначе false.
     */
    static bool parseRuleLine(const std::string& line, Rule& outRule, std::string& error);
};