# -*- coding: utf-8 -*-
import pandas as pd
f = r'd:\app\收入核算系统\output\月度核算报表_Phase1_多平台.xlsx'
df = pd.read_excel(f)

# 看 2025-12 的详细记录
print('=== 2025-12 平台收入详细 ===')
dec = df[df['月份'] == '2025-12']
print(dec[['平台','店铺','站点','平台净结算']].to_string())
print(f'总计: {dec["平台净结算"].sum():.2f}')

# 看综合损益中的备注
f2 = r'd:\app\收入核算系统\output\月度核算报表_Phase2.xlsx'
df2 = pd.read_excel(f2, sheet_name='综合损益概览')
print('\n=== 综合损益概览 (带备注) ===')
print(df2.to_string())
