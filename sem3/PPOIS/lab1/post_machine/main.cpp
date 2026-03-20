/**
 * @file main.cpp
 * @brief CLI для управления машиной Поста.
 * @details
 * В этом файле реализовано текстовое интерфейсное приложение для работы с
 * машиной Поста: ввод ленты, загрузка и редактирование правил, просмотр состояния
 * ленты и запуск исполнения программы.
 *
 * Реализованы функции:
 * - printMenu()
 * - showRules()
 * - main()
 *
 * @author Дождиков Александр, гр. 421702
 * @see Machine
 */

#include <iostream>
#include <string>
#include <limits>
#include "machine.h"

/**
 * @brief Выводит главное меню в консоль.
 * @details Отображает список пунктов меню для управления машиной Поста.
 */
void printMenu(){
    std::cout << "\nМеню:\n"
              << "1. Ввести ленту\n"
              << "2. Загрузить программу (из файла)\n"
              << "3. Редактирование правил (добавить/удалить)\n"
              << "4. Просмотр правил\n"
              << "5. Состояние ленты\n"
              << "6. Запуск программы\n"
              << "0. Выход\n"
              << "Выберите пункт: ";
} 

/**
 * @brief Выводит список правил в человекочитаемом виде.
 * @param rules Ссылка на объект правил для отображения.
 * @details Выводит все правила с указанием id, действия и переходов.
 */
void showRules(const Rules& rules){
    auto all = rules.allRules();
    if(all.empty()){
        std::cout << "(правил нет)\n";
        return;
    }
    std::cout << "Список правил:\n";
    for(const auto& r : all){
        std::cout << r.id << " ";
        switch(r.action){
            case ActionType::SET: std::cout << "SET "; break;
            case ActionType::CLR: std::cout << "CLR "; break;
            case ActionType::MOVE_LEFT: std::cout << "LEFT "; break;
            case ActionType::MOVE_RIGHT: std::cout << "RIGHT "; break;
            case ActionType::NOP: std::cout << "NOP "; break;
        }
        if(r.conditional){
            std::cout << (r.nextIf0 == -1 ? "-1" : std::to_string(r.nextIf0))
                      << " "
                      << (r.nextIf1 == -1 ? "-1" : std::to_string(r.nextIf1));
        } else {
            std::cout << (r.next == -1 ? "-1" : std::to_string(r.next));
        }
        std::cout << "\n";
    }
}

/**
 * @brief Точка входа CLI приложения для машины Поста.
 * @param argc Количество аргументов командной строки.
 * @param argv Массив аргументов командной строки (путь к файлу правил, флаг --log).
 * @return Код возврата (0 при нормальном завершении).
 * @details Обрабатывает аргументы командной строки, создаёт машину, предоставляет
 * интерактивное меню для управления лентой, правилами и запуска исполнения программы.
 */
int main(int argc, char* argv[]){
    std::string rulesPath;
    bool logFlag = false;
    if(argc >= 2){
        rulesPath = argv[1];
        if(argc >= 3){
            std::string secondArg = argv[2];
            if(secondArg == "--log") logFlag = true;
        }
    }

    Machine machine;
    machine.setLogging(logFlag);

    if(!rulesPath.empty()){
        std::string error;
        if(!machine.loadRulesFromFile(rulesPath, error)){
            std::cout << "Не удалось загрузить правила: " << error << std::endl;
        } else {
            std::cout << "Правила загружены из " << rulesPath << std::endl;
        }
    }

    while(true){
        printMenu();
        int choice;
        if(!(std::cin >> choice)){
            std::cin.clear();
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            std::cout << "Неверный ввод. Попробуйте снова.\n";
            continue;
        }
        std::string dummy;
        std::getline(std::cin, dummy);

        if(choice == 0) break;

        switch(choice){
            case 1:
            {
            std::cout << "Введите ленту (строка из 0 и 1): ";
            std::string newRibbon;
            std::getline(std::cin, newRibbon);

            bool correct = true;
            for(char cell : newRibbon){
                if(cell != '0' && cell != '1'){
                    correct = false;
                    break;
            }
            }
            if(!correct){
                std::cout << "Ошибка: допускаются только символы '0' и '1'.\n";
                break;
            }

            Ribbon &ribbon = machine.getRibbon();
            ribbon.clear(); 

            for(size_t i = 0; i < newRibbon.size(); ++i){
                if(newRibbon[i] == '1') ribbon.setLabel();
                else ribbon.removeLabel();

                if(i + 1 < newRibbon.size())
                    ribbon.moveRight();
            }

            for(size_t i = 0; i + 1 < newRibbon.size(); ++i)
                ribbon.moveLeft();

            std::cout << "Лента установлена:\n" << ribbon;
            break;
            }
            case 2:
            {
                std::cout << "Введите путь к файлу с правилами: ";
                std::string path;
                std::getline(std::cin, path);
                std::string error;
                if(machine.loadRulesFromFile(path, error)) {
                    std::cout << "Правила успешно загружены.\n";
                } else {
                    std::cout << "Ошибка загрузки: " << error << std::endl;
                }
                break;
            }
            case 3:
            {
            std::cout << "Редактирование правил:\n1 - добавить/заменить\n2 - удалить\nЛюбая другая клавиша - отмена\nВыберите действие: ";
            int option;
            if(!(std::cin >> option)) { std::cin.clear(); std::getline(std::cin, dummy); break; }
            std::getline(std::cin, dummy);

            if(option == 1){
                std::cout << "Введите правило в одной строке (формат как в файле):\n";
                std::string line;
                std::getline(std::cin, line);
                std::string err;
                Rule parsed;

            if(!Rules::parseRuleLine(line, parsed, err)){
                std::cout << "Ошибка разбора: " << err << std::endl;
                } else {
                    machine.getRules().addOrReplaceRule(parsed);
                    std::cout << "Правило добавлено/заменено.\n";
                }
            }
            else if(option == 2){
                std::cout << "Введите id правила для удаления: ";
                int id;
                if(!(std::cin >> id)) { std::cin.clear(); std::getline(std::cin,dummy); break; }
                std::getline(std::cin, dummy);
                if(machine.getRules().removeRule(id)) std::cout << "Удалено.\n";
                else std::cout << "Правило с таким id не найдено.\n";
            }

            break;
            }
            case 4:
            {
                showRules(machine.getRules());
                break;
            }
            case 5:
            {
                std::cout << "Состояние ленты:\n" << machine.getRibbon();
                break;
            }
            case 6:
            {
                std::cout << "Запуск программы.\n";
                std::string error;
                if(machine.run(error)) std::cout << "Выполнение завершено.\n";
                else std::cout << "Ошибка выполнения: " << error << std::endl;
                break;
            }
            default:
                std::cout << "Неверный пункт меню.\n";
        }
    }

    std::cout << "Выход.\n";
    return 0;
}