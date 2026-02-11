# -*- coding: utf-8 -*-
"""
多平台文件扫描器

自动识别并分类各平台的账单文件
"""
import os
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
import re


@dataclass
class PlatformFile:
    """平台文件信息"""
    platform: str
    file_path: str
    store_name: str
    year_month: str


class MultiPlatformScanner:
    """多平台文件扫描器"""
    
    # 支持的平台列表
    PLATFORMS = ['amazon', 'temu', 'shein', 'managed_store', 'aliexpress']
    
    def __init__(self, base_dirs: List[str]):
        self.base_dirs = base_dirs
    
    def scan(self) -> Dict[str, List[PlatformFile]]:
        """扫描所有平台文件"""
        results = {p: [] for p in self.PLATFORMS}
        
        for base_dir in self.base_dirs:
            if not os.path.exists(base_dir):
                continue
            
            for root, dirs, files in os.walk(base_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    platform, store_name, year_month = self._classify_file(filename, root)
                    
                    if platform and platform in results:
                        results[platform].append(PlatformFile(
                            platform=platform,
                            file_path=file_path,
                            store_name=store_name,
                            year_month=year_month
                        ))
        
        return results
    
    def _classify_file(self, filename: str, folder: str) -> Tuple[str, str, str]:
        """
        分类文件
        
        Returns:
            (platform, store_name, year_month)
        """
        filename_lower = filename.lower()
        folder_name = os.path.basename(folder)
        
        # Amazon CSV
        if filename.endswith('.csv') and 'transaction' in filename_lower:
            store_name, year_month = self._parse_amazon_filename(filename)
            return 'amazon', store_name, year_month
        
        # Temu
        # 支持两种命名方式：FundDetail 和 Detail（某些月份可能使用Detail）
        if (('funddetail' in filename_lower or ' detail' in filename_lower) 
            and filename.endswith('.xlsx')
            and self._is_temu_detail_file(filename)):
            store_name = self._extract_before_temu(filename)
            year_month = self._extract_month_from_folder(folder_name)
            return 'temu', store_name, year_month
        
        # SHEIN
        if ('已完成账单' in filename or '账单商品维度' in filename) and filename.endswith('.xlsx'):
            store_name = self._extract_before(filename, '已完成账单')
            year_month = self._extract_month_from_folder(folder_name)
            return 'shein', store_name, year_month
        
        # 托管店铺
        if '收支明细' in filename and filename.endswith('.xlsx'):
            store_name = self._extract_before(filename, '收支明细')
            year_month = self._extract_month_from_folder(folder_name)
            return 'managed_store', store_name, year_month
        
        # 速卖通
        if '收支流水' in filename and filename.endswith('.xlsx'):
            return 'aliexpress', '速卖通', self._extract_month_from_folder(folder_name)
        
        return None, None, None
    
    def _parse_amazon_filename(self, filename: str) -> Tuple[str, str]:
        """解析 Amazon 文件名"""
        # 示例: 2-UK2025JulMonthlyTransaction.csv
        # 或: 智能万物店铺10_UK 2025NovMonthlyTransaction.csv
        
        store_name = ''
        year_month = ''
        
        # 提取年月
        match = re.search(r'(\d{4})(\w{3})Monthly', filename, re.IGNORECASE)
        if match:
            year = match.group(1)
            month_abbr = match.group(2).lower()
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            month = month_map.get(month_abbr, '01')
            year_month = f"{year}-{month}"
        
        # 提取店铺名
        store_match = re.match(r'^(.+?)[-_]?\s*(UK|DE|US|CA|FR|IT|ES|JP|AU)', filename, re.IGNORECASE)
        if store_match:
            store_name = store_match.group(1).strip()
        else:
            store_name = filename.split('.')[0]
        
        return store_name, year_month
    
    def _is_temu_detail_file(self, filename: str) -> bool:
        """
        判断是否为TEMU的Detail文件
        排除其他平台可能使用Detail命名的文件
        """
        filename_lower = filename.lower()
        
        # 如果包含funddetail，肯定是TEMU文件
        if 'funddetail' in filename_lower:
            return True
            
        # 如果是Detail结尾，需要进一步确认是TEMU文件
        # 检查文件名中是否包含TEMU相关的特征
        temu_indicators = [
            ' funddetail',  # 标准格式
            ' detail-',     # Detail后跟数字标识符
            ' detail.',     # Detail后跟文件扩展名
        ]
        
        for indicator in temu_indicators:
            if indicator in filename_lower:
                return True
                
        return False
    
    def _extract_before_temu(self, filename: str) -> str:
        """
        从TEMU文件名中提取店铺名
        支持FundDetail和Detail两种格式
        """
        import re
        
        # 先尝试标准的FundDetail格式
        store_name = self._extract_before(filename, 'FundDetail')
        if store_name != filename.split('.')[0]:
            # 清理可能包含的月份信息
            store_name = re.sub(r'\s*\d+月\s*$', '', store_name).strip()
            return store_name
            
        # 再尝试Detail格式
        store_name = self._extract_before(filename, 'Detail')
        if store_name != filename.split('.')[0]:
            # 清理可能包含的月份信息
            store_name = re.sub(r'\s*\d+月\s*$', '', store_name).strip()
            return store_name
            
        return filename.split('.')[0]
    
    def _extract_before(self, filename: str, marker: str) -> str:
        """提取标记之前的内容"""
        match = re.match(rf'^(.+?)\s*{marker}', filename, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return filename.split('.')[0]
    
    def _extract_month_from_folder(self, folder_name: str) -> str:
        """从文件夹名提取月份"""
        # 示例: 多平台收入-7月
        match = re.search(r'(\d+)月', folder_name)
        if match:
            month = int(match.group(1))
            return f"2025-{month:02d}"  # 假设 2025 年
        return ''


# 测试
if __name__ == '__main__':
    scanner = MultiPlatformScanner([
        r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\亚马逊',
        r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\多平台',
        r'd:\app\收入核算系统\跨境电商数据\部分店铺收入\速卖通',
    ])
    
    results = scanner.scan()
    
    print("多平台文件扫描结果:")
    print("=" * 50)
    for platform, files in results.items():
        if files:
            print(f"\n{platform.upper()}: {len(files)} 个文件")
            for f in files[:3]:
                print(f"  - {f.store_name} | {f.year_month}")
            if len(files) > 3:
                print(f"  ... 及其他 {len(files) - 3} 个文件")
