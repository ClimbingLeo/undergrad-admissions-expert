---
name: ib-maths-ee-scraper
description: >
  从 Clastify.com 批量抓取 IB 数学 Extended Essay（EE）并写入本地知识库。
  需要用户已登录 Clastify Premium。利用页面内嵌的 __NEXT_DATA__ 获取 EE 元数据列表，
  然后逐篇导航至个人 EE 页面，提取 react-pdf 渲染的 PDF 文本（前5页 + 后3页）写入 MD 文件。
  当用户说"去Clastify抓A级EE"、"继续抓B级"、"搜集IB maths EE样本"、
  "抓50篇高分EE"、"扩充EE知识库"、"帮我找C级EE参考"时触发本 skill。
metadata:
  author: Leo
allowed-tools:
  - mcp__Claude_in_Chrome__computer
  - mcp__Claude_in_Chrome__navigate
  - mcp__Claude_in_Chrome__javascript_tool
  - mcp__Claude_in_Chrome__read_console_messages
  - mcp__Claude_in_Chrome__tabs_context_mcp
  - mcp__Claude_in_Chrome__get_page_text
  - Read
  - Write
  - Bash
---

# IB Maths EE Scraper Skill

## ⚠️ 关键约束（必须严格遵守）

1. **一次只处理一篇 EE**：不要批量同时处理多篇，会耗尽 context window
2. **PDF 等待**：react-pdf 异步渲染，必须等待 `.react-pdf__Page__textContent` 元素出现（最多等 8×2s）
3. **console 清空**：每次输出前先执行 `console.clear()`，避免旧消息积累超限
4. **每段 5000 字符**：通过 console 传输内容时每段不超过 5000 字符
5. **追加写入**：每篇 EE 提取后追加写入对应 grade 文件，不覆盖已有内容

---

## 输出文件位置

| Grade | 文件路径 |
|-------|---------|
| A | `/Users/leo/Downloads/Cowork/IB_essay/ib_maths_ee_grade_a.md` |
| B | `/Users/leo/Downloads/Cowork/IB_essay/ib_maths_ee_grade_b.md` |
| C | `/Users/leo/Downloads/Cowork/IB_essay/ib_maths_ee_grade_c.md` |

---

## Step 1：发现 EE 列表（列表页）

首先导航到 Clastify IB Maths EE 列表页：

```
https://www.clastify.com/ee/maths
```

然后在浏览器执行以下 JS，获取所有可用 EE 的元数据：

```javascript
(async () => {
  // 先从页面 __NEXT_DATA__ 读取
  const nd = window.__NEXT_DATA__?.props?.pageProps?.initialResources;
  if (!nd) { console.log('ERROR: no __NEXT_DATA__'); return; }

  // 按 grade 分组
  const byGrade = {};
  nd.forEach(r => {
    const g = r.grade || 'unknown';
    if (!byGrade[g]) byGrade[g] = [];
    byGrade[g].push({
      id: r._id,
      title: r.title || '(no title)',
      rq: r.researchQuestion || '',
      session: r.applicationYear || '',
      grade: g,
      url: `https://www.clastify.com/ee/maths/${r._id}`
    });
  });

  // 输出汇总
  console.clear();
  const summary = Object.entries(byGrade).map(([g, arr]) => `${g}: ${arr.length}篇`).join(', ');
  console.log('SUMMARY:' + summary);

  // 输出各 grade 的 ID 列表（A/B/C）
  for (const [g, arr] of Object.entries(byGrade)) {
    console.log(`IDS_${g}:` + JSON.stringify(arr));
  }
})();
```

读取 console，了解各 grade 可用数量，以及各 EE 的 id、title、rq、session。

---

## Step 2：逐篇提取 EE 正文

### 2a. 导航到单篇 EE 页面

```
https://www.clastify.com/ee/maths/{ID}
```

### 2b. 等待 PDF 渲染并提取文本

在浏览器执行以下 JS：

```javascript
(async () => {
  // 等待 react-pdf 渲染（最多 8×2s = 16s）
  for (let i = 0; i < 8; i++) {
    if (document.querySelectorAll('.react-pdf__Page__textContent').length > 0) break;
    await new Promise(r => setTimeout(r, 2000));
  }

  const pages = Array.from(document.querySelectorAll('.react-pdf__Page__textContent'));
  const r = window.__NEXT_DATA__?.props?.pageProps?.resource;

  if (!r) { console.log('ERROR: no __NEXT_DATA__ resource'); return; }
  if (pages.length === 0) { console.log('ERROR: PDF pages not rendered'); return; }

  const totalPages = pages.length;

  // 提取前5页（简介/背景/数学工具）
  const introText = pages
    .slice(0, Math.min(5, totalPages))
    .map(el => el.innerText.trim())
    .join('\n\n---\n\n');

  // 提取后3页（结论/参考文献/RPPF）
  const conclusionText = pages
    .slice(Math.max(0, totalPages - 3))
    .map(el => el.innerText.trim())
    .join('\n\n---\n\n');

  // 构建 MD 格式
  const md = [
    `<!-- ee_id: ${r._id} -->`,
    `<!-- source: ${window.location.href} -->`,
    ``,
    `# ${r.title || '(Untitled)'}`,
    ``,
    `**Grade:** ${r.grade || 'N/A'}  `,
    `**Session:** ${r.applicationYear || 'N/A'}  `,
    `**Total Pages:** ${totalPages}  `,
    `**URL:** ${window.location.href}`,
    ``,
    `## Research Question`,
    ``,
    (r.researchQuestion || '*(not extracted)*'),
    ``,
    `## Introduction / Background (Pages 1–5)`,
    ``,
    introText,
    ``,
    `## Conclusion / References / RPPF (Last 3 Pages)`,
    ``,
    conclusionText,
    ``,
    `---`,
    ``
  ].join('\n');

  // 分段输出到 console
  console.clear();
  const sz = 5000;
  const n = Math.ceil(md.length / sz);
  for (let i = 0; i < n; i++) {
    console.log(`EE_CHUNK_${i}:` + md.substring(i * sz, (i + 1) * sz));
  }
  console.log(`EE_CHUNK_END:${n}`);

  return `OK: pages=${totalPages}, chars=${md.length}, chunks=${n}`;
})();
```

### 2c. 读取 console 并追加写入 MD 文件

1. 调用 `read_console_messages`（pattern: `EE_CHUNK_`）
2. 将所有分段按序拼接（去掉 `EE_CHUNK_0:`, `EE_CHUNK_1:` 等前缀）
3. 先用 `Read` 读取目标 MD 文件（获取当前内容）
4. 用 `Write` 写入：原内容 + 新 EE 内容追加

> ⚠️ 如果 MD 文件不存在，创建时先写入 header：
> ```markdown
> # IB Maths EE — Grade X 样本库
>
> > 来源：Clastify.com（需 Premium 账号）
> > 格式：前5页简介 + 后3页结论/参考文献/RPPF
>
> ---
> ```

---

## Step 3：处理公式密集页面（可选）

数学公式在 react-pdf 文本层提取时会乱码（如 `∫`, `Σ`, `∂` 等符号可能丢失或变形）。

如果用户要求抓取公式，或遇到文本提取结果明显不完整时，可截图保存：

```javascript
// 对特定页截图（页码从1开始）
// 使用 mcp__Claude_in_Chrome__computer 工具截图当前视图
```

截图建议保存路径：`/Users/leo/Downloads/Cowork/IB_essay/screenshots/{ee_id}_page_{n}.png`

通常**不需要截图**——文本提取足以获取 EE 结构、RQ、参考文献和论证思路。

---

## Step 4：去重检查

在追加新 EE 前，检查目标 MD 文件中是否已存在该 EE（通过 `ee_id` comment 检查）：

```bash
grep -c "ee_id: {ID}" /sessions/stoic-adoring-pasteur/mnt/IB_essay/ib_maths_ee_grade_a.md
```

若输出 `1` 或更大，说明已存在，跳过。

---

## 完整工作流程示例

### 场景：「去Clastify抓10篇A级IB maths EE」

```
1. navigate → https://www.clastify.com/ee/maths
2. javascript_tool → 执行 Step 1 JS，读取 IDS_A 列表
3. read_console_messages(pattern="IDS_A:") → 得到 A 级 EE 的 id 列表
4. 对每篇 EE（最多按用户要求数量）：
   a. 去重检查（bash grep）
   b. navigate → https://www.clastify.com/ee/maths/{id}
   c. javascript_tool → 执行 Step 2b JS（等PDF，提取，分段输出）
   d. read_console_messages(pattern="EE_CHUNK_") → 拼接内容
   e. Read ib_maths_ee_grade_a.md → Write（追加）
   f. 报告进度："已完成第 X/10 篇：{title}"
5. 汇报总结：共抓取 N 篇，已写入文件
```

---

## 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `ERROR: no __NEXT_DATA__` | 页面未完全加载 | 等待2s后重试；检查是否已登录 Premium |
| `ERROR: PDF pages not rendered` | react-pdf 渲染超时 | 增加等待轮次至12×2s；或截图确认页面状态 |
| console 内容为空/不完整 | 旧消息积累 | 确认执行了 `console.clear()`；重新执行 JS |
| 公式显示为乱码 | PDF 文字层编码问题 | 正常现象，数学符号会丢失；如需精确公式，改用截图 |
| 列表页 `__NEXT_DATA__` 无 EE | 页面 CSR 加载 | 等待5s后重新执行；检查 `initialResources` 路径 |
| EE 已存在但仍然写入 | 跳过了去重检查 | 执行 Step 4 的 bash grep 后再判断 |

---

## 数据字段说明

| 字段 | 来源 | 说明 |
|------|------|------|
| `title` | `__NEXT_DATA__.resource.title` | EE 标题（通常包含数学主题） |
| `grade` | `__NEXT_DATA__.resource.grade` | 成绩等级：`"A"` / `"B"` / `"C"` |
| `researchQuestion` | `__NEXT_DATA__.resource.researchQuestion` | 研究问题原文 |
| `applicationYear` | `__NEXT_DATA__.resource.applicationYear` | IB session 年份（如 `"May 2023"`） |
| `totalPages` | `pages.length` | PDF 总页数（通常 30–60 页） |
| Pages 1–5 | `react-pdf__Page__textContent` | 简介、背景、数学工具定义 |
| Last 3 Pages | `react-pdf__Page__textContent` | 结论、参考文献、RPPF 反思 |

---

## Chrome Private Network Access 限制

⚠️ **从 Clastify 页面无法直接 POST 到本地服务器（127.0.0.1）**。  
Chrome 的 Private Network Access 策略会阻止 HTTPS 页面向私有 IP 发起请求。

唯一可靠的数据传输路径：**console → read_console_messages → Write tool**。
