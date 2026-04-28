import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "detection_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建检测历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detection_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,  -- 'image', 'batch', 'video'
            filename TEXT,
            result_path TEXT NOT NULL,
            detection_count INTEGER DEFAULT 0,
            smoke_count INTEGER DEFAULT 0,
            fire_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'completed'
        )
    ''')
    
    conn.commit()
    conn.close()

def add_detection_record(task_id, type_, filename, result_path, detection_count=0, smoke_count=0, fire_count=0):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO detection_history 
        (task_id, type, filename, result_path, detection_count, smoke_count, fire_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, type_, filename, result_path, detection_count, smoke_count, fire_count, datetime.now()))
    
    conn.commit()
    conn.close()

def get_all_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM detection_history ORDER BY created_at DESC
    ''')
    
    records = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "task_id": r[1],
            "type": r[2],
            "filename": r[3],
            "result_path": r[4],
            "detection_count": r[5],
            "smoke_count": r[6],
            "fire_count": r[7],
            "created_at": r[8],
            "status": r[9]
        }
        for r in records
    ]

def get_record_by_task_id(task_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM detection_history WHERE task_id = ?
    ''', (task_id,))
    
    record = cursor.fetchone()
    conn.close()
    
    if record:
        return {
            "id": record[0],
            "task_id": record[1],
            "type": record[2],
            "filename": record[3],
            "result_path": record[4],
            "detection_count": record[5],
            "smoke_count": record[6],
            "fire_count": record[7],
            "created_at": record[8],
            "status": record[9]
        }
    return None

def delete_record(task_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM detection_history WHERE task_id = ?
    ''', (task_id,))
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()