import efinance as ef
import pandas as pd
from datetime import datetime
import os

class Report_Collect():
    def __init__(self, data_dir="下载数据"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.get_financial_report()

    # 定义需要获取数据的日期列表
    def generate_quarterly_dates(self):
        """
        根据当前日期，自动生成需要获取数据的日期列表
        包括当前年份和前一年的季度末日期
        """
        today = datetime.today()
        current_year = today.year
        current_month = today.month
        
        # 确定当前年份已完成的季度
        quarters = []
        if current_month >= 3:
            quarters.append(f"{current_year}-03-31")
        if current_month >= 6:
            quarters.append(f"{current_year}-06-30")
        if current_month >= 9:
            quarters.append(f"{current_year}-09-30")
        if current_month >= 12:
            quarters.append(f"{current_year}-12-31")
        
        # 添加前几年的季度日期
        dates = quarters.copy()
        for i in range(1, 3):  # 添加前两年的数据
            year = current_year - i
            dates.extend([
                f"{year}-12-31",
                f"{year}-09-30",
                f"{year}-06-30",
                f"{year}-03-31"
            ])
        
        return dates

    def get_financial_report(self):

        # 自动生成日期列表
        dates = self.generate_quarterly_dates()

        # 创建一个空列表来存储各日期的数据
        dataframes = []

        # 循环获取每个日期的数据
        for date in dates:
            kline_dict = ef.stock.get_all_company_performance(date)
            df = pd.DataFrame(kline_dict)
            # 添加日期列以便后续处理
            df['日期'] = date
            dataframes.append(df)

        # 合并所有数据
        combined_df = pd.concat(dataframes, ignore_index=True)

        # 转换日期格式
        combined_df['日期'] = pd.to_datetime(combined_df['日期'])

        # 先检查数据中实际包含的列
        print("数据中实际包含的列:", combined_df.columns.tolist())

        # 选择数据中实际存在的关键财务指标列进行透视
        available_columns = [col for col in ['股票代码', '股票简称', '日期', '公告日期', '营业收入', '营业收入同比增长', '营业收入季度环比', '净利润', '净利润同比增长', '净利润季度环比', '每股收益', '每股净资产', '净资产收益率', '销售毛利率', '每股经营现金流量'] if col in combined_df.columns]
        missing_columns = [col for col in ['股票代码', '股票简称', '日期', '每股收益', '营业收入', '净利润'] if col not in combined_df.columns]
        if missing_columns:
            print(f"以下列在数据中不存在: {missing_columns}")

        filtered_df = combined_df[available_columns]

        # 将数据重塑为透视表格式，每个日期作为列，股票代码作为行
        # 这样便于横向比较同一日期下不同股票的财务指标
        if '股票代码' in filtered_df.columns and '日期' in filtered_df.columns:
            pivot_values = [col for col in ['公告日期', '营业收入', '营业收入同比增长', '营业收入季度环比', '净利润', '净利润同比增长', '净利润季度环比', '每股收益', '每股净资产', '净资产收益率', '销售毛利率', '每股经营现金流量'] if col in filtered_df.columns]
            
            pivot_df = filtered_df.pivot_table(
                index=['股票代码'] + (['股票简称'] if '股票简称' in filtered_df.columns else []),
                columns='日期',
                values=pivot_values,
                aggfunc='first'
            )

            # 展平列索引，使输出更清晰
            pivot_df.columns = [f"{col[0]}_{col[1].strftime('%Y-%m-%d')}" for col in pivot_df.columns]

            # 重置索引，使股票代码和名称成为普通列
            pivot_df = pivot_df.reset_index()

            # 导出为Excel文件
            filepath = os.path.join(self.data_dir, 'company_performance_pivot.xlsx')
            pivot_df.to_excel(filepath, index=False)
            print(f"数据已导出到 {filepath} 文件")
        else:
            print("缺少必要的列（股票代码或日期），无法生成透视表")

if __name__ == '__main__':
    Report_Collect()