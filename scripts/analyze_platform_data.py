# -*- coding: utf-8 -*-
"""
数据结构分析脚本
分析平台收入数据和仓库账单数据
"""
import csv
import io
import os
from decimal import Decimal, InvalidOperation
from collections import defaultdict, Counter
from pathlib import Path

def parse_decimal(s):
    """解析金额"""
    if not s or not s.strip():
        return Decimal('0')
    try:
        return Decimal(s.strip().replace(',', ''))
    except:
        return Decimal('0')

def analyze_amazon_csv(file_path):
    """分析Amazon CSV文件"""
    print(f"\n{'='*60}")
    print(f"分析文件: {Path(file_path).name}")
    print('='*60)
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    lines = content.split('\n')
    header_idx = -1
    for i, line in enumerate(lines):
        if 'date/time' in line.lower():
            header_idx = i
            break
    
    if header_idx < 0:
        print("未找到表头行")
        return None
    
    reader = csv.DictReader(io.StringIO('\n'.join(lines[header_idx:])))
    rows = list(reader)
    
    print(f"\n总记录数: {len(rows)}")
    
    # 1. type字段分布
    type_counter = Counter(row.get('type', '') for row in rows)
    print("\n【type字段值分布】")
    for t, count in type_counter.most_common():
        print(f"  {t if t else '(空)':35}: {count:>5} 条")
    
    # 2. 按type汇总total金额
    type_totals = defaultdict(Decimal)
    type_counts = defaultdict(int)
    
    for row in rows:
        t = row.get('type', '')
        total = parse_decimal(row.get('total', '0'))
        type_totals[t] += total
        type_counts[t] += 1
    
    print("\n【按type汇总total金额】")
    grand_total = Decimal('0')
    for t in sorted(type_totals.keys(), key=lambda x: float(type_totals[x]), reverse=True):
        total = type_totals[t]
        count = type_counts[t]
        grand_total += total
        t_name = t if t else '(空)'
        print(f"  {t_name:35} | {count:5} 条 | Total: {float(total):>12,.2f}")
    
    print(f"  {'-'*60}")
    print(f"  {'总计':35} | {len(rows):5} 条 | Total: {float(grand_total):>12,.2f}")
    
    # 3. 验证total计算公式
    print("\n【验证total计算公式 - 前3条Order】")
    count = 0
    for row in rows:
        if row.get('type') != 'Order':
            continue
        if count >= 3:
            break
        count += 1
        
        product_sales = parse_decimal(row.get('product sales', '0'))
        product_sales_tax = parse_decimal(row.get('product sales tax', '0'))
        postage_credits = parse_decimal(row.get('postage credits', '0'))
        shipping_credits_tax = parse_decimal(row.get('shipping credits tax', '0'))
        gift_wrap_credits = parse_decimal(row.get('gift wrap credits', '0'))
        giftwrap_credits_tax = parse_decimal(row.get('giftwrap credits tax', '0'))
        promotional_rebates = parse_decimal(row.get('promotional rebates', '0'))
        promotional_rebates_tax = parse_decimal(row.get('promotional rebates tax', '0'))
        marketplace_withheld_tax = parse_decimal(row.get('marketplace withheld tax', '0'))
        selling_fees = parse_decimal(row.get('selling fees', '0'))
        fba_fees = parse_decimal(row.get('fba fees', '0'))
        other_transaction_fees = parse_decimal(row.get('other transaction fees', '0'))
        other = parse_decimal(row.get('other', '0'))
        total = parse_decimal(row.get('total', '0'))
        
        calculated = (product_sales + product_sales_tax + postage_credits + 
                     shipping_credits_tax + gift_wrap_credits + giftwrap_credits_tax +
                     promotional_rebates + promotional_rebates_tax + 
                     marketplace_withheld_tax + selling_fees + fba_fees + 
                     other_transaction_fees + other)
        
        diff = total - calculated
        order_id = row.get('order id', '')[:15]
        print(f"  订单 {order_id}: 文件total={float(total):.2f}, 计算值={float(calculated):.2f}, 差异={float(diff):.2f}")
    
    # 4. 分析Refund记录
    print("\n【分析Refund记录 - 前3条】")
    count = 0
    for row in rows:
        if row.get('type') != 'Refund':
            continue
        if count >= 3:
            break
        count += 1
        
        product_sales = parse_decimal(row.get('product sales', '0'))
        selling_fees = parse_decimal(row.get('selling fees', '0'))
        fba_fees = parse_decimal(row.get('fba fees', '0'))
        total = parse_decimal(row.get('total', '0'))
        
        order_id = row.get('order id', '')[:15]
        print(f"  退款订单 {order_id}:")
        print(f"    product_sales={float(product_sales):.2f}, selling_fees={float(selling_fees):.2f}")
        print(f"    fba_fees={float(fba_fees):.2f}, total={float(total):.2f}")
    
    return {
        'total_rows': len(rows),
        'type_distribution': dict(type_counter),
        'type_totals': {k: float(v) for k, v in type_totals.items()},
        'grand_total': float(grand_total)
    }

def main():
    # 分析UK站点文件
    uk_file = r'd:/app/收入核算系统/跨境电商数据/部分店铺收入/亚马逊/智能万物店铺10_UK 2025NovMonthlyTransaction.csv'
    if os.path.exists(uk_file):
        analyze_amazon_csv(uk_file)
    
    # 分析DE站点文件
    de_file = r'd:/app/收入核算系统/跨境电商数据/部分店铺收入/亚马逊/智能万物店铺10_DE 2025NovMonthlyTransaction.csv'
    if os.path.exists(de_file):
        analyze_amazon_csv(de_file)

if __name__ == '__main__':
    main()
