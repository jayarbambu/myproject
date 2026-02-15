import sqlite3
import os

db_path = 'instance/shopping.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print('Existing tables:', tables)
    conn.close()
    
    # Recreate DB to ensure all tables are created
    print('Removing old DB to recreate with all tables...')
    os.remove(db_path)
    print('Database removed. Restart the server to recreate with Order/OrderItem tables.')
else:
    print('Database does not exist.')
