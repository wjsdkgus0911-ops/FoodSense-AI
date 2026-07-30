import sqlite3
from datetime import datetime



DB_NAME="food_ai.db"



def init_database():

    conn=sqlite3.connect(DB_NAME)

    cursor=conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    time TEXT,

    grade TEXT,

    score REAL,

    freshness TEXT,

    blue_ratio REAL

    )
    """)


    conn.commit()

    conn.close()





def save_result(result):

    conn=sqlite3.connect(DB_NAME)

    cursor=conn.cursor()


    cursor.execute("""

    INSERT INTO results
    (
    time,
    grade,
    score,
    freshness,
    blue_ratio
    )

    VALUES
    (?,?,?,?,?)

    """,

    (

    datetime.now().isoformat(),

    result["grade"],

    result["score"],

    result["freshness"],

    result["blue_ratio"]

    ))


    conn.commit()

    conn.close()






def latest_result():

    conn=sqlite3.connect(DB_NAME)

    cursor=conn.cursor()


    cursor.execute("""
    SELECT *
    FROM results
    ORDER BY id DESC
    LIMIT 1
    """)


    data=cursor.fetchone()


    conn.close()


    return data
