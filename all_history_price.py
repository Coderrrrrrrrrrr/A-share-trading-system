import efinance as ef
import pandas as pd
import os
import time
import re
from daily_price import get_daily_price

# 获取实时行情数据
res = ef.stock.get_realtime_quotes()

# 提取股票代码和股票名称列
stocks_data = res[['股票代码', '股票名称']]

# 创建保存数据的目录
data_dir = os.path.join('下载数据', '沪深京所有股票价格')
os.makedirs(data_dir, exist_ok=True)

# 获取目录中已存在的文件名（不含扩展名）
existing_files = set()
for file_name in os.listdir(data_dir):
    if file_name.endswith('.xlsx'):
        # 提取文件名（不含扩展名）
        file_base_name = os.path.splitext(file_name)[0]
        existing_files.add(file_base_name)

# 遍历每只股票，获取其价格数据并保存到单独的Excel文件中
for index, row in stocks_data.iterrows():
    stock_code = str(row['股票代码'])
    stock_name = str(row['股票名称'])
    
    # 清理股票名称中的特殊字符，特别是'*'，以避免文件名无效
    cleaned_stock_name = re.sub(r'[\\/:*?"<>|]', '', stock_name)
    
    # 检查是否已存在该股票的数据文件
    file_identifier = f"{cleaned_stock_name}20240101至20251027股价"
    if file_identifier in existing_files:
        print(f"{stock_name}({stock_code}) 的数据已存在，跳过获取")
        continue
    
    try:
        # 调用get_daily_price方法获取股票数据
        print(f"正在获取 {stock_name}({stock_code}) 的价格数据...")
        get_daily_price(stock_code=stock_code, stock_name=cleaned_stock_name, data_dir=data_dir)
        print(f'已获取 {stock_name}({stock_code}) 的价格数据')
        # 增加API调用间隔，避免触发限制
        import random
        time.sleep(random.randint(15, 20))

    except Exception as e:
        print(f"获取 {stock_name}({stock_code}) 数据时出错: {e}")
        # 即使出错也等待一段时间再继续
        time.sleep(2)
        
print("所有股票数据获取完成！")