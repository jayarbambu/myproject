import sqlite3
import os

DB = 'shopping.db'
INSTANCE_DB = os.path.join(os.path.dirname(__file__), 'instance', 'shopping.db')

def ensure_image_column(db_path=None):
    # try several possible DB locations
    candidates = []
    if db_path:
        candidates.append(db_path)
    candidates.append(os.path.join(os.path.dirname(__file__), DB))
    candidates.append(INSTANCE_DB)
    db_path = next((p for p in candidates if p and os.path.exists(p)), None)
    if not db_path:
        print('DB not found; nothing to migrate')
        return
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info('product')")
    cols = [r[1] for r in cur.fetchall()]
    if 'image' in cols:
        print('image column already exists')
    else:
        try:
            cur.execute("ALTER TABLE product ADD COLUMN image TEXT")
            conn.commit()
            print('Added image column')
        except Exception as e:
            print('Failed to add image column:', e)
    if 'stock' in cols:
        print('stock column already exists')
    else:
        try:
            cur.execute("ALTER TABLE product ADD COLUMN stock INTEGER DEFAULT 50")
            conn.commit()
            print('Added stock column')
        except Exception as e:
            print('Failed to add stock column:', e)
    conn.close()


def ensure_uploads():
    uploads = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    os.makedirs(uploads, exist_ok=True)
    print('Ensured uploads dir at', uploads)


if __name__ == '__main__':
    ensure_image_column()
    ensure_uploads()
