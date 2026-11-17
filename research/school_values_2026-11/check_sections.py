"""核对画像中「学校看重的特质」节：原话逐字可查、链接来自证据、区分度档位。用法：python3 -I check_sections.py"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
P = ROOT / "undergraduate_essay/admission profile"; E = ROOT / "research/school_values_2026-11/evidence"
norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"'))
ev_raw = " ".join(f.read_text() for f in E.glob("*.md")); EV = norm(ev_raw)
prof_all = norm(" ".join(f.read_text() for f in P.glob("*.md")))
n = miss = badurl = 0; rows = []
for f in sorted(P.glob("*.md")):
    t = f.read_text()
    for m in re.finditer(r"^## 学校看重的特质（官方表述）\n(.*?)(?=^## |^# |\Z)", t, re.S | re.M):
        sec = m.group(1); rest = prof_all.replace(norm(sec), "")
        for q in [x for x in re.findall(r'"([^"]*)"', sec) if len(x) >= 8]:
            n += 1
            for frag in [x.strip(" ,.;") for x in norm(q).split("…") if len(x.strip()) > 6]:
                if frag not in EV and frag not in rest:
                    miss += 1; print("MISS", f.name, frag[:80])
        for u in re.findall(r"\]\((https?://[^)]+)\)", sec):
            if u not in ev_raw and u not in t.replace(sec, ""):
                badurl += 1; print("URL?", f.name, u)
        d = re.search(r"\*\*区分度：([^*]+)\*\*", sec)
        rows.append((f.name[:40], d.group(1) if d else "NO-DIST"))
for r in rows: print(*r)
print(f"sections {len(rows)} quotes {n} missing {miss} bad_urls {badurl}")
