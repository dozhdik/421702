/*
 * Тесты для CsvParser
 * Проверка парсинга CSV файлов с данными о магазинах
 */

#include <gtest/gtest.h>
#include <filesystem>
#include "utils/CsvParser.hpp"

using namespace logistics;

static std::string GetTestDataPath(std::string const & filename)
{
  std::filesystem::path thisFile(__FILE__);
  return (thisFile.parent_path() / "test_data" / filename).string();
}

// Тест 1: Парсинг различных CSV файлов
TEST(CsvParserTest, ParseFiles)
{
  struct TestCase {
    std::string file;
    int expectedCount;
    bool checkFirst;
    bool checkLast;
  };

  TestCase cases[] = {
    {"shops_3.csv", 3, false, false},
    {"shops_5.csv", 5, true, true},
    {"shops_15.csv", 15, false, false}
  };

  for (auto const & tc : cases)
  {
    std::vector<ShopData> shops;
    std::string error;
    bool result = CsvParser::ParseShopsFile(GetTestDataPath(tc.file), shops, error);
    
    ASSERT_TRUE(result) << "Ошибка парсинга " << tc.file << ": " << error;
    EXPECT_EQ(shops.size(), static_cast<size_t>(tc.expectedCount));
    
    if (tc.checkFirst && shops.size() > 0)
    {
      EXPECT_EQ(shops[0].id, 1);
      EXPECT_NEAR(shops[0].x, 10.0, 0.01);
      EXPECT_NEAR(shops[0].y, 15.0, 0.01);
      EXPECT_NEAR(shops[0].volume, 200.0, 0.01);
    }
    
    if (tc.checkLast && shops.size() >= 5)
    {
      EXPECT_EQ(shops[4].id, 5);
      EXPECT_NEAR(shops[4].x, 55.0, 0.01);
      EXPECT_NEAR(shops[4].y, 35.0, 0.01);
      EXPECT_NEAR(shops[4].volume, 320.0, 0.01);
    }
    
    for (size_t i = 0; i < shops.size(); i++)
    {
      EXPECT_GT(shops[i].x, 0);
      EXPECT_GT(shops[i].y, 0);
      EXPECT_GT(shops[i].volume, 0);
    }
  }
}

// Тест 2: Ошибка - несуществующий файл
TEST(CsvParserTest, Error_FileNotFound)
{
  std::vector<ShopData> shops;
  std::string error;
  bool result = CsvParser::ParseShopsFile("/tmp/nonexistent_12345.csv", shops, error);
  
  EXPECT_FALSE(result);
  EXPECT_FALSE(error.empty());
}
