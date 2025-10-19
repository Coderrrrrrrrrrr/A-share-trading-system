import efinance as ef
import pandas as pd
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

class HolderNumber():
    def __init__(self, data_dir="下载数据"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        filepath = os.path.join(self.data_dir, '股东人数统计.xlsx')
        if not os.path.exists(filepath):
            self.get_holder_number()
        else:
            print("股东人数统计.xlsx 文件已存在，跳过生成")

    def get_holder_number(self):
    
        # 创建一个字典用于存储报告期数据
        report_data = {}

        # 创建一个列表用于存储所有数据
        all_data = []

        # 生成从2024-01-01至今的所有日期
        start_date = datetime(2024, 1, 1)
        end_date = datetime.now()

        # 生成日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        # 定义报告期日期（MMDD格式）
        report_periods = ['0331', '0630', '0930', '1231']

        print("开始获取股东人数数据...")

        # 遍历每个日期
        for date_obj in date_range:
            # 格式化日期为字符串
            date_str = date_obj.strftime('%Y-%m-%d')
            mmdd = date_obj.strftime('%m%d')
            yyyy = date_obj.strftime('%Y')
            
            try:
                # 检查是否为报告期
                if mmdd in report_periods:
                    print(f"正在获取 {date_str} 的数据...")
                    # 获取指定日期的股东人数数据
                    res = ef.stock.get_latest_holder_number(date=date_str)
                    
                    # 检查是否有数据返回
                    if res is not None and not res.empty:
                        # 只保留需要的列
                        res_filtered = res[['股票代码', '股票名称', '股东人数']].copy()
                        
                        # 存储报告期数据
                        report_data[yyyy + mmdd] = res_filtered
                        print(f"成功获取 {date_str} 的数据，共 {len(res_filtered)} 条记录")
                    else:
                        print(f"{date_str} 没有数据返回")
                        report_data[yyyy + mmdd] = pd.DataFrame()
                else:
                    # 非报告期日期，使用最近的报告期数据
                    # 确定最近的报告期
                    latest_report_period = None
                    for period in sorted(report_periods, reverse=True):
                        if mmdd > period:
                            latest_report_period = yyyy + period
                            break
                    
                    # 如果当年没有合适的报告期，使用上一年最后一个报告期
                    if latest_report_period is None:
                        prev_year = str(int(yyyy) - 1)
                        latest_report_period = prev_year + '1231'
                    
                    # 如果有对应的报告期数据，则使用
                    if latest_report_period in report_data and not report_data[latest_report_period].empty:
                        # 复用已有数据
                        res_filtered = report_data[latest_report_period].copy()
                        res_filtered['日期'] = date_str
                        # 添加到总数据中
                        all_data.append(res_filtered)
                    
            except Exception as e:
                print(f"处理{date_str}的数据时出错: {e}")

        # 处理报告期数据，添加到总数据中
        for key, data in report_data.items():
            if not data.empty:
                # 从键中提取年份和期间
                yyyy = key[:4]
                mmdd = key[4:6] + key[6:8]
                
                # 构造日期字符串
                date_str = f"{yyyy}-{mmdd[:2]}-{mmdd[2:4]}"
                
                # 添加日期列
                data_with_date = data.copy()
                data_with_date['日期'] = date_str
                
                # 添加到总数据中
                all_data.append(data_with_date)

        print("\n数据获取完成，正在处理数据...")

        # 合并所有数据
        if all_data:
            # 合并所有DataFrame
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"总共处理了 {len(date_range)} 天的数据，合计 {len(combined_df)} 条记录")
            
            # 将数据重塑为宽格式，使每列代表一个日期
            pivot_df = combined_df.pivot_table(
                index=['股票代码', '股票名称'], 
                columns='日期', 
                values='股东人数', 
                aggfunc='first'
            )
            
            # 重置列名，去除多重索引
            pivot_df.columns.name = None
            pivot_df.index.names = ['股票代码', '股票名称']
            
            # 保存为Excel文件
            output_filename = os.path.join(self.data_dir, '股东人数统计.xlsx')
            pivot_df.to_excel(output_filename)
            print(f"数据已保存到 {output_filename}")
            
            # 显示部分结果
            print("\n部分结果预览:")
            print(pivot_df.head(10))
        else:
            print("未获取到任何数据")


if __name__ == '__main__':
    HolderNumber()