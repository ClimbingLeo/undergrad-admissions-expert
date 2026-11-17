# Clastify Common App 抓取 —— 踩坑记录

**最后更新：** 2026-04-14  
**当前进度：** top30: 66篇 / 目标200篇 | top31_50: 10篇

---

## ✅ 已完成

- 收集了 78 个合格 URL（top30 + top31_50）
- 处理了其中约 40 个，top30 从 40 篇增加到 66 篇
- 剩余约 38 个合格 URL 待处理（存在 `/tmp/qualifying_urls.txt`，重启后需重建）
- 还需要更多 URL：通过 Prompt 过滤器组合（7个 Prompt × 3个年份）可获取更多

---

## 🕳️ 坑一：Clastify 每日免费浏览限制

**症状：**
- PDF 容器渲染 `MuiSkeleton` loading 占位符，永远不解析
- 页面出现红色边框（视觉提示）
- `react-pdf__Page__textContent` 始终为 0

**原因：**
- Clastify 免费账号有每日 PDF 查看限额，连续批量抓取后触发限制
- 即使是 Premium 会员，某些情况下也可能触发速率限制

**解决方案：**
- 等待 ~24 小时让限制重置
- Premium 账号限制更宽松，优先使用 Premium 账号登录后抓取
- 每批处理后间隔几秒，减少触发速率限制的可能性

---

## 🕳️ 坑二：2024/2025 新文章 PDF 无法加载（marking.status: "pending"）

**症状：**
- `pdfDocExists: false`，`.react-pdf__Document` 根本不在 DOM 中
- 反复重试也无效

**原因：**
- 新文章（IDs 以 `68xxx`, `69xxx` 开头）的文章内容存储在 OpenAI Assistants API 的文件中（`assistantFileId: "file-xxx"`）
- `marking.status = "pending"` 表示 PDF 还未生成/处理完毕
- 这些文章的内容无法通过浏览器直接访问

**识别方法（在导航前快速检测，节省等待时间）：**
```javascript
const r = window.__NEXT_DATA__?.props?.pageProps?.resource;
if (r.marking?.status === 'pending') return 'SKIP_PENDING:' + r._id;
```

**解决方案：**
- 在批量抓取脚本中加入这个早期检测，立即跳过 pending 文章
- 专注于 2022/2023 及更早年份的文章（IDs 以 `66xxx`, `65xxx`, `64xxx` 开头）

---

## 🕳️ 坑三：字体编码损坏（Font Encoding Issues）

**症状：**
- 提取的 rawEssay 显示乱码：`Xlagzla3 Baaa`, `Gl Ðe · e b×`, `¯·«` 等
- `isReadable` 检测失败

**原因：**
- 某些 PDF 使用自定义字体，PDF.js 无法正确解码字符

**识别方法：**
```javascript
const isReadable = /\b(the|and|my|I|was|it|in|of|to|a)\b/i.test(e.substring(0, 200));
if (!isReadable) return 'UNREADABLE:' + r._id;
```

**解决方案：**
- 可读性检测已集成到提取脚本中，自动跳过

---

## 🕳️ 坑四：Python 脚本学校名称匹配不完整

**症状：**
- 录取了 UCB/UCLA/UCSD 的文章被错误分类到 `top31_50`

**原因：**
- `process_essay.py` 的 TOP30 集合中只有缩写（"uc berkeley"），没有全名
- Clastify 存储的是全名 "University of California, Berkeley"
- 字符串匹配时 `"uc berkeley" in "university of california, berkeley"` = **False**

**修复（已应用到 `/tmp/process_essay.py`）：**
```python
TOP30 = {
    ...
    "university of california, berkeley",
    "university of california, los angeles", 
    "university of california, san diego",
    "georgia institute of technology",
    "rice university",
    "emory university",
    "washington university in st",  # WashU
    ...
}
```

**注意：** 每次新会话需要重新创建 `/tmp/process_essay.py`（`/tmp` 不持久化）

---

## 🕳️ 坑五：console.log 消息读取顺序问题

**症状：**
- `read_console_messages(pattern="^ESSAY_DATA:", limit=1, clear=true)` 返回旧消息
- 因为有多条匹配消息，`limit=1` 只返回第一条（最旧的）

**解决方案：**
- 每次提取时在 console.log tag 中加入文章 ID：`console.log('FE:' + r._id + ':' + JSON.stringify(d))`
- 读取时用精确 pattern 匹配：`pattern="^FE:{specific_id}"`
- 这样即使有旧消息也不会混淆

---

## 🕳️ 坑六：JS 批量检测中学校匹配不准确（影响 pre-filter）

**症状：**
- 批量 fetch 检测时，某些有效 top30 学校被标记为 "discard"
- 例如：`accepted: ["Massachusetts Institute of Technology"]` 被误标为 discard（因为 JS 只匹配 "mit"）

**原因：**
- 批量 fetch 阶段使用 JS 字符串列表匹配，不如 Python 完整

**解决方案：**
- JS pre-filter 只作为初步筛选，可以有误报（false negative）
- 最终分类由 Python `process_essay.py` 决定（更准确）
- 在 JS 检测中添加更多全名匹配词

---

## 📋 下次会话恢复步骤

### 第一步：重建工作文件
```bash
# 检查当前进度
grep -c '<!-- essay_id:' /mnt/common_app_essay/common_app_top30.md

# 获取已处理 IDs
grep "<!-- essay_id:" /mnt/common_app_essay/common_app_top30.md /mnt/common_app_essay/common_app_top31_50.md | grep -oP '[a-f0-9]{24}' | sort > /tmp/already_done_ids.txt
```

### 第二步：重建 process_essay.py
将 `/tmp/process_essay.py` 重新创建（见仓库中的模板），**务必包含完整的 TOP30 全名列表**。

### 第三步：继续处理剩余 qualifying URLs
以下 URL 已预先筛选为 top30/top31_50，但尚未提取 PDF（约 35 个）：

**需要处理（Batch 3 — 2022/2023 文章，预计 PDF 可以加载）：**
- 666dedaa23885f531f7a074f (Stanford/USC/Michigan/UT Austin)
- 6669b7cce1ed6e21742370e7 (Princeton/Yale/Brown/Duke/Rice/Emory/Columbia/Stanford/JHU/UPenn)
- 666798d6ede6aed387aad47c (Harvard/Yale/Columbia)
- 66679374ede6aed387a9f786 (UPenn/Columbia/Cornell)
- 6667916cede6aed387a9bd7b (Yale/UNC/Purdue/Dartmouth)
- 66679036ede6aed387a997f1 (Stanford)
- 66678a6fede6aed387a8a37d (Stanford/UCB)
- 66673d73ede6aed3879b98d1 (Columbia)
- 666733efede6aed38798e10b (UPenn/UChicago/Northeastern)
- 66673181ede6aed387984bf8 (Columbia/UPenn)
- 66672e39ede6aed387977a0b (Harvard/Columbia)
- 66672a5dede6aed38796381b (Harvard/Yale/Columbia)
- 66671eb9ede6aed38791a51a (Yale/Harvard/Columbia)
- 666717b8ede6aed3878fcb00 (Yale/Purdue/USC)
- 66671677ede6aed3878f64b3 (Yale)
- 66670828ede6aed3878a5a77 (Yale/Michigan)
- 66670049ede6aed387875280 (Yale/Harvard)
- 666099f5ede6aed3871e7771 (Yale/Emory/WashU/Stanford/NYU/Duke)
- 66607ad6ede6aed3871644cc (Columbia/Princeton)
- 6660799dede6aed38715f1a4 (Columbia)
- 665f65d4b46fe8a0fe06a985 (Stanford/Columbia/UPenn/Duke/Purdue/Michigan/NW/GaTech/Rice/USC)
- 665f0cfcdb70dc1d067aaf4d (MIT/Stanford)
- 665f09e4db70dc1d0679c28d (Harvard/Yale/Stanford)
- 66293c7b0bdbbaaf1074883f (BU/MIT/Princeton)
- 66293b120bdbbaaf1073f95a (JHU/Princeton/Yale)
- 64cba2d867f22a00126cd085 (Harvard)
- 64c123bdf8603e0013d6581e (Stanford/GaTech)
- 64cba3de67f22a00126cd0f2 (Harvard)
- 66105a4ed5196dc646080d50 (Yale)
- 64c0efd5f8603e0013d6535d (Brown/Emory/UFL/UMiami/FSU)
- 64c11a5ff8603e0013d657e7 (Stanford)
- 64c12297f8603e0013d6580c (Emory)
- 6659b28a82aa9c137326cc9c (MIT — JS 误标 discard，Python 会正确识别)

**跳过的（`marking.status: "pending"` — 无 PDF）：**
- 687b681b, 687ade59, 687a4458, 6879c23f, 688102d0, 689036cd 等 2024/2025 batch

### 第四步：获取更多 URL（通过 Prompt 过滤器）
当前只用了年份过滤器。还可以用 Prompt 1-7 × 年份组合：
```
过滤器 → Prompt → 选择 Prompt 1 → Apply → 收集 URL
过滤器 → Prompt → 选择 Prompt 2 → Apply → 收集 URL
...
过滤器 → Prompt × Year 组合（2022/2023 × Prompt 1-7 = 7 × 40 = 280 URLs）
```
已知含大量哈佛/耶鲁/哥大文章的 2022/2023 batch 质量最高。

---

## 📊 技术细节速查

### URL 格式
```
https://www.clastify.com/common-app-essay-examples/{24位十六进制ID}
```

### 快速提取模板（一篇文章完整流程）
```javascript
// 1. navigate(url) 后等待 PDF 加载
(async()=>{
  await new Promise(r=>setTimeout(r,800));
  const r=window.__NEXT_DATA__?.props?.pageProps?.resource;
  if(!r) return 'NO_DATA';
  if(r.marking?.status==='pending') return 'SKIP_PENDING:'+r._id;
  let ok=false;
  for(let i=0;i<10;i++){await new Promise(r=>setTimeout(r,800));if(document.querySelectorAll('.react-pdf__Page__textContent').length>0){ok=true;break;}}
  if(!ok) return 'FAIL_PDF:'+r._id;
  const gi=r.ownerId?.generalInfo||{};
  const e=Array.from(document.querySelectorAll('.react-pdf__Page__textContent')).map(el=>el.innerText).join('\n').trim();
  if(!/\b(the|and|my|I|was|it|in|of|to|a)\b/i.test(e.substring(0,200)))return'UNREADABLE:'+r._id;
  const d={id:r._id,url:window.location.href,category:r.category,title:r.title,prompt:r.prompt,applicationYear:r.applicationYear,major:r.major,accepted:r.collegesAcceptedTo||[],rejected:r.collegesRejectedFrom||[],enrolledAt:gi.college||null,gender:gi.gender||null,ethnicity:gi.ethnicity||null,country:gi.country||null,satMath:r.scores?.sat?.math||null,satVerbal:r.scores?.sat?.verbal||null,gpa:r.scores?.gpaScore||null,ibScore:r.scores?.ibScore||null,rawEssay:e};
  console.log('FE:'+r._id+':'+JSON.stringify(d));
  return'OK:'+r._id+':'+e.length;
})()
```

### 批量 URL fetch（不需要浏览器渲染）
```javascript
// 一次检测 20-30 个 URL 的录取学校（用 fetch 抓 __NEXT_DATA__ HTML）
const res = await fetch(url);
const html = await res.text();
const m = html.match(/<script id="__NEXT_DATA__" type="application\/json">([\s\S]+?)<\/script>/);
const r = JSON.parse(m[1]).props?.pageProps?.resource;
// r.collegesAcceptedTo → 判断是否 top30/50
```

### 年份过滤器 UI 流程
```javascript
// 打开过滤器 → 选年份 → Apply
const filterBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Filters');
filterBtn?.click();
// 等 800ms...
const yearEl = Array.from(document.querySelectorAll('*')).find(el => el.childElementCount === 0 && el.innerText?.trim() === '2022/2023');
yearEl?.click();
// 等 400ms...
const applyBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Apply Filters');
applyBtn?.click();
// 等 3000ms → 收集 URL
```

