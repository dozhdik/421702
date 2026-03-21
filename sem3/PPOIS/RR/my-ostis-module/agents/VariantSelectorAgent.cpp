/*
 * Агент выбора варианта размещения
 */

#include "VariantSelectorAgent.hpp"

#include <sc-memory/sc_memory.hpp>
#include <sc-memory/sc_stream.hpp>
#include <iomanip>
#include <sstream>

#include "../keynodes/LogisticsKeynodes.hpp"

VariantSelectorAgent::VariantSelectorAgent()
{
  m_logger = utils::ScLogger(
      utils::ScLogger::ScLogType::File,
      "logs/VariantSelectorAgent.log",
      utils::ScLogLevel::Debug);
}

ScAddr VariantSelectorAgent::GetActionClass() const
{
  return LogisticsKeynodes::action_select_best_variant;
}

ScResult VariantSelectorAgent::DoProgram(ScAction & action)
{
  m_logger.Info("Агент VariantSelectorAgent запущен");

  try
  {
    auto const & [v1, v2, v3] = action.GetArguments<3>();

    if (!v1.IsValid() || !v2.IsValid() || !v3.IsValid())
    {
      m_logger.Error("Не все варианты размещения найдены");
      return action.FinishWithError();
    }

    auto getCost = [this](ScAddr const & variantAddr) -> double {
      ScIterator5Ptr it = m_context.CreateIterator5(
          variantAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_transport_cost);

      if (it->Next())
      {
        ScStreamPtr stream = m_context.GetLinkContent(it->Get(2));
        if (stream && stream->IsValid())
        {
          std::string s;
          if (ScStreamConverter::StreamToString(stream, s))
          {
            try { return std::stod(s); } catch (...) { }
          }
        }
      }
      return 0.0;
    };

    double cost1 = getCost(v1);
    double cost2 = getCost(v2);
    double cost3 = getCost(v3);

    m_logger.Info("Costs: " + std::to_string((int)cost1) + ", " + std::to_string((int)cost2) + ", " + std::to_string((int)cost3));

    double econ2 = cost1 > 0.0 ? 100.0 * (1.0 - cost2 / cost1) : 0.0;
    double econ3 = cost1 > 0.0 ? 100.0 * (1.0 - cost3 / cost1) : 0.0;

    // Выбираем вариант с минимальной стоимостью; при равенстве выбираем первый по порядку
    ScAddr best = v1;
    double bestCost = cost1;
    if (cost2 < bestCost) { best = v2; bestCost = cost2; }
    if (cost3 < bestCost) { best = v3; bestCost = cost3; }

    auto addEconomy = [this](ScAddr const & variantAddr, double economy) {
      std::ostringstream oss;
      oss << std::fixed << std::setprecision(2) << economy;

      ScAddr link = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(link, oss.str());

      ScAddr arc = m_context.GenerateConnector(ScType::ConstCommonArc, variantAddr, link);
      m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::nrel_economy, arc);
    };

    addEconomy(v1, 0.0);
    addEconomy(v2, econ2);
    addEconomy(v3, econ3);

    ScStructure result = m_context.GenerateStructure();
    ScAddr resNode = m_context.GenerateNode(ScType::ConstNode);
    result << resNode;

    ScAddr bestArc = m_context.GenerateConnector(ScType::ConstCommonArc, resNode, best);
    ScAddr attr = m_context.GenerateConnector(ScType::ConstPermPosArc, LogisticsKeynodes::nrel_recommendation, bestArc);
    result << best << bestArc << attr << LogisticsKeynodes::nrel_recommendation;

    action.SetResult(result);
    m_logger.Info("VariantSelectorAgent успешно завершён");
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
