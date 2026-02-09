# Phase 2.1 仓库字段解析说明

> 版本: Phase 2.1  
> 更新日期: 2026-02-07

---

## 一、WarehouseCost 标准模型

```python
WarehouseCost {
    warehouse_name: str     # 仓库名称 (TSP, 海洋, 西邮 等)
    warehouse_region: str   # 仓库区域 (UK, US, DE)
    
    order_id: str           # 订单号 (可为空)
    sku: str                # SKU (可为空)
    tracking_number: str    # 物流跟踪号 (可为空)
    store_id: str           # 店铺ID (可为空)
    
    cost_amount: Decimal    # 成本金额
    currency: str           # 币种
    cost_type: CostType     # 成本类型枚举
    cost_type_raw: str      # 原始费用描述
    
    cost_date: datetime     # 费用日期
    billing_period: str     # 账单周期 (2025-07)
    
    source_file: str        # 源文件
    row_number: int         # 行号
}
```

---

## 二、CostType 成本类型枚举

| 类型 | 值 | 匹配关键词 |
|------|-----|-----------|
| SHIPPING | 派送费 | 派送, delivery, shipping, 运费 |
| STORAGE | 仓储费 | 仓储, storage, 仓租 |
| INBOUND | 入库费 | 入库, inbound, receiving |
| OUTBOUND | 出库费 | 出库, outbound, fulfil |
| HANDLING | 操作费 | 操作, handling, process |
| PACKAGING | 包装费 | 包装, packag, box |
| RETURN | 退货费 | 退货, return |
| MANAGEMENT | 管理费 | 管理, management, account |
| TRANSPORT | 头程费 | 头程, freight |
| CUSTOMS | 清关费 | 清关, customs, duty |
| OTHER | 其他 | (默认) |

---

## 三、各仓库字段映射

### TSP 仓库 (英国)

| WarehouseCost | TSP 原始列 |
|---------------|-----------|
| warehouse_name | 固定 `TSP` |
| warehouse_region | 固定 `UK` |
| cost_amount | `Cost` |
| currency | 固定 `GBP` |
| cost_type_raw | `Invoice Item Type` |
| cost_date | `Invoice Date` |

**费用类型映射:**
- Account Management Fee → Management
- Pick & Pack, Collection → Handling
- 其他 → Other

---

### 海洋仓库 (英国)

| WarehouseCost | 海洋 原始列 |
|---------------|-----------|
| warehouse_name | 固定 `海洋` |
| warehouse_region | 固定 `UK` |
| order_id | `单号` |
| tracking_number | `跟踪号` |
| cost_amount | `结算金额` |
| currency | `结算币种` |
| cost_type_raw | `费用类型` |

**费用类型映射:**
- 仓储费 → Storage
- 操作费 → Handling
- 运输费 → Shipping
- 包材费用 → Packaging

---

### 西邮仓库 (美国)

| WarehouseCost | 西邮 原始列 |
|---------------|-----------|
| warehouse_name | 固定 `西邮` |
| warehouse_region | 固定 `US` |
| cost_amount | Sheet 内金额列 |
| currency | 固定 `USD` |
| cost_type_raw | Sheet 名称 |

**Sheet → 费用类型:**
- 仓租 → Storage
- 入库 → Inbound
- 自发货 → Shipping

---

## 四、验证结果

| 仓库 | 样本文件 | 记录数 | 总成本 |
|------|---------|--------|--------|
| TSP | Jul25 Wk1 | 525 | 4,786.73 GBP |
| 海洋 | 2025-7月 | 311 | 549.70 GBP |
| 西邮 | 2025.07 | 382 | 215.48 USD |

---

## 五、使用方式

```python
from src.parser.warehouse_parser import TSPParser, HaiyangParser, XiyouParser

# 解析 TSP 账单
parser = TSPParser()
costs, summary = parser.parse('path/to/tsp_invoice.xlsx')

print(f"总成本: {summary.total_cost} {summary.currency}")
```
