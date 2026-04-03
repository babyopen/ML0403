from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
import numpy as np
import pickle
import logging
from datetime import datetime
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = 'lottery.db'
MODEL_PATH = 'model.pkl'

ZODIAC_ALL = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

ZODIAC_NUM_TO_NAME = {
    1: '鼠', 2: '牛', 3: '虎', 4: '兔', 5: '龙', 6: '蛇',
    7: '马', 8: '羊', 9: '猴', 10: '鸡', 11: '狗', 12: '猪'
}

ELEMENT_MAP = {
    '鼠': '水', '牛': '土', '虎': '木', '兔': '木', '龙': '土', '蛇': '火',
    '马': '火', '羊': '土', '猴': '金', '鸡': '金', '狗': '土', '猪': '水'
}

COLOR_MAP = {
    '鼠': '红', '牛': '绿', '虎': '蓝', '兔': '绿', '龙': '红', '蛇': '蓝',
    '马': '红', '羊': '绿', '猴': '蓝', '鸡': '红', '狗': '绿', '猪': '蓝'
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    return None

def get_latest_draw():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lottery_history ORDER BY period DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        zodiac_num = row['zodiac']
        zodiac_name = ZODIAC_NUM_TO_NAME.get(zodiac_num, str(zodiac_num))
        return {
            'period': row['period'],
            'zodiac': zodiac_name,
            'zodiac_num': zodiac_num,
            'date': row['date'],
            'element': ELEMENT_MAP.get(zodiac_name, ''),
            'color': COLOR_MAP.get(zodiac_name, '')
        }
    return None

def get_recent_draws(n=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lottery_history ORDER BY period DESC LIMIT ?', (n,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        zodiac_num = row['zodiac']
        zodiac_name = ZODIAC_NUM_TO_NAME.get(zodiac_num, str(zodiac_num))
        results.append({
            'period': row['period'],
            'zodiac': zodiac_name,
            'zodiac_num': zodiac_num,
            'date': row['date'],
            'element': ELEMENT_MAP.get(zodiac_name, ''),
            'color': COLOR_MAP.get(zodiac_name, '')
        })
    return results

def get_prediction_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM predictions ORDER BY created_at DESC LIMIT 20')
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'period': row['period'],
            'prediction': row['prediction'],
            'result': row['result'],
            'status': row['status'],
            'created_at': row['created_at']
        })
    return results

def save_prediction(period, prediction, result=None, status='pending'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (period, prediction, result, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (period, prediction, result, status, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_prediction_result(prediction_id, result, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE predictions
        SET result = ?, status = ?
        WHERE id = ?
    ''', (result, status, prediction_id))
    conn.commit()
    conn.close()

def get_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM predictions')
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as checked FROM predictions WHERE status != 'pending'")
    checked = cursor.fetchone()['checked']
    
    cursor.execute("SELECT COUNT(*) as correct FROM predictions WHERE status = 'correct'")
    correct = cursor.fetchone()['correct']
    
    conn.close()
    
    accuracy = (correct / checked * 100) if checked > 0 else 0
    
    return {
        'total': total,
        'checked': checked,
        'correct': correct,
        'accuracy': accuracy
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/latest')
def api_latest():
    try:
        latest = get_latest_draw()
        if latest:
            return jsonify({'success': True, 'data': latest})
        return jsonify({'success': False, 'error': 'No data available'})
    except Exception as e:
        logger.error(f"Error getting latest draw: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recent/<int:n>')
def api_recent(n=10):
    try:
        recent = get_recent_draws(n)
        return jsonify({'success': True, 'data': recent})
    except Exception as e:
        logger.error(f"Error getting recent draws: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/statistics')
def api_statistics():
    try:
        stats = get_statistics()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        model = load_model()
        if model is None:
            return jsonify({'success': False, 'error': 'Model not loaded'})
        
        latest = get_latest_draw()
        if latest is None:
            return jsonify({'success': False, 'error': 'No latest draw data'})
        
        conn = get_db_connection()
        df = pd.read_sql_query('SELECT * FROM lottery_history ORDER BY period', conn)
        conn.close()
        
        if len(df) < 50:
            return jsonify({'success': False, 'error': 'Insufficient data for prediction'})
        
        features = build_features(df)
        last_features = [features[-1]]
        
        proba = model.predict_proba(last_features)[0]
        
        zodiac_probs = []
        for i, prob in enumerate(proba):
            zodiac_num = i + 1
            zodiac_name = ZODIAC_NUM_TO_NAME.get(zodiac_num, str(zodiac_num))
            zodiac_probs.append({
                'zodiac_num': zodiac_num,
                'zodiac_name': zodiac_name,
                'probability': float(prob),
                'element': ELEMENT_MAP.get(zodiac_name, ''),
                'color': COLOR_MAP.get(zodiac_name, '')
            })
        
        zodiac_probs.sort(key=lambda x: x['probability'], reverse=True)
        
        top3 = zodiac_probs[:3]
        next_period = latest['period'] + 1
        
        prediction_text = ','.join([z['zodiac_name'] for z in top3])
        save_prediction(next_period, prediction_text)
        
        confidence = top3[0]['probability'] * 100
        
        analysis = [
            f"{top3[0]['zodiac_name']} 的预测概率为 {top3[0]['probability']*100:.2f}%，在所有生肖中排名最高",
            f"与第二名 {top3[1]['zodiac_name']} 的概率差距为 {(top3[0]['probability']-top3[1]['probability'])*100:.2f}%",
            f"该生肖五行属{top3[0]['element']}，对应{top3[0]['color']}波",
            "模型基于历史数据统计、时序特征和五行波色关联进行预测"
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'prediction': {
                    'next_period': next_period,
                    'confidence': confidence,
                    'recommended': top3[0],
                    'top3': top3,
                    'all': zodiac_probs,
                    'analysis': analysis
                },
                'timestamp': datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history')
def api_history():
    try:
        history = get_prediction_history()
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        logger.error(f"Error getting prediction history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def build_features(df):
    features = []
    
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
    
    return features

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)