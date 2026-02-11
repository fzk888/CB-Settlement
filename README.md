# 收入核算系统 (Revenue Accounting System)

跨境电商多平台、多店铺月度收入与成本核算。

---

## 项目结构

```
收入核算系统/
├── src/                      # 核心源码
│   ├── models/               # 数据模型 (Transaction, StoreInfo, StoreMonthlyResult 等)
│   ├── parser/               # 各平台/仓库解析器
│   │   ├── multi_platform_scanner.py   # 多平台文件扫描
│   │   ├── amazon_parser.py            # Amazon CSV (多语言、站点/币种)
│   │   ├── temu_parser.py              # Temu FundDetail Excel
│   │   ├── shein_parser.py             # SHEIN 账单 Excel
│   │   ├── managed_store_parser.py    # 托管店铺 Excel
│   │   ├── aliexpress_parser.py        # 速卖通 Excel
│   │   └── warehouse_parser.py         # 仓库账单 (Phase 2)
│   ├── calculator/           # 核算逻辑 (RevenueCalculator, 聚合等)
│   ├── reporter/             # 报表导出 (Excel)
│   └── main.py               # 应用入口 (供 run_phase1.py 调用)
│
├── run_phase1.py             # Phase 1 单入口 (基于 src.main，主要测 Amazon)
├── run_phase1_multiplatform.py   # Phase 1 多平台核算主入口（推荐）
├── run_phase2.py             # Phase 2：平台收入 × 仓库履约成本
│
├── data/                     # 数据目录
│   ├── 部分店铺收入/          # 平台账单 (亚马逊、多平台、速卖通)
│   └── 仓库财务账单/          # 海外仓账单 (Phase 2)
│
├── output/                   # 报表输出 (Phase1/Phase2 Excel)
├── docs/                     # 项目文档 (平台字段对照、仓库说明等)
├── scripts/                  # 辅助脚本
│   └── run_monthly_accounting.py   # 月度利润核算（依赖 profit_accounting 包时使用）
│
├── requirements.txt
└── README.md
```

---

## 环境与依赖

```bash
pip install -r requirements.txt
```

主要依赖：`pandas`、`openpyxl`、`xlsxwriter`、`PyYAML`。

---

## 快速开始

### Phase 1：多平台收入核算（推荐）

扫描并解析各平台账单，按店铺/月份/币种汇总平台净结算：

```bash
python run_phase1_multiplatform.py
```

- **支持平台**：Amazon (CSV)、Temu (Excel)、SHEIN (Excel)、托管店铺 (Excel)、速卖通 (Excel)
- **数据目录**：`data/部分店铺收入/` 下 `亚马逊`、`多平台`、`速卖通`
- **输出**：`output/月度核算报表_Phase1_多平台.xlsx`（若文件被占用则写入 `月度核算报表_Phase1_多平台_auto.xlsx`）

### Phase 1 单入口（仅 Amazon）

```bash
python run_phase1.py
```

输出：`output/月度核算报表_Phase1.xlsx`。

### Phase 2：平台收入 × 仓库成本

在 Phase 1 报表基础上，叠加仓库履约成本汇总：

```bash
python run_phase2.py
```

- 会读取 `output/月度核算报表_Phase1_多平台.xlsx` 或 `月度核算报表_Phase1.xlsx`
- 汇总 `data/仓库财务账单/海外仓账单` 下指定仓库成本
- 输出：`output/月度核算报表_Phase2.xlsx`

---

## Phase 1 功能说明

- **多平台解析**：按文件名与目录自动识别平台并选择对应解析器
- **站点与币种**：优先从文件名解析（如 `4-DE`、`4-UK`）；若文件名无站点，则从正文“All amounts in XXX”等说明推断币种与站点
- **Transfer 剥离**：Amazon 等自动排除提现/转账类记录
- **多维度汇总**：按平台、店铺、站点、月份、币种输出净结算与提现金额

详细字段与公式见：`docs/Phase1_平台字段对照表.md`。

---

## 可选脚本

- **scripts/run_monthly_accounting.py**：月度利润核算流水线入口，需安装并配置 `profit_accounting` 包后使用，例如：
  ```bash
  python scripts/run_monthly_accounting.py --month 2025-11
  ```

---

## 文档

| 文档 | 说明 |
|------|------|
| `docs/Phase1_平台字段对照表.md` | 各平台账单字段、收入公式、排除规则 |
| `docs/Phase2_仓库字段解析说明.md` | 仓库账单结构与解析说明 |
| `docs/多平台多店铺多仓库跨境电商收入核算系统.md` | 系统整体说明 |

---

## 后续规划

- 对接更多平台/店铺格式
- 接入 ERP 采购成本与动态汇率（若需）
