/*
 * Тесты для DataValidationAgent
 * Агент проверяет корректность входных данных торговой сети
 */

#include <sc-memory/test/sc_test.hpp>
#include <sc-memory/sc_memory.hpp>
#include "agents/DataVerifierAgent.hpp"
#include "keynodes/LogisticsKeynodes.hpp"

using DataValidationAgentTest = ScMemoryTest;

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

static int ExtractShopCount(ScAgentContext & ctx, ScStructure const & result)
{
  ScIterator3Ptr iter = ctx.CreateIterator3(result, ScType::ConstPermPosArc, ScType::ConstNode);
  while (iter->Next())
  {
    ScAddr nodeAddr = iter->Get(2);
    ScIterator5Ptr countIter = ctx.CreateIterator5(
        nodeAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_shop_count);
    if (countIter->Next())
    {
      std::string countStr;
      ctx.GetLinkContent(countIter->Get(2), countStr);
      return std::stoi(countStr);
    }
  }
  return -1;
}

// Тест 1: Валидация корректных данных (5 и 15 магазинов)
TEST_F(DataValidationAgentTest, ValidData)
{
  m_ctx->SubscribeAgent<DataVerifierAgent>();

  struct TestCase {
    int shopCount;
    std::vector<std::tuple<int, double, double, double>> shops;
  };

  TestCase cases[] = {
    {5, {{1,10,15,200}, {2,25,30,350}, {3,45,20,180}, {4,35,45,280}, {5,55,35,320}}},
    {15, {{1,10,15,200}, {2,25,30,350}, {3,45,20,180}, {4,35,45,280}, {5,55,35,320},
          {6,12,40,150}, {7,65,25,240}, {8,30,12,190}, {9,8,25,160}, {10,48,55,220},
          {11,70,40,200}, {12,18,60,130}, {13,40,8,170}, {14,22,50,210}, {15,60,15,260}}}
  };

  for (auto const & tc : cases)
  {
    ScAddr networkAddr = CreateNetwork(*m_ctx);
    for (auto const & shop : tc.shops)
    {
      CreateShop(*m_ctx, networkAddr, std::get<0>(shop), std::get<1>(shop), 
                 std::get<2>(shop), std::get<3>(shop));
    }

    ScAction action = m_ctx->GenerateAction(LogisticsKeynodes::action_validate_network);
    action.SetArguments(networkAddr);
    ASSERT_TRUE(action.InitiateAndWait(10000));
    ASSERT_TRUE(action.IsFinishedSuccessfully());

    int count = ExtractShopCount(*m_ctx, action.GetResult());
    EXPECT_EQ(count, tc.shopCount);
  }

  m_ctx->UnsubscribeAgent<DataVerifierAgent>();
}

// Тест 2: Ошибка - недостаточно магазинов
TEST_F(DataValidationAgentTest, InvalidData_TooFewShops)
{
  m_ctx->SubscribeAgent<DataVerifierAgent>();

  ScAddr networkAddr = CreateNetwork(*m_ctx);
  CreateShop(*m_ctx, networkAddr, 1, 10, 15, 200);
  CreateShop(*m_ctx, networkAddr, 2, 25, 30, 350);

  ScAction action = m_ctx->GenerateAction(LogisticsKeynodes::action_validate_network);
  action.SetArguments(networkAddr);
  ASSERT_TRUE(action.InitiateAndWait(10000));
  EXPECT_TRUE(action.IsFinishedWithError());

  m_ctx->UnsubscribeAgent<DataVerifierAgent>();
}
