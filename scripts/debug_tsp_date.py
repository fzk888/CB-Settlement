
import sys
import os
import pandas as pd

# Add source path
sys.path.insert(0, r'd:\app\收入核算系统')

from src.parser.warehouse_parser import TSPParser, scan_warehouse_files

def debug_tsp():
    print("Debug TSP Date Parsing")
    folder = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单\TSP'
    files = scan_warehouse_files(r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单', 'TSP')
    
    parser = TSPParser()
    
    for f in files:
        fname = os.path.basename(f)
        try:
            # We want to check how the parser extracts date. 
            # The parse_file method does it internally.
            # We will use parse_file and print the meta if available, or just the returned count and we can inspect the transactions if needed (but parser currently aggregates)
            # Actually WarehouseTSPParser.parse_file returns (total_amount, breakdown_dict, count)
            # It relies on _extract_date_from_filename OR _extract_date_from_content
            
            # Let's try to call the internal method if possible, or just print the filename and let's see if we can visually spot it.
            # Better: Modify the parser to print date? No, let's just use the public methods or inspect filename first.
            
            date_from_fname = parser.extract_month(fname)
            if date_from_fname and date_from_fname.startswith('2001'):
                print(f"⚠️ FOUND 2001-01: {fname} -> {date_from_fname}")
            elif not date_from_fname:
                print(f"REJECTED: {fname}")
            
            if not date_from_fname:
                 # If not in filename, it reads content.
                 # Let's peek at the content extraction logic
                 pass

        except Exception as e:
            print(f"Error checking {fname}: {e}")

if __name__ == "__main__":
    debug_tsp()
