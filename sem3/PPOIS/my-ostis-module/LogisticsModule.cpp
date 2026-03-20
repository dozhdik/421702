/*
 * Модуль логистической оптимизации
 * Вариант 16 ППОИС: Размещение логистических складов
 * Архитектура C: семантически-ориентированный подход
 *
 * Агенты модуля:
 * 1. StorageOptimizationAgent - оркестратор
 * 2. FileParseAgent - парсинг CSV
 * 3. DataValidationAgent - валидация данных
 * 4. ClusteringAgent - кластеризация
 * 5. CostCalculationAgent - расчёт затрат
 * 6. VariantSelectorAgent - выбор варианта
 */

#include "LogisticsModule.hpp"

#include "agents/StorageOptimizationAgent.hpp"
#include "agents/FileLoaderAgent.hpp"
#include "agents/DataVerifierAgent.hpp"
#include "agents/ShopClusteringAgent.hpp"
#include "agents/CostEstimatorAgent.hpp"
#include "agents/VariantSelectorAgent.hpp"

SC_MODULE_REGISTER(LogisticsModule)
    ->Agent<StorageOptimizationAgent>()
    ->Agent<FileLoaderAgent>()
    ->Agent<DataVerifierAgent>()
    ->Agent<ShopClusteringAgent>()
    ->Agent<CostEstimatorAgent>()
    ->Agent<VariantSelectorAgent>();
