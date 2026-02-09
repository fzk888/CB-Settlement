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
    print(f"File: {os.path.basename(f)}")
    
    # columns capturing "Fee", "Cost", "Rate"
    # Logic in parser: any(k in str(c) for k in ['Fee', '费', 'Cost', 'Rate', 'Surcharge'])
    fee_cols = [c for c in df.columns if any(k in str(c) for k in ['Fee', '费', 'Cost', 'Rate', 'Surcharge'])]
    
    print(f"\nCaptured Fee Cols ({len(fee_cols)}):")
    total = 0
    vat_sum = 0
    for c in fee_cols:
        val = df[c].apply(lambda x: float(str(x).replace(',','')) if pd.notna(x) and str(x).replace(',','').replace('.','').replace('-','').isdigit() else 0).sum()
        print(f"  {c}: {val:,.2f}")
        total += val
        if 'VAT' in str(c).upper():
            vat_sum += val
    
    print(f"\nTotal Parsed: {total:,.2f}")
    print(f"VAT Component: {vat_sum:,.2f}")
    if total > 0:
        print(f"VAT % of Total: {vat_sum/total*100:.1f}%")
        print(f"Total excl VAT: {total - vat_sum:,.2f}")

def check_jd_cols():
    print("\n" + "="*60)
    print("JD Analysis")
    print("="*60)
    # Find the specific file
    folder = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\京东'
    target_files = [x for x in os.listdir(folder) if '2c27.xlsx' in x] # BR1985014116657500160_2c27
    if not target_files:
        print("JD file not found")
        return
    f = os.path.join(folder, target_files[0])
    
    print(f"File: {os.path.basename(f)}")
    xl = pd.ExcelFile(f)
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        if sheet == '汇总页': continue
        print(f"\nSheet [{sheet}] Analysis:")
        df = pd.read_excel(f, sheet_name=sheet)
        
        # Check specific amount columns
        amount_cols_rule1 = [c for c in df.columns if '金额' in str(c) and '含税' in str(c)]
        amount_cols_rule2 = [c for c in df.columns if '金额' in str(c)]
        
        print(f"  Columns matching '金额' + '含税': {amount_cols_rule1}")
        print(f"  Columns matching '金额': {amount_cols_rule2}")
        
        # Check sums
        for c in amount_cols_rule2: # check all amount columns
             val = df[c].apply(lambda x: float(x) if pd.notna(x) else 0).sum()
             print(f"    {c}: {val:,.2f}")


if __name__ == '__main__':
    check_1510_cols()
    check_jd_cols()
