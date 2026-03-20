/**
 * @file rules.cpp
 * @brief Реализация парсинга и хранения правил для машины Поста.
 * @details
 * В этом файле реализованы функции по управлению набором правил и разбору
 * строк правил из текстового файла.
 *
 * Реализованы функции/методы:
 * - Rules()
 * - empty()
 * - clear()
 * - addOrReplaceRule()
 * - removeRule()
 * - getRule()
 * - allRules()
 * - parseRuleLine()
 * - loadFromFile()
 *
 * Автор: Дождиков Александр, гр. 421702
 * @see Rules
 */

#include "rules.h"
#include <sstream>
#include <fstream>
#include <cctype>
#include <algorithm>

/**
 * @brief Конструктор по умолчанию — создаёт пустой контейнер правил.
 */
Rules::Rules() : rules(){}

/**
 * @brief Вспомогательная функция: возвращает верхний регистр строки.
 */
static std::string upperCopy(const std::string& original){
    std::string copy = original;
    std::transform(copy.begin(), copy.end(), copy.begin(), [](unsigned char rule){ return std::toupper(rule); });
    return copy;
}

/**
 * @brief Проверяет, пуст ли набор правил.
 */
bool Rules::empty() const{ 
    return rules.empty(); 
}

/**
 * @brief Очищает все правила.
 */
void Rules::clear(){ 
    rules.clear(); 
}

/**
 * @brief Добавляет или заменяет правило по id.
 * @return true при успешной операции.
 */
bool Rules::addOrReplaceRule(const Rule& rule){
    if(rule.id < 0) return false;  
    if(rule.action == ActionType::NOP && rule.conditional) 
        return false; 
    rules[rule.id] = rule;
    return true;
}

/**
 * @brief Удаляет правило по идентификатору.
 * @return true, если правило найдено и удалено.
 */
bool Rules::removeRule(int id){
    auto it = rules.find(id);
    if(it == rules.end()) return false;
    rules.erase(it);
    return true;
}

/**
 * @brief Возвращает указатель на правило по id или nullptr при отсутствии.
 */
const Rule* Rules::getRule(int id) const{
    auto it = rules.find(id);
    if(it == rules.end()) return nullptr;
    return &it->second;
}

/**
 * @brief Возвращает все правила в виде вектора (копия).
 */
std::vector<Rule> Rules::allRules() const{
    std::vector<Rule> v;
    for(const auto &p : rules) v.push_back(p.second);
    return v;
}

/**
 * @brief Парсит строку описания правила в структуру `Rule`.
 * @param raw Входная строка (включая возможный комментарий после '#').
 * @param outRule Выходной объект `Rule`.
 * @param error Сообщение об ошибке при неудаче.
 * @return true при успешном разборе.
 */
bool Rules::parseRuleLine(const std::string& raw, Rule& outRule, std::string& error){
    std::string line = raw;
    auto pos = line.find('#');
    if(pos != std::string::npos) line = line.substr(0, pos);

    auto L = line.find_first_not_of(" \t\r\n");
    if(L == std::string::npos) return false; 
    auto R = line.find_last_not_of(" \t\r\n");
    line = line.substr(L, R-L+1);

    std::istringstream iss(line);
    std::vector<std::string> tok;
    std::string t;
    while(iss >> t) tok.push_back(t);

    if(tok.size() < 3){
        error = "Недостаточно токенов: " + line;
        return false;
    }

    Rule r;

    try { r.id = std::stoi(tok[0]); }
    catch(...) {
        error = "Некорректный id: " + tok[0];
        return false;
    }

    std::string a = upperCopy(tok[1]);
    if(a == "SET") r.action = ActionType::SET;
    else if(a == "CLR") r.action = ActionType::CLR;
    else if(a == "R" || a == "RIGHT") r.action = ActionType::MOVE_RIGHT;
    else if(a == "L" || a == "LEFT") r.action = ActionType::MOVE_LEFT;
    else if(a == "NOP") r.action = ActionType::NOP;
    else {
        error = "Неизвестное действие: " + tok[1];
        return false;
    }

    if(tok.size() == 3){
        r.conditional = false;
        try { r.next = std::stoi(tok[2]); }
        catch(...) {
            error = "Некорректный next: " + tok[2];
            return false;
        }
        outRule = r;
        return true;
    }

    if(tok.size() == 4){
        r.conditional = true;
        try {
            r.nextIf0 = std::stoi(tok[2]);
            r.nextIf1 = std::stoi(tok[3]);
        } catch(...) {
            error = "Некорректные переходы: " + line;
            return false;
        }
        outRule = r;
        return true;
    }

    error = "Слишком много токенов: " + line;
    return false;
}

/**
 * @brief Загружает правила из файла, игнорируя пустые строки и комментарии.
 * @return true при успешной загрузке, иначе false и `error` содержит сообщение.
 */
bool Rules::loadFromFile(const std::string& path, std::string& error){
    std::ifstream in(path);
    if(!in){
        error = "Не удалось открыть файл: " + path;
        return false;
    }

    rules.clear();
    std::string line;
    int lineno = 0;

    while(std::getline(in, line)){
        ++lineno;

        Rule r;
        std::string err;

        if(!parseRuleLine(line, r, err)){
            if(!err.empty()){
                error = "Ошибка в строке " + std::to_string(lineno) + ": " + err;
                return false;
            }
            continue;
        }

        addOrReplaceRule(r);
    }

    return true;
}
