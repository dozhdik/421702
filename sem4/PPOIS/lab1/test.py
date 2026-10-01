class MyError(Exception):
    pass

def check_age(age):
    if age < 0:
        raise MyError("возраст не может быть отрицательным")

try:
    check_age(-1)
except MyError as e:
    print(e)