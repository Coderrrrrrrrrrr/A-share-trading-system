import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import textwrap

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def read_trade_data(file_path):
    """
    读取中日贸易数据CSV文件
    """
    # 读取CSV文件，由于编码问题可能需要指定encoding参数
    encodings = ['utf-8', 'gbk', 'latin1']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"成功使用 {encoding} 编码读取文件")
            break
        except Exception as e:
            print(f"使用 {encoding} 编码读取失败: {e}")
            continue
    
    if df is None:
        raise Exception("无法使用任何编码读取文件")
    
    # 清理列名（去除引号和多余空格）
    df.columns = [col.strip().strip('"') for col in df.columns]
    
    # 清理数据（去除引号和多余空格）
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip().str.strip('"')
    
    return df

def parse_currency_column(currency_str):
    """
    解析货币字符串，处理带逗号的数字
    """
    if pd.isna(currency_str):
        return np.nan
        
    if isinstance(currency_str, str):
        # 移除逗号并转换为浮点数
        # 处理类似 "27,118,603" 的字符串
        cleaned_str = re.sub(r'[^\d.]', '', currency_str)
        try:
            return float(cleaned_str) if cleaned_str else np.nan
        except:
            return np.nan
    elif isinstance(currency_str, (int, float)):
        return float(currency_str)
    else:
        return np.nan

def wrap_labels(labels, width=15):
    """
    将标签文本按指定宽度换行
    """
    wrapped_labels = []
    for label in labels:
        if isinstance(label, str):
            wrapped_label = '\n'.join(textwrap.wrap(label, width))
            wrapped_labels.append(wrapped_label)
        else:
            wrapped_labels.append(str(label))
    return wrapped_labels

# 读取进出口数据
export_file = r'e:\PycharmProject\量化交易\下载数据\2024年中日贸易出口数据导出.csv'
import_file = r'e:\PycharmProject\量化交易\下载数据\2024年中日贸易进口数据导出.csv'

print("正在读取出口数据...")
export_df = read_trade_data(export_file)
print(f"出口数据行数: {len(export_df)}")

print("正在读取进口数据...")
import_df = read_trade_data(import_file)
print(f"进口数据行数: {len(import_df)}")

# 查看数据结构
print("\n出口数据列名:")
print(export_df.columns.tolist())

print("\n进口数据列名:")
print(import_df.columns.tolist())

# 确定"人民币"列（应该是第九列，索引为8）
currency_col_index = 8
if len(export_df.columns) > currency_col_index:
    export_currency_data = export_df.iloc[:, currency_col_index]
    print(f"\n出口数据人民币列示例: {export_currency_data.head().tolist()}")
else:
    export_currency_data = export_df.iloc[:, -1]  # 使用最后一列作为备选
    print(f"\n出口数据使用最后一列作为人民币列")

if len(import_df.columns) > currency_col_index:
    import_currency_data = import_df.iloc[:, currency_col_index]
    print(f"进口数据人民币列示例: {import_currency_data.head().tolist()}")
else:
    import_currency_data = import_df.iloc[:, -1]  # 使用最后一列作为备选
    print(f"进口数据使用最后一列作为人民币列")

# 解析人民币列数据
export_df['人民币'] = export_currency_data.apply(parse_currency_column)
import_df['人民币'] = import_currency_data.apply(parse_currency_column)

print(f"\n解析后的人民币数据示例:")
print(f"出口数据人民币列解析后示例: {export_df['人民币'].head().tolist()}")
print(f"进口数据人民币列解析后示例: {import_df['人民币'].head().tolist()}")

# 获取商品名称列（应该是第二列，索引为1）
export_df['商品名称'] = export_df.iloc[:, 1]
import_df['商品名称'] = import_df.iloc[:, 1]

# 数据清洗：移除无效的人民币值
initial_export_count = len(export_df)
initial_import_count = len(import_df)

export_df = export_df.dropna(subset=['人民币'])
import_df = import_df.dropna(subset=['人民币'])

# 移除无穷大值和负值
export_df = export_df[export_df['人民币'] >= 0]
import_df = import_df[import_df['人民币'] >= 0]

export_df = export_df[np.isfinite(export_df['人民币'])]
import_df = import_df[np.isfinite(import_df['人民币'])]

final_export_count = len(export_df)
final_import_count = len(import_df)

print(f"\n数据清洗情况:")
print(f"出口数据: {initial_export_count} -> {final_export_count}")
print(f"进口数据: {initial_import_count} -> {final_import_count}")

# 按人民币金额降序排列
export_df = export_df.sort_values('人民币', ascending=False)
import_df = import_df.sort_values('人民币', ascending=False)

# 选择前50个商品
top50_export = export_df[['商品名称', '人民币']].head(50)
top50_import = import_df[['商品名称', '人民币']].head(50)

print(f"\n出口前50商品数据条数: {len(top50_export)}")
print(f"进口前50商品数据条数: {len(top50_import)}")

# 检查是否有有效数据
if len(top50_export) == 0 or len(top50_import) == 0:
    print("警告：没有足够的有效数据来生成图表")
else:
    # 创建单独的出口图表
    fig1, ax1 = plt.subplots(figsize=(12, 16))
    
    # 绘制出口前50商品横向柱状图
    y_pos1 = np.arange(len(top50_export))
    bars1 = ax1.barh(y_pos1, top50_export['人民币'], color='skyblue', height=0.6)
    ax1.set_ylabel('商品名称')
    ax1.set_xlabel('人民币金额')
    ax1.set_title('2024年中日贸易出口前50商品\n（按人民币金额排序）')
    
    # 处理商品名称换行显示
    wrapped_labels1 = wrap_labels(top50_export['商品名称'], width=15)
    ax1.set_yticks(y_pos1)
    ax1.set_yticklabels(wrapped_labels1, fontsize=7)
    
    # 增加y轴间距，防止标签重叠
    ax1.tick_params(axis='y', pad=15)
    
    # 在每个柱子上显示数值（仅当值为有限数值时）
    for bar, (_, row) in zip(bars1, top50_export.iterrows()):
        value = row['人民币']
        if np.isfinite(value):
            ax1.text(bar.get_width() + bar.get_width()*0.01, bar.get_y() + bar.get_height()/2,
                     f'{value:,.0f}',
                     ha='left', va='center', fontsize=6)
    
    plt.tight_layout()
    plt.show()
    
    # 创建单独的进口图表
    fig2, ax2 = plt.subplots(figsize=(12, 16))
    
    # 绘制进口前50商品横向柱状图
    y_pos2 = np.arange(len(top50_import))
    bars2 = ax2.barh(y_pos2, top50_import['人民币'], color='lightcoral', height=0.6)
    ax2.set_ylabel('商品名称')
    ax2.set_xlabel('人民币金额')
    ax2.set_title('2024年中日贸易进口前50商品\n（按人民币金额排序）')
    
    # 处理商品名称换行显示
    wrapped_labels2 = wrap_labels(top50_import['商品名称'], width=15)
    ax2.set_yticks(y_pos2)
    ax2.set_yticklabels(wrapped_labels2, fontsize=7)
    
    # 增加y轴间距，防止标签重叠
    ax2.tick_params(axis='y', pad=15)
    
    # 在每个柱子上显示数值（仅当值为有限数值时）
    for bar, (_, row) in zip(bars2, top50_import.iterrows()):
        value = row['人民币']
        if np.isfinite(value):
            ax2.text(bar.get_width() + bar.get_width()*0.01, bar.get_y() + bar.get_height()/2,
                     f'{value:,.0f}',
                     ha='left', va='center', fontsize=6)
    
    plt.tight_layout()
    plt.show()

# 打印前10名商品信息
print("\n出口前10商品:")
for i, (_, row) in enumerate(top50_export.head(10).iterrows(), 1):
    print(f"{i:2d}. {row['商品名称']:<50} {row['人民币']:>15,.0f}")

print("\n进口前10商品:")
for i, (_, row) in enumerate(top50_import.head(10).iterrows(), 1):
    print(f"{i:2d}. {row['商品名称']:<50} {row['人民币']:>15,.0f}")