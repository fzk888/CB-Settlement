#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的TEMU平台数据验证脚本
分析原始TEMU数据文件并验证报表计算准确性
"""

import pandas as pd
import os
from pathlib import Path
import sys
from decimal import Decimal
from datetime import datetime

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser.temu_parser import TemuParser

def analyze_temu_files(data_root):
    """分析所有TEMU文件"""
    temu_parser = TemuParser()
    all_temu_data = []
    
    print("=== TEMU平台原始数据分析 ===")
    
    # 遍历所有月份目录
    months_dirs = [d for d in Path(data_root).iterdir() if d.is_dir() and '多平台收入' in d.name]
    months_dirs.sort(key=lambda x: int(x.name.split('-')[1].replace('月', '')))
    
    monthly_summary = {}
    
    for month_dir in months_dirs:
        month_name = month_dir.name
        month_num = int(month_name.split('-')[1].replace('月', ''))
        year_month = f"2025-{month_num:02d}"
        
        print(f"\n--- {month_name} ---")
        
        # 查找TEMU文件
        temu_files = list(month_dir.glob("*FundDetail*.xlsx"))
        
        if not temu_files:
            print("  未找到TEMU文件")
            continue
            
        month_total_revenue = Decimal('0')
        month_total_cost = Decimal('0')
        month_transactions = 0
        stores_in_month = []
        
        for temu_file in temu_files:
            store_name = temu_file.name.split(' FundDetail')[0]
            print(f"  处理店铺: {store_name}")
            
            try:
                transactions, meta = temu_parser.parse(str(temu_file))
                
                if transactions:
                    store_revenue = sum(t.total for t in transactions if t.total > 0)
                    store_cost = abs(sum(t.total for t in transactions if t.total < 0))
                    store_net = sum(t.total for t in transactions)
                    
                    print(f"    交易记录: {len(transactions)} 条")
                    print(f"    总收入: ${float(store_revenue):,.2f}")
                    print(f"    总成本: ${float(store_cost):,.2f}")
                    print(f"    净收入: ${float(store_net):,.2f}")
                    
                    month_total_revenue += store_revenue
                    month_total_cost += store_cost
                    month_transactions += len(transactions)
                    stores_in_month.append({
                        'store': store_name,
                        'revenue': float(store_revenue),
                        'cost': float(store_cost),
                        'net': float(store_net),
                        'transactions': len(transactions)
                    })
                    
                    # 保存详细数据用于后续验证
                    for txn in transactions:
                        all_temu_data.append({
                            'date': txn.date_time.strftime('%Y-%m-%d') if txn.date_time else '',
                            'store': store_name,
                            'month': year_month,
                            'type': txn.type.value,
                            'amount': float(txn.total),
                            'currency': txn.currency,
                            'order_id': txn.order_id
                        })
                else:
                    print(f"    无有效交易记录")
                    
            except Exception as e:
                print(f"    解析失败: {e}")
        
        monthly_summary[year_month] = {
            'revenue': float(month_total_revenue),
            'cost': float(month_total_cost),
            'net': float(month_total_revenue - month_total_cost),
            'transactions': month_transactions,
            'stores': stores_in_month
        }
        
        print(f"  {month_name} 总计:")
        print(f"    总收入: ${float(month_total_revenue):,.2f}")
        print(f"    总成本: ${float(month_total_cost):,.2f}")
        print(f"    净收入: ${float(month_total_revenue - month_total_cost):,.2f}")
        print(f"    交易总数: {month_transactions}")
    
    return monthly_summary, all_temu_data

def load_report_data(report_path):
    """加载报表数据"""
    try:
        xls = pd.ExcelFile(report_path)
        report_data = {}
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            report_data[sheet_name] = df
            
        return report_data
    except Exception as e:
        print(f"加载报表失败: {e}")
        return None

def extract_temu_from_report(report_data):
    """从报表中提取TEMU数据"""
    temu_report_data = {}
    
    for sheet_name, df in report_data.items():
        if '店铺月度汇总' in sheet_name:
            temu_rows = df[df['店铺'].str.contains('TEMU', case=False, na=False)]
            if not temu_rows.empty:
                temu_report_data['monthly_summary'] = temu_rows
                
        elif '详细交易记录' in sheet_name:
            temu_transactions = df[df['店铺'].str.contains('TEMU', case=False, na=False)]
            if not temu_transactions.empty:
                temu_report_data['detailed_records'] = temu_transactions
    
    return temu_report_data

def compare_data(original_summary, report_temu_data):
    """对比原始数据与报表数据"""
    print("\n" + "="*60)
    print("TEMU平台数据准确性验证结果")
    print("="*60)
    
    report_summary = report_temu_data.get('monthly_summary')
    if report_summary is None or report_summary.empty:
        print("✗ 报表中未找到TEMU数据")
        return False
    
    print("\n原始数据 vs 报表数据对比:")
    print("-" * 80)
    print(f"{'月份':<10} {'原始收入':<15} {'报表收入':<15} {'差异':<12} {'状态'}")
    print("-" * 80)
    
    total_matches = 0
    total_compared = 0
    
    for year_month, original_data in original_summary.items():
        # 在报表中查找对应月份的数据
        report_month_data = report_summary[report_summary['月份'] == year_month]
        
        if report_month_data.empty:
            print(f"{year_month:<10} ${original_data['revenue']:<14,.2f} {'未找到':<15} {'N/A':<12} {'✗ 缺失'}")
            continue
            
        original_revenue = original_data['revenue']
        report_revenue = report_month_data['总收入'].iloc[0]
        diff = abs(original_revenue - report_revenue)
        tolerance = 0.01  # 允许的小数点差异
        
        status = "✓ 匹配" if diff <= tolerance else "✗ 不匹配"
        if diff <= tolerance:
            total_matches += 1
        total_compared += 1
            
        print(f"{year_month:<10} ${original_revenue:<14,.2f} ${report_revenue:<14,.2f} ${diff:<11,.2f} {status}")
    
    print("-" * 80)
    match_rate = (total_matches / total_compared * 100) if total_compared > 0 else 0
    print(f"匹配率: {total_matches}/{total_compared} ({match_rate:.1f}%)")
    
    if match_rate >= 95:
        print("✓ TEMU平台数据计算基本准确")
        return True
    else:
        print("✗ TEMU平台数据存在显著差异")
        return False

def main():
    """主函数"""
    print("开始TEMU平台详细数据验证...")
    
    # 设置路径
    data_root = r"d:\app\收入核算系统\data\部分店铺收入\多平台"
    report_path = r"d:\app\收入核算系统\output\月度核算报表_Phase1_多平台.xlsx"
    
    # 1. 分析原始TEMU数据
    print("\n1. 分析原始TEMU数据...")
    original_summary, detailed_data = analyze_temu_files(data_root)
    
    # 2. 保存详细数据到CSV用于进一步分析
    if detailed_data:
        df_detailed = pd.DataFrame(detailed_data)
        detail_output = r"d:\app\收入核算系统\output\temu_detailed_analysis.csv"
        df_detailed.to_csv(detail_output, index=False, encoding='utf-8-sig')
        print(f"\n详细数据已保存到: {detail_output}")
    
    # 3. 加载报表数据
    print("\n2. 加载报表数据...")
    report_data = load_report_data(report_path)
    if not report_data:
        return
    
    # 4. 提取报表中的TEMU数据
    print("\n3. 提取报表中的TEMU数据...")
    report_temu_data = extract_temu_from_report(report_data)
    
    # 5. 对比验证
    print("\n4. 数据对比验证...")
    is_accurate = compare_data(original_summary, report_temu_data)
    
    # 输出总结
    print("\n" + "="*60)
    print("验证总结:")
    print(f"- 原始数据月份: {len(original_summary)} 个月")
    print(f"- 报表数据月份: {len(report_temu_data.get('monthly_summary', [])) if 'monthly_summary' in report_temu_data else 0} 个月")
    print(f"- 数据准确性: {'✓ 准确' if is_accurate else '✗ 存在问题'}")
    print("="*60)

if __name__ == "__main__":
    main()