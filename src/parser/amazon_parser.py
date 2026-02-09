# -*- coding: utf-8 -*-
"""
Amazon CSV 解析器

解析Amazon月度交易CSV，支持:
- 自动检测表头行
- 各数值字段解析
- total字段校验
- Transfer/Payout识别
"""
import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, List, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import (
    Transaction, TransactionType, 
    StoreInfo, ParseResult, ParseStats
)
from src.parser.base_parser import BaseParser


class AmazonCSVParser(BaseParser):
    """Amazon CSV 解析器 (支持多语言)"""
    
    # 语言特征字段 (用于检测表头)
    LANG_MARKERS = {
        'en': ['type', 'product sales', 'total'],
        'de': ['typ', 'umsätze', 'gesamt'],
        'fr': ['type', 'ventes de produits', 'total'],
        'jp': ['トランザクションの種類', '商品の売上', '合計'],
    }
    
    # 多语言完整字段映射
    # 格式: {标准字段名: {lang: 本地化字段名}}
    FIELD_MAPPING_MULTI = {
        'date_time': {
            'en': 'date/time',
            'de': 'datum/uhrzeit', 
            'fr': 'date/heure',
            'jp': '日付/時間'
        },
        'settlement_id': {
            'en': 'settlement id',
            'de': 'abrechnungsnummer',
            'fr': 'numéro de règlement',
            'jp': '決済番号'
        },
        'type_raw': {
            'en': 'type',
            'de': 'typ',
            'fr': 'type',
            'jp': 'トランザクションの種類'
        },
        'order_id': {
            'en': 'order id',
            'de': 'bestellnummer',
            'fr': 'numéro de la commande',
            'jp': '注文番号'
        },
        'sku': {
            'en': 'sku',
            'de': 'sku',
            'fr': 'sku',
            'jp': 'sku'
        },
        'description': {
            'en': 'description',
            'de': 'beschreibung',
            'fr': 'description',
            'jp': '商品名'
        },
        # 数值字段
        'product_sales': {
            'en': 'product sales',
            'de': 'umsätze',
            'fr': 'ventes de produits',
            'jp': '商品の売上'
        },
        'product_sales_tax': {
            'en': 'product sales tax',
            'de': 'produktumsatzsteuer',
            'fr': 'taxe sur les ventes de produits',
            'jp': '商品の売上税'
        },
        'postage_credits': {
            'en': 'postage credits',
            'de': 'gutschrift für versandkosten',
            'fr': 'crédits d\'expédition',
            'jp': '配送料'
        },
        'postage_credits_tax': {
            'en': 'postage credits tax',
            'de': 'steuer auf versandgutschrift',
            'fr': 'taxe sur les crédits d\'expédition',
            'jp': '配送料金にかかる税金'
        },
        'shipping_credits': {
            'en': 'shipping credits',
            'de': 'gutschrift für versandkosten',
            'fr': 'crédits d\'expédition',
            'jp': '配送料' 
        },
        'shipping_credits_tax': {
            'en': 'shipping credits tax',
            'de': 'steuer auf versandgutschrift',
            'fr': 'taxe sur les crédits d\'expédition',
            'jp': '配送料金にかかる税金'
        },
        'gift_wrap_credits': {
            'en': 'gift wrap credits',
            'de': 'gutschrift für geschenkverpackung',
            'fr': 'crédits cadeau',
            'jp': 'ギフト包装手数料'
        },
        'giftwrap_credits_tax': {
            'en': 'giftwrap credits tax',
            'de': 'steuer auf geschenkverpackungsgutschriften',
            'fr': 'taxe sur les crédits cadeau',
            'jp': 'ギフト包装料にかかる税金'
        },
        'promotional_rebates': {
            'en': 'promotional rebates',
            'de': 'rabatte aus werbeaktionen',
            'fr': 'rabais promotionnels',
            'jp': 'プロモーション割引额'
        },
        'promotional_rebates_tax': {
            'en': 'promotional rebates tax',
            'de': 'steuer auf aktionsrabatte',
            'fr': 'taxe sur les rabais promotionnels',
            'jp': 'プロモーション割引の税金'
        },
        'marketplace_withheld_tax': {
            'en': 'marketplace withheld tax',
            'de': 'einbehaltene steuer auf marketplace',
            'fr': 'taxe retenue par le site de vente',
            'jp': '源泉徴収税'
        },
        'selling_fees': {
            'en': 'selling fees',
            'de': 'verkaufsgebühren',
            'fr': 'frais de vente',
            'jp': '手数料'
        },
        'fba_fees': {
            'en': 'fba fees',
            'de': 'gebühren zu versand durch amazon',
            'fr': 'frais expédié par amazon',
            'jp': 'fba 手数料'
        },
        'other_transaction_fees': {
            'en': 'other transaction fees',
            'de': 'andere transaktionsgebühren',
            'fr': 'autres frais de transaction',
            'jp': 'トランザクションに関するその他の手数料'
        },
        'other': {
            'en': 'other',
            'de': 'andere',
            'fr': 'divers',
            'jp': 'その他'
        },
        'total': {
            'en': 'total',
            'de': 'gesamt',
            'fr': 'total',
            'jp': '合計'
        }
    }
    
    # 必需的数值字段
    NUMERIC_FIELDS = [
        'product_sales', 'product_sales_tax',
        'postage_credits', 'postage_credits_tax',
        'shipping_credits', 'shipping_credits_tax',
        'gift_wrap_credits', 'giftwrap_credits_tax',
        'promotional_rebates', 'promotional_rebates_tax',
        'marketplace_withheld_tax',
        'selling_fees', 'fba_fees',
        'other_transaction_fees', 'other',
        'total',
    ]
    
    def __init__(self):
        super().__init__()
        self.encoding = 'utf-8-sig'
    
    def get_platform(self) -> str:
        return "amazon"
    
    def parse(self, file_path: str) -> ParseResult:
        """解析Amazon CSV文件"""
        path = Path(file_path)
        result = ParseResult(
            success=False,
            source_file=path.name,
        )
        
        try:
            # 读取文件
            content = self._read_file(path)
            if not content:
                result.errors.append("文件为空或无法读取")
                return result
            
            # 检测表头行和语言
            header_idx, lang = self._detect_header_and_lang(content)
            
            if header_idx is None:
                result.errors.append("未找到有效表头行 (支持 En/De/Fr/Jp)")
                return result
            
            # 解析店铺信息
            store_info = StoreInfo.from_filename(path.name)
            result.store_id = store_info.store_id
            result.store_name = store_info.store_name
            result.platform = store_info.platform
            result.marketplace = store_info.marketplace
            result.currency = store_info.currency
            
            # 解析CSV
            lines = content.split('\n')
            csv_content = '\n'.join(lines[header_idx:])
            
            transactions, stats, errors = self._parse_csv(
                csv_content, store_info, path.name, lang
            )
            
            result.transactions = transactions
            result.stats = stats
            result.errors.extend(errors)
            result.year_month = self._extract_year_month(path.name, transactions)
            result.success = len(transactions) > 0
            
        except Exception as e:
            result.errors.append(f"解析异常: {str(e)}")
        
        return result
    
    def _detect_header_and_lang(self, content: str) -> Tuple[Optional[int], str]:
        """检测表头行位置及语言"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines[:50]): # 只扫描前50行
            line_lower = line.lower()
            
            # 检测试语言标记
            for lang, markers in self.LANG_MARKERS.items():
                if all(marker in line_lower for marker in markers):
                    return i, lang
                    
        return None, 'en'
    
    def detect_header_row(self, content: str) -> Optional[int]:
        """兼容基类方法"""
        idx, _ = self._detect_header_and_lang(content)
        return idx
    
    def _read_file(self, path: Path) -> str:
        """读取文件内容 (尝试多种编码)"""
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'shift_jis', 'latin-1', 'cp1252']
        
        for enc in encodings:
            try:
                return path.read_text(encoding=enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return ""
    
    def _parse_csv(
        self, 
        csv_content: str, 
        store_info: StoreInfo,
        source_file: str,
        lang: str
    ) -> Tuple[List[Transaction], ParseStats, List[str]]:
        """解析CSV内容"""
        transactions = []
        errors = []
        stats = ParseStats()
        
        reader = csv.DictReader(io.StringIO(csv_content))
        
        # 构建当前语言的字段映射表: csv_col -> attr_name
        current_mapping = {}
        if reader.fieldnames:
            fieldnames_lower = {f.strip().lower(): f for f in reader.fieldnames}
            
            for attr, lang_map in self.FIELD_MAPPING_MULTI.items():
                target_col = lang_map.get(lang)
                if not target_col:
                    target_col = lang_map.get('en') # 回退到英文
                
                if target_col and target_col in fieldnames_lower:
                    current_mapping[fieldnames_lower[target_col]] = attr
        else:
            errors.append("无法读取CSV列名")
            return transactions, stats, errors
            
        row_num = 0
        for row in reader:
            row_num += 1
            stats.total_rows += 1
            
            try:
                txn = self._parse_row(
                    row, current_mapping,
                    store_info, source_file, row_num, lang
                )
                
                if txn:
                    transactions.append(txn)
                    stats.parsed_rows += 1
                    
                    type_name = txn.type.value
                    stats.type_counts[type_name] = stats.type_counts.get(type_name, 0) + 1
                    
                    if txn.is_total_verified():
                        stats.total_verified += 1
                    else:
                        stats.total_mismatch += 1
                else:
                    stats.skipped_rows += 1
                    
            except Exception as e:
                stats.error_rows += 1
                errors.append(f"行{row_num}: {str(e)}")
        
        return transactions, stats, errors
    
    def _parse_row(
        self, 
        row: dict, 
        mapping: dict,
        store_info: StoreInfo,
        source_file: str,
        row_num: int,
        lang: str
    ) -> Optional[Transaction]:
        """解析单行数据"""
        # 提取关键字段判断空行
        # 这里需要用反向映射找到csv列名
        # 为简化，遍历row
        has_content = False
        for v in row.values():
            if v and v.strip():
                has_content = True
                break
        if not has_content:
            return None
            
        txn = Transaction(
            store_id=store_info.store_id,
            store_name=store_info.store_name,
            platform=store_info.platform,
            currency=store_info.currency,
            source_file=source_file,
            row_number=row_num,
        )
        
        # 根据映射填充字段
        for csv_col, value in row.items():
            if not csv_col: continue
            
            attr_name = mapping.get(csv_col.strip())
            if not attr_name: continue
            
            val_str = value.strip() if value else ''
            
            if attr_name == 'date_time':
                txn.date_time = self._parse_datetime(val_str)
            elif attr_name == 'type_raw':
                txn.type_raw = val_str
                # 需要翻译type? 我们的TransactionType.from_string目前只支持英文+变体
                # 建立多语言Type映射
                type_en = self._translate_type(val_str, lang)
                txn.type = TransactionType.from_string(type_en)
            elif attr_name in self.NUMERIC_FIELDS:
                setattr(txn, attr_name, self._parse_decimal(val_str, lang))
            else:
                setattr(txn, attr_name, val_str)
                
        return txn
    
    def _translate_type(self, value: str, lang: str) -> str:
        """翻译交易类型"""
        if lang == 'en': return value
        
        val_lower = value.lower()
        
        # 德语映射
        if lang == 'de':
            if 'bestellung' in val_lower: return 'Order'
            if 'erstattung' in val_lower: return 'Refund'
            if 'übertrag' in val_lower or 'transfer' in val_lower: return 'Transfer'
            if 'servicegebühr' in val_lower: return 'Service Fee'
            if 'anpassung' in val_lower: return 'Adjustment'
            
        # 法语映射
        if lang == 'fr':
            if 'commande' in val_lower: return 'Order'
            if 'remboursement' in val_lower: return 'Refund'
            if 'transfert' in val_lower: return 'Transfer'
            if 'frais de service' in val_lower: return 'Service Fee'
            if 'ajustement' in val_lower: return 'Adjustment'
            
        # 日语映射
        if lang == 'jp':
            if '注文' in val_lower: return 'Order'
            if '返金' in val_lower: return 'Refund'
            if '振込' in val_lower or '送金' in val_lower: return 'Transfer'
            if 'サービス料' in val_lower: return 'Service Fee'
            if '調整' in val_lower: return 'Adjustment'
            
        return value

    def _parse_decimal(self, value: str, lang: str) -> Decimal:
        """解析数值 (处理多语言格式)"""
        if not value or not str(value).strip():
            return Decimal('0')
        
        clean = str(value).strip()
        
        # 德语/法语: 1.234,56 (逗号是小数点，点是千分位)
        if lang in ['de', 'fr']:
            # 有些文件可能已经是标准格式，尝试判断
            # 如果同时有点和逗号，且逗号在后 -> 欧洲格式
            if '.' in clean and ',' in clean and clean.rfind(',') > clean.rfind('.'):
                clean = clean.replace('.', '').replace(',', '.')
            elif ',' in clean and '.' not in clean:
                # 只有逗号 -> 可能是小数点
                # 除非它是只有千分位? 假设是小数点
                clean = clean.replace(',', '.')
        else:
            # 英语/日语: 1,234.56
            clean = clean.replace(',', '')
            
        try:
            return Decimal(clean).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            return Decimal('0')

    
    def _parse_datetime(self, value: str) -> Optional[datetime]:
        """解析日期时间"""
        if not value:
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
        ]
        
        value = value.strip()
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_year_month(
        self, 
        filename: str, 
        transactions: List[Transaction]
    ) -> str:
        """提取年月"""
        # 从文件名提取
        # 示例: 2025NovMonthlyTransaction
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
        }
        
        match = re.search(r'(\d{4})([A-Za-z]{3})', filename)
        if match:
            year = match.group(1)
            month_str = match.group(2).lower()
            month = month_map.get(month_str, '01')
            return f"{year}-{month}"
        
        # 从交易记录提取
        for txn in transactions:
            if txn.date_time:
                return txn.date_time.strftime('%Y-%m')
        
        return ""


def parse_amazon_csv(file_path: str) -> ParseResult:
    """便捷函数: 解析Amazon CSV"""
    parser = AmazonCSVParser()
    return parser.parse(file_path)
