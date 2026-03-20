#!/bin/bash

cd "$(dirname "$0")"

echo "=== Building project ==="
if [ ! -d "cmake-build-debug" ]; then
    mkdir -p cmake-build-debug
fi
cd cmake-build-debug
cmake .. > /dev/null 2>&1 || cmake ..
BUILD_OUTPUT=$(cmake --build . --target tests lab2s 2>&1)
BUILD_RESULT=$?
echo "$BUILD_OUTPUT" | grep -v "ninja: no work to do"
if [ $BUILD_RESULT -ne 0 ]; then
    exit 1
fi

echo ""
echo "=== Running tests ==="
TEST_RESULT=0
./tests --gtest_color=no 2>&1 | \
    awk '
    BEGIN {
        test_count = 0;
        GREEN = "\033[32m";
        RED = "\033[31m";
        RESET = "\033[0m";
    }
    /^\[ RUN      \]/ { 
        test_name = $0; 
        gsub(/^\[ RUN      \] /, "", test_name);
        test_count++;
        current_test = sprintf("[%3d] %s", test_count, test_name);
        next
    }
    /^\[       OK \]/ {
        printf "%s%s - ✓ PASSED%s\n", GREEN, current_test, RESET;
        next
    }
    /^\[  FAILED  \]/ {
        printf "%s%s - ✗ FAILED%s\n", RED, current_test, RESET;
        next
    }
    /^\[==========\]/ { 
        if (/Running.*tests from.*test suites/) {
            next
        }
        print "\n" $0; 
        next 
    }
    /^\[  PASSED  \]/ { 
        print $0; 
        next 
    }
    /^\[  FAILED  \]/ { 
        print $0; 
        next 
    }
    { 
        if (/^Maintenance|^Using|^=== Organizing|^Preparing|^Boarding|^Setting|^Flight|^Climate|^Passenger|^==== AIRLINE|^Select|^Running main|^$/) {
            next
        }
    }
    ' || TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo -e "\033[32m✓ All tests passed!\033[0m"
else
    echo ""
    echo -e "\033[31m✗ Some tests failed (exit code: $TEST_RESULT)\033[0m"
fi

cd ..

echo ""
echo "=== Generating coverage report ==="
if [ -f "generate_coverage.sh" ]; then
    ./generate_coverage.sh
else
    echo "Warning: generate_coverage.sh not found, skipping coverage generation"
fi

echo ""
echo "=== Generating Doxygen documentation ==="
if [ -f "Doxyfile" ]; then
    doxygen Doxyfile > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Doxygen documentation generated"
    else
        echo "✗ Doxygen generation failed"
    fi
else
    echo "Warning: Doxyfile not found, skipping Doxygen generation"
fi

echo ""
echo "=== Opening Doxygen documentation ==="
# Open only Doxygen documentation (it contains links to all coverage reports)
if [ -f "docs/html/index.html" ]; then
    open docs/html/index.html 2>/dev/null || xdg-open docs/html/index.html 2>/dev/null
    echo "✓ Opened docs/html/index.html (all reports accessible from here)"
else
    echo "Warning: Doxygen documentation not found"
fi

echo ""
echo "=== Running main program ==="
cd cmake-build-debug
./lab2s