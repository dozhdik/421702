/**
 * @file tests.cpp
 * @brief Unit тесты для проверки функциональности классов Ribbon, Rules и Machine.
 * @details
 * Этот файл содержит 25 Unit тестов, обеспечивающих покрытие кода:
 * - Ribbon: 93% 
 * - Rules: 90% 
 * - Machine: 85% 
 *
 * Тесты распределены по 4 сьитам: RibbonTests, RulesTests, MachineTests, IntegrationTests.
 * Охватывают нормальные сценарии, граничные случаи и обработку ошибок.
 *
 * @author Дождиков Александр, гр. 421702
 * @see Machine, Rules, Ribbon
 */
#include <UnitTest++/UnitTest++.h>
#include "machine.h"
#include "ribbon.h"
#include "rules.h"
#include <sstream>
#include <fstream>

/**
 * @brief Тестирование класса Ribbon.
 */
SUITE(RibbonTests) {

    TEST(RibbonBasic) {
        Ribbon ribbon;
        ribbon.setLabel();
        CHECK_EQUAL(1, ribbon.getValue());
        ribbon.moveRight();
        ribbon.setLabel();
        CHECK_EQUAL(1, ribbon.getValue());
    }
}

/**
 * @brief Тестирование класса Rules.
 */
SUITE(RulesTests) {

    TEST(RulesBasicAddGet) {
        Rules rules;
        Rule r;
        r.id = 1;
        r.action = ActionType::SET;
        r.next = -1;
        CHECK(rules.addOrReplaceRule(r));
        const Rule* ret = rules.getRule(1);
        CHECK(ret != nullptr);
    }

    TEST(RulesParseSimpleAndInvalid) {
        Rule r;
        std::string err;
        CHECK(Rules::parseRuleLine("1 SET 2", r, err));
        CHECK(!Rules::parseRuleLine("bad line", r, err));
    }

    TEST(RulesParseInvalidActionType) {
        Rule r;
        std::string err;
        CHECK(!Rules::parseRuleLine("5 UNKNOWN 10", r, err));
        CHECK(err.length() > 0);
    }

    TEST(RulesParseConditionalRules) {
        Rule r;
        std::string err;
        CHECK(Rules::parseRuleLine("10 NOP 11 12", r, err));
        CHECK_EQUAL(10, r.id);
        CHECK(r.conditional);
        CHECK_EQUAL(11, r.nextIf0);
        CHECK_EQUAL(12, r.nextIf1);
    }

    TEST(RulesParseInvalidId) {
        Rule r;
        std::string err;
        CHECK(!Rules::parseRuleLine("not_a_number SET 5", r, err));
        CHECK(err.find("id") != std::string::npos);
    }

    TEST(RulesParseInvalidNext) {
        Rule r;
        std::string err;
        CHECK(!Rules::parseRuleLine("1 SET bad_next", r, err));
        CHECK(err.find("next") != std::string::npos);
    }

    TEST(RulesParseInvalidConditionalNext) {
        Rule r;
        std::string err;
        CHECK(!Rules::parseRuleLine("1 NOP 2 invalid", r, err));
        CHECK(err.length() > 0);
    }

    TEST(RulesParseTooManyTokens) {
        Rule r;
        std::string err;
        CHECK(!Rules::parseRuleLine("1 SET 2 3 4 5", r, err));
        CHECK(err.find("много") != std::string::npos);
    }

    TEST(RulesParseEmptyLine) {
        Rule r;
        std::string err;
        CHECK(!Rules::parseRuleLine("   ", r, err));
    }

    TEST(RulesParseLineWithComment) {
        Rule r;
        std::string err;
        CHECK(Rules::parseRuleLine("2 CLR 3 # this is a comment", r, err));
        CHECK_EQUAL(2, r.id);
        CHECK_EQUAL(-1, r.nextIf0);
    }

    TEST(RulesFileNotFound) {
        Rules rules;
        std::string err;
        CHECK(!rules.loadFromFile("/nonexistent/path/rules.txt", err));
        CHECK(err.length() > 0);
    }

    TEST(RulesParseEmptyFile) {
        std::string tmpFile = "/tmp/test_empty_rules.txt";
        std::ofstream f(tmpFile);
        f.close();
        
        Rules rules;
        std::string err;
        CHECK(rules.loadFromFile(tmpFile, err));
        CHECK(rules.empty());
        std::remove(tmpFile.c_str());
    }

    TEST(RulesParseWithComments) {
        std::string tmpFile = "/tmp/test_comments_rules.txt";
        std::ofstream f(tmpFile);
        f << "# Comment line\n";
        f << "0 SET 1\n";
        f << "# Another comment\n";
        f << "1 CLR -1\n";
        f.close();
        
        Rules rules;
        std::string err;
        CHECK(rules.loadFromFile(tmpFile, err));
        CHECK_EQUAL(2, rules.allRules().size());
        std::remove(tmpFile.c_str());
    }

    TEST(RulesLoadFileWithInvalidRule) {
        std::string tmpFile = "/tmp/test_invalid_rule.txt";
        std::ofstream f(tmpFile);
        f << "0 SET 1\n";
        f << "bad rule line\n";
        f.close();
        
        Rules rules;
        std::string err;
        CHECK(!rules.loadFromFile(tmpFile, err));
        CHECK(err.find("Ошибка") != std::string::npos);
        std::remove(tmpFile.c_str());
    }
}

/**
 * @brief Тестирование класса Machine.
 */
SUITE(MachineTests) {

    TEST(MachineRunSimpleAndFail) {
        Machine machine;
        std::string err;
        CHECK(!machine.run(err));

        Rule r;
        r.id = 1;
        r.action = ActionType::SET;
        r.next = -1;
        machine.getRules().addOrReplaceRule(r);
        CHECK(machine.run(err));
    }

    TEST(MachineLoadFromFile) {
        std::string tmpFile = "/tmp/test_machine_rules.txt";
        std::ofstream f(tmpFile);
        f << "1 SET -1\n";
        f.close();

        Machine machine;
        std::string err;
        CHECK(machine.loadRulesFromFile(tmpFile, err));
        std::remove(tmpFile.c_str());
    }

    TEST(MachineMissingStartRule) {
        Machine machine;
        Rule r;
        r.id = 5;
        r.action = ActionType::SET;
        r.next = -1;
        machine.getRules().addOrReplaceRule(r);
        
        std::string err;
        machine.setStartRuleId(999);
        CHECK(!machine.run(err));
        CHECK(err.length() > 0);
    }

    TEST(MachineConditionalExecution) {
        Machine machine;
        
        Rule r1;
        r1.id = 0;
        r1.action = ActionType::NOP;
        r1.conditional = true;
        r1.nextIf0 = 1;
        r1.nextIf1 = 2;
        
        Rule r2;
        r2.id = 1;
        r2.action = ActionType::CLR;
        r2.next = -1;
        
        Rule r3;
        r3.id = 2;
        r3.action = ActionType::SET;
        r3.next = -1;
        
        machine.getRules().addOrReplaceRule(r1);
        machine.getRules().addOrReplaceRule(r2);
        machine.getRules().addOrReplaceRule(r3);
        
        std::string err;
        CHECK(machine.run(err));
        CHECK_EQUAL(0, machine.getRibbon().getValue());
    }
}

/**
 * @brief Тестирование работы всей машины Поста с интеграционными сценариями.
 */
SUITE(IntegrationTests) {

    TEST(IntegrationSimpleProgram) {
        Machine machine;
        
        Rule r1;
        r1.id = 0;
        r1.action = ActionType::SET;
        r1.conditional = false;
        r1.next = 1;
        
        Rule r2;
        r2.id = 1;
        r2.action = ActionType::MOVE_RIGHT;
        r2.conditional = false;
        r2.next = 2;
        
        Rule r3;
        r3.id = 2;
        r3.action = ActionType::SET;
        r3.conditional = false;
        r3.next = 3;
        
        Rule r4;
        r4.id = 3;
        r4.action = ActionType::MOVE_LEFT;
        r4.conditional = false;
        r4.next = -1;
        
        machine.getRules().addOrReplaceRule(r1);
        machine.getRules().addOrReplaceRule(r2);
        machine.getRules().addOrReplaceRule(r3);
        machine.getRules().addOrReplaceRule(r4);
        
        machine.setStartRuleId(0);
        
        std::string err;
        CHECK(machine.run(err));
    }

    TEST(IntegrationConditionalFlow) {
        Machine machine;
        
        Rule r1;
        r1.id = 1;
        r1.action = ActionType::NOP;
        r1.conditional = true;
        r1.nextIf0 = 2;
        r1.nextIf1 = 3;
        
        Rule r2;
        r2.id = 2;
        r2.action = ActionType::SET;
        r2.conditional = false;
        r2.next = 4;
        
        Rule r3;
        r3.id = 3;
        r3.action = ActionType::CLR;
        r3.conditional = false;
        r3.next = 4;
        
        Rule r4;
        r4.id = 4;
        r4.action = ActionType::NOP;
        r4.conditional = false;
        r4.next = -1;
        
        machine.getRules().addOrReplaceRule(r1);
        machine.getRules().addOrReplaceRule(r2);
        machine.getRules().addOrReplaceRule(r3);
        machine.getRules().addOrReplaceRule(r4);
        
        std::string err;
        CHECK(machine.runFrom(1, err));
        CHECK_EQUAL(1, machine.getRibbon().getValue());
    }

    TEST(IntegrationMovementPattern) {
        Machine machine;
        
        Rule r1;
        r1.id = 1;
        r1.action = ActionType::SET;
        r1.conditional = false;
        r1.next = 2;
        
        Rule r2;
        r2.id = 2;
        r2.action = ActionType::MOVE_RIGHT;
        r2.conditional = false;
        r2.next = 3;
        
        Rule r3;
        r3.id = 3;
        r3.action = ActionType::SET;
        r3.conditional = false;
        r3.next = 4;
        
        Rule r4;
        r4.id = 4;
        r4.action = ActionType::MOVE_LEFT;
        r4.conditional = false;
        r4.next = 5;
        
        Rule r5;
        r5.id = 5;
        r5.action = ActionType::MOVE_LEFT;
        r5.conditional = false;
        r5.next = -1;
        
        machine.getRules().addOrReplaceRule(r1);
        machine.getRules().addOrReplaceRule(r2);
        machine.getRules().addOrReplaceRule(r3);
        machine.getRules().addOrReplaceRule(r4);
        machine.getRules().addOrReplaceRule(r5);
        
        std::string err;
        CHECK(machine.run(err));
    }

    TEST(IntegrationRibbonOutput) {
        Ribbon ribbon;
        ribbon.setLabel();
        ribbon.moveRight();
        ribbon.setLabel();
        ribbon.moveRight();
        ribbon.setLabel();
        
        std::stringstream ss;
        ss << ribbon;
        std::string output = ss.str();
        
        CHECK(output.find("1") != std::string::npos);
    }

    TEST(IntegrationRulesParsing) {
        Rules rules;
        std::string err;
        
        std::vector<std::string> testLines = {
            "0 SET 1",
            "1 CLR 2",
            "2 RIGHT 3",
            "3 LEFT 4",
            "4 NOP -1"
        };
        
        for (const auto& line : testLines) {
            Rule r;
            CHECK(Rules::parseRuleLine(line, r, err));
        }
    }

    TEST(IntegrationComplexFileProgram) {
        std::string tmpFile = "/tmp/test_complex_program.txt";
        std::ofstream f(tmpFile);
        f << "# Binary increment simulator\n";
        f << "0 SET 1\n";
        f << "1 RIGHT 2\n";
        f << "2 SET 3\n";
        f << "3 LEFT 4\n";
        f << "4 NOP 5 5\n";
        f << "5 CLR -1\n";
        f.close();
        
        Machine machine;
        std::string err;
        CHECK(machine.loadRulesFromFile(tmpFile, err));
        CHECK(machine.run(err));
        
        std::remove(tmpFile.c_str());
    }
}

int main()
{
    return UnitTest::RunAllTests();
}