# -*- coding: utf-8 -*-
"""
从 Phase 1 预留的各种空接口
(Phase 2 实现)
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, Tuple
from datetime import datetime


class WarehouseInterface(ABC):
    @abstractmethod
    def get_monthly_cost(
        self, 
        store_id: str, 
        year_month: str
    ) -> Optional[Decimal]:
        pass

class NullWarehouseInterface(WarehouseInterface):
    def get_monthly_cost(self, store_id, year_month):
        return None


class ExchangeInterface(ABC):
    @abstractmethod
    def get_rate(
        self, 
        from_currency: str, 
        to_currency: str
    ) -> Decimal:
        pass

class FixedExchangeRate(ExchangeInterface):
    RATES = {
        'GBP': Decimal('9.2'),
        'EUR': Decimal('7.8'),
        'USD': Decimal('7.2'),
        'CAD': Decimal('5.3'),
        'JPY': Decimal('0.048'),
        'AUD': Decimal('4.7'),
    }
    
    def get_rate(self, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal('1')
        if to_currency == 'CNY':
            return self.RATES.get(from_currency, Decimal('1'))
        return Decimal('1')
