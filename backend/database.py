import sqlite3


DB="results.db"



def create_table():

    conn=sqlite3.connect(DB)

    cur=conn.cursor()


    cur.execute("""

    CREATE TABLE IF NOT EXISTS results(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    filename TEXT,

    grade TEXT,

    score INTEGER,

    freshness TEXT,

    blue_ratio REAL,

    R INTEGER,

    G INTEGER,

    B INTEGER,

    H INTEGER,

    S INTEGER,

    V INTEGER,

    analysis TEXT

    )

    """)


    conn.commit()
    conn.close()





def save_result(filename,data):

    conn=sqlite3.connect(DB)

    cur=conn.cursor()


    cur.execute("""

    INSERT INTO results VALUES

    (
    NULL,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
    )

    """,

    (

    filename,

    data["grade"],

    data["score"],

    data["freshness"],

    data["blue_ratio"],

    data["sensor_color"]["R"],

    data["sensor_color"]["G"],

    data["sensor_color"]["B"],

    data["hsv"]["H"],

    data["hsv"]["S"],

    data["hsv"]["V"],

    data["analysis"]

    ))


    conn.commit()
    conn.close()