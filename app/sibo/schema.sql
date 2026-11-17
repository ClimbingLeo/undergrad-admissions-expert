PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ───────────── 全局知识库（只读，ingest 幂等重建） ─────────────
CREATE TABLE IF NOT EXISTS schools (
    slug        TEXT PRIMARY KEY,
    name_en     TEXT NOT NULL,
    name_zh     TEXT,
    region      TEXT,
    aliases     TEXT DEFAULT '[]',
    has_profile INTEGER DEFAULT 0
);

-- trust: verified_source | official | sponsored | composite | simulated | unsourced
CREATE TABLE IF NOT EXISTS school_profile_sections (
    id           INTEGER PRIMARY KEY,
    school_slug  TEXT NOT NULL REFERENCES schools(slug),
    ord          INTEGER NOT NULL,
    heading      TEXT NOT NULL,
    body_md      TEXT NOT NULL,
    section_type TEXT,
    trust        TEXT NOT NULL,
    source_urls  TEXT DEFAULT '[]',
    source_file  TEXT
);

CREATE TABLE IF NOT EXISTS applicants (
    id               TEXT PRIMARY KEY,
    bucket           TEXT,
    gender           TEXT,
    ethnicity        TEXT,
    country          TEXT,
    high_school_type TEXT,
    application_year TEXT,
    major            TEXT,
    major_group      TEXT,
    enrolled_at      TEXT,
    sat_total        INTEGER,
    act_composite    INTEGER,
    gpa_uw           REAL,
    gpa_w            REAL,
    class_rank       TEXT,
    scores_json      TEXT,
    source_url       TEXT,
    n_accepted       INTEGER DEFAULT 0,
    n_rejected       INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS applicant_decisions (
    applicant_id TEXT NOT NULL REFERENCES applicants(id),
    school_slug  TEXT NOT NULL,
    school_name  TEXT NOT NULL,
    result       TEXT NOT NULL,   -- accepted | rejected | waitlisted
    PRIMARY KEY (applicant_id, school_slug, result)
);

CREATE TABLE IF NOT EXISTS applicant_activities (
    id           INTEGER PRIMARY KEY,
    applicant_id TEXT NOT NULL REFERENCES applicants(id),
    ord          INTEGER,
    position     TEXT,
    organization TEXT,
    description  TEXT
);

CREATE TABLE IF NOT EXISTS applicant_awards (
    id           INTEGER PRIMARY KEY,
    applicant_id TEXT NOT NULL REFERENCES applicants(id),
    name         TEXT,
    level        TEXT
);

-- kind: common_app | supplement
CREATE TABLE IF NOT EXISTS essays (
    id           TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,
    title        TEXT,
    school_slug  TEXT,             -- supplement: 所属学校；common_app: 目标/代表学校（可空）
    prompt_key   TEXT,
    prompt_text  TEXT,
    word_limit   INTEGER,
    result       TEXT,             -- accepted | rejected | unknown
    year         TEXT,
    major        TEXT,
    stats        TEXT,
    body         TEXT NOT NULL,
    word_count   INTEGER,
    source_url   TEXT,
    applicant_id TEXT,
    decisions    TEXT DEFAULT '[]', -- common_app: [{school, slug, result}]
    source_file  TEXT
);
CREATE INDEX IF NOT EXISTS idx_essays_school ON essays(school_slug, kind);

CREATE VIRTUAL TABLE IF NOT EXISTS essays_fts USING fts5(
    id UNINDEXED, title, prompt_text, body, major, tokenize = 'trigram'
);

CREATE TABLE IF NOT EXISTS supp_guides (
    id          INTEGER PRIMARY KEY,
    school_slug TEXT NOT NULL,
    title       TEXT,
    body_md     TEXT NOT NULL,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS narrative_cases (
    case_code   TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    outcome     TEXT,             -- strong_admit | surprise_reject | typical_fail | borderline | simulated
    category    TEXT,
    body_md     TEXT NOT NULL,
    source_type TEXT,
    source_url  TEXT,
    trust       TEXT NOT NULL,
    source_file TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts USING fts5(
    case_code UNINDEXED, title, body_md, tokenize = 'trigram'
);

CREATE TABLE IF NOT EXISTS ee_samples (
    id             TEXT PRIMARY KEY,
    grade          TEXT NOT NULL,
    title          TEXT,
    session        TEXT,
    total_pages    INTEGER,
    strong_aspects TEXT,
    grade_verified INTEGER,
    excerpt        TEXT,
    url            TEXT
);

CREATE TABLE IF NOT EXISTS kb_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- ───────────── 租户数据 ─────────────
CREATE TABLE IF NOT EXISTS orgs (
    id             INTEGER PRIMARY KEY,
    name           TEXT NOT NULL,
    brand_name     TEXT,
    brand_color    TEXT DEFAULT '#1f3a5f',
    api_key_enc    TEXT,
    default_effort TEXT DEFAULT 'medium',
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    org_id        INTEGER NOT NULL REFERENCES orgs(id),
    email         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('owner', 'consultant', 'viewer')),
    password_hash TEXT,
    invite_token  TEXT,
    invite_expires TEXT,
    active        INTEGER DEFAULT 1,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY,
    org_id        INTEGER NOT NULL REFERENCES orgs(id),
    owner_user_id INTEGER REFERENCES users(id),
    name          TEXT NOT NULL,
    aliases       TEXT,                   -- 英文名 / 小名 / 拼音，逗号分隔；同样会被替换为代号
    code          TEXT NOT NULL,          -- 送入 AI 的代号，替代真名
    grade_level   TEXT,
    school        TEXT,
    curriculum    TEXT,
    gpa           TEXT,
    tests         TEXT,
    intended_major TEXT,
    major_group   TEXT,
    target_schools TEXT DEFAULT '[]',
    activities    TEXT,
    awards        TEXT,
    background    TEXT,
    budget_notes  TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reports (
    id             INTEGER PRIMARY KEY,
    org_id         INTEGER NOT NULL REFERENCES orgs(id),
    student_id     INTEGER REFERENCES students(id),
    created_by     INTEGER REFERENCES users(id),
    type           TEXT NOT NULL,   -- diagnosis | activity_plan | essay_strategy | essay_review | ee_review | marketing
    title          TEXT NOT NULL,
    input_snapshot TEXT,
    output_md      TEXT,
    citations      TEXT DEFAULT '[]',
    model          TEXT,
    input_tokens   INTEGER,
    output_tokens  INTEGER,
    status         TEXT DEFAULT 'done',  -- pending | done | error
    error          TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY,
    org_id     INTEGER,
    user_id    INTEGER,
    action     TEXT NOT NULL,
    detail     TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
