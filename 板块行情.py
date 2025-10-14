import efinance as ef
import pandas as pd
from datetime import datetime

res1 = ef.stock.get_realtime_quotes('行业板块')

# 获取当前日期
today = datetime.now().strftime('%Y-%m-%d')

# 保存为xlsx文件，文件名包含当天日期
filename = f'行业板块实时行情_{today}.xlsx'
res1.to_excel(filename, index=False)

print(f'数据已保存至 {filename}')
print(res1)


res2 = ef.stock.get_realtime_quotes('概念板块')

# 获取当前日期
today = datetime.now().strftime('%Y-%m-%d')

# 保存为xlsx文件，文件名包含当天日期
filename = f'概念板块实时行情_{today}.xlsx'
res2.to_excel(filename, index=False)

print(f'数据已保存至 {filename}')
print(res2)


res3 = ef.stock.get_realtime_quotes()

# 获取当前日期
today = datetime.now().strftime('%Y-%m-%d')

# 保存为xlsx文件，文件名包含当天日期
filename = f'沪深京A股市场行情_{today}.xlsx'
res3.to_excel(filename, index=False)

print(f'数据已保存至 {filename}')
print(res3)