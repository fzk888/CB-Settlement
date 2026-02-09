# -*- coding: utf-8 -*-
"""分析各平台 Excel 字段结构 - 输出到文件"""
import pandas as pd
import os

output_lines = []

def log(msg):
    print(msg)
    output_lines.append(msg)

samples = {
    'temu': r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台\多平台收入-7月\All F Home FundDetail-1754358591792-f173.xlsx',
    'shein': r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台\多平台收入-7月\天基希音UK 已完成账单-账单商品维度-供货价-2025-08-05+02_55--360142954.xlsx',
    'managed_store': r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台\多平台收入-7月\天基托管 收支明细_20250701-20250731.xlsx',
    'aliexpress': r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\速卖通\收支流水20260203182340.xlsx',
}

for platform, path in samples.items():
    log(f"\n{'='*60}")
    log(f"平台: {platform.upper()}")
    log(f"文件: {os.path.basename(path)}")
    log('='*60)
    
    if not os.path.exists(path):
        log(f"  文件不存在")
        continue
    
    try:
        xl = pd.ExcelFile(path)
        log(f"Sheets: {xl.sheet_names}")
        
        sheet = xl.sheet_names[0]
        df = pd.read_excel(path, sheet_name=sheet, nrows=3)
        log(f"\n列名列表 ({len(df.columns)} 列):")
        for i, col in enumerate(df.columns):
            sample = df[col].dropna().head(1).tolist()
            s = str(sample[0])[:25] if sample else 'N/A'
            log(f"  {i+1:2d}. {str(col)[:30]:30s} | {s}")
    except Exception as e:
        log(f"  错误: {e}")

# 写入文件
with open('output/platform_field_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("\n\n结果已保存到: output/platform_field_analysis.txt")
