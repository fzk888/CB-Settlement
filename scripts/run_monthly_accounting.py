#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
月度利润核算运行脚本

使用示例：
    python run_monthly_accounting.py --month 2025-11
    python run_monthly_accounting.py --month 2025-11 --platform-dir ./data/platforms
"""
import argparse
import logging
from pathlib import Path
from datetime import datetime
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from profit_accounting.pipeline.monthly_pipeline import MonthlyAccountingPipeline


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    parser = argparse.ArgumentParser(
        description='月度利润核算系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s --month 2025-11
  %(prog)s --month 2025-11 --output ./output/november_report.xlsx
  %(prog)s --month 2025-11 --dimensions platform store site warehouse
        '''
    )
    
    parser.add_argument(
        '--month', '-m',
        required=True,
        help='目标月份 (格式: YYYY-MM)'
    )
    
    parser.add_argument(
        '--config-dir', '-c',
        type=Path,
        default=Path(__file__).parent.parent / 'configs',
        help='配置文件目录路径 (默认: ./configs)'
    )
    
    parser.add_argument(
        '--platform-dir', '-p',
        type=Path,
        default=Path(__file__).parent.parent / '跨境电商数据/部分店铺收入',
        help='平台数据目录路径'
    )
    
    parser.add_argument(
        '--warehouse-dir', '-w',
        type=Path,
        default=Path(__file__).parent.parent / '跨境电商数据/财务账单',
        help='仓库账单目录路径'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='输出文件路径 (默认: ./output/YYYY-MM_月度利润报表.xlsx)'
    )
    
    parser.add_argument(
        '--dimensions', '-d',
        nargs='+',
        default=['platform', 'store', 'site'],
        choices=['platform', 'store', 'site', 'warehouse'],
        help='聚合维度 (默认: platform store site)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # 验证月份格式
    try:
        datetime.strptime(args.month, '%Y-%m')
    except ValueError:
        logger.error(f"无效的月份格式: {args.month}, 请使用 YYYY-MM 格式")
        sys.exit(1)
    
    # 设置输出路径
    if args.output is None:
        output_dir = Path(__file__).parent.parent / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        args.output = output_dir / f"{args.month}_月度利润报表.xlsx"
    
    # 验证目录存在
    if not args.config_dir.exists():
        logger.error(f"配置目录不存在: {args.config_dir}")
        sys.exit(1)
    
    if not args.platform_dir.exists():
        logger.warning(f"平台数据目录不存在: {args.platform_dir}")
    
    if not args.warehouse_dir.exists():
        logger.warning(f"仓库账单目录不存在: {args.warehouse_dir}")
    
    # 执行核算
    try:
        logger.info("初始化核算流水线...")
        pipeline = MonthlyAccountingPipeline(args.config_dir)
        
        logger.info(f"开始 {args.month} 月度核算...")
        output_path = pipeline.run(
            platform_data_dir=args.platform_dir,
            warehouse_data_dir=args.warehouse_dir,
            output_path=args.output,
            target_month=args.month,
            dimensions=args.dimensions
        )
        
        logger.info(f"核算完成！报表已保存到: {output_path}")
        
    except Exception as e:
        logger.exception(f"核算过程出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
