"""平台运维命令行。

  python -m sibo.cli init                     # 建表 + 入库 + （空库时）写入演示机构
  python -m sibo.cli ingest [素材目录]          # 重建知识库
  python -m sibo.cli create-org "机构名" owner@x.com "管理员姓名"   # 开通新机构，打印邀请链接
  python -m sibo.cli seed-demo                # 写入 / 重置演示机构
  python -m sibo.cli set-password email 新密码
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import auth, config, db
from .ingest.parsers import major_group
from .ingest.run import ingest

DEMO_ORG = "思博杂学社（演示机构）"
DEMO_USERS = [
    ("owner@demo.sibo", "陈主任", "owner"),
    ("consultant@demo.sibo", "林顾问", "consultant"),
    ("viewer@demo.sibo", "新人小周", "viewer"),
]
DEMO_PASSWORD = "demo1234"

DEMO_STUDENTS = [
    dict(name="王子睿", aliases="Zirui Wang, Ray", grade_level="G11", school="上海某 IB 国际学校", curriculum="IB（HL 数学 AA / 物理 / 经济）",
         gpa="IB 预估 42/45；校内 GPA 3.92 UW", tests="SAT 1540（M 800 / RW 740）；TOEFL 113",
         intended_major="Computer Science", target_schools=["mit", "stanford", "cmu", "uc_berkeley", "uiuc", "gatech"],
         activities="- 校机器人社社长（G10–G12）：带队参加 FRC 区域赛，负责视觉识别模块\n- AMC 12 校队，校内数学社讲师（每周给 G9 上课）\n- 暑期在高校实验室参与图像分割项目（4 周，帮忙标注与跑基线）\n- 自学开发「校园失物招领」小程序，约 400 名同学使用\n- 钢琴十级，偶尔在校音乐会伴奏",
         awards="- AMC 12：114.0 分（2025），AIME 资格\n- FRC 区域赛 Engineering Inspiration Award 团队奖\n- 校级优秀学生",
         background="父母均为工程师。在上海长大，周末常陪外婆去社区医院，发现老人看不懂自助挂号机，曾帮她们一台台操作。对「技术如何服务不会用技术的人」有真实兴趣，但还没有把它变成项目。性格偏内向，动手能力强。",
         budget_notes="暑期可投入 6–8 周；活动预算中等，不倾向高价付费科研"),
    dict(name="李若溪", aliases="Ruoxi Li", grade_level="G11", school="北京某公立校国际部", curriculum="AP（已修 6 门）",
         gpa="3.88 UW / 4.4 W", tests="SAT 1500（RW 760 / M 740）；TOEFL 110；AP 5×4",
         intended_major="Economics / Public Policy", target_schools=["penn", "columbia", "georgetown", "nyu", "bu", "uw"],
         activities="- 模拟联合国：副秘书长，组织校际会议 200 人\n- 校辩论队（英辩），省级赛四强\n- 在社区做留守儿童线上英语辅导（1 年，每周 2 小时）\n- 经济学社创始人，写了 6 篇校刊经济评论\n- 参加某名校经济学夏校（2 周）",
         awards="- 全国中学生英语辩论赛省级四强\n- NEC 全美经济学挑战赛（中国赛区）铜奖",
         background="父亲在县城经营一家小型家具厂，疫情后订单下滑，她帮忙整理过账本和电商数据。对「小微企业的融资困难」有切身观察，但目前的活动更像标准的「模联 + 辩论 + 夏校」组合。",
         budget_notes="预算较充足；希望活动有实际影响力而不只是证书"),
    dict(name="张一鸣", grade_level="G10", school="深圳某民办双语学校", curriculum="A-Level（数学 / 生物 / 化学 / 进阶数学）",
         gpa="IGCSE 6A* 2A", tests="尚未考 SAT；雅思 7.0", intended_major="Biology / Pre-med",
         target_schools=["jhu", "duke", "emory", "ucl", "imperial", "hku"],
         activities="- 校生物社成员，参与校园植物普查\n- 在宠物医院做志愿者（每周六，半年）\n- 喜欢拍摄昆虫微距照片，在小红书有 3000 粉丝",
         awards="- BBO 英国生物奥赛 Bronze",
         background="家里养了很多爬宠，从小对动物行为好奇。母亲是护士。目前活动零散，没有形成主线；家长倾向医学方向，但学生本人更喜欢野外和生态。",
         budget_notes="时间充裕（G10），愿意做长期项目"),
]


def seed_demo(conn) -> int:
    row = conn.execute("SELECT id FROM orgs WHERE name=?", (DEMO_ORG,)).fetchone()
    if row:
        org_id = row["id"]
    else:
        org_id = conn.execute("INSERT INTO orgs(name, brand_name, brand_color) VALUES (?,?,?)",
                              (DEMO_ORG, "思博杂学社", "#1f3a5f")).lastrowid
    uids = {}
    for email, name, role in DEMO_USERS:
        u = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if u:
            uids[role] = u["id"]
            continue
        uids[role] = conn.execute("INSERT INTO users(org_id,email,name,role,password_hash) VALUES (?,?,?,?,?)",
                                  (org_id, email, name, role, auth.hash_password(DEMO_PASSWORD))).lastrowid
    for i, s in enumerate(DEMO_STUDENTS):
        if conn.execute("SELECT 1 FROM students WHERE org_id=? AND name=?", (org_id, s["name"])).fetchone():
            continue
        owner = uids["consultant"] if i < 2 else uids["owner"]
        conn.execute(
            """INSERT INTO students(org_id, owner_user_id, name, aliases, code, grade_level, school, curriculum, gpa, tests,
               intended_major, major_group, target_schools, activities, awards, background, budget_notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (org_id, owner, s["name"], s.get("aliases"), auth.next_student_code(conn, org_id), s["grade_level"], s["school"], s["curriculum"],
             s["gpa"], s["tests"], s["intended_major"], major_group(s["intended_major"]), json.dumps(s["target_schools"]),
             s["activities"], s["awards"], s["background"], s["budget_notes"]))
    conn.commit()
    load_sample_reports(conn, org_id, uids)
    return org_id


SAMPLES_DIR = Path(__file__).parent / "samples"


def load_sample_reports(conn, org_id: int, uids: dict) -> int:
    """samples/*.json：预先生成的示例报告，让没有 API Key 的演示环境也能看到完整效果。"""
    n = 0
    for f in sorted(SAMPLES_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if conn.execute("SELECT 1 FROM reports WHERE org_id=? AND title=?", (org_id, d["title"])).fetchone():
            continue
        sid = None
        if d.get("student_name"):
            r = conn.execute("SELECT id FROM students WHERE org_id=? AND name=?", (org_id, d["student_name"])).fetchone()
            sid = r["id"] if r else None
        from .ai.citations import validate, allowed_ids_from_context
        md, cites, warns = validate(d["output_md"], set(d.get("allowed_ids") or allowed_ids_from_context(d["output_md"])))
        conn.execute(
            """INSERT INTO reports(org_id, student_id, created_by, type, title, input_snapshot, output_md, citations, model,
               status, error) VALUES (?,?,?,?,?,?,?,?, 'sample', 'done', ?)""",
            (org_id, sid, uids.get(d.get("author_role", "consultant")), d["type"], d["title"],
             json.dumps(d.get("snapshot", {}), ensure_ascii=False), md, json.dumps(cites, ensure_ascii=False),
             "\n".join(["示例报告：由系统预生成，用于演示。"] + warns)))
        n += 1
    conn.commit()
    return n


def bootstrap(verbose: bool = False) -> None:
    """应用启动时调用：建表；知识库为空则入库；没有任何机构则写入演示机构。"""
    conn = db.connect()
    db.init_schema(conn)
    if not conn.execute("SELECT 1 FROM kb_meta WHERE key='stats'").fetchone():
        ingest(conn, config.SOURCE_ROOT, verbose=verbose)
    if not conn.execute("SELECT 1 FROM orgs").fetchone() and config.SEED_DEMO:
        seed_demo(conn)
    from .ai.runner import recover_orphans
    n = recover_orphans(conn)
    if n:
        print(f"[sibo] {n} 份上次未完成的报告已标记为中断")
    conn.close()


def main(argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return
    cmd, args = argv[0], argv[1:]
    conn = db.connect()
    db.init_schema(conn)
    if cmd == "init":
        ingest(conn, config.SOURCE_ROOT)
        seed_demo(conn)
        print(f"完成。演示账号：{', '.join(u[0] for u in DEMO_USERS)}，密码 {DEMO_PASSWORD}")
    elif cmd == "ingest":
        ingest(conn, Path(args[0]) if args else config.SOURCE_ROOT)
    elif cmd == "seed-demo":
        seed_demo(conn)
        print("演示机构已就绪")
    elif cmd == "create-org":
        name, email, admin = args[0], args[1], (args[2] if len(args) > 2 else args[1].split("@")[0])
        org_id = conn.execute("INSERT INTO orgs(name, brand_name) VALUES (?,?)", (name, name)).lastrowid
        token = auth.new_token()
        conn.execute("INSERT INTO users(org_id,email,name,role,invite_token,invite_expires) "
                     f"VALUES (?,?,?,?,?, datetime('now', '+{config.INVITE_DAYS} days'))",
                     (org_id, email.lower(), admin, "owner", token))
        conn.commit()
        print(f"机构「{name}」已开通。请把邀请链接发给管理员（{config.INVITE_DAYS} 天内有效）：<站点地址>/invite/{token}")
    elif cmd == "set-password":
        conn.execute("UPDATE users SET password_hash=?, invite_token=NULL WHERE lower(email)=lower(?)",
                     (auth.hash_password(args[1]), args[0]))
        conn.commit()
        print("已更新")
    else:
        print(__doc__)
    conn.close()


if __name__ == "__main__":
    main(sys.argv[1:])
