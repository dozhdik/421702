/*
 * Тесты для ClusteringAgent
 * Агент выполняет K-means кластеризацию магазинов и определяет координаты складов
 */

#include <sc-memory/test/sc_test.hpp>
#include <sc-memory/sc_memory.hpp>
#include <cmath>
#include "agents/ShopClusteringAgent.hpp"
#include "keynodes/LogisticsKeynodes.hpp"
#include "utils/GeometryUtils.hpp"

using namespace logistics;
using ClusteringAgentTest = ScMemoryTest;

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

struct WarehouseCoord { double x, y; };

static std::vector<WarehouseCoord> ExtractWarehouses(ScAgentContext & ctx, ScStructure const & result)
{
  std::vector<WarehouseCoord> coords;
  ScIterator3Ptr variantIt = ctx.CreateIterator3(result, ScType::ConstPermPosArc, ScType::ConstNode);
  
  while (variantIt->Next())
  {
    ScAddr nodeAddr = variantIt->Get(2);
    ScIterator5Ptr whIt = ctx.CreateIterator5(
        nodeAddr, ScType::ConstCommonArc, ScType::ConstNode,
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_warehouse);

    while (whIt->Next())
    {
      ScAddr warehouseAddr = whIt->Get(2);
      WarehouseCoord wh = {0, 0};

      ScIterator5Ptr xIt = ctx.CreateIterator5(
          warehouseAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_x);
      if (xIt->Next())
      {
        std::string xStr;
        ctx.GetLinkContent(xIt->Get(2), xStr);
        wh.x = std::stod(xStr);
      }

      ScIterator5Ptr yIt = ctx.CreateIterator5(
          warehouseAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_y);
      if (yIt->Next())
      {
        std::string yStr;
        ctx.GetLinkContent(yIt->Get(2), yStr);
        wh.y = std::stod(yStr);
      }

      coords.push_back(wh);
    }
  }
  return coords;
}

// Тест 1: Кластеризация с K=1,2,3
TEST_F(ClusteringAgentTest, Clustering_K1_K2_K3)
{
  m_ctx->SubscribeAgent<ShopClusteringAgent>();

  std::vector<ShopData> shops = {
    {1, "", 10, 15, 200}, {2, "", 25, 30, 350}, {3, "", 45, 20, 180},
    {4, "", 35, 45, 280}, {5, "", 55, 35, 320}
  };

  ScAddr networkAddr = CreateNetwork(*m_ctx);
  for (auto const & shop : shops)
    CreateShop(*m_ctx, networkAddr, shop.id, shop.x, shop.y, shop.volume);

  for (int k = 1; k <= 3; k++)
  {
    auto expected = GeometryUtils::KMeansClustering(shops, k);

    ScAction action = m_ctx->GenerateAction(LogisticsKeynodes::action_cluster_shops);
    ScAddr kLink = m_ctx->GenerateLink(ScType::ConstNodeLink);
    m_ctx->SetLinkContent(kLink, std::to_string(k));
    action.SetArguments(networkAddr, kLink);

    ASSERT_TRUE(action.InitiateAndWait(10000));
    ASSERT_TRUE(action.IsFinishedSuccessfully());

    auto coords = ExtractWarehouses(*m_ctx, action.GetResult());
    ASSERT_EQ(coords.size(), static_cast<size_t>(k));

    if (k == 1)
    {
      EXPECT_NEAR(coords[0].x, expected[0].position.x, 0.1);
      EXPECT_NEAR(coords[0].y, expected[0].position.y, 0.1);
    }
    else
    {
      for (size_t i = 0; i < coords.size(); i++)
      {
        EXPECT_GE(coords[i].x, 10.0);
        EXPECT_LE(coords[i].x, 55.0);
        EXPECT_GE(coords[i].y, 15.0);
        EXPECT_LE(coords[i].y, 45.0);
      }
      if (k == 2)
      {
        double dist = std::sqrt(std::pow(coords[0].x - coords[1].x, 2) + 
                               std::pow(coords[0].y - coords[1].y, 2));
        EXPECT_GT(dist, 5.0);
      }
    }
  }

  m_ctx->UnsubscribeAgent<ShopClusteringAgent>();
}

// Тест 2: Ошибка - невалидное K=0
TEST_F(ClusteringAgentTest, Error_InvalidK_Zero)
{
  m_ctx->SubscribeAgent<ShopClusteringAgent>();

  ScAddr networkAddr = CreateNetwork(*m_ctx);
  CreateShop(*m_ctx, networkAddr, 1, 10, 15, 200);
  CreateShop(*m_ctx, networkAddr, 2, 25, 30, 350);
  CreateShop(*m_ctx, networkAddr, 3, 45, 20, 180);

  ScAction action = m_ctx->GenerateAction(LogisticsKeynodes::action_cluster_shops);
  ScAddr kLink = m_ctx->GenerateLink(ScType::ConstNodeLink);
  m_ctx->SetLinkContent(kLink, "0");
  action.SetArguments(networkAddr, kLink);

  ASSERT_TRUE(action.InitiateAndWait(10000));
  EXPECT_TRUE(action.IsFinishedWithError());

  m_ctx->UnsubscribeAgent<ShopClusteringAgent>();
}

// Тест 3: Ошибка - K больше количества магазинов
TEST_F(ClusteringAgentTest, Error_K_MoreThanShops)
{
  m_ctx->SubscribeAgent<ShopClusteringAgent>();

  ScAddr networkAddr = CreateNetwork(*m_ctx);
  CreateShop(*m_ctx, networkAddr, 1, 10, 15, 200);
  CreateShop(*m_ctx, networkAddr, 2, 25, 30, 350);

  ScAction action = m_ctx->GenerateAction(LogisticsKeynodes::action_cluster_shops);
  ScAddr kLink = m_ctx->GenerateLink(ScType::ConstNodeLink);
  m_ctx->SetLinkContent(kLink, "5");
  action.SetArguments(networkAddr, kLink);

  ASSERT_TRUE(action.InitiateAndWait(10000));
  EXPECT_TRUE(action.IsFinishedWithError());

  m_ctx->UnsubscribeAgent<ShopClusteringAgent>();
}
