import pandas as pd

files = [
    'data/仓库财务账单/海外仓账单/京东/2025-03/费用明细_606ac359-5d0a-41ab-983f-d43436d9580d_1744885711874.xlsx',
    'data/仓库财务账单/海外仓账单/京东/2025-03/费用明细_cee1004a-566c-4257-ab3a-6073bba0e032_1744887492243.xlsx'
]

total_quote = 0
total_settlement = 0

for file_path in files:
    print(f"\n=== {file_path} ===")
    df = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # 找到报价币种含税金额列（第15行）
    quote_col = None
    settlement_col = None
    
    for j in range(df.shape[1]):
        if pd.notna(df.iloc[15, j]) and '报价币种含税金额' in str(df.iloc[15, j]):
            quote_col = j
        if pd.notna(df.iloc[15, j]) and '结算币种含税金额' in str(df.iloc[15, j]):
            settlement_col = j
    
    print(f"Quote col: {quote_col}, Settlement col: {settlement_col}")
    
    if quote_col is not None:
        file_quote_total = 0
        for i in range(17, df.shape[0]):
            val = df.iloc[i, quote_col]
            if pd.notna(val):
                try:
                    file_quote_total += float(val)
                except:
                    pass
        total_quote += file_quote_total
        print(f"Quote total: {file_quote_total}")
    
    if settlement_col is not None:
        file_settlement_total = 0
        for i in range(17, df.shape[0]):
            val = df.iloc[i, settlement_col]
            if pd.notna(val):
                try:
                    file_settlement_total += float(val)
                except:
                    pass
        total_settlement += file_settlement_total
        print(f"Settlement total: {file_settlement_total}")

print(f"\n=== FINAL TOTALS ===")
print(f"Quote currency total: {total_quote}")
print(f"Settlement currency total: {total_settlement}")