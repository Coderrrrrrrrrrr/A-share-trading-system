import pandas as pd
import matplotlib.pyplot as plt
import os

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def read_sales_data(excel_path):
    """
    读取汽车销量数据
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"找不到文件: {excel_path}")
    
    # 读取Excel文件
    df = pd.read_excel(excel_path)
    return df

def plot_sales_by_month(dataframe, save_fig=False):
    """
    按月份绘制销量柱状图，每个图显示当月销量前10的品牌
    """
    # 确保日期列为datetime类型
    dataframe['日期'] = pd.to_datetime(dataframe['日期'])
    
    # 提取年月
    dataframe['年月'] = dataframe['日期'].dt.to_period('M')
    
    # 获取所有唯一月份
    months = sorted(dataframe['年月'].unique())
    
    # 创建图形布局
    fig, axes = plt.subplots(len(months), 1, figsize=(15, 5*len(months)))
    
    # 如果只有一个月份，axes不是数组形式，需要转换
    if len(months) == 1:
        axes = [axes]
    
    # 为每个月份绘制柱状图
    for i, month in enumerate(months):
        # 筛选当前月份的数据
        month_data = dataframe[dataframe['年月'] == month].copy()
        
        # 按销量排序，取前10个品牌
        top_brands = month_data.nlargest(10, '销量')
        
        # 打印调试信息
        print(f"正在绘制 {month} 的数据:")
        print(top_brands[['品牌', '销量']])
        print("-" * 30)
        
        # 绘制柱状图
        ax = axes[i]
        bars = ax.bar(range(len(top_brands)), top_brands['销量'], color='skyblue')
        
        # 设置标题和标签
        ax.set_title(f'{month} 汽车品牌销量排行榜 Top 10', fontsize=16, pad=20)
        ax.set_xlabel('品牌', fontsize=12)
        ax.set_ylabel('销量', fontsize=12)
        
        # 设置x轴标签
        ax.set_xticks(range(len(top_brands)))
        ax.set_xticklabels(top_brands['品牌'], rotation=0, ha='right')
        
        # 在柱子上显示数值
        for j, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=9)
        
        # 设置网格
        ax.grid(axis='y', alpha=0.3)
        
    # 调整布局避免重叠
    plt.tight_layout(pad=3.0)
    
    # 保存图像（可选）
    if save_fig:
        plt.savefig(r'e:\PycharmProject\量化交易\下载数据\汽车品牌月度销量.png', dpi=300, bbox_inches='tight')
        print("图表已保存至: e:\\PycharmProject\\量化交易\\下载数据\\汽车品牌月度销量.png")
    
    # 显示图表
    plt.show()

def main():
    # Excel文件路径
    excel_path = r'e:\PycharmProject\量化交易\下载数据\汽车品牌截至2025年9月销量数据.xlsx'
    
    try:
        # 读取数据
        sales_data = read_sales_data(excel_path)
        print("成功读取数据，共有 {} 行记录".format(len(sales_data)))
        print(sales_data.head(10))
        print("=" * 50)
        
        # 按月份绘制图表
        plot_sales_by_month(sales_data, save_fig=True)
        
    except Exception as e:
        print(f"处理数据时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()