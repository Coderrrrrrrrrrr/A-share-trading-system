import efinance as ef
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import ticker
import matplotlib.font_manager as fm

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取Excel文件数据
data = pd.read_excel('比亚迪2024年至今股价.xlsx')

# 读取财务数据
financial_data = pd.read_excel('./company_performance_pivot.xlsx')

# 筛选比亚迪的财务数据（股票代码002594）
byd_financial_data = financial_data[financial_data['股票简称'] == '比亚迪']
if byd_financial_data.empty:
    raise ValueError("未找到股票简称为比亚迪的财务数据")
byd_financial = byd_financial_data.iloc[0]

# 提取净利润数据 - 自动查找所有可用日期
profit_annotations = []

# 获取所有以"净利润_"开头的列名，并提取日期部分
profit_columns = [col for col in byd_financial.index if col.startswith('净利润_')]
for col in profit_columns:
    # 从列名中提取日期（例如从"净利润_2023-12-31"中提取"2023-12-31"）
    date_str = col.split('_', 1)[1]
    announcement_col = f'公告日期_{date_str}'
    
    # 检查数据是否存在且非空
    if (announcement_col in byd_financial and 
        col in byd_financial and 
        not pd.isna(byd_financial.get(announcement_col)) and 
        not pd.isna(byd_financial.get(col))):
        
        profit_annotations.append({
            'date': pd.to_datetime(byd_financial[announcement_col]),
            'profit': byd_financial[col]/100000000,  # 转换为亿元
            'label': f'净利润{byd_financial[col]/100000000:.2f}亿'
        })

# 确保日期列是datetime类型
data['日期'] = pd.to_datetime(data['日期'])

# 创建图形和子图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# 绘制收盘价图表
ax1.plot(data['日期'], data['收盘'], color='red', linewidth=2)
ax1.set_title('比亚迪2024年至今收盘价走势', fontsize=16)
ax1.set_ylabel('收盘价 (元)', fontsize=12)
ax1.grid(True, alpha=0.3)

# 格式化x轴日期显示
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 添加一个函数来查找下一个最近的交易日
def find_next_trading_date(target_date, data):
    """查找下一个最近的交易日"""
    # 筛选大于等于目标日期的数据
    future_data = data[data['日期'] >= target_date]
    if not future_data.empty:
        # 返回最近的交易日
        return future_data.iloc[0]['日期']
    else:
        # 如果没有找到，返回原始日期
        return target_date

# 在收盘价图表上添加注释
for annotation in profit_annotations:
    target_date = annotation['date']
    # 查找下一个最近的交易日
    actual_date = find_next_trading_date(target_date, data)
    trading_data = data[data['日期'] == actual_date]
    if not trading_data.empty:
        close_price = trading_data['收盘'].values[0]
        ax1.annotate(annotation['label'],
                    xy=(actual_date, close_price),
                    xytext=(0, 30),  # 统一偏移量
                    textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', color='black', lw=0.8),
                    fontsize=9,
                    ha='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))


# 绘制涨跌幅图表
ax2.plot(data['日期'], data['涨跌幅'], color='blue', linewidth=2)
ax2.set_title('比亚迪2024年至今涨跌幅', fontsize=16)
ax2.set_xlabel('日期', fontsize=12)
ax2.set_ylabel('涨跌幅 (%)', fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='black', linewidth=0.5)

# 格式化x轴日期显示
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

# 在涨跌幅图表上添加注释
for annotation in profit_annotations:
    target_date = annotation['date']
    # 查找下一个最近的交易日
    actual_date = find_next_trading_date(target_date, data)
    trading_data = data[data['日期'] == actual_date]
    if not trading_data.empty:
        change_percent = trading_data['涨跌幅'].values[0]
        ax2.annotate(annotation['label'],
                    xy=(actual_date, change_percent),
                    xytext=(0, 30),
                    textcoords='offset points',
                    arrowprops=dict(arrowstyle='->', color='black', lw=0.8),
                    fontsize=9,
                    ha='center',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

# 自动调整布局
plt.tight_layout()

# 显示图表
plt.show()