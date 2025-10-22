import pandas as pd
import numpy as np
import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

current_date = datetime.now().strftime('%Y%m%d')

def extract_car_production_data():
    # 生成输出文件名
    output_dir = r'e:\PycharmProject\量化交易\下载数据'
    output_file = os.path.join(output_dir, f'各品牌汽车产量-{current_date}.xlsx')
    
    # 检查结果文件是否已存在
    if os.path.exists(output_file):
        print(f"文件 {output_file} 已存在，无需重新生成")
        # 读取已存在的文件
        df = pd.read_excel(output_file)
        return df
    # 读取Excel文件
    input_file = r'e:\PycharmProject\量化交易\下载数据\汽车产量中国一汽累计值等_20251020_172208.xlsx'
    df = pd.read_excel(input_file)
    
    # 获取所有列名
    columns = df.columns.tolist()
    
    # 筛选出符合"汽车:产量:XXXX:累计值"格式的列（第2列，第11列，第20列……）
    target_columns = []
    brand_names = []
    
    # 符合规律的列索引: 1, 10, 19, 28, ... (从0开始计数，即第2, 11, 20, 29...列)
    # 这些列的共同特征是只有4个冒号分隔的部分，即"汽车:产量:XXXX:累计值"
    for i, col in enumerate(columns):
        if isinstance(col, str) and col.startswith("汽车:产量:") and col.endswith(":累计值"):
            parts = col.split(":")
            # 检查是否正好有4个部分（即3个冒号）
            if len(parts) == 4:
                target_columns.append(i)
                # 提取品牌名（XXXX部分）
                brand_name = parts[2]
                brand_names.append(brand_name)
    
    # 创建新的DataFrame，包含日期列和筛选出的列
    if target_columns:
        # 日期列是第一列（指标名称）
        result_columns = [0] + target_columns
        new_df = df.iloc[:, result_columns].copy()
        
        # 重命名列名，只保留品牌名（第一列保持原名，其他列提取品牌名）
        new_columns = [columns[0]] + brand_names
        new_df.columns = new_columns
        
        
        # 保存到Excel文件
        new_df.to_excel(output_file, index=False)
        print(f"数据已保存至: {output_file}")
        print(f"提取的列索引: {target_columns}")
        print(f"提取的品牌: {brand_names}")
        return new_df
    else:
        print("未找到符合格式的列")

def extract_car_sales_data():
    # 生成输出文件名
    output_dir = r'e:\PycharmProject\量化交易\下载数据'
    output_file = os.path.join(output_dir, f'各品牌汽车销量-{current_date}.xlsx')
    
    # 检查结果文件是否已存在
    if os.path.exists(output_file):
        print(f"文件 {output_file} 已存在，无需重新生成")
        # 读取已存在的文件
        df = pd.read_excel(output_file)
        return df
    
    # 读取Excel文件
    input_file = r'e:\PycharmProject\量化交易\下载数据\狭义乘用车零售销量比亚迪汽车当月值等_20251020_170555.xlsx'
    df = pd.read_excel(input_file)
    
    # 获取所有列名
    columns = df.columns.tolist()
    
    # 筛选出符合"狭义乘用车:零售销量:XXXX:当月值"格式的列
    target_columns = []
    brand_names = []
    
    # 查找符合"狭义乘用车:零售销量:XXXX:当月值"格式的列
    for i, col in enumerate(columns):
        if isinstance(col, str) and col.startswith("狭义乘用车:零售销量:") and col.endswith(":当月值"):
            parts = col.split(":")
            # 检查是否正好有4个部分（即3个冒号）
            if len(parts) == 4:
                target_columns.append(i)
                # 提取品牌名（XXXX部分）
                brand_name = parts[2]
                brand_names.append(brand_name)
    
    # 创建新的DataFrame，包含日期列和筛选出的列
    if target_columns:
        # 日期列是第一列（指标名称）
        result_columns = [0] + target_columns
        new_df = df.iloc[:, result_columns].copy()
        
        # 重命名列名，只保留品牌名（第一列保持原名，其他列提取品牌名）
        new_columns = [columns[0]] + brand_names
        new_df.columns = new_columns
        
        # 保存到Excel文件
        new_df.to_excel(output_file, index=False)
        print(f"数据已保存至: {output_file}")
        print(f"提取的列索引: {target_columns}")
        print(f"提取的品牌: {brand_names}")
        return new_df
    else:
        print("未找到符合格式的列")

def plot_production_vs_sales(production_df, sales_df):
    """
    绘制产量和销量的时间序列折线图
    """
    # 设置图形大小和样式
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # 处理产量数据的时间序列
    production_dates = pd.to_datetime(production_df['指标名称'])
    
    # 绘制每个品牌的产量折线
    production_brands = production_df.columns[1:]  # 跳过'指标名称'列
    for brand in production_brands:
        ax.plot(production_dates, production_df[brand], marker='o', label=f'{brand} 产量')
    
    # 处理销量数据的时间序列
    sales_dates = pd.to_datetime(sales_df['指标名称'])
    
    # 绘制每个品牌的销量折线
    sales_brands = sales_df.columns[1:]  # 跳过'指标名称'列
    for brand in sales_brands:
        ax.plot(sales_dates, sales_df[brand], marker='s', label=f'{brand} 销量')
    
    # 添加标签和标题
    ax.set_xlabel('日期')
    ax.set_ylabel('数量')
    ax.set_title('各品牌汽车产量与销量时间序列变化')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 自动调整日期标签
    fig.autofmt_xdate()
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_dir = r'e:\PycharmProject\量化交易\下载数据'
    output_file = os.path.join(output_dir, f'各品牌汽车产销量时间序列图-{current_date}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"产销量时间序列图已保存至: {output_file}")
    
    # 显示图表
    plt.show()
    
    return fig

# 执行函数
if __name__ == "__main__":
    production_df = extract_car_production_data()
    sales_df = extract_car_sales_data()
    
    if production_df is not None and sales_df is not None:
        plot_production_vs_sales(production_df, sales_df)