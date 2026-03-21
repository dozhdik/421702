/*
 * Оркестратор оптимизации размещения хранилищ (переименованный)
 * Вызывает атомарные агенты через SC-память
 */

#include "StorageOptimizationAgent.hpp"

#include <sc-memory/sc_memory.hpp>
#include <sc-memory/sc_stream.hpp>

#include "../keynodes/LogisticsKeynodes.hpp"

static const uint32_t ORCHESTRATOR_TIMEOUT_MS = 45000;

StorageOptimizationAgent::StorageOptimizationAgent()
{
  m_logger = utils::ScLogger(
      utils::ScLogger::ScLogType::File,
      "logs/StorageOrchestrator.log",
      utils::ScLogLevel::Debug);
}

ScAddr StorageOptimizationAgent::GetActionClass() const
{
  return LogisticsKeynodes::action_optimize_warehouses;
}

ScResult StorageOptimizationAgent::DoProgram(ScAction & action)
{
  m_logger.Info("Оркестратор размещения хранилищ запущен");

  try
  {
    auto const & [inputEntityAddr] = action.GetArguments<1>();

    if (!inputEntityAddr.IsValid())
    {
      m_logger.Error("Аргумент действия не найден");
      return action.FinishWithError();
    }

    m_logger.Info("Шаг 1: парсинг входного файла");
    if (!CallFileParseAgent(inputEntityAddr))
    {
      m_logger.Error("Ошибка парсинга файла");
      return action.FinishWithError();
    }

    ScAddr networkAddr = GetParsedNetwork(inputEntityAddr);
    if (!networkAddr.IsValid())
    {
      m_logger.Error("Торговая сеть не найдена");
      return action.FinishWithError();
    }

    m_logger.Info("Шаг 2: валидация данных");
    if (!CallDataValidationAgent(networkAddr))
    {
      m_logger.Error("Ошибка валидации данных");
      return action.FinishWithError();
    }

    m_logger.Info("Запуск расчёта вариантов размещения (K=1,2,3)");
    std::vector<int> ks = {1, 2, 3};
    std::vector<ScAddr> variants;
    variants.reserve(ks.size());

    for (int k : ks)
    {
      m_logger.Info("Кластеризация: K=" + std::to_string(k));
      ScAddr variantAddr = CallClusteringAgent(networkAddr, k);
      if (!variantAddr.IsValid())
      {
        m_logger.Error("Кластеризация провалена для K=" + std::to_string(k));
        return action.FinishWithError();
      }

      m_logger.Info("Расчёт затрат для K=" + std::to_string(k));
      if (!CallCostCalculationAgent(variantAddr, networkAddr))
      {
        m_logger.Error("Ошибка расчёта затрат для K=" + std::to_string(k));
        return action.FinishWithError();
      }

      variants.push_back(variantAddr);
    }

    m_logger.Info("Сравнение вариантов");
    ScStructure comparisonResult = m_context.GenerateStructure();
    if (variants.size() >= 3)
      comparisonResult = CallVariantComparisonAgent(variants[0], variants[1], variants[2]);
    if (comparisonResult.IsEmpty())
    {
      m_logger.Error("Ошибка сравнения вариантов");
      return action.FinishWithError();
    }

    action.SetResult(comparisonResult);
    m_logger.Info("Оркестратор успешно завершён");
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

// --- Вспомогательные методы (копия логики оригинала, адаптирована) ---
bool StorageOptimizationAgent::CallFileParseAgent(ScAddr const & inputEntityAddr)
{
  ScAddr actionAddr = m_context.GenerateNode(ScType::ConstNode);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action_load_file, actionAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action, actionAddr);

  ScAddr argArc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, inputEntityAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_1, argArc);

  ScAction agentAction = m_context.ConvertToAction(actionAddr);
  if (!agentAction.InitiateAndWait(ORCHESTRATOR_TIMEOUT_MS))
    return false;

  return agentAction.IsFinishedSuccessfully();
}

ScAddr StorageOptimizationAgent::GetParsedNetwork(ScAddr const & inputEntityAddr)
{
  ScIterator5Ptr iter = m_context.CreateIterator5(
      inputEntityAddr,
      ScType::ConstCommonArc,
      ScType::ConstNode,
      ScType::ConstPermPosArc,
      LogisticsKeynodes::nrel_loaded_data);

  if (iter->Next())
    return iter->Get(2);

  return ScAddr();
}

bool StorageOptimizationAgent::CallDataValidationAgent(ScAddr const & networkAddr)
{
  ScAddr actionAddr = m_context.GenerateNode(ScType::ConstNode);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action_validate_network, actionAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action, actionAddr);

  ScAddr argArc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, networkAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_1, argArc);

  ScAction agentAction = m_context.ConvertToAction(actionAddr);
  if (!agentAction.InitiateAndWait(ORCHESTRATOR_TIMEOUT_MS))
    return false;

  if (!agentAction.IsFinishedSuccessfully())
    return false;

  ScStructure const & result = agentAction.GetResult();
  ScIterator3Ptr iter = m_context.CreateIterator3(result, ScType::ConstPermPosArc, ScType::ConstNode);
  while (iter->Next())
  {
    ScAddr nodeAddr = iter->Get(2);
    ScIterator5Ptr validIter = m_context.CreateIterator5(
        nodeAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_is_valid);
    if (validIter->Next())
    {
      ScStreamPtr stream = m_context.GetLinkContent(validIter->Get(2));
      if (stream && stream->IsValid())
      {
        std::string validStr;
        if (ScStreamConverter::StreamToString(stream, validStr))
        {
          if (validStr == "false")
          {
            m_logger.Error("Данные невалидны (nrel_is_valid=false)");
            return false;
          }
        }
      }
    }
  }

  return true;
}

ScAddr StorageOptimizationAgent::CallClusteringAgent(ScAddr const & networkAddr, int k)
{
  ScAddr kLink = m_context.GenerateLink(ScType::ConstNodeLink);
  m_context.SetLinkContent(kLink, std::to_string(k));

  ScAddr actionAddr = m_context.GenerateNode(ScType::ConstNode);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action_cluster_shops, actionAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action, actionAddr);

  ScAddr arg1Arc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, networkAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_1, arg1Arc);

  ScAddr arg2Arc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, kLink);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_2, arg2Arc);

  ScAction agentAction = m_context.ConvertToAction(actionAddr);
  if (!agentAction.InitiateAndWait(ORCHESTRATOR_TIMEOUT_MS))
    return ScAddr();

  if (!agentAction.IsFinishedSuccessfully())
    return ScAddr();

  ScStructure const & result = agentAction.GetResult();
  ScIterator3Ptr variantIter = m_context.CreateIterator3(
      result, ScType::ConstPermPosArc, ScType::ConstNode);

  while (variantIter->Next())
  {
    ScAddr nodeAddr = variantIter->Get(2);
    if (m_context.CheckConnector(LogisticsKeynodes::concept_placement_variant, nodeAddr, ScType::ConstPermPosArc))
      return nodeAddr;
  }

  return ScAddr();
}

bool StorageOptimizationAgent::CallCostCalculationAgent(ScAddr const & variantAddr, ScAddr const & networkAddr)
{
  ScAddr actionAddr = m_context.GenerateNode(ScType::ConstNode);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action_calculate_transport_cost, actionAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action, actionAddr);

  ScAddr arg1Arc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, variantAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_1, arg1Arc);

  ScAddr arg2Arc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, networkAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_2, arg2Arc);

  ScAction agentAction = m_context.ConvertToAction(actionAddr);
  if (!agentAction.InitiateAndWait(ORCHESTRATOR_TIMEOUT_MS))
    return false;

  return agentAction.IsFinishedSuccessfully();
}

ScStructure StorageOptimizationAgent::CallVariantComparisonAgent(
    ScAddr const & variant1Addr,
    ScAddr const & variant2Addr,
    ScAddr const & variant3Addr)
{
  ScAddr actionAddr = m_context.GenerateNode(ScType::ConstNode);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action_select_best_variant, actionAddr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::action, actionAddr);

  ScAddr arg1Arc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, variant1Addr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_1, arg1Arc);

  ScAddr arg2Arc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, variant2Addr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_2, arg2Arc);

  ScAddr arg3Arc = m_context.GenerateConnector(ScType::ConstPermPosArc, actionAddr, variant3Addr);
  m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::rrel_3, arg3Arc);

  ScAction agentAction = m_context.ConvertToAction(actionAddr);
  if (!agentAction.InitiateAndWait(ORCHESTRATOR_TIMEOUT_MS))
    return m_context.GenerateStructure();

  if (!agentAction.IsFinishedSuccessfully())
    return m_context.GenerateStructure();

  return agentAction.GetResult();
}
