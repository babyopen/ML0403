import sqlite3

def clean_duplicate_data():
    """
    清理数据库中的重复数据，只保留完整期号格式的数据
    """
    try:
        conn = sqlite3.connect('lottery.db')
        cursor = conn.cursor()
        
        # 查看清理前的记录数
        cursor.execute('SELECT COUNT(*) FROM lottery_history')
        count_before = cursor.fetchone()[0]
        print(f"清理前记录数: {count_before}")
        
        # 删除期号小于1000的记录（这些应该是旧格式的数据）
        # 因为正常的期号格式应该是2026xxx，至少有7位数字
        cursor.execute('DELETE FROM lottery_history WHERE period < 1000')
        deleted_count = cursor.rowcount
        
        conn.commit()
        
        # 查看清理后的记录数
        cursor.execute('SELECT COUNT(*) FROM lottery_history')
        count_after = cursor.fetchone()[0]
        print(f"清理后记录数: {count_after}")
        print(f"删除的记录数: {deleted_count}")
        
        # 检查2026年的记录数
        cursor.execute("SELECT COUNT(*) FROM lottery_history WHERE date LIKE '2026%'")
        count_2026 = cursor.fetchone()[0]
        print(f"2026年记录数: {count_2026}")
        
        # 显示期号范围
        cursor.execute('SELECT MIN(period), MAX(period) FROM lottery_history WHERE date LIKE "2026%"')
        min_period, max_period = cursor.fetchone()
        print(f"2026年期号范围: {min_period} 到 {max_period}")
        
        conn.close()
        print("\n数据清理完成！")
        
    except Exception as e:
        print(f"清理数据时出错: {e}")

if __name__ == "__main__":
    clean_duplicate_data()
