/*
 * Ключевые узлы для модуля логистики
 */

#pragma once

#include <sc-memory/sc_addr.hpp>
#include <sc-memory/sc_keynodes.hpp>

class LogisticsKeynodes : public ScKeynodes
{
public:
  // Классы действий
  static inline ScKeynode const action_optimize_warehouses{
      "action_optimize_warehouses", ScType::ConstNodeClass};
  static inline ScKeynode const action_load_file{
      "action_load_file", ScType::ConstNodeClass};
  static inline ScKeynode const action_validate_network{
      "action_validate_network", ScType::ConstNodeClass};
  static inline ScKeynode const action_cluster_shops{
      "action_cluster_shops", ScType::ConstNodeClass};
  static inline ScKeynode const action_calculate_transport_cost{
      "action_calculate_transport_cost", ScType::ConstNodeClass};
  static inline ScKeynode const action_select_best_variant{
      "action_select_best_variant", ScType::ConstNodeClass};

  // Классы понятий
  static inline ScKeynode const concept_warehouse{
      "concept_warehouse", ScType::ConstNodeClass};
  static inline ScKeynode const concept_placement_variant{
      "concept_placement_variant", ScType::ConstNodeClass};
  static inline ScKeynode const concept_network{
      "concept_network", ScType::ConstNodeClass};
  static inline ScKeynode const concept_shop{
      "concept_shop", ScType::ConstNodeClass};

  // Отношения
  static inline ScKeynode const nrel_result{
      "nrel_result", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_loaded_data{
      "nrel_loaded_data", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_x{"nrel_x", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_y{"nrel_y", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_id{"nrel_id", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_transport_cost{"nrel_transport_cost", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_economy{"nrel_economy", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_serves_shops{"nrel_serves_shops", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_shop_count{"nrel_shop_count", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_total_volume{"nrel_total_volume", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_warehouse{"nrel_warehouse", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_volume{"nrel_volume", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_recommendation{
      "nrel_recommendation", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_is_valid{
      "nrel_is_valid", ScType::ConstNodeNonRole};

  // Системные
  static inline ScKeynode const lang_ru{"lang_ru", ScType::ConstNodeClass};
  static inline ScKeynode const nrel_main_idtf{"nrel_main_idtf", ScType::ConstNodeNonRole};
  static inline ScKeynode const action{"action", ScType::ConstNodeClass};
  static inline ScKeynode const rrel_1{"rrel_1", ScType::ConstNodeRole};
  static inline ScKeynode const rrel_2{"rrel_2", ScType::ConstNodeRole};
  static inline ScKeynode const rrel_3{"rrel_3", ScType::ConstNodeRole};
  static inline ScKeynode const rrel_4{"rrel_4", ScType::ConstNodeRole};
  static inline ScKeynode const rrel_5{"rrel_5", ScType::ConstNodeRole};
};
