# -*- coding: utf-8 -*-
"""调试 Product Sales 计算差异"""
import csv
import io
from pathlib import Path
from decimal import Decimal

file_path = r'd:/app/收入核算系统/跨境电商数据/部分店铺收入/亚马逊/2-UK2025JulMonthlyTransaction.csv'
content = Path(file_path).read_text(encoding='utf-8-sig')

lines = content.split('\n')
header_idx = 0
for i, line in enumerate(lines[:20]):
    if 'type' in line.lower() and 'total' in line.lower():
        header_idx = i
        break

csv_content = '\n'.join(lines[header_idx:])
reader = csv.DictReader(io.StringIO(csv_content))

ps_total = Decimal('0')
postage_total = Decimal('0')
shipping_total = Decimal('0')
total_col = Decimal('0')

# Print headers first
print("CSV 字段列表:")
for row in reader:
    print([k for k in row.keys()][:15])
    break

# Re-parse
csv_content = '\n'.join(lines[header_idx:])
reader = csv.DictReader(io.StringIO(csv_content))

for row in reader:
    ps_val = row.get('product sales', '').strip().replace(',', '')
    post_val = row.get('postage credits', '').strip().replace(',', '')
    ship_val = row.get('shipping credits', '').strip().replace(',', '')
    total_val = row.get('total', '').strip().replace(',', '')
    
    if ps_val:
        try: ps_total += Decimal(ps_val)
        except: pass
    if post_val:
        try: postage_total += Decimal(post_val)
        except: pass
    if ship_val:
        try: shipping_total += Decimal(ship_val)
        except: pass
    if total_val:
        try: total_col += Decimal(total_val)
        except: pass

print("")
print("=== CSV 原始数据汇总 ===")
print(f"Product Sales:     {ps_total}")
print(f"Postage Credits:   {postage_total}")
print(f"Shipping Credits:  {shipping_total}")
print(f"Total 列汇总:      {total_col}")
print("")
print("=== 报表显示值 ===")
print(f"报表 Product Sales: 3,453.65")
print(f"差额: {Decimal('3453.65') - ps_total}")
