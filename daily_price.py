import efinance as ef
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import ticker
import matplotlib.font_manager as fm
from datetime import datetime

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 将 market_type 参数从字符串 'A_stock' 修改为正确的枚举值
# 修改end参数使其始终等于当天日期
end_date = datetime.now().strftime('%Y%m%d')
kline_dict = ef.stock.get_quote_history(stock_codes='002594', beg='20240101', end=end_date, klt=101, fqt=1, market_type=None, suppress_error=False, use_id_cache=True)

df = pd.DataFrame(kline_dict)
print(df)

# 导出为Excel文件
df.to_excel('比亚迪2024年至今股价.xlsx', index=False)
print("数据已导出到 比亚迪2024年至今股价.xlsx 文件")

# 读取Excel文件数据
data = pd.read_excel('比亚迪2024年至今股价.xlsx')

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
# 2024年3月27日标注：净利润300.41亿
mar_27_date = pd.to_datetime('2024-03-27')
mar_27_data = data[data['日期'] == mar_27_date]
if not mar_27_data.empty:
    mar_27_close = mar_27_data['收盘'].values[0]
    ax1.annotate('净利润300.41亿', 
                xy=(mar_27_date, mar_27_close),
                xytext=(mar_27_date, mar_27_close + 10),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2024年4月30日标注：净利润45.69亿
apr_30_date = pd.to_datetime('2024-04-30')
apr_30_data = data[data['日期'] == apr_30_date]
if not apr_30_data.empty:
    apr_30_close = apr_30_data['收盘'].values[0]
    ax1.annotate('净利润45.69亿', 
                xy=(apr_30_date, apr_30_close),
                xytext=(apr_30_date, apr_30_close + 10),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2024年8月29日标注：净利润136.31亿
aug_29_date = pd.to_datetime('2024-08-29')
aug_29_data = data[data['日期'] == aug_29_date]
if not aug_29_data.empty:
    aug_29_close = aug_29_data['收盘'].values[0]
    ax1.annotate('净利润136.31亿', 
                xy=(aug_29_date, aug_29_close),
                xytext=(aug_29_date, aug_29_close + 10),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2025年3月25日标注：净利润402.54亿
mar_25_2025_date = pd.to_datetime('2025-03-25')
mar_25_2025_data = data[data['日期'] == mar_25_2025_date]
if not mar_25_2025_data.empty:
    mar_25_2025_close = mar_25_2025_data['收盘'].values[0]
    ax1.annotate('净利润402.54亿', 
                xy=(mar_25_2025_date, mar_25_2025_close),
                xytext=(mar_25_2025_date, mar_25_2025_close + 10),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2025年4月26日标注：净利润91.55亿
apr_26_2025_date = pd.to_datetime('2025-04-26')
# 查找下一个最近的交易日
actual_apr_26_date = find_next_trading_date(apr_26_2025_date, data)
apr_26_2025_data = data[data['日期'] == actual_apr_26_date]
if not apr_26_2025_data.empty:
    apr_26_2025_close = apr_26_2025_data['收盘'].values[0]
    ax1.annotate('净利润91.55亿', 
                xy=(actual_apr_26_date, apr_26_2025_close),
                xytext=(actual_apr_26_date, apr_26_2025_close + 10),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

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
# 2024年3月27日标注：净利润300.41亿
if not mar_27_data.empty:
    mar_27_change = mar_27_data['涨跌幅'].values[0]
    ax2.annotate('净利润300.41亿', 
                xy=(mar_27_date, mar_27_change),
                xytext=(mar_27_date, mar_27_change + 2),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2024年4月30日标注：净利润45.69亿
if not apr_30_data.empty:
    apr_30_change = apr_30_data['涨跌幅'].values[0]
    ax2.annotate('净利润45.69亿', 
                xy=(apr_30_date, apr_30_change),
                xytext=(apr_30_date, apr_30_change + 2),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2024年8月29日标注：净利润136.31亿
if not aug_29_data.empty:
    aug_29_change = aug_29_data['涨跌幅'].values[0]
    ax2.annotate('净利润136.31亿', 
                xy=(aug_29_date, aug_29_change),
                xytext=(aug_29_date, aug_29_change + 2),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2025年3月25日标注：净利润402.54亿
if not mar_25_2025_data.empty:
    mar_25_2025_change = mar_25_2025_data['涨跌幅'].values[0]
    ax2.annotate('净利润402.54亿', 
                xy=(mar_25_2025_date, mar_25_2025_change),
                xytext=(mar_25_2025_date, mar_25_2025_change + 2),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 2025年4月26日标注：净利润91.55亿
# 使用实际的交易日日期
if not apr_26_2025_data.empty:
    apr_26_2025_change = apr_26_2025_data['涨跌幅'].values[0]
    ax2.annotate('净利润91.55亿', 
                xy=(actual_apr_26_date, apr_26_2025_change),
                xytext=(actual_apr_26_date, apr_26_2025_change + 2),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10,
                ha='center')

# 自动调整布局
plt.tight_layout()

# 显示图表
plt.show()