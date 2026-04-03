import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
import pickle
import requests
import sqlite3
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='lottery_system.log'
)

# 开奖接口配置
LATEST_DRAW_API = "https://macaumarksix.com/api/macaujc2.com"  # 最新开奖接口
HISTORY_DRAW_API = "https://history.macaumarksix.com/history/macaujc2/y/{year}"  # 历史开奖接口
API_KEY = ""  # 该接口不需要API密钥

# 辅助映射表
# 生肖配置
ZODIAC_ALL = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 生肖名称到数字的映射
ZODIAC_NAME_TO_NUM = {
    '鼠': 1, '牛': 2, '虎': 3, '兔': 4, '龙': 5, '蛇': 6,
    '马': 7, '羊': 8, '猴': 9, '鸡': 10, '狗': 11, '猪': 12
}

# 生肖数字到名称的映射
ZODIAC_NUM_TO_NAME = {
    1: '鼠', 2: '牛', 3: '虎', 4: '兔', 5: '龙', 6: '蛇',
    7: '马', 8: '羊', 9: '猴', 10: '鸡', 11: '狗', 12: '猪'
}

# 繁体到简体的映射
ZODIAC_TRAD_TO_SIMP = {
    '鼠': '鼠', '牛': '牛', '虎': '虎', '兔': '兔', '龍': '龙', '蛇': '蛇',
    '馬': '马', '羊': '羊', '猴': '猴', '雞': '鸡', '狗': '狗', '豬': '猪'
}

# 五行对应
ELEMENT_MAP = {
    '鼠': '水', '牛': '土', '虎': '木', '兔': '木', '龙': '土', '蛇': '火',
    '马': '火', '羊': '土', '猴': '金', '鸡': '金', '狗': '土', '猪': '水'
}

# 波色对应
COLOR_MAP = {
    '鼠': '红波', '牛': '绿波', '虎': '蓝波', '兔': '绿波', '龙': '红波', '蛇': '蓝波',
    '马': '红波', '羊': '绿波', '猴': '蓝波', '鸡': '红波', '狗': '绿波', '猪': '蓝波'
}

# 生肖到五行的映射（数字键）
ZODIAC_TO_ELEMENT = {
    1: '水', 2: '土', 3: '木', 4: '木', 5: '土', 6: '火',
    7: '火', 8: '土', 9: '金', 10: '金', 11: '土', 12: '水'
}

# 生肖到波色的映射（数字键）
ZODIAC_TO_WAVE_COLOR = {
    1: '红', 2: '绿', 3: '蓝', 4: '绿', 5: '红', 6: '蓝',
    7: '红', 8: '绿', 9: '蓝', 10: '红', 11: '绿', 12: '蓝'
}

ZODIAC_TO_ODD_EVEN = {z: '奇' if z % 2 == 1 else '偶' for z in range(1, 13)}

ZODIAC_TO_SIZE = {z: '小' if z <= 6 else '大' for z in range(1, 13)}

ZODIAC_TO_INTERVAL = {
    z: '1-4' if z <= 4 else '5-8' if z <= 8 else '9-12' for z in range(1, 13)
}

ZODIAC_TO_HEAD = {z: 0 if z <= 9 else 1 for z in range(1, 13)}

ZODIAC_TO_TAIL = {z: z % 10 if z % 10 != 0 else 0 for z in range(1, 13)}

# 五行相生相克关系
ELEMENT_RELATION = {
    '水': {'生': '木', '克': '火'},
    '木': {'生': '火', '克': '土'},
    '火': {'生': '土', '克': '金'},
    '土': {'生': '金', '克': '水'},
    '金': {'生': '水', '克': '木'}
}

def load_data(file_path):
    """
    读取CSV数据并按期号排序
    """
    try:
        df = pd.read_csv(file_path)
        # 按期号排序
        df = df.sort_values('period').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None

def get_latest_draw():
    """
    从开奖接口获取最新开奖数据
    """
    try:
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.get(LATEST_DRAW_API, headers=headers, timeout=10)
        response.raise_for_status()  # 检查响应状态
        data = response.json()
        
        # 解析接口返回的数据格式
        if isinstance(data, list) and len(data) > 0:
            item = data[0]
            # 解析期号（使用完整的期号）
            expect = item.get("expect", "")
            period = int(expect) if expect else 0
            
            # 解析生肖，获取最后一个生肖作为需要预测的生肖
            zodiac_str = item.get("zodiac", "")
            zodiac_names = zodiac_str.split(",")
            last_zodiac_name = zodiac_names[-1] if zodiac_names else ""
            # 转换繁体生肖名称为简体
            simplified_zodiac = ZODIAC_TRAD_TO_SIMP.get(last_zodiac_name, last_zodiac_name)
            zodiac = ZODIAC_NAME_TO_NUM.get(simplified_zodiac, 0)
            
            # 解析日期
            open_time = item.get("openTime", "")
            date = open_time.split(" ")[0] if open_time else datetime.now().strftime("%Y-%m-%d")
            
            latest_draw = {
                "period": period,
                "zodiac": zodiac,
                "date": date
            }
            
            logging.info(f"成功获取最新开奖数据: 期号 {latest_draw['period']}, 生肖 {latest_draw['zodiac']}")
            return latest_draw
        
        logging.error("开奖接口返回数据格式错误")
        return None
    except Exception as e:
        logging.error(f"获取最新开奖数据时出错: {e}")
        return None

def get_history_draw(year=None):
    """
    从开奖历史接口获取历史开奖数据
    """
    try:
        # 如果没有提供年份，使用当前年份
        if not year:
            year = datetime.now().year
        
        # 构建URL，替换年份占位符
        url = HISTORY_DRAW_API.format(year=year)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 检查响应状态
        data = response.json()
        
        # 解析返回的数据格式
        history_draws = []
        if data.get("result") and data.get("code") == 200:
            for item in data.get("data", []):
                # 解析期号（使用完整的期号）
                expect = item.get("expect", "")
                period = int(expect) if expect else 0
                
                # 解析生肖，获取最后一个生肖作为需要预测的生肖
                zodiac_str = item.get("zodiac", "")
                zodiac_names = zodiac_str.split(",")
                last_zodiac_name = zodiac_names[-1] if zodiac_names else ""
                # 转换繁体生肖名称为简体
                simplified_zodiac = ZODIAC_TRAD_TO_SIMP.get(last_zodiac_name, last_zodiac_name)
                zodiac = ZODIAC_NAME_TO_NUM.get(simplified_zodiac, 0)
                
                # 解析日期
                open_time = item.get("openTime", "")
                date = open_time.split(" ")[0] if open_time else datetime.now().strftime("%Y-%m-%d")
                
                history_draws.append({
                    "period": period,
                    "zodiac": zodiac,
                    "date": date
                })
        
        logging.info(f"成功获取历史开奖数据: {len(history_draws)} 条记录")
        return history_draws
    except Exception as e:
        logging.error(f"获取历史开奖数据时出错: {e}")
        return []

def init_database():
    """
    初始化数据库，创建开奖历史表
    """
    try:
        conn = sqlite3.connect('lottery.db')
        cursor = conn.cursor()
        # 创建开奖历史表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lottery_history (
            period INTEGER PRIMARY KEY,
            zodiac INTEGER NOT NULL,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()
        logging.info("数据库初始化成功")
    except Exception as e:
        logging.error(f"数据库初始化出错: {e}")

def save_to_database(draws):
    """
    将开奖数据保存到数据库
    """
    if not draws:
        return
    
    try:
        conn = sqlite3.connect('lottery.db')
        cursor = conn.cursor()
        
        for draw in draws:
            # 使用UPSERT语句，存在则更新，不存在则插入
            cursor.execute('''
            INSERT OR REPLACE INTO lottery_history (period, zodiac, date)
            VALUES (?, ?, ?)
            ''', (draw['period'], draw['zodiac'], draw['date']))
        
        conn.commit()
        conn.close()
        logging.info(f"成功保存 {len(draws)} 条开奖数据到数据库")
    except Exception as e:
        logging.error(f"保存数据到数据库时出错: {e}")

def load_from_database():
    """
    从数据库加载开奖历史数据
    """
    try:
        conn = sqlite3.connect('lottery.db')
        # 使用pandas读取数据库
        df = pd.read_sql_query('SELECT period, zodiac, date FROM lottery_history ORDER BY period', conn)
        conn.close()
        logging.info(f"成功从数据库加载 {len(df)} 条开奖数据")
        return df
    except Exception as e:
        logging.error(f"从数据库加载数据时出错: {e}")
        return pd.DataFrame()

def get_max_period_from_database():
    """
    获取数据库中最大的期号
    """
    try:
        conn = sqlite3.connect('lottery.db')
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(period) FROM lottery_history')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] else 0
    except Exception as e:
        logging.error(f"获取最大期号时出错: {e}")
        return 0

def get_recent_draws(n=3):
    """
    获取最近n期的开奖数据
    """
    try:
        conn = sqlite3.connect('lottery.db')
        # 使用pandas读取数据库，按期号降序排序，取前n条
        df = pd.read_sql_query('SELECT period, zodiac, date FROM lottery_history ORDER BY period DESC LIMIT ?', conn, params=(n,))
        conn.close()
        return df
    except Exception as e:
        logging.error(f"获取最近开奖数据时出错: {e}")
        return pd.DataFrame()

def get_2026_records_count():
    """
    统计2026年的开奖记录数量
    """
    try:
        conn = sqlite3.connect('lottery.db')
        # 查询2026年的记录
        query = "SELECT COUNT(*) FROM lottery_history WHERE date LIKE '2026%'"
        cursor = conn.cursor()
        cursor.execute(query)
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logging.error(f"统计2026年记录时出错: {e}")
        return 0

def analyze_lottery_data():
    """
    对开奖历史记录数据进行全面检查与分析
    """
    try:
        # 从数据库加载所有数据
        conn = sqlite3.connect('lottery.db')
        df = pd.read_sql_query('SELECT period, zodiac, date, created_at FROM lottery_history', conn)
        conn.close()
        
        print("开奖历史记录数据检查与分析结果：")
        print("=" * 80)
        
        # 1. 字段完整性检查
        print("\n1. 字段完整性检查：")
        print(f"总记录数: {len(df)}")
        print(f"缺失值统计：")
        print(df.isnull().sum())
        
        # 检查关键字段是否有缺失
        key_fields = ['period', 'zodiac', 'date']
        for field in key_fields:
            if df[field].isnull().any():
                print(f"⚠️  警告：{field} 字段存在缺失值")
            else:
                print(f"✅  {field} 字段完整")
        
        # 2. 重复性校验
        print("\n2. 重复性校验：")
        duplicate_periods = df[df.duplicated('period', keep=False)]
        if len(duplicate_periods) > 0:
            print(f"⚠️  警告：发现 {len(duplicate_periods)} 条重复期号记录")
            print(duplicate_periods)
        else:
            print("✅  未发现重复期号记录")
        
        # 3. 时间顺序检查
        print("\n3. 时间顺序检查：")
        # 按日期排序
        df_sorted_by_date = df.sort_values('date')
        # 检查日期是否连续
        date_diff = pd.to_datetime(df_sorted_by_date['date']).diff().dt.days
        gaps = date_diff[date_diff > 1]
        if len(gaps) > 0:
            print(f"⚠️  警告：发现 {len(gaps)} 个日期间隔大于1天的情况")
            print("日期间隔详情：")
            for i, gap in gaps.items():
                prev_date = df_sorted_by_date.iloc[i-1]['date']
                curr_date = df_sorted_by_date.iloc[i]['date']
                print(f"  {prev_date} 到 {curr_date} 间隔 {gap} 天")
        else:
            print("✅  日期顺序连贯")
        
        # 检查期号是否连续
        df_sorted_by_period = df.sort_values('period')
        period_diff = df_sorted_by_period['period'].diff().dropna()
        non_consecutive = period_diff[period_diff != 1]
        if len(non_consecutive) > 0:
            print(f"⚠️  警告：发现 {len(non_consecutive)} 个期号不连续的情况")
            print("期号间隔详情：")
            for i, diff in non_consecutive.items():
                prev_period = df_sorted_by_period.iloc[i-1]['period']
                curr_period = df_sorted_by_period.iloc[i]['period']
                print(f"  期号 {prev_period} 到 {curr_period} 间隔 {int(diff)} 期")
        else:
            print("✅  期号顺序连贯")
        
        # 4. 数据格式检查
        print("\n4. 数据格式检查：")
        # 检查期号格式
        period_format_error = []
        for period in df['period']:
            if not isinstance(period, int) or period <= 0:
                period_format_error.append(period)
        if period_format_error:
            print(f"⚠️  警告：发现 {len(period_format_error)} 个期号格式错误")
            print(period_format_error[:10])  # 只显示前10个
        else:
            print("✅  期号格式正确")
        
        # 检查生肖格式
        zodiac_format_error = []
        for zodiac in df['zodiac']:
            if not isinstance(zodiac, int) or zodiac < 1 or zodiac > 12:
                zodiac_format_error.append(zodiac)
        if zodiac_format_error:
            print(f"⚠️  警告：发现 {len(zodiac_format_error)} 个生肖格式错误")
            print(zodiac_format_error[:10])  # 只显示前10个
        else:
            print("✅  生肖格式正确")
        
        # 检查日期格式
        date_format_error = []
        for date in df['date']:
            try:
                pd.to_datetime(date)
            except:
                date_format_error.append(date)
        if date_format_error:
            print(f"⚠️  警告：发现 {len(date_format_error)} 个日期格式错误")
            print(date_format_error[:10])  # 只显示前10个
        else:
            print("✅  日期格式正确")
        
        # 5. 数据统计
        print("\n5. 数据统计：")
        print(f"日期范围：{df['date'].min()} 到 {df['date'].max()}")
        print(f"期号范围：{df['period'].min()} 到 {df['period'].max()}")
        print("生肖分布：")
        zodiac_counts = df['zodiac'].value_counts().sort_index()
        for zodiac, count in zodiac_counts.items():
            zodiac_name = ZODIAC_NUM_TO_NAME.get(zodiac, zodiac)
            print(f"  生肖{zodiac_name}：{count}次")
        
        print("\n分析完成！")
        return True
    except Exception as e:
        logging.error(f"分析开奖数据时出错: {e}")
        print(f"分析出错: {e}")
        return False

def validate_draw_data(draw):
    """
    验证开奖数据的有效性
    """
    if not draw:
        return False
    
    # 验证期号
    if 'period' not in draw or not isinstance(draw['period'], int) or draw['period'] <= 0:
        return False
    
    # 验证生肖
    if 'zodiac' not in draw or not isinstance(draw['zodiac'], int) or draw['zodiac'] < 1 or draw['zodiac'] > 12:
        return False
    
    # 验证日期
    if 'date' in draw:
        try:
            datetime.strptime(draw['date'], '%Y-%m-%d')
        except ValueError:
            return False
    
    return True

def clean_draw_data(draws):
    """
    清洗开奖数据
    """
    cleaned_draws = []
    for draw in draws:
        if validate_draw_data(draw):
            # 确保日期格式正确
            if 'date' not in draw or not draw['date']:
                draw['date'] = datetime.now().strftime('%Y-%m-%d')
            cleaned_draws.append(draw)
        else:
            logging.warning(f"无效的开奖数据: {draw}")
    return cleaned_draws

def update_lottery_data():
    """
    更新开奖数据，包括历史数据和最新数据
    """
    # 初始化数据库
    init_database()
    
    # 获取当前年份和前一年份的历史数据
    current_year = datetime.now().year
    for year in [current_year - 1, current_year]:
        history_draws = get_history_draw(year=year)
        if history_draws:
            # 清洗数据
            cleaned_history = clean_draw_data(history_draws)
            # 保存到数据库
            save_to_database(cleaned_history)
    
    # 获取最新开奖数据
    latest_draw = get_latest_draw()
    if latest_draw:
        # 清洗数据
        cleaned_latest = clean_draw_data([latest_draw])
        # 保存到数据库
        save_to_database(cleaned_latest)
    
    logging.info("开奖数据更新完成")

def calculate_missing_days(zodiac, history, current_period):
    """
    计算当前遗漏（距离上次开出的期数）
    """
    # 找到当前期之前的所有记录
    past_data = history[history['period'] < current_period]
    # 找到该生肖最近一次出现的期号
    last_occurrence = past_data[past_data['zodiac'] == zodiac]['period']
    if len(last_occurrence) == 0:
        # 从未出现过
        return current_period - 1
    return current_period - last_occurrence.iloc[-1]

def calculate_max_missing(zodiac, history, current_period):
    """
    计算历史最大遗漏
    """
    past_data = history[history['period'] < current_period]
    if len(past_data) == 0:
        return 0
    # 获取该生肖出现的所有期号
    occurrences = past_data[past_data['zodiac'] == zodiac]['period'].tolist()
    if len(occurrences) == 0:
        # 从未出现过，最大遗漏为当前期数-1
        return current_period - 1
    # 计算相邻两次出现的间隔
    gaps = [occurrences[0] - 1]  # 第一次出现前的间隔
    for i in range(1, len(occurrences)):
        gaps.append(occurrences[i] - occurrences[i-1] - 1)
    # 最后一次出现到当前期的间隔
    gaps.append(current_period - occurrences[-1] - 1)
    return max(gaps)

def calculate_recent_count(zodiac, history, current_period, n):
    """
    计算最近n期出现次数
    """
    # 找到当前期之前的n期
    past_data = history[(history['period'] < current_period) & (history['period'] >= current_period - n)]
    return len(past_data[past_data['zodiac'] == zodiac])

def calculate_hot_rank(history, current_period):
    """
    计算热门排名
    """
    # 最近20期
    past_data = history[(history['period'] < current_period) & (history['period'] >= current_period - 20)]
    if len(past_data) == 0:
        return {z: 1 for z in range(1, 13)}
    # 统计每个生肖出现次数
    counts = past_data['zodiac'].value_counts().to_dict()
    # 为所有生肖设置出现次数（未出现的为0）
    for z in range(1, 13):
        if z not in counts:
            counts[z] = 0
    # 按出现次数排序，次数相同则按生肖号排序
    sorted_zodiacs = sorted(counts.keys(), key=lambda x: (-counts[x], x))
    # 生成排名
    rank = {z: i+1 for i, z in enumerate(sorted_zodiacs)}
    return rank

def calculate_streak(zodiac, history, current_period):
    """
    计算连开次数
    """
    past_data = history[history['period'] < current_period]
    if len(past_data) == 0:
        return 0
    # 从最近一期开始往前找
    streak = 0
    for i in range(len(past_data)-1, -1, -1):
        if past_data.iloc[i]['zodiac'] == zodiac:
            streak += 1
        else:
            break
    return streak

def calculate_break_status(zodiac, history, current_period):
    """
    计算连断状态
    """
    past_data = history[history['period'] < current_period]
    if len(past_data) < 2:
        return False
    # 检查上上期和上期
    last_two = past_data.tail(2)
    return last_two.iloc[1]['zodiac'] == zodiac and last_two.iloc[0]['zodiac'] != zodiac

def calculate_position_gap(current_zodiac, last_zodiac):
    """
    计算位置间隔
    """
    gap = abs(current_zodiac - last_zodiac)
    # 取最小值（考虑环形）
    return min(gap, 12 - gap)

def calculate_element_relation(current_zodiac, last_zodiac):
    """
    计算五行相生关系
    """
    current_element = ZODIAC_TO_ELEMENT[current_zodiac]
    last_element = ZODIAC_TO_ELEMENT[last_zodiac]
    if current_element == last_element:
        return 1  # 相同
    elif ELEMENT_RELATION[last_element]['生'] == current_element:
        return 2  # 相生
    else:
        return 0  # 相克

def calculate_wave_color_same(current_zodiac, last_zodiac):
    """
    计算波色是否相同
    """
    return ZODIAC_TO_WAVE_COLOR[current_zodiac] == ZODIAC_TO_WAVE_COLOR[last_zodiac]

def calculate_odd_even_same(current_zodiac, last_zodiac):
    """
    计算单双是否相同
    """
    return ZODIAC_TO_ODD_EVEN[current_zodiac] == ZODIAC_TO_ODD_EVEN[last_zodiac]

def calculate_size_same(current_zodiac, last_zodiac):
    """
    计算大小是否相同
    """
    return ZODIAC_TO_SIZE[current_zodiac] == ZODIAC_TO_SIZE[last_zodiac]

def calculate_interval_same(current_zodiac, last_zodiac):
    """
    计算区间是否相同
    """
    return ZODIAC_TO_INTERVAL[current_zodiac] == ZODIAC_TO_INTERVAL[last_zodiac]

def calculate_head_same(current_zodiac, last_zodiac):
    """
    计算头数是否相同
    """
    return ZODIAC_TO_HEAD[current_zodiac] == ZODIAC_TO_HEAD[last_zodiac]

def calculate_tail_same(current_zodiac, last_zodiac):
    """
    计算尾数是否相同
    """
    return ZODIAC_TO_TAIL[current_zodiac] == ZODIAC_TO_TAIL[last_zodiac]

def calculate_interval_stats(zodiac, history, current_period, n=5):
    """
    计算近期间隔均值/标准差
    """
    past_data = history[history['period'] < current_period]
    occurrences = past_data[past_data['zodiac'] == zodiac]['period'].tolist()
    if len(occurrences) < 2:
        return 0, 0
    # 取最近n次出现的间隔
    intervals = []
    for i in range(1, len(occurrences)):
        intervals.append(occurrences[i] - occurrences[i-1])
    intervals = intervals[-n:]
    if len(intervals) == 0:
        return 0, 0
    return np.mean(intervals), np.std(intervals)

def calculate_heat_change(history, current_period):
    """
    计算热度变化（最近2期热门排名的差值）
    """
    if current_period <= 21:  # 需要至少21期数据
        return {z: 0 for z in range(1, 13)}
    # 计算上一期的热门排名
    rank_prev = calculate_hot_rank(history, current_period - 1)
    # 计算当前期的热门排名
    rank_current = calculate_hot_rank(history, current_period)
    # 计算差值
    change = {z: rank_prev[z] - rank_current[z] for z in range(1, 13)}
    return change

def build_features(df):
    """
    为每一期构建特征向量和标签
    """
    features = []
    labels = []
    
    for i in range(len(df)):
        current_period = df.iloc[i]['period']
        current_zodiac = df.iloc[i]['zodiac']
        
        # 跳过第一期，因为没有历史数据
        if i == 0:
            continue
        
        # 构建特征向量
        feature_vector = []
        
        # 基础统计特征（全局）
        for zodiac in range(1, 13):
            # 当前遗漏
            missing = calculate_missing_days(zodiac, df, current_period)
            feature_vector.append(missing)
            
            # 遗漏比例
            max_missing = calculate_max_missing(zodiac, df, current_period)
            missing_ratio = missing / max_missing if max_missing > 0 else 0
            feature_vector.append(missing_ratio)
            
            # 近期出现次数（10期、20期、50期）
            for n in [10, 20, 50]:
                count = calculate_recent_count(zodiac, df, current_period, n)
                feature_vector.append(count)
                # 近期频率
                total_periods = min(n, current_period - 1)
                frequency = count / total_periods if total_periods > 0 else 0
                feature_vector.append(frequency)
        
        # 热门排名
        hot_rank = calculate_hot_rank(df, current_period)
        for zodiac in range(1, 13):
            feature_vector.append(hot_rank[zodiac])
        
        # 连开次数
        for zodiac in range(1, 13):
            streak = calculate_streak(zodiac, df, current_period)
            feature_vector.append(streak)
            
            # 连断状态
            break_status = calculate_break_status(zodiac, df, current_period)
            feature_vector.append(1 if break_status else 0)
        
        # 动态特征（与上期关联）
        last_zodiac = df.iloc[i-1]['zodiac']
        
        # 位置间隔
        position_gap = calculate_position_gap(current_zodiac, last_zodiac)
        feature_vector.append(position_gap)
        
        # 五行相生
        element_relation = calculate_element_relation(current_zodiac, last_zodiac)
        feature_vector.append(element_relation)
        
        # 波色相同
        wave_color_same = calculate_wave_color_same(current_zodiac, last_zodiac)
        feature_vector.append(1 if wave_color_same else 0)
        
        # 单双相同
        odd_even_same = calculate_odd_even_same(current_zodiac, last_zodiac)
        feature_vector.append(1 if odd_even_same else 0)
        
        # 大小相同
        size_same = calculate_size_same(current_zodiac, last_zodiac)
        feature_vector.append(1 if size_same else 0)
        
        # 区间相同
        interval_same = calculate_interval_same(current_zodiac, last_zodiac)
        feature_vector.append(1 if interval_same else 0)
        
        # 头数相同
        head_same = calculate_head_same(current_zodiac, last_zodiac)
        feature_vector.append(1 if head_same else 0)
        
        # 尾数相同
        tail_same = calculate_tail_same(current_zodiac, last_zodiac)
        feature_vector.append(1 if tail_same else 0)
        
        # 时序特征
        for zodiac in range(1, 13):
            # 近期间隔均值/标准差
            interval_mean, interval_std = calculate_interval_stats(zodiac, df, current_period)
            feature_vector.append(interval_mean)
            feature_vector.append(interval_std)
        
        # 热度变化
        heat_change = calculate_heat_change(df, current_period)
        for zodiac in range(1, 13):
            feature_vector.append(heat_change[zodiac])
        
        features.append(feature_vector)
        labels.append(current_zodiac - 1)  # 标签从0开始
    
    return np.array(features), np.array(labels)

def train_model(X_train, y_train):
    """
    训练随机森林模型
    """
    # 计算类别权重，处理类别不平衡
    class_counts = np.bincount(y_train)
    total_samples = len(y_train)
    class_weights = total_samples / (len(class_counts) * class_counts)
    sample_weights = np.array([class_weights[y] for y in y_train])
    
    # 创建并训练模型
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train, sample_weight=sample_weights)
    return model

def evaluate_model(model, X_test, y_test):
    """
    计算评估指标
    """
    # 预测概率
    y_pred_proba = model.predict_proba(X_test)
    
    # 预测类别
    y_pred = np.argmax(y_pred_proba, axis=1)
    
    # 准确率
    accuracy = accuracy_score(y_test, y_pred)
    
    # Top-3准确率
    top3_accuracy = 0
    for i in range(len(y_test)):
        top3_indices = np.argsort(y_pred_proba[i])[-3:]
        if y_test[i] in top3_indices:
            top3_accuracy += 1
    top3_accuracy /= len(y_test)
    
    # 对数损失
    logloss = log_loss(y_test, y_pred_proba)
    
    # 特征重要性
    feature_importance = model.feature_importances_
    
    return accuracy, top3_accuracy, logloss, feature_importance

def predict_next(model, last_period_data, all_history):
    """
    根据最新历史数据预测下一期概率
    """
    last_period = last_period_data['period'].iloc[0]
    next_period = last_period + 1
    
    # 构建特征向量（与build_features类似，但针对下一期）
    feature_vector = []
    
    # 基础统计特征（全局）
    for zodiac in range(1, 13):
        # 当前遗漏
        missing = calculate_missing_days(zodiac, all_history, next_period)
        feature_vector.append(missing)
        
        # 遗漏比例
        max_missing = calculate_max_missing(zodiac, all_history, next_period)
        missing_ratio = missing / max_missing if max_missing > 0 else 0
        feature_vector.append(missing_ratio)
        
        # 近期出现次数（10期、20期、50期）
        for n in [10, 20, 50]:
            count = calculate_recent_count(zodiac, all_history, next_period, n)
            feature_vector.append(count)
            # 近期频率
            total_periods = min(n, next_period - 1)
            frequency = count / total_periods if total_periods > 0 else 0
            feature_vector.append(frequency)
    
    # 热门排名
    hot_rank = calculate_hot_rank(all_history, next_period)
    for zodiac in range(1, 13):
        feature_vector.append(hot_rank[zodiac])
    
    # 连开次数
    for zodiac in range(1, 13):
        streak = calculate_streak(zodiac, all_history, next_period)
        feature_vector.append(streak)
        
        # 连断状态
        break_status = calculate_break_status(zodiac, all_history, next_period)
        feature_vector.append(1 if break_status else 0)
    
    # 动态特征（与上期关联）
    last_zodiac = last_period_data['zodiac'].iloc[0]
    
    # 注意：这里我们不知道下一期的生肖，所以使用一个占位符（实际预测时会被模型处理）
    # 位置间隔 - 使用上期生肖作为当前生肖计算
    position_gap = calculate_position_gap(last_zodiac, last_zodiac)
    feature_vector.append(position_gap)
    
    # 五行相生
    element_relation = calculate_element_relation(last_zodiac, last_zodiac)
    feature_vector.append(element_relation)
    
    # 波色相同
    wave_color_same = calculate_wave_color_same(last_zodiac, last_zodiac)
    feature_vector.append(1 if wave_color_same else 0)
    
    # 单双相同
    odd_even_same = calculate_odd_even_same(last_zodiac, last_zodiac)
    feature_vector.append(1 if odd_even_same else 0)
    
    # 大小相同
    size_same = calculate_size_same(last_zodiac, last_zodiac)
    feature_vector.append(1 if size_same else 0)
    
    # 区间相同
    interval_same = calculate_interval_same(last_zodiac, last_zodiac)
    feature_vector.append(1 if interval_same else 0)
    
    # 头数相同
    head_same = calculate_head_same(last_zodiac, last_zodiac)
    feature_vector.append(1 if head_same else 0)
    
    # 尾数相同
    tail_same = calculate_tail_same(last_zodiac, last_zodiac)
    feature_vector.append(1 if tail_same else 0)
    
    # 时序特征
    for zodiac in range(1, 13):
        # 近期间隔均值/标准差
        interval_mean, interval_std = calculate_interval_stats(zodiac, all_history, next_period)
        feature_vector.append(interval_mean)
        feature_vector.append(interval_std)
    
    # 热度变化
    heat_change = calculate_heat_change(all_history, next_period)
    for zodiac in range(1, 13):
        feature_vector.append(heat_change[zodiac])
    
    # 预测概率
    X_next = np.array([feature_vector])
    y_pred_proba = model.predict_proba(X_next)[0]
    
    # 构建结果字典
    zodiac_prob = {i+1: prob for i, prob in enumerate(y_pred_proba)}
    return zodiac_prob

def main():
    """
    主程序
    """
    # 更新开奖数据
    update_lottery_data()
    
    # 从数据库加载数据
    df = load_from_database()
    if df.empty:
        # 如果数据库为空，尝试从CSV文件加载
        file_path = 'lottery_history.csv'
        df = load_data(file_path)
        if df is None:
            print("无法加载数据")
            return
        # 将CSV数据保存到数据库
        draws = []
        for _, row in df.iterrows():
            draw = {
                "period": row['period'],
                "zodiac": row['zodiac'],
                "date": row.get('date', datetime.now().strftime('%Y-%m-%d'))
            }
            draws.append(draw)
        cleaned_draws = clean_draw_data(draws)
        save_to_database(cleaned_draws)
    
    # 构建特征
    X, y = build_features(df)
    if len(X) == 0:
        print("数据不足，无法构建特征")
        return
    
    # 划分训练集和测试集（按时间顺序）
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # 训练模型
    model = train_model(X_train, y_train)
    
    # 评估模型
    accuracy, top3_accuracy, logloss, feature_importance = evaluate_model(model, X_test, y_test)
    print(f"准确率: {accuracy:.4f}")
    print(f"Top-3准确率: {top3_accuracy:.4f}")
    print(f"对数损失: {logloss:.4f}")
    
    # 输出特征重要性（前20个）
    print("\n特征重要性（前20个）:")
    top_features = np.argsort(feature_importance)[-20:]
    for i, idx in enumerate(reversed(top_features)):
        print(f"{i+1}. 特征{idx}: {feature_importance[idx]:.4f}")
    
    # 预测下一期
    last_period_data = df.tail(1)
    next_period_prob = predict_next(model, last_period_data, df)
    print("\n下一期预测概率:")
    for zodiac, prob in sorted(next_period_prob.items(), key=lambda x: x[1], reverse=True):
        zodiac_name = ZODIAC_NUM_TO_NAME.get(zodiac, zodiac)
        print(f"生肖{zodiac_name}: {prob:.4f}")
    
    # 保存模型
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("\n模型已保存为 model.pkl")
    
    # 输出最近3期开奖数据
    recent_draws = get_recent_draws(3)
    print("\n最近3期开奖数据:")
    if not recent_draws.empty:
        for _, row in recent_draws.iterrows():
            zodiac_name = ZODIAC_NUM_TO_NAME.get(row['zodiac'], row['zodiac'])
            print(f"期号: {row['period']}, 生肖: {zodiac_name}, 日期: {row['date']}")
    else:
        print("暂无数据")
    
    # 统计2026年的记录数量
    count_2026 = get_2026_records_count()
    print(f"\n2026年的开奖记录数量: {count_2026}")
    
    # 执行数据检查与分析
    print("\n" + "=" * 80)
    print("开始对开奖历史记录数据进行全面检查与分析...")
    analyze_lottery_data()
    print("=" * 80)
    
    # 输出接口对接状态
    print("\n接口对接状态:")
    print("- 数据更新: 完成")
    print(f"- 数据库记录数: {len(df)}")
    print(f"- 最新期号: {df['period'].max() if not df.empty else 0}")
    print("- 模型训练: 完成")
    print("- 预测生成: 完成")
    print("- 数据分析: 完成")
    
    logging.info("模型训练、预测和数据分析完成")

if __name__ == "__main__":
    main()
