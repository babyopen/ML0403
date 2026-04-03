import pandas as pd
import sqlite3
import pickle
from sklearn.ensemble import RandomForestClassifier

def get_data():
    conn = sqlite3.connect('lottery.db')
    df = pd.read_sql_query('SELECT * FROM lottery_history ORDER BY period', conn)
    conn.close()
    return df

def build_features(df):
    features = []
    labels = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        zodiac = row['zodiac']
        
        past_data = df.iloc[:i+1]
        
        current_features = []
        
        for z in range(1, 13):
            mask = past_data['zodiac'] == z
            if not mask.any():
                current_features.extend([100, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
            else:
                last_appearances = past_data[mask].index.tolist()
                last_idx = last_appearances[-1]
                current_missing = i - last_idx
                
                max_missing = len(past_data)
                missing_ratio = current_missing / max_missing if max_missing > 0 else 0
                
                recent_10 = past_data.tail(10)
                recent_20 = past_data.tail(20)
                recent_50 = past_data.tail(50)
                
                count_10 = (recent_10['zodiac'] == z).sum()
                count_20 = (recent_20['zodiac'] == z).sum()
                count_50 = (recent_50['zodiac'] == z).sum()
                
                freq_10 = count_10 / len(recent_10) if len(recent_10) > 0 else 0
                freq_20 = count_20 / len(recent_20) if len(recent_20) > 0 else 0
                freq_50 = count_50 / len(recent_50) if len(recent_50) > 0 else 0
                
                # 连开次数
                consecutive = 0
                j = i
                while j >= 0 and past_data.iloc[j]['zodiac'] == z:
                    consecutive += 1
                    j -= 1
                
                # 连断状态
                break_state = False
                if i > 0 and past_data.iloc[i]['zodiac'] == z and past_data.iloc[i-1]['zodiac'] != z:
                    break_state = True
                
                current_features.extend([
                    current_missing,
                    missing_ratio,
                    count_10,
                    count_20,
                    count_50,
                    freq_10,
                    freq_20,
                    freq_50,
                    consecutive,
                    1 if break_state else 0,
                    0,  # 位置间隔
                    0,  # 五行相生
                    0,  # 波色相同
                    0,  # 单双相同
                    0   # 大小相同
                ])
        
        # 添加动态特征
        if i > 0:
            prev_zodiac = past_data.iloc[i-1]['zodiac']
            pos_diff = abs(zodiac - prev_zodiac)
            
            # 五行相生
            elements = ['水', '土', '木', '木', '土', '火', '火', '土', '金', '金', '土', '水']
            element_prev = elements[prev_zodiac - 1]
            element_curr = elements[zodiac - 1]
            
            generate_map = {
                ('木', '火'): 2, ('火', '土'): 2, ('土', '金'): 2, ('金', '水'): 2, ('水', '木'): 2,
                ('火', '木'): 0, ('土', '火'): 0, ('金', '土'): 0, ('水', '金'): 0, ('木', '水'): 0
            }
            generate = 1  # 相同
            if (element_prev, element_curr) in generate_map:
                generate = generate_map[(element_prev, element_curr)]
            
            # 波色相同
            colors = ['红', '绿', '蓝', '绿', '红', '蓝', '红', '绿', '蓝', '红', '绿', '蓝']
            color_prev = colors[prev_zodiac - 1]
            color_curr = colors[zodiac - 1]
            color_same = 1 if color_prev == color_curr else 0
            
            # 单双相同
            odd_prev = 1 if prev_zodiac % 2 == 1 else 0
            odd_curr = 1 if zodiac % 2 == 1 else 0
            odd_same = 1 if odd_prev == odd_curr else 0
            
            # 大小相同
            big_prev = 1 if prev_zodiac > 6 else 0
            big_curr = 1 if zodiac > 6 else 0
            big_same = 1 if big_prev == big_curr else 0
            
            current_features.extend([pos_diff, generate, color_same, odd_same, big_same])
        else:
            current_features.extend([0, 0, 0, 0, 0])
        
        features.append(current_features)
        labels.append(zodiac)
    
    return features, labels

def main():
    print("加载数据...")
    df = get_data()
    print(f"数据加载完成，共 {len(df)} 条记录")
    
    print("构建特征...")
    X, y = build_features(df)
    print(f"特征构建完成，特征数量: {len(X[0])}")
    
    print("训练模型...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    print("模型训练完成")
    
    print("保存模型...")
    with open('model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("模型保存完成")
    print(f"特征数量: {len(X[0])}")

if __name__ == '__main__':
    main()
