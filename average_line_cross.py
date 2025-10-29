import pandas as pd
import os
import re
import pymysql
from sqlalchemy import create_engine
import warnings
import mplfinance.original_flavor as mpf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
import efinance as ef

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


def get_holder_data(stock_name, data_dir="下载数据"):
    """获取股东人数数据"""
    # 读取股东人数统计文件
    filepath = os.path.join(data_dir, '股东人数统计.xlsx')
    if not os.path.exists(filepath):
        print(f"未找到股东人数统计文件: {filepath}")
        return None
        
    holder_data = pd.read_excel(filepath)
    
    # 筛选指定股票名称的数据
    stock_holder_data = holder_data[holder_data['股票名称'] == stock_name]
    
    if stock_holder_data.empty:
        print(f"未找到股票名称为{stock_name}的股东人数数据")
        return None
        
    # 选择需要的列并重命名
    # 从宽格式转换为长格式，日期作为一列，股东人数作为一列
    holder_df = stock_holder_data.melt(
        id_vars=['股票代码', '股票名称'], 
        var_name='Date', 
        value_name='HolderCount'
    )
    
    # 转换日期格式并设置为索引
    holder_df['Date'] = pd.to_datetime(holder_df['Date'])
    holder_df = holder_df.set_index('Date')
    
    # 按日期排序
    holder_df = holder_df.sort_index()
    
    return holder_df


def find_average_line_cross_stocks(stock_name=None, stock_code=None):
    """查找连续7天或以上上涨且成交量连续递增的股票"""
    try:
        # 创建数据库连接
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
        
        # 确保至少提供了一个参数
        if stock_name is None and stock_code is None:
            print("请提供股票名称或股票代码中的至少一个参数")
            return
        
        # 如果只提供了股票名称，则查询股票代码
        if stock_name is not None and stock_code is None:
            query_code = """
            SELECT DISTINCT stock_code
            FROM stock_data 
            WHERE stock_name = %s
            LIMIT 1
            """
            code_result = pd.read_sql(query_code, engine, params=(stock_name,))
            if code_result.empty:
                print(f"未找到股票名称为 {stock_name} 的股票代码")
                return
            stock_code = code_result.iloc[0]['stock_code']
        
        # 如果只提供了股票代码，则查询股票名称
        elif stock_name is None and stock_code is not None:
            query_name = """
            SELECT DISTINCT stock_name
            FROM stock_data 
            WHERE stock_code = %s
            LIMIT 1
            """
            name_result = pd.read_sql(query_name, engine, params=(stock_code,))
            if name_result.empty:
                print(f"未找到股票代码为 {stock_code} 的股票名称")
                return
            stock_name = name_result.iloc[0]['stock_name']
        
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
        
        # 计算移动平均线
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['MA90'] = df['Close'].rolling(window=90).mean()
        df['MA120'] = df['Close'].rolling(window=120).mean()
        
        # 计算成交量的20日移动平均线
        df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
        
        # 删除包含NaN的行（由于计算移动平均线导致的前几行缺失值）
        df.dropna(inplace=True)
        
        # 增加图形尺寸以适应更宽的蜡烛图
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 10), gridspec_kw={"height_ratios": [3, 1, 1]})
        
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
        
        # 绘制移动平均线
        ax1.plot(date_nums, df['MA60'], color='blue', linewidth=1.5, label='60日均线')
        ax1.plot(date_nums, df['MA90'], color='orange', linewidth=1.5, label='90日均线')
        ax1.plot(date_nums, df['MA120'], color='purple', linewidth=1.5, label='120日均线')
        ax1.legend()
        
        ax1.set_title("{} 蜡烛图".format(stock_name), fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        # 格式化x轴日期显示
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 10, 20]))  # 只显示每月1号、10号、20号
        
        # 中层：成交量
        ax2.bar(date_nums, df["Volume"], 
                width=0.6, 
                color=df.apply(lambda x: "red" if x.Close > x.Open else "green", axis=1))
        ax2.set_ylabel("Volume", fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 绘制成交量的20日移动平均线
        ax2.plot(date_nums, df['Volume_MA20'], color='blue', linewidth=1.5, label='20日均量')
        ax2.legend()
        
        # 标注成交量大于20日均线3倍以上的日期
        high_volume_indices = df[df['Volume'] > 3 * df['Volume_MA20']].index
        
        for date in high_volume_indices:
            idx = df.index.get_loc(date)
            if isinstance(idx, int) and idx < len(date_nums):
                volume = df['Volume'].iloc[idx]
                # 绘制虚线框标注
                date_num = date_nums[idx]
                # 绘制矩形框 (left, bottom, width, height)
                rect = Rectangle(
                    (float(date_num) - 0.3, 0),  # 略微调整位置使框居中
                    0.6,  # 宽度与柱状图一致
                    float(volume),  # 高度为成交量值
                    linewidth=1,
                    linestyle='--',
                    edgecolor='blue',
                    facecolor='none'
                )
                ax2.add_patch(rect)
        
        # 格式化x轴日期显示，与上图保持一致
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 10, 20]))  # 只显示每月1号、10号、20号

        # 下层：股东人数变化
        holder_data = get_holder_data(stock_name)
        if holder_data is not None and not holder_data.empty:
            # 将股东人数数据与股价数据的日期对齐
            aligned_data = holder_data.reindex(df.index, method='nearest')
            
            # 将日期转换为数字格式以匹配其他子图
            holder_date_nums = [mdates.date2num(date) for date in aligned_data.index]
            
            # 绘制股东人数变化曲线
            ax3.plot(holder_date_nums, aligned_data['HolderCount'], color='blue', linewidth=1.5)
            ax3.fill_between(holder_date_nums, aligned_data['HolderCount'], alpha=0.3, color='blue')
            ax3.set_ylabel("股东人数", fontsize=12)
            ax3.grid(True, alpha=0.3)
            ax3.set_title("股东人数变化", fontsize=12)
            
            # 从efinance获取最新的户均持股信息
            latest_holder_info = None
            try:
                holder_df = ef.stock.get_latest_holder_number()
                # 根据股票代码或股票名称查找对应的户均持股信息
                if stock_code:
                    latest_holder_info = holder_df[holder_df['股票代码'] == stock_code]
                if latest_holder_info is None or latest_holder_info.empty:
                    latest_holder_info = holder_df[holder_df['股票名称'] == stock_name]
                    
                if not latest_holder_info.empty:
                    avg_shares = latest_holder_info['户均持股数量'].iloc[0]
                    avg_value = latest_holder_info['户均持股市值'].iloc[0]
                    
                    # 标注最新的户均持股信息
                    latest_date = aligned_data.index[-1]
                    latest_holder_count = aligned_data['HolderCount'].iloc[-1]
                    if not pd.isna(latest_holder_count):
                        # 将Timestamp转为datetime再格式化
                        latest_date_dt = pd.to_datetime(latest_date)
                        latest_date_str = latest_date_dt.strftime('%Y-%m-%d')
                        latest_date_num = mdates.date2num(latest_date_dt)
                        ax3.annotate(f'最新({latest_date_str}): {latest_holder_count:.0f}人\n户均持股:{avg_shares:.0f}股\n户均市值:{avg_value:.0f}元', 
                                    xy=(latest_date_num, latest_holder_count),
                                    xytext=(10, 0),
                                    textcoords='offset points',
                                    fontsize=10,
                                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
            except Exception as e:
                print(f"获取最新股东信息时出错: {e}")
            
            # 格式化x轴日期显示
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax3.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 10, 20]))
        else:
            ax3.set_visible(False)  # 如果没有股东数据，则隐藏该子图
        
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"绘制 {stock_name} 蜡烛图时出错: {e}")

if __name__ == "__main__":
    # 可以只提供股票名称
    find_average_line_cross_stocks(stock_name='中宠股份')
    # 或者只提供股票代码
    # find_average_line_cross_stocks(stock_code='000001')