/*
 * Тесты для CostCalculationAgent
 * Агент рассчитывает транспортные затраты для варианта размещения складов
 */

#include <sc-memory/test/sc_test.hpp>
#include <sc-memory/sc_memory.hpp>
#include "agents/ShopClusteringAgent.hpp"
#include "agents/CostEstimatorAgent.hpp"
#include "keynodes/LogisticsKeynodes.hpp"

using CostCalculationAgentTest = ScMemoryTest;

static ScAddr CreateShop(ScAgentContext & ctx, ScAddr networkAddr, int id, double x, double y, double volume)
{
  ScAddr shopAddr = ctx.GenerateNode(ScType::ConstNode);
  ctx.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::concept_shop, shopAddr);
  ctx.GenerateConnector(ScType::ConstPermPosArc, networkAddr, shopAddr);

  ScAddr idLink = ctx.GenerateLink(ScType::ConstNodeLink);
  ctx.SetLinkContent(idLink, std::to_string(id));
  ScAddr idArc = ctx.GenerateConnector(ScType::ConstCommonArc, shopAddr, idLink);
  ctx.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::nrel_id, idArc);

  ScAddr xLink = ctx.GenerateLink(ScType::ConstNodeLink);
  ctx.SetLinkContent(xLink, std::to_string(x));
  ScAddr xArc = ctx.GenerateConnector(ScType::ConstCommonArc, shopAddr, xLink);
  ctx.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::nrel_x, xArc);

  ScAddr yLink = ctx.GenerateLink(ScType::ConstNodeLink);
  ctx.SetLinkContent(yLink, std::to_string(y));
  ScAddr yArc = ctx.GenerateConnector(ScType::ConstCommonArc, shopAddr, yLink);
  ctx.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::nrel_y, yArc);

  ScAddr volLink = ctx.GenerateLink(ScType::ConstNodeLink);
  ctx.SetLinkContent(volLink, std::to_string(volume));
      ScAddr volArc = ctx.GenerateConnector(ScType::ConstCommonArc, shopAddr, volLink);
      ctx.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::nrel_volume, volArc);

  return shopAddr;
}

static ScAddr CreateNetwork(ScAgentContext & ctx)
{
  ScAddr networkAddr = ctx.GenerateNode(ScType::ConstNode);
  ctx.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::concept_network, networkAddr);
  return networkAddr;
}

static ScAddr ExtractVariant(ScAgentContext & ctx, ScStructure const & result)
{
  ScIterator3Ptr iter = ctx.CreateIterator3(result, ScType::ConstPermPosArc, ScType::ConstNode);
  while (iter->Next())
  {
    ScAddr nodeAddr = iter->Get(2);
    if (ctx.CheckConnector(LogisticsKeynodes::concept_placement_variant, nodeAddr, ScType::ConstPermPosArc))
      return nodeAddr;
  }
  return ScAddr();
}

static double ExtractCost(ScAgentContext & ctx, ScAddr variantAddr)
{
  ScIterator5Ptr costIter = ctx.CreateIterator5(
      variantAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
      ScType::ConstPermPosArc, LogisticsKeynodes::nrel_transport_cost);
  if (costIter->Next())
  {
    std::string costStr;
    ctx.GetLinkContent(costIter->Get(2), costStr);
    return std::stod(costStr);
  }
  return -1.0;
}

// Тест: Расчёт стоимости для всех вариантов (K=1,2,3) и сравнение
TEST_F(CostCalculationAgentTest, CostCalculation_AllVariants)
{
  m_ctx->SubscribeAgent<ShopClusteringAgent>();
  m_ctx->SubscribeAgent<CostEstimatorAgent>();

  ScAddr networkAddr = CreateNetwork(*m_ctx);
  CreateShop(*m_ctx, networkAddr, 1, 10, 15, 200);
  CreateShop(*m_ctx, networkAddr, 2, 25, 30, 350);
  CreateShop(*m_ctx, networkAddr, 3, 45, 20, 180);
  CreateShop(*m_ctx, networkAddr, 4, 35, 45, 280);
  CreateShop(*m_ctx, networkAddr, 5, 55, 35, 320);

  double costs[3] = {0, 0, 0};

  for (int k = 1; k <= 3; k++)
  {
    ScAction clusterAction = m_ctx->GenerateAction(LogisticsKeynodes::action_cluster_shops);
    ScAddr kLink = m_ctx->GenerateLink(ScType::ConstNodeLink);
    m_ctx->SetLinkContent(kLink, std::to_string(k));
    clusterAction.SetArguments(networkAddr, kLink);
    ASSERT_TRUE(clusterAction.InitiateAndWait(10000));
    ASSERT_TRUE(clusterAction.IsFinishedSuccessfully());

    ScAddr variantAddr = ExtractVariant(*m_ctx, clusterAction.GetResult());
    ASSERT_TRUE(variantAddr.IsValid());

    ScAction costAction = m_ctx->GenerateAction(LogisticsKeynodes::action_calculate_transport_cost);
    costAction.SetArguments(variantAddr, networkAddr);
    ASSERT_TRUE(costAction.InitiateAndWait(10000));
    ASSERT_TRUE(costAction.IsFinishedSuccessfully());

    costs[k-1] = ExtractCost(*m_ctx, variantAddr);
    EXPECT_GT(costs[k-1], 0.0);
  }

  EXPECT_GT(costs[0], costs[1]);
  EXPECT_GT(costs[1], costs[2]);

  m_ctx->UnsubscribeAgent<CostEstimatorAgent>();
  m_ctx->UnsubscribeAgent<ShopClusteringAgent>();
}
