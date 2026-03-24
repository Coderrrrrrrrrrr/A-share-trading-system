import pandas as pd
import re
import sys

def process_stock_data(excel_file_path):
    """
    处理股票数据Excel文件
    1. 提取"股票代码"列数据
    2. 将"."前的六位数字转换为字符串
    3. 将"."后的字母转换为汉字(BJ->北交所, SZ->深A, SH->沪A)
    4. 填入"市场类型"列
    """
    # 读取Excel文件
    df = pd.read_excel(excel_file_path)
    
    # 确保有"股票代码"列
    if '股票代码' not in df.columns:
        raise ValueError("Excel文件中没有找到'股票代码'列")
    
    # 如果没有"市场类型"列，则添加
    if '市场类型' not in df.columns:
        df['市场类型'] = ''
    else:
        # 确保"市场类型"列是字符串类型
        df['市场类型'] = df['市场类型'].astype(str)
    
    # 定义转换字典
    market_mapping = {
        'BJ': '北交所',
        'SZ': '深A',
        'SH': '沪A'
    }
    
    # 处理每一行数据
    for index, row in df.iterrows():
        stock_code = str(row['股票代码'])
        
        # 使用正则表达式匹配格式如 000001.SZ 的代码
        match = re.match(r'^(\d{6})\.([A-Z]+)$', stock_code)
        if match:
            # 提取六位数字和市场代码
            stock_number = match.group(1)
            market_code = match.group(2)
            
            # 转换市场代码为汉字
            if market_code in market_mapping:
                df.at[index, '市场类型'] = market_mapping[market_code]
                
            # 将股票代码更新为纯数字格式（去除市场代码部分）
            df.at[index, '股票代码'] = stock_number
    
    # 生成新文件名
    file_name_parts = excel_file_path.rsplit('.', 1)
    new_file_path = f"{file_name_parts[0]}_processed.{file_name_parts[1]}"
    
    # 保存处理后的数据到新文件
    df.to_excel(new_file_path, index=False)
    
    print(f"处理完成，结果已保存到: {new_file_path}")
    return new_file_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python insert_miss_data.py <excel文件路径>")
        sys.exit(1)
    
    excel_file_path = sys.argv[1]
    process_stock_data(excel_file_path)