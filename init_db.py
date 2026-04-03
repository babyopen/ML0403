import sqlite3
import os

DATABASE_PATH = 'lottery.db'

def init_database():
    """初始化数据库，创建必要的表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建开奖历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lottery_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period INTEGER UNIQUE NOT NULL,
            zodiac INTEGER NOT NULL,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建预测历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period INTEGER NOT NULL,
            prediction TEXT NOT NULL,
            result TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")

if __name__ == '__main__':
    init_database()
