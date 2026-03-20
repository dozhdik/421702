/*
 * Интеграционные тесты модуля логистики
 * Проверка полной цепочки агентов: Validation -> Clustering -> Cost -> Comparison
 */

#include <sc-memory/test/sc_test.hpp>
#include <sc-memory/sc_memory.hpp>
#include "agents/DataVerifierAgent.hpp"
#include "agents/ShopClusteringAgent.hpp"
#include "agents/CostEstimatorAgent.hpp"
#include "agents/VariantSelectorAgent.hpp"
#include "keynodes/LogisticsKeynodes.hpp"

using IntegrationTest = ScMemoryTest;

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

static int CountWarehouses(ScAgentContext & ctx, ScAddr variantAddr)
{
  int count = 0;
  ScIterator5Ptr iter = ctx.CreateIterator5(
      variantAddr, ScType::ConstCommonArc, ScType::ConstNode,
      ScType::ConstPermPosArc, LogisticsKeynodes::nrel_warehouse);
  while (iter->Next()) count++;
  return count;
}

static ScAddr ExtractBestVariant(ScAgentContext & ctx, ScStructure const & result)
{
  ScIterator3Ptr iter = ctx.CreateIterator3(result, ScType::ConstPermPosArc, ScType::ConstNode);
  while (iter->Next())
  {
    ScAddr nodeAddr = iter->Get(2);
    ScIterator5Ptr recIter = ctx.CreateIterator5(
        nodeAddr, ScType::ConstCommonArc, ScType::ConstNode,
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_recommendation);
    if (recIter->Next())
      return recIter->Get(2);
  }
  return ScAddr();
}

// Тест: Полный пайплайн с 5 магазинами
TEST_F(IntegrationTest, FullPipeline)
{
  m_ctx->SubscribeAgent<DataVerifierAgent>();
  m_ctx->SubscribeAgent<ShopClusteringAgent>();
  m_ctx->SubscribeAgent<CostEstimatorAgent>();
  m_ctx->SubscribeAgent<VariantSelectorAgent>();

  ScAddr networkAddr = CreateNetwork(*m_ctx);
  CreateShop(*m_ctx, networkAddr, 1, 10, 15, 200);
  CreateShop(*m_ctx, networkAddr, 2, 25, 30, 350);
  CreateShop(*m_ctx, networkAddr, 3, 45, 20, 180);
  CreateShop(*m_ctx, networkAddr, 4, 35, 45, 280);
  CreateShop(*m_ctx, networkAddr, 5, 55, 35, 320);

  // Валидация
  ScAction validateAction = m_ctx->GenerateAction(LogisticsKeynodes::action_validate_network);
  validateAction.SetArguments(networkAddr);
  ASSERT_TRUE(validateAction.InitiateAndWait(10000));
  ASSERT_TRUE(validateAction.IsFinishedSuccessfully());

  // Кластеризация и расчёт для K=1,2,3
  std::vector<ScAddr> variants(3);
  for (int k = 1; k <= 3; k++)
  {
    ScAction clusterAction = m_ctx->GenerateAction(LogisticsKeynodes::action_cluster_shops);
    ScAddr kLink = m_ctx->GenerateLink(ScType::ConstNodeLink);
    m_ctx->SetLinkContent(kLink, std::to_string(k));
    clusterAction.SetArguments(networkAddr, kLink);
    ASSERT_TRUE(clusterAction.InitiateAndWait(10000));
    ASSERT_TRUE(clusterAction.IsFinishedSuccessfully());

    variants[k-1] = ExtractVariant(*m_ctx, clusterAction.GetResult());
    ASSERT_TRUE(variants[k-1].IsValid());
    EXPECT_EQ(CountWarehouses(*m_ctx, variants[k-1]), k);

    ScAction costAction = m_ctx->GenerateAction(LogisticsKeynodes::action_calculate_transport_cost);
    costAction.SetArguments(variants[k-1], networkAddr);
    ASSERT_TRUE(costAction.InitiateAndWait(10000));
    ASSERT_TRUE(costAction.IsFinishedSuccessfully());
  }

  // Сравнение вариантов
  ScAction compareAction = m_ctx->GenerateAction(LogisticsKeynodes::action_select_best_variant);
  compareAction.SetArguments(variants[0], variants[1], variants[2]);
  ASSERT_TRUE(compareAction.InitiateAndWait(10000));
  ASSERT_TRUE(compareAction.IsFinishedSuccessfully());

  ScAddr bestVariant = ExtractBestVariant(*m_ctx, compareAction.GetResult());
  ASSERT_TRUE(bestVariant.IsValid());

  m_ctx->UnsubscribeAgent<VariantSelectorAgent>();
  m_ctx->UnsubscribeAgent<CostEstimatorAgent>();
  m_ctx->UnsubscribeAgent<ShopClusteringAgent>();
  m_ctx->UnsubscribeAgent<DataVerifierAgent>();
}
