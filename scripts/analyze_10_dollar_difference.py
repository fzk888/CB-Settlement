#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确分析$10差异来源的验证脚本
专门针对All F Home 10月份$5424.53 vs $5434.53的差异
"""

import pandas as pd
import os
from pathlib import Path
import sys
from decimal import Decimal

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser.temu_parser import TemuParser

def detailed_transaction_analysis():
    """详细分析交易记录，查找$10差异"""
    data_root = r"d:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月"
    temu_parser = TemuParser()
    
    print("=== All F Home 10月份$10差异详细分析 ===")
    
    # 查找All F Home的TEMU文件
    temu_files = list(Path(data_root).glob("*All F Home*FundDetail*.xlsx"))
    
    if not temu_files:
        print("✗ 未找到All F Home的TEMU文件")
        return
    
    file_path = temu_files[0]
    print(f"分析文件: {file_path.name}")
    
    try:
        # 读取Excel文件的所有sheets进行详细分析
        xl = pd.ExcelFile(file_path)
        print(f"文件包含 {len(xl.sheet_names)} 个工作表:")
        for sheet in xl.sheet_names:
            print(f"  - {sheet}")
        
        # 逐个sheet分析
        total_sum = Decimal('0')
        sheet_details = {}
        
        for sheet_name in xl.sheet_names:
            try:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                print(f"\n--- {sheet_name} ---")
                print(f"行数: {len(df)}")
                
                # 查找金额列
                amount_cols = [col for col in df.columns if any(keyword in col.lower() 
                              for keyword in ['金额', '收入', '结算', '交易'])]
                
                if amount_cols:
                    amount_col = amount_cols[0]
                    print(f"金额列: {amount_col}")
                    
                    # 计算该sheet的总额
                    sheet_total = Decimal('0')
                    valid_records = 0
                    
                    for idx, row in df.iterrows():
                        amount_val = row.get(amount_col, 0)
                        if pd.notna(amount_val) and amount_val != '/' and amount_val != '':
                            try:
                                amount = Decimal(str(amount_val))
                                # 根据sheet类型确定符号
                                if '退款' in sheet_name or '违规' in sheet_name or '支出' in sheet_name:
                                    amount = -abs(amount)
                                else:
                                    amount = abs(amount)
                                
                                sheet_total += amount
                                valid_records += 1
                                
                                # 如果接近我们的目标差异，记录详细信息
                                if abs(amount) >= Decimal('1') and abs(amount) <= Decimal('20'):
                                    print(f"    行{idx+2}: ${float(amount):.2f} - {row.get('订单编号', 'N/A')}")
                                    
                            except (ValueError, TypeError):
                                continue
                    
                    sheet_details[sheet_name] = {
                        'total': sheet_total,
                        'records': valid_records
                    }
                    total_sum += sheet_total
                    
                    print(f"  有效记录: {valid_records}")
                    print(f"  小计: ${float(sheet_total):.2f}")
                    
                else:
                    print("  未找到金额列")
                    
            except Exception as e:
                print(f"  处理失败: {e}")
        
        print(f"\n=== 汇总分析 ===")
        print(f"各Sheet明细:")
        for sheet, details in sheet_details.items():
            print(f"  {sheet}: ${float(details['total']):.2f} ({details['records']}条)")
        
        print(f"\n总计: ${float(total_sum):.2f}")
        print(f"预期: $5434.53")
        print(f"差异: ${float(abs(total_sum - Decimal('5434.53'))):.2f}")
        
        # 检查是否能找到$10的差异来源
        target_difference = Decimal('10.00')
        found_sources = []
        
        print(f"\n=== 寻找${float(target_difference):.2f}差异来源 ===")
        
        # 检查每个sheet中是否有接近$10的单项交易
        for sheet_name in xl.sheet_names:
            try:
                df = pd.read_excel(xl, sheet_name=sheet_name)
                amount_cols = [col for col in df.columns if any(keyword in col.lower() 
                              for keyword in ['金额', '收入', '结算', '交易'])]
                
                if amount_cols:
                    amount_col = amount_cols[0]
                    for idx, row in df.iterrows():
                        amount_val = row.get(amount_col, 0)
                        if pd.notna(amount_val) and amount_val != '/' and amount_val != '':
                            try:
                                raw_amount = Decimal(str(amount_val))
                                # 考虑正负号
                                if '退款' in sheet_name or '违规' in sheet_name or '支出' in sheet_name:
                                    processed_amount = -abs(raw_amount)
                                else:
                                    processed_amount = abs(raw_amount)
                                    
                                # 检查是否接近$10
                                if abs(abs(processed_amount) - target_difference) <= Decimal('0.01'):
                                    found_sources.append({
                                        'sheet': sheet_name,
                                        'row': idx + 2,
                                        'raw_amount': float(raw_amount),
                                        'processed_amount': float(processed_amount),
                                        'order_id': row.get('订单编号', 'N/A')
                                    })
                            except (ValueError, TypeError):
                                continue
            except Exception:
                continue
        
        if found_sources:
            print("找到可能的$10来源:")
            for source in found_sources:
                print(f"  Sheet: {source['sheet']}, 行: {source['row']}")
                print(f"    原始金额: ${source['raw_amount']:.2f}")
                print(f"    处理后金额: ${source['processed_amount']:.2f}")
                print(f"    订单号: {source['order_id']}")
        else:
            print("未找到精确的$10单项交易")
            
    except Exception as e:
        print(f"✗ 分析失败: {e}")

def main():
    detailed_transaction_analysis()

if __name__ == "__main__":
    main()