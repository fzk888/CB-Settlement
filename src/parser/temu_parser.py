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
import pandas as pd
from decimal import Decimal
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import re
import sys

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
        '支出-技术服务费': ('FEE', -1),
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
        
        # 元信息
        meta = {
            'platform': self.platform,
            'store_name': store_name,
            'site': 'GLOBAL',
            'currency': list(all_currencies)[0] if all_currencies else 'USD',
            'year_month': list(all_months)[0] if all_months else '',
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
            return []  # 跳过未知的 Sheet
        
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
        possible_cols = ['交易收入', '退款金额', '运费收入', '运费退款', '违规金额', '扣款金额', '结算金额']
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
                # 解析金额
                amount_val = row.get(amount_col, 0)
                if pd.isna(amount_val) or amount_val == '/':
                    continue
                
                amount = Decimal(str(amount_val)) * sign
                
                # 解析时间
                date_time = None
                time_col = row.get('账务时间', row.get('时间', None))
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


# 测试
if __name__ == '__main__':
    parser = TemuParser()
    test_file = r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台\多平台收入-7月\All F Home FundDetail-1754358591792-f173.xlsx'
    
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
