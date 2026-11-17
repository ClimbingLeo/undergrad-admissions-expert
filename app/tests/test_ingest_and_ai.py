"""全量入库计数 + 检索 / 引用 / 匿名化。"""
from sibo.ai import builder, citations


def test_ingest_counts(conn):
    n = lambda sql: conn.execute(sql).fetchone()[0]
    assert n("SELECT COUNT(*) FROM applicants") == 120
    assert n("SELECT COUNT(*) FROM essays WHERE kind='common_app'") == 135
    assert n("SELECT COUNT(*) FROM essays WHERE kind='supplement'") >= 640
    assert n("SELECT COUNT(DISTINCT id) FROM essays") == n("SELECT COUNT(*) FROM essays")
    assert n("SELECT COUNT(*) FROM schools WHERE has_profile=1") >= 38
    assert n("SELECT COUNT(*) FROM ee_samples") >= 40
    # 档案中的虚构案例必须被识别
    assert n("SELECT COUNT(*) FROM school_profile_sections WHERE trust='composite'") > 100
    assert n("SELECT COUNT(*) FROM school_profile_sections WHERE body_md LIKE '%李明%' AND trust!='composite'") == 0


def test_retrieval_excludes_composite(conn):
    s = conn.execute("SELECT * FROM students WHERE code='S001'").fetchone()
    r = builder.build(conn, "diagnosis", s, {})
    for sid in [x for x in r.allowed_ids if x.startswith("S:")]:
        slug, _, ord_ = sid[2:].partition("#")
        trust = conn.execute("SELECT trust FROM school_profile_sections WHERE school_slug=? AND ord=?", (slug, int(ord_))).fetchone()[0]
        assert trust not in ("composite", "simulated")
    assert any(x.startswith("A:") for x in r.allowed_ids)


def test_student_name_never_sent(conn):
    for code in ("S001", "S002", "S003"):
        s = conn.execute("SELECT * FROM students WHERE code=?", (code,)).fetchone()
        for t in ("diagnosis", "activity_plan"):
            r = builder.build(conn, t, s, {})
            assert s["name"] not in r.user_content
        r = builder.build(conn, "essay_review", s, {"school_slug": "penn", "draft": f"My name is {s['name']} and I love Penn " * 5})
        assert s["name"] not in r.user_content


def test_citation_validation():
    allowed = {"A:abc123abc123abc123abc123", "C:STEM-002", "S:mit#3"}
    md, cites, warns = citations.validate(
        "见 [A:abc123abc123abc123abc123] 与 [C:STEM-002]、[S:mit#3]，伪造 [E:ffffffffffffffffffffffff]；录取概率约 40%", allowed)
    assert "/library/applicants/abc123abc123abc123abc123" in md
    assert "/library/schools/mit#sec-3" in md
    assert "ffffffff" not in md
    assert len(cites) == 3
    assert any("移除 1 处" in w for w in warns) and any("概率" in w for w in warns)


def test_applicant_brief_never_hides_target_rejections(conn):
    from sibo.ai import retrieval as R
    # 找一个拒绝学校超过 10 所的申请者，挑一所排在后面的被拒学校当"目标校"
    aid = conn.execute("SELECT applicant_id FROM applicant_decisions WHERE result='rejected' "
                       "GROUP BY applicant_id HAVING COUNT(*) > 10 LIMIT 1").fetchone()[0]
    rows = conn.execute("SELECT school_slug, school_name FROM applicant_decisions WHERE applicant_id=? AND result='rejected' "
                        "ORDER BY school_name DESC", (aid,)).fetchall()
    a = conn.execute("SELECT * FROM applicants WHERE id=?", (aid,)).fetchone()
    brief = R.applicant_brief(conn, a, targets=[rows[0]["school_slug"]])
    assert f"★{rows[0]['school_name']}" in brief
    assert "另有" in brief  # 其余超出部分写明数量，而不是静默截断


def test_application_cycle_by_grade():
    import datetime as d
    from sibo.ai.prompts import application_cycle
    t = d.date(2026, 11, 17)
    assert application_cycle("G12", t).startswith("预计 2026 年秋季递交申请、2027 年秋季入学")
    assert application_cycle("G11", t).startswith("预计 2027 年秋季递交申请、2028 年秋季入学")
    assert application_cycle("高三", t).startswith("预计 2026")
    assert "请顾问确认" in application_cycle("", t)


def test_crosscheck_flags_wrong_numbers_and_quotes(conn):
    a = conn.execute("SELECT id, sat_total FROM applicants WHERE sat_total IS NOT NULL LIMIT 1").fetchone()
    e = conn.execute("SELECT id, body FROM essays WHERE length(body) > 500 LIMIT 1").fetchone()
    real_quote = " ".join(e["body"].split()[5:12])
    ok = f"SAT {a['sat_total']} 的申请者 [A:{a['id']}]。原文 \"{real_quote}\" [E:{e['id']}]。"
    assert citations.crosscheck(ok, conn) == []
    bad = f"SAT {a['sat_total'] - 30} 的申请者 [A:{a['id']}]。原文 \"I have always loved burning toast\" [E:{e['id']}]。"
    w = citations.crosscheck(bad, conn)
    assert w and "2 处" in w[0]


def test_trust_summary_sections_not_verified():
    from sibo.ingest.parsers import _trust_for
    assert _trust_for("最终总结：核心要点", "见 https://example.edu/stats", "ec") == "unsourced"
    assert _trust_for("关键录取数据", "见 https://example.edu/stats", "data") == "verified_source"


def test_trust_composite_only_for_fictional_hypotheticals():
    from sibo.ingest.parsers import _trust_for
    # 普通用法的「假设」不是虚构案例
    assert _trust_for("对中国学生的建议", "不要假设录取官知道 AMC 的价值", "insight") == "unsourced"
    # 假设的学生 / 化名人物 → 示例画像
    assert _trust_for("学生画像", "以下是一个假设的学生：北京国际学校，SAT 1550", "cases") == "composite"


def test_stream_retries_only_before_any_text(monkeypatch):
    import pytest
    from sibo.ai import client as C
    monkeypatch.setattr(C.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def flaky(client, model, sb, uc, effort, mt, emit, res):
        calls["n"] += 1
        if calls["n"] == 1:
            raise C.NetworkInterrupted(C._NET_MSG)   # 思考阶段断线，没有任何正文
        emit("正文")
    monkeypatch.setattr(C, "_do_stream", flaky)
    r = C.stream_generate(api_key="k", system_blocks=[], user_content="x")
    assert r.text == "正文" and calls["n"] == 2 and "自动重试 1 次" in r.notes[0]

    def mid_stream(client, model, sb, uc, effort, mt, emit, res):
        emit("已经写了一半")
        raise C.NetworkInterrupted(C._NET_MSG)
    monkeypatch.setattr(C, "_do_stream", mid_stream)
    with pytest.raises(C.NetworkInterrupted) as ei:
        C.stream_generate(api_key="k", system_blocks=[], user_content="x")
    assert ei.value.partial == "已经写了一半"   # 已有输出不重发，交给上层保留部分内容


def test_transport_errors_become_chinese_message():
    import pytest
    from sibo.ai import client as C
    Err = type("RemoteProtocolError", (Exception,), {"__module__": "httpcore2"})
    with pytest.raises(C.NetworkInterrupted):
        with C._errors("m"):
            raise Err("peer closed connection")


def test_abbreviated_ids_expanded_only_when_unique():
    allowed = {"A:6821fc3dd84d23dec7de9dac", "A:6821fffbd84d23dec7e0bfed", "S:mit#1"}
    md, cites, warns = citations.validate("见 [A:6821fc3d] 和 [A:6821f]。[S:mit#1]", allowed)
    assert "/library/applicants/6821fc3dd84d23dec7de9dac" in md      # 唯一前缀：补全
    assert "6821f]" not in md and any("已移除 1 处" in w for w in warns)  # 前缀不唯一：删除
    assert {c["id"] for c in cites} == {"A:6821fc3dd84d23dec7de9dac", "S:mit#1"}


def test_crosscheck_flags_reversed_decisions(conn):
    row = conn.execute("""SELECT a.applicant_id, a.school_name AS acc, r.school_name AS rej
                          FROM applicant_decisions a JOIN applicant_decisions r ON r.applicant_id=a.applicant_id
                          WHERE a.result='accepted' AND r.result='rejected' LIMIT 1""").fetchone()
    aid, acc, rej = row
    assert citations.crosscheck(f"该生录取 {acc}；拒 {rej} [A:{aid}]。", conn) == []
    w = citations.crosscheck(f"该生被 {rej} 录取 [A:{aid}]。", conn)
    assert w and "录取，档案为拒绝" in w[0]
    assert citations.crosscheck(f"录取率 5% 的 {rej} [A:{aid}]。", conn) == []   # "录取率"不是录取结论


def test_values_section_type():
    from sibo.ingest.parsers import classify_section
    assert classify_section("学校看重的特质（官方表述）") == "values"
    # 旧画像里未溯源的「价值观」小节不能混进 values
    assert classify_section("UCSD的价值观和申请契合度") != "values"


def test_every_profiled_school_has_values_section(conn):
    missing = conn.execute("""SELECT slug FROM schools WHERE has_profile=1 AND slug NOT IN
                              (SELECT school_slug FROM school_profile_sections WHERE section_type='values')""").fetchall()
    assert [r[0] for r in missing] == []
    # 每节开头都写明区分度档位
    bad = conn.execute("""SELECT school_slug FROM school_profile_sections WHERE section_type='values'
                          AND body_md NOT LIKE '%区分度%'""").fetchall()
    assert bad == []
