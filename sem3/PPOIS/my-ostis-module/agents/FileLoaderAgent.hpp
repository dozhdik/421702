/*
 * Агент загрузки и парсинга входного файла (переименованный FileParseAgent)
 */

#pragma once

#include <sc-memory/sc_agent.hpp>

class FileLoaderAgent : public ScActionInitiatedAgent
{
public:
  FileLoaderAgent();
  ScAddr GetActionClass() const override;
  ScResult DoProgram(ScAction & action) override;

private:
  bool GetFilePathFromEntity(ScAddr const & entityAddr, std::string & filePath);
  void ClearPreviousResult(ScAddr const & inputAddr);
};
