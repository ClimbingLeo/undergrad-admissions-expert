# 调研任务：学校「看重什么样的人」——官方原话收集（所有调研 agent 共用）

背景：我们在验证一个命题：美国顶尖大学除了「好奇、优秀、有影响力」这类人人都说的话之外，是否各自偏好**某种特定的独特性**。如果有，会写进给中国升学顾问用的学校画像；如果只是共性话术，这个命题就是伪命题。你的工作是**收集证据，不是证明命题**。不要只挑有特色的话，学校主要说什么就收什么，共性的话照样收。今天是 2026-11-17。

## 只用官方或准官方来源
按优先级：
1. 招生办官网的「What we look for / Who we are looking for」、申请指南、FAQ；
2. 招生办官方博客、播客文字稿、招生主任/副主任署名文章；
3. 招生主任、校长在校报（Crimson、YDN、Daily Pennsylvanian 等）或权威媒体中的**直接引语**；
4. 校长开学或毕业演讲、使命陈述（mission statement）、本科教育理念页面。

不要用咨询公司博客、Reddit、College Confidential 当证据。可以用它们找线索，但必须追到官方原文。不要把用户或项目的任何信息写进搜索词。

## 输出（每校一个文件）
写到 `/private/tmp/claude-501/-Users-leo--claude-spares-spare-D0sM1z/20ae8b50-7222-4675-8fc3-e228d8b6ad73/scratchpad/values2/<slug>.md`，格式如下：

```
# <slug>

## identifying_terms
（逗号分隔：会直接暴露校名的专有名词，用于盲测时抹掉。包括校名及缩写、吉祥物、城市/街区、校内建筑、以学校命名的项目名、人名。例如：Brown, Brunonian, Providence, Open Curriculum, Paxson）

## quotes
（8–12 条英文原话，每条不超过 40 词，尽量 3 个以上不同来源、跨 2 个年份。格式：）
- "原话" — 说话人/职务，来源类型，年份，URL

## application_design
- 2026–27 补充文书题目（只写题目要点，不抄全文）
- 特殊申请材料（作品集、面试、视频、Maker Portfolio 等）
- CDS C7 中评为 Very important 的项（读本地画像文件 `/Users/leo/Downloads/Cowork/undergrad-admissions-expert/undergraduate_essay/admission profile/` 里对应学校的文件即可）

## candidate_preferences
- 你认为该校有没有区别于同档学校的偏好（0–3 条）。每条写：支持它的 quotes 编号、反面或共性证据、它是否体现在 application_design 中。
- **流行说法核查**：对下面指定的说法，回答官方证据是支持、部分支持还是不支持，并说明理由。
```

## 硬性规则
- 原话必须逐字准确，每条都要能在给出的 URL 上找到。打不开的页面不要用。
- 不要编造任何引语、人名或年份。宁可少收，不要凑数。
- 完成后回复不超过 200 字：每个文件的路径、收集到的条数、哪所学校证据不足。

## 第二批补充（这批学校类型更杂）
- **UC 各校区**：UC 有统一的 comprehensive review 标准（13 项）。先找各校区自己的表述（招生页「我们看重什么」、校区招生主任讲话）；如果某校区基本只是复述 UC 统一标准，就如实写，并在 candidate_preferences 里说明。
- **英国 / ETH**：招生主要看学术潜力和学科兴趣。收集招生办、学院或院系关于 personal statement、面试、「what tutors / selectors look for」的原话，如实记录课外活动在评估中的地位（看或不看、看到什么程度）。UCAS 个人陈述近年有改版，以官方页面为准。
- **香港**：收集招生页关于 non-academic achievements、面试、whole-person development 的表述，区分 JUPAS（本地）与 non-JUPAS / 国际生。
- 公立大学和英港学校如果官方原话本来就很少，8 条以下也可以，但不要凑数，并在回复里说明。
