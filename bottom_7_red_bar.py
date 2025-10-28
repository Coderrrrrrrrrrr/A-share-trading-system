import pandas as pd
import os
import re
import pymysql
from sqlalchemy import create_engine
import warnings
import mplfinance.original_flavor as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

warnings.filterwarnings('ignore')

# 数据库连接配置 - 请根据实际情况修改
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'cxtx1028',  # 请修改为实际密码
    'database': 'quant',
    'charset': 'utf8mb4'
}

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def find_consecutive_rising_stocks(check_volume=True):
    """查找连续7天或以上上涨且成交量连续递增的股票"""
    try:
        # 创建数据库连接
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
        
        # 查询所有股票的交易数据（包含成交量）
        query = """
        SELECT stock_name, stock_code, trade_date, change_percent, volume
        FROM stock_data 
        ORDER BY stock_code, trade_date
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("数据库中没有数据")
            return []
        
        # 按股票代码分组处理
        results = []
        for stock_code, group in df.groupby('stock_code'):
            # 按日期排序
            group = group.sort_values('trade_date').reset_index(drop=True)
            
            # 查找连续上涨的天数
            consecutive_days = 0
            max_consecutive_days = 0
            start_date = None
            max_start_date = None
            
            for i in range(len(group)):
                if group.loc[i, 'change_percent'] > 0:  # 上涨
                    if consecutive_days == 0:  # 新的上涨周期开始
                        start_date = group.loc[i, 'trade_date']
                    consecutive_days += 1
                    
                    # 更新最大连续上涨天数和起始日期
                    if consecutive_days > max_consecutive_days:
                        max_consecutive_days = consecutive_days
                        max_start_date = start_date
                else:  # 下跌或持平，重置计数
                    consecutive_days = 0
                    start_date = None
            
            # 如果连续上涨天数大于等于7天
            if max_consecutive_days >= 7:
                # 如果不需要检查成交量，则直接添加到结果中
                if not check_volume:
                    stock_name = group.loc[0, 'stock_name']
                    results.append({
                        'stock_name': stock_name,
                        'stock_code': stock_code,
                        'consecutive_days': max_consecutive_days,
                        'start_date': max_start_date
                    })
                    print(f"股票 {stock_name}({stock_code}) 连续上涨 {max_consecutive_days} 天，起始日期: {max_start_date}")
                else:
                    # 验证成交量是否也连续递增
                    start_idx = None
                    for i, date in enumerate(group['trade_date']):
                        if date == max_start_date:
                            start_idx = i
                            break
                    
                    if start_idx is not None:
                        end_idx = min(start_idx + max_consecutive_days, len(group))
                        # 检查该区间内成交量是否连续递增
                        volume_increasing = True
                        volume_series = group['volume'].iloc[start_idx:end_idx]
                        
                        # 检查成交量是否连续递增（每个值都比前一个值大）
                        for j in range(1, len(volume_series)):
                            if volume_series.iloc[j] <= volume_series.iloc[j-1]:
                                volume_increasing = False
                                break
                        
                        # 只有当成交量也连续递增时才记录结果
                        if volume_increasing and len(volume_series) > 1:  # 确保至少有2天的数据可以比较
                            stock_name = group.loc[0, 'stock_name']
                            results.append({
                                'stock_name': stock_name,
                                'stock_code': stock_code,
                                'consecutive_days': max_consecutive_days,
                                'start_date': max_start_date
                            })
                            print(f"股票 {stock_name}({stock_code}) 连续上涨 {max_consecutive_days} 天且成交量连续递增，起始日期: {max_start_date}")
                        elif len(volume_series) <= 1:
                            stock_name = group.loc[0, 'stock_name']
                            print(f"股票 {stock_name}({stock_code}) 连续上涨 {max_consecutive_days} 天，但上涨区间数据不足，已排除")
                        else:
                            stock_name = group.loc[0, 'stock_name']
                            print(f"股票 {stock_name}({stock_code}) 连续上涨 {max_consecutive_days} 天，但成交量未连续递增，已排除")
        
        return results
    except Exception as e:
        print(f"查找连续上涨股票时出错: {e}")
        return []

def plot_candlestick_chart(stock_name, stock_code, start_date=None, consecutive_days=None):
    """为指定股票绘制蜡烛图，并标注连续上涨区间"""
    try:
        # 创建数据库连接
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
        
        # 查询指定股票的所有历史数据
        query = """
        SELECT trade_date, open_price, high_price, low_price, close_price, volume
        FROM stock_data 
        WHERE stock_code = %s
        ORDER BY trade_date
        """
        df = pd.read_sql(query, engine, params=(stock_code,))
        
        if df.empty:
            print(f"未找到股票 {stock_name}({stock_code}) 的数据")
            return
        
        # 设置日期为索引
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        
        # 重命名列以匹配绘图要求
        df.rename(columns={
            'open_price': 'Open',
            'high_price': 'High',
            'low_price': 'Low',
            'close_price': 'Close',
            'volume': 'Volume'
        }, inplace=True)
        
        # 增加图形尺寸以适应更宽的蜡烛图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={"height_ratios": [3, 1]})
        
        # 准备OHLC数据，需要将日期转换为数字格式
        ohlc_data = []
        date_nums = []
        
        for i in range(len(df)):
            date_num = mdates.date2num(df.index[i])
            date_nums.append(date_num)
            open_price = df['Open'].iloc[i]
            high_price = df['High'].iloc[i]
            low_price = df['Low'].iloc[i]
            close_price = df['Close'].iloc[i]
            ohlc_data.append([date_num, open_price, high_price, low_price, close_price])
        
        # 上层：蜡烛图
        mpf.candlestick_ohlc(
            ax1, 
            ohlc_data,  # 格式：[时间戳, O, H, L, C]
            width=0.6,  # 蜡烛宽度
            colorup="red",  # 上涨（收盘价>开盘价）颜色
            colordown="green",  # 下跌颜色
            alpha=0.8  # 透明度
        )
        
        # 如果提供了连续上涨信息，则绘制虚线框标注
        if start_date is not None and consecutive_days is not None:
            # 找到起始日期在数据中的位置
            start_idx = None
            end_idx = None
            
            # 查找起始日期的索引
            for i, date in enumerate(df.index):
                if date.date() == start_date:
                    start_idx = i
                    break
            
            # 如果找到了起始日期，则计算结束日期的索引
            if start_idx is not None:
                end_idx = min(start_idx + consecutive_days - 1, len(df) - 1)
                
                # 获取这个区间的最高价和最低价用于绘制矩形框
                high_prices = df['High'].iloc[start_idx:end_idx+1]
                low_prices = df['Low'].iloc[start_idx:end_idx+1]
                
                # 绘制虚线框标注连续上涨区间
                start_time = mdates.date2num(df.index[start_idx])
                end_time = mdates.date2num(df.index[end_idx])
                
                # 绘制矩形框 (left, bottom, width, height)
                rect = plt.Rectangle(
                    (start_time, low_prices.min()),
                    end_time - start_time,
                    high_prices.max() - low_prices.min(),
                    linewidth=2,
                    linestyle='--',
                    edgecolor='blue',
                    facecolor='none',
                    label=f'连续上涨{consecutive_days}天'
                )
                ax1.add_patch(rect)
                
                # 添加标注文本
                ax1.text(
                    start_time, 
                    high_prices.max(), 
                    f'连续上涨{consecutive_days}天', 
                    fontsize=10, 
                    color='blue',
                    verticalalignment='bottom'
                )
        
        ax1.set_title("{} 蜡烛图".format(stock_name), fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        # 格式化x轴日期显示
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 10, 20]))  # 只显示每月1号、10号、20号
        
        # 下层：成交量
        ax2.bar(date_nums, df["Volume"], 
                width=0.6, 
                color=df.apply(lambda x: "red" if x.Close > x.Open else "green", axis=1))
        ax2.set_ylabel("Volume", fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 格式化x轴日期显示，与上图保持一致
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 10, 20]))  # 只显示每月1号、10号、20号
        
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"绘制 {stock_name} 蜡烛图时出错: {e}")

def query_examples():
    """查询示例"""
    try:
        # 创建数据库连接
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
        
        print("\n=== 查询示例 ===")
        
        # 检查数据库中是否有数据
        count_query = "SELECT COUNT(*) as total FROM stock_data"
        count_df = pd.read_sql(count_query, engine)
        total_records = count_df['total'].iloc[0]
        print(f"数据库中总共有 {total_records} 条记录")
        
        if total_records == 0:
            print("数据库中没有数据，请先导入数据")
            return
        
        # 示例1: 查询最近5条记录
        print("1. 查询最近的5条记录:")
        query1 = "SELECT * FROM stock_data ORDER BY trade_date DESC, stock_code LIMIT 5"
        df1 = pd.read_sql(query1, engine)
        print(df1.to_string(index=False))
        
        # 示例2: 查询特定日期的所有股票数据（如果有）
        print("\n2. 查询2024-01-01的所有股票数据:")
        query2 = "SELECT * FROM stock_data WHERE trade_date = %s LIMIT 5"
        df2 = pd.read_sql(query2, engine, params=('2024-01-02',))
        if df2.empty:
            print("2024-01-01 没有数据")
        else:
            print(df2.to_string(index=False))
        
        # 示例3: 查询任意一只股票的所有历史数据
        print("\n3. 查询任意一只股票的所有历史数据:")
        # 先查找数据库中存在的股票
        stock_query = "SELECT DISTINCT stock_name, stock_code FROM stock_data LIMIT 1"
        stock_df = pd.read_sql(stock_query, engine)
        if not stock_df.empty:
            stock_name = stock_df['stock_name'].iloc[0]
            print(f"查询股票 {stock_name} 的历史数据:")
            query3 = "SELECT * FROM stock_data WHERE stock_name = %s ORDER BY trade_date LIMIT 5"
            df3 = pd.read_sql(query3, engine, params=(stock_name,))
            print(df3.to_string(index=False))
        else:
            print("数据库中没有股票数据")
    except Exception as e:
        print(f"执行查询示例时出错: {e}")

if __name__ == "__main__":
    # 设置是否启用成交量递增筛选条件
    # True: 启用成交量递增筛选（默认）
    # False: 仅使用连续上涨天数筛选
    ENABLE_VOLUME_CHECK = False
    
    # 查找连续7天或以上上涨的股票
    if ENABLE_VOLUME_CHECK:
        print("查找连续7天或以上上涨且成交量连续递增的股票...")
    else:
        print("查找连续7天或以上上涨的股票...")
        
    rising_stocks = find_consecutive_rising_stocks(check_volume=ENABLE_VOLUME_CHECK)
    
    if rising_stocks:
        print(f"\n找到 {len(rising_stocks)} 只符合条件的股票，开始绘制蜡烛图...")
        # 为每只符合条件的股票绘制蜡烛图
        for stock in rising_stocks:
            print(f"\n正在绘制 {stock['stock_name']}({stock['stock_code']}) 的蜡烛图...")
            plot_candlestick_chart(
                stock['stock_name'], 
                stock['stock_code'],
                stock['start_date'],
                stock['consecutive_days']
            )
    else:
        if ENABLE_VOLUME_CHECK:
            print("\n没有找到连续7天或以上上涨且成交量连续递增的股票")
        else:
            print("\n没有找到连续7天或以上上涨的股票")
    
    # # 显示查询示例
    # query_examples()