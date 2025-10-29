import pandas as pd
import os
import re
import pymysql
from sqlalchemy import create_engine
import warnings
from datetime import datetime

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


def import_excel_file_to_mysql(file_path):
    """将指定Excel文件导入MySQL数据库"""
    try:
        # 创建数据库连接引擎
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"文件 {file_path} 不存在，请检查路径")
            return False
                
        # 读取Excel文件
        df = pd.read_excel(file_path)
                
        # 确保df是DataFrame类型
        df = pd.DataFrame(df)
        
        # 重命名列以匹配数据库字段
        column_mapping = {
            '股票代码': 'stock_code',
            '股票名称': 'stock_name',
            '最新交易日': 'trade_date',
            '今开': 'open_price',
            '最新价': 'close_price',
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
        
        # 确保股票代码列是字符串类型，并且长度为6位，不足的前面补0
        df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)
        
        # 确保日期列是日期类型
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        # 处理数值列，替换NaN值为0或其他默认值
        numeric_columns = ['open_price', 'close_price', 'high_price', 'low_price', 'volume', 
                          'turnover', 'amplitude', 'change_percent', 'change_amount', 'turnover_rate']
        
        for col in numeric_columns:
            if col in df.columns:
                # 替换NaN和无穷大值为0
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(0)
            else:
                # 如果列不存在，添加默认值
                df[col] = 0
        
        # 处理字符串列
        df['stock_name'] = df['stock_name'].fillna('未知').astype(str)
        
        # 检查数据库中已存在的股票代码
        existing_query = "SELECT DISTINCT stock_code FROM stock_data"
        existing_codes_df = pd.read_sql(existing_query, engine)
        
        # 确保df是pandas DataFrame类型
        df = pd.DataFrame(df)
        
        if not existing_codes_df.empty:
            existing_codes = existing_codes_df['stock_code'].tolist()
            # 分离已存在和新增的股票数据
            matched_df = df[df['stock_code'].isin(existing_codes)]
            unmatched_df = df[~df['stock_code'].isin(existing_codes)]
        else:
            matched_df = pd.DataFrame(columns=df.columns)
            unmatched_df = df
        
        # 打印未匹配的股票代码
        if len(unmatched_df) > 0:
            print("以下股票代码在原数据表中未找到:")
            unique_codes = pd.Series(unmatched_df['stock_code']).unique()
            for code in unique_codes:
                # 使用pandas方法获取第一个匹配项的名字
                name_row = unmatched_df[unmatched_df['stock_code'] == code]
                if len(name_row) > 0:
                    # 使用values[0]代替iloc[0]避免类型问题
                    name = pd.Series(name_row['stock_name']).values[0] 
                else:
                    name = "未知"
                print(f"  {code}: {name}")
            print("请确认是否需要添加这些新的股票代码到数据库中。")
        
        # 添加验证机制：检查数据库中已存在的股票代码和日期组合
        if len(df) > 0:
            # 构建查询语句，获取数据库中已存在的股票代码和日期组合
            existing_data_query = "SELECT stock_code, trade_date FROM stock_data"
            existing_data_df = pd.read_sql(existing_data_query, engine)
            
            # 如果数据库中已有数据，则过滤掉重复的数据
            if not existing_data_df.empty:
                # 将trade_date转换为日期格式以确保一致性
                existing_data_df['trade_date'] = pd.to_datetime(existing_data_df['trade_date'])
                
                # 创建一个集合来存储已存在的(code, date)组合
                existing_combinations = set(
                    zip(existing_data_df['stock_code'], existing_data_df['trade_date'].dt.strftime('%Y-%m-%d'))
                )
                
                # 过滤掉已存在的数据
                filtered_rows = []
                skipped_count = 0
                
                for index, row in df.iterrows():
                    code = row['stock_code']
                    # 使用pandas方法处理日期
                    date = pd.to_datetime(row['trade_date']).strftime('%Y-%m-%d')
                    
                    # 如果(code, date)组合不存在，则保留该行
                    if (code, date) not in existing_combinations:
                        filtered_rows.append(row)
                    else:
                        skipped_count += 1
                
                # 更新DataFrame
                df = pd.DataFrame(filtered_rows, columns=df.columns)
                if skipped_count > 0:
                    print(f"跳过了 {skipped_count} 条已存在的数据记录")
            else:
                print("数据库中没有已存在的数据记录")
        
        # 重新排序列以匹配数据库表结构
        required_columns = ['stock_name', 'stock_code', 'trade_date', 'open_price', 'close_price', 
                           'high_price', 'low_price', 'volume', 'turnover', 'amplitude',
                           'change_percent', 'change_amount', 'turnover_rate']
        
        # 选择需要的列
        df = df[required_columns]
        
        # 确保数据类型正确
        df['open_price'] = df['open_price'].astype('float')
        df['close_price'] = df['close_price'].astype('float')
        df['high_price'] = df['high_price'].astype('float')
        df['low_price'] = df['low_price'].astype('float')
        df['volume'] = df['volume'].astype('int64')
        df['turnover'] = df['turnover'].astype('float')
        df['amplitude'] = df['amplitude'].astype('float')
        df['change_percent'] = df['change_percent'].astype('float')
        df['change_amount'] = df['change_amount'].astype('float')
        df['turnover_rate'] = df['turnover_rate'].astype('float')
        
        # 将数据导入数据库
        if len(df) > 0:
            df.to_sql('stock_data', con=engine, if_exists='append', index=False, method='multi')
            print(f"成功导入文件 {file_path} 到数据库，共导入 {len(df)} 条记录")
        else:
            print("没有新数据需要导入")
        return True
                
    except Exception as e:
        print(f"导入文件时出错: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False



if __name__ == "__main__":
    
    end_date = datetime.now().strftime('%Y%m%d')

    import sys
    
    # 如果提供了命令行参数，则使用指定的Excel文件
    if len(sys.argv) > 1:
        excel_file_path = sys.argv[1]
    else:
        # 默认Excel文件路径
        excel_file_path = r'e:\PycharmProject\量化交易\下载数据\沪深京所有股票价格\沪深京{}最新股价.xlsx'.format(end_date)
    
    # 创建数据库和表
    if create_database_and_table():
        # 导入指定的Excel文件到MySQL
        success = import_excel_file_to_mysql(excel_file_path)
        if not success:
            print("数据导入失败")
    else:
        print("数据库初始化失败，程序退出")