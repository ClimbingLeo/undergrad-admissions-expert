"""Web：页面冒烟、租户 / 角色隔离、无 Key 降级、生成链路（假模型）。"""
import re
import time

from sibo.ai import runner
from sibo.ai.client import GenResult

PAGES = ["/", "/students", "/students/new", "/students/1/edit", "/reports", "/reports/1", "/reports/1/edit",
         "/reports/1?print=1", "/reports/1?print=1&clean=1", "/account", "/library/schools", "/library/schools/stanford", "/library/compare?s=mit&s=ucl",
         "/library/essays", "/library/essays?q=grandmother", "/library/applicants", "/library/cases", "/ee", "/marketing",
         "/data", "/settings"]


def test_pages_render(login):
    c = login("owner@demo.sibo")
    for p in PAGES:
        assert c.get(p).status_code == 200, p


def test_login_required(tmp_db):
    from fastapi.testclient import TestClient
    from sibo.web.main import app
    with TestClient(app) as c:
        r = c.get("/students", follow_redirects=False)
        assert r.status_code == 303 and "/login" in r.headers["location"]


def test_roles(login, conn):
    owner_student = conn.execute("SELECT s.id FROM students s JOIN users u ON u.id=s.owner_user_id WHERE u.role='owner'").fetchone()[0]
    viewer = login("viewer@demo.sibo")
    assert viewer.get("/students/new").status_code == 403
    assert viewer.get(f"/students/{owner_student}").status_code == 200
    assert viewer.get("/settings").status_code == 403  # 页面含邀请链接，只有管理员能看
    r = viewer.post("/settings/org", data={"csrf": viewer.csrf, "name": "x"}, follow_redirects=False)
    assert r.status_code == 403
    consultant = login("consultant@demo.sibo")
    assert consultant.get(f"/students/{owner_student}").status_code == 404


def test_tenant_isolation(login, conn):
    from sibo import auth
    org2 = conn.execute("INSERT INTO orgs(name) VALUES ('其他机构')").lastrowid
    conn.execute("INSERT INTO users(org_id,email,name,role,password_hash) VALUES (?,?,?,?,?)",
                 (org2, "boss@other.org", "老板", "owner", auth.hash_password("demo1234")))
    conn.commit()
    other = login("boss@other.org")
    demo_sid = conn.execute("SELECT id FROM students WHERE code='S001'").fetchone()[0]
    assert other.get(f"/students/{demo_sid}").status_code == 404
    assert "王子睿" not in other.get("/students").text
    for rid, in conn.execute("SELECT id FROM reports WHERE org_id != ?", (org2,)).fetchall()[:3]:
        assert other.get(f"/reports/{rid}").status_code == 404


def test_no_key_degrades(login, conn):
    conn.execute("UPDATE orgs SET api_key_enc=NULL")
    conn.commit()
    c = login("owner@demo.sibo")
    assert "尚未启用" in c.get("/").text
    sid = conn.execute("SELECT id FROM students WHERE code='S003'").fetchone()[0]
    r = c.post(f"/students/{sid}/generate/diagnosis", data={"csrf": c.csrf})
    assert r.status_code == 400 and "API Key" in r.text


def test_generation_pipeline(login, conn, monkeypatch):
    def fake(*, api_key, system_blocks, user_content, effort, on_text=None, **kw):
        ids = re.findall(r"\[(?:A|S|C):[^\]]+\]", user_content)[:2]
        text = ("## 一句话定位\n示例 " + " ".join(ids) + " [A:000000000000000000000000]\n\n"
                + "这是一段用于测试的正文，足够长以免被判定为空输出。" * 10)
        for ch in text:
            on_text(ch)
        return GenResult(text=text, model="fake", input_tokens=10, output_tokens=5)
    monkeypatch.setattr(runner, "GENERATE", fake)
    c = login("owner@demo.sibo")
    c.post("/settings/org", data={"csrf": c.csrf, "name": "演示", "api_key": "sk-ant-fake-key-000000", "brand_color": "#123456",
                                  "default_effort": "medium"})
    sid = conn.execute("SELECT id FROM students WHERE code='S003'").fetchone()[0]
    r = c.post(f"/students/{sid}/generate/diagnosis", data={"csrf": c.csrf}, follow_redirects=False)
    assert r.status_code == 303
    rid = int(r.headers["location"].rsplit("/", 1)[1])
    for _ in range(50):
        if conn.execute("SELECT status FROM reports WHERE id=?", (rid,)).fetchone()[0] != "pending":
            break
        time.sleep(0.1)
    row = conn.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
    assert row["status"] == "done"
    assert "000000000000" not in row["output_md"] and "/library/" in row["output_md"]
    assert "sk-ant-fake" not in (conn.execute("SELECT api_key_enc FROM orgs WHERE id=1").fetchone()[0] or "")
    page = c.get(f"/reports/{rid}").text
    assert "已移除 1 处" in page
    conn.execute("UPDATE orgs SET api_key_enc=NULL")
    conn.commit()


def test_csrf_enforced(login):
    c = login("owner@demo.sibo")
    r = c.post("/students/new", data={"csrf": "bad", "name": "x"})
    assert r.status_code == 400


def test_viewer_cannot_hijack_invite(login, conn):
    """审查 P0：只读账号不能看到待激活成员的邀请链接。"""
    owner = login("owner@demo.sibo")
    owner.post("/settings/members", data={"csrf": owner.csrf, "email": "newboss@demo.sibo", "role": "owner", "name": "新管理员"})
    token = conn.execute("SELECT invite_token FROM users WHERE email='newboss@demo.sibo'").fetchone()[0]
    for who in ("viewer@demo.sibo", "consultant@demo.sibo"):
        r = login(who).get("/settings")
        assert r.status_code == 403 and token not in r.text
    # 过期链接不可用
    conn.execute("UPDATE users SET invite_expires=datetime('now','-1 day') WHERE email='newboss@demo.sibo'")
    conn.commit()
    assert owner.get(f"/invite/{token}").status_code == 404


def test_open_redirect_blocked(tmp_db):
    from fastapi.testclient import TestClient
    from sibo.web.main import app, _safe_next
    assert _safe_next("//evil.example.com/x") == "/" and _safe_next("/\\evil") == "/" and _safe_next("/students") == "/students"


def test_orphan_pending_recovered(login, conn):
    """审查 P0：进程重启后 pending 报告不能永久卡死。"""
    rid = conn.execute("INSERT INTO reports(org_id, type, title, status) VALUES (1, 'diagnosis', '孤儿', 'pending')").lastrowid
    conn.commit()
    c = login("owner@demo.sibo")
    page = c.get(f"/reports/{rid}").text
    assert "服务重启导致生成中断" in page and "EventSource" not in page


def test_markdown_rendering_safety():
    from sibo.web.main import render_md
    assert 'href="#"' in render_md("[x](javascript:alert(1))", untrusted=True)
    assert "<script" not in render_md("<script>alert(1)</script>", untrusted=True)
    assert "<em>" not in render_md("UCL 要求 A*AA；Imperial 常见 A*A*A。", untrusted=True)
    assert "<li>" in render_md("**候选 A**\n- 一\n- 二", untrusted=True)


def test_anonymize_variants():
    from sibo.ai.prompts import anonymize
    s = {"name": "王子睿", "code": "S001", "aliases": "Zirui Wang, Ray"}
    out = anonymize("Zirui Wang / Wang Zirui / zirui / 子睿 / 王 子 睿 / Ray / array", s)
    assert "Zirui" not in out and "zirui" not in out and "子睿" not in out and "Ray" not in out
    assert "array" in out  # 词边界：不误伤普通单词


def test_report_edit_and_clean_print(login, conn):
    c = login("owner@demo.sibo")
    rid = conn.execute("SELECT id FROM reports WHERE status='done' AND output_md LIKE '%/library/%' LIMIT 1").fetchone()[0]
    clean = c.get(f"/reports/{rid}?print=1&clean=1").text
    assert "/library/applicants/" not in clean and "/library/schools/" not in clean
    r = c.post(f"/reports/{rid}/edit", data={"csrf": c.csrf, "title": "改过的标题", "output_md": "## 顾问修改版\n内容"},
               follow_redirects=False)
    assert r.status_code == 303
    row = conn.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()
    assert row["output_md"].startswith("## 顾问修改版") and row["output_original"]
    c.post(f"/reports/{rid}/edit", data={"csrf": c.csrf, "restore": "1"})
    assert conn.execute("SELECT output_md FROM reports WHERE id=?", (rid,)).fetchone()[0] == row["output_original"]
    assert login("viewer@demo.sibo").get(f"/reports/{rid}/edit").status_code == 403


def test_student_delete_requires_code(login, conn):
    c = login("owner@demo.sibo")
    c.post("/students/new", data={"csrf": c.csrf, "name": "待删学生"})
    sid, code = conn.execute("SELECT id, code FROM students WHERE name='待删学生'").fetchone()
    assert c.post(f"/students/{sid}/delete", data={"csrf": c.csrf, "confirm": "wrong"}).status_code == 400
    c.post(f"/students/{sid}/delete", data={"csrf": c.csrf, "confirm": code})
    assert conn.execute("SELECT 1 FROM students WHERE id=?", (sid,)).fetchone() is None


def test_change_password(login, conn):
    from sibo import auth
    conn.execute("INSERT INTO users(org_id,email,name,role,password_hash) VALUES (1,'pw@demo.sibo','改密','viewer',?)",
                 (auth.hash_password("demo1234"),))
    conn.commit()
    c = login("pw@demo.sibo")
    r = c.post("/account/password", data={"csrf": c.csrf, "old": "demo1234", "new": "newpass99", "new2": "newpass99"},
               follow_redirects=False)
    assert r.status_code == 303
    assert auth.verify_password("newpass99", conn.execute("SELECT password_hash FROM users WHERE email='pw@demo.sibo'").fetchone()[0])


def test_common_app_uses_common_app_samples(conn):
    from sibo.ai import builder
    s = conn.execute("SELECT * FROM students WHERE code='S002'").fetchone()
    req = builder.build(conn, "essay_strategy", s, {})
    eids = [i.split(":")[1] for i in req.allowed_ids if i.startswith("E:")]
    kinds = {conn.execute("SELECT kind FROM essays WHERE id=?", (e,)).fetchone()[0] for e in eids}
    assert kinds == {"common_app"}
    assert "今天是" in req.user_content


def test_clean_print_drops_consultant_notes():
    from sibo.web.main import strip_cites
    md = ("正文结论 [C·STEM-002](/library/cases/STEM-002)。\n\n---\n\n## 审稿备注（仅供顾问）\n1. 标题已调整\n")
    out = strip_cites(md)
    assert "审稿备注" not in out and "标题已调整" not in out
    assert out.endswith("正文结论（案例 1）。")
    assert "审稿备注" not in strip_cites("a\n### 【审稿备注｜仅供顾问】\nb")
