# 研究约束清单 (RESTRICTIONS)

## 1. 计算与资源守卫
- [ ] Pilot 运行完成并记录 TIME_ESTIMATE
- [ ] 动态种子缩放（条件 > 100 组时种子降至 3-5 次）
- [ ] time_guard 逻辑已启用（80% 资源时优雅停止）

## 2. 真实性红线
- [ ] 无 RNG 伪造（无 random.uniform() 模拟下降曲线）
- [ ] 真实收敛检查（连续 N 次 objective 变化 < 1e-8）
- [ ] NaN/Inf 根因修复（非 try-except 掩盖）

## 3. 顶会论文标准
- [ ] 1-2 个核心创新点（sushi not curry）
- [ ] Figure 1 架构图存在
- [ ] 消融实验完成（移除组件对比数据存在）
- [ ] Strong baselines（基线经过同等调优）
- [ ] 字数达标（Introduction ≥ 800, Method ≥ 1000）

## 4. 证据一致性
- [ ] 论文声称 vs 实验结果一致
- [ ] Trial count 与代码一致
- [ ] 引用相关性审查完成

## 5. 环境兼容性
- [ ] NumPy 2.x 兼容（无 np.trapz, np.bool, np.int）
- [ ] 硬件检测完成（CUDA/MPS/CPU）