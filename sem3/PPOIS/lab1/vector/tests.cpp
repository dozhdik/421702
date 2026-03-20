/**
 * @file tests.cpp
 * @brief Unit тесты для проверки функциональности классов Ribbon, Rules и Machine.
 * @details
 * Этот файл содержит 31 Unit тест, обеспечивающих покрытие кода 31%
 *
 * @author Дождиков Александр, гр. 421702
 * @see Vector
 */
#include "vector.h"
#include <UnitTest++/UnitTest++.h>
#include <sstream>
#include <cmath>
#include <limits>

static const double EPS = 1e-6;

TEST(Constructor_Default_IsZero)
{
    Vector v;
    CHECK_CLOSE(0.0, v.get_lenth(), EPS);
}

TEST(Constructor_Params_Length)
{
    Vector v(1.0, 2.0, 2.0);
    CHECK_CLOSE(3.0, v.get_lenth(), EPS);
}

TEST(CopyConstructor_ProducesEqualObject)
{
    Vector a(1.0, -2.0, 3.5);
    Vector b(a);
    CHECK(b == a);
    CHECK_CLOSE(a.get_lenth(), b.get_lenth(), EPS);
}

TEST(AssignmentOperator_CopiesValues)
{
    Vector a(2.0, 3.0, 4.0);
    Vector b;
    b = a;
    CHECK(b == a);
}

TEST(Addition_OperatorPlus)
{
    Vector a(1.0, 2.0, 3.0);
    Vector b(4.0, -1.0, 0.5);
    Vector c = a + b;
    Vector expected(5.0, 1.0, 3.5);
    CHECK(c == expected);
}

TEST(OperatorPlusEquals_ModifiesLeft)
{
    Vector a(1.0, 1.0, 1.0);
    Vector b(2.0, 3.0, 4.0);
    a += b;
    Vector expected(3.0, 4.0, 5.0);
    CHECK(a == expected);
}

TEST(Subtraction_OperatorMinus)
{
    Vector a(5.0, 4.0, 3.0);
    Vector b(1.0, 2.0, 3.0);
    Vector c = a - b;
    Vector expected(4.0, 2.0, 0.0);
    CHECK(c == expected);
}

TEST(OperatorMinusEquals_ModifiesLeft)
{
    Vector a(5.0, 5.0, 5.0);
    Vector b(1.0, 2.0, 3.0);
    a -= b;
    Vector expected(4.0, 3.0, 2.0);
    CHECK(a == expected);
}

TEST(CrossProduct_OperatorMultiply_Vector)
{
    Vector a(1.0, 0.0, 0.0);
    Vector b(0.0, 1.0, 0.0);
    Vector c = a * b; 
    Vector expected(0.0, 0.0, 1.0);
    CHECK(c == expected);
}

TEST(CrossProduct_OperatorMultiplyAssign)
{
    Vector a(0.0, 1.0, 0.0);
    Vector b(0.0, 0.0, 1.0);
    a *= b; 
    Vector expected(1.0, 0.0, 0.0);
    CHECK(a == expected);
}

TEST(ScalarMultiplication_OperatorMultiplyDouble)
{
    Vector a(1.5, -2.0, 4.0);
    Vector b = a * 2.0;
    Vector expected(3.0, -4.0, 8.0);
    CHECK(b == expected);
}

TEST(ScalarMultiplication_OperatorMultiplyAssignDouble)
{
    Vector a(1.0, 2.0, 3.0);
    a *= 3.0;
    Vector expected(3.0, 6.0, 9.0);
    CHECK(a == expected);
}

TEST(Division_PerComponent)
{
    Vector a(6.0, 8.0, 10.0);
    Vector b(2.0, 4.0, 5.0);
    Vector c = a / b;
    Vector expected(3.0, 2.0, 2.0);
    CHECK(c == expected);
}

TEST(DivisionAssign_PerComponent)
{
    Vector a(9.0, 6.0, 3.0);
    Vector b(3.0, 2.0, 1.0);
    a /= b;
    Vector expected(3.0, 3.0, 3.0);
    CHECK(a == expected);
}

TEST(DivisionByZero_Throws)
{
    Vector a(1.0, 2.0, 3.0);
    Vector b(1.0, 0.0, 1.0);
    CHECK_THROW(a / b, std::runtime_error);
}

TEST(DivideAssignByZero_Throws)
{
    Vector a(1.0, 2.0, 3.0);
    Vector b(0.0, 0.0, 0.0);
    CHECK_THROW(a /= b, std::runtime_error);
}

TEST(DotProduct_CosineOperator_NormalCase)
{
    Vector a(1.0, 0.0, 0.0);
    Vector b(0.0, 1.0, 0.0);
    double cosab = a ^ b;
    CHECK_CLOSE(0.0, cosab, EPS);
}

TEST(DotProduct_CosineOperator_AngleZero)
{
    Vector a(1.0, 2.0, 3.0);
    Vector b(2.0, 4.0, 6.0);
    double cosab = a ^ b; 
    CHECK_CLOSE(1.0, cosab, 1e-9);
}

TEST(DotProduct_WithZeroVector_Throws)
{
    Vector zero;
    Vector a(1.0, 2.0, 3.0);
    CHECK_THROW(zero ^ a, std::runtime_error);
    CHECK_THROW(a ^ zero, std::runtime_error);
}

TEST(Comparison_GreaterAndLess)
{
    Vector small(1.0, 0.0, 0.0);
    Vector big(3.0, 4.0, 0.0);
    CHECK(big > small);
    CHECK(!(small > big));
    CHECK(small < big);
    CHECK(!(big < small));
}

TEST(Comparison_GreaterEqualLessEqual)
{
    Vector a(1.0, 2.0, 2.0); 
    Vector b(3.0, 0.0, 0.0); 
    CHECK(a >= b);
    CHECK(b <= a);
}

TEST(EqualityAndInequality)
{
    Vector a(1.1, 2.2, 3.3);
    Vector b(1.1, 2.2, 3.3);
    Vector c(1.1, 2.2, -3.3);
    CHECK(a == b);
    CHECK(!(a != b));
    CHECK(a != c);
    CHECK(!(a == c));
}

TEST(Stream_Output_Format)
{
    Vector a(1.0, 2.0, 3.0);
    std::stringstream ss;
    ss << a;
    std::string s = ss.str();

    CHECK(s.find("1") != std::string::npos);
    CHECK(s.find("2") != std::string::npos);
    CHECK(s.find("3") != std::string::npos);
}

TEST(Stream_Input_ReadsValues)
{
    Vector a;
    std::stringstream ss("7.5 8.5 9.5");
    ss >> a;
    Vector expected(7.5, 8.5, 9.5);
    CHECK(a == expected);
}

TEST(Chain_Add_Subtract_CommutativityCheck)
{
    Vector a(1.0, 1.0, 1.0);
    Vector b(2.0, 0.5, -1.0);
    Vector c = a + b - a; 
    CHECK(c == b);
}

TEST(CrossProduct_AssociativityNotRequired)
{
    Vector a(1,0,0), b(0,1,0), c(0,0,1);
    Vector r = a * b;
    CHECK(r == c);
}

TEST(Scalar_Multiplication_DoesNotAffectOriginal_WhenUsingBinary)
{
    Vector a(1,2,3);
    Vector b = a * 2.0;
    Vector expected(2,4,6);
    CHECK(b == expected);
    Vector original(1,2,3);
    CHECK(a == original);
}

TEST(OperatorMultiplyAssign_WithVector_ProducesCorrectLength)
{
    Vector a(1,2,3);
    Vector b(4,5,6);
    a *= b;

    Vector cross = Vector(1,2,3) * Vector(4,5,6);
    CHECK_CLOSE(a.get_lenth(), cross.get_lenth(), EPS);
}

TEST(Assignment_ToDefaultSizedVector_Works)
{
    Vector a(1,2,3);
    Vector b; 
    b = a;
    CHECK(b == a);
}

TEST(ZeroVector_LengthExactlyZero)
{
    Vector z;
    CHECK_CLOSE(0.0, z.get_lenth(), EPS);
}

TEST(Operators_DoNotThrow_ForTypicalInputs)
{
    Vector a(1,2,3), b(2,3,4);

    try { a + b; }
    catch(...) { CHECK(false); }

    try { a - b; }
    catch(...) { CHECK(false); }

    try { a * b; }
    catch(...) { CHECK(false); }

    try { a * 2.5; }
    catch(...) { CHECK(false); }

    try { a ^ b; }
    catch(...) { CHECK(false); }
}

int main()
{
    return UnitTest::RunAllTests();
}
