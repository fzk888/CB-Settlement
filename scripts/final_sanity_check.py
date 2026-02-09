import pandas as pd
import sys
import os

def check_phase2_report():
    f = r'd:\app\收入核算系统\output\月度核算报表_Phase2.xlsx'
    if not os.path.exists(f):
        print(f"Report file not found: {f}")
        return

    print("=== Phase 2 Report Sanity Check ===")
    
    try:
        # Platform Revenue Check
        df_rev = pd.read_excel(f, sheet_name='平台收入汇总')
        print(f"\n[Platform Revenue] Total Records: {len(df_rev)}")
        
        # 1. Negative Revenue
        neg_rev = df_rev[df_rev['平台净结算'] < 0]
        if not neg_rev.empty:
            print("\n⚠️ Negative Revenue Records:")
            print(neg_rev[['平台', '店铺', '月份', '平台净结算']].to_string())
        
        # 2. Zero Revenue with Transactions
        zero_rev = df_rev[(df_rev['平台净结算'] == 0) & (df_rev['交易数'] > 0)]
        if not zero_rev.empty:
            print("\n⚠️ Zero Revenue with Transactions:")
            print(zero_rev[['平台', '店铺', '月份', '交易数']].to_string())
            
        # 3. Missing Platforms
        expected_platforms = ['amazon', 'temu', 'shein', 'managed_store', 'aliexpress']
        actual_platforms = df_rev['平台'].unique()
        missing_platforms = set(expected_platforms) - set(actual_platforms)
        if missing_platforms:
             print(f"\n⚠️ Missing Platforms: {missing_platforms}")
        else:
             print("\n✅ All expected platforms present.")

        # Warehouse Cost Check
        df_cost = pd.read_excel(f, sheet_name='仓库成本汇总')
        print(f"\n[Warehouse Cost] Total Records: {len(df_cost)}")
        
        # 4. Zero Cost
        zero_cost = df_cost[df_cost['履约成本合计'] == 0]
        if not zero_cost.empty:
            print("\n⚠️ Zero Cost Records:")
            print(zero_cost[['月份', '仓库', '履约成本合计']].to_string())
            
        # 5. Missing Warehouses
        expected_warehouses = ['TSP', '1510', '京东', 'LHZ', '海洋', '西邮']
        actual_warehouses = df_cost['仓库'].unique()
        missing_warehouses = set(expected_warehouses) - set(actual_warehouses)
        if missing_warehouses:
            print(f"\n⚠️ Missing Warehouses: {missing_warehouses}")
            # Note: West Post (西邮) might be P3/Manual so acceptable to missing
        else:
            print("\n✅ All expected warehouses present.")

        # Summary Check
        df_summary = pd.read_excel(f, sheet_name='综合损益概览')
        print(f"\n[Summary] Total Records: {len(df_summary)}")
        
        # 6. Negative Profit (Gross)
        neg_profit = df_summary[df_summary['毛利(不含商品成本)'] < 0]
        if not neg_profit.empty:
             print("\n⚠️ Negative Gross Profit Months:")
             print(neg_profit[['月份', '平台总收入', '仓库总成本', '毛利(不含商品成本)', '备注']].to_string())

        print("\n=== Check Complete ===")

    except Exception as e:
        print(f"Error checking report: {e}")

if __name__ == "__main__":
    check_phase2_report()
