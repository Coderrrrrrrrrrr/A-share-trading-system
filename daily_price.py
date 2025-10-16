import efinance as ef
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import ticker
import matplotlib.font_manager as fm
from datetime import datetime

class Price_Collect():

    def __init__(self):

        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        self.stock_name = '比亚迪'
        self.stock_code = '002594'
        self.begin_date = '20240101'

        self.get_daily_price()
        self.draw_up_down_line_chart()


    def get_daily_price(self):
        # 获取股票价格数据
        # 将 market_type 参数从字符串 'A_stock' 修改为正确的枚举值
        # 修改end参数使其始终等于当天日期
        end_date = datetime.now().strftime('%Y%m%d')
        kline_dict = ef.stock.get_quote_history(stock_codes=self.stock_code, beg=self.begin_date, end=end_date, klt=101, fqt=1, market_type=None, suppress_error=False, use_id_cache=True)

        df = pd.DataFrame(kline_dict)
        print(df)

        # 导出为Excel文件
        df.to_excel('{}{}至今股价.xlsx'.format(self.stock_name,self.begin_date), index=False)
        print("数据已导出到 {}{}至今股价.xlsx 文件".format(self.stock_name,self.begin_date))

    def draw_price_line_chart(self):
        # 读取Excel文件数据
        data = pd.read_excel('{}{}至今股价.xlsx'.format(self.stock_name,self.begin_date))

        # 确保日期列是datetime类型
        data['日期'] = pd.to_datetime(data['日期'])

        # 创建图形和子图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

        # 绘制收盘价图表
        ax1.plot(data['日期'], data['收盘'], color='red', linewidth=2)
        ax1.set_title('{}{}至今收盘价走势'.format(self.stock_name,self.begin_date), fontsize=16)
        ax1.set_ylabel('收盘价 (元)', fontsize=12)
        ax1.grid(True, alpha=0.3)

        # 格式化x轴日期显示
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

        return data,ax1,ax2


    def draw_up_down_line_chart(self):
        data,ax1,ax2 = self.draw_price_line_chart()
# 绘制涨跌幅图表
        ax2.plot(data['日期'], data['涨跌幅'], color='blue', linewidth=2)
        ax2.set_title('{}{}至今涨跌幅'.format(self.stock_name,self.begin_date), fontsize=16)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('涨跌幅 (%)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linewidth=0.5)

        # 格式化x轴日期显示
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

        
        # 自动调整布局
        plt.tight_layout()

        # 显示图表
        plt.show()

if __name__ == '__main__':
    
    Price_Collect()