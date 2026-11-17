# IB数学EE大纲评审报告

**评审对象**：Finite-State Difference Constraints and Smoothness in Discrete Time Functions
**研究问题**：How does restricting the first differences of a discrete time function to a finite set affect its smoothness and stability?

---

## 核心判断

这个outline目前处于**C级风险区**。数学工具几乎全部停留在高中以下水平（差分序列、绝对值运算、有限集合枚举），参数测试替代了推导，真实数据仅作"illustration"而非验证核心结论。按现有结构写完，很可能变成一篇「展示已知结论」的描述性文章，而非「用数学解决问题」的探究性论文。

---

## 亮点

- 选题来源于一篇真实发表的同行评审学术论文（Bielski et al., 2024, ACM e-Energy），起点有一定学术分量，不是凭空捏造的话题。
- 结构逻辑清晰，从定义→约束→度量→边界分析→数值验证的链条是合理的研究思路。
- 已识别限制条件（第7节），说明学生有自我审视的意识。

---

## 关键问题（按严重程度排序）

### 问题一：数学深度严重不足（最高影响：Criterion B，潜在丢失4–5分）

**问题**：整篇outline使用的数学工具全部属于高中以下或IB AA/AI基础课程水平：
- 一阶差分 Δyₜ = yₜ − yₜ₋₁：初中数列
- 二阶差分 Δ²yₜ：IB课程内差分运算
- 平均绝对值 O = (1/(T−2)) Σ|Δ²yₜ|：简单描述性统计
- 有限集 S={−a,0,a} 枚举测试：没有推导，是穷举

没有任何超出IB HL课程的工具——没有优化理论、没有凸性分析、没有信号处理框架（如ℓ₁正则化）、没有数值方法的收敛性证明。

**影响**：Criterion B（Knowledge & Understanding，满分6分）严重受限，预计得分不超过2–3分。

**案例对照**：对比A级EE中的交通流量案例，该EE在Greenshield模型基础上引入了马尔可夫链转移矩阵和Webster时差优化——这些都是IB课程之外的工具，构成了Criterion B的高分基础。而本outline从头到尾没有任何超课程内容。

---

### 问题二：参数测试替代了数学推导（影响：Criterion C，潜在丢失5–6分）

**问题**：第5–6节的核心方法是「测试a=3, 6, 12三个值，看哪个效果好」。这不是数学分析，这是枚举实验。没有回答：
- 什么值的a是「最优」的？有没有解析表达式？
- a的最优选择和序列本身的统计性质（如方差、自相关）有什么关系？
- 为什么是这三个值？选取依据是什么？

**影响**：Criterion C（Critical Thinking，满分12分）的核心是分析与推导，而非描述观察结果。「比较三个数值的效果」是描述，不是分析。

**案例对照**：A级EE中的农村儿童认知实验EE，用OLS完整推导了最小二乘估计量的解析表达式，然后才把数据代入——先有数学，后有数值。本outline的顺序是反的：先有数值实验，没有数学。

---

### 问题三：研究问题边界模糊，结论可预测（影响：Criterion A，潜在丢失2–3分）

**问题**：RQ问的是「限制一阶差分到有限集，会如何影响平滑性？」答案几乎已经写在RQ里了——显然会影响，约束越紧影响越大，约束越松越接近无约束。这个结论在提出RQ的瞬间就是可以预测的，不需要做实验来发现。

一个好的RQ应该有一个**不确定的答案**——学生必须通过数学推导才能知道结论。「限制差分到有限集的最优a应该如何选取，才能在控制稳定性的同时最小化信号失真？」这类问题才有探究价值。

**影响**：Criterion A要求RQ清晰且有探究价值，可预测的结论会让考官认为研究缺乏原创性。

---

### 问题四：真实数据仅作"illustration"，无法支撑验证（影响：Criterion C，潜在丢失2–3分）

**问题**：Gas turbine dataset在第6节被明确标注为「may use... as illustration」，在limitations中也承认「real dataset used only as illustration」。这意味着整篇文章的结论是在构造序列（人工数据）上得出的，没有真实世界的验证。

A级EE的标志是：理论结论 → 真实数据验证 → 量化误差并解释偏差来源。单靠构造数据，考官没有理由相信结论具有实际意义。

---

## 具体改进建议

### 针对问题一（数学深度）：引入优化理论框架

把「有限集约束」改写成一个正式的约束优化问题：

```
minimize   Σ (Δ²yₜ)²
subject to  Δyₜ ∈ {−a, 0, a}  for all t
```

然后：
1. 证明这个问题在离散情形下是NP-hard还是可以用动态规划多项式时间求解（提示：DP路径在有限状态空间上是可行的）
2. 写出DP转移方程并推导时间复杂度O(T·|S|²)
3. 讨论当S从有限集扩展到连续区间时，问题退化为标准ℓ₁正则化（TV正则化），建立离散有限集与连续正则化之间的数学联系

这样就引入了动态规划（超出IB课程）和最优化理论，Criterion B分数会有质的提升。

### 针对问题二（参数测试→推导）：推导a的最优选择条件

不要只测试a=3,6,12，而是：
1. 定义信号失真度量：D(a) = Σ(yₜ − ŷₜ)²，其中ŷₜ是约束后的序列
2. 推导D(a)和平滑度O(a)之间的trade-off关系（两者都是a的函数）
3. 推导最优a*的条件：∂[λ·O(a) + D(a)]/∂a = 0，或者在离散情形下找到使Pareto前沿最陡的a值
4. 用这个推导出的a*去做数值实验，而不是拍脑袋选三个值

### 针对问题三（RQ）：重新聚焦研究问题

改写RQ为：

> "What is the optimal finite state set S = {−a, 0, a} for smoothing a discrete time series, and how does the choice of a relate to the statistical properties (variance, autocorrelation) of the original sequence?"

或者：

> "How does the dynamic programming solution to finite-state constrained smoothing compare to ℓ₁-regularized total variation minimization in terms of reconstruction accuracy and computational complexity?"

第二个版本需要引入TV正则化（超课程），但会让Criterion B和C都大幅提升。

### 针对问题四（真实数据）：把gas turbine数据变成核心验证

1. 从Bielski et al.（2024）提取或重现gas turbine功率序列（论文应提供数据或方法）
2. 用推导出的最优a*对真实数据做约束平滑
3. 与原始序列对比：计算O（平滑度）和D（失真度）的具体数值
4. 与无约束TV正则化的结果对比：列出误差表格
5. 解释偏差：为什么有限集约束会在某些时段产生更大失真？

---

## 选题走向建议

### 路径一：在现有方向上深化（推荐，可达B级，加强后可挑战A级）

核心改造：
- 引入**动态规划**求解有限状态约束优化问题（超课程工具）
- 推导**a的最优选择条件**（解析推导，而非数值枚举）
- 把gas turbine数据从"illustration"升级为**核心验证实验**
- 增加与**TV正则化（ℓ₁约束）**的方法对比

需要加入的内容：DP转移方程推导、Pareto最优trade-off分析、与连续方法的比较。这些内容可以在4000词内完成，且有Bielski等人的论文作为学术支撑。

### 路径二：调整RQ，聚焦方法比较

新RQ："How does dynamic programming with finite-state difference constraints compare to total variation regularization for smoothing discrete time series, in terms of mathematical tractability and reconstruction accuracy?"

这个版本：
- 有明确的方法A vs 方法B（满足Criterion C方法比较要求）
- 两种方法都有推导（满足Criterion B数学深度要求）
- 可以用gas turbine数据做真实验证（满足可验证性）

### 路径三：换方向（备选，仅在路径一和二都不想走时考虑）

如果对信号处理不感兴趣，可以考虑以下方向，数学深度天然更高：
- **傅里叶分析在信号去噪中的应用**：FFT推导 + 真实音频数据 + 与小波变换对比
- **马尔可夫链建模离散时间过程**：转移矩阵 + 平稳分布推导 + 真实序列拟合
- **ODE数值方法比较**：欧拉法 vs RK4 vs 解析解，真实物理系统验证

---

## 自查清单得分

| 问题 | 当前状态 | 说明 |
|------|----------|------|
| RQ聚焦性：能在3800词内完整回答？ | ⚠️ | RQ本身可以回答，但结论过于可预测，探究价值低 |
| 数学超越性：有至少一个超出IB HL课程的工具？ | ❌ | 差分、绝对值、枚举测试——全部IB课程以内甚至以下 |
| 可验证性：有真实数据或已知答案验证模型？ | ❌ | 真实数据仅作"illustration"，不构成验证 |
| 个人连接：为什么是这个话题？ | ⚠️ | 来源于学术论文是好事，但没有说明个人连接 |
| 文献支撑：能找到至少8条学术来源？ | ⚠️ | 目前只有1条；离散时间信号处理和TV正则化有大量文献，需要主动找 |
| 方法比较：有至少两种方法并做对比分析？ | ❌ | 只有有限集约束这一种方法；与无约束的"对比"不算方法比较 |

**结论**：6项中通过1项（RQ聚焦性，但有保留），3项❌，2项⚠️。这个outline如果不做实质性修改，Criterion B和C的得分会非常有限。

---

*评审日期：2026-05-15*
