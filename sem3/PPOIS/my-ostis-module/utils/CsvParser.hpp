/*
 * Парсер CSV файлов для загрузки данных о магазинах
 * Формат: shop_id;name;x;y;volume
 */

#pragma once

#include <string>
#include <vector>
#include <fstream>
#include <sstream>

namespace logistics
{

// Структура для хранения данных о магазине
struct ShopData
{
  int id;              // Идентификатор магазина
  std::string name;    // Название магазина
  double x;            // Координата X
  double y;            // Координата Y
  double volume;       // Объём поставок (тонн/месяц)
};

// Класс для парсинга CSV файлов с данными магазинов
class CsvParser
{
public:
  // Парсит CSV файл и возвращает вектор данных о магазинах
  // Возвращает true при успешном парсинге, false при ошибке
  static bool ParseShopsFile(
      std::string const & filePath,
      std::vector<ShopData> & shops,
      std::string & errorMessage);

private:
  // Парсит одну строку CSV
  static bool ParseLine(
      std::string const & line,
      ShopData & shop,
      std::string & errorMessage);
};

}  // namespace logistics
