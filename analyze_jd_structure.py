import pandas as pd
import os

def analyze_file(file_path, month):
    print(f"\n=== {month} - {os.path.basename(file_path)} ===")
    df = pd.read_excel(file_path, sheet_name=0, header=None)
    
    # 查找结算币种含税金额字段
    for i in range(20):
        for j in range(df.shape[1]):
            cell = df.iloc[i, j]
            if pd.notna(cell) and '结算币种含税金额' in str(cell):
                print(f"Field found at row {i}, col {j}")
                # 检查右侧几列的值
                for offset in range(1, 5):
                    if j + offset < df.shape[1]:
                        value = df.iloc[i, j + offset]
                        if pd.notna(value):
                            try:
                                float_val = float(value)
                                print(f"  Value at offset +{offset} (col {j + offset}): {float_val}")
                                break
                            except:
                                print(f"  Non-numeric at offset +{offset} (col {j + offset}): {value}")
                        else:
                            print(f"  NaN at offset +{offset} (col {j + offset})")
                return

# 测试不同月份的文件
test_files = [
    ('March', 'data/仓库财务账单/海外仓账单/京东/2025-03/费用明细_606ac359-5d0a-41ab-983f-d43436d9580d_1744885711874.xlsx'),
    ('October', 'data/仓库财务账单/海外仓账单/京东/2025-10/KH9220000002310_海外物流仓储服务费-全球_2025-10-01_2025-10-15_BR1979085385791279104_9b3484.xlsx'),
    ('September', 'data/仓库财务账单/海外仓账单/京东/2025-09/费用明细_c3d72c8b-f000-4435-a0a3-c83c30ada3a5_1758126181450.xlsx')
]

for month, file_path in test_files:
    if os.path.exists(file_path):
        analyze_file(file_path, month)