# -*- coding: utf-8 -*-
import pandas as pd
f = r'd:\app\收入核算系统\output\月度核算报表_Phase2.xlsx'

# 查看综合损益有负数的月份
df = pd.read_excel(f, sheet_name='综合损益概览')
print('=== 毛利为负的月份 ===')
print(df.columns.tolist())
negative = df[df.iloc[:,3] < 0]
print(negative.to_string())

# 看 2025-12 的平台收入明细
df2 = pd.read_excel(f, sheet_name='平台收入汇总')
print('\n=== 2025-12 平台收入明细 ===')
dec = df2[df2['月份'] == '2025-12']
print(dec[['平台','店铺','平台净结算']].to_string())
print(f'2025-12 总收入: {dec["平台净结算"].sum()}')

# 看月份列唯一值
print('\n=== 月份列唯一值 ===')
print(df2['月份'].unique()[:20])
