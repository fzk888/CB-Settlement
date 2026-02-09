# -*- coding: utf-8 -*-
"""
详细验证每个仓库的解析逻辑
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


def detailed_verify_tsp():
    """详细验证 TSP"""
    print("\n" + "="*70)
    print("【TSP 详细验证】")
    print("="*70)
    
    files = scan_warehouse_files(BASE_PATH, "TSP")
    print(f"文件数: {len(files)}")
    
    parser = TSPParser()
    sample_file = files[0]
    print(f"\n抽样: {os.path.basename(sample_file)}")
    
    xl = pd.ExcelFile(sample_file)
    print(f"Sheets: {xl.sheet_names}")
    
    # 检查每个 sheet
    for sheet in xl.sheet_names:
        df = pd.read_excel(sample_file, sheet_name=sheet)
        print(f"\n--- {sheet} ---")
        print(f"列: {list(df.columns)[:8]}")
        print(f"行数: {len(df)}")
        
        # 找 cost 列
        cost_cols = [c for c in df.columns if 'cost' in str(c).lower()]
        if cost_cols:
            for c in cost_cols:
                total = df[c].apply(lambda x: float(x) if pd.notna(x) else 0).sum()
                print(f"  列 [{c}] 合计: {total:,.2f}")
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample_file)
    print(f"\n解析器结果: {total:,.2f} ({count} 条)")


def detailed_verify_1510():
    """详细验证 1510"""
    print("\n" + "="*70)
    print("【1510 详细验证】")
    print("="*70)
    
    files = scan_warehouse_files(BASE_PATH, "1510")
    print(f"文件数: {len(files)}")
    
    parser = Warehouse1510Parser()
    sample_file = files[0]
    print(f"\n抽样: {os.path.basename(sample_file)}")
    
    xl = pd.ExcelFile(sample_file)
    print(f"Sheets: {xl.sheet_names}")
    
    # 检查每个 sheet
    for sheet in xl.sheet_names[:5]:
        df = pd.read_excel(sample_file, sheet_name=sheet)
        print(f"\n--- {sheet} ---")
        print(f"列: {list(df.columns)[:10]}")
        print(f"行数: {len(df)}")
        
        # 找费用列
        fee_cols = [c for c in df.columns if any(k in str(c) for k in ['费', 'fee', 'charge', 'cost', '金额'])]
        if fee_cols:
            for c in fee_cols[:3]:
                try:
                    # 清洗数据
                    vals = df[c].apply(lambda x: float(str(x).replace(',','')) if pd.notna(x) and str(x).replace(',','').replace('.','').replace('-','').isdigit() else 0)
                    total = vals.sum()
                    if total != 0:
                        print(f"  列 [{c}] 合计: {total:,.2f}")
                except:
                    pass
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample_file)
    print(f"\n解析器结果: {total:,.2f} ({count} 条)")


def detailed_verify_jd():
    """详细验证 京东"""
    print("\n" + "="*70)
    print("【京东 详细验证】")
    print("="*70)
    
    files = scan_warehouse_files(BASE_PATH, "京东")
    print(f"文件数: {len(files)}")
    
    parser = JDParser()
    sample_file = files[0]
    print(f"\n抽样: {os.path.basename(sample_file)}")
    
    xl = pd.ExcelFile(sample_file)
    print(f"Sheets: {xl.sheet_names}")
    
    # 检查关键 sheet
    for sheet in xl.sheet_names[:3]:
        df = pd.read_excel(sample_file, sheet_name=sheet)
        print(f"\n--- {sheet} ---")
        print(f"列: {list(df.columns)[:10]}")
        print(f"行数: {len(df)}")
        
        # 找金额列
        amount_cols = [c for c in df.columns if any(k in str(c) for k in ['金额', '含税', '结算', 'Amount'])]
        if amount_cols:
            for c in amount_cols[:2]:
                try:
                    total = df[c].apply(lambda x: float(x) if pd.notna(x) else 0).sum()
                    if total != 0:
                        print(f"  列 [{c}] 合计: {total:,.2f}")
                except:
                    pass
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample_file)
    print(f"\n解析器结果: {total:,.2f} ({count} 条)")


def detailed_verify_haiyang():
    """详细验证 海洋"""
    print("\n" + "="*70)
    print("【海洋 详细验证】")
    print("="*70)
    
    files = scan_warehouse_files(BASE_PATH, "海洋")
    print(f"文件数: {len(files)}")
    
    parser = HaiyangParser()
    sample_file = files[0]
    print(f"\n抽样: {os.path.basename(sample_file)}")
    
    xl = pd.ExcelFile(sample_file)
    print(f"Sheets: {xl.sheet_names}")
    
    # 检查每个 sheet
    for sheet in xl.sheet_names[:3]:
        df = pd.read_excel(sample_file, sheet_name=sheet)
        print(f"\n--- {sheet} ---")
        print(f"列: {list(df.columns)}")
        print(f"行数: {len(df)}")
        print(f"前3行:\n{df.head(3).to_string()}")
        
        # 找结算金额
        amt_cols = [c for c in df.columns if any(k in str(c) for k in ['金额', '结算', 'Amount'])]
        if amt_cols:
            for c in amt_cols:
                try:
                    total = df[c].apply(lambda x: float(x) if pd.notna(x) else 0).sum()
                    if total != 0:
                        print(f"  列 [{c}] 合计: {total:,.2f}")
                except:
                    pass
    
    # 解析器结果
    total, breakdown, count = parser.parse_file(sample_file)
    print(f"\n解析器结果: {total:,.2f} ({count} 条)")


def main():
    detailed_verify_tsp()
    detailed_verify_1510()
    detailed_verify_jd()
    detailed_verify_haiyang()


if __name__ == '__main__':
    main()
