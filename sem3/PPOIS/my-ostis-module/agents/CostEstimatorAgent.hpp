/*
 * Агент оценки/расчёта транспортных затрат (переименован из CostCalculationAgent)
 */

#pragma once

#include <sc-memory/sc_agent.hpp>

class CostEstimatorAgent : public ScActionInitiatedAgent
{
public:
  CostEstimatorAgent();
  ScAddr GetActionClass() const override;
  ScResult DoProgram(ScAction & action) override;
};
