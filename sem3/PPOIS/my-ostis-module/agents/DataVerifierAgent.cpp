/*
 * Агент проверки входных данных
 */

#include "DataVerifierAgent.hpp"

#include <sc-memory/sc_memory.hpp>
#include <sc-memory/sc_stream.hpp>

#include "../keynodes/LogisticsKeynodes.hpp"

DataVerifierAgent::DataVerifierAgent()
{
  m_logger = utils::ScLogger(
      utils::ScLogger::ScLogType::File,
      "logs/DataVerifierAgent.log",
      utils::ScLogLevel::Debug);
}

ScAddr DataVerifierAgent::GetActionClass() const
{
  return LogisticsKeynodes::action_validate_network;
}

ScResult DataVerifierAgent::DoProgram(ScAction & action)
{
  m_logger.Info("DataVerifierAgent started");

  try
  {
    auto const & [networkAddr] = action.GetArguments<1>();

    if (!networkAddr.IsValid())
    {
      m_logger.Error("Network not found");
      return action.FinishWithError();
    }

    int shopCount = 0;
    bool hasInvalidData = false;

    ScIterator3Ptr shopIter = m_context.CreateIterator3(
        networkAddr, ScType::ConstPermPosArc, ScType::ConstNode);

    while (shopIter->Next())
    {
      ScAddr shopAddr = shopIter->Get(2);

      if (!m_context.CheckConnector(LogisticsKeynodes::concept_shop, shopAddr, ScType::ConstPermPosArc))
        continue;

      shopCount++;

      ScIterator5Ptr idIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_id);
      bool hasId = idIter->Next();

      ScIterator5Ptr xIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_x);
      bool hasX = xIter->Next();

      ScIterator5Ptr yIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_y);
      bool hasY = yIter->Next();

      ScIterator5Ptr volIter = m_context.CreateIterator5(
          shopAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_volume);
      bool hasVolume = volIter->Next();

      if (!hasId || !hasX || !hasY || !hasVolume)
      {
        hasInvalidData = true;
        m_logger.Warning("Shop with incomplete data");
      }
    }

    m_logger.Info("Checked shops: " + std::to_string(shopCount));

    if (shopCount < 3)
    {
      m_logger.Error("Not enough shops, minimum 3");
      return action.FinishWithError();
    }

    if (hasInvalidData)
      m_logger.Warning("Found shops with incomplete data");

    ScStructure result = m_context.GenerateStructure();

    ScAddr validationResultAddr = m_context.GenerateNode(ScType::ConstNode);
    result << validationResultAddr;

    ScAddr countLink = m_context.GenerateLink(ScType::ConstNodeLink);
    m_context.SetLinkContent(countLink, std::to_string(shopCount));
    ScAddr countArc = m_context.GenerateConnector(ScType::ConstCommonArc, validationResultAddr, countLink);
    ScAddr countAttrArc = m_context.GenerateConnector(
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_shop_count, countArc);
    result << countLink << countArc << countAttrArc << LogisticsKeynodes::nrel_shop_count;

    ScAddr validLink = m_context.GenerateLink(ScType::ConstNodeLink);
    m_context.SetLinkContent(validLink, hasInvalidData ? "false" : "true");
    ScAddr validArc = m_context.GenerateConnector(ScType::ConstCommonArc, validationResultAddr, validLink);
    ScAddr validAttrArc = m_context.GenerateConnector(
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_is_valid, validArc);
    result << validLink << validArc << validAttrArc << LogisticsKeynodes::nrel_is_valid;

    action.SetResult(result);
    m_logger.Info("DataVerifierAgent finished successfully");
    return action.FinishSuccessfully();
  }
  catch (utils::ScException const & e)
  {
    m_logger.Error(std::string("SC exception: ") + e.Message());
    return action.FinishWithError();
  }
  catch (std::exception const & e)
  {
    m_logger.Error(std::string("Exception: ") + e.what());
    return action.FinishWithError();
  }
  catch (...)
  {
    m_logger.Error("Unknown exception");
    return action.FinishWithError();
  }
}
