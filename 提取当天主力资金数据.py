import efinance as ef
import pandas as pd
from datetime import datetime

class BigMoney():
    def __init__(self):

        # 获取当前日期
        self.current_date = datetime.now().strftime('%Y-%m-%d')

        for i in ['行业板块实时','概念板块实时','沪深京A股市场']:
             self.get_stock_code(i)
        

    def get_stock_code(self,filename):
        # 读取之前保存的Excel文件
        df_industry = pd.read_excel('{}行情_{}.xlsx'.format(filename,self.current_date))

        # 打印列名以确认正确的列名
        print("列名:", df_industry.columns.tolist())

        # 检查是否存在"股票代码"列，如果不存在则使用第一列
        if '股票代码' in df_industry.columns:
            stock_codes = df_industry['股票代码'].tolist()
        else:
            # 假设第一列是股票代码
            first_column = df_industry.columns[0]
            stock_codes = df_industry[first_column].tolist()
            print(f"使用第一列 '{first_column}' 作为股票代码列")

        # 创建一个空的DataFrame用于存储结果
        result_df = pd.DataFrame()


        # 循环处理每个股票代码
        for code in stock_codes:
            try:
                # 获取历史账单数据
                stock_data = ef.stock.get_history_bill(str(code))
                
                # 筛选日期为当前日期的数据
                date_columns = [col for col in stock_data.columns if '日期' in col]
                if date_columns:
                    # 使用第一个包含"日期"的列
                    date_column = date_columns[0]
                    # 根据日期筛选数据
                    filtered_data = stock_data[stock_data[date_column].astype(str).str.contains(self.current_date)]
                    
                    # 如果有匹配的数据，则添加到结果DataFrame中
                    if not filtered_data.empty:
                        result_df = pd.concat([result_df, filtered_data], ignore_index=True)
                
                print(f"已处理股票代码: {code}")
                
            except Exception as e:
                print(f"处理股票代码 {code} 时出错: {e}")

        # 保存结果到Excel文件
        output_filename = f'{filename}主力资金流入数据_{self.current_date}.xlsx'
        result_df.to_excel(output_filename, index=False)

        print(f"数据已保存至 {output_filename}")
        print(result_df)


if __name__ == '__main__':
    BigMoney()