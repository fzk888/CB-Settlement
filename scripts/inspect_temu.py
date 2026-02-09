import pandas as pd
import sys

f = r'd:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月\Boutique local FundDetail-1762143796093-afd2.xlsx'
try:
    xl = pd.ExcelFile(f)
    print(f"Sheets: {xl.sheet_names}")
    
    if '结算' in xl.sheet_names:
        df = pd.read_excel(f, sheet_name='结算')
        print("\n--- Sheet: 结算 ---")
        print("Columns:", df.columns.tolist())
        print("Head(2):")
        print(df.head(2).to_string())
        
        if '结算金额' in df.columns:
            total = df['结算金额'].sum()
            print(f"\nTotal '结算金额': {total}")
        
        print("\nFirst 3 rows:")
        for idx, row in df.head(3).iterrows():
            print(row.to_dict())

except Exception as e:
    print(f"Error: {e}")
