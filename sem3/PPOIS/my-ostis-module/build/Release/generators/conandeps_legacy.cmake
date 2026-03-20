message(STATUS "Conan: Using CMakeDeps conandeps_legacy.cmake aggregator via include()")
message(STATUS "Conan: It is recommended to use explicit find_package() per dependency instead")

find_package(sc-machine)
find_package(GTest)

set(CONANDEPS_LEGACY  sc-machine::sc-machine  gtest::gtest )