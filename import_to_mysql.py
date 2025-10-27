import pandas as pd
import os
import re
import pymysql
from sqlalchemy import create_engine
import warnings

warnings.filterwarnings('ignore')

# 数据库连接配置 - 请根据实际情况修改
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'cxtx1028',  # 请修改为实际密码
    'database': 'quant',
    'charset': 'utf8mb4'
}

def create_database_and_table():
    """创建数据库和数据表"""
    try:
        # 连接数据库（不指定数据库名）
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("请检查数据库是否运行以及连接配置是否正确")
        return False
    
    try:
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute("CREATE DATABASE IF NOT EXISTS quant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            connection.commit()
            
            # 使用quant数据库
            cursor.execute("USE quant")
            
            # 创建股票数据表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS stock_data (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
                stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
                trade_date DATE NOT NULL COMMENT '交易日期',
                open_price DECIMAL(10, 4) NOT NULL COMMENT '开盘价',
                close_price DECIMAL(10, 4) NOT NULL COMMENT '收盘价',
                high_price DECIMAL(10, 4) NOT NULL COMMENT '最高价',
                low_price DECIMAL(10, 4) NOT NULL COMMENT '最低价',
                volume BIGINT NOT NULL COMMENT '成交量',
                turnover DECIMAL(15, 4) NOT NULL COMMENT '成交额',
                amplitude DECIMAL(10, 4) NOT NULL COMMENT '振幅',
                change_percent DECIMAL(10, 4) NOT NULL COMMENT '涨跌幅',
                change_amount DECIMAL(10, 4) NOT NULL COMMENT '涨跌额',
                turnover_rate DECIMAL(10, 4) NOT NULL COMMENT '换手率',
                UNIQUE KEY unique_stock_date (stock_name, stock_code, trade_date),
                INDEX idx_trade_date (trade_date),
                INDEX idx_stock_name (stock_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票交易数据表'
            """
            cursor.execute(create_table_sql)
            connection.commit()
            
        print("数据库和数据表创建成功")
        connection.close()
        return True
    except Exception as e:
        print(f"创建数据库和数据表时出错: {e}")
        connection.close()
        return False

def clean_stock_name(stock_name):
    """清理股票名称中的特殊字符"""
    # 移除不允许的文件名字符
    cleaned_name = re.sub(r'[\\/:*?"<>|]', '', stock_name)
    return cleaned_name

def import_excel_files_to_mysql():
    """将Excel文件导入MySQL数据库"""
    try:
        # 创建数据库连接引擎
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
        
        # Excel文件目录
        data_dir = os.path.join('下载数据', '沪深京所有股票价格')
        
        # 检查目录是否存在
        if not os.path.exists(data_dir):
            print(f"目录 {data_dir} 不存在，请检查路径")
            return
        
        # 获取目录中所有Excel文件
        excel_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
        
        print(f"找到 {len(excel_files)} 个Excel文件")
        
        # 统计信息
        total_files = len(excel_files)
        processed_files = 0
        skipped_files = 0
        error_files = 0
        
        for file_name in excel_files:
            try:
                # 解析文件名获取股票名称
                # 文件名格式: {股票名称}20240101至20251027股价.xlsx
                stock_name = file_name.replace('20240101至20251027股价.xlsx', '')
                # 清理股票名称
                stock_name = clean_stock_name(stock_name)
                
                # 读取Excel文件
                file_path = os.path.join(data_dir, file_name)
                df = pd.read_excel(file_path)
                
                # 检查是否有数据
                if df.empty:
                    print(f"文件 {file_name} 没有数据，跳过")
                    continue
                
                # 确保df是DataFrame类型
                df = pd.DataFrame(df)
                
                # 重命名列以匹配数据库字段
                column_mapping = {
                    '日期': 'trade_date',
                    '开盘': 'open_price',
                    '收盘': 'close_price',
                    '最高': 'high_price',
                    '最低': 'low_price',
                    '成交量': 'volume',
                    '成交额': 'turnover',
                    '振幅': 'amplitude',
                    '涨跌幅': 'change_percent',
                    '涨跌额': 'change_amount',
                    '换手率': 'turnover_rate'
                }
                
                # 应用列名映射
                df.rename(columns=column_mapping, inplace=True)
                
                # 添加股票名称和股票代码列
                # 从Excel数据中获取股票代码
                stock_code = ''
                if '股票代码' in df.columns:
                    # 从数据中获取第一个股票代码
                    stock_code = str(df['股票代码'].iloc[0])
                
                # 如果没有股票代码，跳过该文件
                if not stock_code:
                    print(f"文件 {file_name} 缺少股票代码，跳过")
                    skipped_files += 1
                    continue
                
                df['stock_name'] = stock_name
                df['stock_code'] = stock_code
                
                # 确保股票代码列是字符串类型，并且长度为6位，不足的前面补0
                df['stock_code'] = df['stock_code'].apply(lambda x: str(x).zfill(6))
                
                # 更新stock_code变量以确保后续使用处理后的代码
                stock_code = str(stock_code).zfill(6)
                
                # 确保日期列是日期类型
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                
                # 检查数据库中是否已存在该股票的最新数据
                check_query = "SELECT MAX(trade_date) as latest_date FROM stock_data WHERE stock_code = %s"
                latest_date_df = pd.read_sql(check_query, engine, params=(stock_code,))
                
                if not latest_date_df.empty and latest_date_df['latest_date'].iloc[0] is not None:
                    latest_date = latest_date_df['latest_date'].iloc[0]
                    # 确保latest_date是datetime类型，以便与df['trade_date']比较
                    if not pd.isna(latest_date):
                        latest_date = pd.to_datetime(latest_date)
                        # 过滤掉数据库中已存在的日期数据
                        df = df[df['trade_date'] > latest_date]
                    
                    # 如果没有新数据，跳过该文件
                    if df.empty:
                        print(f"文件 {file_name} 中没有新的数据需要导入，跳过")
                        skipped_files += 1
                        continue
                
                # 重新排序列以匹配数据库表结构
                df = df[['stock_name', 'stock_code', 'trade_date', 'open_price', 'close_price', 
                         'high_price', 'low_price', 'volume', 'turnover', 'amplitude',
                         'change_percent', 'change_amount', 'turnover_rate']]
                
                # 将数据导入数据库
                df.to_sql('stock_data', con=engine, if_exists='append', index=False, method='multi')
                
                processed_files += 1
                print(f"已处理文件 ({processed_files}/{total_files}): {file_name}")
                
            except Exception as e:
                error_files += 1
                print(f"处理文件 {file_name} 时出错: {e}")
                print(f"错误详情: {type(e).__name__}: {str(e)}")
        
        print(f"导入完成。成功处理: {processed_files} 个文件, 跳过: {skipped_files} 个文件, 出错: {error_files} 个文件")
    except Exception as e:
        print(f"连接数据库时出错: {e}")
        print("请检查数据库连接配置")


if __name__ == "__main__":
    # 创建数据库和表
    if create_database_and_table():
        # 导入Excel文件到MySQL
        import_excel_files_to_mysql()
        
    else:
        print("数据库初始化失败，程序退出")