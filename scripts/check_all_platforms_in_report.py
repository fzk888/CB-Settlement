#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查报表中所有平台的数据分布
找出TEMU数据可能的去向
"""

import pandas as pd
import os
from pathlib import Path

def analyze_report_platforms(report_path):
    """分析报表中各平台的数据分布"""
    try:
        xls = pd.ExcelFile(report_path)
        print(f"报表工作表: {xls.sheet_names}")
        
        for sheet_name in xls.sheet_names:
            print(f"\n=== {sheet_name} ===")
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            if '店铺月度汇总' in sheet_name:
                # 分析店铺月度汇总
                print("店铺分布:")
                store_counts = df['店铺'].value_counts()
                for store, count in store_counts.items():
                    print(f"  {store}: {count} 条记录")
                
                print("\n平台分布:")
                if '平台' in df.columns:
                    platform_counts = df['平台'].value_counts()
                    for platform, count in platform_counts.items():
                        print(f"  {platform}: {count} 条记录")
                else:
                    print("  未找到平台列")
                
                print("\n月份分布:")
                month_counts = df['月份'].value_counts().sort_index()
                for month, count in month_counts.items():
                    print(f"  {month}: {count} 条记录")
                    
            elif '详细交易记录' in sheet_name:
                # 分析详细交易记录
                print("前10条记录预览:")
                print(df.head(10)[['日期', '店铺', '平台', '币种', '收入', '成本', '净收入']].to_string())
                
                print("\n平台分布:")
                if '平台' in df.columns:
                    platform_counts = df['平台'].value_counts()
                    for platform, count in platform_counts.items():
                        print(f"  {platform}: {count} 条记录")
                        
                # 查看是否有类似TEMU的店铺名
                print("\n包含'Home'的店铺:")
                home_stores = df[df['店铺'].str.contains('Home', case=False, na=False)]['店铺'].unique()
                for store in home_stores:
                    print(f"  {store}")
                    
    except Exception as e:
        print(f"分析报表失败: {e}")

def main():
    """主函数"""
    report_path = r"d:\app\收入核算系统\output\月度核算报表_Phase1_多平台.xlsx"
    analyze_report_platforms(report_path)

if __name__ == "__main__":
    main()