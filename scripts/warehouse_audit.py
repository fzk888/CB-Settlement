# -*- coding: utf-8 -*-
"""
仓库账单数据体检脚本

仅做数据检查与结构分析，不写任何解析逻辑
"""
import pandas as pd
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

output = []
def log(msg):
    print(msg)
    output.append(str(msg))

def analyze_excel_structure(file_path: str, warehouse_name: str):
    """分析 Excel 文件结构"""
    try:
        xl = pd.ExcelFile(file_path)
        sheets = xl.sheet_names
        
        result = {
            'file': Path(file_path).name,
            'sheets': sheets,
            'sheet_details': []
        }
        
        for sheet in sheets[:5]:  # 最多分析5个sheet
            try:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=10)
                cols = list(df.columns)
                
                # 分析列类型
                numeric_cols = [c for c in df.columns if df[c].dtype in ['float64', 'int64']]
                
                # 检查关键字段
                has_order = any('订单' in str(c) or 'order' in str(c).lower() for c in cols)
                has_sku = any('sku' in str(c).lower() or '产品' in str(c) for c in cols)
                has_amount = any('金额' in str(c) or '费用' in str(c) or 'cost' in str(c).lower() or 'amount' in str(c).lower() for c in cols)
                has_date = any('日期' in str(c) or '时间' in str(c) or 'date' in str(c).lower() for c in cols)
                has_currency = any('币种' in str(c) or 'currency' in str(c).lower() for c in cols)
                
                sheet_info = {
                    'sheet_name': sheet,
                    'columns': cols[:15],
                    'row_count': len(df),
                    'numeric_cols': numeric_cols[:8],
                    'has_order': has_order,
                    'has_sku': has_sku,
                    'has_amount': has_amount,
                    'has_date': has_date,
                    'has_currency': has_currency,
                }
                result['sheet_details'].append(sheet_info)
            except:
                pass
        
        return result
    except Exception as e:
        return {'file': Path(file_path).name, 'error': str(e)}


def scan_warehouse_directory(dir_path: str, warehouse_name: str):
    """扫描仓库目录"""
    log(f"\n{'='*70}")
    log(f"【{warehouse_name}】")
    log(f"{'='*70}")
    log(f"路径: {dir_path}")
    
    # 收集所有 xlsx/csv 文件
    files = []
    for root, dirs, filenames in os.walk(dir_path):
        for f in filenames:
            if f.endswith(('.xlsx', '.csv')) and not f.startswith('~$'):
                files.append(os.path.join(root, f))
    
    log(f"文件数量: {len(files)}")
    
    if not files:
        log("  (无 Excel/CSV 文件)")
        return
    
    # 分析前3个样本文件
    log(f"\n样本文件分析 (取前3个):")
    
    all_has_order = False
    all_has_sku = False
    all_has_amount = False
    
    for file_path in files[:3]:
        result = analyze_excel_structure(file_path, warehouse_name)
        
        log(f"\n  文件: {result.get('file', '')}")
        
        if 'error' in result:
            log(f"    错误: {result['error']}")
            continue
        
        log(f"    Sheets: {result.get('sheets', [])}")
        
        for sheet_info in result.get('sheet_details', []):
            log(f"\n    [{sheet_info['sheet_name']}]")
            log(f"      列名: {sheet_info['columns']}")
            log(f"      数值列: {sheet_info['numeric_cols']}")
            log(f"      有订单号: {'✓' if sheet_info['has_order'] else '✗'}")
            log(f"      有SKU: {'✓' if sheet_info['has_sku'] else '✗'}")
            log(f"      有金额: {'✓' if sheet_info['has_amount'] else '✗'}")
            log(f"      有日期: {'✓' if sheet_info['has_date'] else '✗'}")
            log(f"      有币种: {'✓' if sheet_info['has_currency'] else '✗'}")
            
            if sheet_info['has_order']:
                all_has_order = True
            if sheet_info['has_sku']:
                all_has_sku = True
            if sheet_info['has_amount']:
                all_has_amount = True
    
    # 判定账单类型
    log(f"\n账单类型判定:")
    if all_has_order and all_has_amount:
        log(f"  类型: B. 出库/履约明细账单（含单号）")
        bill_type = 'B'
    elif all_has_sku and all_has_amount:
        log(f"  类型: C. 产品维度成本表（SKU / 产品）")
        bill_type = 'C'
    elif all_has_amount:
        log(f"  类型: A. 月度费用汇总账单（无订单）")
        bill_type = 'A'
    else:
        log(f"  类型: D. 混合型账单（需进一步分析）")
        bill_type = 'D'
    
    # 可用性裁决
    log(f"\n成本可用性裁决:")
    log(f"  月度成本汇总: ✅" if all_has_amount else f"  月度成本汇总: ❌")
    log(f"  订单级匹配: {'⚠️ 可能' if all_has_order else '❌ 不支持'}")
    log(f"  SKU级匹配: {'⚠️ 可能' if all_has_sku else '❌ 不支持'}")
    
    # 可解析等级
    if all_has_order and all_has_sku:
        level = 'L3'
    elif all_has_order or all_has_sku:
        level = 'L2'
    else:
        level = 'L1'
    log(f"\n可解析等级: {level}")


# 主程序
log("=" * 70)
log("仓库账单结构审计报告")
log("生成时间: 2026-02-07")
log("=" * 70)

base_path = r'd:\app\收入核算系统\data\仓库财务账单'

# 1. 澳洲仓库
scan_warehouse_directory(os.path.join(base_path, '澳洲', 'FDM'), 'FDM (澳洲)')
scan_warehouse_directory(os.path.join(base_path, '澳洲', 'sphere freight'), 'Sphere Freight (澳洲)')

# 2. 海外仓账单 - 主要仓库
overseas_path = os.path.join(base_path, '海外仓账单')
for subdir in ['TSP', '京东', '海洋', 'LHZ', '西邮', 'G7', '1510', '东方嘉盛']:
    sub_path = os.path.join(overseas_path, subdir)
    if os.path.exists(sub_path):
        scan_warehouse_directory(sub_path, subdir)

# 3. 上海货盘
shanghai_path = os.path.join(base_path, '上海货盘费用账单')
for subdir in ['叶水福', '2024-2025.4账单']:
    sub_path = os.path.join(shanghai_path, subdir)
    if os.path.exists(sub_path):
        scan_warehouse_directory(sub_path, f'上海-{subdir}')

# 保存报告
log("\n" + "=" * 70)

with open('output/warehouse_audit_report.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("\n报告已保存至: output/warehouse_audit_report.txt")
