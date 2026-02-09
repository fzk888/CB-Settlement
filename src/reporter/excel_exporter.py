# -*- coding: utf-8 -*-
"""
Excel报表导出器
"""
from typing import List
import pandas as pd
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import StoreMonthlyResult, ReportOutput


class ExcelExporter:
    """Excel报表导出器"""
    
    def export(
        self, 
        results: List[StoreMonthlyResult], 
        output_path: str
    ) -> ReportOutput:
        """
        导出Excel报表
        """
        try:
            # 转换数据
            rows = [r.to_report_row() for r in results]
            headers = StoreMonthlyResult.report_headers()
            
            df = pd.DataFrame(rows, columns=headers)
            
            # 导出
            # 确保目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 使用xlsxwriter引擎以获得更好格式支持
            writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='月度汇总', index=False)
            
            # 格式化
            workbook = writer.book
            worksheet = writer.sheets['月度汇总']
            
            # 金额列格式
            money_fmt = workbook.add_format({'num_format': '#,##0.00'})
            for i, col in enumerate(headers):
                if i >= 5: # 从销售收入开始是金额列
                    worksheet.set_column(i, i, 15, money_fmt)
                else:
                    worksheet.set_column(i, i, 12)
            
            writer.close()
            
            return ReportOutput(
                success=True,
                report_type='multi_store',
                output_format='excel',
                file_path=output_path,
                data={'rows': len(rows)},
                total_stores=len(results) 
            )
            
        except Exception as e:
            return ReportOutput(
                success=False,
                report_type='multi_store',
                output_format='excel',
                message=str(e)
            )
