"""思博杂学社 Agent —— Web 入口。"""
from __future__ import annotations

import asyncio
import html
import io
import json
import re
import threading
import time
from pathlib import Path

import markdown as md_lib
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .. import auth, config, db
from ..ai import builder, runner
from ..ai.client import mask_key, resolve_api_key, encrypt_key
from ..ai.retrieval import TRUST_LABEL, school_prompts
from ..ingest.parsers import MAJOR_GROUP_LABELS, major_group

HERE = Path(__file__).parent
templates = Jinja2Templates(directory=HERE / "templates")

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app):
    from ..cli import bootstrap
    bootstrap()
    yield


app = FastAPI(title=config.PRODUCT_NAME, docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, session_cookie="sibo_session",
                   max_age=60 * 60 * 24 * 14, same_site="lax", https_only=config.HTTPS_ONLY)


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    return resp
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")


# ───────────────────────── 工具函数 ─────────────────────────
_LIST_LINE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_GRADE_STAR = re.compile(r"(?<![A-Za-z\\])([A-E])\*(?!\*)")


def _loosen_lists(text: str) -> str:
    """Python-Markdown 要求列表前有空行，模型输出常常没有：在「普通段落行 → 列表行」之间补一个空行。"""
    out: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if (not in_fence and out and _LIST_LINE.match(line) and out[-1].strip()
                and not _LIST_LINE.match(out[-1]) and not out[-1].lstrip().startswith("|")):
            out.append("")
        out.append(line)
    return "\n".join(out)


_HREF = re.compile(r'(href|src)="([^"]*)"')
_CITE_LINK = re.compile(r"\[(?:A|E|C|S|EE)·[^\]]*\]\([^)]*\)")
_CITE_LINK_K = re.compile(r"\[(A|E|C|S|EE)·[^\]]*\]\(([^)]*)\)")


def _safe_href(m: re.Match) -> str:
    url = html.unescape(m.group(2)).strip()
    if re.match(r"(https?:|/(?![/\\])|#)", url, re.I):
        return m.group(0)
    return f'{m.group(1)}="#"'


def render_md(text: str | None, untrusted: bool = False) -> str:
    if not text:
        return ""
    if untrusted:
        text = text.replace("<", "&lt;")
    text = _GRADE_STAR.sub(r"\1\\*", text)  # A*AA / A*A*A 之类成绩里的星号不是斜体
    out = md_lib.markdown(_loosen_lists(text), extensions=["tables", "fenced_code", "sane_lists"])
    return _HREF.sub(_safe_href, out) if untrusted else out  # 只放行 http(s)、站内路径和锚点，挡掉 javascript: 等


def essay_html(body: str) -> str:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in paras)


templates.env.filters["md"] = render_md
templates.env.filters["md_untrusted"] = lambda t: render_md(t, untrusted=True)
templates.env.filters["essay"] = essay_html
_REVIEW_NOTES = re.compile(r"^[ \t]*#{1,6}[ \t]*[【\[]?审稿备注.*$", re.M)  # 「审稿备注（仅供顾问）」及其后全部内容不进交付版


def strip_cites(text: str | None) -> str:
    """交付版：去掉指向内部知识库的链接。案例 / 文书按首次出现编号（同一出处全文同号），学校数据出处直接去掉。"""
    nums: dict[str, str] = {}
    counters = {"案例": 0, "文书样本": 0, "EE 样本": 0}

    def repl(m: re.Match) -> str:
        kind, url = m.group(1), m.group(2)
        if kind == "S":
            return ""
        label = {"A": "案例", "C": "案例", "E": "文书样本", "EE": "EE 样本"}[kind]
        if url not in nums:
            counters[label] += 1
            nums[url] = f"{label} {counters[label]}"
        return f"（{nums[url]}）"

    out = _REVIEW_NOTES.split(text or "", maxsplit=1)[0].rstrip().removesuffix("---").rstrip()
    out = _CITE_LINK_K.sub(repl, out)
    out = re.sub(r"(（[^（）]{1,12}）)(?:\s*\1)+", r"\1", out)          # 连续重复的同一标签只留一个
    out = re.sub(r"(?<=[^\s|])[ \t]+(（(?:案例|文书样本|EE 样本) \d+）)", r"\1", out)  # 标签紧贴前文
    return re.sub(r"[ \t]+([，。；、])", r"\1", out)


templates.env.filters["strip_cites"] = strip_cites
templates.env.filters["fromjson"] = lambda s: json.loads(s) if s else []
templates.env.globals.update(
    PRODUCT=config.PRODUCT_NAME, TRUST_LABEL=TRUST_LABEL, REPORT_TYPES=builder.REPORT_TYPES,
    MAJOR_GROUPS=MAJOR_GROUP_LABELS, ROLES=auth.ROLES,
)


class NeedLogin(Exception):
    pass


@app.exception_handler(NeedLogin)
async def _need_login(request: Request, exc: NeedLogin):
    return RedirectResponse(f"/login?next={request.url.path}", status_code=303)


def get_conn():
    return db.connect()


def current_user(request: Request, conn):
    uid = request.session.get("uid")
    if not uid:
        raise NeedLogin()
    u = conn.execute("SELECT u.*, o.name AS org_name, o.brand_name, o.brand_color FROM users u JOIN orgs o ON o.id=u.org_id "
                     "WHERE u.id=? AND u.active=1", (uid,)).fetchone()
    if not u:
        request.session.clear()
        raise NeedLogin()
    return u


def org_of(conn, user):
    return conn.execute("SELECT * FROM orgs WHERE id=?", (user["org_id"],)).fetchone()


def page(request: Request, name: str, ctx: dict, status: int = 200):
    ctx = {"request": request, "csrf": auth.csrf_token(request.session), **ctx}
    return templates.TemplateResponse(request, name, ctx, status_code=status)


def require_csrf(request: Request, token: str | None):
    if not auth.check_csrf(request.session, token):
        raise HTTPException(400, "表单已过期，请刷新页面后重试。")


def require_write(user):
    if not auth.can_write(user):
        raise HTTPException(403, "当前账号为只读权限。")


def flash(request: Request, msg: str, kind: str = "ok"):
    request.session.setdefault("flash", []).append([kind, msg])


def pop_flash(request: Request):
    return request.session.pop("flash", [])


templates.env.globals["pop_flash"] = pop_flash


def ai_ready(conn, user) -> bool:
    return bool(resolve_api_key(org_of(conn, user)))


def schools_options(conn):
    return conn.execute(
        """SELECT s.slug, s.name_en, s.name_zh, s.region, s.has_profile,
                  (SELECT COUNT(*) FROM essays e WHERE e.school_slug=s.slug AND e.kind='supplement') AS n_supp
           FROM schools s WHERE s.name_zh IS NOT NULL ORDER BY s.region, s.name_en""").fetchall()


@app.exception_handler(StarletteHTTPException)  # 同时覆盖路由不存在时 Starlette 抛出的 404
async def _http_error(request: Request, exc: StarletteHTTPException):
    detail = exc.detail if exc.status_code != 404 or exc.detail != "Not Found" else "页面不存在。"
    return templates.TemplateResponse(request, "error.html", {"request": request, "status": exc.status_code,
                                                              "detail": detail}, status_code=exc.status_code)


# ───────────────────────── 登录 ─────────────────────────
_FAILS: dict[str, list[float]] = {}
_FAILS_LOCK = threading.Lock()
MAX_FAILS, FAIL_WINDOW = 8, 15 * 60


def _too_many_fails(key: str) -> bool:
    now = time.time()
    with _FAILS_LOCK:
        recent = [t for t in _FAILS.get(key, []) if now - t < FAIL_WINDOW]
        _FAILS[key] = recent
        return len(recent) >= MAX_FAILS


def _record_fail(key: str) -> None:
    with _FAILS_LOCK:
        _FAILS.setdefault(key, []).append(time.time())


def _safe_next(nxt: str | None) -> str:
    nxt = nxt or "/"
    return nxt if re.match(r"^/(?![/\\])", nxt) else "/"


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/"):
    return page(request, "login.html", {"next": _safe_next(next), "error": None})


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), next: str = Form("/"),
          csrf: str = Form(None)):
    require_csrf(request, csrf)
    keys = [f"e:{email.strip().lower()}", f"ip:{request.client.host if request.client else '-'}"]
    if any(_too_many_fails(k) for k in keys):
        return page(request, "login.html", {"next": _safe_next(next), "error": "尝试次数过多，请 15 分钟后再试。"}, status=429)
    conn = get_conn()
    u = conn.execute("SELECT * FROM users WHERE lower(email)=lower(?) AND active=1", (email.strip(),)).fetchone()
    if not u or not auth.verify_password(password, u["password_hash"]):
        for k in keys:
            _record_fail(k)
        return page(request, "login.html", {"next": _safe_next(next), "error": "邮箱或密码错误"}, status=401)
    request.session.clear()
    request.session["uid"] = u["id"]
    auth.audit(conn, u, "login")
    conn.commit()
    return RedirectResponse(_safe_next(next), status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


def _invitee(conn, token: str):
    u = conn.execute("SELECT * FROM users WHERE invite_token=? AND active=1 "
                     "AND (invite_expires IS NULL OR invite_expires > datetime('now'))", (token,)).fetchone()
    if not u:
        raise HTTPException(404, "邀请链接无效、已使用或已过期，请联系机构管理员重新生成。")
    return u


@app.get("/invite/{token}", response_class=HTMLResponse)
def invite_form(request: Request, token: str):
    conn = get_conn()
    u = _invitee(conn, token)
    return page(request, "invite.html", {"invitee": u, "token": token, "error": None})


@app.post("/invite/{token}")
def invite_accept(request: Request, token: str, password: str = Form(...), csrf: str = Form(None)):
    require_csrf(request, csrf)
    conn = get_conn()
    u = _invitee(conn, token)
    if len(password) < 8:
        return page(request, "invite.html", {"invitee": u, "token": token, "error": "密码至少 8 位"}, status=400)
    conn.execute("UPDATE users SET password_hash=?, invite_token=NULL, invite_expires=NULL WHERE id=?",
                 (auth.hash_password(password), u["id"]))
    auth.audit(conn, u, "invite.accept")
    conn.commit()
    request.session.clear()
    request.session["uid"] = u["id"]
    return RedirectResponse("/", status_code=303)


@app.get("/account", response_class=HTMLResponse)
def account_page(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    return page(request, "account.html", {"user": user, "error": None})


@app.post("/account/password")
async def account_password(request: Request, old: str = Form(...), new: str = Form(...), new2: str = Form(...),
                           csrf: str = Form(None)):
    require_csrf(request, csrf)
    conn = get_conn()
    user = current_user(request, conn)
    err = None
    if not auth.verify_password(old, user["password_hash"]):
        err = "当前密码不正确"
    elif len(new) < 8:
        err = "新密码至少 8 位"
    elif new != new2:
        err = "两次输入的新密码不一致"
    if err:
        return page(request, "account.html", {"user": user, "error": err}, status=400)
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (auth.hash_password(new), user["id"]))
    auth.audit(conn, user, "account.password")
    conn.commit()
    flash(request, "密码已修改")
    return RedirectResponse("/account", status_code=303)


# ───────────────────────── 工作台 ─────────────────────────
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    stats = json.loads((conn.execute("SELECT value FROM kb_meta WHERE key='stats'").fetchone() or ["{}"])[0])
    students = auth.students_for(conn, user)[:6]
    reports = auth.reports_for(conn, user, limit=8)
    return page(request, "dashboard.html", {"user": user, "stats": stats, "students": students, "reports": reports,
                                            "ai_ready": ai_ready(conn, user)})


# ───────────────────────── 学生 ─────────────────────────
STUDENT_FIELDS = ["name", "aliases", "grade_level", "school", "curriculum", "gpa", "tests", "intended_major", "activities",
                  "awards", "background", "budget_notes"]


@app.get("/students", response_class=HTMLResponse)
def students_list(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    rows = auth.students_for(conn, user)
    counts = {r["student_id"]: r["n"] for r in conn.execute(
        "SELECT student_id, COUNT(*) n FROM reports WHERE org_id=? GROUP BY student_id", (user["org_id"],))}
    return page(request, "students.html", {"user": user, "students": rows, "counts": counts})


@app.get("/students/new", response_class=HTMLResponse)
def student_new(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    return page(request, "student_form.html", {"user": user, "s": None, "schools": schools_options(conn), "targets": [],
                                               "consultants": _consultants(conn, user)})


def _consultants(conn, user):
    return conn.execute("SELECT id, name, role, active FROM users WHERE org_id=? AND role IN ('owner','consultant') "
                        "AND password_hash IS NOT NULL ORDER BY role DESC, name", (user["org_id"],)).fetchall()


def _save_student(request: Request, conn, user, form, student_id: int | None):
    vals = {k: (form.get(k) or "").strip() for k in STUDENT_FIELDS}
    if not vals["name"]:
        raise HTTPException(400, "请填写学生姓名")
    targets = [t for t in form.getlist("target_schools") if t][:8]
    mg = major_group(vals["intended_major"])
    if student_id is None:
        code = auth.next_student_code(conn, user["org_id"])
        cur = conn.execute(
            f"""INSERT INTO students(org_id, owner_user_id, code, major_group, target_schools, {', '.join(STUDENT_FIELDS)})
                VALUES (?,?,?,?,?,{', '.join('?' * len(STUDENT_FIELDS))})""",
            (user["org_id"], user["id"], code, mg, json.dumps(targets), *vals.values()))
        student_id = cur.lastrowid
        auth.audit(conn, user, "student.create", code)
    else:
        sets = ", ".join(f"{k}=?" for k in STUDENT_FIELDS)
        conn.execute(f"UPDATE students SET {sets}, major_group=?, target_schools=?, updated_at=datetime('now') "
                     f"WHERE id=? AND org_id=?", (*vals.values(), mg, json.dumps(targets), student_id, user["org_id"]))
        auth.audit(conn, user, "student.update", str(student_id))
    new_owner = form.get("owner_user_id")
    if auth.is_owner(user) and new_owner and new_owner.isdigit():
        if conn.execute("SELECT 1 FROM users WHERE id=? AND org_id=? AND role IN ('owner','consultant')",
                        (int(new_owner), user["org_id"])).fetchone():
            conn.execute("UPDATE students SET owner_user_id=? WHERE id=? AND org_id=?", (int(new_owner), student_id, user["org_id"]))
    conn.commit()
    return student_id


@app.post("/students/new")
async def student_create(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    sid = _save_student(request, conn, user, form, None)
    flash(request, "学生档案已创建")
    return RedirectResponse(f"/students/{sid}", status_code=303)


@app.get("/students/{sid}", response_class=HTMLResponse)
def student_detail(request: Request, sid: int):
    conn = get_conn()
    user = current_user(request, conn)
    s = auth.get_student(conn, user, sid)
    if not s:
        raise HTTPException(404, "学生不存在或无权访问")
    reports = auth.reports_for(conn, user, student_id=sid)
    targets = json.loads(s["target_schools"] or "[]")
    tnames = {r["slug"]: r for r in conn.execute(
        f"SELECT slug, name_en, name_zh, has_profile FROM schools WHERE slug IN ({','.join('?' * len(targets)) or 'NULL'})",
        targets)}
    return page(request, "student_detail.html", {"user": user, "s": s, "reports": reports, "targets": targets,
                                                 "tnames": tnames, "ai_ready": ai_ready(conn, user),
                                                 "schools": schools_options(conn)})


@app.get("/students/{sid}/edit", response_class=HTMLResponse)
def student_edit(request: Request, sid: int):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    s = auth.get_student(conn, user, sid)
    if not s:
        raise HTTPException(404, "学生不存在或无权访问")
    return page(request, "student_form.html", {"user": user, "s": s, "schools": schools_options(conn),
                                               "targets": json.loads(s["target_schools"] or "[]"),
                                               "consultants": _consultants(conn, user)})


@app.post("/students/{sid}/edit")
async def student_update(request: Request, sid: int):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    if not auth.get_student(conn, user, sid):
        raise HTTPException(404, "学生不存在或无权访问")
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    _save_student(request, conn, user, form, sid)
    flash(request, "已保存")
    return RedirectResponse(f"/students/{sid}", status_code=303)


@app.post("/students/{sid}/delete")
async def student_delete(request: Request, sid: int):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    s = auth.get_student(conn, user, sid)
    if not s:
        raise HTTPException(404, "学生不存在或无权访问")
    if (form.get("confirm") or "").strip() != s["code"]:
        raise HTTPException(400, f"请输入学生代号 {s['code']} 以确认删除。")
    conn.execute("DELETE FROM reports WHERE student_id=? AND org_id=?", (sid, user["org_id"]))
    conn.execute("DELETE FROM students WHERE id=? AND org_id=?", (sid, user["org_id"]))
    auth.audit(conn, user, "student.delete", s["code"])
    conn.commit()
    flash(request, f"已删除学生 {s['code']} 及其全部报告")
    return RedirectResponse("/students", status_code=303)


@app.get("/api/schools/{slug}/prompts")
def api_school_prompts(request: Request, slug: str):
    conn = get_conn()
    current_user(request, conn)
    return [{"prompt_text": r["prompt_text"], "word_limit": r["word_limit"], "n": r["n"], "n_acc": r["n_acc"],
             "n_rej": r["n_rej"]} for r in school_prompts(conn, slug)]


# ───────────────────────── 报告生成 ─────────────────────────
def _create_report(conn, user, req: builder.BuiltRequest, student_id: int | None) -> int:
    cur = conn.execute(
        "INSERT INTO reports(org_id, student_id, created_by, type, title, input_snapshot, status) VALUES (?,?,?,?,?,?, 'pending')",
        (user["org_id"], student_id, user["id"], req.report_type, req.title, json.dumps(req.snapshot, ensure_ascii=False)))
    conn.commit()
    auth.audit(conn, user, f"report.{req.report_type}", str(cur.lastrowid))
    conn.commit()
    return cur.lastrowid


def _launch(conn, user, req, student_id):
    org = org_of(conn, user)
    if not resolve_api_key(org):
        raise HTTPException(400, "尚未配置 Anthropic API Key。请机构管理员在「机构设置」中填写后再生成。")
    # 防连点：同一个人对同一学生的同类报告正在生成时，直接跳到那一份
    dup = conn.execute("SELECT id FROM reports WHERE org_id=? AND created_by=? AND type=? AND student_id IS ? "
                       "AND status='pending' ORDER BY id DESC LIMIT 1",
                       (user["org_id"], user["id"], req.report_type, student_id)).fetchone()
    if dup and runner.get_job(dup["id"]) is not None:
        return RedirectResponse(f"/reports/{dup['id']}", status_code=303)
    n_today = conn.execute("SELECT COUNT(*) FROM reports WHERE org_id=? AND model IS NOT 'sample' "
                           "AND created_at >= datetime('now', 'start of day')", (user["org_id"],)).fetchone()[0]
    if n_today >= config.DAILY_REPORT_LIMIT:
        raise HTTPException(429, f"本机构今天已生成 {n_today} 份报告，达到每日上限（{config.DAILY_REPORT_LIMIT}）。"
                                 "如需调高，请联系平台运营方。")
    if not req.effort or req.effort == builder.DEFAULT_EFFORT[req.report_type]:
        if org["default_effort"] == "high" and req.effort == "medium":
            req.effort = "high"
    rid = _create_report(conn, user, req, student_id)
    runner.start(rid, req, resolve_api_key(org), db_path=config.DB_PATH)
    return RedirectResponse(f"/reports/{rid}", status_code=303)


@app.post("/students/{sid}/generate/{rtype}")
async def generate_for_student(request: Request, sid: int, rtype: str):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    s = auth.get_student(conn, user, sid)
    if not s or rtype not in ("diagnosis", "activity_plan", "essay_strategy", "essay_review"):
        raise HTTPException(404, "无效请求")
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    params = {k: form.get(k) for k in ("school_slug", "prompt_text", "word_limit", "draft") if form.get(k)}
    if rtype == "essay_review" and not params.get("draft"):
        raise HTTPException(400, "请粘贴文书草稿")
    if rtype == "activity_plan":
        last = conn.execute("SELECT output_md FROM reports WHERE student_id=? AND type='diagnosis' AND status='done' "
                            "ORDER BY id DESC LIMIT 1", (sid,)).fetchone()
        if last:
            params["diagnosis_md"] = last["output_md"]
    req = builder.build(conn, rtype, s, params)
    return _launch(conn, user, req, sid)


@app.get("/reports", response_class=HTMLResponse)
def reports_list(request: Request, type: str = ""):
    conn = get_conn()
    user = current_user(request, conn)
    rows = auth.reports_for(conn, user, limit=500)
    if type:
        rows = [r for r in rows if r["type"] == type]
    return page(request, "reports.html", {"user": user, "reports": rows, "ftype": type})


@app.get("/reports/{rid}", response_class=HTMLResponse)
def report_view(request: Request, rid: int, print: int = 0, clean: int = 0):
    conn = get_conn()
    user = current_user(request, conn)
    r = auth.get_report(conn, user, rid)
    if not r:
        raise HTTPException(404, "报告不存在或无权访问")
    if r["status"] == "pending" and runner.get_job(rid) is None:
        runner.recover_orphans(conn)
        r = auth.get_report(conn, user, rid)
    org = org_of(conn, user)
    return page(request, "report_print.html" if print else "report.html",
                {"user": user, "r": r, "org": org, "snapshot": json.loads(r["input_snapshot"] or "{}"),
                 "citations": json.loads(r["citations"] or "[]"), "clean": clean})


@app.get("/reports/{rid}/edit", response_class=HTMLResponse)
def report_edit(request: Request, rid: int):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    r = auth.get_report(conn, user, rid)
    if not r or r["status"] == "pending":
        raise HTTPException(404, "报告不存在、无权访问或仍在生成中")
    return page(request, "report_edit.html", {"user": user, "r": r})


@app.post("/reports/{rid}/edit")
async def report_save(request: Request, rid: int):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    r = auth.get_report(conn, user, rid)
    if not r or r["status"] == "pending":
        raise HTTPException(404, "报告不存在、无权访问或仍在生成中")
    if form.get("restore") and r["output_original"]:
        md = r["output_original"]
    else:
        md = (form.get("output_md") or "").replace("\r\n", "\n")
    title = (form.get("title") or r["title"]).strip()[:120]
    conn.execute("UPDATE reports SET output_original=COALESCE(output_original, output_md), output_md=?, title=?, "
                 "edited_at=datetime('now') WHERE id=? AND org_id=?", (md, title, rid, user["org_id"]))
    auth.audit(conn, user, "report.edit", str(rid))
    conn.commit()
    flash(request, "已恢复为 AI 原稿" if form.get("restore") else "修改已保存（AI 原稿已保留，可随时恢复）")
    return RedirectResponse(f"/reports/{rid}", status_code=303)


@app.get("/reports/{rid}/stream")
async def report_stream(request: Request, rid: int):
    conn = get_conn()
    user = current_user(request, conn)
    if not auth.get_report(conn, user, rid):
        raise HTTPException(404)

    async def events():
        sent_len = -1
        idle = 0
        while True:
            if await request.is_disconnected():
                return
            job = runner.get_job(rid)
            if job is None:
                yield "event: done\ndata: reload\n\n"
                return
            if len(job.text) != sent_len:
                sent_len = len(job.text)
                html_ = render_md(job.text, untrusted=True)
                yield "data: " + json.dumps({"html": html_, "chars": sent_len}) + "\n\n"
                idle = 0
            if job.done:
                yield "event: done\ndata: " + json.dumps({"error": job.error}) + "\n\n"
                return
            idle += 1
            if idle % 30 == 0:
                yield ": keepalive\n\n"
            await asyncio.sleep(0.6)

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/reports/{rid}/delete")
async def report_delete(request: Request, rid: int):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    r = auth.get_report(conn, user, rid)
    if not r:
        raise HTTPException(404)
    conn.execute("DELETE FROM reports WHERE id=? AND org_id=?", (rid, user["org_id"]))
    auth.audit(conn, user, "report.delete", str(rid))
    conn.commit()
    flash(request, "报告已删除")
    return RedirectResponse(f"/students/{r['student_id']}" if r["student_id"] else "/reports", status_code=303)


# ───────────────────────── 知识库：学校 ─────────────────────────
@app.get("/library/schools", response_class=HTMLResponse)
def schools_list(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    rows = conn.execute(
        """SELECT s.*,
             (SELECT COUNT(*) FROM essays e WHERE e.school_slug=s.slug AND e.kind='supplement') AS n_supp,
             (SELECT COUNT(DISTINCT applicant_id) FROM applicant_decisions d WHERE d.school_slug=s.slug) AS n_app,
             (SELECT COUNT(*) FROM applicant_decisions d WHERE d.school_slug=s.slug AND d.result='accepted') AS n_acc,
             (SELECT COUNT(*) FROM school_profile_sections p WHERE p.school_slug=s.slug AND p.trust='verified_source') AS n_verified,
             (SELECT COUNT(*) FROM school_profile_sections p WHERE p.school_slug=s.slug) AS n_sections
           FROM schools s WHERE s.name_zh IS NOT NULL ORDER BY s.region, s.name_en""").fetchall()
    return page(request, "schools.html", {"user": user, "schools": rows})


@app.get("/library/schools/{slug}", response_class=HTMLResponse)
def school_detail(request: Request, slug: str):
    conn = get_conn()
    user = current_user(request, conn)
    s = conn.execute("SELECT * FROM schools WHERE slug=?", (slug,)).fetchone()
    if not s:
        raise HTTPException(404, "学校不存在")
    sections = conn.execute("SELECT * FROM school_profile_sections WHERE school_slug=? ORDER BY ord", (slug,)).fetchall()
    prompts = school_prompts(conn, slug)
    decisions = conn.execute(
        """SELECT d.result, a.* FROM applicant_decisions d JOIN applicants a ON a.id=d.applicant_id
           WHERE d.school_slug=? ORDER BY d.result, a.sat_total DESC""", (slug,)).fetchall()
    guides = conn.execute("SELECT * FROM supp_guides WHERE school_slug=?", (slug,)).fetchall()
    ca = conn.execute("SELECT id, title, result FROM essays WHERE kind='common_app' AND decisions LIKE ? LIMIT 30",
                      (f'%"slug": "{slug}"%',)).fetchall()
    return page(request, "school_detail.html", {"user": user, "s": s, "sections": sections, "prompts": prompts,
                                                "decisions": decisions, "guides": guides, "ca": ca})


@app.get("/library/compare", response_class=HTMLResponse)
def school_compare(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    slugs = [x for x in request.query_params.getlist("s") if x][:4]
    cols = []
    for slug in slugs:
        s = conn.execute("SELECT * FROM schools WHERE slug=?", (slug,)).fetchone()
        if not s:
            continue
        secs = {t: conn.execute("SELECT * FROM school_profile_sections WHERE school_slug=? AND section_type=? "
                                "AND trust NOT IN ('composite','simulated') ORDER BY ord LIMIT 1", (slug, t)).fetchone()
                for t in ("data", "academic", "ec", "hooks", "essay")}
        stat = conn.execute("""SELECT COUNT(*) n, SUM(result='accepted') acc, SUM(result='rejected') rej
                               FROM applicant_decisions WHERE school_slug=?""", (slug,)).fetchone()
        sat = conn.execute("""SELECT AVG(a.sat_total) FROM applicant_decisions d JOIN applicants a ON a.id=d.applicant_id
                              WHERE d.school_slug=? AND d.result='accepted' AND a.sat_total IS NOT NULL""", (slug,)).fetchone()[0]
        cols.append({"s": s, "secs": secs, "stat": stat, "sat": sat})
    return page(request, "compare.html", {"user": user, "cols": cols, "schools": schools_options(conn), "slugs": slugs})


# ───────────────────────── 知识库：文书 ─────────────────────────
@app.get("/library/essays", response_class=HTMLResponse)
def essays_list(request: Request, kind: str = "", school: str = "", result: str = "", q: str = "", prompt: str = "",
                page_no: int = 1):
    conn = get_conn()
    user = current_user(request, conn)
    where, params = ["1=1"], []
    if kind:
        where.append("e.kind=?")
        params.append(kind)
    if school:
        where.append("(e.school_slug=? OR (e.kind='common_app' AND e.decisions LIKE ?))")
        params += [school, f'%"slug": "{school}"%']
    if result:
        where.append("e.result=?")
        params.append(result)
    if prompt:
        where.append("e.prompt_text=?")
        params.append(prompt)
    if q.strip():
        from ..ai.retrieval import search_essays
        ids = search_essays(conn, q, limit=300)
        where.append(f"e.id IN ({','.join('?' * len(ids)) or 'NULL'})")
        params += ids
    per = 30
    total = conn.execute(f"SELECT COUNT(*) FROM essays e WHERE {' AND '.join(where)}", params).fetchone()[0]
    rows = conn.execute(
        f"""SELECT e.id, e.kind, e.title, e.school_slug, e.prompt_text, e.result, e.year, e.major, e.word_count,
                   substr(e.body, 1, 220) AS preview, s.name_zh, s.name_en
            FROM essays e LEFT JOIN schools s ON s.slug=e.school_slug WHERE {' AND '.join(where)}
            ORDER BY e.kind, s.name_en, e.result LIMIT ? OFFSET ?""", (*params, per, (page_no - 1) * per)).fetchall()
    prompts = school_prompts(conn, school) if school else []
    from urllib.parse import urlencode
    base_qs = urlencode({k: v for k, v in {"kind": kind, "school": school, "result": result, "q": q, "prompt": prompt}.items() if v})
    return page(request, "essays.html", {"user": user, "rows": rows, "total": total, "page_no": page_no, "per": per,
                                         "base_qs": base_qs,
                                         "f": {"kind": kind, "school": school, "result": result, "q": q, "prompt": prompt},
                                         "schools": schools_options(conn), "prompts": prompts})


@app.get("/library/essays/{eid}", response_class=HTMLResponse)
def essay_detail(request: Request, eid: str):
    conn = get_conn()
    user = current_user(request, conn)
    e = conn.execute("SELECT e.*, s.name_zh, s.name_en FROM essays e LEFT JOIN schools s ON s.slug=e.school_slug WHERE e.id=?",
                     (eid,)).fetchone()
    if not e:
        raise HTTPException(404, "文书不存在")
    same = conn.execute("SELECT id, result, major, word_count FROM essays WHERE prompt_text=? AND school_slug IS ? AND id!=? "
                        "ORDER BY result LIMIT 12", (e["prompt_text"], e["school_slug"], eid)).fetchall()
    applicant = conn.execute("SELECT * FROM applicants WHERE id=?", (e["applicant_id"],)).fetchone() if e["applicant_id"] else None
    return page(request, "essay_detail.html", {"user": user, "e": e, "same": same, "applicant": applicant})


# ───────────────────────── 知识库：申请者画像 ─────────────────────────
@app.get("/library/applicants", response_class=HTMLResponse)
def applicants_list(request: Request, mg: str = "", school: str = "", result: str = "", intl: str = "",
                    sat_min: int = 0, q: str = ""):
    conn = get_conn()
    user = current_user(request, conn)
    where, params = ["1=1"], []
    if mg:
        where.append("a.major_group=?")
        params.append(mg)
    if intl == "1":
        where.append("a.country != 'United States'")
    elif intl == "0":
        where.append("a.country = 'United States'")
    if sat_min:
        where.append("a.sat_total >= ?")
        params.append(sat_min)
    if school:
        if result:
            where.append("EXISTS (SELECT 1 FROM applicant_decisions d WHERE d.applicant_id=a.id AND d.school_slug=? AND d.result=?)")
            params += [school, result]
        else:
            where.append("EXISTS (SELECT 1 FROM applicant_decisions d WHERE d.applicant_id=a.id AND d.school_slug=?)")
            params.append(school)
    if q.strip():
        where.append("(a.major LIKE ? OR EXISTS (SELECT 1 FROM applicant_activities x WHERE x.applicant_id=a.id AND "
                     "(x.organization LIKE ? OR x.description LIKE ? OR x.position LIKE ?)))")
        params += [f"%{q}%"] * 4
    rows = conn.execute(f"SELECT a.* FROM applicants a WHERE {' AND '.join(where)} ORDER BY a.n_accepted DESC, a.sat_total DESC",
                        params).fetchall()
    tops = {}
    for r in conn.execute("""SELECT d.applicant_id, d.school_name FROM applicant_decisions d
                             JOIN schools s ON s.slug=d.school_slug WHERE d.result='accepted' AND s.name_zh IS NOT NULL"""):
        tops.setdefault(r["applicant_id"], []).append(r["school_name"])
    return page(request, "applicants.html", {"user": user, "rows": rows, "tops": tops, "schools": schools_options(conn),
                                             "f": {"mg": mg, "school": school, "result": result, "intl": intl,
                                                   "sat_min": sat_min or "", "q": q}})


@app.get("/library/applicants/{aid}", response_class=HTMLResponse)
def applicant_detail(request: Request, aid: str):
    conn = get_conn()
    user = current_user(request, conn)
    a = conn.execute("SELECT * FROM applicants WHERE id=?", (aid,)).fetchone()
    if not a:
        raise HTTPException(404, "画像不存在")
    acts = conn.execute("SELECT * FROM applicant_activities WHERE applicant_id=? ORDER BY ord", (aid,)).fetchall()
    awards = conn.execute("SELECT * FROM applicant_awards WHERE applicant_id=?", (aid,)).fetchall()
    decs = conn.execute("SELECT * FROM applicant_decisions WHERE applicant_id=? ORDER BY result", (aid,)).fetchall()
    essays = conn.execute("SELECT e.id, e.kind, e.title, e.prompt_text, e.school_slug, e.result FROM essays e WHERE applicant_id=?",
                          (aid,)).fetchall()
    return page(request, "applicant_detail.html", {"user": user, "a": a, "acts": acts, "awards": awards, "decs": decs,
                                                   "essays": essays, "scores": json.loads(a["scores_json"] or "{}")})


# ───────────────────────── 知识库：叙事案例 ─────────────────────────
@app.get("/library/cases", response_class=HTMLResponse)
def cases_list(request: Request, trust: str = ""):
    conn = get_conn()
    user = current_user(request, conn)
    rows = conn.execute("SELECT case_code, title, outcome, category, trust, source_url, source_type FROM narrative_cases "
                        + ("WHERE trust=? " if trust else "") + "ORDER BY category, case_code", ((trust,) if trust else ())).fetchall()
    return page(request, "cases.html", {"user": user, "rows": rows, "ftrust": trust})


@app.get("/library/cases/{code}", response_class=HTMLResponse)
def case_detail(request: Request, code: str):
    conn = get_conn()
    user = current_user(request, conn)
    c = conn.execute("SELECT * FROM narrative_cases WHERE case_code=?", (code,)).fetchone()
    if not c:
        raise HTTPException(404, "案例不存在")
    return page(request, "case_detail.html", {"user": user, "c": c})


# ───────────────────────── IB EE ─────────────────────────
@app.get("/ee", response_class=HTMLResponse)
def ee_home(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    samples = conn.execute("SELECT id, grade, title, session, strong_aspects FROM ee_samples ORDER BY grade, session DESC").fetchall()
    reports = [r for r in auth.reports_for(conn, user, limit=300) if r["type"] == "ee_review"][:10]
    students = auth.students_for(conn, user)
    return page(request, "ee.html", {"user": user, "samples": samples, "reports": reports, "students": students,
                                     "ai_ready": ai_ready(conn, user)})


MAX_UPLOAD = 20 * 1024 * 1024


def _extract_upload(f: UploadFile | None) -> str:
    if f is None or not f.filename:
        return ""
    name = f.filename.lower()
    if not name.endswith((".pdf", ".docx", ".txt", ".md")):
        raise HTTPException(400, "仅支持 PDF / DOCX / TXT / MD")
    data = f.file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(400, "文件超过 20MB")
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
            if len(text.strip()) < 80:
                raise HTTPException(400, "没能从 PDF 中读出文字，可能是扫描件。请直接把文字粘贴到文本框中。")
            return text
        if name.endswith(".docx"):
            import docx
            return "\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs)
        return data.decode("utf-8", errors="ignore")
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001 — 损坏 / 加密文件
        raise HTTPException(400, "文件无法读取（可能已损坏或加密）。请另存为新文件，或直接粘贴文字。")


@app.post("/ee/review")
async def ee_review(request: Request, draft: str = Form(""), stage: str = Form("提纲"), label: str = Form(""),
                    student_id: str = Form(""), file: UploadFile | None = None, csrf: str = Form(None)):
    require_csrf(request, csrf)
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    text = (draft or "").strip() or _extract_upload(file).strip()
    if len(text) < 80:
        raise HTTPException(400, "材料过短：请粘贴研究问题 + 提纲 / 草稿，或上传文件。")
    s = auth.get_student(conn, user, int(student_id)) if student_id.isdigit() else None
    req = builder.build(conn, "ee_review", s, {"draft": text[:120000], "stage": stage, "label": label.strip()})
    return _launch(conn, user, req, s["id"] if s is not None else None)


@app.get("/ee/samples/{eid}", response_class=HTMLResponse)
def ee_sample(request: Request, eid: str):
    conn = get_conn()
    user = current_user(request, conn)
    r = conn.execute("SELECT * FROM ee_samples WHERE id=?", (eid,)).fetchone()
    if not r:
        raise HTTPException(404, "样本不存在")
    return page(request, "ee_sample.html", {"user": user, "r": r})


# ───────────────────────── 获客内容 ─────────────────────────
@app.get("/marketing", response_class=HTMLResponse)
def marketing_home(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    cases = conn.execute("SELECT case_code, title, trust FROM narrative_cases WHERE trust NOT IN ('simulated','composite') "
                         "ORDER BY category, case_code").fetchall()
    reports = [r for r in auth.reports_for(conn, user, limit=300) if r["type"] == "marketing"][:10]
    return page(request, "marketing.html", {"user": user, "cases": cases, "reports": reports, "ai_ready": ai_ready(conn, user)})


@app.post("/marketing")
async def marketing_generate(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    require_write(user)
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    eids = re.findall(r"[0-9a-f]{24}", form.get("essay_ids") or "")[:8]
    codes = [c for c in form.getlist("case_codes")[:6] if conn.execute(
        "SELECT 1 FROM narrative_cases WHERE case_code=? AND trust NOT IN ('simulated','composite')", (c,)).fetchone()]
    params = {"topic": (form.get("topic") or "").strip(), "audience": form.get("audience"), "fmt": form.get("fmt"),
              "length": form.get("length"), "case_codes": codes, "essay_ids": eids}
    if not params["topic"]:
        raise HTTPException(400, "请填写主题")
    if not params["case_codes"] and not eids:
        raise HTTPException(400, "请至少选择一个案例或填入一篇文书 ID")
    req = builder.build(conn, "marketing", None, params)
    return _launch(conn, user, req, None)


# ───────────────────────── 机构设置 ─────────────────────────
@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    if not auth.is_owner(user):  # 页面含待激活成员的邀请链接，只能管理员看
        raise HTTPException(403, "仅机构管理员可查看机构设置。")
    org = org_of(conn, user)
    members = conn.execute("SELECT * FROM users WHERE org_id=? ORDER BY id", (user["org_id"],)).fetchall()
    usage = conn.execute("""SELECT COUNT(*) n, COALESCE(SUM(input_tokens),0) inp, COALESCE(SUM(output_tokens),0) outp
                            FROM reports WHERE org_id=? AND status='done' AND model IS NOT NULL AND model != 'sample'""",
                         (user["org_id"],)).fetchone()
    key = resolve_api_key(org)
    key_src = "机构设置" if org["api_key_enc"] else ("服务器环境变量" if config.ENV_API_KEY else "")
    return page(request, "settings.html", {"user": user, "org": org, "members": members, "usage": usage,
                                           "key_masked": mask_key(key), "key_src": key_src,
                                           "base_url": str(request.base_url).rstrip("/"), "model": config.DEFAULT_MODEL})


@app.post("/settings/org")
async def settings_org(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    if not auth.is_owner(user):
        raise HTTPException(403, "仅机构管理员可修改")
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    color = form.get("brand_color") or "#1f3a5f"
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        color = "#1f3a5f"
    effort = form.get("default_effort") if form.get("default_effort") in ("medium", "high") else "medium"
    conn.execute("UPDATE orgs SET name=?, brand_name=?, brand_color=?, default_effort=? WHERE id=?",
                 ((form.get("name") or "").strip() or "未命名机构", (form.get("brand_name") or "").strip(), color, effort, user["org_id"]))
    key = (form.get("api_key") or "").strip()
    if key:
        conn.execute("UPDATE orgs SET api_key_enc=? WHERE id=?", (encrypt_key(key), user["org_id"]))
        auth.audit(conn, user, "settings.api_key")
    if form.get("clear_key"):
        conn.execute("UPDATE orgs SET api_key_enc=NULL WHERE id=?", (user["org_id"],))
    conn.commit()
    flash(request, "设置已保存")
    return RedirectResponse("/settings", status_code=303)


@app.post("/settings/test-key")
async def settings_test_key(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    if not auth.is_owner(user):
        raise HTTPException(403, "仅机构管理员可操作")
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    from ..ai.client import AIUnavailable, ping
    try:
        served = await asyncio.to_thread(ping, resolve_api_key(org_of(conn, user)))
        flash(request, f"连接正常：模型 {served} 可用。")
    except AIUnavailable as e:
        flash(request, f"连接失败：{e}", "bad")
    return RedirectResponse("/settings", status_code=303)


@app.post("/settings/members")
async def settings_invite(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    if not auth.is_owner(user):
        raise HTTPException(403, "仅机构管理员可邀请成员")
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    email = (form.get("email") or "").strip().lower()
    role = form.get("role") if form.get("role") in auth.ROLES else "consultant"
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(400, "邮箱格式不正确")
    if conn.execute("SELECT 1 FROM users WHERE lower(email)=?", (email,)).fetchone():
        raise HTTPException(400, "该邮箱已存在")
    token = auth.new_token()
    conn.execute("INSERT INTO users(org_id,email,name,role,invite_token,invite_expires) "
                 f"VALUES (?,?,?,?,?, datetime('now', '+{config.INVITE_DAYS} days'))",
                 (user["org_id"], email, (form.get("name") or email.split("@")[0]).strip(), role, token))
    auth.audit(conn, user, "member.invite", email)
    conn.commit()
    flash(request, f"已创建邀请链接：{request.base_url}invite/{token}（{config.INVITE_DAYS} 天内有效，请发送给对方）")
    return RedirectResponse("/settings", status_code=303)


@app.post("/settings/members/{uid}/reset")
async def settings_reset(request: Request, uid: int):
    """重新生成邀请 / 重设密码链接：用于成员忘记密码或邀请过期。旧密码立即失效。"""
    conn = get_conn()
    user = current_user(request, conn)
    if not auth.is_owner(user):
        raise HTTPException(403, "仅机构管理员可操作")
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    m = conn.execute("SELECT * FROM users WHERE id=? AND org_id=?", (uid, user["org_id"])).fetchone()
    if not m:
        raise HTTPException(404, "成员不存在")
    token = auth.new_token()
    conn.execute(f"UPDATE users SET invite_token=?, invite_expires=datetime('now', '+{config.INVITE_DAYS} days'), "
                 "password_hash=CASE WHEN id=? THEN password_hash ELSE NULL END WHERE id=?", (token, user["id"], uid))
    auth.audit(conn, user, "member.reset", m["email"])
    conn.commit()
    flash(request, f"已为 {m['name']} 生成新的设置密码链接：{request.base_url}invite/{token}（{config.INVITE_DAYS} 天内有效）")
    return RedirectResponse("/settings", status_code=303)


@app.post("/settings/members/{uid}/toggle")
async def settings_toggle(request: Request, uid: int):
    conn = get_conn()
    user = current_user(request, conn)
    if not auth.is_owner(user) or uid == user["id"]:
        raise HTTPException(403, "无法操作")
    form = await request.form()
    require_csrf(request, form.get("csrf"))
    conn.execute("UPDATE users SET active = 1 - active WHERE id=? AND org_id=?", (uid, user["org_id"]))
    conn.commit()
    return RedirectResponse("/settings", status_code=303)


# ───────────────────────── 数据说明 ─────────────────────────
@app.get("/data", response_class=HTMLResponse)
def data_page(request: Request):
    conn = get_conn()
    user = current_user(request, conn)
    meta = {r["key"]: r["value"] for r in conn.execute("SELECT * FROM kb_meta")}
    trust = conn.execute("SELECT trust, COUNT(*) n FROM school_profile_sections GROUP BY trust").fetchall()
    ctrust = conn.execute("SELECT trust, COUNT(*) n FROM narrative_cases GROUP BY trust").fetchall()
    countries = conn.execute("SELECT country, COUNT(*) n FROM applicants GROUP BY country ORDER BY n DESC LIMIT 8").fetchall()
    years = conn.execute("SELECT application_year y, COUNT(*) n FROM applicants GROUP BY y ORDER BY y DESC").fetchall()
    return page(request, "data.html", {"user": user, "stats": json.loads(meta.get("stats", "{}")),
                                       "warnings": json.loads(meta.get("warnings", "[]")), "ingested_at": meta.get("ingested_at"),
                                       "trust_rows": trust, "ctrust": ctrust, "countries": countries, "years": years})


@app.get("/healthz")
def healthz():
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM essays").fetchone()[0]
    return {"ok": True, "essays": n}
