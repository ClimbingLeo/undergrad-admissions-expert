"""知识库入库：python -m sibo.ingest.run

幂等：每次清空全局知识表后重建，不动租户数据。结束时打印各表计数。
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from .. import config, db, schools
from . import parsers as P

KNOWLEDGE_TABLES = [
    "essays_fts", "cases_fts", "applicant_decisions", "applicant_activities", "applicant_awards",
    "applicants", "essays", "supp_guides", "narrative_cases", "ee_samples", "school_profile_sections",
    "schools", "kb_meta",
]


def _ensure_school(conn: sqlite3.Connection, slug: str, name_en: str | None = None) -> None:
    if not slug:
        return
    conn.execute("INSERT OR IGNORE INTO schools(slug, name_en) VALUES (?, ?)", (slug, name_en or slug))


def ingest(conn: sqlite3.Connection, root: Path, verbose: bool = True) -> dict:
    stats: Counter = Counter()
    warnings: list[str] = []
    for t in KNOWLEDGE_TABLES:
        conn.execute(f"DELETE FROM {t}")

    for slug, en, zh, region, aliases in schools.canon_rows():
        conn.execute("INSERT INTO schools(slug, name_en, name_zh, region, aliases) VALUES (?,?,?,?,?)",
                     (slug, en, zh, region, json.dumps(aliases)))

    # 1. 申请者画像
    applicants = P.load_applicants(root)
    for a in applicants:
        n_acc = sum(1 for d in a["decisions"] if d["result"] == "accepted")
        n_rej = sum(1 for d in a["decisions"] if d["result"] == "rejected")
        conn.execute(
            """INSERT INTO applicants(id,bucket,gender,ethnicity,country,high_school_type,application_year,major,major_group,
               enrolled_at,sat_total,act_composite,gpa_uw,gpa_w,class_rank,scores_json,source_url,n_accepted,n_rejected)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (a["id"], a["bucket"], a["gender"], a["ethnicity"], a["country"], a["high_school_type"], a["application_year"],
             a["major"], a["major_group"], a["enrolled_at"], a["sat_total"], a["act_composite"], a["gpa_uw"], a["gpa_w"],
             a["class_rank"], a["scores_json"], a["source_url"], n_acc, n_rej))
        for d in a["decisions"]:
            _ensure_school(conn, d["school_slug"], d["school_name"])
            conn.execute("INSERT OR IGNORE INTO applicant_decisions VALUES (?,?,?,?)",
                         (a["id"], d["school_slug"], d["school_name"], d["result"]))
        for i, act in enumerate(a["activities"]):
            conn.execute("INSERT INTO applicant_activities(applicant_id,ord,position,organization,description) VALUES (?,?,?,?,?)",
                         (a["id"], i, act["position"], act["organization"], act["description"]))
        for aw in a["awards"]:
            conn.execute("INSERT INTO applicant_awards(applicant_id,name,level) VALUES (?,?,?)", (a["id"], aw["name"], aw["level"]))
    stats["applicants"] = len(applicants)
    essay_owner = {eid: a["id"] for a in applicants for eid in a["essay_link_ids"]}

    # 2/3. 文书
    essays: dict[str, dict] = {}
    ca_dir = root / "clastify/common_app_essay"
    for f in sorted(ca_dir.glob("common_app_top*.md")):
        for e in P.parse_common_app_collection(f.read_text(encoding="utf-8"), f.relative_to(root).as_posix()):
            essays.setdefault(e["id"], e)
    for f in sorted(ca_dir.glob("commonapp_*.md")):
        e = P.parse_common_app_single(f.read_text(encoding="utf-8"), f.relative_to(root).as_posix())
        if e is None:
            warnings.append(f"无法解析 {f.name}")
            continue
        if e["id"] in essays:  # 合集里已有：补充决策信息
            prev = essays[e["id"]]
            known = {(d["slug"], d["result"]) for d in prev["decisions"]}
            prev["decisions"] += [d for d in e["decisions"] if (d["slug"], d["result"]) not in known]
        else:
            essays[e["id"]] = e
    stats["common_app_essays"] = sum(1 for e in essays.values() if e["kind"] == "common_app")

    supp_root = root / "clastify/supplements_essay"
    guide_rows = []
    dup = 0
    for f in sorted(supp_root.rglob("*.md")):
        rel = f.relative_to(supp_root)
        if len(rel.parts) < 2:  # README / _index / COMPLETION_REPORT
            continue
        slug = schools.resolve(rel.parts[0])
        hint = rel.parts[1].replace("prompt_", "").replace("_", " ") if len(rel.parts) == 3 else None
        es, gs = P.parse_supplement_file(f.read_text(encoding="utf-8"), slug, f.relative_to(root).as_posix(), hint)
        for e in es:
            if e["id"] in essays:
                dup += 1
                # 更具体的 prompt 目录优先
                if hint and essays[e["id"]].get("source_file", "").count("/") < e["source_file"].count("/"):
                    essays[e["id"]].update(prompt_key=e["prompt_key"], prompt_text=e["prompt_text"], word_limit=e["word_limit"])
                continue
            essays[e["id"]] = e
        guide_rows += gs
    stats["supplement_essays"] = sum(1 for e in essays.values() if e["kind"] == "supplement")
    stats["supplement_duplicates_dropped"] = dup

    linked = 0
    for e in essays.values():
        e["applicant_id"] = essay_owner.get(e["id"])
        linked += bool(e["applicant_id"])
        _ensure_school(conn, e["school_slug"])
        conn.execute(
            """INSERT INTO essays(id,kind,title,school_slug,prompt_key,prompt_text,word_limit,result,year,major,stats,body,
               word_count,source_url,applicant_id,decisions,source_file) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (e["id"], e["kind"], e["title"], e["school_slug"], e["prompt_key"], e["prompt_text"], e["word_limit"], e["result"],
             e["year"], e["major"], e["stats"], e["body"], P.word_count(e["body"]), e["source_url"], e["applicant_id"],
             json.dumps(e["decisions"], ensure_ascii=False), e["source_file"]))
        conn.execute("INSERT INTO essays_fts(id,title,prompt_text,body,major) VALUES (?,?,?,?,?)",
                     (e["id"], e["title"] or "", e["prompt_text"] or "", e["body"], e["major"] or ""))
    stats["essays_linked_to_applicant"] = linked

    for g in guide_rows:
        conn.execute("INSERT INTO supp_guides(school_slug,title,body_md,source_file) VALUES (?,?,?,?)",
                     (g["school_slug"], g["title"], g["body_md"], g["source_file"]))
    stats["supp_guides"] = len(guide_rows)

    # 4. 学校档案
    prof_dir = root / "undergraduate_essay/admission profile"
    trust_counter: Counter = Counter()
    for f in sorted(prof_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(root).as_posix()
        if f.stem.startswith("school_profiles_"):
            pieces = [(schools.resolve(name), body) for name, body in P.split_combined_profiles(text)]
        else:
            slug = schools.resolve_profile_filename(f.stem)
            if not slug:
                warnings.append(f"档案无法匹配学校：{f.name}")
                continue
            pieces = [(slug, text)]
        for slug, body in pieces:
            _ensure_school(conn, slug)
            secs = P.parse_school_profile(body, rel)
            for s in secs:
                trust_counter[s["trust"]] += 1
                conn.execute(
                    """INSERT INTO school_profile_sections(school_slug,ord,heading,body_md,section_type,trust,source_urls,source_file)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (slug, s["ord"], s["heading"], s["body_md"], s["section_type"], s["trust"], json.dumps(s["source_urls"]), rel))
            conn.execute("UPDATE schools SET has_profile=1 WHERE slug=?", (slug,))
    stats["schools_with_profile"] = conn.execute("SELECT COUNT(*) FROM schools WHERE has_profile=1").fetchone()[0]
    stats["profile_sections"] = sum(trust_counter.values())
    for k, v in trust_counter.items():
        stats[f"profile_sections.{k}"] = v

    # 5. 叙事案例
    case_count: Counter = Counter()
    for f in sorted((root / "undergraduate_essay").glob("CASES*.md")):
        for c in P.parse_cases(f.read_text(encoding="utf-8"), f.relative_to(root).as_posix()):
            if conn.execute("SELECT 1 FROM narrative_cases WHERE case_code=?", (c["case_code"],)).fetchone():
                warnings.append(f"案例编号重复：{c['case_code']}")
                continue
            conn.execute(
                """INSERT INTO narrative_cases(case_code,title,outcome,category,body_md,source_type,source_url,trust,source_file)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (c["case_code"], c["title"], c["outcome"], c["category"], c["body_md"], c["source_type"], c["source_url"], c["trust"], c["source_file"]))
            conn.execute("INSERT INTO cases_fts(case_code,title,body_md) VALUES (?,?,?)", (c["case_code"], c["title"], c["body_md"]))
            case_count[c["trust"]] += 1
    stats["narrative_cases"] = sum(case_count.values())
    for k, v in case_count.items():
        stats[f"narrative_cases.{k}"] = v

    # 6. IB EE
    ib = root / "clastify/IB_essay"
    meta = {}
    csv_path = root / "undergraduate_essay/clastify_maths_ee_grade_a.csv"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                meta[row["id"]] = row
    for grade in ("a", "b", "c"):
        f = ib / f"ib_maths_ee_grade_{grade}.md"
        if not f.exists():
            continue
        for s in P.parse_ee_file(f.read_text(encoding="utf-8"), grade.upper()):
            m = meta.get(s["id"], {})
            conn.execute(
                """INSERT OR IGNORE INTO ee_samples(id,grade,title,session,total_pages,strong_aspects,grade_verified,excerpt,url)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (s["id"], s["grade"], s["title"], s["session"], s["total_pages"], m.get("strongAspects"),
                 1 if m.get("gradeVerified") == "true" else None, s["excerpt"], s["url"]))
            stats[f"ee_samples.{grade.upper()}"] += 1

    stats["schools_total"] = conn.execute("SELECT COUNT(*) FROM schools").fetchone()[0]
    conn.execute("INSERT INTO kb_meta VALUES ('ingested_at', ?)", (datetime.now().isoformat(timespec="seconds"),))
    conn.execute("INSERT INTO kb_meta VALUES ('stats', ?)", (json.dumps(dict(stats), ensure_ascii=False),))
    conn.execute("INSERT INTO kb_meta VALUES ('warnings', ?)", (json.dumps(warnings, ensure_ascii=False),))
    conn.commit()
    if verbose:
        for k in sorted(stats):
            print(f"  {k:40s} {stats[k]}")
        for w in warnings:
            print("  ⚠", w)
    return dict(stats)


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else config.SOURCE_ROOT
    conn = db.connect()
    db.init_schema(conn)
    print(f"入库素材目录：{root}\n数据库：{config.DB_PATH}")
    ingest(conn, root)
    conn.close()


if __name__ == "__main__":
    main()
