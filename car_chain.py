import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
import os
warnings.filterwarnings('ignore')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 定义文件路径
parts_file = r'e:\PycharmProject\量化交易\下载数据\汽车零部件及配件制造业净资产收益率全行业平均值等_20251020_175434.xlsx'
vehicle_file = r'e:\PycharmProject\量化交易\下载数据\汽车整车制造业净资产收益率全行业平均值等_20251020_175342.xlsx'
manufacturing_file = r'e:\PycharmProject\量化交易\下载数据\汽车制造业净资产收益率全行业平均值等_20251020_175259.xlsx'

# 检查文件是否存在
files_exist = True
missing_files = []

for file_path in [parts_file, vehicle_file, manufacturing_file]:
    if not os.path.exists(file_path):
        files_exist = False
        missing_files.append(file_path)

def load_excel_data(file_path, file_label):
    """加载Excel数据并显示基本信息"""
    try:
        data = pd.read_excel(file_path)
        print(f"\n{file_label} 数据信息:")
        print(f"  文件: {os.path.basename(file_path)}")
        print(f"  形状: {data.shape}")
        print(f"  列名: {list(data.columns)}")
        print(f"  前5行数据:")
        print(data.head())
        return data
    except Exception as e:
        print(f"读取 {file_path} 失败: {e}")
        return None

if files_exist:
    print("正在读取Excel文件...")
    # 读取三个Excel文件
    parts_data = load_excel_data(parts_file, "汽车零部件及配件制造业")
    vehicle_data = load_excel_data(vehicle_file, "汽车整车制造业")
    manufacturing_data = load_excel_data(manufacturing_file, "汽车制造业")
    
    # 检查数据是否成功加载
    if parts_data is None or vehicle_data is None or manufacturing_data is None:
        print("错误：无法加载数据，请检查文件格式")
        exit()
else:
    print("警告：以下文件不存在，使用模拟数据:")
    for file_path in missing_files:
        print(f"  - {file_path}")
    
    

# 数据预处理函数
def preprocess_data(data, prefix):
    """预处理数据，提取年份并清理列名"""
    # 提取年份
    data['年份'] = pd.to_datetime(data['指标名称']).dt.year
    
    # 清理列名，只保留指标名称部分
    new_columns = {}
    for col in data.columns:
        if col == '指标名称' or col == '年份':
            new_columns[col] = col
        else:
            # 从列名中提取指标名称
            metric_name = col.split(':')[-2] if ':' in col else col
            new_columns[col] = metric_name
    
    data.rename(columns=new_columns, inplace=True)
    return data

# 处理数据
if files_exist:
    parts_data = preprocess_data(parts_data, '汽车零部件及配件制造业')
    vehicle_data = preprocess_data(vehicle_data, '汽车整车制造业')
    manufacturing_data = preprocess_data(manufacturing_data, '汽车制造业')

# 定义要比较的指标
common_metrics = [
    '净资产收益率',
    '总资产报酬率', 
    '总资产增长率',
    '资产负债率',
    '销售增长率',
    '销售利润率',
    '成本费用利润率',
    '资本收益率',
    '存货周转率',
    '不良资产比率'

]

# 创建大屏图表
fig = plt.figure(figsize=(20, 15))
fig.suptitle('汽车行业三大领域财务指标对比分析', fontsize=24, fontweight='bold', y=0.95)

# 定义颜色
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
labels = ['零部件制造业', '整车制造业', '汽车制造业']

# 为每个指标创建子图
for i, metric in enumerate(common_metrics):
    ax = plt.subplot(5, 2, i+1)
    
    if files_exist:
        # 确保年份列存在
        if '年份' not in parts_data.columns or '年份' not in vehicle_data.columns or '年份' not in manufacturing_data.columns:
            print("错误：数据中缺少年份列")
            break
            
        # 确保指标列存在
        if metric not in parts_data.columns or metric not in vehicle_data.columns or metric not in manufacturing_data.columns:
            print(f"警告：指标 '{metric}' 在某些数据中不存在")
            continue
            
        # 过滤掉空值并按年份排序
        parts_filtered = parts_data[['年份', metric]].dropna().sort_values('年份')
        vehicle_filtered = vehicle_data[['年份', metric]].dropna().sort_values('年份')
        manufacturing_filtered = manufacturing_data[['年份', metric]].dropna().sort_values('年份')
        
        # 绘制三个领域的指标对比
        ax.plot(parts_filtered['年份'], parts_filtered[metric], marker='o', linewidth=2, 
                markersize=8, color=colors[0], label=labels[0])
        ax.plot(vehicle_filtered['年份'], vehicle_filtered[metric], marker='s', linewidth=2, 
                markersize=8, color=colors[1], label=labels[1])
        ax.plot(manufacturing_filtered['年份'], manufacturing_filtered[metric], marker='^', 
                linewidth=2, markersize=8, color=colors[2], label=labels[2])
        
        # 添加数值标签
        for j, row in parts_filtered.iterrows():
            ax.annotate(f'{row[metric]:.1f}', 
                       (row['年份'], row[metric]), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=colors[0])
        for j, row in vehicle_filtered.iterrows():
            ax.annotate(f'{row[metric]:.1f}', 
                       (row['年份'], row[metric]), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=colors[1])
        for j, row in manufacturing_filtered.iterrows():
            ax.annotate(f'{row[metric]:.1f}', 
                       (row['年份'], row[metric]), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=colors[2])
    else:
        # 使用模拟数据
        ax.plot(parts_data['年份'], parts_data[metric], marker='o', linewidth=2, 
                markersize=8, color=colors[0], label=labels[0])
        ax.plot(vehicle_data['年份'], vehicle_data[metric], marker='s', linewidth=2, 
                markersize=8, color=colors[1], label=labels[1])
        ax.plot(manufacturing_data['年份'], manufacturing_data[metric], marker='^', 
                linewidth=2, markersize=8, color=colors[2], label=labels[2])
        
        # 添加数值标签
        for j, row in parts_data.iterrows():
            ax.annotate(f'{row[metric]:.1f}', 
                       (row['年份'], row[metric]), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=colors[0])
        for j, row in vehicle_data.iterrows():
            ax.annotate(f'{row[metric]:.1f}', 
                       (row['年份'], row[metric]), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=colors[1])
        for j, row in manufacturing_data.iterrows():
            ax.annotate(f'{row[metric]:.1f}', 
                       (row['年份'], row[metric]), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color=colors[2])

    # 设置图表属性
    ax.set_title(f'{metric}(%)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel(f'{metric}(%)', fontsize=12)
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # 设置x轴刻度
    if files_exist:
        years = sorted(set(list(parts_filtered['年份']) + list(vehicle_filtered['年份']) + list(manufacturing_filtered['年份'])))
    else:
        years = sorted(set(list(parts_data['年份']) + list(vehicle_data['年份']) + list(manufacturing_data['年份'])))
    ax.set_xticks(years)

# 调整子图间距
plt.tight_layout(rect=[0, 0, 1, 0.93])

# 保存图表
plt.savefig('./下载数据/汽车行业财务指标对比分析.png', dpi=300, bbox_inches='tight')
print("\n图表已保存为 '汽车行业财务指标对比分析.png'")

# 显示图表
plt.show()

# 打印数据表用于参考
print("\n=== 汽车零部件及配件制造业数据 ===")
if files_exist:
    cols_to_show = ['年份'] + common_metrics
    filtered_cols = [col for col in cols_to_show if col in parts_data.columns]
    print(parts_data[filtered_cols].to_string(index=False))
else:
    print(parts_data.to_string(index=False))

print("\n=== 汽车整车制造业数据 ===")
if files_exist:
    cols_to_show = ['年份'] + common_metrics
    filtered_cols = [col for col in cols_to_show if col in vehicle_data.columns]
    print(vehicle_data[filtered_cols].to_string(index=False))
else:
    print(vehicle_data.to_string(index=False))

print("\n=== 汽车制造业数据 ===")
if files_exist:
    cols_to_show = ['年份'] + common_metrics
    filtered_cols = [col for col in cols_to_show if col in manufacturing_data.columns]
    print(manufacturing_data[filtered_cols].to_string(index=False))
else:
    print(manufacturing_data.to_string(index=False))