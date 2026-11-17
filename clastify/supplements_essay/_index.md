# Supplemental Essay 知识库总览
**最后更新：** 2026-04-14
**数据来源：** Clastify 真实学生文书（全部有可溯源 URL）
**总文书数：** 2505 篇 | **学校数：** 26 所

---

## 覆盖情况

| 学校 | 文书数 | 文件结构 | Clastify 可用上限 |
|------|:------:|---------|:-------------:|
| **Stanford** | 309 | 5 个 prompt 子文件夹 | ~320 |
| **Yale** | 244 | 4 个 prompt 子文件夹 | ~261 |
| **Columbia** | 246 | 11 个 prompt 子文件夹 | ~200 |
| **Princeton** | 200 | 7 个 prompt 子文件夹 | ~238 |
| **Brown** | 186 | 6 个 prompt 子文件夹 | ~180 |
| **Harvard** | 108 | 6 个 prompt 子文件夹 | ~122 |
| **Penn** | 115 | 4 个 prompt 子文件夹 | ~105 |
| **Duke** | 106 | prompt_all/ | ~40 |
| **Cornell** | 101 | prompt_all/ | ~26 |
| **MIT** | 70 | 4 个 prompt 子文件夹 | ~78 |
| **UCSD** | 70 | prompt_all/ | ~19 |
| **UCLA** | 69 | prompt_all/ | ~16 |
| **UC Berkeley** | 68 | prompt_all/ | ~15 |
| **CMU** | 63 | prompt_all/ | ~20 |
| **Northwestern** | 61 | prompt_all/ | ~20 |
| **Rice** | 53 | prompt_all/ | ~15 |
| **Dartmouth** | 57 | prompt_all/ | — |
| **Emory** | 51 | prompt_all/ | ~23 |
| **JHU** | 49 | prompt_all/ | — |
| **NYU** | 47 | prompt_all/ | — |
| **Georgetown** | 45 | prompt_all/ | ~10 |
| **Vanderbilt** | 41 | prompt_all/ | ~29 |
| **WashU** | 38 | prompt_all/ | ~17 |
| **Notre Dame** | 34 | prompt_all/ | ~7 |
| **Tufts** | 32 | prompt_all/ | ~11 |
| **UChicago** | 42 | prompt_all/ | ~16 |

---

## Clastify Slug 对照表（Python 直接 fetch 用）

| 学校 | Slug |
|------|------|
| Columbia | columbia-university |
| Yale | yale-university |
| Princeton | princeton-university |
| Harvard | harvard-university |
| MIT | **mit** |
| Stanford | stanford-university |
| Penn | **upenn** |
| Brown | brown-university |
| Dartmouth | dartmouth-college |
| Cornell | cornell-university |
| JHU | **johns-hopkins** |
| Rice | rice-university |
| Northwestern | northwestern-university |
| Duke | duke-university |
| Vanderbilt | vanderbilt-university |
| Georgetown | georgetown-university |
| Notre Dame | **notre-dame** |
| WashU | washington-university-in-st-louis |
| Emory | emory-university |
| CMU | carnegie-mellon-university |
| Tufts | tufts-university |
| NYU | **nyu** |
| UChicago | **uchicago** |
| UC Berkeley | **uc-berkeley** |
| UCLA | **ucla** |
| UCSD | **ucsd** |

---

## 数据提取技术说明

Clastify 使用 Next.js SSR，每所学校页面的 `__NEXT_DATA__` 包含最多 40 个 Application Package，每个 Package 含 5-8 道 prompt 的完整文书正文。

**提取方式（Python）：**
```python
import requests, json, re

def fetch_school(slug, cookies=None):
    url = f'https://www.clastify.com/supplement/{slug}'
    r = requests.get(url, cookies=cookies, headers={'User-Agent': 'Mozilla/5.0'})
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if not m: return None
    pp = json.loads(m.group(1))['props']['pageProps']
    return pp.get('initialResources'), pp.get('college')
```

⚠️ 需要 Premium 登录 Cookie（httpOnly，需从浏览器会话中获取）

**浏览器内提取方式（JS）：**
```javascript
const r = await fetch(`/supplement/${slug}`, {credentials:'include'});
const html = await r.text();
const m = html.match(/<script id="__NEXT_DATA__"[^>]*>(.*?)<\/script>/s);
const pp = JSON.parse(m[1]).props.pageProps;
// pp.initialResources = 40 packages with full essays
```

---

## 下一步扩充优先级

1. **Stanford**（可用 320 篇，当前 13 篇）— 最大缺口
2. **Princeton**（可用 238 篇，当前 12 篇）
3. **Brown**（可用 180 篇，当前 12 篇）
4. **Penn**（可用 105 篇，当前 10 篇）
5. **Harvard**（可用 122 篇，当前 18 篇）

---

## Skill 文件
- `supplement-essay-collector.skill` — v2.0 文书搜集 skill
- `clastify-essay-extractor.skill` — Clastify 批量提取 skill
