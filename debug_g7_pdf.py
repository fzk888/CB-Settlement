#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试G7 PDF文件内容
"""

import pdfplumber

def debug_pdf_content():
    pdf_path = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\G7\10月\702510206R.pdf'
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"=== 第 {page_num + 1} 页 ===")
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if 'total' in line.lower() or 'amount' in line.lower():
                        print(f"行 {i}: {repr(line)}")
                        
                # 打印最后几行，通常Total Amount在底部
                print("\n最后10行:")
                for line in lines[-10:]:
                    print(repr(line))
            else:
                print("无法提取文本")

if __name__ == '__main__':
    debug_pdf_content()