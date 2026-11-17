# 思博杂学社 Agent

面向**升学咨询机构**的申请策略系统（Web 应用）。机构的顾问、销售和新人在同一个平台上完成：

| 模块 | 用途 | 对应机构痛点 |
|---|---|---|
| 学生档案 → **背景诊断报告** | 定位、硬件 / 活动分级、叙事主线、相似真实案例对照、选校分档、90 天行动清单 | 交付质量依赖个别顾问 |
| **活动 / Spike 规划** | 2–3 个差异化 Spike 假设 + 学期路线图，参考同专业录取者的真实活动结构 | 活动方案同质化 |
| **文书策略 / 批改** | 按学校 + 题目调出录取与未录取的真实样本对照，生成选题角度、结构骨架或逐段批改 | 文书经验难沉淀 |
| **IB 数学 EE 评审** | 对照真实 A / B / C 级 EE 与评分标准，诊断 RQ、数学深度与批判性分析 | 增值服务 |
| **知识库** | 60 所学校画像、120 份申请者画像（多校录取 / 拒绝结果）、786 篇真实文书全文、30 个深度案例、42 篇 EE 样本 | 新人培训成本高 |
| **获客内容** | 把真实案例转成公众号长文 / 讲座提纲 / 朋友圈文案 | 销售缺专业弹药 |
| **报告编辑与交付** | 顾问可直接改稿（AI 原稿保留、可恢复）；「内部版」带知识库出处，「交付版」把出处换成"案例 1/2/3"，机构品牌页眉，A4 打印 / 存为 PDF | 客户交付 |

所有 AI 输出的边界：

- **不给录取概率**：提示词禁止；输出后再用规则扫描"七成把握、稳录、录取机会 60%"等说法，命中就在报告顶部警告顾问。
- **只能引用本次注入的材料**：每条引用可点击回溯；不在本次检索材料里的 ID（包括各种变体写法）会被自动删除并提示。
- **出处抽查**：生成后自动比对最容易写错的具体事实——引用申请者时写的 SAT / GPA、写成"录取"或"拒绝"的学校是否与档案相符（只查说反了的），引用文书时的英文原话能否在原文中找到；不一致的在报告顶部提示顾问（不自动删改）。学校统计数字和其他论断仍需顾问复核。
- **审稿备注不外流**：模型需要提醒顾问的内容统一写在文末「审稿备注（仅供顾问）」一节，「交付版」打印自动删除。
- **学生姓名脱敏**：档案中登记的中文姓名、名、英文名、别名（含倒序、大小写变化）在发送前统一替换为 S001 这类代号。草稿和上传文件里的其他身份信息（学校名、IB 考号等）不会被识别，请顾问自行删去。

---

## 快速开始（本机）

```bash
cd app
./run.sh
```

打开 http://127.0.0.1:8000 ，用演示账号登录（密码均为 `demo1234`）：

| 账号 | 角色 | 能做什么 |
|---|---|---|
| `owner@demo.sibo` | 机构管理员 | 全部功能 + 成员管理 + API Key + 品牌设置 |
| `consultant@demo.sibo` | 顾问 | 只看自己负责的学生；生成报告 |
| `viewer@demo.sibo` | 只读（销售 / 新人） | 浏览知识库和报告，不能生成或修改 |

首次启动会自动：建库 → 从仓库里的原始素材入库（约 1 秒）→ 创建演示机构、3 位虚构学生和 7 份**示例报告**（真实 API 生成；没有 API Key 也能完整演示）。

### 开启 AI 生成

用管理员登录 → **机构设置** → 填入 Anthropic API Key（加密存储）。也可以在服务器上设置环境变量 `ANTHROPIC_API_KEY` 作为全机构默认值。

- 模型：`claude-opus-5-5`（可用环境变量 `SIBO_MODEL` 覆盖）
- 推理强度：诊断 / 规划 / EE 评审用 `high`，其余用 `medium`；机构设置里可统一调高
- 已开启服务端 refusal fallback：模型偶发误拒时，API 自动换备用模型续写，报告页会注明
- 实测（2026-11-17）：诊断约 1.8 万输入 / 1 万输出 token（含思考），活动规划 1.4 万 / 0.9 万，文书类 0.5–0.7 万 / 0.45 万，EE 评审 2 万 / 2.4 万（逐条复算推导，思考量大），获客 0.7 万 / 0.5 万；单份 1–5 分钟
- 网络中断时：还没输出正文就断开的，自动重试最多 2 次；已经输出一部分的，保留已生成内容并提示重新生成
- **填好 Key 后先点「测试连接」**：用与正式生成相同的模型和参数发一个极小的请求，10 秒内确认 Key、模型、网络都可用
- 每个机构每天最多生成 60 份报告（`SIBO_DAILY_REPORT_LIMIT` 可调），防止误操作或账号泄露后烧 Key

> **网络**：服务器必须能访问 `api.anthropic.com`。中国大陆服务器通常无法直连，需设置 `HTTPS_PROXY`（出口代理）或 `ANTHROPIC_BASE_URL`（可用的 API 网关），两者都已在 `docker-compose.yml` 中预留。

## 部署（Docker）

```bash
# 在仓库根目录
echo "SIBO_SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_hex(32))')" > app/.env
cd app && docker compose --env-file .env up -d --build
```

- **中国大陆服务器**：Docker Hub 和 PyPI 通常拉不下来，在 `app/.env` 里加两行再构建（2026-11-17 实测 daocloud 镜像站 + 清华 PyPI 可用，构建约 20 秒）：
  ```
  SIBO_BASE_IMAGE=docker.m.daocloud.io/library/python:3.12-slim
  SIBO_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
  ```
  调用 Claude 需要代理时设 `SIBO_HTTPS_PROXY`（容器内可达的地址；代理在宿主机上要写 `http://host.docker.internal:端口`，不能写 127.0.0.1）。宿主机 shell 里的 `HTTPS_PROXY` 不会被带进容器。
- 数据库在 Docker 卷 `sibo-data`（`/data/sibo.db`，单个 SQLite 文件）。**备份 = 复制这个文件**。
- 镜像内含知识库原始素材，容器首次启动时自动入库。
- `SIBO_SECRET_KEY` 用于会话签名和 API Key 加密，**上线后不要更换**，否则已保存的 Key 需要重新填写。
- 正式对外请放在 HTTPS 反向代理（Nginx / Caddy）之后，并设 `SIBO_HTTPS_ONLY=1`（会话 Cookie 只走 HTTPS）。
- `docker-compose.yml` 默认**不写入**演示机构（演示账号的密码是公开的）。本地演示时设 `SIBO_SEED_DEMO=1`。
- 只跑**单个 worker**：生成任务在进程内存中执行，多 worker 时 SSE 进度可能连到另一个进程。单机构规模下单 worker 足够。
- 服务重启时，正在生成的报告会被标记为「中断」，顾问重新生成即可。

## 开通新机构

```bash
cd app
.venv/bin/python -m sibo.cli create-org "某某教育" boss@example.com "张老师"
# 输出邀请链接 /invite/<token>，发给对方设置密码
```

机构管理员登录后，在「机构设置」里邀请顾问 / 只读成员，生成邀请链接发给对方。

- 邀请链接 7 天内有效，用一次即失效；只有机构管理员能看到。
- 成员忘记密码：管理员在成员列表点「重设密码链接」，发给对方。所有人都可以在「我的账号」里自行修改密码。
- 顾问离职：管理员停用账号，并在学生档案编辑页把「负责顾问」改成其他人。
- 家长要求删除数据：学生详情页底部「删除学生档案」，输入代号确认，档案和全部报告一并删除。
- 登录连续失败 8 次会锁定 15 分钟（按邮箱和 IP 分别计数）。

## 更新知识库

修改仓库中 `clastify/`、`undergraduate_essay/` 下的素材后：

```bash
.venv/bin/python -m sibo.cli ingest
```

入库是幂等的：只重建知识表，不影响机构、学生和报告。结束时打印各表计数，「数据来源说明」页同步更新。

## 数据质量与使用边界（交付前必读）

- **学校画像**：人工 + AI 整理。只有附带公开链接的数据段落标为「已溯源」，其余（包括「总结 / 建议 / 规律」类观点段落）标「数据待核实」。画像里所有「真实案例」小节经抽查都是综合或虚构人物（如"李明，北京一流国际学校"），系统统一标为「示例画像（非真实案例）」：页面醒目提示，AI 检索也不会引用。
- **申请者画像**：来自 Clastify，以美国本土和其他国际生为主，中国大陆样本仅 3 份。适合作为"能力 / 活动结构参照"，不能当作中国学生的录取标准。
- **文书全文**：来自 Clastify（含付费可见内容）、学校官方 Essays That Worked、学生公开博客。产品内保留全文供机构内部研究，**存在版权与平台条款风险，由运营方自行评估承担**。建议：只在登录后可见；对外材料只用短摘录 + 链接；禁止用于代写。
- **Harvard Crimson 文书**：属于赞助专题，非哈佛官方，系统已标注。
- **学生数据**：会以代号形式发送给 Anthropic API 处理。请在机构服务协议中告知家长。
- **藤校 + 顶尖私校画像（2026-11 新增）**：Harvard、Yale、Princeton、MIT、Columbia、Penn、Caltech、UChicago、Duke、Brown、Cornell、Dartmouth、Northwestern 共 13 所，由调研 agent 逐条对照官方来源（招生办新闻稿、Common Data Set、官方 class profile、2026–27 官方文书题目）编写，每个数字附原始链接，未编写任何学生案例；官方未公布的数据（如多数学校的国际生录取率、早申分轮次数据）明确写「官方未公布」。每年 9–11 月新数据发布后需要更新。
- **热门公立 / 私校画像（2026-11 第二批）**：CMU、UC Berkeley、UCLA、Michigan、Rice、Vanderbilt、WashU、Notre Dame 共 8 所，编写规则同上；UC 系列按 test-blind 和 PIQ 写，CMU / Berkeley / Michigan / UCLA 单列了学院或专业差异。Fable 独立抽查约 60 处，未发现编造的数字或人物；已改正 CMU「ED 只能报一个学院」、Michigan ED 录取率不可比等问题。至此 US News 全国大学排名前 30 都有画像；顶尖文理学院（Williams、Amherst、Pomona、Harvey Mudd 等）和其余学校仍未覆盖，诊断报告会提示"材料未覆盖，需顾问补充核实"。
- **「学校看重的特质（官方表述）」（2026-11，全部 60 校）**：每校 10–15 条官方原话（招生办、招生主任、校长），逐字核对原网页。按同档分 6 组（美国顶尖 15、美国私立 13、UC 6、美国其他公立 13、英国 + ETH 8、香港 5）做抹名盲测：只保留特质描述、意译成中文后让评判模型配对。分档结果：明显 16 所、中等 14 所、与同档学校基本一致 30 所；靠制度线索猜对的不算特质差异。档位写在每节开头，明细见「数据来源说明」页。只证明学校公开说法不同，不证明录取实际加权。每节都经 Fable 独立审稿后改正。证据、盲测材料和预测记录在仓库 `research/school_values_2026-11/`。
- **官方原件核对**：Princeton、Brown、Columbia、Notre Dame 的 2025–26 CDS 和 Yale Class of 2030 官方 profile 已下载逐项比对，数字一致；MIT、Berkeley、UCLA 见上。JHU 2025–26 CDS 核对后更正了数据表（旧表把上一届数字标成 Class of 2029），UNC 2025–26 CDS 核对后更正了 C7。部分官方页面（Tableau、Cloudflare 防护、403）无法自动读取，相关数字保留来源链接，待人工下载原件后复核。
- **文书题目、申请要求与奖学金核对（2026-11，全部 60 校）**：逐校对照官网 2026–27 要求改正题目原文、字数、截止日期、面试和笔试，以及国际生的奖学金 / 资助资格。改出的典型错误：UCSB、UC Davis、UCSD 把 Common App 题或编造的题塞进 UC PIQ；部分 UC 画像写了不存在的 EA；Ohio State 建议中国学生申请只限美国公民 / 绿卡的 Morrill；英国画像仍用旧版 UCAS 个人陈述和已停用的 MAT / PAT / TSA；多所学校写了国际生拿不到的 merit 奖学金或 need-based 资助，或编造了奖学金档次和金额。官网打不开的（Michigan、UVA、Columbia、NYU 申请页等）只标「待核」，不下结论。官方题目原文存于 `research/official_prompts_2026-11/`。

## 开发

```bash
cd app
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt pytest httpx
.venv/bin/python -m pytest -q          # 解析器、入库计数、检索、引用校验、权限 / 租户隔离、生成链路
```

```
app/
├── sibo/
│   ├── ingest/        # 素材解析（parsers.py）与入库（run.py）
│   ├── ai/            # builder（组装请求）· retrieval（SQL+FTS5 检索）· prompts · citations（引用校验）· client（Claude）· runner（后台生成 + SSE）
│   ├── web/           # FastAPI 路由、Jinja 模板、无外部依赖的 CSS
│   ├── samples/       # 预生成示例报告（演示用）
│   ├── auth.py        # 密码、CSRF、角色、按机构隔离的查询
│   ├── schools.py     # 校名归一化
│   └── cli.py         # init / ingest / create-org / seed-demo / set-password
├── scripts/build_samples.py
├── tests/
├── Dockerfile · docker-compose.yml · run.sh
└── DEMO.md            # 3 分钟演示脚本
```
