#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门验证All F Home店铺10月份TEMU数据准确性
"""

import pandas as pd
import os
from pathlib import Path
import sys
from decimal import Decimal

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser.temu_parser import TemuParser

def verify_all_f_home_october():
    """验证All F Home 10月份数据"""
    data_root = r"d:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月"
    temu_parser = TemuParser()
    
    print("=== All F Home 10月份TEMU数据详细验证 ===")
    
    # 查找All F Home的TEMU文件
    temu_files = list(Path(data_root).glob("*All F Home*FundDetail*.xlsx"))
    
    if not temu_files:
        print("✗ 未找到All F Home的TEMU文件")
        return
    
    file_path = temu_files[0]
    print(f"文件路径: {file_path}")
    
    try:
        # 解析文件
        transactions, meta = temu_parser.parse(str(file_path))
        
        print(f"\n文件元信息:")
        print(f"  店铺名: {meta.get('store_name')}")
        print(f"  年月: {meta.get('year_month')}")
        print(f"  币种: {meta.get('currency')}")
        print(f"  总记录数: {meta.get('total_records')}")
        
        if transactions:
            # 按交易类型分类统计
            type_stats = {}
            total_amount = Decimal('0')
            
            print(f"\n详细交易统计:")
            for txn in transactions:
                type_key = txn.type.value
                if type_key not in type_stats:
                    type_stats[type_key] = {'count': 0, 'amount': Decimal('0')}
                
                type_stats[type_key]['count'] += 1
                type_stats[type_key]['amount'] += txn.total
                total_amount += txn.total
            
            # 显示各类别统计
            for txn_type, stats in type_stats.items():
                print(f"  {txn_type}: {stats['count']} 条, 金额: ${float(stats['amount']):,.2f}")
            
            print(f"\n总计:")
            print(f"  交易记录数: {len(transactions)}")
            print(f"  总金额: ${float(total_amount):,.2f}")
            
            # 与报表数据对比
            report_amount = Decimal('5424.53')
            difference = abs(total_amount - report_amount)
            
            print(f"\n数据对比:")
            print(f"  原始计算: ${float(total_amount):,.2f}")
            print(f"  报表数值: ${float(report_amount):,.2f}")
            print(f"  差异: ${float(difference):,.2f}")
            
            if difference <= Decimal('0.01'):
                print("✓ 数据匹配准确")
            else:
                print("✗ 数据存在差异")
                
        else:
            print("✗ 未解析到有效交易记录")
            
    except Exception as e:
        print(f"✗ 解析失败: {e}")

def main():
    verify_all_f_home_october()

if __name__ == "__main__":
    main()