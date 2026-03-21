/*
 * Агент кластеризации магазинов (переименованный ClusteringAgent)
 */

#include "ShopClusteringAgent.hpp"

#include <sc-memory/sc_memory.hpp>
#include <sc-memory/sc_stream.hpp>

#include "../keynodes/LogisticsKeynodes.hpp"
#include "../utils/CsvParser.hpp"
#include "../utils/GeometryUtils.hpp"

using namespace logistics;

ShopClusteringAgent::ShopClusteringAgent()
{
  m_logger = utils::ScLogger(
      utils::ScLogger::ScLogType::File,
      "logs/ShopClusteringAgent.log",
      utils::ScLogLevel::Debug);
}

ScAddr ShopClusteringAgent::GetActionClass() const
{
  return LogisticsKeynodes::action_cluster_shops;
}

ScResult ShopClusteringAgent::DoProgram(ScAction & action)
{
  m_logger.Info("Агент кластеризации запущен");

  try
  {
    auto const & [networkAddr, kValueAddr] = action.GetArguments<2>();

    if (!networkAddr.IsValid())
    {
      m_logger.Error("Торговая сеть не найдена");
      return action.FinishWithError();
    }

    if (!kValueAddr.IsValid())
    {
      m_logger.Error("Количество кластеров не указано");
      return action.FinishWithError();
    }

    ScStreamPtr kStream = m_context.GetLinkContent(kValueAddr);
    if (!kStream || !kStream->IsValid())
    {
      m_logger.Error("Не удалось получить значение K");
      return action.FinishWithError();
    }

    std::string kStr;
    if (!ScStreamConverter::StreamToString(kStream, kStr))
    {
      m_logger.Error("Не удалось преобразовать K в строку");
      return action.FinishWithError();
    }

    int k = 0;
    try
    {
      k = std::stoi(kStr);
    }
    catch (...)
    {
      m_logger.Error("Невалидное значение K " + kStr);
      return action.FinishWithError();
    }

    if (k <= 0 || k > 10)
    {
      m_logger.Error("K должно быть от 1 до 10");
      return action.FinishWithError();
    }

    m_logger.Info("Кластеризация с K = " + std::to_string(k));

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

    if (shops.size() < static_cast<size_t>(k))
    {
      m_logger.Error("Недостаточно магазинов для кластеризации");
      return action.FinishWithError();
    }

    m_logger.Info("Найдено магазинов " + std::to_string(shops.size()));

    // Кластеризация
    std::vector<WarehouseData> warehouses = GeometryUtils::KMeansClustering(shops, k);

    m_logger.Info("Создано складов " + std::to_string(warehouses.size()));

    // Результат
    ScStructure result = m_context.GenerateStructure();

    ScAddr variantAddr = m_context.GenerateNode(ScType::ConstNode);
    result << variantAddr;

    ScAddr variantClassArc = m_context.GenerateConnector(
        ScType::ConstPermPosArc, LogisticsKeynodes::concept_placement_variant, variantAddr);
    result << variantClassArc << LogisticsKeynodes::concept_placement_variant;

    for (auto const & warehouse : warehouses)
    {
      ScAddr warehouseAddr = m_context.GenerateNode(ScType::ConstNode);
      result << warehouseAddr;

      ScAddr whClassArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::concept_warehouse, warehouseAddr);
      result << whClassArc << LogisticsKeynodes::concept_warehouse;

      ScAddr whArc = m_context.GenerateConnector(ScType::ConstCommonArc, variantAddr, warehouseAddr);
      ScAddr whAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_warehouse, whArc);
      result << whArc << whAttrArc << LogisticsKeynodes::nrel_warehouse;

      // ID
      ScAddr idLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(idLink, std::to_string(warehouse.id));
      ScAddr idArc = m_context.GenerateConnector(ScType::ConstCommonArc, warehouseAddr, idLink);
      ScAddr idAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_id, idArc);
      result << idLink << idArc << idAttrArc << LogisticsKeynodes::nrel_id;

      // X
      ScAddr xLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(xLink, std::to_string(warehouse.position.x));
      ScAddr xArc = m_context.GenerateConnector(ScType::ConstCommonArc, warehouseAddr, xLink);
      ScAddr xAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_x, xArc);
      result << xLink << xArc << xAttrArc << LogisticsKeynodes::nrel_x;

      // Y
      ScAddr yLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(yLink, std::to_string(warehouse.position.y));
      ScAddr yArc = m_context.GenerateConnector(ScType::ConstCommonArc, warehouseAddr, yLink);
      ScAddr yAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_y, yArc);
      result << yLink << yArc << yAttrArc << LogisticsKeynodes::nrel_y;

      // Shops
      std::string shopsStr;
      for (size_t i = 0; i < warehouse.shopIds.size(); i++)
      {
        if (i > 0) shopsStr += ",";
        shopsStr += std::to_string(warehouse.shopIds[i]);
      }

      ScAddr shopsLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(shopsLink, shopsStr);
      ScAddr shopsArc = m_context.GenerateConnector(ScType::ConstCommonArc, warehouseAddr, shopsLink);
      ScAddr shopsAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_serves_shops, shopsArc);
      result << shopsLink << shopsArc << shopsAttrArc << LogisticsKeynodes::nrel_serves_shops;
    }

    action.SetResult(result);
    m_logger.Info("Агент кластеризации успешно завершён");
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
