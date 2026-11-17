"""账号与租户：密码哈希（scrypt）、会话、CSRF、角色校验、按 org 隔离的查询。"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3

ROLES = {"owner": "机构管理员", "consultant": "顾问", "viewer": "只读（销售/新人）"}


def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${h.hex()}"


def verify_password(pw: str, stored: str | None) -> bool:
    if not stored or not stored.startswith("scrypt$"):
        return False
    _, salt_hex, h_hex = stored.split("$")
    h = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1, dklen=32)
    return hmac.compare_digest(h.hex(), h_hex)


def new_token() -> str:
    return secrets.token_urlsafe(24)


def csrf_token(session: dict) -> str:
    tok = session.get("csrf")
    if not tok:
        tok = session["csrf"] = new_token()
    return tok


def check_csrf(session: dict, submitted: str | None) -> bool:
    return bool(submitted) and hmac.compare_digest(session.get("csrf", ""), submitted)


def can_write(user) -> bool:
    return user["role"] in ("owner", "consultant")


def is_owner(user) -> bool:
    return user["role"] == "owner"


# ───────────── 租户隔离：所有学生 / 报告查询都必须经过这里 ─────────────
def students_for(conn: sqlite3.Connection, user) -> list[sqlite3.Row]:
    if user["role"] in ("owner", "viewer"):
        return conn.execute("SELECT * FROM students WHERE org_id=? ORDER BY updated_at DESC", (user["org_id"],)).fetchall()
    return conn.execute("SELECT * FROM students WHERE org_id=? AND owner_user_id=? ORDER BY updated_at DESC",
                        (user["org_id"], user["id"])).fetchall()


def get_student(conn: sqlite3.Connection, user, student_id: int):
    row = conn.execute("SELECT * FROM students WHERE id=? AND org_id=?", (student_id, user["org_id"])).fetchone()
    if row is None:
        return None
    if user["role"] == "consultant" and row["owner_user_id"] != user["id"]:
        return None
    return row


def reports_for(conn: sqlite3.Connection, user, student_id: int | None = None, limit: int = 200,
                report_id: int | None = None) -> list[sqlite3.Row]:
    sql = """SELECT r.*, s.code AS student_code, s.name AS student_name, u.name AS author
             FROM reports r LEFT JOIN students s ON s.id=r.student_id LEFT JOIN users u ON u.id=r.created_by
             WHERE r.org_id=?"""
    params: list = [user["org_id"]]
    if report_id is not None:
        sql += " AND r.id=?"
        params.append(report_id)
    if student_id is not None:
        sql += " AND r.student_id=?"
        params.append(student_id)
    if user["role"] == "consultant":
        sql += " AND (r.created_by=? OR s.owner_user_id=?)"
        params += [user["id"], user["id"]]
    sql += " ORDER BY r.id DESC LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def get_report(conn: sqlite3.Connection, user, report_id: int):
    rows = reports_for(conn, user, limit=1, report_id=report_id)
    return rows[0] if rows else None


def next_student_code(conn: sqlite3.Connection, org_id: int) -> str:
    n = conn.execute("SELECT COUNT(*) FROM students WHERE org_id=?", (org_id,)).fetchone()[0]
    while True:
        n += 1
        code = f"S{n:03d}"
        if not conn.execute("SELECT 1 FROM students WHERE org_id=? AND code=?", (org_id, code)).fetchone():
            return code


def audit(conn: sqlite3.Connection, user, action: str, detail: str = "") -> None:
    conn.execute("INSERT INTO audit_log(org_id,user_id,action,detail) VALUES (?,?,?,?)",
                 (user["org_id"] if user else None, user["id"] if user else None, action, detail[:500]))
