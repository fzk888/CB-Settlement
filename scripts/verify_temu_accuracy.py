#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEMU平台数据准确性验证脚本
对比原始TEMU数据文件与最终报表中的计算结果
"""

import pandas as pd
import os
from pathlib import Path
import sys
from datetime import datetime

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser.temu_parser import TemuParser
from calculator.revenue_calculator import RevenueCalculator

def load_report_data(report_path):
    """加载报表数据"""
    try:
        # 读取所有工作表
        xls = pd.ExcelFile(report_path)
        report_data = {}
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            report_data[sheet_name] = df
            
        print(f"✓ 成功加载报表文件: {report_path}")
        print(f"  工作表数量: {len(xls.sheet_names)}")
        print(f"  工作表名称: {xls.sheet_names}")
        
        return report_data
    except Exception as e:
        print(f"✗ 加载报表文件失败: {e}")
        return None

def extract_temu_from_report(report_data):
    """从报表中提取TEMU相关数据"""
    temu_data = {}
    
    # 查找包含TEMU的店铺名称
    for sheet_name, df in report_data.items():
        if '店铺月度汇总' in sheet_name:
            # 查找TEMU相关的行
            temu_rows = df[df['店铺'].str.contains('TEMU', case=False, na=False)]
            if not temu_rows.empty:
                temu_data['店铺月度汇总'] = temu_rows
                print(f"\n=== 店铺月度汇总中的TEMU数据 ===")
                print(temu_rows[['店铺', '月份', '币种', '总收入', '总成本', '净收入']].to_string())
                
        elif '详细交易记录' in sheet_name:
            # 查找TEMU相关的交易记录
            temu_transactions = df[df['店铺'].str.contains('TEMU', case=False, na=False)]
            if not temu_transactions.empty:
                temu_data['详细交易记录'] = temu_transactions
                print(f"\n=== 详细交易记录中的TEMU数据 ===")
                print(f"交易记录数量: {len(temu_transactions)}")
                print(temu_transactions.head(10)[['日期', '店铺', '币种', '收入', '成本', '净收入']].to_string())
    
    return temu_data

def parse_original_temu_files(data_root):
    """解析原始TEMU数据文件"""
    temu_parser = TemuParser()
    all_temu_transactions = []
    
    # 遍历所有月份目录
    months_dirs = [d for d in Path(data_root).iterdir() if d.is_dir() and '多平台收入' in d.name]
    
    print(f"\n=== 解析原始TEMU文件 ===")
    print(f"找到月份目录: {[d.name for d in months_dirs]}")
    
    for month_dir in months_dirs:
        month_name = month_dir.name
        print(f"\n处理 {month_name}:")
        
        # 查找TEMU文件
        temu_files = list(month_dir.glob("*TEMU*.csv"))
        if not temu_files:
            temu_files = list(month_dir.glob("*temu*.csv"))
            
        if temu_files:
            for temu_file in temu_files:
                print(f"  解析文件: {temu_file.name}")
                try:
                    transactions = temu_parser.parse(str(temu_file))
                    if transactions:
                        print(f"    成功解析 {len(transactions)} 条记录")
                        all_temu_transactions.extend(transactions)
                    else:
                        print(f"    无有效交易记录")
                except Exception as e:
                    print(f"    解析失败: {e}")
        else:
            print(f"  未找到TEMU文件")
    
    return all_temu_transactions

def calculate_temu_summary(transactions):
    """计算TEMU数据汇总"""
    if not transactions:
        return None
    
    # 按店铺和月份分组
    store_monthly_data = {}
    
    for transaction in transactions:
        key = (transaction.store_name, transaction.month.strftime('%Y-%m'))
        if key not in store_monthly_data:
            store_monthly_data[key] = {
                'transactions': [],
                'total_revenue': 0,
                'total_cost': 0,
                'currency': transaction.currency
            }
        store_monthly_data[key]['transactions'].append(transaction)
        store_monthly_data[key]['total_revenue'] += transaction.revenue
        store_monthly_data[key]['total_cost'] += transaction.cost
    
    # 计算净收入
    for data in store_monthly_data.values():
        data['net_income'] = data['total_revenue'] - data['total_cost']
    
    return store_monthly_data

def compare_temu_data(original_summary, report_temu_data):
    """对比原始数据与报表数据"""
    print("\n" + "="*60)
    print("TEMU平台数据准确性验证报告")
    print("="*60)
    
    if not original_summary:
        print("✗ 未找到原始TEMU数据")
        return False
    
    if not report_temu_data:
        print("✗ 未找到报表中的TEMU数据")
        return False
    
    # 获取报表中的TEMU汇总数据
    report_summary = report_temu_data.get('店铺月度汇总')
    if report_summary is None or report_summary.empty:
        print("✗ 报表中未找到TEMU店铺月度汇总数据")
        return False
    
    print(f"\n原始数据统计:")
    print(f"  店铺-月份组合数: {len(original_summary)}")
    for (store, month), data in original_summary.items():
        print(f"  {store} ({month}):")
        print(f"    原始总收入: ${data['total_revenue']:,.2f}")
        print(f"    原始总成本: ${data['total_cost']:,.2f}")
        print(f"    原始净收入: ${data['net_income']:,.2f}")
        print(f"    交易记录数: {len(data['transactions'])}")
    
    print(f"\n报表数据统计:")
    for _, row in report_summary.iterrows():
        store = row['店铺']
        month = str(row['月份'])
        currency = row['币种']
        total_revenue = row['总收入']
        total_cost = row['总成本']
        net_income = row['净收入']
        
        print(f"  {store} ({month}):")
        print(f"    报表总收入: ${total_revenue:,.2f}")
        print(f"    报表总成本: ${total_cost:,.2f}")
        print(f"    报表净收入: ${net_income:,.2f}")
        
        # 查找对应的原始数据进行对比
        original_key = None
        for key in original_summary.keys():
            if store in key[0] and month in key[1]:
                original_key = key
                break
        
        if original_key:
            original_data = original_summary[original_key]
            revenue_diff = abs(total_revenue - original_data['total_revenue'])
            cost_diff = abs(total_cost - original_data['total_cost'])
            income_diff = abs(net_income - original_data['net_income'])
            
            print(f"    ↔ 收入差异: ${revenue_diff:,.2f}")
            print(f"    ↔ 成本差异: ${cost_diff:,.2f}")
            print(f"    ↔ 净收入差异: ${income_diff:,.2f}")
            
            # 判断是否匹配（允许小数点后2位的差异）
            tolerance = 0.01
            if (revenue_diff <= tolerance and 
                cost_diff <= tolerance and 
                income_diff <= tolerance):
                print(f"    ✓ 数据匹配")
            else:
                print(f"    ✗ 数据不匹配")
                return False
        else:
            print(f"    ? 未找到对应的原始数据")
    
    return True

def main():
    """主函数"""
    print("开始TEMU平台数据准确性验证...")
    
    # 设置路径
    data_root = r"d:\app\收入核算系统\data\部分店铺收入\多平台"
    report_path = r"d:\app\收入核算系统\output\月度核算报表_Phase1_多平台.xlsx"
    
    # 1. 加载报表数据
    print("\n1. 加载报表数据...")
    report_data = load_report_data(report_path)
    if not report_data:
        return
    
    # 2. 提取报表中的TEMU数据
    print("\n2. 提取报表中的TEMU数据...")
    report_temu_data = extract_temu_from_report(report_data)
    
    # 3. 解析原始TEMU文件
    print("\n3. 解析原始TEMU文件...")
    original_transactions = parse_original_temu_files(data_root)
    
    # 4. 计算原始数据汇总
    print("\n4. 计算原始数据汇总...")
    original_summary = calculate_temu_summary(original_transactions)
    
    # 5. 对比验证
    print("\n5. 数据对比验证...")
    is_accurate = compare_temu_data(original_summary, report_temu_data)
    
    # 输出最终结论
    print("\n" + "="*60)
    if is_accurate:
        print("✓ TEMU平台数据计算准确")
    else:
        print("✗ TEMU平台数据计算存在差异")
    print("="*60)

if __name__ == "__main__":
    main()