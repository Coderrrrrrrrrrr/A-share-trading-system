import pandas as pd
import os
import re
import pymysql
from sqlalchemy import create_engine, DECIMAL, BIGINT, DATE, String
import warnings
from datetime import datetime
import numpy as np

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

def read_excel_data(file_path):
    """读取Excel文件数据"""
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        print(f"成功读取Excel文件: {file_path}")
        print(f"数据形状: {df.shape}")
        print("列名:", df.columns.tolist())
        print("前5行数据:")
        print(df.head())
        return df
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return None

def process_excel_data(df, file_path):
    """处理Excel数据，转换为数据库表结构"""
    try:
        print("开始处理Excel数据...")
        # 获取股票代码和名称（从文件名或数据中）
        file_name = os.path.basename(file_path)
        stock_code = file_name.split('.')[0]  # 从文件名提取股票代码
        
        # 从数据中获取股票名称
        stock_name = df.iloc[0]['股票名称'] if '股票名称' in df.columns else stock_code
        
        print(f"股票代码: {stock_code}, 股票名称: {stock_name}")
        
        # 根据Excel结构处理数据
        # 前三列是元数据: 股票代码, 股票名称, 数据维度
        # 从第4列开始是日期数据
        
        # 获取日期列（从第4列开始）
        date_columns = df.columns[3:]  # 跳过前3列元数据列
        print(f"日期列数量: {len(date_columns)}")
        
        # 创建结果DataFrame
        result_data = []
        
        # 遍历每一行数据（每个数据维度）
        for index, row in df.iterrows():
            dimension = row['数据维度']
            
            # 遍历每个日期列
            for date_col in date_columns:
                if pd.notna(row[date_col]):  # 如果该日期有数据
                    # 创建一条记录
                    record = {
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'trade_date': date_col,  # 日期列名就是日期
                    }
                    
                    # 根据数据维度设置相应的值
                    if dimension == '开盘价':
                        record['open_price'] = row[date_col]
                    elif dimension == '收盘价':
                        record['close_price'] = row[date_col]
                    elif dimension == '最高价':
                        record['high_price'] = row[date_col]
                    elif dimension == '最低价':
                        record['low_price'] = row[date_col]
                    elif dimension == '成交量':
                        record['volume'] = row[date_col]
                    elif dimension == '成交额':
                        record['turnover'] = row[date_col]
                    elif dimension == '振幅':
                        record['amplitude'] = row[date_col]
                    elif dimension == '涨跌幅':
                        record['change_percent'] = row[date_col]
                    elif dimension == '涨跌':
                        record['change_amount'] = row[date_col]
                    elif dimension == '换手率':
                        record['turnover_rate'] = row[date_col]
                    
                    result_data.append(record)
        
        # 转换为DataFrame
        temp_df = pd.DataFrame(result_data)
        
        # 按股票代码、股票名称和交易日期分组，合并相同日期的记录
        processed_data = temp_df.groupby(['stock_code', 'stock_name', 'trade_date']).first().reset_index()
        
        # 用0填充缺失的数值列
        numeric_columns = ['open_price', 'close_price', 'high_price', 'low_price', 
                          'volume', 'turnover', 'amplitude', 'change_percent', 
                          'change_amount', 'turnover_rate']
        
        for col in numeric_columns:
            if col in processed_data.columns:
                processed_data[col] = processed_data[col].fillna(0)
            else:
                processed_data[col] = 0
        
        print("处理后的数据:")
        print(processed_data.head())
        print(f"处理完成，共 {len(processed_data)} 行数据")
        return processed_data
    except Exception as e:
        print(f"处理Excel数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def import_data_to_mysql(data_df):
    """将数据导入MySQL数据库"""
    try:
        # 创建数据库连接引擎
        engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
        
        # 导入数据到数据库
        data_df.to_sql('stock_data', con=engine, if_exists='append', index=False, 
                      dtype={
                          'stock_name': String(50),
                          'stock_code': String(20),
                          'trade_date': DATE,
                          'open_price': DECIMAL(10, 4),
                          'close_price': DECIMAL(10, 4),
                          'high_price': DECIMAL(10, 4),
                          'low_price': DECIMAL(10, 4),
                          'volume': BIGINT,
                          'turnover': DECIMAL(15, 4),
                          'amplitude': DECIMAL(10, 4),
                          'change_percent': DECIMAL(10, 4),
                          'change_amount': DECIMAL(10, 4),
                          'turnover_rate': DECIMAL(10, 4)
                      })
        print(f"成功导入 {len(data_df)} 条记录到数据库")
        return True
    except Exception as e:
        print(f"导入数据到数据库时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def extract_stock_info_from_excel(file_path):
    """从Excel文件名或内容中提取股票代码和名称"""
    # 从文件名提取股票代码
    file_name = os.path.basename(file_path)
    stock_code = file_name.split('.')[0]  # 假设文件名格式为 股票代码.xlsx
    
    # 股票名称需要从数据中获取或者手动设置
    stock_name = stock_code  # 默认使用股票代码作为名称
    
    return stock_code, stock_name

def main(excel_file_path):
    """主函数"""
    print(f"处理文件: {excel_file_path}")
    
    # 创建数据库和表
    if not create_database_and_table():
        print("创建数据库或表失败")
        return
    
    # 读取Excel数据
    df = read_excel_data(excel_file_path)
    if df is None:
        print("读取Excel数据失败")
        return
    
    # 处理数据
    processed_data = process_excel_data(df, excel_file_path)
    if processed_data is None:
        print("处理数据失败")
        return
    
    # 检查是否有有效数据
    if len(processed_data) == 0:
        print("没有有效的数据可以导入")
        return
    
    # 导入数据到数据库
    if import_data_to_mysql(processed_data):
        print("数据导入完成")
    else:
        print("数据导入失败")

if __name__ == "__main__":
    
    # Excel文件目录
    data_dir = os.path.join('下载数据', 'iFind表格拆分','split_tables')
    
    # 检查目录是否存在
    if not os.path.exists(data_dir):
        print(f"目录 {data_dir} 不存在，请检查路径")
        exit(1)
    
    # 获取目录中所有Excel文件
    excel_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
    
    print(f"找到 {len(excel_files)} 个Excel文件")
    
    # 统计信息
    total_files = len(excel_files)
    success_count = 0
    
    # 创建数据库和表（只需要执行一次）
    if not create_database_and_table():
        print("创建数据库或表失败")
        exit(1)
    
    for file_name in excel_files:
        file_path = os.path.join(data_dir, file_name)
        print(f"处理文件: {file_path}")
        
        # 读取Excel数据
        df = read_excel_data(file_path)
        if df is None:
            print(f"读取Excel数据失败: {file_path}")
            continue
        
        # 处理数据
        processed_data = process_excel_data(df, file_path)
        if processed_data is None:
            print(f"处理数据失败: {file_path}")
            continue
        
        # 检查是否有有效数据
        if len(processed_data) == 0:
            print(f"没有有效的数据可以导入: {file_path}")
            continue
        
        # 导入数据到数据库
        if import_data_to_mysql(processed_data):
            print(f"数据导入完成: {file_path}")
            success_count += 1
        else:
            print(f"数据导入失败: {file_path}")
    
    print(f"\n处理完成，总共 {total_files} 个文件，成功导入 {success_count} 个文件")