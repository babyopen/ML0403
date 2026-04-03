 import sqlite3
import pandas as pd

def check_2026_data():
    """
    详细检查2026年的数据
    """
    try:
        conn = sqlite3.connect('lottery.db')
        
        # 查询2026年的所有记录
        query = "SELECT period, zodiac, date FROM lottery_history WHERE date LIKE '2026%' ORDER BY period"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print("2026年开奖数据详细检查：")
        print("=" * 80)
        print(f"总记录数: {len(df)}")
        print(f"\n期号范围: {df['period'].min()} 到 {df['period'].max()}")
        print(f"日期范围: {df['date'].min()} 到 {df['date'].max()}")
        
        # 检查期号分布
        print("\n期号分布统计：")
        print(f"期号小于2026000的记录数: {len(df[df['period'] < 2026000])}")
        print(f"期号在2026000-2026093之间的记录数: {len(df[(df['period'] >= 2026000) & (df['period'] <= 2026093)])}")
        print(f"期号大于2026093的记录数: {len(df[df['period'] > 2026093])}")
        
        # 显示期号小于2026000的记录
        if len(df[df['period'] < 2026000]) > 0:
            print("\n期号小于2026000的记录（前10条）：")
            print(df[df['period'] < 2026000].head(10))
        
        # 显示期号大于2026093的记录
        if len(df[df['period'] > 2026093]) > 0:
            print("\n期号大于2026093的记录：")
            print(df[df['period'] > 2026093])
        
        # 检查重复的期号
        duplicates = df[df.duplicated('period', keep=False)]
        if len(duplicates) > 0:
            print(f"\n发现 {len(duplicates)} 条重复期号记录：")
            print(duplicates)
        
        # 显示所有2026年的记录（按日期排序）
        print("\n2026年所有记录（按日期排序，前20条）：")
        df_sorted = df.sort_values('date')
        print(df_sorted.head(20))
        
        print("\n2026年所有记录（按日期排序，后20条）：")
        print(df_sorted.tail(20))
        
    except Exception as e:
        print(f"检查数据时出错: {e}")

if __name__ == "__main__":
    check_2026_data()
