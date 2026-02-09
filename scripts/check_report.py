# -*- coding: utf-8 -*-
"""验证报表数据准确性"""
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

df = pd.read_excel(r'd:\app\收入核算系统\output\月度核算报表_Phase1_多平台.xlsx', sheet_name='详细数据')

print("=== SHEIN 所有记录 ===")
shein = df[df['平台'] == 'shein']
for _, row in shein.iterrows():
    print(f"  {row['店铺'][:15]:15s} | {row['月份']:7s} | {row['交易数']:5d}条 | {row['平台净结算']:>12,.2f} {row['币种']}")

print("\n=== 托管店铺 所有记录 ===")
ms = df[df['平台'] == 'managed_store']
for _, row in ms.iterrows():
    print(f"  {row['店铺'][:15]:15s} | {row['月份']:7s} | {row['交易数']:5d}条 | {row['平台净结算']:>12,.2f} {row['币种']}")

print("\n=== TEMU 2025-07 记录 ===")
temu = df[(df['平台'] == 'temu') & (df['月份'] == '2025-07')]
for _, row in temu.head(5).iterrows():
    print(f"  {row['店铺'][:15]:15s} | {row['月份']:7s} | {row['交易数']:5d}条 | {row['平台净结算']:>12,.2f} {row['币种']}")
print(f"  ... 共 {len(temu)} 条")

print("\n=== 速卖通 ===")
ali = df[df['平台'] == 'aliexpress']
for _, row in ali.iterrows():
    print(f"  {row['店铺'][:15]:15s} | {row['月份']:7s} | {row['交易数']:5d}条 | {row['平台净结算']:>12,.2f} {row['币种']}")
