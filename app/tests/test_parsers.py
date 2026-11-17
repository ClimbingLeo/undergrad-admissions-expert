"""解析器单测：每种素材格式一个最小 fixture。"""
from sibo import schools
from sibo.ingest import parsers as P

CA = """<!-- essay_id: 662eb83600ae203db9bb83b3 -->
<!-- source: https://www.clastify.com/common-app-essay-examples/662eb83600ae203db9bb83b3 -->

# A Father's Legacy

## Applicant Profile

| Field | Value |
|-------|-------|
| Application Year | 2022/2023 |
| SAT Total | 1550 |

## Decisions

- ✅ Johns Hopkins University
- ❌ Harvard University

## Essay — Prompt #2

> The lessons we take from obstacles we encounter can be fundamental to later success.

His eyes stared back at me with contentment and the ring caught the light in my bedroom every single day.

That picture has stayed the same for sixteen years and I still look at it when I need courage.

---
"""

SUPP = """# Brown — Supplemental Essays

## 写作要点

Brown 重视开放课程（Open Curriculum），招生官希望看到学生如何主动设计自己的学习路径。这里是一段足够长的写作指南文字，用于测试指南段落会被识别为 guide 而不是样本，因此需要超过八十个字符的长度才行。

## Why Brown (250w) (250 words)

> "Brown students care deeply about their work and the world around them."

## 样本

### 01 ✅ 真实录取
**申请专业：** English  
**申请年份：** 2023/2024  
**学生数据：** 未披露

> One of my chief sources of satisfaction is the writing of letters, well written and well thought out, which I send every week.

**来源：** [Clastify](https://www.clastify.com/supplement/brown-university/68872be475fd7ee6016336be)

---

### 02 ❌ 真实未录取
**申请专业：** 未指定  
**申请年份：** 2024/2025  
**学生数据：** SAT 1500

> I like Brown because it is a great school with an open curriculum and many opportunities for students like me to grow.

**来源：** [Clastify](https://www.clastify.com/supplement/brown-university/6825dca8ac0d03f81425e9ad)
"""

PROFILE = """# 波士顿学院

## 📊 关键录取数据（2024-2025）

录取率约 15%，来源 https://www.bc.edu/admission

## 🏆 课外活动（EC）画像

### Tier 1
- 全国或国际级竞赛获奖、发表学术论文、创办有真实影响力的组织
- 州级以上体育成绩

### 课外活动真实申请者案例分析

**案例1：李明（Tier 1）- 录取**
北京一流国际学校，GPA 3.9。

## ✍️ 真实录取文书解析（至少3篇）

一篇关于家族传统的文书，开头描写奶奶包饺子的场景，结尾回到 BC 的 Jesuit 价值观，没有任何来源链接。
"""

CASES = """## 一、STEM

### 案例 STEM-001 🔍 模拟画像/示例案例

**来源：** goodgoblin.ai 公开 profile 示例（未提供可核验录取链接）

正文一

### 案例 JHU-001 ✅强录取

**来源**
- 类型：官方 Essays That Worked
- URL：https://apply.jhu.edu/hopkins-insider/where-math-collides-with-art/

正文二

## 三、横向对比
不属于案例
"""


def test_common_app_collection():
    es = P.parse_common_app_collection(CA, "x.md")
    assert len(es) == 1
    e = es[0]
    assert e["id"] == "662eb83600ae203db9bb83b3"
    assert e["result"] == "accepted" and e["school_slug"] == "jhu"
    assert e["prompt_key"] == "ca_2" and e["prompt_text"].startswith("The lessons")
    assert "sixteen years" in e["body"] and "---" not in e["body"]
    assert {d["slug"] for d in e["decisions"]} == {"jhu", "harvard"}


def test_common_app_prompt_without_number():
    es = P.parse_common_app_collection(CA.replace("Prompt #2", "Prompt #"), "x.md")
    assert es and es[0]["prompt_key"] == "ca_unknown"


def test_supplement_samples_and_guides():
    es, gs = P.parse_supplement_file(SUPP, "brown", "brown/essays.md")
    assert [e["result"] for e in es] == ["accepted", "rejected"]
    assert es[0]["id"] == "68872be475fd7ee6016336be"
    assert es[0]["prompt_text"].startswith("Brown students care")
    assert es[0]["word_limit"] == 250
    assert es[1]["major"] is None and es[1]["stats"] == "SAT 1500"
    assert any(g["title"] == "写作要点" for g in gs)


def test_profile_flags_fictional_cases():
    secs = P.parse_school_profile(PROFILE, "bc.md")
    by = {s["heading"]: s["trust"] for s in secs}
    assert by["关键录取数据（2024-2025）"] == "verified_source"
    assert by["课外活动（EC）画像"] == "unsourced"
    assert by["课外活动（EC）画像 › 课外活动真实申请者案例分析"] == "composite"
    assert by["真实录取文书解析（至少3篇）"] == "composite"


def test_cases_trust_and_boundaries():
    cs = {c["case_code"]: c for c in P.parse_cases(CASES, "CASES.md")}
    assert cs["STEM-001"]["trust"] == "simulated"
    assert cs["JHU-001"]["trust"] == "official"
    assert "横向对比" not in cs["JHU-001"]["body_md"]


def test_school_resolution():
    assert schools.resolve("Stanford University (Enrolled)") == "stanford"
    assert schools.resolve("University of Kansas **(Enrolled)**") == "university_of_kansas"
    assert schools.resolve_profile_filename("UW_Madison_University_of_Wisconsin_Madison") == "uw_madison"
    assert schools.resolve_profile_filename("UW_University_of_Washington") == "uw"
    assert schools.resolve_profile_filename("HKUST_Hong_Kong_University_of_Science_and_Technology") == "hkust"
    assert schools.resolve_profile_filename("UCL_University_College_London") == "ucl"


def test_major_group():
    assert P.major_group("Computer Science") == "cs"
    assert P.major_group("Economics / Public Policy") == "biz_econ"
    assert P.major_group(None) == "undecided"
