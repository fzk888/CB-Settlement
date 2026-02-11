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
        """
        1510 海外仓账单：只取第一个 sheet（账单封面/Bill cover）中的
        `账单总计(Total bill amount)`，其余 sheet 均为明细。
        """
        xl = pd.ExcelFile(file_path)
        if not xl.sheet_names:
            return Decimal('0'), {}, 0

        cover_sheet = xl.sheet_names[0]
        df_cover = pd.read_excel(file_path, sheet_name=cover_sheet, header=None)

        total = Decimal('0')
        found = False

        # 在封面中定位 “Total bill amount / 账单总计 / 账单小计”等单元格，取其右侧值
        keywords = ['total bill amount', '账单总计', '账单小计', '账单合计']

        for r in range(df_cover.shape[0]):
            for c in range(df_cover.shape[1]):
                v = df_cover.iat[r, c]
                if isinstance(v, str):
                    text = v.strip().lower()
                    if not any(k in text for k in keywords):
                        continue

                    if c + 1 < df_cover.shape[1]:
                        amt = df_cover.iat[r, c + 1]
                        try:
                            if pd.notna(amt):
                                total = Decimal(str(amt))
                                found = True
                        except Exception:
                            pass
                    break
            if found:
                break

        breakdown = {}
        if found:
            breakdown['Total bill amount'] = total
            return total, breakdown, 1

        # 兜底：如果封面字段定位失败，则返回 0（避免误把明细累加成总计）
        return Decimal('0'), {}, 0
    
    def extract_month(self, filename: str) -> str:
        """
        从 1510 账单文件名中提取「费用所属月份」

        规则说明（根据账单封面 Statement Period 推导）：
        - 文件名形如：bill-HBR-O-M20250101.xlsx
          - 中间的 M / A + YYYYMMDD 对应「账单到期日」(Payment Due Date)
          - 封面上的 Statement Period 为上一自然月：
            * 2025-01-01 -> 2024-12-01 ~ 2024-12-31 （所属 2024-12 月）
            * 2025-02-01 -> 2025-01-01 ~ 2025-01-31 （所属 2025-01 月）
        - 因此：按「到期日 - 1 天」来确定费用所属月份。
        - 同样适用于 A 开头的调整账单（bill-HBR-O-A20241001...）。
        """
        from datetime import date, timedelta

        # 捕获 M/A + YYYYMMDD，比如 M20250101 / A20241001
        match = re.search(r'[AM](\d{4})(\d{2})(\d{2})', filename, re.IGNORECASE)
        if not match:
            return ""

        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        try:
            due_date = date(year, month, day)
            period_last_day = due_date - timedelta(days=1)
            return f"{period_last_day.year}-{period_last_day.month:02d}"
        except Exception:
            return ""


class JDParser(BaseWarehouseParser):
    """京东海外仓解析器 (Multi-currency)"""
    
    def __init__(self):
        super().__init__("京东", "Global", "CNY")
    
    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        """
        京东海外仓：
        - 只看第一个 sheet（通常为「汇总页」）
        - 该 sheet 顶部是账单信息，下面有一行中英文表头：
            Billing Product / Billing Item / ... / Amount of Settlement Currency ...
        - 我们按「Amount of Settlement Currency」这一列表头来汇总金额。
        """
        xl = pd.ExcelFile(file_path)
        if not xl.sheet_names:
            return Decimal('0'), {}, 0

        summary_sheet = xl.sheet_names[0]

        # 京东汇总页常见结构：前若干行为说明、第 13/14 行为表头
        # 为稳妥起见，用 header>=0 的多次尝试来找到包含目标列名的那一行
        target_col = None
        df = None

        for header_row in range(0, 20):
            try:
                tmp = pd.read_excel(file_path, sheet_name=summary_sheet, header=header_row)
            except Exception:
                continue

            for c in tmp.columns:
                if 'amount of settlement currency' in str(c).lower():
                    target_col = c
                    df = tmp
                    break
            if target_col is not None:
                break

        if df is None or target_col is None:
            return Decimal('0'), {}, 0

        total = Decimal('0')
        count = 0

        for _, row in df.iterrows():
            val = row.get(target_col, 0)
            if pd.isna(val):
                continue
            try:
                amt = Decimal(str(val))
            except Exception:
                continue
            total += amt
            count += 1

        breakdown = {}
        if total != 0:
            breakdown['Amount of Settlement Currency'] = total

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
        """
        海洋仓库账单：只使用 CostBill sheet 的「计费规则金额」，忽略 CostBill2 等其他 sheet。
        """
        total = Decimal('0')
        breakdown: Dict[str, Decimal] = {}
        count = 0

        xl = pd.ExcelFile(file_path)
        if not xl.sheet_names:
            return Decimal('0'), {}, 0

        # 仅取名为 CostBill 的 sheet
        sheet_name = None
        for sh in xl.sheet_names:
            if str(sh).strip().lower() == 'costbill':
                sheet_name = sh
                break
        if sheet_name is None:
            # 若没有明确的 CostBill，就使用第一个 sheet 作为兜底
            sheet_name = xl.sheet_names[0]

        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # 寻找计费规则金额列（若无，则退回到结算金额/金额列）
        amount_col = None

        # 1) 优先：计费规则金额 / 计费金额
        priority_keywords = ['计费规则金额', '计费金额']
        for kw in priority_keywords:
            for c in df.columns:
                if kw in str(c):
                    amount_col = c
                    break
            if amount_col is not None:
                break

        # 2) 次优：结算金额
        if amount_col is None:
            for c in df.columns:
                if '结算金额' in str(c):
                    amount_col = c
                    break

        # 3) 兜底：包含“金额”的列
        if amount_col is None:
            for c in df.columns:
                if '金额' in str(c):
                    amount_col = c
                    break

        if amount_col is None:
            return Decimal('0'), {}, 0

        sheet_total = Decimal('0')
        for _, row in df.iterrows():
            val = row.get(amount_col, 0)
            if pd.isna(val):
                continue
            try:
                amt = Decimal(str(val))
            except Exception:
                continue
            sheet_total += amt
            count += 1

        if sheet_total > 0:
            breakdown['计费规则金额'] = sheet_total
            total = sheet_total

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
        """
        LHZ 海外仓账单：只取第一个 sheet（通常为“总计”）中的账单金额，其他 sheet 为明细。

        实际样例中字段常见为：
        - 账单金额 / Rechnungsbetrag
        - 未税金额合计 / Netto（不作为最终账单金额）
        """
        xl = pd.ExcelFile(file_path)
        if not xl.sheet_names:
            return Decimal('0'), {}, 0

        cover_sheet = xl.sheet_names[0]
        df_cover = pd.read_excel(file_path, sheet_name=cover_sheet, header=None)

        keywords = [
            '账单金额', 'rechnungsbetrag',
            'total bill amount', 'invoice total', 'grand total',
        ]

        total = Decimal('0')
        found = False

        for r in range(df_cover.shape[0]):
            for c in range(df_cover.shape[1]):
                v = df_cover.iat[r, c]
                if isinstance(v, str) and any(k in v.lower() for k in keywords):
                    # 优先取右侧第一个可解析为数字的值
                    for cc in range(c + 1, df_cover.shape[1]):
                        amt = df_cover.iat[r, cc]
                        try:
                            if pd.notna(amt):
                                total = Decimal(str(amt))
                                found = True
                                break
                        except Exception:
                            continue
                    break
            if found:
                break

        breakdown = {}
        if found:
            breakdown['Bill amount'] = total
            return total, breakdown, 1

        # 兜底：定位失败则返回 0，避免误把明细累加成总计
        return Decimal('0'), {}, 0
    
    def extract_month(self, filename: str) -> str:
        """
        LHZ 文件名常见格式：
        - 开票费用明细 05-2025 HUP xlsx.xlsx  -> 2025-05
        - 开票费用明细 12.2024 HUP xlsx.xlsx  -> 2024-12
        - 开票费用明细 10.2024 HUP xlsx.xlsx  -> 2024-10
        以及部分文件名包含 NBSP(\xa0) 等不可见字符。
        """
        safe = (filename or "").replace("\xa0", " ")

        # 1) MM-YYYY
        match = re.search(r'(\d{2})-(\d{4})', safe)
        if match:
            return f"{match.group(2)}-{match.group(1)}"

        # 2) MM.YYYY
        match = re.search(r'(\d{2})\.(\d{4})', safe)
        if match:
            return f"{match.group(2)}-{match.group(1)}"

        return ""


class AoyunhuiParser(BaseWarehouseParser):
    """奥韵汇仓库解析器 (DE, EUR)

    结算口径：按账单明细中的「结算金额」汇总。
    """

    def __init__(self):
        super().__init__("奥韵汇", "DE", "EUR")

    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        """
        默认解析：返回整份账单内「计费规则金额」在各月份上的总和。
        实际按月拆分逻辑在 parse_file_by_month 中完成，这里仅做汇总，
        以兼容旧接口。
        """
        monthly = self.parse_file_by_month(file_path)
        if not monthly:
            return Decimal('0'), {}, 0

        total = sum(v[0] for v in monthly.values())
        count = sum(v[2] for v in monthly.values())
        breakdown: Dict[str, Decimal] = {'计费规则金额': total}
        return total, breakdown, count

    def _load_costbill_df(self, file_path: str):
        """加载奥韵汇账单的 CostBill sheet."""
        xl = pd.ExcelFile(file_path)
        if not xl.sheet_names:
            return None

        sheet_name = None
        for sh in xl.sheet_names:
            if str(sh).lower() == 'costbill':
                sheet_name = sh
                break
        if sheet_name is None:
            sheet_name = xl.sheet_names[0]

        return pd.read_excel(file_path, sheet_name=sheet_name)

    def parse_file_by_month(self, file_path: str) -> Dict[str, Tuple[Decimal, Dict[str, Decimal], int]]:
        """
        按「计费时间」拆分到各个自然月：
        - 文件时间跨度可能覆盖多个月（甚至多季度），不能简单按文件名月份算。
        - 以每行明细的「计费时间」列确定所属月份（YYYY-MM）。
        """
        df = self._load_costbill_df(file_path)
        if df is None or df.empty:
            return {}

        # 找计费规则金额列（与 parse_file 中逻辑保持一致）
        amount_col = None
        priority_keywords = ['计费规则金额', '计费金额']
        for kw in priority_keywords:
            for c in df.columns:
                if kw in str(c):
                    amount_col = c
                    break
            if amount_col is not None:
                break

        if amount_col is None:
            for c in df.columns:
                if '结算金额' in str(c):
                    amount_col = c
                    break

        if amount_col is None:
            for c in df.columns:
                name = str(c)
                if ('结算' in name) and ('金额' in name):
                    amount_col = c
                    break

        if amount_col is None:
            for c in df.columns:
                if '金额' in str(c):
                    amount_col = c
                    break

        if amount_col is None:
            return {}

        # 寻找计费时间列
        time_col = None
        for c in df.columns:
            name = str(c)
            # 常见：计费时间 / 计费日期 / Billing Time / Billing Date
            if any(k in name for k in ['计费时间', '计费日期', 'Billing Time', 'Billing Date']) or '时间' in name or 'ʱ' in name:
                time_col = c
                break

        if time_col is None:
            return {}

        monthly: Dict[str, Tuple[Decimal, Dict[str, Decimal], int]] = {}

        for _, row in df.iterrows():
            val = row.get(amount_col, 0)
            if pd.isna(val):
                continue
            try:
                amt = Decimal(str(val))
            except Exception:
                continue

            t = row.get(time_col)
            ts = pd.to_datetime(t, errors='coerce')
            if pd.isna(ts):
                continue

            ym = f"{ts.year}-{ts.month:02d}"

            if ym not in monthly:
                monthly[ym] = (Decimal('0'), {}, 0)

            total_prev, bd_prev, cnt_prev = monthly[ym]
            total_new = total_prev + amt
            cnt_new = cnt_prev + 1
            bd_new = dict(bd_prev)
            bd_new['计费规则金额'] = bd_new.get('计费规则金额', Decimal('0')) + amt
            monthly[ym] = (total_new, bd_new, cnt_new)

        return monthly

    def extract_month(self, filename: str) -> str:
        # 例如：2025-12-31_CostBillExport1887.xlsx
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return ""


class DongFangParser(BaseWarehouseParser):
    """东方嘉盛仓库解析器 (CN, CNY)

    结算口径：按「记账金额」列汇总，并根据「记账时间/记账日期」按月拆分。
    """

    def __init__(self):
        super().__init__("东方嘉盛", "CN", "CNY")

    def _load_main_df(self, file_path: str):
        """东方嘉盛账单通常只有一个账户明细 sheet，直接读第一个 sheet 即可。"""
        xl = pd.ExcelFile(file_path)
        if not xl.sheet_names:
            return None
        sheet_name = xl.sheet_names[0]
        return pd.read_excel(file_path, sheet_name=sheet_name)

    def parse_file(self, file_path: str) -> Tuple[Decimal, Dict[str, Decimal], int]:
        """
        向后兼容的整文件汇总：返回所有月份的合计记账金额。
        实际的按月拆分由 parse_file_by_month 完成。
        """
        monthly = self.parse_file_by_month(file_path)
        if not monthly:
            return Decimal('0'), {}, 0

        total = sum(v[0] for v in monthly.values())
        count = sum(v[2] for v in monthly.values())
        breakdown: Dict[str, Decimal] = {"记账金额": total}
        return total, breakdown, count

    def parse_file_by_month(self, file_path: str) -> Dict[str, Tuple[Decimal, Dict[str, Decimal], int]]:
        """
        东方嘉盛**不按月份截断**：每个文件作为一个整体，汇总「记账金额」。

        为了适配 Phase2 的月度报表输出，这里用该文件中「记账时间」的最大值所属月份作为归属月。

        - 金额列：优先按列名匹配“记账金额/入账金额/收支金额/发生额/交易金额”，若找不到则用数值分布做兜底。
        - 时间列：优先按列名匹配“记账时间/记账日期”，若找不到则按可解析为日期的成功率兜底选取。
        """
        df = self._load_main_df(file_path)
        if df is None or df.empty:
            return {}

        # 1) 金额列：优先按列名匹配（兼容导出乱码/不同字段名）
        amount_col = None
        preferred_amount_keywords = ["记账金额", "入账金额", "收支金额", "发生额", "交易金额"]
        for kw in preferred_amount_keywords:
            for c in df.columns:
                if kw in str(c):
                    amount_col = c
                    break
            if amount_col is not None:
                break

        # 兜底：从“数值列”里挑选最像金额的列（混合正负、非汇率）
        if amount_col is None:
            best = None
            best_score = None
            for c in df.columns:
                if str(c).strip().lower() in ["id", "no"]:
                    continue
                ser = pd.to_numeric(df[c], errors="coerce").dropna()
                if ser.empty:
                    continue

                # 排除汇率类（大量接近 1）
                near_one_frac = float(((ser >= 0.9) & (ser <= 1.1)).mean())
                if near_one_frac > 0.8 and ser.nunique() < 20:
                    continue

                neg_frac = float((ser < 0).mean())
                mixed_sign = 0.05 <= neg_frac <= 0.95
                score = (1 if mixed_sign else 0) * 1_000_000 + len(ser)

                if best_score is None or score > best_score:
                    best_score = score
                    best = c
            amount_col = best

        if amount_col is None:
            return {}

        # 2) 时间列：优先按列名，其次按可解析日期成功率
        time_col = None
        preferred_time_keywords = ["记账时间", "记账日期", "入账时间", "交易时间", "交易日期"]
        for kw in preferred_time_keywords:
            for c in df.columns:
                if kw in str(c):
                    time_col = c
                    break
            if time_col is not None:
                break

        if time_col is None:
            best = None
            best_rate = 0.0
            for c in df.columns:
                ser = pd.to_datetime(df[c], errors="coerce")
                rate = float(ser.notna().mean())
                if rate > best_rate and rate >= 0.2:
                    best_rate = rate
                    best = c
            time_col = best

        if time_col is None:
            return {}

        ts_all = pd.to_datetime(df[time_col], errors="coerce").dropna()
        if ts_all.empty:
            return {}

        ym = f"{ts_all.max().year}-{ts_all.max().month:02d}"

        ser_amt = pd.to_numeric(df[amount_col], errors="coerce").dropna()
        if ser_amt.empty:
            return {}

        total = Decimal(str(float(ser_amt.sum())))
        count = int(ser_amt.shape[0])
        return {ym: (total, {"记账金额": total}, count)}

    def extract_month(self, filename: str) -> str:
        """
        东方嘉盛文件名通常不含明确月份，这里返回空字符串，
        实际月份由 parse_file_by_month 中的记账时间来决定。
        """
        return ""


def get_parser(warehouse_name: str) -> BaseWarehouseParser:
    """获取仓库解析器"""
    parsers = {
        'TSP': TSPParser(),
        '1510': Warehouse1510Parser(),
        '京东': JDParser(),
        '海洋': HaiyangParser(),
        'LHZ': LHZParser(),
        '奥韵汇': AoyunhuiParser(),
        '东方嘉盛': DongFangParser(),
    }
    return parsers.get(warehouse_name)


def scan_warehouse_files(base_path: str, warehouse_name: str) -> List[str]:
    """扫描仓库目录下的所有 Excel 文件"""
    wh_path = os.path.join(base_path, warehouse_name)
    files = []
    
    # 某些 Windows 环境下中文目录名在不同编码/终端里可能出现乱码，导致直接拼接路径找不到。
    # 这里为个别仓库提供兜底扫描策略（按文件名特征）。
    if not os.path.exists(wh_path):
        if warehouse_name == '东方嘉盛':
            # 东方嘉盛导出的文件名通常包含 table-list
            for root, _, filenames in os.walk(base_path):
                for f in filenames:
                    if f.startswith('~$'):
                        continue
                    if f.lower().endswith(('.xlsx', '.xls')) and ('table-list' in f.lower()):
                        files.append(os.path.join(root, f))
            # 继续走去重逻辑
        else:
            return files
    
    for root, dirs, filenames in os.walk(wh_path):
        for f in filenames:
            if f.lower().endswith(('.xlsx', '.xls')) and not f.startswith('~$'):
                files.append(os.path.join(root, f))

    # 去重：同一目录下同名的重复下载文件通常带 "(1)/(2)/(3)" 后缀，避免重复计入
    # 规则：对相同“规范化相对路径”的文件，仅保留最后修改时间最新的那一份
    def _normalize_relpath(fp: str) -> str:
        rel = os.path.relpath(fp, wh_path)
        d = os.path.dirname(rel)
        base = os.path.basename(rel)
        stem, ext = os.path.splitext(base)
        # 仅对“重复下载”常见的 (1)/(2)... 做去重，避免把业务编号 (18)/(33) 等误当重复文件
        m = re.search(r'\s*\((\d+)\)$', stem)
        if m:
            try:
                n = int(m.group(1))
            except Exception:
                n = None
            # 通常重复下载后缀在 1~9 之间；超过 9 更可能是业务序号
            if n is not None and 1 <= n <= 9:
                stem = re.sub(r'\s*\(\d+\)$', '', stem)  # e.g. "xxx (3).xlsx" -> "xxx.xlsx"
        norm_base = (stem + ext).lower()
        return os.path.join(d, norm_base).lower()

    best = {}
    for fp in files:
        key = _normalize_relpath(fp)
        try:
            mtime = os.path.getmtime(fp)
        except Exception:
            mtime = 0

        if key not in best:
            best[key] = (mtime, fp)
        else:
            if mtime >= best[key][0]:
                best[key] = (mtime, fp)

    return [v[1] for v in best.values()]


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
                
                # 支持按文件内部「计费时间」拆分月份的解析器（如奥韵汇）
                if hasattr(parser, "parse_file_by_month"):
                    # type: ignore[attr-defined]
                    month_map = parser.parse_file_by_month(fp)  # 返回 { 'YYYY-MM': (total, breakdown, count) }
                else:
                    year_month = parser.extract_month(filename)
                    if not year_month:
                        continue
                    total, breakdown, count = parser.parse_file(fp)
                    month_map = {year_month: (total, breakdown, count)}

                for year_month, (total, breakdown, count) in month_map.items():
                    if not year_month:
                        continue
                    
                    if year_month not in monthly_data:
                        monthly_data[year_month] = {
                            'total': Decimal('0'),
                            'breakdown': {},
                            'count': 0,
                            'files': []
                        }
                    
                    monthly_data[year_month]['total'] += total
                    monthly_data[year_month]['count'] += count
                    if filename not in monthly_data[year_month]['files']:
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
