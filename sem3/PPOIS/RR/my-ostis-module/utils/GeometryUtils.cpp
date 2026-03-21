/*
 * Утилиты для геометрических расчётов
 * Реализация методов
 */

#include "GeometryUtils.hpp"

namespace logistics
{

// Вычисляет евклидово расстояние между двумя точками
double GeometryUtils::CalculateDistance(Point const & p1, Point const & p2)
{
  double dx = p2.x - p1.x;
  double dy = p2.y - p1.y;
  return std::sqrt(dx * dx + dy * dy);
}

// Вычисляет взвешенный центроид для набора магазинов
Point GeometryUtils::CalculateWeightedCentroid(std::vector<ShopData> const & shops)
{
  double totalWeight = 0;
  double weightedX = 0;
  double weightedY = 0;

  for (auto const & shop : shops)
  {
    weightedX += shop.x * shop.volume;
    weightedY += shop.y * shop.volume;
    totalWeight += shop.volume;
  }

  if (totalWeight == 0)
    return Point(0, 0);

  return Point(weightedX / totalWeight, weightedY / totalWeight);
}

// Вычисляет транспортные затраты для одного склада
double GeometryUtils::CalculateTransportCost(
    Point const & warehousePos,
    std::vector<ShopData> const & shops)
{
  double totalCost = 0;

  for (auto const & shop : shops)
  {
    double distance = CalculateDistance(warehousePos, Point(shop.x, shop.y));
    totalCost += distance * shop.volume * TRANSPORT_COST_PER_KM_TON * 2;
  }

  return totalCost;
}

// Вычисляет транспортные затраты для нескольких складов
double GeometryUtils::CalculateTransportCostMultiWarehouse(
    std::vector<WarehouseData> const & warehouses,
    std::vector<ShopData> const & shops)
{
  double totalCost = 0;

  for (auto const & shop : shops)
  {
    // Находим ближайший склад
    double minDistance = std::numeric_limits<double>::max();
    for (auto const & warehouse : warehouses)
    {
      double distance = CalculateDistance(warehouse.position, Point(shop.x, shop.y));
      if (distance < minDistance)
      {
        minDistance = distance;
      }
    }

    totalCost += minDistance * shop.volume * TRANSPORT_COST_PER_KM_TON * 2;
  }

  return totalCost;
}

// K-means кластеризация магазинов
std::vector<WarehouseData> GeometryUtils::KMeansClustering(
    std::vector<ShopData> const & shops,
    int k,
    int maxIterations)
{
  if (shops.empty() || k <= 0)
    return {};

  // Инициализируем центроиды первыми k магазинами
  std::vector<Point> centroids;
  for (int i = 0; i < k && i < static_cast<int>(shops.size()); i++)
  {
    centroids.push_back(Point(shops[i].x, shops[i].y));
  }

  // Вектор для хранения принадлежности магазинов к кластерам
  std::vector<int> assignments(shops.size(), 0);

  for (int iter = 0; iter < maxIterations; iter++)
  {
    bool changed = false;

    // Шаг 1: Назначаем каждый магазин ближайшему центроиду
    for (size_t i = 0; i < shops.size(); i++)
    {
      Point shopPos(shops[i].x, shops[i].y);
      double minDist = std::numeric_limits<double>::max();
      int bestCluster = 0;

      for (int c = 0; c < k; c++)
      {
        double dist = CalculateDistance(shopPos, centroids[c]);
        if (dist < minDist)
        {
          minDist = dist;
          bestCluster = c;
        }
      }

      if (assignments[i] != bestCluster)
      {
        assignments[i] = bestCluster;
        changed = true;
      }
    }

    // Шаг 2: Пересчитываем центроиды как взвешенные средние
    for (int c = 0; c < k; c++)
    {
      std::vector<ShopData> clusterShops;
      for (size_t i = 0; i < shops.size(); i++)
      {
        if (assignments[i] == c)
        {
          clusterShops.push_back(shops[i]);
        }
      }

      if (!clusterShops.empty())
      {
        centroids[c] = CalculateWeightedCentroid(clusterShops);
      }
    }

    // Если ничего не изменилось после первой итерации, выходим
    if (!changed && iter > 0)
      break;
  }

  // Формируем результат
  std::vector<WarehouseData> result;
  for (int c = 0; c < k; c++)
  {
    WarehouseData warehouse;
    warehouse.id = c + 1;
    warehouse.position = centroids[c];

    for (size_t i = 0; i < shops.size(); i++)
    {
      if (assignments[i] == c)
      {
        warehouse.shopIds.push_back(shops[i].id);
      }
    }

    result.push_back(warehouse);
  }

  return result;
}

// Вычисляет общий грузооборот
double GeometryUtils::CalculateTotalVolume(std::vector<ShopData> const & shops)
{
  double total = 0;
  for (auto const & shop : shops)
  {
    total += shop.volume;
  }
  return total;
}

}  // namespace logistics
