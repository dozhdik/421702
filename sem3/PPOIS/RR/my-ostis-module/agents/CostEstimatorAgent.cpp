/*
 * Агент оценки/расчёта транспортных затрат (переименован из CostCalculationAgent)
 */

#include "CostEstimatorAgent.hpp"

#include <sc-memory/sc_memory.hpp>
#include <sc-memory/sc_stream.hpp>
#include <iomanip>
#include <sstream>

#include "../keynodes/LogisticsKeynodes.hpp"
#include "../utils/CsvParser.hpp"
#include "../utils/GeometryUtils.hpp"

using namespace logistics;

CostEstimatorAgent::CostEstimatorAgent()
{
  m_logger = utils::ScLogger(
      utils::ScLogger::ScLogType::File,
      "logs/CostEstimatorAgent.log",
      utils::ScLogLevel::Debug);
}

ScAddr CostEstimatorAgent::GetActionClass() const
{
  return LogisticsKeynodes::action_calculate_transport_cost;
}

ScResult CostEstimatorAgent::DoProgram(ScAction & action)
{
  m_logger.Info("Агент расчёта затрат (CostEstimatorAgent) запущен");

  try
  {
    auto const & [variantAddr, networkAddr] = action.GetArguments<2>();

    if (!variantAddr.IsValid())
    {
      m_logger.Error("Вариант размещения не найден");
      return action.FinishWithError();
    }

    if (!networkAddr.IsValid())
    {
      m_logger.Error("Торговая сеть не найдена");
      return action.FinishWithError();
    }

    // Собираем данные о складах
    std::vector<WarehouseData> warehouses;

    ScIterator5Ptr whIter = m_context.CreateIterator5(
        variantAddr, ScType::ConstCommonArc, ScType::ConstNode,
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_warehouse);

    while (whIter->Next())
    {
      ScAddr warehouseAddr = whIter->Get(2);
      WarehouseData warehouse;

      // ID
      ScIterator5Ptr idIter = m_context.CreateIterator5(
          warehouseAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_id);
      if (idIter->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(idIter->Get(2));
        std::string idStr;
        if (stream && ScStreamConverter::StreamToString(stream, idStr))
          try { warehouse.id = std::stoi(idStr); } catch (...) { warehouse.id = 0; }
      }

      // X
      ScIterator5Ptr xIter = m_context.CreateIterator5(
          warehouseAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_x);
      if (xIter->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(xIter->Get(2));
        std::string xStr;
        if (stream && ScStreamConverter::StreamToString(stream, xStr))
          try { warehouse.position.x = std::stod(xStr); } catch (...) { warehouse.position.x = 0; }
      }

      // Y
      ScIterator5Ptr yIter = m_context.CreateIterator5(
          warehouseAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_y);
      if (yIter->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(yIter->Get(2));
        std::string yStr;
        if (stream && ScStreamConverter::StreamToString(stream, yStr))
          try { warehouse.position.y = std::stod(yStr); } catch (...) { warehouse.position.y = 0; }
      }

      warehouses.push_back(warehouse);
    }

    if (warehouses.empty())
    {
      m_logger.Error("Не найдено складов");
      return action.FinishWithError();
    }

    m_logger.Info("Найдено складов " + std::to_string(warehouses.size()));

    // Собираем данные о магазинах
    std::vector<ShopData> shops;

    ScIterator3Ptr shopIter = m_context.CreateIterator3(
        networkAddr, ScType::ConstPermPosArc, ScType::ConstNode);

    while (shopIter->Next())
    {
      ScAddr shopAddr = shopIter->Get(2);

      if (!m_context.CheckConnector(LogisticsKeynodes::concept_shop, shopAddr, ScType::ConstPermPosArc))
        continue;

      ShopData shop;

      // ID
      ScIterator5Ptr idIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_id);
      if (idIter->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(idIter->Get(2));
        std::string idStr;
        if (stream && ScStreamConverter::StreamToString(stream, idStr))
          try { shop.id = std::stoi(idStr); } catch (...) { shop.id = 0; }
      }

      // X
      ScIterator5Ptr xIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_x);
      if (xIter->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(xIter->Get(2));
        std::string xStr;
        if (stream && ScStreamConverter::StreamToString(stream, xStr))
          try { shop.x = std::stod(xStr); } catch (...) { shop.x = 0; }
      }

      // Y
      ScIterator5Ptr yIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_y);
      if (yIter->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(yIter->Get(2));
        std::string yStr;
        if (stream && ScStreamConverter::StreamToString(stream, yStr))
          try { shop.y = std::stod(yStr); } catch (...) { shop.y = 0; }
      }

      // Volume
      ScIterator5Ptr volIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_volume);
      if (volIter->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(volIter->Get(2));
        std::string volStr;
        if (stream && ScStreamConverter::StreamToString(stream, volStr))
          try { shop.volume = std::stod(volStr); } catch (...) { shop.volume = 0; }
      }

      shops.push_back(shop);
    }

    if (shops.empty())
    {
      m_logger.Error("Не найдено магазинов");
      return action.FinishWithError();
    }

    m_logger.Info("Найдено магазинов " + std::to_string(shops.size()));

    // Расчёт затрат
    double totalCost = GeometryUtils::CalculateTransportCostMultiWarehouse(warehouses, shops);

    m_logger.Info("Затраты " + std::to_string(static_cast<int>(totalCost)) + " руб/мес");

    // Результат
    ScStructure result = m_context.GenerateStructure();

    std::ostringstream oss;
    oss << std::fixed << std::setprecision(0) << totalCost;

    ScAddr costLink = m_context.GenerateLink(ScType::ConstNodeLink);
    m_context.SetLinkContent(costLink, oss.str());

    ScAddr costArc = m_context.GenerateConnector(ScType::ConstCommonArc, variantAddr, costLink);
    ScAddr costAttrArc = m_context.GenerateConnector(
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_transport_cost, costArc);

    result << costLink << costArc << costAttrArc << LogisticsKeynodes::nrel_transport_cost;

    action.SetResult(result);
    m_logger.Info("Агент расчёта затрат успешно завершён");
    return action.FinishSuccessfully();
  }
  catch (utils::ScException const & e)
  {
    m_logger.Error("Исключение SC " + std::string(e.Message()));
    return action.FinishWithError();
  }
  catch (std::exception const & e)
  {
    m_logger.Error("Исключение " + std::string(e.what()));
    return action.FinishWithError();
  }
  catch (...)
  {
    m_logger.Error("Неизвестное исключение");
    return action.FinishWithError();
  }
}
