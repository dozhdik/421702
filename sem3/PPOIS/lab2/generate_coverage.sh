#!/bin/bash

# Script to generate test coverage report using gcov/lcov
# gcov/lcov works reliably on both macOS and Linux

set -e

cd "$(dirname "$0")"

BUILD_DIR="cmake-build-debug"
COVERAGE_INFO="coverage.info"
COVERAGE_HTML_DIR="coverage_html"
COVERAGE_PAGE="coverage_report.html"

echo "=== Generating test coverage report with gcov/lcov ==="

# Check if lcov is installed
if ! command -v lcov &> /dev/null; then
    echo "Error: lcov is not installed."
    echo "Installation instructions:"
    echo "  macOS: brew install lcov"
    echo "  Linux: sudo apt-get install lcov  (or use your distribution's package manager)"
    exit 1
fi

# Check if build directory exists
if [ ! -d "$BUILD_DIR" ]; then
    echo "Error: Build directory $BUILD_DIR not found. Please build the project first."
    exit 1
fi

# Ensure tests are built with coverage flags
cd "$BUILD_DIR"

# Configure CMake with coverage flags if not already done
if ! grep -q "coverage" CMakeCache.txt 2>/dev/null; then
    echo "Configuring CMake with coverage support..."
    cmake -DCMAKE_BUILD_TYPE=Debug \
          -DCMAKE_CXX_FLAGS="-g --coverage -fprofile-arcs -ftest-coverage" \
          -DCMAKE_EXE_LINKER_FLAGS="--coverage" \
          .. > /dev/null 2>&1 || cmake -DCMAKE_BUILD_TYPE=Debug \
          -DCMAKE_CXX_FLAGS="-g --coverage -fprofile-arcs -ftest-coverage" \
          -DCMAKE_EXE_LINKER_FLAGS="--coverage" ..
fi

# Build tests with coverage
echo "Building tests with coverage flags..."
cmake --build . --target tests > /dev/null 2>&1 || cmake --build . --target tests

# Run tests to generate coverage data
cd ..
echo "Running tests to generate coverage data..."
cd "$BUILD_DIR"
./tests --gtest_color=no > /dev/null 2>&1
cd ..

# Generate coverage info file
echo "Collecting coverage data..."
set +e  # Temporarily disable exit on error for lcov
lcov --capture --directory "$BUILD_DIR" --output-file "$COVERAGE_INFO" \
     --ignore-errors inconsistent,missing,unsupported,corrupt,empty 2>&1 | grep -v "WARNING\|ERROR" || true
set -e  # Re-enable exit on error

# Remove system and test files from coverage
if [ -f "$COVERAGE_INFO" ]; then
    set +e  # Temporarily disable exit on error
    lcov --remove "$COVERAGE_INFO" \
         '/usr/*' \
         '*/googletest/*' \
         '*/googlemock/*' \
         '*/tests/*' \
         '*/cmake-build-debug/_deps/*' \
         '*/CMakeFiles/*' \
         --output-file "$COVERAGE_INFO" \
         --ignore-errors inconsistent,missing,unsupported,corrupt,empty 2>&1 | grep -v "WARNING\|ERROR" || true
    set -e  # Re-enable exit on error
fi

# Generate HTML report
echo "Generating HTML report..."
if [ -f "$COVERAGE_INFO" ]; then
    set +e  # Temporarily disable exit on error
    genhtml "$COVERAGE_INFO" --output-directory "$COVERAGE_HTML_DIR" \
            --ignore-errors inconsistent,missing,unsupported,corrupt,category,empty \
            --no-function-coverage \
            --no-branch-coverage 2>&1 | grep -v "WARNING\|ERROR" || true
    set -e  # Re-enable exit on error
fi

# Extract coverage percentage from HTML report
COVERAGE_PERCENT="0.00"
TOTAL_LINES=0
COVERED_LINES=0

if [ -f "$COVERAGE_HTML_DIR/index.html" ]; then
    HTML_CONTENT=$(cat "$COVERAGE_HTML_DIR/index.html")
    
    # Extract from table row with Lines coverage
    LINES_SECTION=$(echo "$HTML_CONTENT" | grep -A 3 'class="headerItem">Lines:')
    
    if [ -n "$LINES_SECTION" ]; then
        # Extract percentage (first number with decimal)
        COVERAGE_PERCENT=$(echo "$LINES_SECTION" | grep -oE '[0-9]+\.[0-9]+' | head -1)
        # Extract numbers from td tags in order: percentage, total, covered
        TD_NUMBERS=($(echo "$LINES_SECTION" | grep -oE '<td[^>]*>([0-9]+)</td>' | grep -oE '[0-9]+'))
        if [ ${#TD_NUMBERS[@]} -ge 2 ]; then
            TOTAL_LINES="${TD_NUMBERS[0]}"
            COVERED_LINES="${TD_NUMBERS[1]}"
        fi
    fi
    
    # Fallback: try simple pattern matching
    if [ -z "$COVERAGE_PERCENT" ]; then
        COVERAGE_PERCENT=$(echo "$HTML_CONTENT" | grep -oE '[0-9]+\.[0-9]+&nbsp;%' | head -1 | sed 's/&nbsp;%//')
    fi
fi

# Fallback: try lcov summary
if [ -z "$COVERAGE_PERCENT" ] || [ "$COVERAGE_PERCENT" = "0.00" ] || [ "$COVERAGE_PERCENT" = "" ]; then
    if [ -f "$COVERAGE_INFO" ]; then
        LCOV_SUMMARY=$(lcov --summary "$COVERAGE_INFO" --ignore-errors inconsistent,missing,unsupported,corrupt,empty 2>&1 | grep -v "ERROR\|WARNING" | grep -E "lines|functions|branches")
        COVERAGE_LINE=$(echo "$LCOV_SUMMARY" | grep "lines.*:" | head -1)
        
        if [ -n "$COVERAGE_LINE" ]; then
            COVERAGE_PERCENT=$(echo "$COVERAGE_LINE" | awk '{print $2}' | sed 's/%//')
            TOTAL_LINES=$(echo "$COVERAGE_LINE" | awk '{print $4}')
        fi
    fi
fi

# Calculate covered lines if we have percentage and total
if [ -n "$COVERAGE_PERCENT" ] && [ -n "$TOTAL_LINES" ] && [ "$TOTAL_LINES" != "0" ] && [ "$TOTAL_LINES" != "" ]; then
    if [ -z "$COVERED_LINES" ] || [ "$COVERED_LINES" = "" ]; then
        COVERED_LINES=$(awk "BEGIN {printf \"%.0f\", ($COVERAGE_PERCENT / 100) * $TOTAL_LINES}")
    fi
fi

# Default values if extraction failed
if [ -z "$COVERAGE_PERCENT" ] || [ "$COVERAGE_PERCENT" = "" ]; then
    COVERAGE_PERCENT="0.00"
fi
if [ -z "$TOTAL_LINES" ] || [ "$TOTAL_LINES" = "" ] || ! echo "$TOTAL_LINES" | grep -qE '^[0-9]+$'; then
    TOTAL_LINES=0
fi
if [ -z "$COVERED_LINES" ] || [ "$COVERED_LINES" = "" ] || ! echo "$COVERED_LINES" | grep -qE '^[0-9]+$'; then
    COVERED_LINES=0
fi

echo "Coverage: $COVERAGE_PERCENT% ($COVERED_LINES / $TOTAL_LINES lines)"

# Copy coverage HTML to docs directory for Doxygen
# Copy coverage_html to docs/html/coverage so it's accessible from Doxygen
mkdir -p docs/html/coverage
cp -r "$COVERAGE_HTML_DIR"/* docs/html/coverage/ 2>/dev/null || true

# Create a simple HTML page for Doxygen with link to detailed report
cat > "$COVERAGE_PAGE" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Coverage Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .coverage-info {
            margin: 30px 0;
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 4px solid #4CAF50;
            border-radius: 4px;
        }
        .percentage {
            font-size: 48px;
            font-weight: bold;
            color: #4CAF50;
            margin: 20px 0;
        }
        .details {
            color: #666;
            margin-top: 10px;
        }
        .bar {
            width: 100%;
            height: 30px;
            background-color: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }
        .bar-fill {
            height: 100%;
            background-color: #4CAF50;
            transition: width 0.3s ease;
        }
        .link-button {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        .link-button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Coverage Report</h1>
        <div class="coverage-info">
            <div class="percentage">$COVERAGE_PERCENT%</div>
            <div class="bar">
                <div class="bar-fill" style="width: $COVERAGE_PERCENT%"></div>
            </div>
            <div class="details">
                <strong>Covered lines:</strong> $COVERED_LINES<br>
                <strong>Total lines:</strong> $TOTAL_LINES<br>
                <strong>Uncovered lines:</strong> $((TOTAL_LINES - COVERED_LINES))
            </div>
            <a href="coverage_html/index.html" class="link-button" target="_blank">View Detailed lcov Report</a>
        </div>
        <p style="color: #666; font-size: 14px;">
            This report was generated automatically using gcov/lcov from test execution coverage data.
            The coverage percentage represents the ratio of executed lines to total lines in the source code.
        </p>
    </div>
</body>
</html>
EOF

# Copy coverage_report.html to docs/html for Doxygen integration
mkdir -p docs/html
cp "$COVERAGE_PAGE" docs/html/ 2>/dev/null || true

# Update README.md with coverage information (preserve existing content)
if [ -f "README.md" ]; then
    # Check if README has a Test Coverage section
    if grep -q "## Test Coverage" README.md; then
        # Update existing Test Coverage section
        # Create a temporary file with updated coverage info
        awk -v coverage="$COVERAGE_PERCENT" \
            -v covered="$COVERED_LINES" \
            -v total="$TOTAL_LINES" \
            -v uncovered="$((TOTAL_LINES - COVERED_LINES))" '
        BEGIN { in_coverage = 0; coverage_printed = 0 }
        /^## Test Coverage/ {
            in_coverage = 1
            coverage_printed = 0
            print "## Test Coverage"
            print ""
            print "**Current test coverage: " coverage "%**"
            print ""
            print "- **Covered lines:** " covered
            print "- **Total lines:** " total
            print "- **Uncovered lines:** " uncovered
            print ""
            print "For detailed coverage report, see [Coverage Report](coverage_report.html) or [Detailed lcov Report](coverage_html/index.html)."
            next
        }
        /^## / && in_coverage {
            in_coverage = 0
        }
        in_coverage {
            next
        }
        { print }
        ' README.md > README.md.tmp && mv README.md.tmp README.md
    else
        # Add Test Coverage section at the end
        cat >> README.md << EOF

## Test Coverage

**Current test coverage: $COVERAGE_PERCENT%**

- **Covered lines:** $COVERED_LINES
- **Total lines:** $TOTAL_LINES
- **Uncovered lines:** $((TOTAL_LINES - COVERED_LINES))

For detailed coverage report, see [Coverage Report](coverage_report.html) or [Detailed lcov Report](coverage_html/index.html).
EOF
    fi
    echo "README.md updated with coverage information"
else
    # Create new README if it doesn't exist
    cat > README.md << EOF
# Airline Management System

Airline management system with aircraft, flights, tools, and passenger management.

## Test Coverage

**Current test coverage: $COVERAGE_PERCENT%**

- **Covered lines:** $COVERED_LINES
- **Total lines:** $TOTAL_LINES
- **Uncovered lines:** $((TOTAL_LINES - COVERED_LINES))

For detailed coverage report, see [Coverage Report](coverage_report.html) or [Detailed lcov Report](coverage_html/index.html).

## Building and Testing

\`\`\`bash
# Build project
./run.sh

# Generate coverage report
./generate_coverage.sh
\`\`\`

## Documentation

Generate documentation with Doxygen:
\`\`\`bash
doxygen Doxyfile
\`\`\`

The documentation will be available in \`docs/html/index.html\`.
EOF
    echo "README.md created with coverage information"
fi

echo "Coverage report generated: $COVERAGE_PAGE"
echo "Detailed HTML report: $COVERAGE_HTML_DIR/index.html"
echo "Coverage percentage: $COVERAGE_PERCENT%"