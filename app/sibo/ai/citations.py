"""引用校验：只保留注入上下文里真实存在的 ID，渲染成站内链接；并检测违规表述。"""
from __future__ import annotations

import re

CITE_RE = re.compile(r"\[(A|E|C|S|EE):([A-Za-z0-9_\-#]+)\]")
_ID = r"(?:A|E|C|S|EE)\s*[:：]\s*[A-Za-z0-9_\-#]+"
# 一个括号里放多个 ID：[A:x, A:y] / 【A:x；E:y】 / (A:x、A:y)
_GROUP = re.compile(r"[\[【(（]\s*(" + _ID + r"(?:\s*[,，;；、]\s*" + _ID + r")*)\s*[\]】)）]")
# 没有括号的裸 ID：只认形态明确的（24 位十六进制 / 案例编号 / 学校段落）
_BARE = re.compile(r"(?<![A-Za-z0-9\[·/])((?:A|E|EE)[:：][0-9a-f]{8,}|C[:：][A-Z]{2,}-\d{2,}|S[:：][a-z_]+#\d+)")
PROB_RE = re.compile(
    r"(录取|命中|上岸|成功)(概率|几率|胜率|把握|机会|可能性)[^。\n]{0,12}(\d{1,3}\s*%|[一二三四五六七八九]成)"
    r"|(概率|几率)[^。\n]{0,12}\d{1,3}\s*%"
    r"|\d{1,3}\s*%\s*的?(录取)?(概率|几率|把握)"
    r"|[一二三四五六七八九十]成(的)?把握"
    r"|稳录|必录|包录|保录|稳上|十拿九稳"
    r"|百分之[一二三四五六七八九十百]+"
    r"|(录取|上岸)(概率|几率|可能性)(较|很|极|非常|相当)?(高|大|低|小)")


def normalize(text: str) -> str:
    """把模型常见的变体写法统一成 [K:id]，好让后面的校验覆盖到它们。"""
    def group(m):
        ids = re.split(r"\s*[,，;；、]\s*", m.group(1))
        return "".join("[" + re.sub(r"\s*[:：]\s*", ":", i.strip()) + "]" for i in ids)
    text = _GROUP.sub(group, text)
    return _BARE.sub(lambda m: "[" + m.group(1).replace("：", ":") + "]", text)


def allowed_ids_from_context(context: str) -> set[str]:
    return {f"{k}:{v}" for k, v in CITE_RE.findall(context)}


def link_for(kind: str, ident: str) -> str:
    if kind == "A":
        return f"/library/applicants/{ident}"
    if kind == "E":
        return f"/library/essays/{ident}"
    if kind == "C":
        return f"/library/cases/{ident}"
    if kind == "S":
        slug, _, ord_ = ident.partition("#")
        return f"/library/schools/{slug}#sec-{ord_}"
    if kind == "EE":
        return f"/ee/samples/{ident}"
    return "#"


def _expand_prefix(kind: str, ident: str, allowed: set[str]) -> str | None:
    """模型有时把 24 位编号缩写成前 6–12 位：只有当它唯一对应本次材料里的某个编号时才补全。"""
    if kind not in ("A", "E", "EE") or not re.fullmatch(r"[0-9a-f]{6,23}", ident):
        return None
    hits = [k for k in allowed if k.startswith(f"{kind}:{ident}")]
    return hits[0] if len(hits) == 1 else None


def validate(text: str, allowed: set[str]) -> tuple[str, list[dict], list[str]]:
    """返回 (处理后的 markdown, citations 列表, 警告)。无效 ID 删除并计数。

    注意：这里只核验「ID 是否来自本次注入的材料」，不核验论断与材料是否相符。"""
    cites: dict[str, dict] = {}
    invalid: list[str] = []

    def repl(m):
        key = f"{m.group(1)}:{m.group(2)}"
        if key not in allowed:
            key = _expand_prefix(m.group(1), m.group(2), allowed) or key
        if key not in allowed:
            invalid.append(key)
            return ""
        kind, ident = key.split(":", 1)
        cites.setdefault(key, {"id": key, "kind": kind, "ref": ident, "url": link_for(kind, ident)})
        short = ident[:6] if kind in ("A", "E", "EE") else ident
        return f"[{kind}·{short}]({link_for(kind, ident)})"

    out = CITE_RE.sub(repl, normalize(text))
    warnings = []
    if invalid:
        warnings.append(f"已移除 {len(invalid)} 处无法核验的引用（{', '.join(sorted(set(invalid))[:5])}…）。")
    if PROB_RE.search(out):
        warnings.append("检测到疑似「录取概率」表述，对外交付前请人工删改。")
    return out, list(cites.values()), warnings


# ───────────── 论断—出处的机械核对（只报警，不删改） ─────────────
_QUOTE_RE = re.compile(r"[“\"]([^“”\"\n]{12,400})[”\"]")
_SAT_RE = re.compile(r"SAT\s*(?:总分\s*)?(1[0-6]\d0)")
_GPA_RE = re.compile(r"GPA\s*(?:为\s*)?([0-4]\.\d{1,3})")


def _norm_words(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'").replace("—", " ").replace("–", " ")
    return " ".join(re.findall(r"[a-z0-9']+", s))


def _units(text: str):
    """按行切分；段落行再按句号切，保证"一句话里只有一个出处"时的对应关系可靠。"""
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            yield line
        else:
            yield from (u for u in re.split(r"(?<=[。；!?！？])", line) if u.strip())


# 录取 / 拒绝结论核对用：校名的常见缩写和中文名（只用于在句子里认出申请者自己申请过的学校）
_SCHOOL_ABBR = {
    "gatech": ["GT", "Georgia Tech", "佐治亚理工"], "uiuc": ["UIUC", "伊利诺伊"], "umich": ["Michigan", "UMich", "密歇根"],
    "uc_berkeley": ["Berkeley", "UCB", "伯克利"], "ucla": ["UCLA"], "cmu": ["CMU", "Carnegie Mellon", "卡梅"],
    "mit": ["MIT", "麻省理工"], "stanford": ["Stanford", "斯坦福"], "penn": ["Penn", "UPenn", "宾大"],
    "jhu": ["JHU", "Johns Hopkins", "约翰霍普金斯"], "nyu": ["NYU"], "bu": ["BU", "Boston University"],
    "usc": ["USC"], "uva": ["UVA"], "umd": ["UMD"], "unc": ["UNC"], "caltech": ["Caltech", "加州理工"],
    "uchicago": ["UChicago", "芝大", "芝加哥大学"], "washu": ["WashU", "WUSTL"], "uw": ["UW", "University of Washington"],
}
_NOT_DECISION = r"(?!率|生|者|人数|标准|门槛|线|名单|结果|情况|难度|偏好)"
_DECISION_VERB = re.compile(r"(未被|没有被|没被)?(录取" + _NOT_DECISION + r"|拒绝|被拒|拒|录(?![取用]))")


def _school_names(slug: str, name: str) -> list[str]:
    out = {name, slug}
    uc = re.match(r"University of California,?\s+(.+)$", name)
    if uc:  # UC 各分校：UC San Diego / UCSD；不能缩成 "California"
        campus = uc.group(1).strip()
        out.update([f"UC {campus}", "UC" + "".join(w[0] for w in campus.split()).upper()])
    else:
        out.add(re.sub(r"^(The )?University of |^(The )?University at | University$| College$|,.*$| - .*$| at .*$", "", name))
    out.update(_SCHOOL_ABBR.get(slug, []))
    try:
        from ..schools import CANON
        for s_, en, zh, _r, al in CANON:
            if s_ == slug:
                out.update([en, zh])
    except Exception:  # noqa: BLE001
        pass
    return sorted({n for n in out if n and len(n) >= 2}, key=len, reverse=True)


def _named_schools(seg: str, names: dict[str, list[str]]) -> set[str]:
    hits, taken = set(), []
    for slug, ns in names.items():
        for n in ns:
            pat = re.escape(n)
            if n.isascii():
                pat = rf"(?<![A-Za-z]){pat}(?![A-Za-z])"
            for m in re.finditer(pat, seg):
                if any(a < m.end() and m.start() < b for a, b in taken):
                    continue
                taken.append((m.start(), m.end()))
                hits.add(slug)
    return hits


def _decision_claims(unit: str):
    """从一句话里抽出 (结论, 片段)：录取 X、Y；拒 Z / 被 X 录取 / 被 X 拒。"""
    for m in re.finditer(r"(未被|没有被|没被|被)([^，。；|！？]{1,60}?)(录取|拒绝|拒)(?!率|生|者|人数|标准|门槛|线|名单)", unit):
        neg, seg, verb = m.group(1), m.group(2), m.group(3)
        yield ("rejected" if neg != "被" or verb.startswith("拒") else "accepted"), seg
    for m in _DECISION_VERB.finditer(unit):
        if m.group(1):
            continue
        tail = unit[m.end():]
        seg = re.split(r"[；;。|（(]|(?:录取|拒绝|被拒|拒|录|候补)[：:]", tail, maxsplit=1)[0]
        yield ("rejected" if "拒" in m.group(2) else "accepted"), seg[:200]


def decision_mismatches(unit: str, a_id: str, conn) -> list[str]:
    decs = conn.execute("SELECT school_slug, school_name, result FROM applicant_decisions WHERE applicant_id=?",
                        (a_id,)).fetchall()
    if not decs:
        return []
    res: dict[str, set] = {}
    names: dict[str, list[str]] = {}
    for d in decs:
        res.setdefault(d["school_slug"], set()).add(d["result"])
        names.setdefault(d["school_slug"], _school_names(d["school_slug"], d["school_name"]))
    clean = CITE_RE.sub(" ", unit)
    out = []
    for claim, seg in _decision_claims(clean):
        for slug in _named_schools(seg, names):
            actual = res.get(slug, set())
            if claim == "accepted" and actual == {"rejected"} or claim == "rejected" and actual == {"accepted"}:
                nm = names[slug][-1] if names[slug] else slug
                out.append(f"[A:{a_id[:6]}] 写的是被 {nm} {'录取' if claim == 'accepted' else '拒绝'}，档案为"
                           f"{'拒绝' if claim == 'accepted' else '录取'}")
    return out


def crosscheck(text: str, conn) -> list[str]:
    """抽查模型写的具体数字和英文引语是否与所引出处一致。

    - 只含一个 [A:…] 的句子 / 表格行：其中的 SAT 总分、GPA 必须与该申请者档案一致；写成"录取"的学校
      不能是档案里的"拒绝"，反之亦然（只查说反了的，不查漏写的）；
    - 含 [E:…] 的句子：其中 ≥4 个英文单词的引语（按省略号切段）必须能在所引文书原文中找到。
    """
    text = normalize(text)
    problems: list[str] = []
    body_cache: dict[str, str] = {}
    for u in _units(text):
        ids = CITE_RE.findall(u)
        a_ids = list(dict.fromkeys(i for k, i in ids if k == "A"))
        e_ids = list(dict.fromkeys(i for k, i in ids if k == "E"))
        if len(a_ids) == 1:
            a = conn.execute("SELECT sat_total, gpa_uw, gpa_w FROM applicants WHERE id=?", (a_ids[0],)).fetchone()
            if a:
                sats = {int(x) for x in _SAT_RE.findall(u)}
                if sats and a["sat_total"] and a["sat_total"] not in sats:
                    problems.append(f"[A:{a_ids[0][:6]}] 写的 SAT {'/'.join(map(str, sorted(sats)))}，档案为 {a['sat_total']}")
                gpas = {float(x) for x in _GPA_RE.findall(u)}
                real = [g for g in (a["gpa_uw"], a["gpa_w"]) if g]
                if gpas and real and not any(abs(g - r) < 0.006 for g in gpas for r in real):
                    problems.append(f"[A:{a_ids[0][:6]}] 写的 GPA {'/'.join(map(str, sorted(gpas)))}，档案为 {'/'.join(map(str, real))}")
                problems += decision_mismatches(u, a_ids[0], conn)
        if e_ids:
            bodies = []
            for e in e_ids:
                if e not in body_cache:
                    r = conn.execute("SELECT prompt_text, body FROM essays WHERE id=?", (e,)).fetchone()
                    body_cache[e] = _norm_words(f"{r['prompt_text'] or ''} | {r['body'] or ''}") if r else ""
                bodies.append(body_cache[e])
            for q in _QUOTE_RE.findall(u):
                for frag in re.split(r"…|\.\.\.", q):
                    nf = _norm_words(frag)
                    if len(nf.split()) >= 4 and not any(nf in b for b in bodies if b):
                        problems.append(f"引语 “{frag.strip()[:40]}…” 在所引文书 [E:{e_ids[0][:6]}] 的题目和正文中都找不到")
                        break
    if not problems:
        return []
    shown = "；".join(dict.fromkeys(problems))
    return [f"出处核对：有 {len(set(problems))} 处具体数字或引语与所引材料不一致，交付前请顾问复核（{shown[:300]}）。"]
