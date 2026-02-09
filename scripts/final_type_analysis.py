# -*- coding: utf-8 -*-
"""
最终核算口径分析脚本
分析所有type分布，特别关注Transfer/Payout记录
"""
import csv
import io
import os
from decimal import Decimal, InvalidOperation
from collections import defaultdict, Counter
from pathlib import Path

def parse_decimal(s):
    if not s or not str(s).strip():
        return Decimal('0')
    try:
        return Decimal(str(s).strip().replace(',', ''))
    except:
        return Decimal('0')

def analyze_all_types(file_path):
    """完整分析文件中所有type"""
    print(f"\n{'='*80}")
    print(f"Analysis: {Path(file_path).name}")
    print('='*80)
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    lines = content.split('\n')
    header_idx = -1
    for i, line in enumerate(lines):
        if 'date/time' in line.lower():
            header_idx = i
            break
    
    if header_idx < 0:
        print("Header not found")
        return None
    
    reader = csv.DictReader(io.StringIO('\n'.join(lines[header_idx:])))
    rows = list(reader)
    
    print(f"\nTotal records: {len(rows)}")
    
    # Complete type distribution with total sum
    type_stats = defaultdict(lambda: {'count': 0, 'total': Decimal('0'), 'positive': 0, 'negative': 0, 'zero': 0})
    
    for row in rows:
        t = row.get('type', '') or '(empty)'
        total = parse_decimal(row.get('total', '0'))
        type_stats[t]['count'] += 1
        type_stats[t]['total'] += total
        if total > 0:
            type_stats[t]['positive'] += 1
        elif total < 0:
            type_stats[t]['negative'] += 1
        else:
            type_stats[t]['zero'] += 1
    
    print("\n[Complete type distribution with total sums]")
    print(f"{'Type':35} | {'Count':>6} | {'Positive':>8} | {'Negative':>8} | {'Zero':>5} | {'Total Sum':>15}")
    print("-" * 95)
    
    grand_total = Decimal('0')
    for t in sorted(type_stats.keys(), key=lambda x: type_stats[x]['count'], reverse=True):
        stats = type_stats[t]
        grand_total += stats['total']
        print(f"{t:35} | {stats['count']:>6} | {stats['positive']:>8} | {stats['negative']:>8} | {stats['zero']:>5} | {float(stats['total']):>15,.2f}")
    
    print("-" * 95)
    print(f"{'GRAND TOTAL':35} | {len(rows):>6} |          |          |       | {float(grand_total):>15,.2f}")
    
    # Search for Transfer/Payout related records
    print("\n[Transfer/Payout/Payment Analysis]")
    transfer_keywords = ['transfer', 'payout', 'payment', 'withdraw', 'disburse']
    transfer_records = []
    
    for row in rows:
        t = (row.get('type', '') or '').lower()
        desc = (row.get('description', '') or '').lower()
        if any(kw in t or kw in desc for kw in transfer_keywords):
            transfer_records.append(row)
    
    if transfer_records:
        print(f"Found {len(transfer_records)} Transfer/Payout related records:")
        for i, row in enumerate(transfer_records[:10]):
            order_id = row.get('order id', '') or '(no order id)'
            total = row.get('total', '0')
            print(f"  {i+1}. type={row.get('type')}, order_id={order_id[:20]}, total={total}, desc={row.get('description', '')[:40]}")
    else:
        # Check all unique type values for anything related
        all_types = set(row.get('type', '') for row in rows)
        print("No Transfer/Payout records found. All types in file:")
        for t in sorted(all_types):
            print(f"  - {t}")
    
    # Analyze each category for profit calculation
    print("\n[Category breakdown for profit calculation]")
    
    # Order-related
    order_total = sum(parse_decimal(row.get('total', '0')) for row in rows if row.get('type') == 'Order')
    print(f"Order (sales income): {float(order_total):>15,.2f}")
    
    # Refund
    refund_total = sum(parse_decimal(row.get('total', '0')) for row in rows if row.get('type') == 'Refund')
    print(f"Refund (returned): {float(refund_total):>15,.2f}")
    
    # Service Fee
    service_fee_total = sum(parse_decimal(row.get('total', '0')) for row in rows if row.get('type') == 'Service Fee')
    print(f"Service Fee (advertising etc): {float(service_fee_total):>15,.2f}")
    
    # FBA Inventory Fee
    fba_inv_total = sum(parse_decimal(row.get('total', '0')) for row in rows if row.get('type') == 'FBA Inventory Fee')
    print(f"FBA Inventory Fee: {float(fba_inv_total):>15,.2f}")
    
    # Adjustment
    adj_total = sum(parse_decimal(row.get('total', '0')) for row in rows if row.get('type') == 'Adjustment')
    print(f"Adjustment: {float(adj_total):>15,.2f}")
    
    # Transfer (if exists)
    transfer_total = sum(parse_decimal(row.get('total', '0')) for row in rows if 'transfer' in (row.get('type', '') or '').lower())
    print(f"Transfer: {float(transfer_total):>15,.2f}")
    
    # Breakout of selling fees within Order records
    print("\n[Fee breakdown within Order records]")
    selling_fees = sum(parse_decimal(row.get('selling fees', '0')) for row in rows if row.get('type') == 'Order')
    fba_fees = sum(parse_decimal(row.get('fba fees', '0')) for row in rows if row.get('type') == 'Order')
    product_sales = sum(parse_decimal(row.get('product sales', '0')) for row in rows if row.get('type') == 'Order')
    
    print(f"Product Sales (within Order): {float(product_sales):>15,.2f}")
    print(f"Selling Fees (within Order): {float(selling_fees):>15,.2f}")
    print(f"FBA Fees (within Order): {float(fba_fees):>15,.2f}")
    
    return {
        'type_stats': type_stats,
        'grand_total': float(grand_total),
        'order_total': float(order_total),
        'refund_total': float(refund_total),
        'service_fee_total': float(service_fee_total),
        'fba_inv_total': float(fba_inv_total),
        'adj_total': float(adj_total),
        'transfer_found': len(transfer_records) > 0
    }

def main():
    base_dir = Path(r'd:/app/收入核算系统/跨境电商数据/部分店铺收入/亚马逊')
    
    # Analyze multiple files to ensure we see all type values
    files_to_analyze = [
        base_dir / '智能万物店铺10_UK 2025NovMonthlyTransaction.csv',
        base_dir / '智能万物店铺10_DE 2025NovMonthlyTransaction.csv',
        base_dir / '账号2-天基能源-US 2025NovMonthlyUnifiedTransaction.csv',
    ]
    
    for file_path in files_to_analyze:
        if file_path.exists():
            analyze_all_types(file_path)

if __name__ == '__main__':
    main()
