# -*- coding: utf-8 -*-
"""
收入核算器

负责:
1. 接收解析后的交易记录列表
2. 根据规则过滤交易 (排除Transfer/Payout)
3. 汇总各字段金额
4. 生成 CalculationResult
"""
from decimal import Decimal
from typing import List, Dict, Tuple
from collections import defaultdict
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import (
    Transaction, TransactionType, 
    CalculationResult, StoreInfo
)


class RevenueCalculator:
    """收入核算器"""
    
    def calculate(
        self, 
        transactions: List[Transaction],
        store_id: str = "",
        store_name: str = "",
        year_month: str = "",
        currency: str = ""
    ) -> CalculationResult:
        """
        执行核算计算
        """
        result = CalculationResult(
            store_id=store_id,
            store_name=store_name,
            year_month=year_month,
            currency=currency
        )
        
        # 1. 交易分类
        included = []
        excluded = []
        
        for txn in transactions:
            if txn.is_excluded_from_revenue():
                excluded.append(txn)
                # 记录提现金额 (Transfer的net amount)
                result.transfer_amount += txn.platform_net_settlement
            else:
                included.append(txn)
        
        result.included_transactions = included
        result.excluded_transactions = excluded
        
        # 2. 汇总统计 (仅针对参与计算的交易)
        field_totals = defaultdict(Decimal)
        type_totals = defaultdict(Decimal)
        type_counts = defaultdict(int)
        
        platform_net = Decimal('0')
        
        for txn in included:
            # Type统计
            type_val = txn.type.value
            type_totals[type_val] += txn.platform_net_settlement
            type_counts[type_val] += 1
            
            # 核心指标
            platform_net += txn.platform_net_settlement
            
            # 字段汇总
            # 遍历Transaction数值字段
            for field in [
                'product_sales', 'product_sales_tax',
                'postage_credits', 'postage_credits_tax',
                'shipping_credits', 'shipping_credits_tax',
                'gift_wrap_credits', 'giftwrap_credits_tax',
                'promotional_rebates', 'promotional_rebates_tax',
                'marketplace_withheld_tax',
                'selling_fees', 'fba_fees',
                'other_transaction_fees', 'other',
                'total'
            ]:
                val = getattr(txn, field, Decimal('0'))
                field_totals[field] += val
        
        result.field_totals = dict(field_totals)
        result.type_totals = dict(type_totals)
        result.type_counts = dict(type_counts)
        result.platform_net_settlement = platform_net
        
        # 3. 校验
        self._verify_result(result)
        
        return result
    
    def _verify_result(self, result: CalculationResult):
        """校验计算结果"""
        # 校验1: total汇总是否等于platform_net_settlement
        total_sum = result.field_totals.get('total', Decimal('0'))
        if abs(total_sum - result.platform_net_settlement) > Decimal('0.01'):
            result.verification_passed = False
            result.verification_notes.append(
                f"Total汇总({total_sum}) 与 平台净结算({result.platform_net_settlement}) 不一致"
            )
        
        # 校验2: 各字段之和是否等于total
        # 注意: 这里的field_totals包含了total字段本身，需要排除
        calculated_total = Decimal('0')
        for field, value in result.field_totals.items():
            if field != 'total':
                calculated_total += value
        
        diff = total_sum - calculated_total
        if abs(diff) > Decimal('0.01'):
            result.verification_passed = False
            result.verification_notes.append(
                f"各字段汇总({calculated_total}) 与 Total({total_sum}) 存在差异: {diff}"
            )
        
        if not result.verification_notes:
            result.verification_passed = True
