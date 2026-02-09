# -*- coding: utf-8 -*-
"""
分析Transfer/Payout记录的详细特征
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from pathlib import Path

def parse_decimal(s):
    if not s or not str(s).strip():
        return Decimal('0')
    try:
        return Decimal(str(s).strip().replace(',', ''))
    except InvalidOperation:
        return Decimal('0')

def analyze_transfer_records(file_path):
    """分析单个CSV文件中的Transfer/Payout记录"""
    print(f"\n{'='*70}")
    print(f"文件: {Path(file_path).name}")
    print('='*70)
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # 找到表头行
    lines = content.split('\n')
    header_row = None
    header_idx = 0
    
    for i, line in enumerate(lines):
        if 'product sales' in line.lower() and 'type' in line.lower():
            header_row = line
            header_idx = i
            break
    
    if not header_row:
        print("未找到表头行")
        return
    
    # 解析CSV
    csv_content = '\n'.join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_content))
    
    # 记录Transfer相关的行
    transfer_records = []
    
    for row in reader:
        row_lower = {k.strip().lower(): v for k, v in row.items()}
        row_type = row_lower.get('type', '').strip()
        
        if 'transfer' in row_type.lower() or 'payout' in row_type.lower():
            transfer_records.append({
                'type': row_type,
                'order_id': row_lower.get('order id', '').strip(),
                'description': row_lower.get('description', '').strip()[:60],
                'product_sales': parse_decimal(row_lower.get('product sales', '')),
                'selling_fees': parse_decimal(row_lower.get('selling fees', '')),
                'fba_fees': parse_decimal(row_lower.get('fba fees', '')),
                'other': parse_decimal(row_lower.get('other', '')),
                'total': parse_decimal(row_lower.get('total', ''))
            })
    
    if transfer_records:
        print(f"\n找到 {len(transfer_records)} 条 Transfer/Payout 记录:\n")
        for i, r in enumerate(transfer_records[:20]):  # 最多显示20条
            print(f"  记录 {i+1}:")
            print(f"    type: {r['type']}")
            print(f"    order_id: '{r['order_id']}' (空={not r['order_id']})")
            print(f"    description: {r['description']}")
            print(f"    product_sales: {r['product_sales']}")
            print(f"    selling_fees: {r['selling_fees']}")
            print(f"    fba_fees: {r['fba_fees']}")
            print(f"    other: {r['other']}")
            print(f"    total: {r['total']}")
            print()
    else:
        print("未找到 Transfer/Payout 记录")

def main():
    base_path = Path(r'd:/app/收入核算系统/跨境电商数据/部分店铺收入/亚马逊')
    csv_files = list(base_path.glob('**/*.csv'))
    
    # 分析多个文件
    for f in csv_files[:5]:
        try:
            analyze_transfer_records(f)
        except Exception as e:
            print(f"\n分析 {f.name} 出错: {e}")

if __name__ == '__main__':
    main()
