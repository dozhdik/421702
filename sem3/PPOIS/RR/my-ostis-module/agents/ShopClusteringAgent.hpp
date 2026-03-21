/*
 * Агент кластеризации магазинов (переименованный ClusteringAgent)
 */

#pragma once

#include <sc-memory/sc_agent.hpp>

class ShopClusteringAgent : public ScActionInitiatedAgent
{
public:
  ShopClusteringAgent();
  ScAddr GetActionClass() const override;
  ScResult DoProgram(ScAction & action) override;
};
