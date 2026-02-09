import sys
sys.path.append(r'd:\app\收入核算系统')
from src.parser.temu_parser import TemuParser

f = r'd:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-10月\Boutique local FundDetail-1762143796093-afd2.xlsx'
parser = TemuParser()
try:
    txns, meta = parser.parse(f)
    print(f"Total entries: {len(txns)}")
    
    total_amount = sum(t.total for t in txns)
    print(f"Total Amount: {total_amount}")
    
    # Check breakdown by type
    breakdown = {}
    for t in txns:
        breakdown[t.type_raw] = breakdown.get(t.type_raw, 0) + t.total
    
    print("\nBreakdown by sheet:")
    for k, v in breakdown.items():
        print(f"  {k}: {v}")

except Exception as e:
    print(f"Error: {e}")
