# -*- coding: utf-8 -*-
import pandas as pd
from decimal import Decimal
import os
import sys

def check_1510():
    f = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\1510\bill-HBR-M20250401.xlsx'
    if not os.path.exists(f):
        print("1510 file not found", flush=True)
        return
    xl = pd.ExcelFile(f)
    print("=== 1510: bill-HBR-M20250401.xlsx ===", flush=True)
    print("Sheets:", xl.sheet_names, flush=True)
    sheet = 'B2C订单费用B2C Order Charges'
    if sheet in xl.sheet_names:
        df = pd.read_excel(f, sheet_name=sheet)
        print(f"\nSheet: {sheet}", flush=True)
        print("Columns:", df.columns.tolist(), flush=True)
        print("First row data example:", flush=True)
        print(df.head(1).to_dict('records'), flush=True)
        # Check specific fee columns
        fee_cols = [c for c in df.columns if any(k in str(c) for k in ['Fee', '费', 'Cost', 'Rate', 'Surcharge'])]
        print("Identified fee columns:", fee_cols, flush=True)

def check_jd():
    jd_dir = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\京东'
    files = [os.path.join(jd_dir, x) for x in os.listdir(jd_dir) if x.endswith('.xlsx')]
    if not files:
        print("JD file not found", flush=True)
        return
    f = files[0]
    
    xl = pd.ExcelFile(f)
    print("\n=== 京东: " + os.path.basename(f) + " ===", flush=True)
    print("Sheets:", xl.sheet_names, flush=True)
    sheet = '明细_1'
    if sheet in xl.sheet_names:
        df = pd.read_excel(f, sheet_name=sheet)
        print(f"\nSheet: {sheet}", flush=True)
        print("Columns:", df.columns.tolist(), flush=True)
        print("First row data example:", flush=True)
        print(df.head(1).to_dict('records'), flush=True)


if __name__ == "__main__":
    check_1510()
    check_jd()
