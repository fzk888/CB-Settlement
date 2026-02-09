# -*- coding: utf-8 -*-
"""
仓库账单解析器验证脚本

对每个仓库的解析结果进行抽检验证
"""
import pandas as pd
from decimal import Decimal
import os
import sys
sys.path.insert(0, r'd:\app\收入核算系统')

from src.parser.warehouse_parser import (
    TSPParser, Warehouse1510Parser, JDParser, HaiyangParser, LHZParser,
    scan_warehouse_files
)

import warnings
warnings.filterwarnings('ignore')

BASE_PATH = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单'


def verify_warehouse(wh_name: str, parser, sample_count: int = 2):
    """验证一个仓库的解析器"""
    print(f"\n{'='*60}")
    print(f"【{wh_name}】验证")
    print(f"{'='*60}")
    
    files = scan_warehouse_files(BASE_PATH, wh_name)
    print(f"找到 {len(files)} 个文件")
    
    if not files:
        print("  ❌ 无文件")
        return
    
    # 抽样验证
    sample_files = files[:sample_count]
    
    for fp in sample_files:
        print(f"\n--- 文件: {os.path.basename(fp)} ---")
        
        try:
            # 解析器结果
            total, breakdown, count = parser.parse_file(fp)
            month = parser.extract_month(os.path.basename(fp))
            
            print(f"  解析月份: {month}")
            print(f"  解析总成本: {total:,.2f} {parser.currency}")
            print(f"  解析记录数: {count}")
            print(f"  分类明细:")
            for k, v in list(breakdown.items())[:5]:
                print(f"    {k}: {v:,.2f}")
            
            # 手动验证 - 读取原始文件对比
            xl = pd.ExcelFile(fp)
            print(f"  原始Sheets: {xl.sheet_names}")
            
            # 对比逻辑
            manual_total = Decimal('0')
            for sheet in xl.sheet_names[:3]:
                df = pd.read_excel(fp, sheet_name=sheet)
                # 找金额列
                amount_cols = [c for c in df.columns if any(k in str(c).lower() for k in ['cost', 'fee', '金额', '费用', '总计', 'total', 'amount'])]
                if amount_cols:
                    for col in amount_cols[:1]:
                        try:
                            col_sum = df[col].apply(lambda x: float(x) if pd.notna(x) and str(x).replace('.','').replace('-','').replace(',','').isdigit() else 0).sum()
                            if col_sum > 0:
                                print(f"    Sheet [{sheet}] 列 [{col}] 合计: {col_sum:,.2f}")
                                manual_total += Decimal(str(col_sum))
                        except:
                            pass
            
            # 对比结果
            if manual_total > 0:
                diff_pct = abs(float(total - manual_total) / float(manual_total) * 100) if manual_total else 0
                if diff_pct < 5:
                    print(f"  ✅ 解析准确 (误差 {diff_pct:.1f}%)")
                else:
                    print(f"  ⚠️ 可能有问题 (解析 {total:,.2f} vs 抽检 {manual_total:,.2f}, 差 {diff_pct:.1f}%)")
            
        except Exception as e:
            print(f"  ❌ 解析错误: {e}")


def main():
    print("=" * 70)
    print(" 仓库账单解析器验证报告")
    print("=" * 70)
    
    # 验证每个仓库
    verify_warehouse("TSP", TSPParser(), sample_count=2)
    verify_warehouse("1510", Warehouse1510Parser(), sample_count=2)
    verify_warehouse("京东", JDParser(), sample_count=2)
    verify_warehouse("海洋", HaiyangParser(), sample_count=2)
    verify_warehouse("LHZ", LHZParser(), sample_count=2)
    
    # 汇总对比
    print(f"\n\n{'='*70}")
    print(" Phase 2 报表数据汇总验证")
    print("{'='*70}")
    
    report_path = r'd:\app\收入核算系统\output\月度核算报表_Phase2.xlsx'
    df = pd.read_excel(report_path, sheet_name='仓库成本汇总')
    
    print("\n【按仓库汇总】")
    summary = df.groupby('仓库')['履约成本合计'].sum()
    print(summary.to_string())
    
    print(f"\n【总成本】{df['履约成本合计'].sum():,.2f}")


if __name__ == '__main__':
    main()
