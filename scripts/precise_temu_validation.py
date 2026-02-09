#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确的TEMU平台数据验证脚本
逐月对比原始数据与报表中的TEMU计算结果
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

def calculate_original_temu_by_month(data_root):
    """按月份计算原始TEMU数据"""
    temu_parser = TemuParser()
    monthly_data = {}
    
    print("=== 按月份计算原始TEMU数据 ===")
    
    # 遍历所有月份目录
    months_dirs = [d for d in Path(data_root).iterdir() if d.is_dir() and '多平台收入' in d.name]
    months_dirs.sort(key=lambda x: int(x.name.split('-')[1].replace('月', '')))
    
    for month_dir in months_dirs:
        month_name = month_dir.name
        month_num = int(month_name.split('-')[1].replace('月', ''))
        year_month = f"2025-{month_num:02d}"
        
        print(f"\n处理 {month_name} ({year_month}):")
        
        # 查找TEMU文件
        temu_files = list(month_dir.glob("*FundDetail*.xlsx"))
        
        if not temu_files:
            print("  未找到TEMU文件")
            continue
            
        month_total = Decimal('0')
        month_revenue = Decimal('0')
        month_cost = Decimal('0')
        store_details = []
        
        for temu_file in temu_files:
            store_name = temu_file.name.split(' FundDetail')[0]
            
            try:
                transactions, meta = temu_parser.parse(str(temu_file))
                
                if transactions:
                    store_total = sum(t.total for t in transactions)
                    store_revenue = sum(t.total for t in transactions if t.total > 0)
                    store_cost = abs(sum(t.total for t in transactions if t.total < 0))
                    
                    month_total += store_total
                    month_revenue += store_revenue
                    month_cost += store_cost
                    
                    store_details.append({
                        'store': store_name,
                        'total': float(store_total),
                        'revenue': float(store_revenue),
                        'cost': float(store_cost),
                        'transactions': len(transactions),
                        'currency': meta.get('currency', 'Unknown')
                    })
                    
                    print(f"  {store_name}: ${float(store_total):,.2f} ({len(transactions)}条)")
                else:
                    print(f"  {store_name}: 无数据")
                    
            except Exception as e:
                print(f"  {store_name}: 解析失败 - {e}")
        
        monthly_data[year_month] = {
            'total': float(month_total),
            'revenue': float(month_revenue),
            'cost': float(month_cost),
            'net': float(month_revenue - month_cost),
            'transactions': sum(d['transactions'] for d in store_details),
            'stores': store_details
        }
        
        print(f"  {month_name} 总计: ${float(month_total):,.2f}")
        print(f"  交易总数: {sum(d['transactions'] for d in store_details)}")
    
    return monthly_data

def load_report_temu_data(report_path):
    """从报表中加载TEMU数据"""
    try:
        # 读取详细数据表
        df_detail = pd.read_excel(report_path, '详细数据')
        temu_detail = df_detail[df_detail['平台'] == 'temu']
        
        # 读取平台汇总表
        df_summary = pd.read_excel(report_path, '平台汇总')
        temu_summary = df_summary[df_summary['platform'] == 'temu']
        
        print("\n=== 报表中的TEMU数据 ===")
        print("详细数据记录数:", len(temu_detail))
        print("平台汇总记录数:", len(temu_summary))
        
        # 按月份整理详细数据
        report_monthly = {}
        for _, row in temu_detail.iterrows():
            month = str(row['月份'])
            if month not in report_monthly:
                report_monthly[month] = {
                    'total': 0,
                    'transactions': 0,
                    'stores': []
                }
            
            report_monthly[month]['total'] += row['平台净结算']
            report_monthly[month]['transactions'] += row['交易数']
            report_monthly[month]['stores'].append({
                'store': row['店铺'],
                'total': row['平台净结算'],
                'transactions': row['交易数'],
                'currency': row['币种']
            })
        
        # 显示平台汇总数据
        print("\n平台汇总详情:")
        for _, row in temu_summary.iterrows():
            currency = row['currency'] if pd.notna(row['currency']) else 'Unknown'
            print(f"  {currency}: ${row['net_settlement']:,.2f} ({row['total_records']}条)")
        
        return report_monthly, temu_summary
        
    except Exception as e:
        print(f"加载报表数据失败: {e}")
        return {}, None

def compare_temu_data(original_monthly, report_monthly, report_summary):
    """对比原始数据与报表数据"""
    print("\n" + "="*80)
    print("TEMU平台数据准确性验证报告")
    print("="*80)
    
    print("\n逐月对比分析:")
    print("-" * 100)
    print(f"{'月份':<12} {'原始总计':<15} {'报表总计':<15} {'差异':<15} {'状态'}")
    print("-" * 100)
    
    total_matches = 0
    total_compared = 0
    total_original = 0
    total_report = 0
    
    # 获取所有月份
    all_months = set(list(original_monthly.keys()) + list(report_monthly.keys()))
    sorted_months = sorted(all_months)
    
    for month in sorted_months:
        orig_data = original_monthly.get(month)
        report_data = report_monthly.get(month)
        
        if orig_data and report_data:
            orig_total = orig_data['total']
            report_total = report_data['total']
            diff = abs(orig_total - report_total)
            tolerance = 0.01
            
            status = "✓ 匹配" if diff <= tolerance else "✗ 不匹配"
            if diff <= tolerance:
                total_matches += 1
            total_compared += 1
            
            total_original += orig_total
            total_report += report_total
            
            print(f"{month:<12} ${orig_total:<14,.2f} ${report_total:<14,.2f} ${diff:<14,.2f} {status}")
            
        elif orig_data:
            print(f"{month:<12} ${orig_data['total']:<14,.2f} {'未找到':<15} {'N/A':<15} {'✗ 缺失'}")
        elif report_data:
            print(f"{month:<12} {'未找到':<15} ${report_data['total']:<14,.2f} {'N/A':<15} {'✗ 多余'}")
    
    print("-" * 100)
    match_rate = (total_matches / total_compared * 100) if total_compared > 0 else 0
    print(f"匹配率: {total_matches}/{total_compared} ({match_rate:.1f}%)")
    print(f"原始数据总计: ${total_original:,.2f}")
    print(f"报表数据总计: ${total_report:,.2f}")
    print(f"总体差异: ${abs(total_original - total_report):,.2f}")
    
    # 验证币种分布
    print("\n币种分布验证:")
    print("-" * 50)
    if report_summary is not None:
        currency_totals = {}
        for _, row in report_summary.iterrows():
            currency = row['currency'] if pd.notna(row['currency']) else 'Unknown'
            currency_totals[currency] = row['net_settlement']
        
        print("报表币种分布:")
        for currency, amount in currency_totals.items():
            print(f"  {currency}: ${amount:,.2f}")
    
    print("\n" + "="*80)
    if match_rate >= 95 and abs(total_original - total_report) <= 0.01:
        print("✓ TEMU平台数据计算准确")
        return True
    else:
        print("✗ TEMU平台数据存在差异")
        return False

def main():
    """主函数"""
    print("开始TEMU平台精确数据验证...")
    
    # 设置路径
    data_root = r"d:\app\收入核算系统\data\部分店铺收入\多平台"
    report_path = r"d:\app\收入核算系统\output\月度核算报表_Phase1_多平台.xlsx"
    
    # 1. 计算原始TEMU数据
    print("\n1. 计算原始TEMU数据...")
    original_monthly = calculate_original_temu_by_month(data_root)
    
    # 2. 加载报表TEMU数据
    print("\n2. 加载报表TEMU数据...")
    report_monthly, report_summary = load_report_temu_data(report_path)
    
    # 3. 对比验证
    print("\n3. 数据对比验证...")
    is_accurate = compare_temu_data(original_monthly, report_monthly, report_summary)
    
    # 输出最终结论
    print("\n验证结论:")
    print(f"- 原始数据月份: {len(original_monthly)}")
    print(f"- 报表数据月份: {len(report_monthly)}")
    print(f"- 数据准确性: {'✓ 准确' if is_accurate else '✗ 存在问题'}")

if __name__ == "__main__":
    main()