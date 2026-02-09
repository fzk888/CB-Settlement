# -*- coding: utf-8 -*-
import pandas as pd
from decimal import Decimal
import sys
import os

def check_1510_cols():
    print("="*60)
    print("1510 Analysis")
    print("="*60)
    f = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\1510\bill-HBR-M20250401.xlsx'
    if not os.path.exists(f): return
    
    df = pd.read_excel(f, sheet_name='B2C订单费用B2C Order Charges')
    print(f"Columns: {df.columns.tolist()}")
    
    # columns capturing "Fee", "Cost", "Rate"
    fee_cols = [c for c in df.columns if any(k in str(c) for k in ['Fee', '费', 'Cost', 'Rate', 'Surcharge'])]
    print(f"\nCaptured Fee Cols ({len(fee_cols)}):")
    for c in fee_cols:
        val = df[c].sum()
        print(f"  {c}: {val:,.2f}")
    
    total = sum(df[c].sum() for c in fee_cols)
    print(f"\nTotal Parsed: {total:,.2f}")

def check_jd_cols():
    print("\n" + "="*60)
    print("JD Analysis")
    print("="*60)
    f = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\京东\HupperTekCo.Limited_KH9220000002310_海外配送服务费-应收_2025-10-11_2025-10-20_BR1985014116657500160_2c27.xlsx'
    if not os.path.exists(f):
        # find closest match
        folder = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\京东'
        files = os.listdir(folder)
        target = [x for x in files if '海外配送服务费' in x and '2c27' in x]
        if target:
            f = os.path.join(folder, target[0])
        else:
            return

    df = pd.read_excel(f, sheet_name='明细_1' if '明细_1' in pd.ExcelFile(f).sheet_names else '明细_1') 
    # Wait, need to check sheet name
    xl = pd.ExcelFile(f)
    print(f"File: {os.path.basename(f)}")
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        if sheet == '汇总页': continue
        print(f"\nSheet [{sheet}] Analysis:")
        df = pd.read_excel(f, sheet_name=sheet)
        
        # Check specific amount columns
        print("Amount Columns:")
        for c in df.columns:
            if '金额' in str(c):
                print(f"  {c}: {df[c].sum():,.2f}")
        
        # Check currency
        if '结算币种\nSettlement Currency' in df.columns:
            print(f"Currency: {df['结算币种\nSettlement Currency'].unique()}")

if __name__ == '__main__':
    check_1510_cols()
    check_jd_cols()
