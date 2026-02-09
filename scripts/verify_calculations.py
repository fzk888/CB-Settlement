# -*- coding: utf-8 -*-
"""简化的验证脚本 - 输出到文件"""
import pandas as pd
import re
import warnings
warnings.filterwarnings('ignore')

output = []
def log(msg):
    print(msg)
    output.append(msg)

log("=" * 70)
log("多平台计算准确性验证")
log("=" * 70)

report = pd.read_excel(r'd:\app\收入核算系统\output\月度核算报表_Phase1_多平台.xlsx', sheet_name='详细数据')

# 1. TEMU
log("\n【1. TEMU】All F Home - 2025-07")
temu_file = r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台\多平台收入-7月\All F Home FundDetail-1754358591792-f173.xlsx'
xl = pd.ExcelFile(temu_file)
temu_net = 0
for sheet in xl.sheet_names:
    df = pd.read_excel(temu_file, sheet_name=sheet)
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64'] and '订单' not in str(col):
            val = df[col].sum()
            if '退款' in sheet or '支出' in sheet:
                temu_net -= abs(val)
            else:
                temu_net += val
            log(f"  {sheet}: {val:,.2f}")
            break

log(f"  手工合计: {temu_net:,.2f} USD")
r = report[(report['平台']=='temu') & (report['店铺']=='All F Home') & (report['月份']=='2025-07')]
if len(r) > 0:
    log(f"  报表值:   {r['平台净结算'].values[0]:,.2f} USD")
    log(f"  ✅ 匹配" if abs(temu_net - r['平台净结算'].values[0]) < 1 else f"  ❌ 差额: {abs(temu_net - r['平台净结算'].values[0]):.2f}")

# 2. SHEIN
log("\n【2. SHEIN】天基希音UK - 2025-07")
shein_file = r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台\多平台收入-7月\天基希音UK 已完成账单-账单商品维度-供货价-2025-08-05+02_55--360142954.xlsx'
# 读首行汇总
df0 = pd.read_excel(shein_file, nrows=2)
log(f"  Excel首行(汇总): {[f'{x}' for x in df0.iloc[0].tolist() if pd.notna(x)]}")
# 应收金额通常在最后
shein_total = 15135.61  # 从首行看到的应收金额
df_shein = pd.read_excel(shein_file, header=1)
for col in reversed(df_shein.columns.tolist()):
    if df_shein[col].dtype in ['float64', 'int64']:
        shein_total = df_shein[col].sum()
        log(f"  应收金额列({col[:10]}...)合计: {shein_total:,.2f}")
        break

log(f"  手工合计: {shein_total:,.2f} GBP")
r = report[(report['平台']=='shein') & (report['店铺'].str.contains('希音UK', na=False))]
if len(r) > 0:
    log(f"  报表值:   {r['平台净结算'].values[0]:,.2f} GBP")
    log(f"  ✅ 匹配" if abs(shein_total - r['平台净结算'].values[0]) < 1 else f"  ❌ 差额: {abs(shein_total - r['平台净结算'].values[0]):.2f}")

# 3. 托管店铺
log("\n【3. 托管店铺】天基托管 - 2025-07")
managed_file = r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台\多平台收入-7月\天基托管 收支明细_20250701-20250731.xlsx'
df_m = pd.read_excel(managed_file)
if '金额(CNY)' in df_m.columns:
    by_type = df_m.groupby('费用项')['金额(CNY)'].sum()
    for t, a in by_type.items():
        log(f"  {t}: {a:,.2f}")
    managed_total = df_m['金额(CNY)'].sum()
    log(f"  手工合计: {managed_total:,.2f} CNY")
    r = report[(report['平台']=='managed_store') & (report['店铺']=='天基托管') & (report['月份']=='2025-07')]
    if len(r) > 0:
        log(f"  报表值:   {r['平台净结算'].values[0]:,.2f} CNY")
        log(f"  ✅ 匹配" if abs(managed_total - r['平台净结算'].values[0]) < 1 else f"  ❌ 差额: {abs(managed_total - r['平台净结算'].values[0]):.2f}")

# 4. 速卖通
log("\n【4. 速卖通】")
ali_file = r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\速卖通\收支流水20260203182340.xlsx'
df_a = pd.read_excel(ali_file)
def parse_amt(v):
    if pd.isna(v): return 0
    s = re.sub(r'[CN￥¥\s,]', '', str(v))
    try: return float(s)
    except: return 0

df_a['amt'] = df_a['变动金额'].apply(parse_amt)
if '收支类型' in df_a.columns:
    by_type = df_a.groupby('收支类型')['amt'].sum()
    for t, a in by_type.items():
        log(f"  {t}: {a:,.2f}")
    # 排除提现
    no_transfer = df_a[~df_a['收支类型'].str.contains('提现', na=False)]
    ali_total = no_transfer['amt'].sum()
else:
    ali_total = df_a['amt'].sum()

log(f"  手工合计: {ali_total:,.2f} CNY")
r = report[report['平台']=='aliexpress']
if len(r) > 0:
    log(f"  报表值:   {r['平台净结算'].values[0]:,.2f} CNY")
    log(f"  ✅ 匹配" if abs(ali_total - r['平台净结算'].values[0]) < 1 else f"  ❌ 差额: {abs(ali_total - r['平台净结算'].values[0]):.2f}")

log("\n" + "=" * 70)

# 保存结果
with open('output/verification_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
print("\n结果已保存至 output/verification_result.txt")
