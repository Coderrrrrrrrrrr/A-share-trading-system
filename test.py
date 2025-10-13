import efinance as ef
import pandas as pd

# 1. 批量拉取历史日K线
stocks = ['600519', '000001']
kline_dict = ef.stock.get_quote_history(stock_codes=stocks, beg='20240101', end='20240501')

# 合并字典中的每个DataFrame，并添加“股票代码”列以便后续groupby操作
kline_list = []
for code, df in kline_dict.items():
    df['股票代码'] = code  # 添加股票代码列
    kline_list.append(df)

# 合并所有DataFrame
kline = pd.concat(kline_list, ignore_index=True)

# 现在可以使用groupby
print(kline.groupby('股票代码').head())

# 2. 实时行情
realtime = ef.stock.get_realtime_quotes()
print(realtime[['股票代码', '最新价', '涨跌幅']].head())

# 3. 基金净值
funds = ['161725', '005827']
fund_nav = ef.fund.get_quote_history(funds)
print(fund_nav.head())

# 4. 输出文件备份
kline.to_csv('stocks_kline.csv', index=False)
fund_nav.to_csv('funds_nav.csv', index=False)