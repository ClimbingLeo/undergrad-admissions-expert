"""各类原始素材的解析器。每个函数只做「文本 → dict」，不碰数据库，便于单测。"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .. import schools

URL_RE = re.compile(r"https?://[^\s)>\]|\"'，。、]+")
HEX24 = re.compile(r"[0-9a-f]{24}")


def urls_in(text: str) -> list[str]:
    seen, out = set(), []
    for u in URL_RE.findall(text):
        u = u.rstrip(".,;:")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9’']+", text))


def stable_id(*parts: str) -> str:
    return hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()[:24]


# ───────────────────────── 专业大类 ─────────────────────────
MAJOR_GROUPS = [
    ("cs", "计算机/数据", r"computer|software|data science|informatics|artificial intel|\bcs\b|计算机|数据科学"),
    ("eng", "工程", r"engineer|robot|aerospace|mechan|electr|工程"),
    ("math_phys", "数理", r"math|physics|statistic|astronom|数学|物理|统计"),
    ("bio_med", "生命科学/医学预科", r"bio|neuro|chem|pre-?med|medic|health|nurs|pharm|生物|化学|医"),
    ("biz_econ", "商科/经济", r"business|econ|financ|account|marketing|management|商|经济|金融"),
    ("social", "社科/政策", r"politic|government|international|psych|sociolog|law|public policy|anthropolog|政治|国际|心理|社会|法"),
    ("humanities", "人文", r"english|history|philosoph|literat|classics|linguist|religio|language|文学|历史|哲学|语言"),
    ("arts", "艺术/设计", r"art|music|film|theat|design|architect|艺术|音乐|设计|建筑|电影"),
    ("env", "环境/可持续", r"environment|sustainab|earth|climate|环境|可持续"),
]
MAJOR_GROUP_LABELS = {k: v for k, v, _ in MAJOR_GROUPS} | {"undecided": "未定/其他"}


def major_group(major: str | None) -> str:
    if not major:
        return "undecided"
    low = major.lower()
    for key, _, pat in MAJOR_GROUPS:
        if re.search(pat, low):
            return key
    return "undecided"


# ───────────────────────── 1. Clastify 申请者画像 jsonl ─────────────────────────
def parse_applicant(d: dict, bucket: str) -> dict:
    s = d.get("scores") or {}
    dec = d.get("decisions") or {}
    decisions = []
    for result in ("accepted", "rejected", "waitlisted"):
        for raw in dec.get(result) or []:
            name, _ = schools.clean_name(raw)
            if not name or name.lower() == "other":
                continue
            decisions.append({"school_name": name, "school_slug": schools.resolve(name), "result": result})
    acts = [
        {"position": a.get("position"), "organization": a.get("organization"), "description": a.get("description")}
        for a in d.get("activities") or []
    ]
    awards = [{"name": a.get("name"), "level": a.get("level")} for a in d.get("awards") or [] if a.get("name") or a.get("level")]
    return {
        "id": d["id"],
        "bucket": bucket,
        "gender": d.get("gender"),
        "ethnicity": d.get("ethnicity"),
        "country": d.get("country"),
        "high_school_type": d.get("highSchoolType"),
        "application_year": d.get("applicationYear"),
        "major": d.get("major"),
        "major_group": major_group(d.get("major")),
        "enrolled_at": d.get("enrolledAt") or dec.get("enrolledAt"),
        "sat_total": s.get("satTotal"),
        "act_composite": s.get("actComposite"),
        "gpa_uw": s.get("gpaUnweighted"),
        "gpa_w": s.get("gpaWeighted"),
        "class_rank": s.get("classRank"),
        "scores_json": json.dumps(s, ensure_ascii=False),
        "source_url": d.get("profileUrl"),
        "decisions": decisions,
        "activities": acts,
        "awards": awards,
        "essay_link_ids": [e.get("id") for e in d.get("essayLinks") or [] if e.get("id")],
    }


def load_applicants(root: Path) -> list[dict]:
    base = root / "clastify/commonapp_applicant_persona/clastify_data"
    out, seen = [], set()
    for bucket in ("core", "borderline", "rejection_cases"):
        f = base / bucket / "profiles.jsonl"
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if d["id"] in seen:
                continue
            seen.add(d["id"])
            out.append(parse_applicant(d, bucket.replace("_cases", "")))
    return out


# ───────────────────────── 2. Common App 合集 md ─────────────────────────
_DEC_LINE = re.compile(r"^-\s*(✅|❌|⏳|🟡|⚠️)\s*(.+?)\s*$", re.M)
_RESULT_BY_EMOJI = {"✅": "accepted", "❌": "rejected", "⏳": "waitlisted", "🟡": "waitlisted", "⚠️": "waitlisted"}


def _profile_table(block: str) -> dict:
    out = {}
    for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", block, re.M):
        k, v = m.group(1), m.group(2)
        if k in ("Field", "-------") or set(k) <= {"-"}:
            continue
        out[k] = v
    return out


def _stats_from_table(t: dict) -> str:
    bits = []
    for k in ("SAT Total", "ACT Composite", "GPA (Unweighted)", "GPA (Weighted)", "Intended Major", "Major"):
        if t.get(k):
            bits.append(f"{k}: {t[k]}")
    return " | ".join(bits)


def parse_common_app_collection(text: str, source_file: str) -> list[dict]:
    chunks = re.split(r"(?=<!-- essay_id: )", text)
    out = []
    for ch in chunks:
        m = re.match(r"<!-- essay_id: ([0-9a-f]+) -->", ch)
        if not m:
            continue
        eid = m.group(1)
        src = re.search(r"<!-- source: (\S+) -->", ch)
        title = re.search(r"^# (.+)$", ch, re.M)
        prof = re.search(r"## Applicant Profile\s*(.+?)(?=^## )", ch, re.S | re.M)
        table = _profile_table(prof.group(1)) if prof else {}
        dec_block = re.search(r"## Decisions\s*(.+?)(?=^## )", ch, re.S | re.M)
        decisions = []
        if dec_block:
            for em, name in _DEC_LINE.findall(dec_block.group(1)):
                name, enrolled = schools.clean_name(name)
                decisions.append({"school": name, "slug": schools.resolve(name), "result": _RESULT_BY_EMOJI.get(em, "unknown"), "enrolled": enrolled})
        em = re.search(r"^## Essay — Prompt #(\d*)\s*$(.*)", ch, re.S | re.M)
        if not em:
            continue
        prompt_no, rest = em.group(1), em.group(2)
        rest = rest.split("\n---", 1)[0] if "\n---\n" in rest else rest
        pm = re.match(r"\s*>\s*(.+?)\n\n", rest, re.S)
        prompt_text = pm.group(1).replace("\n>", " ").strip() if pm else ""
        body = rest[pm.end():] if pm else rest
        body = body.strip().rstrip("-").strip()
        body = "\n".join(ln[1:].lstrip() if ln.startswith(">") else ln for ln in body.splitlines())  # 去掉引用块标记
        accepted = [d for d in decisions if d["result"] == "accepted"]
        out.append({
            "id": eid,
            "kind": "common_app",
            "title": title.group(1).strip() if title else None,
            "school_slug": accepted[0]["slug"] if accepted else (decisions[0]["slug"] if decisions else None),
            "prompt_key": f"ca_{prompt_no}" if prompt_no else "ca_unknown",
            "prompt_text": prompt_text,
            "word_limit": 650,
            "result": "accepted" if accepted else ("rejected" if decisions else "unknown"),
            "year": table.get("Application Year"),
            "major": table.get("Intended Major") or table.get("Major"),
            "stats": _stats_from_table(table),
            "body": body,
            "source_url": src.group(1) if src else f"https://www.clastify.com/common-app-essay-examples/{eid}",
            "decisions": decisions,
            "source_file": source_file,
        })
    return out


def _field(text: str, name: str) -> str | None:
    m = re.search(rf"\*\*{re.escape(name)}[：:]\*\*\s*(.*)", text)
    return m.group(1).strip() if m else None


def parse_common_app_single(text: str, source_file: str) -> dict | None:
    """commonapp_<school>_..._rejected.md：单篇，结果针对「申请目标学校」。"""
    url = _field(text, "Clastify URL")
    eid = HEX24.search(url or "")
    if not eid:
        return None
    title = re.match(r"# Common App — (.+?)(?: \(\d+ words\))?\s*$", text.splitlines()[0])
    target = _field(text, "申请目标学校") or ""
    result_raw = _field(text, "结果") or ""
    result = "rejected" if "reject" in result_raw.lower() or "❌" in result_raw else ("accepted" if "✅" in result_raw else "unknown")
    decisions = [{"school": schools.clean_name(target)[0], "slug": schools.resolve(target), "result": result, "enrolled": False}]
    other = re.search(r"\*\*其他学校结果[^*]*\*\*(.+?)(?=\n\*\*结果)", text, re.S)
    if other:
        for name, res in re.findall(r"[✅❌]\s*(.+?)\s*\((admitted|rejected|waitlisted)\)", other.group(1)):
            decisions.append({"school": name, "slug": schools.resolve(name), "result": "accepted" if res == "admitted" else res, "enrolled": False})
    prompt = _field(text, "Common App Prompt") or ""
    pn = re.match(r"#(\d+)\s*\"?(.*?)\"?$", prompt)
    body_m = re.search(r"## Essay Body\s*(.+)", text, re.S)
    body = ""
    if body_m:
        lines = [ln[1:].strip() if ln.startswith(">") else ln for ln in body_m.group(1).splitlines()]
        # 合并 PDF 硬换行：空行分隔的碎行先拼接，真正的段落以句末标点结束
        paras, cur = [], ""
        for ln in lines:
            if not ln.strip():
                continue
            cur = f"{cur} {ln.strip()}".strip()
            if re.search(r"[.!?\"”’)]$", cur):
                paras.append(cur)
                cur = ""
        if cur:
            paras.append(cur)
        body = "\n\n".join(paras)
    stats = _field(text, "学生数据") or ""
    major = re.search(r"Intended Major:\s*([^|]+)", stats)
    return {
        "id": eid.group(0),
        "kind": "common_app",
        "title": title.group(1).strip() if title else None,
        "school_slug": decisions[0]["slug"],
        "prompt_key": f"ca_{pn.group(1)}" if pn else None,
        "prompt_text": pn.group(2).strip() if pn else prompt,
        "word_limit": 650,
        "result": result,
        "year": _field(text, "申请年份"),
        "major": major.group(1).strip() if major else None,
        "stats": stats,
        "body": body,
        "source_url": url,
        "decisions": decisions,
        "source_file": source_file,
    }


# ───────────────────────── 3. 补充文书 ─────────────────────────
_SAMPLE_HDR = re.compile(r"^### (\d+)\s*(✅|❌)\s*(.*)$", re.M)
_NON_PROMPT_HEADINGS = ("样本", "写作要点", "文书特点", "分析总结", "核心", "总结", "规律", "失败", "成功", "对比", "建议", "数据")


def _clean_quote(block: str) -> str:
    lines = []
    for ln in block.splitlines():
        if ln.startswith(">"):
            lines.append(ln[1:].lstrip() if len(ln) > 1 else "")
        elif not ln.strip():
            lines.append("")
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def parse_supplement_file(text: str, school_slug: str, source_file: str, prompt_hint: str | None = None) -> tuple[list[dict], list[dict]]:
    """返回 (essays, guide_sections)。

    `## ` 标题若下面直接跟样本（### NN ✅/❌），视为 prompt；否则视为写作指南段落。
    """
    essays, guides = [], []
    sections = re.split(r"(?=^## )", text, flags=re.M)
    current_prompt, current_prompt_text, current_limit = prompt_hint, None, None
    for sec in sections:
        hm = re.match(r"## (.+)", sec)
        heading = hm.group(1).strip() if hm else ""
        has_samples = bool(_SAMPLE_HDR.search(sec))
        is_prompt_heading = heading and not heading.startswith(_NON_PROMPT_HEADINGS) and (
            has_samples or re.search(r"\(\d+\s*(words|字)\)", heading) or heading.lower().startswith("prompt")
        )
        if is_prompt_heading:
            current_prompt = heading
            q = re.search(r"^>\s*\"?(.+?)\"?\s*$", sec, re.M)
            current_prompt_text = q.group(1).strip().strip('"') if q else heading
            lm = re.search(r"\((\d+)\s*(?:words|字)", heading)
            current_limit = int(lm.group(1)) if lm else None
        if not has_samples:
            if heading and not sec.startswith("# ") and len(sec.strip()) > 80:
                guides.append({"school_slug": school_slug, "title": heading, "body_md": sec.strip(), "source_file": source_file})
            continue
        samples = list(_SAMPLE_HDR.finditer(sec))
        for i, m in enumerate(samples):
            end = samples[i + 1].start() if i + 1 < len(samples) else len(sec)
            block = sec[m.end():end]
            url_m = re.search(r"\*\*来源：\*\*\s*\[[^\]]*\]\((\S+?)\)", block)
            url = url_m.group(1) if url_m else None
            idm = HEX24.search(url or "")
            body = _clean_quote(block.split("**来源", 1)[0])
            # 去掉样本里重复引用的 prompt 原文（若第一段与 prompt 相同）
            if current_prompt_text and body.startswith(current_prompt_text[:60]):
                body = body.split("\n", 1)[1].strip() if "\n" in body else body
            if not body or word_count(body) < 15:
                continue
            stats = (re.search(r"\*\*学生数据：\*\*\s*(.+)", block) or [None, None])[1]
            essays.append({
                "id": idm.group(0) if idm else stable_id(school_slug, current_prompt or "", body[:200]),
                "kind": "supplement",
                "title": None,
                "school_slug": school_slug,
                "prompt_key": current_prompt,
                "prompt_text": current_prompt_text,
                "word_limit": current_limit,
                "result": "accepted" if m.group(2) == "✅" else "rejected",
                "year": (re.search(r"\*\*申请年份：\*\*\s*(\S+)", block) or [None, None])[1],
                "major": ((re.search(r"\*\*申请专业：\*\*\s*(.+?)\s*$", block, re.M) or [None, None])[1] or "").replace("未指定", "").strip() or None,
                "stats": None if stats in (None, "未披露") else stats.strip(),
                "body": body,
                "source_url": url,
                "decisions": [],
                "source_file": source_file,
            })
    return essays, guides


# ───────────────────────── 4. 学校档案 ─────────────────────────
COMPOSITE_HEADING = re.compile(r"真实.*(案例|申请者|文书)|典型.*案例|案例分析|文书解析|录取案例")
COMPOSITE_BODY = re.compile(r"代表性|综合整理|虚构|化名|模拟|示例画像|典型画像|假设(?:的|案例|人物|学生|画像|情境)")
SECTION_TYPES = [
    ("values", r"看重的特质"),  # 学校官方表述的特质偏好（2026-11 盲测验证区分度）
    ("data", r"录取数据|关键数据|申请情况|录取率|统计"),
    ("academic", r"学术|硬件|成绩|A-Level|IB要求|标化|GPA"),
    ("ec", r"课外|活动|EC"),
    ("hooks", r"Hook|加分|优势"),
    ("essay", r"文书|个人陈述|Personal Statement|Essay"),
    ("process", r"流程|时间线|截止|材料|面试|要求"),
    ("insight", r"规律|总结|启示|建议|差距"),
    ("cases", r"案例"),
]


def classify_section(heading: str) -> str:
    for t, pat in SECTION_TYPES:
        if re.search(pat, heading, re.I):
            return t
    return "other"


CASE_SUB = re.compile(r"案例|真实申请者|申请者画像|学生画像")
FICTIONAL_NAME = re.compile(
    r"代称|化名|[王李张陈刘赵周吴][A-Z]{2}\b|[王李张陈刘赵周吴]同学|李明|王思语|王思宇|张浩东|张欣雨|周晓月|李浩然"
)


SUMMARY_HEADING = re.compile(r"总结|要点|建议|规律|启示")


def _trust_for(heading: str, body: str, stype: str) -> str:
    urls = urls_in(body)
    # 学校档案里的「案例」经抽查均为综合/虚构画像（链接指向统计页而非案例出处），一律降级
    if stype == "cases" or COMPOSITE_HEADING.search(heading):
        return "composite"
    if FICTIONAL_NAME.search(body) and not urls:
        return "composite"
    if (COMPOSITE_HEADING.search(heading) or stype == "cases") and not urls:
        return "composite"
    if COMPOSITE_BODY.search(body[:600]) and not urls:
        return "composite"
    if FICTIONAL_NAME.search(body):  # 有链接但含化名人物：链接多半是数据来源而非案例出处
        return "composite"
    if SUMMARY_HEADING.search(heading):  # 总结 / 建议类是整理者的观点，带链接也只是泛泛的数据来源，不算已溯源
        return "unsourced"
    return "verified_source" if urls else "unsourced"


def parse_school_profile(text: str, source_file: str) -> list[dict]:
    """按 `## ` 切 section；其中「案例类」`###` 子节单独拆出并独立判定 trust。

    这样「EC 画像」正文保留，而夹在里面的化名案例会被标成 composite（示例画像），
    且不会进入 AI 检索上下文。
    """
    out = []
    ord_ = 0

    def add(heading, body, stype):
        nonlocal ord_
        if len(body.strip()) < 30:
            return
        ord_ += 1
        out.append({"ord": ord_, "heading": heading, "body_md": body.strip(), "section_type": stype,
                    "trust": _trust_for(heading, body, stype), "source_urls": urls_in(body),
                    "source_file": source_file})

    for p in re.split(r"(?=^## )", text, flags=re.M):
        hm = re.match(r"## (.+)", p)
        if not hm:
            continue
        heading = re.sub(r"^[^\w\u4e00-\u9fff]+", "", hm.group(1)).strip()
        body = p[hm.end():]
        stype = classify_section(heading)
        subs = re.split(r"(?=^### )", body, flags=re.M)
        keep, case_subs = [subs[0]], []
        for sub in subs[1:]:
            sh = re.match(r"### (.+)", sub).group(1).strip().strip("*")
            if CASE_SUB.search(sh) and stype not in ("cases",):
                case_subs.append((sh, sub[sub.index("\n") + 1:] if "\n" in sub else ""))
            else:
                keep.append(sub)
        add(heading, "".join(keep), stype)
        for sh, sb in case_subs:
            add(f"{heading} › {sh}", sb, "cases")
    return out


def split_combined_profiles(text: str) -> list[tuple[str, str]]:
    """合集文件按 `# ` 拆成 [(英文校名, 正文)]。"""
    parts = re.split(r"(?=^# )", text, flags=re.M)
    out = []
    for p in parts:
        m = re.match(r"# ([A-Za-z][A-Za-z .,&'-]+?)\s+[一-鿿]", p)
        if m:
            out.append((m.group(1).strip(), p))
    return out


# ───────────────────────── 5. 叙事案例库 CASES*.md ─────────────────────────
_CASE_HDR = re.compile(r"^### 案例 ([A-Z]+-\d+)\s*(.*)$", re.M)


def _case_trust(source_block: str, header: str) -> tuple[str, str | None]:
    urls = urls_in(source_block)
    s = source_block + header
    if "模拟" in s or "示例案例" in s:
        return "simulated", urls[0] if urls else None
    if re.search(r"Brand Studio|赞助|sponsored", s, re.I):
        return "sponsored", urls[0] if urls else None
    if re.search(r"官方|Essays That Worked|apply\.jhu\.edu|admissions\.", s, re.I) and urls:
        return "official", urls[0]
    if urls:
        return "verified_source", urls[0]
    return "unsourced", None


def _outcome(header: str) -> str:
    if "模拟" in header:
        return "simulated"
    if "⚠" in header:
        return "surprise_reject"
    if "❌" in header:
        return "typical_fail"
    if "🔍" in header:
        return "borderline"
    return "strong_admit"


def parse_cases(text: str, source_file: str) -> list[dict]:
    out = []
    hits = list(_CASE_HDR.finditer(text))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        body = text[m.end():end]
        # 截断到下一个 `## ` 大节（横向对比/索引等不属于该案例）
        nxt = re.search(r"^## ", body, re.M)
        if nxt:
            body = body[:nxt.start()]
        body = body.strip().rstrip("-").strip()
        code, header = m.group(1), m.group(2).strip()
        src = re.search(r"\*\*来源[：:]?\*\*[：:]?(.+?)(?=\n\*\*|\Z)", body, re.S)
        src_text = src.group(1) if src else ""
        trust, url = _case_trust(src_text, header)
        stype = re.search(r"类型[：:]\s*(.+)", src_text)
        out.append({
            "case_code": code,
            "title": f"{code} {header}".strip(),
            "outcome": _outcome(header),
            "category": code.split("-")[0],
            "body_md": body,
            "source_type": stype.group(1).strip() if stype else (src_text.strip()[:80] or None),
            "source_url": url,
            "trust": trust,
            "source_file": source_file,
        })
    return out


# ───────────────────────── 6. IB Maths EE ─────────────────────────
def parse_ee_file(text: str, grade: str) -> list[dict]:
    out = []
    for ch in re.split(r"(?=<!-- ee_id: )", text):
        m = re.match(r"<!-- ee_id: ([0-9a-f]+) -->", ch)
        if not m:
            continue
        title = re.search(r"^# (.+)$", ch, re.M)
        sess = re.search(r"\*\*Session:\*\*\s*(\S+)", ch)
        pages = re.search(r"\*\*Total Pages:\*\*\s*(\d+)", ch)
        url = re.search(r"\*\*URL:\*\*\s*(\S+)", ch)
        body = re.split(r"^## ", ch, maxsplit=1, flags=re.M)
        excerpt = ("## " + body[1]).strip() if len(body) > 1 else ""
        excerpt = re.sub(r"\n{3,}", "\n\n", excerpt)
        out.append({
            "id": m.group(1),
            "grade": grade,
            "title": title.group(1).strip() if title else None,
            "session": sess.group(1) if sess else None,
            "total_pages": int(pages.group(1)) if pages else None,
            "excerpt": excerpt,
            "url": url.group(1) if url else None,
        })
    return out
