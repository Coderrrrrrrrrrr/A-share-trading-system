import pandas as pd
import pymysql
from datetime import datetime
import numpy as np
import sys

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'cxtx1028',  # 请修改为实际密码
    'database': 'quant',
    'charset': 'utf8mb4'
}

def connect_to_database():
    """连接到数据库"""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset']
        )
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("请检查数据库是否运行以及连接配置是否正确")
        return None

def create_database_and_table(connection):
    """创建数据库和数据表"""
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
        return True
    except Exception as e:
        print(f"创建数据库和数据表时出错: {e}")
        return False

def check_if_record_exists(cursor, stock_name, stock_code, trade_date):
    """检查记录是否已存在"""
    check_sql = """
    SELECT COUNT(*) FROM stock_data 
    WHERE stock_name = %s AND stock_code = %s AND trade_date = %s
    """
    cursor.execute(check_sql, (stock_name, stock_code, trade_date))
    result = cursor.fetchone()
    return result[0] > 0

def import_excel_to_mysql(excel_file_path):
    """将Excel数据导入到MySQL数据库"""
    # 连接数据库
    connection = connect_to_database()
    if not connection:
        return False
    
    # 创建数据库和表
    if not create_database_and_table(connection):
        connection.close()
        return False
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file_path)
        print(f"成功读取Excel文件，共{len(df)}行数据")
        
        # 使用数据库
        with connection.cursor() as cursor:
            cursor.execute("USE quant")
        
        # 插入数据计数器
        inserted_count = 0
        skipped_count = 0
        
        # 遍历DataFrame中的每一行
        for index, row in df.iterrows():
            try:
                # 获取数据
                stock_name = str(row['股票名称']) if not pd.isna(row['股票名称']) else ''
                stock_code = str(row['股票代码']) if not pd.isna(row['股票代码']) else ''
                
                # 处理日期 (使用最新交易日作为交易日期)
                trade_date = row['最新交易日']
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
                elif hasattr(trade_date, 'date'):
                    trade_date = trade_date.date()
                
                # 数值字段处理
                open_price = 0.0
                if not pd.isna(row['今开']): 
                    try:
                        open_price = float(row['今开'])
                    except (ValueError, TypeError):
                        open_price = 0.0
                
                close_price = 0.0
                if not pd.isna(row['最新价']):
                    try:
                        close_price = float(row['最新价'])
                    except (ValueError, TypeError):
                        close_price = 0.0
                
                high_price = 0.0
                if not pd.isna(row['最高']):
                    try:
                        high_price = float(row['最高'])
                    except (ValueError, TypeError):
                        high_price = 0.0
                
                low_price = 0.0
                if not pd.isna(row['最低']):
                    try:
                        low_price = float(row['最低'])
                    except (ValueError, TypeError):
                        low_price = 0.0
                
                volume = 0
                if not pd.isna(row['成交量']):
                    try:
                        volume = int(float(row['成交量']))
                    except (ValueError, TypeError):
                        volume = 0
                
                # 成交额需要特殊处理，因为Excel中的单位是万元
                turnover = 0.0
                if not pd.isna(row['成交额(万元)']):
                    try:
                        turnover = float(row['成交额(万元)']) * 10000
                    except (ValueError, TypeError):
                        turnover = 0.0
                
                # 振幅需要计算，因为Excel中没有直接提供
                amplitude = 0.0
                if close_price != 0:
                    amplitude = ((high_price - low_price) / close_price * 100)
                
                change_percent = 0.0
                if not pd.isna(row['涨跌幅']):
                    try:
                        change_percent = float(row['涨跌幅'])
                    except (ValueError, TypeError):
                        change_percent = 0.0
                
                change_amount = 0.0
                if not pd.isna(row['涨跌额']):
                    try:
                        change_amount = float(row['涨跌额'])
                    except (ValueError, TypeError):
                        change_amount = 0.0
                
                turnover_rate = 0.0
                if not pd.isna(row['换手率']):
                    try:
                        turnover_rate = float(row['换手率'])
                    except (ValueError, TypeError):
                        turnover_rate = 0.0
                
                # 检查记录是否已存在
                with connection.cursor() as cursor:
                    if check_if_record_exists(cursor, stock_name, stock_code, trade_date):
                        print(f"跳过重复记录: {stock_name}({stock_code}) - {trade_date}")
                        skipped_count += 1
                        continue
                    
                    # 插入数据
                    insert_sql = """
                    INSERT INTO stock_data (
                        stock_name, stock_code, trade_date, open_price, close_price,
                        high_price, low_price, volume, turnover, amplitude,
                        change_percent, change_amount, turnover_rate
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (
                        stock_name, stock_code, trade_date, open_price, close_price,
                        high_price, low_price, volume, turnover, amplitude,
                        change_percent, change_amount, turnover_rate
                    ))
                
                inserted_count += 1
                
                # 每100条记录提交一次
                if (index + 1) % 100 == 0:
                    connection.commit()
                    print(f"已处理 {index + 1} 条记录...")
                    
            except Exception as row_error:
                print(f"处理第{index+1}行数据时出错: {row_error}")
                continue
        
        # 最后提交事务
        connection.commit()
        print(f"数据导入完成! 成功插入 {inserted_count} 条记录，跳过 {skipped_count} 条重复记录")
        
    except Exception as e:
        print(f"导入数据时出错: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python import_excel_to_mysql.py <excel文件路径>")
        sys.exit(1)
    
    excel_file_path = sys.argv[1]
    import_excel_to_mysql(excel_file_path)