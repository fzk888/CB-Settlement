# -*- coding: utf-8 -*-
import pandas as pd
from decimal import Decimal
import sys
import os

# 1510 Debug
f1510 = r'd:\\app\\收入核算系统\\data\\仓库财务账单\\海外仓账单\\1510\\bill-HBR-M20250401.xlsx'
if os.path.exists(f1510):
    print(f"=== 1510 File: {os.path.basename(f1510)} ===")
    xl = pd.ExcelFile(f1510)
    print("Sheets:", xl.sheet_names)
    
    total_parsed = Decimal('0')
    
    # 模拟 parser 逻辑
    for sheet in xl.sheet_names:
        if sheet in ['账单封面Bill cover', '充值Deposit']:
            continue
        try:
            df = pd.read_excel(f1510, sheet_name=sheet)
            # Parser Logic: sum columns with Fee, 费, Cost, Rate, Surcharge
            fee_cols = [c for c in df.columns if any(k in str(c) for k in ['Fee', '费', 'Cost', 'Rate', 'Surcharge'])]
            sheet_sum = Decimal('0')
            for col in fee_cols:
                # simple sum
                s = df[col].apply(lambda x: float(x) if pd.notna(x) and str(x).replace('.','').replace('-','').isdigit() else 0).sum()
                sheet_sum += Decimal(str(s))
            
            if sheet_sum > 0:
                print(f"  Sheet [{sheet}] Parser Sum: {sheet_sum:,.2f}")
                print(f"    Columns used: {fee_cols}")
                total_parsed += sheet_sum
        except Exception as e:
            print(f"  Sheet [{sheet}] Error: {e}")

    print(f"Total Parsed: {total_parsed:,.2f}")
    
    # Check Manual Total if possible (e.g. from Bill Cover)
    if '账单封面Bill cover' in xl.sheet_names:
        df_cover = pd.read_excel(f1510, sheet_name='账单封面Bill cover')
        print("\nBill Cover Head:")
        print(df_cover.head(20).to_string())

# JD Debug
fJD = r'd:\\app\\收入核算系统\\data\\仓库财务账单\\海外仓账单\\京东\\HupperTekCo.Limited_KH9220000002310_海外配送服务费-应收_2025-10-11_2025-10-20_BR1985014116657500160_2c27.xlsx'
if os.path.exists(fJD):
    print(f"\n=== JD File: {os.path.basename(fJD)} ===")
    xl = pd.ExcelFile(fJD)
    print("Sheets:", xl.sheet_names)
    
    for sheet in xl.sheet_names:
        if sheet == '汇总页':
            continue
        df = pd.read_excel(fJD, sheet_name=sheet)
        print(f"\nSheet [{sheet}] Columns: {df.columns.tolist()}")
        
        # Parser Logic check
        amount_cols = [c for c in df.columns if '金额' in str(c) and '含税' in str(c)]
        if not amount_cols:
            amount_cols = [c for c in df.columns if '金额' in str(c)]
        
        print(f"  Identify Amount Cols: {amount_cols}")
        if amount_cols:
            s = df[amount_cols[0]].apply(lambda x: float(x) if pd.notna(x) else 0).sum()
            print(f"  Sum of first col [{amount_cols[0]}]: {s:,.2f}")
            # check if there are other amount cols that are significant
            for c in amount_cols[1:]:
                s2 = df[c].apply(lambda x: float(x) if pd.notna(x) else 0).sum()
                print(f"  Sum of other col [{c}]: {s2:,.2f}")

