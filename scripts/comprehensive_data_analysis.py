# -*- coding: utf-8 -*-
"""
综合数据结构分析脚本
分析平台收入数据和仓库账单数据的字段结构
"""
import csv
import io
import os
from decimal import Decimal, InvalidOperation
from collections import defaultdict, Counter
from pathlib import Path
import pandas as pd

def parse_decimal(s):
    """解析金额"""
    if not s or not str(s).strip():
        return Decimal('0')
    try:
        return Decimal(str(s).strip().replace(',', ''))
    except:
        return Decimal('0')

def analyze_amazon_csv(file_path):
    """分析Amazon CSV文件"""
    print(f"\n{'='*80}")
    print(f"【亚马逊月度交易分析】: {Path(file_path).name}")
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
        print("未找到表头行")
        return None
    
    reader = csv.DictReader(io.StringIO('\n'.join(lines[header_idx:])))
    rows = list(reader)
    
    print(f"\n📊 基本统计:")
    print(f"   总记录数: {len(rows)}")
    print(f"   字段列表: {list(reader.fieldnames)[:10]}...")
    
    # 1. type字段分布
    type_counter = Counter(row.get('type', '') for row in rows)
    print(f"\n📋 【type字段值分布】(用于区分订单类型):")
    for t, count in type_counter.most_common():
        print(f"   {t if t else '(空)':35}: {count:>5} 条")
    
    # 2. 按type汇总total金额
    type_totals = defaultdict(Decimal)
    type_counts = defaultdict(int)
    positive_totals = defaultdict(int)
    negative_totals = defaultdict(int)
    
    for row in rows:
        t = row.get('type', '')
        total = parse_decimal(row.get('total', '0'))
        type_totals[t] += total
        type_counts[t] += 1
        if total > 0:
            positive_totals[t] += 1
        elif total < 0:
            negative_totals[t] += 1
    
    print(f"\n💰 【按type汇总total金额】:")
    grand_total = Decimal('0')
    for t in sorted(type_totals.keys(), key=lambda x: float(type_totals[x]), reverse=True):
        total = type_totals[t]
        count = type_counts[t]
        pos = positive_totals[t]
        neg = negative_totals[t]
        grand_total += total
        t_name = t if t else '(空)'
        print(f"   {t_name:30} | 条数:{count:5} | 正数:{pos:4} | 负数:{neg:4} | Total: {float(total):>15,.2f}")
    
    print(f"   {'-'*85}")
    print(f"   {'总计':30} | 条数:{len(rows):5} |               Total: {float(grand_total):>15,.2f}")
    
    # 3. 分析Order记录的total正负情况
    order_positive = sum(1 for row in rows if row.get('type') == 'Order' and parse_decimal(row.get('total', '0')) > 0)
    order_negative = sum(1 for row in rows if row.get('type') == 'Order' and parse_decimal(row.get('total', '0')) < 0)
    order_zero = sum(1 for row in rows if row.get('type') == 'Order' and parse_decimal(row.get('total', '0')) == 0)
    
    print(f"\n🔍 【Order记录的Total正负分布】:")
    print(f"   正数(收入): {order_positive} 条")
    print(f"   负数(扣减): {order_negative} 条")
    print(f"   零值: {order_zero} 条")
    
    # 4. 分析Refund记录
    refund_rows = [row for row in rows if row.get('type') == 'Refund']
    if refund_rows:
        refund_positive = sum(1 for row in refund_rows if parse_decimal(row.get('total', '0')) > 0)
        refund_negative = sum(1 for row in refund_rows if parse_decimal(row.get('total', '0')) < 0)
        print(f"\n🔍 【Refund记录的Total正负分布】:")
        print(f"   正数: {refund_positive} 条")
        print(f"   负数(退款扣减): {refund_negative} 条")
        
        # 分析退款记录的product sales字段
        refund_product_sales = [parse_decimal(row.get('product sales', '0')) for row in refund_rows]
        negative_ps = sum(1 for ps in refund_product_sales if ps < 0)
        print(f"   Refund记录中product sales为负数: {negative_ps} 条 (占{negative_ps/len(refund_rows)*100:.1f}%)")
    
    # 5. 验证total计算公式(抽样)
    print(f"\n✅ 【验证total = 各组成字段之和】(抽取3条Order验证):")
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
        status = "✓匹配" if abs(float(diff)) < 0.01 else f"✗差异:{float(diff):.2f}"
        print(f"   订单 {order_id}: 文件total={float(total):.2f}, 计算值={float(calculated):.2f} {status}")
    
    # 6. 检查是否存在无order id但有total的记录
    no_order_id = [row for row in rows if not row.get('order id', '').strip() and parse_decimal(row.get('total', '0')) != 0]
    if no_order_id:
        print(f"\n⚠️ 【无order id但有Total的记录】: {len(no_order_id)} 条")
        for row in no_order_id[:3]:
            print(f"   类型:{row.get('type')}, Total:{row.get('total')}, 描述:{row.get('description', '')[:50]}")
    
    return {
        'total_rows': len(rows),
        'type_distribution': dict(type_counter),
        'type_totals': {k: float(v) for k, v in type_totals.items()},
        'grand_total': float(grand_total)
    }

def analyze_warehouse_excel(file_path, warehouse_name):
    """分析仓库Excel文件"""
    print(f"\n{'='*80}")
    print(f"【{warehouse_name}账单分析】: {Path(file_path).name}")
    print('='*80)
    
    try:
        xl = pd.ExcelFile(file_path)
        print(f"\n📊 工作表: {xl.sheet_names}")
        
        for sheet in xl.sheet_names[:2]:
            print(f"\n--- 工作表: {sheet} ---")
            df = pd.read_excel(file_path, sheet_name=sheet, dtype=str, nrows=100)
            
            print(f"📋 列名({len(df.columns)}列):")
            for i, col in enumerate(df.columns):
                non_null = df[col].notna().sum()
                print(f"   {i+1:2}. {str(col)[:40]} (非空: {non_null})")
            
            # 尝试识别关键字段
            cols_lower = [str(c).lower() for c in df.columns]
            order_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['订单', 'order', '单号'])]
            amount_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['金额', 'amount', '费用', '价格', 'price', 'fee'])]
            type_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['类型', 'type', '业务'])]
            date_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['日期', 'date', '时间', 'time'])]
            
            print(f"\n🔍 关键字段识别:")
            print(f"   订单相关: {order_cols[:3]}")
            print(f"   金额相关: {amount_cols[:3]}")
            print(f"   类型相关: {type_cols[:3]}")
            print(f"   日期相关: {date_cols[:3]}")
            
            # 显示前3行样本数据
            print(f"\n📝 样本数据(前3行):")
            for idx, row in df.head(3).iterrows():
                print(f"   行 {idx}: ", end="")
                vals = []
                for col in df.columns[:6]:
                    val = row[col]
                    if pd.notna(val) and str(val).strip():
                        vals.append(f"{str(col)[:10]}={str(val)[:20]}")
                print(", ".join(vals[:4]))
                
    except Exception as e:
        print(f"❌ 读取失败: {e}")

def main():
    print("="*80)
    print("跨境电商收入核算系统 - 数据结构综合分析报告")
    print("="*80)
    
    # 1. 分析平台数据
    print("\n" + "▓"*40)
    print("第一部分: 平台月度交易数据分析")
    print("▓"*40)
    
    uk_file = r'd:/app/收入核算系统/跨境电商数据/部分店铺收入/亚马逊/智能万物店铺10_UK 2025NovMonthlyTransaction.csv'
    if os.path.exists(uk_file):
        analyze_amazon_csv(uk_file)
    
    # 2. 分析仓库账单
    print("\n" + "▓"*40)
    print("第二部分: 仓库账单数据分析")
    print("▓"*40)
    
    base_dir = Path(r'd:/app/收入核算系统/跨境电商数据/财务账单/海外仓账单')
    
    # 东方嘉盛
    dfjsh_files = list((base_dir / "东方嘉盛").glob("*.xlsx"))
    if dfjsh_files:
        analyze_warehouse_excel(dfjsh_files[0], "东方嘉盛")
    
    # TLB
    tlb_files = list((base_dir / "TLB账单").glob("*.xlsx"))
    if tlb_files:
        analyze_warehouse_excel(tlb_files[0], "TLB")
    
    # 易达云
    ydy_files = list((base_dir / "易达云").glob("*.xlsx"))
    if ydy_files:
        analyze_warehouse_excel(ydy_files[0], "易达云")
    
    # G7
    g7_dir = base_dir / "G7"
    for sub_dir in sorted(g7_dir.iterdir())[:1]:
        if sub_dir.is_dir():
            for f in sorted(sub_dir.glob("*.xlsx"))[:1]:
                analyze_warehouse_excel(f, f"G7-{sub_dir.name}")

if __name__ == '__main__':
    main()
