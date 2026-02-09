# -*- coding: utf-8 -*-
"""
店铺数据模型

包含店铺信息和月度核算结果
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


def _quantize(value: Decimal) -> Decimal:
    """保留2位小数"""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


@dataclass
class StoreInfo:
    """店铺基本信息"""
    store_id: str
    store_name: str
    platform: str = "amazon"
    marketplace: str = ""  # UK, DE, US等
    currency: str = ""
    
    @classmethod
    def from_filename(cls, filename: str) -> 'StoreInfo':
        """从文件名解析店铺信息"""
        # 示例: 智能万物店铺10_UK 2025NovMonthlyTransaction.csv
        import re
        
        store_name = ""
        marketplace = ""
        
        # 尝试匹配 店铺名_市场 格式
        match = re.match(r'(.+?)[-_]?(UK|DE|US|CA|FR|IT|ES|JP|AU)', filename, re.IGNORECASE)
        if match:
            store_name = match.group(1).strip()
            marketplace = match.group(2).upper()
        else:
            store_name = filename.split('.')[0]
        
        # 生成store_id
        store_id = f"{store_name}_{marketplace}".lower().replace(' ', '_')
        
        # 推断货币
        currency_map = {
            'UK': 'GBP',
            'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR',
            'US': 'USD', 'CA': 'CAD',
            'JP': 'JPY', 'AU': 'AUD',
        }
        currency = currency_map.get(marketplace, 'USD')
        
        return cls(
            store_id=store_id,
            store_name=store_name,
            platform="amazon",
            marketplace=marketplace,
            currency=currency,
        )


@dataclass
class StoreMonthlyResult:
    """
    店铺月度核算结果
    
    核心指标: platform_net_settlement (月度平台净结算金额)
    """
    # 店铺信息
    store_id: str
    store_name: str
    platform: str
    marketplace: str
    year_month: str  # '2025-11'
    currency: str
    
    # 交易统计
    total_records: int = 0
    included_records: int = 0
    excluded_records: int = 0
    
    # 收入明细
    gross_sales: Decimal = field(default_factory=lambda: Decimal('0'))
    platform_fees: Decimal = field(default_factory=lambda: Decimal('0'))
    promotional_rebates: Decimal = field(default_factory=lambda: Decimal('0'))
    adjustments: Decimal = field(default_factory=lambda: Decimal('0'))
    taxes: Decimal = field(default_factory=lambda: Decimal('0'))
    other: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # 核心指标: 月度平台净结算金额
    platform_net_settlement: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # 排除项统计 (仅展示，不参与计算)
    transfer_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # Phase 2 预留
    warehouse_cost: Optional[Decimal] = None
    procurement_cost: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    
    def __post_init__(self):
        """确保金额精度"""
        self.gross_sales = _quantize(self.gross_sales)
        self.platform_fees = _quantize(self.platform_fees)
        self.promotional_rebates = _quantize(self.promotional_rebates)
        self.adjustments = _quantize(self.adjustments)
        self.taxes = _quantize(self.taxes)
        self.other = _quantize(self.other)
        self.platform_net_settlement = _quantize(self.platform_net_settlement)
        self.transfer_amount = _quantize(self.transfer_amount)
    
    @property
    def calculated_net(self) -> Decimal:
        """根据明细计算的净额 (用于校验)"""
        return _quantize(
            self.gross_sales +
            self.platform_fees +  # 通常为负
            self.promotional_rebates +  # 通常为负
            self.adjustments +
            self.taxes +
            self.other
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'store_id': self.store_id,
            'store_name': self.store_name,
            'platform': self.platform,
            'marketplace': self.marketplace,
            'year_month': self.year_month,
            'currency': self.currency,
            'total_records': self.total_records,
            'included_records': self.included_records,
            'excluded_records': self.excluded_records,
            'gross_sales': float(self.gross_sales),
            'platform_fees': float(self.platform_fees),
            'promotional_rebates': float(self.promotional_rebates),
            'adjustments': float(self.adjustments),
            'taxes': float(self.taxes),
            'other': float(self.other),
            'platform_net_settlement': float(self.platform_net_settlement),
            'transfer_amount': float(self.transfer_amount),
            # Phase 2
            'warehouse_cost': float(self.warehouse_cost) if self.warehouse_cost else None,
            'procurement_cost': float(self.procurement_cost) if self.procurement_cost else None,
            'gross_profit': float(self.gross_profit) if self.gross_profit else None,
        }
    
    def to_report_row(self) -> list:
        """转换为报表行"""
        return [
            self.store_name,
            self.marketplace,
            self.year_month,
            self.currency,
            self.total_records,
            float(self.gross_sales),
            float(self.platform_fees),
            float(self.promotional_rebates),
            float(self.platform_net_settlement),
            float(self.transfer_amount),
        ]
    
    @staticmethod
    def report_headers() -> list:
        """报表表头"""
        return [
            '店铺名称',
            '市场',
            '月份',
            '货币',
            '交易数',
            '销售收入',
            '平台费用',
            '促销折扣',
            '平台净结算',
            '提现金额(参考)',
        ]
