import sqlite3

db_path = "data.db"

def update_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 檢查欄位是否存在，若不存在則新增
    cursor.execute("PRAGMA table_info(predictions)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'ez_result' not in columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN ez_result TEXT")
        print("欄位 'ez_result' 已新增")
    
    if 'amp_result' not in columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN amp_result TEXT")
        print("欄位 'amp_result' 已新增")
    
    conn.commit()
    conn.close()
    print("資料庫更新完成！")

update_db()
