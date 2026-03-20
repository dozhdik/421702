/*
 * Оркестратор оптимизации размещения хранилищ (переименованный)
 * Вызывает атомарные агенты через SC-память
 */

#pragma once

#include <sc-memory/sc_agent.hpp>

class StorageOptimizationAgent : public ScActionInitiatedAgent
{
public:
  StorageOptimizationAgent();
  ScAddr GetActionClass() const override;
  ScResult DoProgram(ScAction & action) override;

private:
  bool CallFileParseAgent(ScAddr const & inputEntityAddr);
  ScAddr GetParsedNetwork(ScAddr const & inputEntityAddr);
  bool CallDataValidationAgent(ScAddr const & networkAddr);
  ScAddr CallClusteringAgent(ScAddr const & networkAddr, int k);
  bool CallCostCalculationAgent(ScAddr const & variantAddr, ScAddr const & networkAddr);
  ScStructure CallVariantComparisonAgent(
      ScAddr const & variant1Addr,
      ScAddr const & variant2Addr,
      ScAddr const & variant3Addr);
};
