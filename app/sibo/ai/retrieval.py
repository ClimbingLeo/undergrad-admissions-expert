"""为各类 AI 报告挑选检索上下文。全部用 SQL + FTS5，不用向量库。

每条注入上下文都带引用 ID：
  [A:<applicant_id>]  Clastify 申请者画像
  [E:<essay_id>]      文书
  [C:<case_code>]     叙事案例
  [S:<school_slug>#<ord>]  学校档案段落
模型只能引用这些 ID；生成后由 citations.py 校验。
"""
from __future__ import annotations

import json
import re
import sqlite3

from ..ingest.parsers import major_group

EXCLUDED_TRUST = ("composite", "simulated")
TRUST_LABEL = {
    "verified_source": "已溯源",
    "official": "官方来源",
    "sponsored": "赞助内容（非官方）",
    "unsourced": "数据待核实",
    "composite": "示例画像（非真实案例）",
    "simulated": "模拟画像",
}


def _parse_sat(tests: str | None) -> int | None:
    if not tests:
        return None
    m = re.search(r"SAT\D{0,6}(1[0-6]\d\d)", tests, re.I)
    return int(m.group(1)) if m else None


def _parse_gpa(gpa: str | None) -> float | None:
    if not gpa:
        return None
    m = re.search(r"([0-4]\.\d{1,2})", gpa)
    return float(m.group(1)) if m else None


def student_targets(student) -> list[str]:
    try:
        return json.loads(student["target_schools"] or "[]")
    except json.JSONDecodeError:
        return []


def is_international(student) -> bool:
    bg = f"{student['background'] or ''} {student['school'] or ''} {student['curriculum'] or ''}"
    return not re.search(r"美国本土|US citizen|美国公民|domestic", bg, re.I)


# ───────────────────────── 申请者画像 ─────────────────────────
def similar_applicants(conn: sqlite3.Connection, student, k: int = 8) -> list[sqlite3.Row]:
    mg = student["major_group"] or major_group(student["intended_major"])
    sat = _parse_sat(student["tests"])
    gpa = _parse_gpa(student["gpa"])
    targets = student_targets(student)
    intl = is_international(student)
    rows = conn.execute("SELECT * FROM applicants").fetchall()
    dec = {}
    for r in conn.execute("SELECT applicant_id, school_slug, result FROM applicant_decisions"):
        dec.setdefault(r["applicant_id"], []).append((r["school_slug"], r["result"]))

    scored = []
    for a in rows:
        s = 0.0
        if a["major_group"] == mg:
            s += 3
        if sat and a["sat_total"]:
            s += max(0.0, 2 - abs(a["sat_total"] - sat) / 40)
        if gpa and a["gpa_uw"]:
            s += max(0.0, 1.5 - abs(a["gpa_uw"] - gpa) * 5)
        if intl and a["country"] and a["country"] != "United States":
            s += 1.5
        hit = [r for slug, r in dec.get(a["id"], []) if slug in targets]
        s += min(3, 1.5 * len(hit))
        scored.append((s, a, hit))
    scored.sort(key=lambda x: -x[0])

    # 尽量让「目标校被拒」样本占一席之地，避免只看成功者
    picked, rejected_hits = [], []
    for s, a, hit in scored:
        if "rejected" in hit and len(rejected_hits) < k // 3:
            rejected_hits.append(a)
    for s, a, hit in scored:
        if len(picked) + len(rejected_hits) >= k:
            break
        if a not in rejected_hits:
            picked.append(a)
    return picked + rejected_hits


def applicant_brief(conn: sqlite3.Connection, a, max_acts: int = 6, targets=()) -> str:
    acts = conn.execute(
        "SELECT position, organization, description FROM applicant_activities WHERE applicant_id=? ORDER BY ord LIMIT ?",
        (a["id"], max_acts)).fetchall()
    awards = conn.execute("SELECT name, level FROM applicant_awards WHERE applicant_id=? LIMIT 4", (a["id"],)).fetchall()
    decs = conn.execute(
        "SELECT school_slug, school_name, result FROM applicant_decisions WHERE applicant_id=? ORDER BY result", (a["id"],)).fetchall()
    tset = set(targets or ())

    def names(result: str, cap: int) -> list[str]:
        # 学生目标校的结果永远全列、排在前面（标 ★），其余最多 cap 所，剩下的写明数量——不能静默截断，否则会藏掉反证
        rows = [d for d in decs if d["result"] == result]
        hit = [f"★{d['school_name']}" for d in rows if d["school_slug"] in tset]
        rest = [d["school_name"] for d in rows if d["school_slug"] not in tset]
        out = hit + rest[:cap]
        if len(rest) > cap:
            out.append(f"另有 {len(rest) - cap} 所未列出")
        return out

    acc, rej, wl = names("accepted", 10), names("rejected", 10), names("waitlisted", 4)
    score = []
    if a["sat_total"]:
        score.append(f"SAT {a['sat_total']}")
    if a["act_composite"]:
        score.append(f"ACT {a['act_composite']}")
    if a["gpa_uw"]:
        score.append(f"UW GPA {a['gpa_uw']}")
    lines = [
        f"[A:{a['id']}] {a['country'] or '国家未知'} | {a['high_school_type'] or ''} | 专业 {a['major'] or '未填'} | "
        f"{', '.join(score) or '无标化'} | 申请季 {a['application_year'] or '?'}",
        "  活动：" + "；".join(
            f"{x['position'] or ''}@{x['organization'] or ''}（{(x['description'] or '')[:80]}）" for x in acts),
    ]
    if awards:
        lines.append("  奖项：" + "；".join(
            f"{w['name']}（{w['level']}级）" if w["name"] and w["level"] else (w["name"] or f"{w['level']}级奖项（名称未披露）")
            for w in awards))
    lines.append(f"  录取：{', '.join(acc) or '—'}")
    lines.append(f"  拒绝：{', '.join(rej) or '—'}" + (f" | 候补：{', '.join(wl)}" if wl else ""))
    if tset:
        lines.append("  （★ = 本学生的目标校）")
    return "\n".join(lines)


def aggregated_activities(conn: sqlite3.Connection, mg: str, limit: int = 40) -> str:
    rows = conn.execute(
        """SELECT a.id, act.position, act.organization, act.description
           FROM applicant_activities act JOIN applicants a ON a.id = act.applicant_id
           WHERE a.major_group = ? AND a.n_accepted > 0 ORDER BY act.ord LIMIT ?""", (mg, limit * 2)).fetchall()
    seen, out = set(), []
    for r in rows:
        key = (r["organization"] or "").lower()[:30]
        if key in seen:
            continue
        seen.add(key)
        out.append(f"- [A:{r['id']}] {r['position'] or ''} @ {r['organization'] or ''}：{(r['description'] or '')[:120]}")
        if len(out) >= limit:
            break
    return "\n".join(out)


# ───────────────────────── 学校档案 ─────────────────────────
def school_name(conn: sqlite3.Connection, slug: str) -> str:
    r = conn.execute("SELECT name_en, name_zh FROM schools WHERE slug=?", (slug,)).fetchone()
    if not r:
        return slug
    return f"{r['name_zh']}（{r['name_en']}）" if r["name_zh"] else r["name_en"]


def school_sections(conn: sqlite3.Connection, slug: str, types=("data", "academic", "ec", "hooks"),
                    max_chars: int = 2200) -> str:
    q = ",".join("?" * len(types))
    rows = conn.execute(
        f"""SELECT ord, heading, body_md, trust FROM school_profile_sections
            WHERE school_slug=? AND section_type IN ({q}) AND trust NOT IN ('composite','simulated') ORDER BY ord""",
        (slug, *types)).fetchall()
    out = []
    for r in rows:
        body = r["body_md"]
        if len(body) > max_chars:
            body = body[:max_chars] + "\n…（节选）"
        out.append(f"[S:{slug}#{r['ord']}] 【{r['heading']}】（可信度：{TRUST_LABEL[r['trust']]}）\n{body}")
    return "\n\n".join(out)


def supp_guides(conn: sqlite3.Connection, slug: str, max_chars: int = 5000) -> str:
    rows = conn.execute("SELECT title, body_md FROM supp_guides WHERE school_slug=?", (slug,)).fetchall()
    text = "\n\n".join(f"【{r['title']}】\n{r['body_md']}" for r in rows)
    return text[:max_chars]


# ───────────────────────── 叙事案例 ─────────────────────────
def narrative_cases(conn: sqlite3.Connection, keywords: list[str], k: int = 3, max_chars: int = 1600) -> list[sqlite3.Row]:
    terms = [t for t in keywords if t and len(t) >= 3][:6]
    rows = []
    if terms:
        q = " OR ".join('"' + t.replace('"', "") + '"' for t in terms)
        try:
            rows = conn.execute(
                f"""SELECT n.* FROM cases_fts f JOIN narrative_cases n ON n.case_code=f.case_code
                    WHERE cases_fts MATCH ? AND n.trust NOT IN ('composite','simulated') ORDER BY rank LIMIT ?""",
                (q, k)).fetchall()
        except sqlite3.OperationalError:
            rows = []
    if len(rows) < k:
        have = {r["case_code"] for r in rows}
        extra = conn.execute(
            "SELECT * FROM narrative_cases WHERE trust IN ('official','verified_source') ORDER BY random() LIMIT ?",
            (k * 2,)).fetchall()
        rows += [r for r in extra if r["case_code"] not in have][: k - len(rows)]
    return rows


def case_brief(c, max_chars: int = 1600) -> str:
    body = c["body_md"]
    if len(body) > max_chars:
        body = body[:max_chars] + "\n…（节选）"
    return f"[C:{c['case_code']}] {c['title']}（来源可信度：{TRUST_LABEL.get(c['trust'], c['trust'])}）\n{body}"


# ───────────────────────── 文书 ─────────────────────────
def school_prompts(conn: sqlite3.Connection, slug: str) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT prompt_text, MAX(word_limit) AS word_limit, COUNT(*) AS n,
                  SUM(result='accepted') AS n_acc, SUM(result='rejected') AS n_rej
           FROM essays WHERE kind='supplement' AND school_slug=? AND prompt_text IS NOT NULL
           GROUP BY prompt_text ORDER BY n DESC""", (slug,)).fetchall()


def essay_samples(conn: sqlite3.Connection, slug: str | None, prompt_text: str | None, major: str | None,
                  n_acc: int = 4, n_rej: int = 2, kind: str = "supplement") -> list[sqlite3.Row]:
    out = []
    for result, n in (("accepted", n_acc), ("rejected", n_rej)):
        params: list = [kind, result]
        where = "kind=? AND result=?"
        if slug:
            where += " AND school_slug=?"
            params.append(slug)
        rows = []
        if prompt_text:
            rows = conn.execute(f"SELECT * FROM essays WHERE {where} AND prompt_text=? ORDER BY (major LIKE ?) DESC, random() LIMIT ?",
                                (*params, prompt_text, f"%{(major or '').split(' ')[0]}%", n)).fetchall()
        if len(rows) < n:
            have = {r["id"] for r in rows}
            more = conn.execute(f"SELECT * FROM essays WHERE {where} ORDER BY random() LIMIT ?", (*params, n * 3)).fetchall()
            rows += [r for r in more if r["id"] not in have][: n - len(rows)]
        out += rows
    return out


def essay_brief(e, max_words: int = 700) -> str:
    words = e["body"].split()
    body = " ".join(words[:max_words]) + (" …（节选）" if len(words) > max_words else "")
    res = {"accepted": "录取", "rejected": "未录取"}.get(e["result"], "结果未知")
    meta = " | ".join(x for x in (e["major"], e["year"], e["stats"]) if x)
    return f"[E:{e['id']}] 结果：{res} | {meta}\nPrompt：{e['prompt_text'] or '—'}\n正文：\n{body}"


def search_essays(conn: sqlite3.Connection, q: str, limit: int = 50) -> list[str]:
    """空格分隔的多个词按"都要出现"匹配。≥3 个字的词走 FTS5 trigram 索引；1–2 个字的词（如"钢琴""AI"）
    trigram 查不到，改在 Python 里过滤：英文按整词匹配（"AI" 不会命中 "said"），中文按子串匹配。"""
    terms = [t.replace('"', "") for t in q.split() if t.strip()][:6]
    if not terms:
        return []
    long_t, short_t = [t for t in terms if len(t) >= 3], [t for t in terms if len(t) < 3]
    try:
        if long_t:
            rows = conn.execute(
                "SELECT e.id, e.title, e.prompt_text, e.body FROM essays_fts f JOIN essays e ON e.id = f.id "
                "WHERE essays_fts MATCH ? ORDER BY rank", (" AND ".join(f'"{t}"' for t in long_t),)).fetchall()
        else:
            rows = conn.execute("SELECT id, title, prompt_text, body FROM essays ORDER BY id").fetchall()
    except sqlite3.OperationalError:
        return []
    pats = [re.compile(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", re.I) if t.isascii() else re.compile(re.escape(t))
            for t in short_t]
    out = []
    for r in rows:
        text = f"{r['title'] or ''}\n{r['prompt_text'] or ''}\n{r['body'] or ''}"
        if all(p.search(text) for p in pats):
            out.append(r["id"])
            if len(out) >= limit:
                break
    return out


# ───────────────────────── IB EE ─────────────────────────
def ee_samples_for(conn: sqlite3.Connection, draft: str, max_chars: int = 2500) -> list[sqlite3.Row]:
    words = {w.lower() for w in re.findall(r"[A-Za-z]{5,}", draft)}

    def overlap(r):
        t = f"{r['title'] or ''} {r['excerpt'][:1500]}".lower()
        return sum(1 for w in words if w in t)

    rows = conn.execute("SELECT * FROM ee_samples").fetchall()
    a = sorted([r for r in rows if r["grade"] == "A"], key=overlap, reverse=True)[:2]
    c = sorted([r for r in rows if r["grade"] == "C"], key=overlap, reverse=True)[:1]
    return a + c


def ee_brief(r, max_chars: int = 2500) -> str:
    ex = r["excerpt"][:max_chars]
    return f"[EE:{r['id']}] 等级 {r['grade']} | {r['session'] or ''} | {r['title']}\n优势维度：{r['strong_aspects'] or '—'}\n节选：\n{ex}"
