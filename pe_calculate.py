import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
from daily_price import get_daily_price

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def read_excel_data(file_path):
    """
    读取Excel文件数据
    """
    try:
        # 读取Excel文件的第一个工作表
        df = pd.read_excel(file_path, sheet_name=0)
        return df
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return None

def clean_and_convert_data(df):
    """
    清理和转换数据，将字符串格式的数字和百分比转换为数值
    """
    # 创建数据副本
    df_clean = df.copy()
    
    # 处理所有列，将包含千分位符和百分号的字符串转换为数值
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            # 将包含千分位符的数字转换为数值
            if df_clean[col].astype(str).str.contains(',').any():
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '').replace('', np.nan)
                # 尝试转换为数值
                df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
            
            # 将百分比转换为小数
            if df_clean[col].astype(str).str.contains('%').any():
                df_clean[col] = df_clean[col].astype(str).str.replace('%', '').replace('', np.nan)
                numeric_col = pd.to_numeric(df_clean[col], errors='coerce')
                # 除以100转换为小数
                df_clean[col] = pd.Series(numeric_col) / 100.0
    
    return df_clean

def plot_columns_bar_charts(df, output_dir='下载数据'):
    """
    为每一列生成柱状图，显示在同一个页面上
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取数值列（排除文本列）
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # 获取品牌名称列（使用证券简称列）
    brand_column = '证券简称'  # 明确指定品牌列名称
    
    if not numeric_columns or not brand_column:
        print("未找到有效的数据列")
        return
    
    # 过滤掉不需要的列（如证券代码等）
    columns_to_plot = [col for col in numeric_columns if col not in ['证券代码']]
    
    print(f"将绘制 {len(columns_to_plot)} 个指标的图表: {columns_to_plot}")
    
    # 设置图表
    n_cols = len(columns_to_plot)
    n_cols_per_row = 3  # 每行显示3个图表
    n_rows = (n_cols + n_cols_per_row - 1) // n_cols_per_row
    
    # 创建一个大的图表，包含所有子图
    fig, axes = plt.subplots(n_rows, n_cols_per_row, figsize=(20, 6*n_rows))
    fig.suptitle('比亚迪综合比较分析', fontsize=16, fontweight='bold')
    
    # 确保axes始终是一维数组
    if n_rows * n_cols_per_row == 1:
        axes = np.array([axes])
    elif n_rows > 1:
        axes = axes.flatten()
    else:
        axes = axes.reshape(-1)
    
    # 为每一列生成柱状图
    for i, column in enumerate(columns_to_plot):
        # 确定当前子图位置
        ax = axes[i]
        
        # 提取数据
        brands = df[brand_column].astype(str)
        values = df[column]
        
        # 绘制柱状图
        bars = ax.bar(range(len(brands)), values, color='skyblue')
        ax.set_title(column, fontsize=12)
        ax.set_xticks(range(len(brands)))
        ax.set_xticklabels(brands, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3)
        
        # 添加数值标签
        for bar, value in zip(bars, values):
            if pd.notna(value):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                       f'{value:.2f}' if isinstance(value, (int, float)) else str(value),
                       ha='center', va='bottom', fontsize=8)
    
    # 隐藏多余的子图
    total_subplots = n_rows * n_cols_per_row
    for i in range(n_cols, total_subplots):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '比亚迪综合比较分析.png'), dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"图表已保存到 {os.path.join(output_dir, '比亚迪综合比较分析.png')}")

def plot_price_pe_comparison():
    """
    绘制比亚迪股价和市盈率(TTM)对比图
    """
    # 获取比亚迪股价数据
    price_df = get_daily_price()
    
    # 读取估值分析明细Excel文件
    pe_file = r'e:\PycharmProject\量化交易\下载数据\比亚迪(002594.SZ)-估值分析明细.xlsx'
    pe_df = pd.read_excel(pe_file)
    
    # 确保日期列是datetime类型
    price_df['日期'] = pd.to_datetime(price_df['日期'])
    pe_df['日期'] = pd.to_datetime(pe_df['日期'])
    
    # 合并数据框，基于日期列
    merged_df = pd.merge(price_df, pe_df, on='日期', how='inner')
    
    if merged_df.empty:
        print("警告: 无法合并股价数据和市盈率数据，请检查日期范围是否匹配")
        return
    
    # 创建图形和双Y轴
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # 绘制股价（收盘价）
    color = 'tab:blue'
    ax1.set_xlabel('日期')
    ax1.set_ylabel('股价 (收盘价)', color=color)
    ax1.plot(merged_df['日期'], merged_df['收盘'], color=color, label='收盘价')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # 创建第二个Y轴用于市盈率
    ax2 = ax1.twinx()  # type: ignore
    color = 'tab:red'
    ax2.set_ylabel('市盈率(TTM)', color=color)
    ax2.plot(merged_df['日期'], merged_df['市盈率(TTM)'], color=color, label='市盈率(TTM)')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # 设置标题
    plt.title('比亚迪股价与市盈率(TTM)对比图', fontsize=16, fontweight='bold')
    
    # 添加图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # 格式化X轴日期显示
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_dir = '下载数据'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, '比亚迪股价与市盈率对比图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"股价与市盈率对比图已保存到 {output_path}")

def main():
    # Excel文件路径
    excel_file = r'e:\PycharmProject\量化交易\下载数据\比亚迪(002594.SZ)-综合比较.xls'
    
    # 读取数据
    df = read_excel_data(excel_file)
    if df is not None:
        print("数据读取成功:")
        print(df.head())
        print("\n数据列信息:")
        print(df.columns.tolist())
        
        # 清理和转换数据
        df_clean = clean_and_convert_data(df)
        
        print("\n清理后的数值列信息:")
        numeric_columns = df_clean.select_dtypes(include=[np.number]).columns.tolist()
        print(numeric_columns)
        
        # 显示每列的数据类型和示例值
        print("\n各列数据类型和示例:")
        for col in df_clean.columns:
            sample_value = df_clean[col].iloc[0] if len(df_clean) > 0 else "N/A"
            print(f"{col}: {df_clean[col].dtype} -> {sample_value}")
        
        # 生成图表
        plot_columns_bar_charts(df_clean)
    else:
        print("无法读取数据")
    
    # 绘制股价和市盈率对比图
    plot_price_pe_comparison()

if __name__ == "__main__":
    main()