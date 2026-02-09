# -*- coding: utf-8 -*-
"""
报表相关数据模型

包含解析结果、计算结果、报表输出等
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Dict, Optional, Any
from .transaction import Transaction


@dataclass
class ParseStats:
    """解析统计信息"""
    total_rows: int = 0
    parsed_rows: int = 0
    skipped_rows: int = 0
    error_rows: int = 0
    
    # 按type统计
    type_counts: Dict[str, int] = field(default_factory=dict)
    
    # 校验统计
    total_verified: int = 0
    total_mismatch: int = 0


@dataclass
class ParseResult:
    """CSV解析结果"""
    success: bool
    transactions: List[Transaction] = field(default_factory=list)
    store_id: str = ""
    store_name: str = ""
    platform: str = ""
    marketplace: str = ""
    currency: str = ""
    year_month: str = ""
    source_file: str = ""
    
    stats: ParseStats = field(default_factory=ParseStats)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """获取解析摘要"""
        return (
            f"文件: {self.source_file}\n"
            f"店铺: {self.store_name} ({self.marketplace})\n"
            f"月份: {self.year_month}\n"
            f"解析: {self.stats.parsed_rows}/{self.stats.total_rows} 行\n"
            f"错误: {len(self.errors)} 条"
        )


@dataclass 
class CalculationResult:
    """核算计算结果"""
    # 店铺信息
    store_id: str
    store_name: str
    year_month: str
    currency: str
    
    # 交易分类
    included_transactions: List[Transaction] = field(default_factory=list)
    excluded_transactions: List[Transaction] = field(default_factory=list)
    
    # 按字段汇总
    field_totals: Dict[str, Decimal] = field(default_factory=dict)
    
    # 按Type汇总
    type_totals: Dict[str, Decimal] = field(default_factory=dict)
    type_counts: Dict[str, int] = field(default_factory=dict)
    
    # 核心结果
    platform_net_settlement: Decimal = field(default_factory=lambda: Decimal('0'))
    transfer_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    
    # 校验
    verification_passed: bool = True
    verification_notes: List[str] = field(default_factory=list)
    
    def get_audit_summary(self) -> str:
        """获取审计摘要"""
        lines = [
            f"=== 核算结果审计 ===",
            f"店铺: {self.store_name}",
            f"月份: {self.year_month}",
            f"货币: {self.currency}",
            f"",
            f"--- 交易分类 ---",
            f"参与计算: {len(self.included_transactions)} 条",
            f"排除(Transfer等): {len(self.excluded_transactions)} 条",
            f"",
            f"--- 按Type汇总 ---",
        ]
        
        for t, amount in sorted(self.type_totals.items(), key=lambda x: -abs(x[1])):
            count = self.type_counts.get(t, 0)
            lines.append(f"  {t}: {amount:,.2f} ({count}条)")
        
        lines.extend([
            f"",
            f"--- 核心指标 ---",
            f"平台净结算: {self.platform_net_settlement:,.2f}",
            f"提现金额(排除): {self.transfer_amount:,.2f}",
            f"",
            f"校验: {'通过' if self.verification_passed else '失败'}",
        ])
        
        if self.verification_notes:
            lines.append("校验备注:")
            for note in self.verification_notes:
                lines.append(f"  - {note}")
        
        return '\n'.join(lines)


@dataclass
class ReportOutput:
    """报表输出结果"""
    success: bool
    report_type: str  # 'single_store', 'multi_store', 'platform_summary'
    output_format: str  # 'console', 'excel', 'json'
    
    # 输出路径
    file_path: Optional[str] = None
    
    # 报表数据
    data: Dict[str, Any] = field(default_factory=dict)
    
    # 汇总
    total_stores: int = 0
    total_platform_net_settlement: Decimal = field(default_factory=lambda: Decimal('0'))
    
    message: str = ""
