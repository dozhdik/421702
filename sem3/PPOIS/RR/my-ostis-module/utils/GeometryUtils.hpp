/*
 * Утилиты для геометрических расчётов
 * Расчёт расстояний, центроидов и кластеризация
 */

#pragma once

#include <vector>
#include <cmath>
#include <limits>
#include <algorithm>

#include "CsvParser.hpp"

namespace logistics
{

// Структура для хранения координат точки
struct Point
{
  double x;
  double y;

  Point() : x(0), y(0) {}
  Point(double x_, double y_) : x(x_), y(y_) {}
};

// Структура для хранения данных о складе
struct WarehouseData
{
  int id;                      // Идентификатор склада
  Point position;              // Координаты склада
  std::vector<int> shopIds;    // Идентификаторы обслуживаемых магазинов
};

// Структура для хранения варианта размещения
struct PlacementVariant
{
  int warehouseCount;                    // Количество складов
  std::vector<WarehouseData> warehouses; // Данные о складах
  double monthlyCost;                    // Ежемесячные затраты
  double economyPercent;                 // Процент экономии относительно варианта с 1 складом
};

// Класс с утилитами для геометрических расчётов
class GeometryUtils
{
public:
  // Константа: стоимость транспортировки (руб/км*т)
  static constexpr double TRANSPORT_COST_PER_KM_TON = 12.0;

  // Вычисляет евклидово расстояние между двумя точками
  static double CalculateDistance(Point const & p1, Point const & p2);

  // Вычисляет взвешенный центроид для набора магазинов
  // Веса = объёмы поставок
  static Point CalculateWeightedCentroid(std::vector<ShopData> const & shops);

  // Вычисляет транспортные затраты для одного склада
  // Формула: сумма(расстояние * объём * стоимость_км_т * 2)
  // Множитель 2 учитывает доставку туда и обратно
  static double CalculateTransportCost(
      Point const & warehousePos,
      std::vector<ShopData> const & shops);

  // Вычисляет транспортные затраты для нескольких складов
  // Каждый магазин обслуживается ближайшим складом
  static double CalculateTransportCostMultiWarehouse(
      std::vector<WarehouseData> const & warehouses,
      std::vector<ShopData> const & shops);

  // K-means кластеризация магазинов
  // Возвращает вектор центроидов кластеров
  static std::vector<WarehouseData> KMeansClustering(
      std::vector<ShopData> const & shops,
      int k,
      int maxIterations = 100);

  // Вычисляет общий грузооборот
  static double CalculateTotalVolume(std::vector<ShopData> const & shops);
};

}  // namespace logistics
