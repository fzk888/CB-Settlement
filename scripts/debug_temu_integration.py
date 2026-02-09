
import sys
import warnings
from pathlib import Path
from decimal import Decimal
import pandas as pd

# 忽略 openpyxl 警告
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# 添加源码路径
sys.path.insert(0, r'd:\app\收入核算系统')

from src.parser.temu_parser import TemuParser

def debug_temu():
    print("Debug Temu Parser Integration")
    f_path = r'd:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月\Boutique local FundDetail-1762143796093-afd2.xlsx'
    
    parser = TemuParser()
    print(f"Parsing file: {f_path}")
    
    # Check checks in parser
    print(f"SHEET_TYPE_MAP keys: {list(parser.SHEET_TYPE_MAP.keys())}")
    
    txns, meta = parser.parse(f_path)
    print(f"Total transactions: {len(txns)}")
    
    total = sum(t.total for t in txns)
    print(f"Total Amount: {total}")
    
    for t in txns:
        if t.total > 0:
            print(f"Positive txn: {t.type_raw} - {t.total}")
            break
            
if __name__ == "__main__":
    debug_temu()
