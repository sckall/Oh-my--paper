# 学科路由 Playbook

把 user 输入（research direction / abstract）映射到合适的 adapter。

## 关键词触发器

| 学科组 | 触发关键词（中英混合）| 路由到 |
|---|---|---|
| 生医 / 生物 | medicine, medical, clinical, disease, drug, gene, protein, cell, cancer, virus, biology, biomedical, neuroscience, immunology, 临床, 医学, 药物, 基因, 蛋白, 细胞, 肿瘤, 病毒, 生物 | **JANE** ✅ v0.1 实装 |
| 化学 / 材料 / 物理 | chemistry, material, polymer, catalyst, semiconductor, nanotechnology, synthesis, physics, photonic, 化学, 材料, 聚合物, 催化, 半导体, 纳米, 物理 | Springer Suggester / Elsevier JF ⏳ TODO |
| 工程 / 电气 / 计算机 | engineering, electrical, electronic, signal, control, robotics, machine learning, AI, neural network, computer, software, algorithm, 工程, 电气, 控制, 机器学习, 计算机 | IEEE Publication Recommender ⏳ TODO |
| 商科 / 管理 / 文社科 | management, marketing, finance, economics, business, accounting, leadership, social, sociology, psychology, education, 管理, 营销, 金融, 经济, 商业, 社会, 心理, 教育 | ❌ Fallback（无 AI 选刊器，提示 letpub 手筛 + ABS 目录）|
| 跨学科 / 交叉 / AI for X | "X for medicine", "AI in healthcare", "ML for chemistry", AI 应用类 | **JANE 默认**（PubMed 覆盖最广）+ 下轮接其他 adapter 后并发取并集 |

## 决策流程

```
1. 拿到 query → 检查语言
     ├─ 中文 → 直接 fallback 提示用户改用 journal-research-cn
     └─ 英文 / 混合 → 进 step 2

2. 关键词扫描 → 命中第一个学科组
     ├─ 生医 → JANE
     ├─ 化材物 → Springer/Elsevier (TODO，v0.1 返回 not_implemented)
     ├─ 工电计 → IEEE (TODO，v0.1 返回 not_implemented)
     ├─ 商科文社 → fallback（空 list + 提示）
     └─ 多学科 / 无匹配 → JANE 默认（PubMed 是宽语料）

3. 学科识别置信度 < 0.6（边界模糊）
     → 同时跑 JANE + 任一 TODO adapter 的 stub 提示
     → orchestrator 看到双 source 时取 JANE（v0.1 唯一实装）
```

## 边缘案例

| 输入 | 处理 |
|---|---|
| "我研究 LLM 在医学的应用" | 跨学科——计算机 + 生医。v0.1 走 JANE（生医优先），下轮加 IEEE 并发 |
| "城市规划与社会公平" | 商科/文社——fallback |
| "材料力学有限元分析" | 化材物——v0.1 返回 not_implemented + 提示用 letpub 手筛 |
| "我研究的方向" | query 信息量 < 5 字 → 退给用户："请补充关键词或摘要" |
| "中文期刊投稿" | 直接 fallback 提示走 `journal-research-cn:muchong-cn-journal-review` 或 PLAN-3 中文探索 skill |
| 空 query | 拒绝，返回 error |

## 实现提示

学科识别用关键词词典 + 模型判断混合：

- 词典提供 fast-path（覆盖 80% 明确场景）
- 模糊场景调当前 agent 的语义判断（"这个 query 偏向哪个学科组"）
- 不要硬编码字典——保留可扩展

## 与 orchestrator 的契约

orchestrator 调本 skill 时会传：

```python
{
    "query": str,
    "discipline_hint": str | None,    # 用户主动声明的学科（可选）
    "language_hint": str | None,      # "en" / "zh" / "auto"
    "max_candidates": int,            # 默认 10，上限 20
}
```

本 skill 返回时附带 `routed_to_adapter` 字段，让 orchestrator 知道走了哪条路：

```python
{
    "candidates": [...],
    "routed_to_adapter": "jane" | "springer-stub" | "ieee-stub" | "fallback-business" | "fallback-cn",
    "discipline_detected": "biomedical" | "chemistry" | "engineering" | "business" | "cross-disciplinary",
    "confidence_in_routing": 0.0-1.0,
}
```
