# -*- coding: utf-8 -*-
"""
Step 1: 扫描并分类 Excel 文件
自动识别 Temu / SHEIN / 托管店铺 / 速卖通
"""
import os
from pathlib import Path
from collections import defaultdict
import re

def classify_excel_file(filename: str) -> str:
    """根据文件名特征分类平台类型"""
    filename_lower = filename.lower()
    
    # Temu / 拼多多跨境
    if 'funddetail' in filename_lower:
        return 'temu'
    
    # SHEIN
    if '已完成账单' in filename or '账单商品维度' in filename:
        return 'shein'
    
    # 速卖通
    if '收支流水' in filename:
        return 'aliexpress'
    
    # 托管店铺 / 其他
    if '收支明细' in filename:
        return 'managed_store'
    
    # 未知类型
    return 'unknown'


def scan_excel_files(base_dir: str) -> dict:
    """扫描目录下所有 Excel 文件并分类"""
    results = defaultdict(list)
    
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(('.xlsx', '.xls')):
                full_path = os.path.join(root, file)
                platform = classify_excel_file(file)
                results[platform].append({
                    'filename': file,
                    'path': full_path,
                    'folder': os.path.basename(root)
                })
    
    return dict(results)


def main():
    # 扫描路径
    search_paths = [
        r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台',
        r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\速卖通',
    ]
    
    all_results = defaultdict(list)
    
    for path in search_paths:
        if os.path.exists(path):
            results = scan_excel_files(path)
            for platform, files in results.items():
                all_results[platform].extend(files)
    
    # 输出统计
    print("=" * 70)
    print("Phase 1 多平台 Excel 文件扫描结果")
    print("=" * 70)
    
    total = 0
    for platform, files in sorted(all_results.items()):
        print(f"\n【{platform.upper()}】 共 {len(files)} 个文件")
        print("-" * 50)
        
        # 按文件夹分组显示
        by_folder = defaultdict(list)
        for f in files:
            by_folder[f['folder']].append(f['filename'])
        
        for folder, filenames in sorted(by_folder.items()):
            print(f"  📁 {folder}/")
            for fname in filenames[:3]:  # 只显示前3个
                print(f"     • {fname[:60]}{'...' if len(fname) > 60 else ''}")
            if len(filenames) > 3:
                print(f"     ... 及其他 {len(filenames) - 3} 个文件")
        
        total += len(files)
    
    print("\n" + "=" * 70)
    print(f"总计: {total} 个 Excel 文件")
    print("=" * 70)
    
    # 返回结果供后续使用
    return all_results


if __name__ == '__main__':
    results = main()
