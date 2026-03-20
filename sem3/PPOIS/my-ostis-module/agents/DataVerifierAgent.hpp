/*
 * Агент проверки и валидации входных данных (переименован DataValidationAgent)
 */

#pragma once

#include <sc-memory/sc_agent.hpp>

class DataVerifierAgent : public ScActionInitiatedAgent
{
public:
  DataVerifierAgent();
  ScAddr GetActionClass() const override;
  ScResult DoProgram(ScAction & action) override;
};
