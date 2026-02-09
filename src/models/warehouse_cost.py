# -*- coding: utf-8 -*-
"""
仓库成本数据模型

Phase 2.1: 仅负责数据建模，不做成本分摊
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional


class CostType(Enum):
    """成本类型枚举"""
    SHIPPING = "Shipping"           # 发货/派送费
    STORAGE = "Storage"             # 仓储费/仓租
    INBOUND = "Inbound"             # 入库费
    OUTBOUND = "Outbound"           # 出库费
    HANDLING = "Handling"           # 操作费
    PACKAGING = "Packaging"         # 包装费
    RETURN = "Return"               # 退货处理费
    MANAGEMENT = "Management"       # 管理费/账户费
    TRANSPORT = "Transport"         # 头程运费
    CUSTOMS = "Customs"             # 清关费
    OTHER = "Other"                 # 其他费用
    
    @classmethod
    def from_string(cls, type_str: str) -> 'CostType':
        """根据字符串推断成本类型"""
        type_str = str(type_str).lower()
        
        # 派送/发货
        if any(k in type_str for k in ['派送', 'delivery', 'shipping', '运费', 'dispatch']):
            return cls.SHIPPING
        # 仓储
        if any(k in type_str for k in ['仓储', 'storage', '仓租', 'rent']):
            return cls.STORAGE
        # 入库
        if any(k in type_str for k in ['入库', 'inbound', 'receiving', 'good in']):
            return cls.INBOUND
        # 出库
        if any(k in type_str for k in ['出库', 'outbound', 'fulfil', 'pick']):
            return cls.OUTBOUND
        # 操作费
        if any(k in type_str for k in ['操作', 'handling', 'process', 'labour']):
            return cls.HANDLING
        # 包装
        if any(k in type_str for k in ['包装', 'packag', 'box', 'carton']):
            return cls.PACKAGING
        # 退货
        if any(k in type_str for k in ['退货', 'return', 'rts']):
            return cls.RETURN
        # 管理费
        if any(k in type_str for k in ['管理', 'management', 'account', 'admin']):
            return cls.MANAGEMENT
        # 头程
        if any(k in type_str for k in ['头程', 'freight', 'sea freight', 'air freight']):
            return cls.TRANSPORT
        # 清关
        if any(k in type_str for k in ['清关', 'customs', 'duty', 'vat']):
            return cls.CUSTOMS
        
        return cls.OTHER


def _quantize(value: Decimal) -> Decimal:
    """保留2位小数"""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


@dataclass
class WarehouseCost:
    """
    标准仓库成本模型
    
    Phase 2.1 目标：将各仓库账单统一转换为此结构
    """
    # 仓库标识
    warehouse_name: str             # 仓库名称 (TSP, 京东, 海洋, 西邮 等)
    warehouse_region: str = ""      # 仓库区域 (UK, US, DE 等)
    
    # 关联字段 (可为空)
    order_id: str = ""              # 订单号 (如有)
    sku: str = ""                   # SKU (如有)
    tracking_number: str = ""       # 物流跟踪号 (如有)
    reference_number: str = ""      # 参考号 (如有)
    store_id: str = ""              # 店铺ID (如有)
    
    # 成本信息
    cost_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    currency: str = "USD"           # 币种
    cost_type: CostType = CostType.OTHER
    cost_type_raw: str = ""         # 原始费用类型描述
    
    # 时间
    cost_date: Optional[datetime] = None  # 费用日期
    billing_period: str = ""        # 账单周期 (2025-07)
    
    # 数量 (如有)
    quantity: int = 0               # 数量
    weight: Decimal = field(default_factory=lambda: Decimal('0'))  # 重量
    
    # 来源
    source_file: str = ""           # 源文件
    row_number: int = 0             # 行号
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.cost_amount, (int, float, str)):
            self.cost_amount = _quantize(Decimal(str(self.cost_amount)))
        if isinstance(self.weight, (int, float, str)):
            self.weight = Decimal(str(self.weight))
    
    @property
    def year_month(self) -> str:
        """获取年月"""
        if self.billing_period:
            return self.billing_period
        if self.cost_date:
            return self.cost_date.strftime('%Y-%m')
        return ""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'warehouse_name': self.warehouse_name,
            'warehouse_region': self.warehouse_region,
            'order_id': self.order_id,
            'sku': self.sku,
            'tracking_number': self.tracking_number,
            'cost_amount': float(self.cost_amount),
            'currency': self.currency,
            'cost_type': self.cost_type.value,
            'cost_type_raw': self.cost_type_raw,
            'cost_date': self.cost_date.isoformat() if self.cost_date else None,
            'billing_period': self.billing_period,
            'quantity': self.quantity,
            'source_file': self.source_file,
        }


@dataclass
class WarehouseBillingSummary:
    """仓库账单汇总"""
    warehouse_name: str
    billing_period: str
    currency: str
    
    total_cost: Decimal = field(default_factory=lambda: Decimal('0'))
    cost_by_type: dict = field(default_factory=dict)
    record_count: int = 0
    
    source_file: str = ""
