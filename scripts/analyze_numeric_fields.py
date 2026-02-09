# -*- coding: utf-8 -*-
"""
分析平台CSV中的具体数值字段
重点分析: product sales, postage credits, shipping credits tax, 
gift wrap credits, giftwrap credits tax, promotional rebates, 
promotional rebates tax, marketplace withheld tax, selling fees,
fba fees, other transaction fees, other, total
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from pathlib import Path

def parse_decimal(s):
    """解析数值，处理逗号分隔符"""
    if not s or not str(s).strip():
        return Decimal('0')
    try:
        return Decimal(str(s).strip().replace(',', ''))
    except InvalidOperation:
        return Decimal('0')

def analyze_file(file_path):
    """分析单个CSV文件的数值字段"""
    print(f"\n{'='*70}")
    print(f"文件: {Path(file_path).name}")
    print('='*70)
    
    # 定义需要分析的数值字段
    numeric_fields = [
        'product sales', 'product sales tax',
        'postage credits', 'postage credits tax',
        'shipping credits', 'shipping credits tax',
        'gift wrap credits', 'giftwrap credits tax',
        'promotional rebates', 'promotional rebates tax',
        'marketplace withheld tax',
        'selling fees', 'fba fees', 
        'other transaction fees', 'other',
        'total'
    ]
    
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
    
    # 统计每个字段的总和，按type分组
    type_field_sums = defaultdict(lambda: defaultdict(Decimal))
    type_counts = defaultdict(int)
    field_stats = defaultdict(lambda: {'sum': Decimal('0'), 'positive': 0, 'negative': 0, 'zero': 0, 'count': 0})
    
    # 找到实际存在的字段
    fieldnames = [f.strip().lower() for f in reader.fieldnames] if reader.fieldnames else []
    print(f"\n实际存在的字段 ({len(fieldnames)}个):")
    for f in fieldnames:
        print(f"  - {f}")
    
    # 重新读取
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        # 标准化键名
        row_lower = {k.strip().lower(): v for k, v in row.items()}
        
        row_type = row_lower.get('type', 'Unknown').strip()
        if not row_type:
            row_type = 'Empty'
        type_counts[row_type] += 1
        
        for field in numeric_fields:
            if field in row_lower:
                val = parse_decimal(row_lower[field])
                type_field_sums[row_type][field] += val
                field_stats[field]['sum'] += val
                field_stats[field]['count'] += 1
                if val > 0:
                    field_stats[field]['positive'] += 1
                elif val < 0:
                    field_stats[field]['negative'] += 1
                else:
                    field_stats[field]['zero'] += 1
    
    # 输出type分布
    print(f"\n--- Type 分布 ---")
    for t, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {cnt}条")
    
    # 输出字段统计
    print(f"\n--- 各字段汇总统计 ---")
    print(f"{'字段名':<30} {'总和':>15} {'正值':>8} {'负值':>8} {'零值':>8}")
    print("-" * 75)
    
    for field in numeric_fields:
        if field in field_stats:
            stats = field_stats[field]
            print(f"{field:<30} {stats['sum']:>15.2f} {stats['positive']:>8} {stats['negative']:>8} {stats['zero']:>8}")
    
    # 输出验证: total 是否等于其他字段之和
    print(f"\n--- 验证: total 与各字段关系 ---")
    calculated_total = Decimal('0')
    for field in numeric_fields:
        if field != 'total' and field in field_stats:
            calculated_total += field_stats[field]['sum']
    
    actual_total = field_stats.get('total', {}).get('sum', Decimal('0'))
    print(f"各字段相加总和: {calculated_total:.2f}")
    print(f"total字段汇总:  {actual_total:.2f}")
    print(f"差异:           {actual_total - calculated_total:.2f}")
    
    # 按type分组的字段汇总
    print(f"\n--- 按 Type 分组的字段金额 ---")
    for t in sorted(type_counts.keys(), key=lambda x: -type_counts[x]):
        print(f"\n  [{t}] ({type_counts[t]}条):")
        for field in ['product sales', 'selling fees', 'fba fees', 'promotional rebates', 'other transaction fees', 'other', 'total']:
            if field in type_field_sums[t]:
                val = type_field_sums[t][field]
                if val != 0:
                    print(f"    {field}: {val:.2f}")

def main():
    # 分析多个平台CSV文件
    base_path = Path(r'd:/app/收入核算系统/跨境电商数据/部分店铺收入/亚马逊')
    
    csv_files = list(base_path.glob('**/*.csv'))
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    # 分析前3个文件作为样本
    for f in csv_files[:3]:
        try:
            analyze_file(f)
        except Exception as e:
            print(f"\n分析 {f.name} 出错: {e}")

if __name__ == '__main__':
    main()
