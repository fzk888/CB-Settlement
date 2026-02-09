# -*- coding: utf-8 -*-
"""
速卖通平台解析器

解析 收支流水xxx.xlsx 文件
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


class AliExpressParser:
    """速卖通 收支流水 解析器"""
    
    # 排除的交易类型 (提现)
    EXCLUDED_TYPES = ['提现', '出金']
    
    def __init__(self):
        self.platform = 'aliexpress'
    
    def parse(self, file_path: str) -> Tuple[List[Transaction], dict]:
        """
        解析速卖通收支流水 Excel 文件
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        transactions = []
        all_months = set()
        
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return [], {'error': str(e)}
        
        if df.empty:
            return [], {'error': '空文件'}
        
        for idx, row in df.iterrows():
            try:
                # 检查是否为提现类型 - 排除
                income_type = str(row.get('收支类型', '')).strip()
                fee_type = str(row.get('费用项', '')).strip()
                
                is_transfer = any(t in income_type for t in self.EXCLUDED_TYPES) or \
                              any(t in fee_type for t in self.EXCLUDED_TYPES)
                
                # 解析金额 - 需要去除 "CN￥ " 前缀
                amount_str = str(row.get('变动金额', '0')).strip()
                amount_str = re.sub(r'[CN￥¥\s,]', '', amount_str)
                
                if not amount_str:
                    continue
                    
                amount = Decimal(amount_str)
                
                # 解析时间
                date_time = None
                time_val = row.get('结算时间')
                if time_val and not pd.isna(time_val):
                    try:
                        if isinstance(time_val, str):
                            date_time = datetime.strptime(time_val, '%Y-%m-%d %H:%M:%S')
                        else:
                            date_time = pd.to_datetime(time_val)
                    except:
                        pass
                
                if date_time:
                    all_months.add(date_time.strftime('%Y-%m'))
                
                # 确定交易类型
                txn_type = TransactionType.TRANSFER if is_transfer else \
                           TransactionType.REFUND if '退款' in income_type else \
                           TransactionType.ORDER
                
                txn = Transaction(
                    date_time=date_time,
                    type=txn_type,
                    type_raw=fee_type,
                    order_id=str(row.get('订单号', '')).strip() if row.get('订单号') else '',
                    total=amount,
                    platform=self.platform,
                    store_name='速卖通',
                    currency=str(row.get('币种', 'CNY')).strip(),
                    source_file=str(file_path),
                    row_number=idx + 2,
                )
                transactions.append(txn)
                
            except Exception as e:
                continue
        
        meta = {
            'platform': self.platform,
            'store_name': '速卖通',
            'site': 'GLOBAL',
            'currency': 'CNY',
            'year_month': list(all_months)[0] if all_months else '',
            'total_records': len(transactions),
            'source_file': str(file_path),
        }
        
        return transactions, meta


# 测试
if __name__ == '__main__':
    parser = AliExpressParser()
    test_file = r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\速卖通\收支流水20260203182340.xlsx'
    
    txns, meta = parser.parse(test_file)
    print(f"平台: {meta.get('platform')}")
    print(f"解析记录数: {len(txns)}")
    
    if txns:
        # 排除 Transfer 后的净结算
        included = [t for t in txns if not t.is_excluded_from_revenue()]
        excluded = [t for t in txns if t.is_excluded_from_revenue()]
        
        net = sum(t.total for t in included)
        transfers = sum(t.total for t in excluded)
        
        print(f"参与计算: {len(included)} 条")
        print(f"排除(Transfer): {len(excluded)} 条")
        print(f"平台净结算: {net} CNY")
        print(f"提现金额: {transfers} CNY")
