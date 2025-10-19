import mplfinance.original_flavor as mpf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import argrelextrema
import numpy as np
import os
from datetime import datetime

class Map_Drawing():

    def __init__(self, stock_name = '比亚迪',stock_code = '002594',begin_date = '20240101',data_dir="下载数据"):

        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        self.stock_name = stock_name
        self.stock_code = stock_code
        self.begin_date = begin_date
        self.data_dir = data_dir
        self.end_date = datetime.now().strftime('%Y%m%d')

        self.graph_draw()

    def get_price(self):
        
        # 1. 从xlsx文件中提取比亚迪股票数据
        filepath = os.path.join(self.data_dir, '{}{}至{}股价.xlsx'.format(self.stock_name,self.begin_date,self.end_date))
        df = pd.read_excel(filepath)

        # 重命名列以匹配英文格式
        data = df.rename(columns={
            '日期': 'Date',
            '开盘': 'Open',
            '最高': 'High',
            '最低': 'Low',
            '收盘': 'Close',
            '成交量': 'Volume'
        })

        # 设置日期为索引
        data['Date'] = pd.to_datetime(data['Date'])
        data.set_index('Date', inplace=True)

        return data

    def get_financial(self):


        # 读取财务数据
        filepath = os.path.join(self.data_dir, './company_performance_pivot.xlsx')
        financial_data = pd.read_excel(filepath)

        # 筛选比亚迪的财务数据（股票代码002594）
        byd_financial_data = financial_data[financial_data['股票简称'] == self.stock_name]
        if byd_financial_data.empty:
            raise ValueError("未找到股票简称为{}的财务数据".format(self.stock_name))
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

        return profit_annotations

    def get_holder_data(self):
        """获取股东人数数据"""
        # 读取股东人数统计文件
        filepath = os.path.join(self.data_dir, './股东人数统计.xlsx')
        holder_data = pd.read_excel(filepath)
        
        # 筛选指定股票名称的数据
        stock_holder_data = holder_data[holder_data['股票名称'] == self.stock_name]
        
        if stock_holder_data.empty:
            print(f"未找到股票名称为{self.stock_name}的股东人数数据")
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

    def graph_mark(self):

        data = self.get_price()

        # ===== 阶段性高点低点检测参数 =====
        # 可手动调整的参数，用于控制极值检测的敏感度
        PEAK_VALLEY_WINDOW = 30  # 窗口大小，用于确定局部极值，值越大检测到的极值点越少
        # ================================

        # 增加图形尺寸以适应更宽的蜡烛图
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 10), gridspec_kw={"height_ratios": [3, 1, 1]})

        # 准备OHLC数据，需要将日期转换为数字格式，同时调整数据点间距以适应更宽的蜡烛图
        ohlc_data = []
        spacing_factor = 3  # 增加数据点间距以避免重叠
        date_nums = []
        for i in range(len(data)):
            date_num = mdates.date2num(data.index[i]) + i * (spacing_factor - 1)  # 调整日期位置以增加间距
            date_nums.append(date_num)
            open_price = data['Open'].iloc[i]
            high_price = data['High'].iloc[i]
            low_price = data['Low'].iloc[i]
            close_price = data['Close'].iloc[i]
            ohlc_data.append([date_num, open_price, high_price, low_price, close_price])

        # 上层：蜡烛图
        mpf.candlestick_ohlc(
            ax1, 
            ohlc_data,  # 格式：[时间戳, O, H, L, C]
            width=2.6,  # 蜡烛宽度
            colorup="red",  # 上涨（收盘价>开盘价）颜色
            colordown="green",  # 下跌颜色
            alpha=0.8  # 透明度
        )
        ax1.set_title("{}{}至今蜡烛图".format(self.stock_name,self.begin_date), fontsize=14)
        ax1.grid(True, alpha=0.3)

        # 格式化x轴日期显示
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator())

        # 查找并标记阶段性高点和低点
        # 使用scipy寻找局部极值点
        print(f"当前使用的窗口大小: {PEAK_VALLEY_WINDOW}")
        local_max_indices = argrelextrema(data['Close'].values, np.greater, order=PEAK_VALLEY_WINDOW)[0]
        local_min_indices = argrelextrema(data['Close'].values, np.less, order=PEAK_VALLEY_WINDOW)[0]

        # 打印高点和低点信息到控制台
        print("阶段性高点:")
        high_points = []
        for idx in local_max_indices:
            date = data.index[idx]
            price = data['High'].iloc[idx]
            high_points.append((date, price))
            print(f"日期: {pd.to_datetime(date).strftime('%Y-%m-%d')}, 价格: {price:.2f}")
            ax1.plot(date_nums[idx], price, 'ro', markersize=8)  # 在图上标记红色圆点
            ax1.annotate(f'{price:.2f}', 
                        xy=(date_nums[idx], price),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        fontsize=8,
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='red', alpha=0.7))

        print("\n阶段性低点:")
        low_points = []
        for idx in local_min_indices:
            date = data.index[idx]
            price = data['Low'].iloc[idx]
            low_points.append((date, price))
            print(f"日期: {pd.to_datetime(date).strftime('%Y-%m-%d')}, 价格: {price:.2f}")
            ax1.plot(date_nums[idx], price, 'go', markersize=8)  # 在图上标记绿色圆点
            ax1.annotate(f'{price:.2f}', 
                        xy=(date_nums[idx], price),
                        xytext=(0, -15),
                        textcoords='offset points',
                        ha='center',
                        fontsize=8,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='green', alpha=0.7))

        profit_annotations = self.get_financial()

        # 在K线图上添加注释
        for annotation in profit_annotations:
            target_date = annotation['date']
            # 查找下一个最近的交易日
            actual_date = self.find_next_trading_date(target_date, data)
            # 获取实际日期在数据中的索引
            if actual_date in data.index:
                idx = data.index.get_loc(actual_date)
                close_price = data['Close'].loc[actual_date]
                ax1.annotate(annotation['label'],
                            xy=(date_nums[idx], close_price),
                            xytext=(0, 30),  # 统一偏移量
                            textcoords='offset points',
                            arrowprops=dict(arrowstyle='->', color='black', lw=0.8),
                            fontsize=9,
                            ha='center',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        return ax1,ax2,ax3,date_nums

    # 添加一个函数来查找下一个最近的交易日
    def find_next_trading_date(self,target_date, data):
        """查找下一个最近的交易日"""
        # 筛选大于等于目标日期的数据
        future_data = data[data.index >= target_date]
        if not future_data.empty:
            # 返回最近的交易日
            return future_data.index[0]
        else:
            # 如果没有找到，返回原始日期
            return target_date


    def graph_draw(self):
        ax1,ax2,ax3,date_nums = self.graph_mark()
        data = self.get_price()
        
        # 获取股东人数数据
        holder_data = self.get_holder_data()

        # 下层：成交量
        # 调整成交量图的宽度以匹配K线图的宽度，并使用相同的x轴位置
        ax2.bar(date_nums, data["Volume"], 
                width=2.6, 
                color=data.apply(lambda x: "red" if x.Close > x.Open else "green", axis=1))
        ax2.set_ylabel("Volume", fontsize=12)
        ax2.grid(True, alpha=0.3)

        # 格式化x轴日期显示，与上图保持一致
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        
        # 最下层：股东人数变化
        if holder_data is not None and not holder_data.empty:
            # 将股东人数数据与股价数据的日期对齐
            aligned_data = holder_data.reindex(data.index, method='nearest')
            
            # 将日期转换为数字格式以匹配其他子图
            holder_date_nums = [mdates.date2num(date) for date in aligned_data.index]
            
            # 绘制股东人数变化曲线
            ax3.plot(holder_date_nums, aligned_data['HolderCount'], color='blue', linewidth=1.5)
            ax3.fill_between(holder_date_nums, aligned_data['HolderCount'], alpha=0.3, color='blue')
            ax3.set_ylabel("股东人数", fontsize=12)
            ax3.grid(True, alpha=0.3)
            ax3.set_title("股东人数变化", fontsize=12)
            
            # 格式化x轴日期显示
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax3.xaxis.set_major_locator(mdates.MonthLocator())
        else:
            ax3.set_visible(False)  # 如果没有股东数据，则隐藏该子图

        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        if holder_data is not None and not holder_data.empty:
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    Map_Drawing()