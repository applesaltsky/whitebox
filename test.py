import sqlite3

with sqlite3.connect(r'C:\Users\User\Desktop\Programming\whitebox\databases\main.db') as conn:
    cursor = conn.cursor()
    rst = cursor.execute('select * from content_table where title = "test3"' )
    for i in rst:
        print(i)
    