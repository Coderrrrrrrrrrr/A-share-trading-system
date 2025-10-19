import efinance as ef
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import ticker
import matplotlib.font_manager as fm
from datetime import datetime
import os

def get_daily_price(stock_code='002594', stock_name='比亚迪', begin_date='20240101', data_dir='下载数据'):
    """获取指定股票的每日价格数据并保存到Excel文件"""
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    end_date = datetime.now().strftime('%Y%m%d')
    
    # 检查目标文件是否已存在
    filepath = os.path.join(data_dir, f'{stock_name}{begin_date}至{end_date}股价.xlsx')
    if os.path.exists(filepath):
        print(f"文件 {filepath} 已存在，跳过数据获取")
        return pd.read_excel(filepath)
    
    # 获取股票价格数据
    kline_dict = ef.stock.get_quote_history(
        stock_codes=stock_code, 
        beg=begin_date, 
        end=end_date, 
        klt=101, 
        fqt=1, 
        market_type=None, 
        suppress_error=False, 
        use_id_cache=True
    )

    df = pd.DataFrame(kline_dict)
    print(df)

    # 确保数据目录存在
    os.makedirs(data_dir, exist_ok=True)
    
    # 导出为Excel文件
    df.to_excel(filepath, index=False)
    print(f"数据已导出到 {filepath} 文件")
    
    return df