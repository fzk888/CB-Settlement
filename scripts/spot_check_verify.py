# -*- coding: utf-8 -*-
"""
逐仓库对账验证 - 对比解析器输出 vs 原始文件 Excel 合计
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


def test_tsp():
    """TSP 抽检"""
    print("="*70)
    print("【TSP】抽检验证")
    print("="*70)
    
    parser = TSPParser()
    files = scan_warehouse_files(BASE_PATH, "TSP")
    sample = files[5] if len(files) > 5 else files[0]
    
    print(f"抽样: {os.path.basename(sample)}")
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample)
    print(f"解析器: {total:,.2f} GBP, {count} 条")
    
    # 手动计算
    manual = Decimal('0')
    xl = pd.ExcelFile(sample)
    for sheet in xl.sheet_names:
        df = pd.read_excel(sample, sheet_name=sheet)
        for c in df.columns:
            if 'cost' in str(c).lower():
                s = df[c].apply(lambda x: float(x) if pd.notna(x) else 0).sum()
                print(f"  [{sheet}][{c}]: {s:,.2f}")
                manual += Decimal(str(s))
    
    print(f"手动: {manual:,.2f} GBP")
    print(f"差异: {float(total - manual):,.2f} ({abs(float(total - manual) / float(manual) * 100) if manual else 0:.1f}%)")


def test_1510():
    """1510 抽检"""
    print("\n" + "="*70)
    print("【1510】抽检验证")
    print("="*70)
    
    parser = Warehouse1510Parser()
    files = scan_warehouse_files(BASE_PATH, "1510")
    sample = files[3] if len(files) > 3 else files[0]
    
    print(f"抽样: {os.path.basename(sample)}")
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample)
    print(f"解析器: {total:,.2f} GBP, {count} 条")
    print(f"分项: {list(breakdown.items())[:5]}")
    
    # 手动计算 - 看原始文件的账单封面汇总
    xl = pd.ExcelFile(sample)
    print(f"Sheets: {xl.sheet_names}")
    
    # 账单封面通常有汇总
    if '账单封面Bill cover' in xl.sheet_names:
        df = pd.read_excel(sample, sheet_name='账单封面Bill cover')
        print(f"\n账单封面Bill cover:")
        print(df.to_string())


def test_jd():
    """京东 抽检"""
    print("\n" + "="*70)
    print("【京东】抽检验证")
    print("="*70)
    
    parser = JDParser()
    files = scan_warehouse_files(BASE_PATH, "京东")
    sample = files[2] if len(files) > 2 else files[0]
    
    print(f"抽样: {os.path.basename(sample)}")
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample)
    print(f"解析器: {total:,.2f} CNY, {count} 条")
    
    # 手动计算 - 汇总页
    xl = pd.ExcelFile(sample)
    print(f"Sheets: {xl.sheet_names}")
    
    if '汇总页' in xl.sheet_names:
        df = pd.read_excel(sample, sheet_name='汇总页')
        print(f"\n汇总页:")
        print(df.to_string())


def test_haiyang():
    """海洋 抽检"""
    print("\n" + "="*70)
    print("【海洋】抽检验证")
    print("="*70)
    
    parser = HaiyangParser()
    files = scan_warehouse_files(BASE_PATH, "海洋")
    sample = files[3] if len(files) > 3 else files[0]
    
    print(f"抽样: {os.path.basename(sample)}")
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample)
    print(f"解析器: {total:,.2f} GBP, {count} 条")
    
    # 手动计算
    df = pd.read_excel(sample)
    if '结算金额' in df.columns:
        manual = df['结算金额'].sum()
        print(f"手动 [结算金额] 合计: {manual:,.2f} GBP")
        print(f"差异: {float(total) - float(manual):,.2f}")


def test_lhz():
    """LHZ 抽检"""
    print("\n" + "="*70)
    print("【LHZ】抽检验证")
    print("="*70)
    
    parser = LHZParser()
    files = scan_warehouse_files(BASE_PATH, "LHZ")
    sample = files[2] if len(files) > 2 else files[0]
    
    print(f"抽样: {os.path.basename(sample)}")
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample)
    print(f"解析器: {total:,.2f} EUR, {count} 条")
    print(f"分项: {breakdown}")
    
    # 手动计算 - 看总计 sheet
    xl = pd.ExcelFile(sample)
    print(f"Sheets: {xl.sheet_names}")
    
    if '总计' in xl.sheet_names:
        df = pd.read_excel(sample, sheet_name='总计')
        print(f"\n总计 Sheet:")
        print(df.to_string())


def phase2_report_summary():
    """Phase 2 报表汇总对比"""
    print("\n" + "="*70)
    print("【Phase 2 报表汇总】")
    print("="*70)
    
    f = r'd:\app\收入核算系统\output\月度核算报表_Phase2.xlsx'
    df = pd.read_excel(f, sheet_name='仓库成本汇总')
    
    # 按仓库汇总
    summary = df.groupby('仓库').agg({
        '履约成本合计': 'sum',
        '记录数': 'sum',
        '文件数': 'sum'
    })
    print(summary)
    
    print(f"\n总成本: {df['履约成本合计'].sum():,.2f}")


if __name__ == '__main__':
    test_tsp()
    test_1510()
    test_jd()
    test_haiyang()
    test_lhz()
    phase2_report_summary()
