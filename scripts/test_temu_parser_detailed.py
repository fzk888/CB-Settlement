#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试TEMU解析器对All F Home文件的解析结果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser.temu_parser import TemuParser
from decimal import Decimal

def test_parser():
    """测试解析器"""
    parser = TemuParser()
    file_path = r"d:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月\All F Home FundDetail-1762149595565-16b5.xlsx"
    
    print("=== TEMU解析器详细测试 ===")
    
    transactions, meta = parser.parse(file_path)
    
    print(f"解析元信息:")
    for key, value in meta.items():
        print(f"  {key}: {value}")
    
    print(f"\n交易记录详情:")
    type_summary = {}
    total_amount = Decimal('0')
    
    for i, txn in enumerate(transactions[:10]):  # 显示前10条
        txn_type = txn.type.value
        amount = txn.total
        
        if txn_type not in type_summary:
            type_summary[txn_type] = {'count': 0, 'total': Decimal('0')}
        
        type_summary[txn_type]['count'] += 1
        type_summary[txn_type]['total'] += amount
        total_amount += amount
        
        print(f"  {i+1}. 类型: {txn_type}, 金额: ${float(amount):.2f}, 订单: {txn.order_id}")
    
    # 统计所有记录
    full_type_summary = {}
    full_total = Decimal('0')
    for txn in transactions:
        txn_type = txn.type.value
        amount = txn.total
        if txn_type not in full_type_summary:
            full_type_summary[txn_type] = {'count': 0, 'total': Decimal('0')}
        full_type_summary[txn_type]['count'] += 1
        full_type_summary[txn_type]['total'] += amount
        full_total += amount
    
    print(f"\n完整统计:")
    for txn_type, stats in full_type_summary.items():
        print(f"  {txn_type}: {stats['count']} 条, ${float(stats['total']):.2f}")
    
    print(f"\n总计: ${float(full_total):.2f}")
    print(f"与报表对比 ($5434.53): 差异 ${float(abs(full_total - Decimal('5434.53'))):.2f}")

if __name__ == "__main__":
    test_parser()