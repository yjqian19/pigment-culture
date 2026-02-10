# blue_paintings.json 数据结构与 1860–1960 筛选说明

## 数据概览

- **总记录数**: 5,241 条
- **来源**: Harvard Art Museums Object API（与 `EDA/object.md` 中 Object 接口一致，本文件为导出子集）
- **与创作年代相关的筛选**: 可以按 **datebegin / dateend** 筛选 1860–1960 年创作的作品

## 能否筛选 1860–1960 的作品？

**可以。**

| 筛选方式 | 记录数 | 说明 |
|----------|--------|------|
| **与 1860–1960 有重叠**（`datebegin`–`dateend` 与 [1860,1960] 相交） | **1,294** | 创作时间段有一部分落在 1860–1960 内即纳入 |
| **严格落在 1860–1960 内**（`datebegin ≥ 1860` 且 `dateend ≤ 1960`） | **1,238** | 整段创作时间都在该百年内 |
| **无年代信息**（`datebegin`/`dateend` 为 null 或 0） | 945 | 无法按数值年代筛选 |

年代字段含义（见 `EDA/object.md`）：

- **datebegin**: 创作开始年（四位数整数，来自 `dated` 的解析）
- **dateend**: 创作结束年（四位数整数）
- **dated**: 创作年代的**自由文本**（如 "c. 1988", "8/23/1941", "1908"），仅作展示/参考

筛选时以 **datebegin / dateend** 为准；需要时可用 **dated** 做展示或二次核对。

---

## 每条记录（data point）可能出现的字段

`blue_paintings.json` 是 Object API 的**子集**，当前每条记录包含以下**顶层键**（所有 5,241 条均存在）：

| 字段 | 类型 | 说明（参见 EDA/object.md） |
|------|------|----------------------------|
| **id** | number | 对象唯一数字 ID（与 objectid 一致） |
| **objectid** | number | 同上 |
| **title** | string | 作品标题 |
| **dated** | string \| null | 创作年代文本（如 "c. 1988", "1908"） |
| **datebegin** | number | 创作开始年（4 位整数；0 表示未提供） |
| **dateend** | number | 创作结束年（4 位整数；0 表示未提供） |
| **classification** | string | 分类名称（如 "Drawings", "Paintings"） |
| **classificationid** | number | 分类 ID |
| **classification_group** | string | 分类组（如 "Painting"） |
| **culture** | string | 文化/地区（如 "American", "Japanese"） |
| **region** | string | 区域（如 "American"） |
| **primaryimageurl** | string | 主图 URL |
| **imagepermissionlevel** | number | 图片使用权限（0/1/2） |
| **people** | array | 关联人物列表（见下） |
| **colors** | array | 从主图提取的颜色列表（见下） |

### people[] 中每个元素可能包含

| 字段 | 类型 | 说明 |
|------|------|------|
| personid | number | 人物 ID |
| name | string | 姓名 |
| displayname | string | 展示用姓名 |
| alphasort | string | 排序用名称 |
| role | string | 角色（如 "Artist", "Sitter"） |
| displaydate | string \| null | 人物生卒等日期展示文本 |
| birthplace, deathplace | string \| null | 出生/逝世地 |
| culture | string \| null | 文化 |
| gender | string | 如 "female", "unknown" |
| prefix | string \| null | 前缀（如 "After"） |
| displayorder | number | 展示顺序 |

- 约 5,037 条记录有 **people**（非空数组）；其余可为空数组或缺失。

### colors[] 中每个元素可能包含

| 字段 | 类型 | 说明（参见 object.md - colors） |
|------|------|----------------------------------|
| color | string | 图中该色 HEX（如 "#967d7d"） |
| spectrum | string | 博物馆 spectrum 调色板中最接近的 HEX |
| css3 | string | CSS3 颜色规范中最接近的 HEX |
| hue | string | 色相名（Red, Orange, Yellow, Green, Blue, Violet, Brown, Grey, Black, White） |
| percent | number | 该色在图中占比，0–1 |

---

## 与完整 Object API 的差异

完整 Object 记录还可能包含（本 JSON 中**未**包含）例如：

- accessionyear, accessionmethod, accesslevel  
- technique, medium, dimensions, provenance, creditline  
- period, century, objectnumber  
- description, commentary, url  
- images[], exhibitions[], contextualtext[]  
- verificationlevel, rank, totalpageviews  
- 等（详见 `EDA/object.md` 与 API 文档）

若需这些字段，需用 **objectid** 或 **id** 再调 `GET /object/{id}` 获取单条完整记录。

---

## 筛选 1860–1960 的示例逻辑（Python）

```python
# 与 1860–1960 有重叠
def overlaps_1860_1960(r):
    b, e = r.get("datebegin"), r.get("dateend")
    if b is None or e is None or (b == 0 and e == 0):
        return False
    return max(1860, b) <= min(1960, e)

# 严格落在 1860–1960 内
def strictly_1860_1960(r):
    b, e = r.get("datebegin"), r.get("dateend")
    if b is None or e is None or (b == 0 and e == 0):
        return False
    return b >= 1860 and e <= 1960

# 使用
with open("blue_paintings.json") as f:
    data = json.load(f)
subset = [r for r in data if overlaps_1860_1960(r)]  # 1294 条
# 或
subset = [r for r in data if strictly_1860_1960(r)]   # 1238 条
```

如需，我可以再帮你写一个直接输出 1860–1960 子集 JSON 或 CSV 的脚本（含命令行参数）。
