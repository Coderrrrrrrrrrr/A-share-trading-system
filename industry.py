import tushare as ts
import pandas as pd
import os
import efinance as ef
from daily_price import get_daily_price
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import candle_graph

class AShareIndex:
    def __init__(self):
        self.index_name = "汽车指数"
        self.index_code = "931008"
        self.data_dir = "下载数据"

        if not os.path.exists(os.path.join(self.data_dir, 'A股所有指数列表.xlsx')):
            self.get_a_share_index()
        else:
            print("A股所有指数列表.xlsx 文件已存在，跳过生成")

        self.get_top10_price()


    def get_a_share_index(self):
        # 1. 初始化Tushare接口（替换为你的token）
        ts.set_token("c2989fb9b4c3d466bf144c75b1ce0ece1c33f59443cf2ea90e51629c")
        pro = ts.pro_api()

        # 2. 获取A股所有指数列表（接口：index_basic）
        # market参数说明：
        # - 'SSE'：上交所指数，'SZSE'：深交所指数，'CSI'：中证指数，'CICC'：中金指数，'SW'：申万指数
        # - 不填market则返回所有市场的指数
        index_df = pro.index_basic(
            market='',  # 空字符串表示获取所有市场指数
            fields='ts_code,name,market,publisher,base_date,base_point'
        )

        # 3. 数据整理（筛选A股相关指数，排除港股/美股等）
        # A股指数的market字段多为'SSE'/'SZSE'/'CSI'/'SW'，可根据需求过滤
        a_share_index = index_df[
            index_df['market'].isin(['SSE', 'SZSE', 'CSI', 'SW', 'CICC'])
        ].copy()

        # 4. 重命名列（更直观）
        a_share_index.rename(
            columns={
                'ts_code': '指数TS代码',  # Tushare内部代码（部分场景用）
                'name': '指数名称',
                'market': '所属市场',
                'publisher': '发布机构',
                'base_date': '基期日期',
                'base_point': '基点'
            },
            inplace=True
        )

        # 5. 按「所属市场」排序，便于查看
        a_share_index = a_share_index.sort_values('所属市场').reset_index(drop=True)

        # 6. 输出结果（前10条示例）
        print("A股指数列表（前10条）：")
        print(a_share_index[['指数名称', '指数TS代码', '所属市场', '发布机构']].head(10))

        # 7. 保存到Excel（方便后续查看）
        a_share_index.to_excel(os.path.join(self.data_dir, 'A股所有指数列表.xlsx'), index=False, engine='openpyxl')
        print(f"\n共获取 {len(a_share_index)} 条A股指数，已保存到 Excel 文件")

    def compare_companies(self):
        # 获取指数成分股
        res = ef.stock.get_members(self.index_code)
        print(res.head(10))
        
        # 读取财务数据
        performance_data = pd.read_excel(os.path.join(self.data_dir, 'company_performance_pivot.xlsx'))
        
        # 根据股票名称合并数据（将指数成分股的"股票名称"与财务数据的"股票简称"进行匹配）
        merged_data = pd.merge(res, performance_data, left_on='股票名称', right_on='股票简称', how='left')
        
        # 保存到新的Excel文件
        filename = f'{self.index_name}成分股财务数据.xlsx'
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            print(f'{self.index_name}成分股财务数据.xlsx已存在，跳过生成')
        else:            
            merged_data.to_excel(filepath, index=False, engine='openpyxl')
            print(f"已生成{filename}")
            print(merged_data.head())

        return merged_data

    def get_top10_price(self):
        merged_data = self.compare_companies()
        top10_company = merged_data.sort_values('股票权重', ascending=False).head(10)
        
        # 为权重前10的公司获取各自股价数据
        for index, row in top10_company.iterrows():
            stock_code = str(row['股票代码_x'])
            stock_name = str(row['股票名称'])
            
            # 调用daily_price模块中的get_daily_price函数获取股价数据
            get_daily_price(stock_code=stock_code, stock_name=stock_name, data_dir=self.data_dir)
            # 调用candle_graph.Map_Drawing生成每只股票的蜡烛图
            candle_graph.Map_Drawing(stock_name=stock_name, stock_code=stock_code, data_dir=self.data_dir)
        
        # # 绘制10家公司的对比折线图
        # self.draw_candlestick_comparison(top10_company)



    def draw_candlestick_comparison(self, top10_company):
        """绘制10家公司的对比蜡烛图"""
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 创建一个大的图形
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # 为每家公司绘制收盘价曲线
        colors = plt.cm.get_cmap('tab10', 10)  # 使用不同的颜色
        
        for i, (index, row) in enumerate(top10_company.iterrows()):
            stock_code = str(row['股票代码_x'])
            stock_name = str(row['股票名称'])
            
            # 读取股价数据
            begin_date = '20240101'
            end_date = pd.Timestamp.now().strftime('%Y%m%d')
            filepath = os.path.join(self.data_dir, f'{stock_name}{begin_date}至{end_date}股价.xlsx')
            
            if os.path.exists(filepath):
                try:
                    data = pd.read_excel(filepath)
                    data['日期'] = pd.to_datetime(data['日期'])
                    data.set_index('日期', inplace=True)
                    
                    # 绘制收盘价
                    ax.plot(data.index, data['收盘'], label=f"{stock_name}", color=colors(i), linewidth=2)
                except Exception as e:
                    print(f"读取 {stock_name} 数据时出错: {e}")
            else:
                print(f"文件 {filepath} 不存在")
        
        # 设置图形属性
        ax.set_title(f"{self.index_name}权重前10公司收盘价对比", fontsize=16)
        ax.set_xlabel("日期", fontsize=12)
        ax.set_ylabel("收盘价 (元)", fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        # 格式化x轴日期显示
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 自动调整布局
        plt.tight_layout()
        
        # 保存图形
        comparison_chart_path = os.path.join(self.data_dir, f'{self.index_name}权重前10公司股价对比图.png')
        plt.savefig(comparison_chart_path, dpi=300, bbox_inches='tight')
        print(f"对比图已保存到 {comparison_chart_path}")
        
        # 显示图形
        plt.show()


if __name__ == '__main__':
    AShareIndex()