from experta import Fact, KnowledgeEngine, Rule, DefFacts, MATCH, TEST, NOT, AS


class TriangleInput(Fact):
    """Входные данные: стороны треугольника."""
    pass


class TriangleResult(Fact):
    """Результат: тип треугольника."""
    pass


class ProcessedTriangle(Fact):
    """Маркер обработанного треугольника."""
    pass


class TriangleClassifier(KnowledgeEngine):

    def get_user_input(self):
        """Получение сторон треугольника от пользователя."""
        print("Введите длины сторон треугольника:")
        try:
            a = float(input("Сторона a: "))
            b = float(input("Сторона b: "))
            c = float(input("Сторона c: "))
            return a, b, c
        except ValueError:
            print("Ошибка: введите числовые значения")
            return None

    @Rule(
        AS.input_fact << TriangleInput(a=MATCH.a, b=MATCH.b, c=MATCH.c),
        TEST(lambda a, b, c: a <= 0 or b <= 0 or c <= 0 or
             a + b <= c or a + c <= b or b + c <= a),
        NOT(ProcessedTriangle(a=MATCH.a, b=MATCH.b, c=MATCH.c)),
        salience=100
    )
    def invalid_triangle(self, input_fact, a, b, c):
        """Правило 1: Проверка существования треугольника."""
        print(f"[Правило 1] Активировано: Стороны ({a}, {b}, {c}) не образуют треугольник")
        self.declare(TriangleResult(sides=(a, b, c), type="не существует"))
        self.declare(ProcessedTriangle(a=a, b=b, c=c))
        self.retract(input_fact)

    @Rule(
        AS.input_fact << TriangleInput(a=MATCH.a, b=MATCH.b, c=MATCH.c),
        TEST(lambda a, b, c: a > 0 and b > 0 and c > 0 and
             a + b > c and a + c > b and b + c > a),
        TEST(lambda a, b, c: abs(a - b) < 1e-6 and abs(b - c) < 1e-6),
        NOT(ProcessedTriangle(a=MATCH.a, b=MATCH.b, c=MATCH.c)),
        salience=90
    )
    def equilateral_triangle(self, input_fact, a, b, c):
        """Правило 2: Равносторонний треугольник."""
        print(f"[Правило 2] Активировано: Треугольник ({a}, {b}, {c}) — равносторонний")
        self.declare(TriangleResult(sides=(a, b, c), type="равносторонний"))
        self.declare(ProcessedTriangle(a=a, b=b, c=c))
        self.retract(input_fact)

    @Rule(
        AS.input_fact << TriangleInput(a=MATCH.a, b=MATCH.b, c=MATCH.c),
        TEST(lambda a, b, c: a > 0 and b > 0 and c > 0 and
             a + b > c and a + c > b and b + c > a),
        TEST(lambda a, b, c: abs(a**2 + b**2 - c**2) < 1e-6 or
             abs(a**2 + c**2 - b**2) < 1e-6 or
             abs(b**2 + c**2 - a**2) < 1e-6),
        NOT(ProcessedTriangle(a=MATCH.a, b=MATCH.b, c=MATCH.c)),
        salience=80
    )
    def right_triangle(self, input_fact, a, b, c):
        """Правило 3: Прямоугольный треугольник."""
        print(f"[Правило 3] Активировано: Треугольник ({a}, {b}, {c}) — прямоугольный")
        self.declare(TriangleResult(sides=(a, b, c), type="прямоугольный"))
        self.declare(ProcessedTriangle(a=a, b=b, c=c))
        self.retract(input_fact)

    @Rule(
        AS.input_fact << TriangleInput(a=MATCH.a, b=MATCH.b, c=MATCH.c),
        TEST(lambda a, b, c: a > 0 and b > 0 and c > 0 and
             a + b > c and a + c > b and b + c > a),
        TEST(lambda a, b, c: (abs(a - b) < 1e-6 and abs(a - c) > 1e-6) or
             (abs(a - c) < 1e-6 and abs(a - b) > 1e-6) or
             (abs(b - c) < 1e-6 and abs(a - b) > 1e-6)),
        NOT(ProcessedTriangle(a=MATCH.a, b=MATCH.b, c=MATCH.c)),
        salience=70
    )
    def isosceles_triangle(self, input_fact, a, b, c):
        """Правило 4: Равнобедренный треугольник."""
        print(f"[Правило 4] Активировано: Треугольник ({a}, {b}, {c}) — равнобедренный")
        self.declare(TriangleResult(sides=(a, b, c), type="равнобедренный"))
        self.declare(ProcessedTriangle(a=a, b=b, c=c))
        self.retract(input_fact)

    @Rule(
        AS.input_fact << TriangleInput(a=MATCH.a, b=MATCH.b, c=MATCH.c),
        TEST(lambda a, b, c: a > 0 and b > 0 and c > 0 and
             a + b > c and a + c > b and b + c > a),
        TEST(lambda a, b, c: a**2 > b**2 + c**2 + 1e-6 or
             b**2 > a**2 + c**2 + 1e-6 or
             c**2 > a**2 + b**2 + 1e-6),
        NOT(ProcessedTriangle(a=MATCH.a, b=MATCH.b, c=MATCH.c)),
        salience=60
    )
    def obtuse_triangle(self, input_fact, a, b, c):
        """Правило 5: Тупоугольный треугольник."""
        print(f"[Правило 5] Активировано: Треугольник ({a}, {b}, {c}) — тупоугольный")
        self.declare(TriangleResult(sides=(a, b, c), type="тупоугольный"))
        self.declare(ProcessedTriangle(a=a, b=b, c=c))
        self.retract(input_fact)

    @Rule(
        AS.input_fact << TriangleInput(a=MATCH.a, b=MATCH.b, c=MATCH.c),
        TEST(lambda a, b, c: a > 0 and b > 0 and c > 0 and
             a + b > c and a + c > b and b + c > a),
        TEST(lambda a, b, c: a**2 < b**2 + c**2 - 1e-6 and
             b**2 < a**2 + c**2 - 1e-6 and
             c**2 < a**2 + b**2 - 1e-6),
        NOT(ProcessedTriangle(a=MATCH.a, b=MATCH.b, c=MATCH.c)),
        salience=50
    )
    def acute_triangle(self, input_fact, a, b, c):
        """Правило 6: Остроугольный треугольник."""
        print(f"[Правило 6] Активировано: Треугольник ({a}, {b}, {c}) — остроугольный")
        self.declare(TriangleResult(sides=(a, b, c), type="остроугольный"))
        self.declare(ProcessedTriangle(a=a, b=b, c=c))
        self.retract(input_fact)

    @Rule(
        AS.input_fact << TriangleInput(a=MATCH.a, b=MATCH.b, c=MATCH.c),
        NOT(ProcessedTriangle(a=MATCH.a, b=MATCH.b, c=MATCH.c)),
        salience=10
    )
    def unknown_triangle(self, input_fact, a, b, c):
        """Правило 7: Fallback для неопределённых случаев."""
        print(f"[Правило 7] Активировано: Треугольник ({a}, {b}, {c}) — разносторонний")
        self.declare(TriangleResult(sides=(a, b, c), type="разносторонний"))
        self.declare(ProcessedTriangle(a=a, b=b, c=c))
        self.retract(input_fact)


if __name__ == "__main__":
    print("=== Экспертная система классификации треугольников ===\n")

    while True:
        engine = TriangleClassifier()
        engine.reset()

        sides = engine.get_user_input()
        if sides is None:
            continue

        a, b, c = sides
        engine.declare(TriangleInput(a=a, b=b, c=c))

        print()
        engine.run()

        print("\n=== Результат ===")
        for fact in engine.facts.values():
            if isinstance(fact, TriangleResult):
                triangle_type = fact.get('type', 'N/A')
                print(f"Треугольник со сторонами ({a}, {b}, {c}): {triangle_type}")

        print()
        continue_input = input("Проверить ещё один треугольник? (да/нет): ").strip().lower()
        if continue_input not in ['да', 'д', 'yes', 'y']:
            print("Завершение работы.")
            break
        print()
