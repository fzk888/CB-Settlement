# -*- coding: utf-8 -*-
"""
Phase 2 仓库账单解析器

仅解析仓库履约成本，不涉及 SKU 级成本
"""
import pandas as pd
from decimal import Decimal
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime
from dataclasses import dataclass, field
import re
import os
import warnings
warnings.filterwarnings('ignore')


@dataclass
class WarehouseMonthlyCost:
    """仓库月度成本汇总"""
    warehouse_name: str
    year_month: str
    total_cost: Decimal
    currency: str
    cost_breakdown: Dict[str, Decimal] = field(default_factory=dict)
    record_count: int = 0
    source_files: List[str] = field(default_factory=list)


class BaseWarehouseParser:
    """仓库解析器基类"""
    
    def __init__(self, warehouse_name: str, region: str, currency: str):
        self.warehouse_name = warehouse_name
        self.region = region
        self.currency = currency
    
    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        """解析单个文件，返回 (总成本, 分类汇总, 记录数)"""
        raise NotImplementedError
    
    def extract_month(self, filename: str) -> str:
        """从文件名提取月份"""
        raise NotImplementedError


class TSPParser(BaseWarehouseParser):
    """TSP 仓库解析器 (UK, GBP)"""
    
    def __init__(self):
        super().__init__("TSP", "UK", "GBP")
    
    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        total = Decimal('0')
        breakdown = {}
        count = 0
        
        xl = pd.ExcelFile(file_path)
        for sheet in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet)
            
            # 确定正确的 Cost 列
            # Invoice Items sheet 有多个分项，使用 Total Cost
            # 其他 sheet 使用 Cost 列
            if 'invoice items' in sheet.lower() and 'additional' not in sheet.lower():
                # Invoice Items - 使用 Total Cost 避免重复计算
                cost_col = None
                for c in df.columns:
                    if 'total cost' in str(c).lower():
                        cost_col = c
                        break
            else:
                # 其他 sheet - 使用 Cost 列
                cost_col = None
                for c in df.columns:
                    if str(c).lower() == 'cost' or ('total' in str(c).lower() and 'cost' in str(c).lower()):
                        cost_col = c
                        break
            
            if cost_col is None:
                continue
            
            sheet_total = Decimal('0')
            for idx, row in df.iterrows():
                try:
                    cost_val = row.get(cost_col, 0)
                    if pd.isna(cost_val):
                        continue
                    
                    amount = Decimal(str(cost_val))
                    sheet_total += amount
                    count += 1
                except:
                    continue
            
            if sheet_total > 0:
                breakdown[sheet] = sheet_total
                total += sheet_total
        
        return total, breakdown, count
    
    def extract_month(self, filename: str) -> str:
        # 1. Standard format: Jul25
        # 2. Full Month: November 2025 or November 25
        # 3. Prevent matching timestamps (e.g. avoid Jan01 as 2001)
        
        # Pattern 1: MonYY (e.g. Jul25), strict year 24-29
        match = re.search(r'([a-zA-Z]{3})(2[4-9])', filename)
        if match:
            month_abbr = match.group(1).lower()
            year = '20' + match.group(2)
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            if month_abbr in month_map:
                return f"{year}-{month_map[month_abbr]}"

        # Pattern 2: Full Month + Year (November 2025 or November 2025... or November 25)
        # Look for full month name followed by 202x or 2x
        month_names = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        filename_lower = filename.lower()
        for m_name, m_code in month_names.items():
            if m_name in filename_lower:
                # Look for year after month name
                # Matches: "november 2025", "november2025", "november 25"
                year_match = re.search(rf'{m_name}.*?(202[4-9]|2[4-9])', filename_lower)
                if year_match:
                    year_raw = year_match.group(1)
                    if len(year_raw) == 4:
                        year = year_raw
                    else:
                        year = '20' + year_raw
                    return f"{year}-{m_code}"
                    
        return ""


class Warehouse1510Parser(BaseWarehouseParser):
    """1510 仓库解析器 (UK, GBP)"""
    
    def __init__(self):
        super().__init__("1510", "UK", "GBP")
    
    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        total = Decimal('0')
        breakdown = {}
        count = 0
        
        xl = pd.ExcelFile(file_path)
        
        # 需要解析的 sheet
        target_sheets = ['B2C订单费用B2C Order Charges', 'B2B订单费用B2B Order Charges',
                         '入库费用Inbound Charges', '仓租费用Storage Charges',
                         '退货费用Returns Charges', '增值费用VAS Charges']
        
        for sheet in xl.sheet_names:
            if sheet in ['账单封面Bill cover', '充值Deposit']:
                continue
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                
                # 找费用相关列并求和
                fee_cols = [c for c in df.columns if any(k in str(c) for k in 
                           ['Fee', '费', 'Cost', 'Rate', 'Surcharge'])]
                
                sheet_total = Decimal('0')
                for col in fee_cols:
                    col_sum = df[col].apply(lambda x: Decimal(str(x)) if pd.notna(x) and str(x).replace('.','').replace('-','').isdigit() else Decimal('0')).sum()
                    sheet_total += col_sum
                
                if sheet_total > 0:
                    breakdown[sheet] = sheet_total
                    total += sheet_total
                    count += len(df)
            except:
                continue
        
        return total, breakdown, count
    
    def extract_month(self, filename: str) -> str:
        # bill-HBR-M20250401.xlsx
        match = re.search(r'M(\d{4})(\d{2})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return ""


class JDParser(BaseWarehouseParser):
    """京东海外仓解析器 (Multi-currency)"""
    
    def __init__(self):
        super().__init__("京东", "Global", "CNY")
    
    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        total = Decimal('0')
        breakdown = {}
        count = 0
        
        xl = pd.ExcelFile(file_path)
        
        for sheet in xl.sheet_names:
            if sheet == '汇总页':
                continue
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                
                # 找金额列
                amount_cols = [c for c in df.columns if '金额' in str(c) and '含税' in str(c)]
                if not amount_cols:
                    amount_cols = [c for c in df.columns if '金额' in str(c)]
                
                if amount_cols:
                    for col in amount_cols[:1]:
                        col_sum = df[col].apply(lambda x: Decimal(str(x)) if pd.notna(x) and str(x).replace('.','').replace('-','').isdigit() else Decimal('0')).sum()
                        breakdown[sheet] = col_sum
                        total += col_sum
                        count += len(df)
            except:
                continue
        
        return total, breakdown, count
    
    def extract_month(self, filename: str) -> str:
        # KH9220000002310_海外物流仓储服务费-全球_2025-10-01_2025-10-15_xxx.xlsx
        match = re.search(r'(\d{4})-(\d{2})-\d{2}', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return ""


class HaiyangParser(BaseWarehouseParser):
    """海洋仓库解析器 (UK, GBP)"""
    
    def __init__(self):
        super().__init__("海洋", "UK", "GBP")
    
    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        total = Decimal('0')
        breakdown = {}
        count = 0
        
        df = pd.read_excel(file_path)
        
        # 结算金额列
        amount_col = '结算金额'
        type_col = '费用类型'
        
        if amount_col in df.columns:
            for idx, row in df.iterrows():
                try:
                    cost_val = row.get(amount_col, 0)
                    if pd.isna(cost_val):
                        continue
                    
                    amount = Decimal(str(cost_val))
                    total += amount
                    count += 1
                    
                    # 按费用类型分类
                    fee_type = str(row.get(type_col, '其他'))
                    breakdown[fee_type] = breakdown.get(fee_type, Decimal('0')) + amount
                except:
                    continue
        
        return total, breakdown, count
    
    def extract_month(self, filename: str) -> str:
        # 2025-7月_CostBillExport1599.xlsx
        match = re.search(r'(\d{4})-(\d{1,2})月', filename)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}"
        return ""


class LHZParser(BaseWarehouseParser):
    """LHZ 仓库解析器 (DE, EUR)"""
    
    def __init__(self):
        super().__init__("LHZ", "DE", "EUR")
    
    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        total = Decimal('0')
        breakdown = {}
        count = 0
        
        xl = pd.ExcelFile(file_path)
        
        for sheet in xl.sheet_names:
            if sheet in ['总计', '开票费用明细']:
                continue
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet)
                
                # 找总计列
                total_cols = [c for c in df.columns if '总计' in str(c) or 'total' in str(c).lower()]
                
                sheet_total = Decimal('0')
                for col in total_cols:
                    col_sum = df[col].apply(lambda x: Decimal(str(x)) if pd.notna(x) and str(x).replace('.','').replace('-','').replace(',','').isdigit() else Decimal('0')).sum()
                    sheet_total += col_sum
                
                if sheet_total > 0:
                    breakdown[sheet] = sheet_total
                    total += sheet_total
                    count += len(df)
            except:
                continue
        
        return total, breakdown, count
    
    def extract_month(self, filename: str) -> str:
        # 开票费用明细 05-2025 HUP xlsx.xlsx
        match = re.search(r'(\d{2})-(\d{4})', filename)
        if match:
            return f"{match.group(2)}-{match.group(1)}"
        return ""


def get_parser(warehouse_name: str) -> BaseWarehouseParser:
    """获取仓库解析器"""
    parsers = {
        'TSP': TSPParser(),
        '1510': Warehouse1510Parser(),
        '京东': JDParser(),
        '海洋': HaiyangParser(),
        'LHZ': LHZParser(),
    }
    return parsers.get(warehouse_name)


def scan_warehouse_files(base_path: str, warehouse_name: str) -> List[str]:
    """扫描仓库目录下的所有 Excel 文件"""
    wh_path = os.path.join(base_path, warehouse_name)
    files = []
    
    if not os.path.exists(wh_path):
        return files
    
    for root, dirs, filenames in os.walk(wh_path):
        for f in filenames:
            if f.endswith('.xlsx') and not f.startswith('~$'):
                files.append(os.path.join(root, f))
    
    return files


def aggregate_warehouse_costs(base_path: str, warehouses: List[str]) -> List[WarehouseMonthlyCost]:
    """汇总所有仓库的月度成本"""
    results = []
    
    for wh_name in warehouses:
        parser = get_parser(wh_name)
        if not parser:
            continue
        
        files = scan_warehouse_files(base_path, wh_name)
        
        # 按月份分组
        monthly_data = {}
        
        for fp in files:
            try:
                filename = os.path.basename(fp)
                year_month = parser.extract_month(filename)
                if not year_month:
                    continue
                
                total, breakdown, count = parser.parse_file(fp)
                
                if year_month not in monthly_data:
                    monthly_data[year_month] = {
                        'total': Decimal('0'),
                        'breakdown': {},
                        'count': 0,
                        'files': []
                    }
                
                monthly_data[year_month]['total'] += total
                monthly_data[year_month]['count'] += count
                monthly_data[year_month]['files'].append(filename)
                
                for k, v in breakdown.items():
                    monthly_data[year_month]['breakdown'][k] = monthly_data[year_month]['breakdown'].get(k, Decimal('0')) + v
                    
            except Exception as e:
                print(f"  解析失败 {fp}: {e}")
        
        # 转换为结果对象
        for ym, data in monthly_data.items():
            results.append(WarehouseMonthlyCost(
                warehouse_name=wh_name,
                year_month=ym,
                total_cost=data['total'],
                currency=parser.currency,
                cost_breakdown=data['breakdown'],
                record_count=data['count'],
                source_files=data['files'],
            ))
    
    return results


if __name__ == '__main__':
    print("=" * 60)
    print("Phase 2 仓库成本汇总测试")
    print("=" * 60)
    
    base = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单'
    warehouses = ['TSP', '1510', '京东', '海洋', 'LHZ']
    
    results = aggregate_warehouse_costs(base, warehouses)
    
    for r in sorted(results, key=lambda x: (x.warehouse_name, x.year_month)):
        print(f"\n{r.warehouse_name} | {r.year_month} | {r.total_cost:,.2f} {r.currency}")
        for k, v in list(r.cost_breakdown.items())[:3]:
            print(f"  - {k}: {v:,.2f}")
