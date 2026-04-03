import sqlite3
import pandas as pd

def check_all_records():
    """
    查看数据库中所有记录的时间分布
    """
    try:
        conn = sqlite3.connect('lottery.db')
        
        # 查询所有记录，按日期排序
        query = "SELECT period, zodiac, date FROM lottery_history ORDER BY date"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print("数据库中所有记录的时间分布：")
        print("=" * 80)
        print(f"总记录数: {len(df)}")
        
        # 按年份统计
        df['year'] = df['date'].str[:4]
        year_counts = df['year'].value_counts().sort_index()
        
        print("\n按年份统计：")
        for year, count in year_counts.items():
            print(f"  {year}年: {count}条记录")
        
        # 显示日期范围
        print(f"\n日期范围: {df['date'].min()} 到 {df['date'].max()}")
        
        # 显示期号范围
        print(f"期号范围: {df['period'].min()} 到 {df['period'].max()}")
        
        # 按年份显示期号范围
        print("\n各年份期号范围：")
        for year in year_counts.index:
            year_data = df[df['year'] == year]
            print(f"  {year}年: 期号 {year_data['period'].min()} 到 {year_data['period'].max()}")
        
        # 显示前10条记录
        print("\n前10条记录：")
        print(df.head(10)[['period', 'zodiac', 'date']])
        
        # 显示后10条记录
        print("\n后10条记录：")
        print(df.tail(10)[['period', 'zodiac', 'date']])
        
    except Exception as e:
        print(f"检查数据时出错: {e}")

if __name__ == "__main__":
    check_all_records()
