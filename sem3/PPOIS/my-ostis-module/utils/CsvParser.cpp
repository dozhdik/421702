/*
 * Парсер CSV файлов для загрузки данных о магазинах
 * Реализация методов
 */

#include "CsvParser.hpp"

namespace logistics
{

// Парсит CSV файл и возвращает вектор данных о магазинах
bool CsvParser::ParseShopsFile(
    std::string const & filePath,
    std::vector<ShopData> & shops,
    std::string & errorMessage)
{
  shops.clear();

  std::ifstream file(filePath);
  if (!file.is_open())
  {
    errorMessage = "Не удалось открыть файл " + filePath;
    return false;
  }

  std::string line;
  int lineNumber = 0;

  // Читаем файл построчно
  while (std::getline(file, line))
  {
    lineNumber++;

    // Пропускаем пустые строки
    if (line.empty())
      continue;

    // Пропускаем заголовок (первая строка)
    if (lineNumber == 1 && line.find("shop_id") != std::string::npos)
      continue;

    // Парсим строку
    ShopData shop;
    if (!ParseLine(line, shop, errorMessage))
    {
      errorMessage = "Ошибка в строке " + std::to_string(lineNumber) + " " + errorMessage;
      return false;
    }

    shops.push_back(shop);
  }

  file.close();

  if (shops.empty())
  {
    errorMessage = "Файл не содержит данных о магазинах";
    return false;
  }

  return true;
}

// Парсит одну строку CSV
bool CsvParser::ParseLine(std::string const & line, ShopData & shop, std::string & errorMessage)
{
  std::vector<std::string> tokens;
  std::stringstream ss(line);
  std::string token;

  // Разбиваем строку по разделителю ';'
  while (std::getline(ss, token, ';'))
  {
    tokens.push_back(token);
  }

  // Проверяем количество полей
  if (tokens.size() < 5)
  {
    errorMessage = "Недостаточно полей, ожидается 5";
    return false;
  }

  try
  {
    shop.id = std::stoi(tokens[0]);
    shop.name = tokens[1];
    shop.x = std::stod(tokens[2]);
    shop.y = std::stod(tokens[3]);
    shop.volume = std::stod(tokens[4]);
  }
  catch (std::exception const &)
  {
    errorMessage = "Ошибка преобразования данных";
    return false;
  }

  // Проверяем корректность данных
  if (shop.volume < 0)
  {
    errorMessage = "Объём поставок не может быть отрицательным";
    return false;
  }

  return true;
}

}  // namespace logistics
