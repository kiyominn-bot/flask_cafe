import sqlite3

# データベースに接続
conn = sqlite3.connect(DATABASE)

cur = conn.cursor()

# purchases テーブルに user_name カラムを追加
try:
    cur.execute("ALTER TABLE purchases ADD COLUMN user_name TEXT")
    print("✅ user_name カラムを追加しました")
except sqlite3.OperationalError as e:
    print("⚠ すでにカラムが存在している可能性があります:", e)

conn.commit()
conn.close()
