cmake_minimum_required(VERSION 3.16)
project(logistics-module VERSION 1.0.0 LANGUAGES CXX)

# Поиск зависимостей
find_package(sc-machine REQUIRED)
find_package(GTest REQUIRED)
include(GoogleTest)

# Сбор исходных кодов
file(GLOB SOURCES CONFIGURE_DEPENDS
    "*.cpp" "*.hpp"
    "agents/*.cpp" "agents/*.hpp"
    "keynodes/*.hpp"
    "utils/*.cpp" "utils/*.hpp"
)

# 1. СНАЧАЛА создаем цель (библиотеку)
add_library(logistics-module SHARED ${SOURCES})

# 2. ЗАТЕМ привязываем к ней библиотеки
target_link_libraries(logistics-module
    PUBLIC sc-machine::sc-memory
    PUBLIC sc-machine::sc-agents-common
)

target_include_directories(logistics-module
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}
)

set_target_properties(logistics-module PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/extensions)

if(SC_CLANG_FORMAT_CODE)
    target_clangformat_setup(logistics-module)
endif()

# Тесты
file(GLOB TEST_SOURCES CONFIGURE_DEPENDS
    "test/*.cpp"
)

if(TEST_SOURCES)
    add_executable(logistics-module-tests ${TEST_SOURCES})
    target_link_libraries(logistics-module-tests
        PRIVATE GTest::gtest_main
        PRIVATE logistics-module
    )
    target_include_directories(logistics-module-tests
        PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}
    )
    gtest_discover_tests(logistics-module-tests
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/test
    )
endif()