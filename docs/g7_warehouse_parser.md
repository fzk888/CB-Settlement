# G7仓库解析器使用说明

## 概述
G7仓库解析器用于处理G7物流仓库的PDF账单文件，支持自动识别INVOICE（应付费用）和CREDIT NOTE（退款）文件，并计算净支出。

## 功能特点
- ✅ 自动识别PDF文件类型（INVOICE/CREDIT NOTE）
- ✅ 解析Total Amount金额
- ✅ 自动跳过明细文件（Appendix后缀）
- ✅ 按月度汇总成本数据
- ✅ 支持多币种处理（默认USD）

## 文件命名约定
解析器支持以下文件命名格式：

### 标准格式
- `702510206R.pdf` - INVOICE文件
- `702510206R_Appendix.pdf` - 明细文件（自动跳过）
- `702510206R_CREDIT.pdf` - CREDIT NOTE文件

### 日期提取规则
文件名中的数字序列会被解析为日期：
- 格式：`YYMMDD` + 编号 + 后缀
- 示例：`702510206R` → 2025年10月20日
- 年份处理：假设为2020年代（20XX）

## 金额计算逻辑
```
总支出 = Σ(INVOICE金额) - Σ(CREDIT NOTE金额)
```

- INVOICE文件：金额为正数（需要支付）
- CREDIT NOTE文件：金额为负数（退款抵扣）

## 使用方法

### 1. 目录结构
```
data/
└── 仓库财务账单/
    └── 海外仓账单/
        └── G7/
            ├── 702510206R.pdf          # INVOICE
            ├── 702510206R_Appendix.pdf # 明细（跳过）
            ├── 702510227R.pdf          # INVOICE
            └── 702510227R_CREDIT.pdf   # CREDIT NOTE
```

### 2. 运行解析
```python
from src.parser.warehouse_parser import aggregate_warehouse_costs

# 解析G7仓库数据
base_path = r'd:\app\收入核算系统\data\仓库财务账单\海外仓账单'
results = aggregate_warehouse_costs(base_path, ['G7'])

# 查看结果
for result in results:
    print(f"{result.warehouse_name} | {result.year_month} | {result.total_cost} {result.currency}")
```

### 3. 独立测试
```bash
python test_g7_parser.py
```

## 输出示例
```
G7 | 2025-10 | -51,269.94 USD
  - INVOICE Total: 4,770.06
  - CREDIT NOTE Total: -56,040.00
```

## 错误处理
- 无法识别的文件类型会显示警告但不会中断处理
- PDF解析失败的文件会被跳过
- Appendix后缀的明细文件会自动排除

## 依赖库
需要安装以下Python库：
```bash
pip install PyPDF2 pdfplumber
```

## 注意事项
1. 确保PDF文件未被密码保护
2. 文件名应包含可识别的日期信息
3. INVOICE和CREDIT NOTE文件应分别明确标识
4. Appendix后缀文件会自动跳过处理