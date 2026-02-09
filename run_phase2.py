# -*- coding: utf-8 -*-
"""
Phase 2: 平台收入 × 仓库履约成本

阶段边界：
- ✅ 平台收入汇总（Phase 1）
- ✅ 仓库履约成本汇总（本阶段）
- ❌ 不做 SKU 级成本
- ❌ 不做订单级匹配
"""
import pandas as pd
from decimal import Decimal
from pathlib import Path
from datetime import datetime
import warnings
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.parser.warehouse_parser import aggregate_warehouse_costs, WarehouseMonthlyCost

warnings.filterwarnings('ignore')


def run_phase2():
    """Phase 2 主入口"""
    print("=" * 70)
    print(" Phase 2: 平台收入 × 仓库履约成本")
    print(" 限制: 不含 SKU 级成本，不做订单级匹配")
    print("=" * 70)
    
    # 路径配置
    platform_data_path = Path(r'd:\app\收入核算系统\data\部分店铺收入')
    warehouse_data_path = Path(r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单')
    output_path = Path(r'd:\app\收入核算系统\output')
    
    # === 1. 平台收入汇总 (沿用 Phase 1 结果) ===
    print("\n[1] 加载平台收入数据...")
    
    # 尝试多个可能的 Phase 1 报表
    possible_reports = [
        output_path / '月度核算报表_Phase1_多平台.xlsx',
        output_path / '月度核算报表_Phase1.xlsx',
        output_path / '多平台核算报表.xlsx',
    ]
    
    phase1_report = None
    for rp in possible_reports:
        if rp.exists():
            phase1_report = rp
            break
    
    platform_revenue = []
    if phase1_report:
        try:
            df = pd.read_excel(phase1_report)
            print(f"  从 Phase 1 报表加载 {len(df)} 条记录")
            platform_revenue = df.to_dict('records')
        except Exception as e:
            print(f"  加载失败: {e}")
    else:
        print(f"  Phase 1 报表不存在: {phase1_report}")
        print("  请先运行 run_phase1_multiplatform.py")
    
    # === 2. 仓库履约成本汇总 ===
    print("\n[2] 汇总仓库履约成本...")
    
    warehouses = ['TSP', '1510', '京东', '海洋', 'LHZ']
    warehouse_costs = aggregate_warehouse_costs(str(warehouse_data_path), warehouses)
    
    print(f"  共解析 {len(warehouse_costs)} 条仓库月度记录")
    
    # 按仓库统计
    wh_summary = {}
    for c in warehouse_costs:
        if c.warehouse_name not in wh_summary:
            wh_summary[c.warehouse_name] = Decimal('0')
        wh_summary[c.warehouse_name] += c.total_cost
    
    for wh, total in wh_summary.items():
        print(f"    {wh}: {total:,.2f}")
    
    # === 3. 生成 Phase 2 报表 ===
    print("\n[3] 生成 Phase 2 报表...")
    
    output_file = output_path / '月度核算报表_Phase2.xlsx'
    
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: 平台收入汇总
            if platform_revenue:
                df_platform = pd.DataFrame(platform_revenue)
                df_platform.to_excel(writer, sheet_name='平台收入汇总', index=False)
                print(f"  - 平台收入汇总: {len(df_platform)} 行")
            
            # Sheet 2: 仓库成本汇总
            warehouse_rows = []
            for c in sorted(warehouse_costs, key=lambda x: (x.year_month, x.warehouse_name)):
                warehouse_rows.append({
                    '月份': c.year_month,
                    '仓库': c.warehouse_name,
                    '区域': {'TSP': 'UK', '1510': 'UK', '京东': 'Global', '海洋': 'UK', 'LHZ': 'DE'}.get(c.warehouse_name, '-'),
                    '履约成本合计': float(c.total_cost),
                    '币种': c.currency,
                    '记录数': c.record_count,
                    '文件数': len(c.source_files),
                })
            
            df_warehouse = pd.DataFrame(warehouse_rows)
            df_warehouse.to_excel(writer, sheet_name='仓库成本汇总', index=False)
            print(f"  - 仓库成本汇总: {len(df_warehouse)} 行")
            
            # Sheet 3: 综合损益概览
            # 按月份汇总
            monthly_summary = {}
            
            # 平台收入按月汇总
            if platform_revenue:
                for row in platform_revenue:
                    # 月份列
                    month_val = str(row.get('月份', ''))[:7] if '月份' in row else None
                    
                    if not month_val:
                        continue
                    
                    if month_val not in monthly_summary:
                        monthly_summary[month_val] = {'收入': Decimal('0'), '成本': Decimal('0')}
                    
                    # 收入列 (平台净结算)
                    revenue_val = row.get('平台净结算', 0)
                    if revenue_val and not pd.isna(revenue_val):
                        try:
                            monthly_summary[month_val]['收入'] += Decimal(str(revenue_val))
                        except:
                            pass
            
            # 仓库成本按月汇总 (仅 GBP，简化处理)
            for c in warehouse_costs:
                if c.year_month not in monthly_summary:
                    monthly_summary[c.year_month] = {'收入': Decimal('0'), '成本': Decimal('0')}
                monthly_summary[c.year_month]['成本'] += c.total_cost
            
            summary_rows = []
            for month in sorted(monthly_summary.keys()):
                data = monthly_summary[month]
                revenue = data['收入']
                cost = data['成本']
                profit = revenue - cost
                
                # 确定备注
                if revenue == 0 and cost > 0:
                    remark = '⚠️ 该月无平台收入数据'
                elif cost == 0 and revenue > 0:
                    remark = '⚠️ 该月无仓库成本数据'
                elif revenue < 0:
                    remark = '⚠️ 该月平台收入为负(退款/调整)'
                elif cost > 0 and revenue > 0 and cost > revenue * 10:
                    remark = '⚠️ 成本远大于收入,数据可能不完整'
                else:
                    remark = '不含SKU采购成本'
                
                summary_rows.append({
                    '月份': month,
                    '平台总收入': float(revenue),
                    '仓库总成本': float(cost),
                    '毛利(不含商品成本)': float(profit),
                    '备注': remark
                })
            
            df_summary = pd.DataFrame(summary_rows)
            df_summary.to_excel(writer, sheet_name='综合损益概览', index=False)
            print(f"  - 综合损益概览: {len(df_summary)} 行")
            
            # Sheet 4: 限制说明
            limitations = [
                {'项目': '数据范围', '说明': '仅含仓库履约成本，不含SKU商品成本'},
                {'项目': '匹配能力', '说明': '无「订单→SKU→成本」链路'},
                {'项目': '订单号', '说明': '仓库订单号 ≠ 平台 order_id'},
                {'项目': 'Phase 3', '说明': 'SKU级成本、商品毛利需补充订单明细数据'},
            ]
            df_limits = pd.DataFrame(limitations)
            df_limits.to_excel(writer, sheet_name='限制说明', index=False)
            
        print(f"\n报表已生成: {output_file}")
        
    except PermissionError:
        print(f"\n❌ 错误: 无法写入文件 {output_file}")
        print("💡 原因: 文件可能已被打开。请关闭 Excel 文件后重试。")
    except Exception as e:
        print(f"\n❌ 生成报表时出错: {e}")
    print("=" * 70)
    
    return output_file


if __name__ == '__main__':
    run_phase2()
