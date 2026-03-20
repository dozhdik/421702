cmake_minimum_required(VERSION 3.14)

project(lab2s)

set(CMAKE_CXX_STANDARD 20)

add_executable(lab2s main.cpp airline.cpp airline.hpp)

target_include_directories(lab2s PUBLIC ${PROJECT_SOURCE_DIR})

include(FetchContent)

FetchContent_Declare(googletest URL https://github.com/google/googletest/archive/release-1.12.1.zip DOWNLOAD_EXTRACT_TIMESTAMP TRUE)

FetchContent_MakeAvailable(googletest)

enable_testing()

add_executable(tests tests/airlineTests.cpp airline.cpp main.cpp)

target_include_directories(tests PUBLIC ${PROJECT_SOURCE_DIR})

target_compile_definitions(tests PRIVATE TESTING)

# Coverage support (gcov/lcov)
# Coverage flags are set via CMake command line or in generate_coverage.sh
# This ensures debug symbols are always available
target_compile_options(tests PRIVATE -g)

target_link_libraries(tests gtest_main)

include(GoogleTest)

# Use gtest_add_tests instead of gtest_discover_tests to avoid running executable for discovery
# This prevents interactive menu from running during test discovery
gtest_add_tests(TARGET tests
    TEST_PREFIX ""
    TEST_SUFFIX ""
    EXTRA_ARGS ""
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
)