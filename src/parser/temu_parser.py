# -*- coding: utf-8 -*-
"""
Temu 平台解析器

解析 FundDetail-xxx.xlsx 文件
多 Sheet 结构:
- 结算-交易收入: 销售收入
- 结算-售后退款: 退款
- 结算-运费收入: 运费收入
- 结算-运费退款: 运费退款
- 支出-履约违规: 违规扣款
"""
import warnings

import pandas as pd
from decimal import Decimal
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import re
import sys

# 忽略 openpyxl 读取无默认样式 Excel 时的警告（不影响解析结果）
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.models import Transaction, TransactionType


class TemuParser:
    """Temu FundDetail 解析器"""
    
    # Sheet 名称到交易类型的映射
    SHEET_TYPE_MAP = {
        '结算-交易收入': ('ORDER', 1),      # 正数
        '结算-售后退款': ('REFUND', -1),    # 负数
        '结算-运费收入': ('SHIPPING', 1),   # 正数
        '结算-运费退款': ('SHIPPING_REFUND', -1),  # 负数
        '支出-履约违规': ('FEE', -1),       # 负数
        # 买家拒付实际上也是平台向店铺收取的费用，应作为费用支出计入
        '支出-买家拒付': ('FEE', -1),
        '支出-技术服务费': ('FEE', -1),
        '其他-售后运费结算': ('FEE', -1),   # 售后运费结算为支出，负数
        '结算': ('ORDER', 1),               # 通用结算(正数)
    }
    
    def __init__(self):
        self.platform = 'temu'
    
    def parse(self, file_path: str) -> Tuple[List[Transaction], dict]:
        """
        解析 Temu FundDetail Excel 文件
        
        Returns:
            transactions: 交易列表
            meta: 元信息 {store_name, year_month, currency, ...}
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 从文件名解析店铺名
        store_name = self._extract_store_name(file_path.name)
        
        transactions = []
        all_currencies = set()
        all_months = set()
        
        try:
            xl = pd.ExcelFile(file_path)
            
            for sheet_name in xl.sheet_names:
                sheet_txns = self._parse_sheet(
                    file_path, 
                    sheet_name, 
                    store_name
                )
                transactions.extend(sheet_txns)
                
                # 收集币种和月份
                for txn in sheet_txns:
                    if txn.currency:
                        all_currencies.add(txn.currency)
                    if txn.date_time:
                        all_months.add(txn.date_time.strftime('%Y-%m'))
            
        except Exception as e:
            return [], {'error': str(e)}
        
        # 确定所属月份（year_month）
        # 优先策略：
        # 1）若所有交易日期都在同一自然月，直接用该月；
        # 2）若跨多个月份，则优先使用文件夹里的“多平台收入-8月”这类信息；
        #    若文件夹中也无法解析出月份，则退回到「所有交易日期里的最大月份」；
        # 3）若所有交易都无日期，再从文件路径中的文件夹名推断（如 多平台收入-11月 -> 2025-11）
        folder_month = self._extract_year_month_from_path(file_path)
        if all_months:
            if len(all_months) == 1:
                # 只有一个自然月，直接采用
                year_month = list(all_months)[0]
            else:
                # 有多个自然月：一般 FundDetail 是「当月结算」，并放在「多平台收入-8月」之类目录下，
                # 因此更可信的是文件夹里的“8月”信息，而不是交易发生月份。
                if folder_month:
                    year_month = folder_month
                else:
                    # 兜底：取交易日期中的最大月份（例如 2025-06/07/08 -> 2025-08）
                    year_month = max(all_months)
        else:
            year_month = folder_month
        
        # 元信息
        meta = {
            'platform': self.platform,
            'store_name': store_name,
            'site': 'GLOBAL',
            'currency': list(all_currencies)[0] if all_currencies else 'USD',
            'year_month': year_month,
            'total_records': len(transactions),
            'source_file': str(file_path),
        }
        
        return transactions, meta
    
    def _parse_sheet(
        self, 
        file_path: Path, 
        sheet_name: str, 
        store_name: str
    ) -> List[Transaction]:
        """解析单个 Sheet"""
        
        # 检查是否为已知的 Sheet 类型
        # 使用最长匹配原则，避免 '结算' 误匹配 '结算-售后退款'
        type_info = None
        matched_prefix_len = 0
        
        for prefix, info in self.SHEET_TYPE_MAP.items():
            if prefix in sheet_name:
                if len(prefix) > matched_prefix_len:
                    matched_prefix_len = len(prefix)
                    type_info = info
        
        if not type_info:
            # 回退规则：根据 Sheet 名字里的关键字判断正负方向
            # 先处理一些特殊的收入 Sheet，例如「账户-税金退回」：
            # 该 Sheet 表示平台将之前代扣的税金退回店铺，本质上属于收入，应计为正数。
            s = str(sheet_name)
            if '税金退回' in s:
                type_info = ('ORDER', 1)
            else:
                # 一般规则：
                # - 含「退款」或「拒付」 -> 视为退款/费用，负数
                # - 含「支出」           -> 视为费用，负数
                # - 含「结算」或「收入」 -> 视为收入，正数
                if ('退款' in s) or ('拒付' in s):
                    type_info = ('REFUND', -1)
                elif '支出' in s:
                    type_info = ('FEE', -1)
                elif ('结算' in s) or ('收入' in s):
                    type_info = ('ORDER', 1)
                else:
                    # 其他完全未知的 Sheet 先跳过，避免误计入
                    return []
        
        txn_type_str, sign = type_info
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception:
            return []
        
        if df.empty:
            return []
        
        transactions = []
        
        # 确定金额列名
        amount_col = None
        # Temu 各类模板里金额列的常见命名
        possible_cols = [
            '交易收入',
            '结算金额',
            '退款金额',
            '运费收入',
            '运费退款',
            '违规金额',
            '支出金额',
            '扣款金额',
        ]
        for col in possible_cols:
            if col in df.columns:
                amount_col = col
                break
        
        if not amount_col:
            # 尝试找任意数值列
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    amount_col = col
                    break
        
        if not amount_col:
            return []
        
        for idx, row in df.iterrows():
            try:
                # 跳过汇总行：通常某一列会标记为「合计」或「总计」
                is_summary_row = False
                for v in row.values:
                    if isinstance(v, str) and v.strip() in ('合计', '总计'):
                        is_summary_row = True
                        break
                
                # 另一种常见汇总行形式：除了金额列外，其它列全部为空 / NaN，
                # 且金额列非空（例如示例文件中最后一行只有「614.8」这一格）
                if not is_summary_row:
                    non_amount_cols = [c for c in df.columns if c != amount_col]
                    if non_amount_cols:
                        other_vals = row[non_amount_cols]
                        amt_val_tmp = row.get(amount_col, None)
                        if other_vals.isna().all() and not pd.isna(amt_val_tmp):
                            is_summary_row = True
                
                if is_summary_row:
                    continue
                
                # 解析金额
                amount_val = row.get(amount_col, 0)
                if pd.isna(amount_val) or amount_val == '/':
                    continue

                # 默认按 Sheet 方向确定正负
                base_amount = Decimal(str(amount_val))

                # 特殊规则：Temu 账务类型为「退回-税金退回」时，一律按收入正数处理
                # 说明：该类型代表平台将之前扣的税金退回给店铺，实质是增加可支配收入，
                # 不应作为费用支出。无论原始金额正负，最终都计为正数。
                biz_type = str(row.get('账务类型') or row.get('交易类型') or '').strip()
                if '退回-税金退回' in biz_type:
                    amount = abs(base_amount)
                else:
                    amount = base_amount * sign
                
                # 解析时间（Temu 不同 Sheet 可能用「账务时间」「时间」或「到账时间」）
                date_time = None
                time_col = row.get('账务时间', row.get('时间', row.get('到账时间', None)))
                if time_col and not pd.isna(time_col):
                    try:
                        if isinstance(time_col, str):
                            date_time = datetime.strptime(time_col, '%Y-%m-%d %H:%M:%S')
                        else:
                            date_time = pd.to_datetime(time_col)
                    except:
                        pass
                
                # 构建 Transaction
                txn = Transaction(
                    date_time=date_time,
                    type=TransactionType.from_string(txn_type_str),
                    type_raw=sheet_name,
                    order_id=str(row.get('订单编号', '')).strip() if row.get('订单编号') else '',
                    total=amount,
                    platform=self.platform,
                    store_id=store_name.lower().replace(' ', '_'),
                    store_name=store_name,
                    currency=str(row.get('币种', 'USD')).strip(),
                    source_file=str(file_path),
                    row_number=idx + 2,
                )
                transactions.append(txn)
                
            except Exception as e:
                continue
        
        return transactions
    
    def _extract_store_name(self, filename: str) -> str:
        """从文件名提取店铺名"""
        # 示例: All F Home FundDetail-1754358591792-f173.xlsx
        match = re.match(r'^(.+?)\s*FundDetail', filename, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return filename.split('.')[0]
    
    def _extract_year_month_from_path(self, file_path: Path) -> str:
        """从文件路径中的文件夹名提取年月，如 多平台收入-11月 -> 2025-11"""
        path_str = str(file_path).replace('\\', '/')
        match = re.search(r'[-\s](\d{1,2})月', path_str)
        if match:
            month = int(match.group(1))
            return f"2025-{month:02d}"
        return ''


# 测试
if __name__ == '__main__':
    parser = TemuParser()
    test_file = r'D:\app\收入核算系统\data\部分店铺收入\多平台\多平台收入-11月\Boutique local 11月 Detail-1764659035833-e7d1.xlsx'
    
    txns, meta = parser.parse(test_file)
    print(f"店铺: {meta.get('store_name')}")
    print(f"币种: {meta.get('currency')}")
    print(f"解析记录数: {len(txns)}")
    
    if txns:
        # 计算平台净结算
        total = sum(t.total for t in txns)
        print(f"平台净结算: {total} {meta.get('currency')}")
        
        # 按类型统计
        by_type = {}
        for t in txns:
            by_type[t.type_raw] = by_type.get(t.type_raw, Decimal('0')) + t.total
        
        print("\n按类型汇总:")
        for k, v in by_type.items():
            print(f"  {k}: {v}")
