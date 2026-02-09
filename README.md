# 收入核算系统 (Revenue Accounting System)

Phase 1 MVP - 跨境电商月度利润核算

## 📂 项目结构

```
d:/app/收入核算系统/
├── src/                # 核心源代码 (MVP实现)
│   ├── models/         # 数据模型 (Transaction, StoreMonthlyResult)
│   ├── parser/         # CSV解析器 (Amazon)
│   ├── calculator/     # 核算引擎 (Transfer过滤, 聚合)
│   ├── reporter/       # 报表生成 (Excel导出)
│   └── main.py         # 应用程序入口
│
├── run_phase1.py       # 🚀 启动脚本 (集成测试入口)
│
├── output/             # 报表输出目录
├── scripts/            # 数据分析辅助脚本
├── docs/               # 项目文档
└── 跨境电商数据/         # 数据源目录
```

## 🚀 快速开始

1. **环境依赖**
   ```bash
   pip install pandas xlsxwriter
   ```

2. **运行核算**
   ```bash
   python run_phase1.py
   ```

3. **查看结果**
   结果将生成于 `output/月度核算报表_Phase1.xlsx`

## 📖 Phase 1 功能特性
*   自动扫描并解析 Amazon 月度交易 CSV
*   **Total精度校验**: 确保所有参与计算的记录金额无误
*   **Transfer剥离**: 自动识别并排除提现记录
*   **多维度汇总**: 按店铺、月份生成净结算报表

## 📅 下一步 (Phase 2)
*   对接仓库账单
*   接入 ERP 采购成本
*   支持动态汇率
