/*
 * Агент загрузки и парсинга входного файла
 */

#include "FileLoaderAgent.hpp"

#include <sc-memory/sc_memory.hpp>
#include <sc-memory/sc_stream.hpp>

#include "../keynodes/LogisticsKeynodes.hpp"
#include "../utils/CsvParser.hpp"

using namespace logistics;

FileLoaderAgent::FileLoaderAgent()
{
  m_logger = utils::ScLogger(
      utils::ScLogger::ScLogType::File,
      "logs/FileLoaderAgent.log",
      utils::ScLogLevel::Debug);
}

ScAddr FileLoaderAgent::GetActionClass() const
{
  return LogisticsKeynodes::action_load_file;
}

ScResult FileLoaderAgent::DoProgram(ScAction & action)
{
  m_logger.Info("FileLoaderAgent started");

  try
  {
    auto const & [inputEntityAddr] = action.GetArguments<1>();

    if (!inputEntityAddr.IsValid())
    {
      m_logger.Error("Action argument not found");
      return action.FinishWithError();
    }

    std::string filePath;
    if (!GetFilePathFromEntity(inputEntityAddr, filePath))
    {
      m_logger.Error("Failed to obtain file path");
      return action.FinishWithError();
    }

    m_logger.Info("Parsing file: " + filePath);

    std::vector<ShopData> shops;
    std::string parseError;

    if (!CsvParser::ParseShopsFile(filePath, shops, parseError))
    {
      m_logger.Error("CSV parse error: " + parseError);
      return action.FinishWithError();
    }

    m_logger.Info("Loaded shops: " + std::to_string(shops.size()));

    ClearPreviousResult(inputEntityAddr);

    ScStructure result = m_context.GenerateStructure();

    ScAddr networkAddr = m_context.GenerateNode(ScType::ConstNode);
    result << networkAddr;

    ScAddr classArc = m_context.GenerateConnector(
        ScType::ConstPermPosArc, LogisticsKeynodes::concept_network, networkAddr);
    result << classArc << LogisticsKeynodes::concept_network;

    for (auto const & shop : shops)
    {
      ScAddr shopAddr = m_context.GenerateNode(ScType::ConstNode);
      result << shopAddr;

      ScAddr shopClassArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::concept_shop, shopAddr);
      result << shopClassArc << LogisticsKeynodes::concept_shop;

      ScAddr memberArc = m_context.GenerateConnector(ScType::ConstPermPosArc, networkAddr, shopAddr);
      result << memberArc;

      ScAddr idLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(idLink, std::to_string(shop.id));
      ScAddr idArc = m_context.GenerateConnector(ScType::ConstCommonArc, shopAddr, idLink);
      ScAddr idAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_id, idArc);
      result << idLink << idArc << idAttrArc << LogisticsKeynodes::nrel_id;

      ScAddr xLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(xLink, std::to_string(shop.x));
      ScAddr xArc = m_context.GenerateConnector(ScType::ConstCommonArc, shopAddr, xLink);
      ScAddr xAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_x, xArc);
      result << xLink << xArc << xAttrArc << LogisticsKeynodes::nrel_x;

      ScAddr yLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(yLink, std::to_string(shop.y));
      ScAddr yArc = m_context.GenerateConnector(ScType::ConstCommonArc, shopAddr, yLink);
      ScAddr yAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_y, yArc);
      result << yLink << yArc << yAttrArc << LogisticsKeynodes::nrel_y;

      ScAddr volumeLink = m_context.GenerateLink(ScType::ConstNodeLink);
      m_context.SetLinkContent(volumeLink, std::to_string(shop.volume));
      ScAddr volumeArc = m_context.GenerateConnector(ScType::ConstCommonArc, shopAddr, volumeLink);
      ScAddr volumeAttrArc = m_context.GenerateConnector(
          ScType::ConstPermPosArc, LogisticsKeynodes::nrel_volume, volumeArc);
      result << volumeLink << volumeArc << volumeAttrArc << LogisticsKeynodes::nrel_volume;
    }

    ScAddr resultArc = m_context.GenerateConnector(ScType::ConstCommonArc, inputEntityAddr, networkAddr);
    ScAddr resultAttrArc = m_context.GenerateConnector(
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_loaded_data, resultArc);
    result << resultArc << resultAttrArc << LogisticsKeynodes::nrel_loaded_data;

    action.SetResult(result);
    m_logger.Info("FileLoaderAgent finished successfully");
    return action.FinishSuccessfully();
  }
  catch (utils::ScException const & e)
  {
    m_logger.Error("SC exception: " + std::string(e.Message()));
    return action.FinishWithError();
  }
  catch (std::exception const & e)
  {
    m_logger.Error("Exception: " + std::string(e.what()));
    return action.FinishWithError();
  }
  catch (...)
  {
    m_logger.Error("Unknown exception");
    return action.FinishWithError();
  }
}

bool FileLoaderAgent::GetFilePathFromEntity(ScAddr const & entityAddr, std::string & filePath)
{
  try
  {
    ScIterator5Ptr iterator = m_context.CreateIterator5(
        entityAddr, ScType::ConstCommonArc, ScType::ConstNodeLink,
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_main_idtf);

    if (!iterator->Next())
      return false;

    ScAddr linkAddr = iterator->Get(2);
    ScStreamPtr stream = m_context.GetLinkContent(linkAddr);

    if (!stream || !stream->IsValid())
      return false;

    std::string content;
    if (!ScStreamConverter::StreamToString(stream, content))
      return false;

    filePath = content;
    return true;
  }
  catch (...)
  {
    return false;
  }
}

void FileLoaderAgent::ClearPreviousResult(ScAddr const & inputAddr)
{
  try
  {
    ScIterator5Ptr iterator = m_context.CreateIterator5(
        inputAddr, ScType::ConstCommonArc, ScType::ConstNode,
        ScType::ConstPermPosArc, LogisticsKeynodes::nrel_loaded_data);

    while (iterator->Next())
    {
      m_context.EraseElement(iterator->Get(3));
      m_context.EraseElement(iterator->Get(1));
    }
  }
  catch (...)
  {
    m_logger.Warning("Error clearing previous result");
  }
}
