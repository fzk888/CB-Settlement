# -*- coding: utf-8 -*-
"""仓库账单字段分析 - 使用正确路径"""
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

output = []
def log(msg):
    print(msg)
    output.append(str(msg))

log("=" * 70)
log("Phase 2.1 仓库账单字段分析报告")
log("=" * 70)

samples = [
    {
        'name': 'TSP仓库 (英国)',
        'file': r'd:\app\收入核算系统\跨境电商数据\财务账单\海外仓账单\TSP\Invoice - HupperTek Jul25 Wk1 - 08_07_2025 14_47_37.xlsx',
    },
    {
        'name': '京东海外仓',
        'file': r'd:\app\收入核算系统\跨境电商数据\财务账单\海外仓账单\京东\费用明细_16d11318-746b-438c-a378-dd14e64aec93_1747498685700.xlsx',
    },
    {
        'name': 'LHZ仓库',
        'file': r'd:\app\收入核算系统\跨境电商数据\财务账单\海外仓账单\LHZ\开票费用明细 05-2025 HUP xlsx.xlsx',
    },
    {
        'name': '海洋仓库',
        'file': r'd:\app\收入核算系统\跨境电商数据\财务账单\海外仓账单\海洋\2025-7月_CostBillExport1599.xlsx',
    },
    {
        'name': '西邮仓库 (美国-TEMU)',
        'file': r'd:\app\收入核算系统\跨境电商数据\财务账单\海外仓账单\西邮\AAB57--US--TEMU--西邮物流仓储账单--2025.07.01-2025.07.31--初版.xlsx',
    },
]

for s in samples:
    log(f"\n{'='*60}")
    log(f"【{s['name']}】")
    log(f"{'='*60}")
    log(f"文件: {s['file'].split(chr(92))[-1]}")
    
    try:
        xl = pd.ExcelFile(s['file'])
        log(f"Sheets: {xl.sheet_names[:5]}")
        
        # 读取第一个sheet
        df = pd.read_excel(s['file'], sheet_name=0)
        log(f"列数: {len(df.columns)}, 行数: {len(df)}")
        log(f"\n列名列表:")
        for i, c in enumerate(df.columns):
            if i < 15:
                log(f"  {i+1}. {c}")
        if len(df.columns) > 15:
            log(f"  ... (共{len(df.columns)}列)")
        
        # 数值列
        numeric_cols = [c for c in df.columns if df[c].dtype in ['float64', 'int64']]
        if numeric_cols:
            log(f"\n数值列(可能是金额): {numeric_cols[:8]}")
        
        # 前2行样本
        log(f"\n前2行数据样本:")
        for idx, row in df.head(2).iterrows():
            log(f"  Row {idx}: {dict(list(row.items())[:6])}")
        
    except Exception as e:
        log(f"读取失败: {e}")

log("\n" + "=" * 70)

with open('output/warehouse_field_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
print("\n结果已保存至 output/warehouse_field_analysis.txt")
