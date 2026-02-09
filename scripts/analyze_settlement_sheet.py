#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门分析结算工作表的脚本
"""

import pandas as pd
import os
from pathlib import Path
import sys
from decimal import Decimal

def analyze_settlement_sheet():
    """分析结算工作表的具体数据"""
    file_path = r"d:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月\All F Home FundDetail-1762149595565-16b5.xlsx"
    
    print("=== 结算工作表详细分析 ===")
    
    try:
        # 直接读取结算工作表
        df = pd.read_excel(file_path, sheet_name='结算')
        print(f"结算表行数: {len(df)}")
        print(f"列名: {df.columns.tolist()}")
        
        # 查看前几行数据
        print("\n前5行数据:")
        print(df.head())
        
        # 尝试不同的金额列名
        possible_amount_cols = ['结算金额', '交易金额', '收入金额', '金额', '结算流水ID']
        amount_col = None
        
        for col in possible_amount_cols:
            if col in df.columns:
                amount_col = col
                break
        
        if amount_col:
            print(f"\n使用金额列: {amount_col}")
            
            # 分析金额数据
            total_income = Decimal('0')
            valid_count = 0
            
            print("\n金额数据分析:")
            for idx, row in df.iterrows():
                amount_val = row.get(amount_col, 0)
                if pd.notna(amount_val) and amount_val != '/' and amount_val != '':
                    try:
                        amount = Decimal(str(amount_val))
                        total_income += amount
                        valid_count += 1
                        
                        # 显示一些样本数据
                        if valid_count <= 10 or amount >= Decimal('10'):
                            print(f"  行{idx+2}: ${float(amount):.2f}")
                            
                    except (ValueError, TypeError):
                        continue
            
            print(f"\n结算表统计:")
            print(f"  有效记录数: {valid_count}")
            print(f"  总收入: ${float(total_income):.2f}")
            
            # 结合支出数据计算净收入
            expenditure_total = Decimal('70.00')  # 支出-履约违规-1(-60) + 支出-买家拒付(-10)
            net_income = total_income - expenditure_total
            
            print(f"\n综合计算:")
            print(f"  总收入: ${float(total_income):.2f}")
            print(f"  总支出: ${float(expenditure_total):.2f}")
            print(f"  净收入: ${float(net_income):.2f}")
            print(f"  与报表对比 ($5434.53): 差异 ${float(abs(net_income - Decimal('5434.53'))):.2f}")
            
        else:
            print("未找到合适的金额列")
            print("所有列:", df.columns.tolist())
            
    except Exception as e:
        print(f"分析失败: {e}")

def main():
    analyze_settlement_sheet()

if __name__ == "__main__":
    main()