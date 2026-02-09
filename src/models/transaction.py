# -*- coding: utf-8 -*-
"""
交易记录数据模型

核心模型，表示平台CSV中的单条交易记录
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    """交易类型枚举"""
    ORDER = "Order"
    REFUND = "Refund"
    TRANSFER = "Transfer"
    PAYOUT = "Payout"
    SERVICE_FEE = "Service Fee"
    FBA_INVENTORY_FEE = "FBA Inventory Fee"
    ADJUSTMENT = "Adjustment"
    LIQUIDATIONS = "Liquidations"
    AMAZON_FEES = "Amazon Fees"
    OTHER = "Other"
    
    @classmethod
    def from_string(cls, value: str) -> 'TransactionType':
        """从字符串解析交易类型，支持变体"""
        if not value:
            return cls.OTHER
        
        value_lower = value.strip().lower()
        
        # 精确匹配
        for t in cls:
            if t.value.lower() == value_lower:
                return t
        
        # 变体匹配
        if 'transfer' in value_lower:
            return cls.TRANSFER
        if 'payout' in value_lower:
            return cls.PAYOUT
        if 'refund' in value_lower:
            return cls.REFUND
        if 'order' in value_lower:
            return cls.ORDER
        if 'service' in value_lower and 'fee' in value_lower:
            return cls.SERVICE_FEE
        if 'fba' in value_lower and ('inventory' in value_lower or 'fee' in value_lower):
            return cls.FBA_INVENTORY_FEE
        if 'adjustment' in value_lower:
            return cls.ADJUSTMENT
        if 'liquidation' in value_lower:
            return cls.LIQUIDATIONS
        if 'amazon' in value_lower and 'fee' in value_lower:
            return cls.AMAZON_FEES
        
        return cls.OTHER
    
    def is_excluded_from_revenue(self) -> bool:
        """是否从收入计算中排除"""
        return self in (TransactionType.TRANSFER, TransactionType.PAYOUT)


def _quantize(value: Decimal) -> Decimal:
    """保留2位小数"""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


@dataclass
class Transaction:
    """
    交易记录模型
    
    核心字段: platform_net_settlement (即total，代表平台净结算金额)
    """
    # 基础信息
    date_time: Optional[datetime] = None
    settlement_id: str = ""
    type: TransactionType = TransactionType.OTHER
    type_raw: str = ""  # 原始type字符串
    order_id: str = ""
    sku: str = ""
    description: str = ""
    
    # 收入类字段 (通常为正)
    product_sales: Decimal = field(default_factory=lambda: Decimal('0'))
    product_sales_tax: Decimal = field(default_factory=lambda: Decimal('0'))
    postage_credits: Decimal = field(default_factory=lambda: Decimal('0'))
    postage_credits_tax: Decimal = field(default_factory=lambda: Decimal('0'))
    shipping_credits: Decimal = field(default_factory=lambda: Decimal('0'))
    shipping_credits_tax: Decimal = field(default_factory=lambda: Decimal('0'))
    gift_wrap_credits: Decimal = field(default_factory=lambda: Decimal('0'))
    giftwrap_credits_tax: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # 扣减类字段 (通常为负)
    promotional_rebates: Decimal = field(default_factory=lambda: Decimal('0'))
    promotional_rebates_tax: Decimal = field(default_factory=lambda: Decimal('0'))
    marketplace_withheld_tax: Decimal = field(default_factory=lambda: Decimal('0'))
    selling_fees: Decimal = field(default_factory=lambda: Decimal('0'))
    fba_fees: Decimal = field(default_factory=lambda: Decimal('0'))
    other_transaction_fees: Decimal = field(default_factory=lambda: Decimal('0'))
    other: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # 核心字段: 平台净结算金额
    total: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # 元数据
    platform: str = "amazon"
    store_id: str = ""
    store_name: str = ""
    currency: str = ""
    source_file: str = ""
    row_number: int = 0
    
    @property
    def platform_net_settlement(self) -> Decimal:
        """平台净结算金额 (核心字段，等价于total)"""
        return _quantize(self.total)
    
    @property
    def calculated_total(self) -> Decimal:
        """根据各字段计算的total，用于校验"""
        return _quantize(
            self.product_sales + self.product_sales_tax +
            self.postage_credits + self.postage_credits_tax +
            self.shipping_credits + self.shipping_credits_tax +
            self.gift_wrap_credits + self.giftwrap_credits_tax +
            self.promotional_rebates + self.promotional_rebates_tax +
            self.marketplace_withheld_tax +
            self.selling_fees + self.fba_fees +
            self.other_transaction_fees + self.other
        )
    
    @property
    def total_verification_diff(self) -> Decimal:
        """total字段与计算值的差异"""
        return _quantize(self.total - self.calculated_total)
    
    def is_total_verified(self, tolerance: Decimal = Decimal('0.01')) -> bool:
        """校验total是否与各字段之和一致"""
        return abs(self.total_verification_diff) <= tolerance
    
    def is_excluded_from_revenue(self) -> bool:
        """是否从收入计算中排除 (Transfer/Payout)"""
        # 优先使用type判断
        if self.type.is_excluded_from_revenue():
            return True
        # 辅助判断: order_id为空 + description含Transfer
        if not self.order_id and 'transfer' in self.description.lower():
            return True
        return False
    
    @property
    def gross_sales(self) -> Decimal:
        """销售收入 (product_sales + 各类credits)"""
        return _quantize(
            self.product_sales +
            self.postage_credits +
            self.shipping_credits +
            self.gift_wrap_credits
        )
    
    @property
    def platform_fees(self) -> Decimal:
        """平台费用 (selling_fees + fba_fees + other_transaction_fees)"""
        return _quantize(
            self.selling_fees +
            self.fba_fees +
            self.other_transaction_fees
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'date_time': self.date_time.isoformat() if self.date_time else None,
            'settlement_id': self.settlement_id,
            'type': self.type.value,
            'type_raw': self.type_raw,
            'order_id': self.order_id,
            'sku': self.sku,
            'description': self.description,
            'product_sales': float(self.product_sales),
            'selling_fees': float(self.selling_fees),
            'fba_fees': float(self.fba_fees),
            'other_transaction_fees': float(self.other_transaction_fees),
            'other': float(self.other),
            'total': float(self.total),
            'platform_net_settlement': float(self.platform_net_settlement),
            'calculated_total': float(self.calculated_total),
            'is_excluded': self.is_excluded_from_revenue(),
            'store_id': self.store_id,
            'currency': self.currency,
            'source_file': self.source_file,
            'row_number': self.row_number,
        }
