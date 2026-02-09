#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面差异分析脚本 - 修正版
正确处理结算表的数据格式
"""

import pandas as pd
import os
from pathlib import Path
import sys
from decimal import Decimal

def comprehensive_analysis():
    """全面分析所有可能的金额项目"""
    file_path = r"d:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月\All F Home FundDetail-1762149595565-16b5.xlsx"
    
    print("=== All F Home 10月份全面差异分析 ===")
    
    try:
        # 读取所有工作表
        xl = pd.ExcelFile(file_path)
        all_sheets = xl.sheet_names
        print(f"文件包含 {len(all_sheets)} 个工作表: {all_sheets}")
        
        total_income = Decimal('0')
        total_expense = Decimal('0')
        income_items = []
        expense_items = []
        
        # 分析每个工作表
        for sheet_name in all_sheets:
            print(f"\n--- 分析 {sheet_name} ---")
            df = pd.read_excel(xl, sheet_name=sheet_name)
            
            # 为不同工作表设置不同的金额列
            if sheet_name == '结算':
                amount_col = '结算金额'
            else:
                # 支出类工作表
                amount_cols = [col for col in df.columns if '金额' in col]
                amount_col = amount_cols[0] if amount_cols else None
            
            if amount_col and amount_col in df.columns:
                print(f"金额列: {amount_col}")
                
                sheet_total = Decimal('0')
                valid_records = 0
                
                for idx, row in df.iterrows():
                    amount_val = row.get(amount_col, 0)
                    if pd.notna(amount_val) and amount_val != '/' and amount_val != '':
                        try:
                            amount = Decimal(str(amount_val))
                            
                            # 根据工作表名称判断是收入还是支出
                            if '支出' in sheet_name or '违规' in sheet_name or '拒付' in sheet_name:
                                # 支出项目，保持负值
                                processed_amount = -abs(amount)
                                expense_items.append({
                                    'sheet': sheet_name,
                                    'row': idx + 2,
                                    'amount': float(processed_amount),
                                    'description': str(row.get('备注', '') or row.get('订单编号', ''))[:50]
                                })
                            else:
                                # 收入项目，保持正值
                                processed_amount = abs(amount)
                                income_items.append({
                                    'sheet': sheet_name,
                                    'row': idx + 2,
                                    'amount': float(processed_amount),
                                    'description': str(row.get('备注', '') or row.get('订单编号', ''))[:50]
                                })
                            
                            sheet_total += processed_amount
                            valid_records += 1
                            
                        except (ValueError, TypeError):
                            continue
                
                print(f"  有效记录: {valid_records}")
                print(f"  小计: ${float(sheet_total):.2f}")
                
                if sheet_total > 0:
                    total_income += sheet_total
                else:
                    total_expense += abs(sheet_total)
            else:
                print("  未找到合适的金额列")
                print(f"  可用列: {df.columns.tolist()}")
        
        print(f"\n=== 综合汇总 ===")
        print(f"总收入明细:")
        income_breakdown = {}
        for item in income_items:
            sheet = item['sheet']
            if sheet not in income_breakdown:
                income_breakdown[sheet] = Decimal('0')
            income_breakdown[sheet] += Decimal(str(item['amount']))
        
        for sheet, amount in income_breakdown.items():
            print(f"  {sheet}: ${float(amount):.2f}")
        
        print(f"\n总支出明细:")
        expense_breakdown = {}
        for item in expense_items:
            sheet = item['sheet']
            if sheet not in expense_breakdown:
                expense_breakdown[sheet] = Decimal('0')
            expense_breakdown[sheet] += Decimal(str(abs(item['amount'])))
        
        for sheet, amount in expense_breakdown.items():
            print(f"  {sheet}: ${float(amount):.2f}")
        
        print(f"\n计算结果:")
        print(f"  总收入: ${float(total_income):.2f}")
        print(f"  总支出: ${float(total_expense):.2f}")
        print(f"  净收入: ${float(total_income - total_expense):.2f}")
        
        expected_net = Decimal('5434.53')
        actual_net = total_income - total_expense
        difference = abs(actual_net - expected_net)
        
        print(f"\n与期望值对比:")
        print(f"  期望净收入: ${float(expected_net):.2f}")
        print(f"  实际净收入: ${float(actual_net):.2f}")
        print(f"  差异: ${float(difference):.2f}")
        
        if difference <= Decimal('0.01'):
            print("✓ 计算结果与期望值匹配")
        else:
            print("✗ 存在计算差异")
            print(f"\n差异分析:")
            print(f"  我们的计算: ${float(total_income):.2f} - ${float(total_expense):.2f} = ${float(actual_net):.2f}")
            print(f"  期望结果: ${float(expected_net):.2f}")
            print(f"  需要调整: ${float(difference):.2f}")
            
    except Exception as e:
        print(f"分析失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    comprehensive_analysis()

if __name__ == "__main__":
    main()