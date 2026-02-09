# -*- coding: utf-8 -*-
"""
仓库账单数据分析脚本
分析各仓库账单Excel文件的字段结构和内容
"""
import os
from pathlib import Path
from collections import Counter
import pandas as pd

def analyze_excel_file(file_path, max_rows=10):
    """分析单个Excel文件"""
    print(f"\n{'='*60}")
    print(f"文件: {Path(file_path).name}")
    print('='*60)
    
    try:
        # 尝试读取所有工作表
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        print(f"工作表: {sheet_names}")
        
        for sheet in sheet_names[:2]:  # 只分析前2个工作表
            print(f"\n--- 工作表: {sheet} ---")
            df = pd.read_excel(file_path, sheet_name=sheet, dtype=str, nrows=100)
            
            print(f"列数: {len(df.columns)}, 行数: {len(df)}")
            print(f"\n列名:")
            for i, col in enumerate(df.columns):
                # 获取非空值数量
                non_null = df[col].notna().sum()
                print(f"  {i+1:2}. {col} (非空: {non_null})")
            
            # 显示前几行数据
            print(f"\n前{min(5, len(df))}行数据:")
            for idx, row in df.head(5).iterrows():
                print(f"\n  行 {idx}:")
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val) and str(val).strip():
                        print(f"    {col}: {str(val)[:50]}")
        
        return True
    except Exception as e:
        print(f"读取失败: {e}")
        return False

def main():
    base_dir = Path(r'd:/app/收入核算系统/跨境电商数据/财务账单/海外仓账单')
    
    # 1. 分析东方嘉盛账单
    print("\n" + "="*80)
    print("【东方嘉盛账单分析】")
    print("="*80)
    dfjsh_dir = base_dir / "东方嘉盛"
    for f in sorted(dfjsh_dir.glob("*.xlsx"))[:1]:  # 只分析第一个
        analyze_excel_file(f)
    
    # 2. 分析TLB账单
    print("\n" + "="*80)
    print("【TLB账单分析】")
    print("="*80)
    tlb_dir = base_dir / "TLB账单"
    for f in sorted(tlb_dir.glob("*.xlsx"))[:1]:
        analyze_excel_file(f)
    
    # 3. 分析G7账单
    print("\n" + "="*80)
    print("【G7账单分析】")
    print("="*80)
    g7_dir = base_dir / "G7"
    # 查找子目录中的文件
    for sub_dir in sorted(g7_dir.iterdir())[:1]:
        if sub_dir.is_dir():
            print(f"\n子目录: {sub_dir.name}")
            for f in sorted(sub_dir.glob("*"))[:3]:
                print(f"  - {f.name}")
                if f.suffix.lower() == '.xlsx':
                    analyze_excel_file(f)
                elif f.suffix.lower() == '.pdf':
                    print(f"    (PDF文件，需要专用解析器)")
    
    # 4. 分析易达云账单
    print("\n" + "="*80)
    print("【易达云账单分析】")
    print("="*80)
    ydy_dir = base_dir / "易达云"
    if ydy_dir.exists():
        for f in sorted(ydy_dir.glob("*.xlsx"))[:1]:
            analyze_excel_file(f)
        for f in sorted(ydy_dir.glob("*.xls"))[:1]:
            analyze_excel_file(f)

if __name__ == '__main__':
    main()
