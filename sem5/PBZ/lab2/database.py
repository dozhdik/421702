import sqlite3

def init_database():
    connection = sqlite3.connect('../data/insurance.db')
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Employee(
        КодОрганизации INTEGER PRIMATY KEY NOT NULL,
        ФИО TEXT NOT NULL,
        Возраст TEXT NOT NULL,
        КатегорияРиска TEXT NOT NULL
        )
    ''')

    connection.commit()
    connection.close()