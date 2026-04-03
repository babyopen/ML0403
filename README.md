# 生肖开奖预测系统

版本号: V0.0.01

## 项目简介

这是一个基于机器学习的生肖开奖预测系统，使用历史开奖数据训练模型，预测下一期的开奖结果。

## 功能特点

- **数据获取**：自动从官方接口获取最新和历史开奖数据
- **特征工程**：构建多种特征（基础统计特征、动态特征、时序特征）
- **模型训练**：使用随机森林分类器进行训练
- **预测功能**：预测下一期的开奖结果，显示置信度和概率分布
- **历史记录**：记录预测历史，支持后续核对和统计
- **前端界面**：现代化的 Web 界面，支持响应式设计

## 技术栈

- **后端**：Python + Flask
- **前端**：HTML5 + CSS3 + JavaScript
- **数据库**：SQLite
- **机器学习**：scikit-learn (RandomForestClassifier)
- **数据处理**：pandas, numpy

## 项目结构

```
ml模型1.0/
├── web_app.py              # Flask 后端应用
├── zodiac_lottery_prediction.py  # 主程序脚本
├── retrain_model.py        # 模型重新训练脚本
├── init_db.py              # 数据库初始化脚本
├── lottery_history.csv     # 示例数据
├── templates/
│   └── index.html          # 前端页面
├── check_2026_data.py      # 数据检查脚本
├── check_all_records.py    # 记录检查脚本
├── clean_duplicate_data.py # 数据清理脚本
└── README.md               # 项目说明
```

## 安装依赖

```bash
pip install flask pandas numpy scikit-learn
```

## 使用方法

### 1. 初始化数据库

```bash
python3 init_db.py
```

### 2. 启动 Web 应用

```bash
python3 web_app.py
```

访问 http://localhost:5003 查看前端界面。

### 3. 重新训练模型

```bash
python3 retrain_model.py
```

### 4. 运行主程序

```bash
python3 zodiac_lottery_prediction.py
```

## API 接口

- `GET /api/latest` - 获取最新开奖数据
- `GET /api/recent/<n>` - 获取最近 n 期开奖数据
- `GET /api/statistics` - 获取预测统计信息
- `POST /api/predict` - 执行预测
- `GET /api/history` - 获取预测历史记录

## 数据来源

- **最新开奖接口**：`https://macaumarksix.com/api/macaujc2.com`
- **历史开奖接口**：`https://history.macaumarksix.com/history/macaujc2/y/${year}`

## 生肖配置

| 生肖 | 对应号码 | 五行 | 波色 |
|------|----------|------|------|
| 鼠 | 7, 19, 31, 43 | 水 | 红 |
| 牛 | 6, 18, 30, 42 | 土 | 绿 |
| 虎 | 5, 17, 29, 41 | 木 | 蓝 |
| 兔 | 4, 16, 28, 40 | 木 | 绿 |
| 龙 | 3, 15, 27, 39 | 土 | 红 |
| 蛇 | 2, 14, 26, 38 | 火 | 蓝 |
| 马 | 1, 13, 25, 37, 49 | 火 | 红 |
| 羊 | 8, 20, 32, 44 | 土 | 绿 |
| 猴 | 9, 21, 33, 45 | 金 | 蓝 |
| 鸡 | 10, 22, 34, 46 | 金 | 红 |
| 狗 | 11, 23, 35, 47 | 土 | 绿 |
| 猪 | 12, 24, 36, 48 | 水 | 蓝 |

## 开发团队

- 项目创建：AI Assistant
- 版本：V0.0.01

## 许可证

MIT License
