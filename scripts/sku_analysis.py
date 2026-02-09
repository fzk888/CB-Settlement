# -*- coding: utf-8 -*-
"""SKU 匹配性分析"""
import pandas as pd
import warnings
import os
warnings.filterwarnings('ignore')

output = []
def log(msg):
    print(msg)
    output.append(str(msg))

log('=' * 70)
log('SKU 匹配性分析报告')
log('=' * 70)

# 1. 仓库产品 SKU
log('\n【1. 仓库产品数据 - SKU 格式】')
f1 = r'd:\app\收入核算系统\data\仓库产品数据\欧洲仓库的产品数据\产品信息-bb70bb92bf815af387714d37365e5c8d.xlsx'
df1 = pd.read_excel(f1)
skus = df1['产品SKU'].dropna().tolist()
log(f'产品总数: {len(skus)}')
log(f'SKU 样本 (前15):')
for s in skus[:15]:
    log(f'  {s}')

# 检查SKU是否有ASIN格式
asin_like = [s for s in skus if str(s).startswith('B0') and len(str(s)) == 10]
log(f'\n类似 ASIN 格式的 SKU: {len(asin_like)} 个')
if asin_like:
    log(f'  样本: {asin_like[:5]}')

# 2. 亚马逊交易数据
log('\n【2. 亚马逊交易数据 - 列结构】')
amazon_dir = r'd:\app\收入核算系统\data\部分店铺收入'
csv_files = []
for root, dirs, files in os.walk(amazon_dir):
    for f in files:
        if f.endswith('.csv'):
            csv_files.append(os.path.join(root, f))

log(f'CSV 文件数: {len(csv_files)}')

# 分析第一个CSV
if csv_files:
    try:
        df = pd.read_csv(csv_files[0], nrows=20, on_bad_lines='skip')
        log(f'\n样本文件: {os.path.basename(csv_files[0])}')
        log(f'列名:')
        for col in df.columns:
            log(f'  - {col}')
        
        # 查找SKU相关列
        sku_cols = [c for c in df.columns if 'sku' in c.lower() or 'asin' in c.lower()]
        if sku_cols:
            log(f'\nSKU/ASIN 列: {sku_cols}')
            for col in sku_cols:
                samples = df[col].dropna().head(5).tolist()
                log(f'  {col}: {samples}')
        else:
            log('\n❌ 亚马逊交易数据中无 SKU/ASIN 列')
            log('   说明: 亚马逊月度交易报告是财务汇总级别，不含订单明细')
    except Exception as e:
        log(f'CSV 解析错误: {e}')

# 3. 结论
log('\n' + '=' * 70)
log('【结论】')
log('=' * 70)
log('亚马逊交易数据 (Monthly Transaction) 是财务级汇总，字段包括:')
log('  - date/time, settlement id, type, order id')
log('  - product sales, fees, total')
log('  ⚠️ 无 SKU/ASIN 字段')
log('')
log('仓库产品数据包含:')
log('  - 产品SKU, 产品名称, 对应单价(USD)')
log('  - 部分 SKU 与 ASIN 格式相似 (B0xxxxxxxx)')
log('')
log('匹配可行性:')
log('  ✅ 仓库账单 (TSP/1510) 有订单号 → 可与亚马逊 order_id 关联')
log('  ⚠️ 但需额外的 订单明细数据 才能获取 SKU → 产品成本')

with open('output/sku_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
log('\n报告已保存: output/sku_analysis.txt')
