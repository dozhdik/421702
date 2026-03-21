/*
 * Агент выбора варианта размещения (рефактор исходного VariantComparisonAgent)
 */

#pragma once

#include <sc-memory/sc_agent.hpp>

class VariantSelectorAgent : public ScActionInitiatedAgent
{
public:
  VariantSelectorAgent();
  ScAddr GetActionClass() const override;
  ScResult DoProgram(ScAction & action) override;
};
