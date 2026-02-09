# -*- coding: utf-8 -*-
"""
多店铺汇总聚合器

负责将多个 CalculationResult 转换为 StoreMonthlyResult，
并支持生成汇总报表所需的数据结构
"""
from typing import List, Dict
from decimal import Decimal
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import (
    CalculationResult, StoreMonthlyResult
)


class MonthlyAggregator:
    """月度数据聚合器"""
    
    def aggregate_store(self, calc_result: CalculationResult) -> StoreMonthlyResult:
        """
        将单店铺核算结果转换为月度结果对象
        """
        totals = calc_result.field_totals
        
        # 计算归类汇总
        gross_sales = (
            totals.get('product_sales', Decimal('0')) +
            totals.get('postage_credits', Decimal('0')) +
            totals.get('shipping_credits', Decimal('0')) +
            totals.get('gift_wrap_credits', Decimal('0'))
        )
        
        platform_fees = (
            totals.get('selling_fees', Decimal('0')) +
            totals.get('fba_fees', Decimal('0')) +
            totals.get('other_transaction_fees', Decimal('0'))
        )
        
        taxes = (
            totals.get('product_sales_tax', Decimal('0')) +
            totals.get('postage_credits_tax', Decimal('0')) +
            totals.get('shipping_credits_tax', Decimal('0')) +
            totals.get('giftwrap_credits_tax', Decimal('0')) +
            totals.get('promotional_rebates_tax', Decimal('0')) +
            totals.get('marketplace_withheld_tax', Decimal('0'))
        )
        
        return StoreMonthlyResult(
            store_id=calc_result.store_id,
            store_name=calc_result.store_name,
            platform="amazon",
            marketplace="", # 需从store_info补充
            year_month=calc_result.year_month,
            currency=calc_result.currency,
            
            total_records=len(calc_result.included_transactions) + len(calc_result.excluded_transactions),
            included_records=len(calc_result.included_transactions),
            excluded_records=len(calc_result.excluded_transactions),
            
            gross_sales=gross_sales,
            platform_fees=platform_fees,
            promotional_rebates=totals.get('promotional_rebates', Decimal('0')),
            adjustments=Decimal('0'), # Adjustment通常在other里，这里暂存0
            taxes=taxes,
            other=totals.get('other', Decimal('0')),
            
            platform_net_settlement=calc_result.platform_net_settlement,
            transfer_amount=calc_result.transfer_amount,
        )
    
    def aggregate_summary(self, store_results: List[StoreMonthlyResult]) -> Dict:
        """
        生成多店铺汇总数据
        """
        summary = {
            'total_stores': len(store_results),
            'total_net_revenue': Decimal('0'),
            'currency_totals': {}
        }
        
        for res in store_results:
            # 简单汇总（注意：不同币种直接相加没有意义，这里按币种分组）
            curr = res.currency
            if curr not in summary['currency_totals']:
                summary['currency_totals'][curr] = Decimal('0')
            
            summary['currency_totals'][curr] += res.platform_net_settlement
        
        return summary
