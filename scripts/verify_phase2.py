# -*- coding: utf-8 -*-
import pandas as pd
f = r'd:\app\收入核算系统\output\月度核算报表_Phase2.xlsx'
xl = pd.ExcelFile(f)
print(f'Sheets: {xl.sheet_names}')

# 综合损益
df = pd.read_excel(f, sheet_name='综合损益概览')
print(f'\n=== 综合损益概览 ({len(df)} 行) ===')
print(df.to_string())
print(f'\n总计:')
print(f'  收入: {df.iloc[:,1].sum():,.2f}')
print(f'  成本: {df.iloc[:,2].sum():,.2f}')
print(f'  毛利: {df.iloc[:,3].sum():,.2f}')

# 平台收入
df2 = pd.read_excel(f, sheet_name='平台收入汇总')
print(f'\n=== 平台收入 ({len(df2)} 行) ===')
print(df2.groupby('平台')['平台净结算'].sum())
