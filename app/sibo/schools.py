"""学校名归一化：把各数据源里五花八门的校名统一成 slug。

CANON 是人工维护的核心校表（slug, 英文名, 中文名, 地区, 别名...）。
不在表里的学校自动生成 slug（例如 Clastify 里出现的长尾学校）。
"""
from __future__ import annotations

import re

# slug, name_en, name_zh, region, aliases(英文/目录名/文件名片段)
CANON: list[tuple[str, str, str, str, list[str]]] = [
    ("harvard", "Harvard University", "哈佛大学", "US", ["harvard"]),
    ("stanford", "Stanford University", "斯坦福大学", "US", ["stanford"]),
    ("mit", "Massachusetts Institute of Technology", "麻省理工学院", "US", ["mit"]),
    ("yale", "Yale University", "耶鲁大学", "US", ["yale"]),
    ("princeton", "Princeton University", "普林斯顿大学", "US", ["princeton"]),
    ("columbia", "Columbia University", "哥伦比亚大学", "US", ["columbia"]),
    ("penn", "University of Pennsylvania", "宾夕法尼亚大学", "US", ["upenn", "penn"]),
    ("brown", "Brown University", "布朗大学", "US", ["brown"]),
    ("cornell", "Cornell University", "康奈尔大学", "US", ["cornell"]),
    ("dartmouth", "Dartmouth College", "达特茅斯学院", "US", ["dartmouth"]),
    ("uchicago", "University of Chicago", "芝加哥大学", "US", ["uchicago"]),
    ("caltech", "California Institute of Technology", "加州理工学院", "US", ["caltech"]),
    ("duke", "Duke University", "杜克大学", "US", ["duke"]),
    ("jhu", "Johns Hopkins University", "约翰霍普金斯大学", "US", ["jhu", "johns_hopkins"]),
    ("northwestern", "Northwestern University", "西北大学", "US", ["northwestern"]),
    ("rice", "Rice University", "莱斯大学", "US", ["rice"]),
    ("vanderbilt", "Vanderbilt University", "范德堡大学", "US", ["vanderbilt"]),
    ("washu", "Washington University in St. Louis", "圣路易斯华盛顿大学", "US", ["washu"]),
    ("notre_dame", "University of Notre Dame", "圣母大学", "US", ["notre_dame"]),
    ("cmu", "Carnegie Mellon University", "卡内基梅隆大学", "US", ["cmu"]),
    ("emory", "Emory University", "埃默里大学", "US", ["emory"]),
    ("georgetown", "Georgetown University", "乔治城大学", "US", ["georgetown"]),
    ("unc", "University of North Carolina at Chapel Hill", "北卡罗来纳大学教堂山分校", "US", ["unc"]),
    ("uva", "University of Virginia", "弗吉尼亚大学", "US", ["uva"]),
    ("umich", "University of Michigan - Ann Arbor", "密歇根大学安娜堡分校", "US", ["umich"]),
    ("uc_berkeley", "University of California, Berkeley", "加州大学伯克利分校", "US", ["uc_berkeley", "ucb"]),
    ("ucla", "University of California, Los Angeles", "加州大学洛杉矶分校", "US", ["ucla"]),
    ("ucsd", "University of California, San Diego", "加州大学圣地亚哥分校", "US", ["ucsd"]),
    ("uci", "University of California, Irvine", "加州大学尔湾分校", "US", ["uci"]),
    ("ucd", "University of California, Davis", "加州大学戴维斯分校", "US", ["uc_davis"]),
    ("ucsb", "University of California, Santa Barbara", "加州大学圣塔芭芭拉分校", "US", ["ucsb"]),
    ("usc", "University of Southern California", "南加州大学", "US", ["usc"]),
    ("nyu", "New York University", "纽约大学", "US", ["nyu"]),
    ("tufts", "Tufts University", "塔夫茨大学", "US", ["tufts"]),
    ("bc", "Boston College", "波士顿学院", "US", ["boston_college"]),
    ("bu", "Boston University", "波士顿大学", "US", ["boston_university", "bu"]),
    ("northeastern", "Northeastern University", "东北大学（美国）", "US", ["northeastern"]),
    ("gatech", "Georgia Institute of Technology", "佐治亚理工学院", "US", ["georgia_tech"]),
    ("uiuc", "University of Illinois at Urbana-Champaign", "伊利诺伊大学厄巴纳-香槟分校", "US", ["uiuc"]),
    ("ut_austin", "University of Texas at Austin", "得克萨斯大学奥斯汀分校", "US", ["ut_austin"]),
    ("uw_madison", "University of Wisconsin - Madison", "威斯康星大学麦迪逊分校", "US", ["uw_madison"]),
    ("uw", "University of Washington", "华盛顿大学", "US", ["uw_university_of_washington"]),
    ("umd", "University of Maryland at College Park", "马里兰大学帕克分校", "US", ["umd"]),
    ("uf", "University of Florida", "佛罗里达大学", "US", ["uf"]),
    ("purdue", "Purdue University", "普渡大学", "US", ["purdue"]),
    ("osu", "Ohio State University", "俄亥俄州立大学", "US", ["ohio_state"]),
    ("rutgers", "Rutgers, The State University of New Jersey - New Brunswick", "罗格斯大学", "US", ["rutgers"]),
    ("oxford", "University of Oxford", "牛津大学", "UK", ["oxford"]),
    ("cambridge", "University of Cambridge", "剑桥大学", "UK", ["cambridge"]),
    ("imperial", "Imperial College London", "帝国理工学院", "UK", ["imperial"]),
    ("ucl", "University College London", "伦敦大学学院", "UK", ["ucl"]),
    ("lse", "London School of Economics", "伦敦政治经济学院", "UK", ["lse"]),
    ("edinburgh", "University of Edinburgh", "爱丁堡大学", "UK", ["edinburgh"]),
    ("manchester", "University of Manchester", "曼彻斯特大学", "UK", ["manchester"]),
    ("eth", "ETH Zurich", "苏黎世联邦理工学院", "EU", ["eth"]),
    ("hku", "University of Hong Kong", "香港大学", "HK", ["hku"]),
    ("cuhk", "Chinese University of Hong Kong", "香港中文大学", "HK", ["cuhk"]),
    ("hkust", "Hong Kong University of Science and Technology", "香港科技大学", "HK", ["hkust"]),
    ("polyu", "Hong Kong Polytechnic University", "香港理工大学", "HK", ["polyu"]),
    ("cityu", "City University of Hong Kong", "香港城市大学", "HK", ["cityu"]),
]

_BY_NAME: dict[str, str] = {}
_BY_ALIAS: dict[str, str] = {}
for slug, en, zh, region, aliases in CANON:
    _BY_NAME[en.lower()] = slug
    _BY_NAME[zh] = slug
    for a in aliases:
        _BY_ALIAS[a.lower()] = slug

# Clastify 里的同校异名
_EXTRA_NAMES = {
    "the tulane university of new orleans": "tulane",
    "university of california system": "uc_system",
    "rutgers university": "rutgers",
    "university of illinois urbana-champaign": "uiuc",
    "university of wisconsin-madison": "uw_madison",
    "university of maryland": "umd",
    "university of michigan": "umich",
}
_BY_NAME.update(_EXTRA_NAMES)

_ENROLLED_RE = re.compile(r"\s*(\*\*)?\(enrolled\)(\*\*)?\s*$", re.I)


def clean_name(name: str) -> tuple[str, bool]:
    """去掉 '(Enrolled)' 等标记，返回 (干净校名, 是否就读)。"""
    name = name.strip()
    enrolled = bool(_ENROLLED_RE.search(name))
    name = _ENROLLED_RE.sub("", name).strip().strip("*").strip()
    return name, enrolled


def auto_slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:60] or "unknown"


def resolve(name: str) -> str:
    """任意校名 / 目录名 → slug。"""
    name, _ = clean_name(name)
    low = name.lower()
    if low in _BY_NAME:
        return _BY_NAME[low]
    if low in _BY_ALIAS:
        return _BY_ALIAS[low]
    return auto_slug(name)


def canon_rows():
    for slug, en, zh, region, aliases in CANON:
        yield slug, en, zh, region, aliases


def resolve_profile_filename(stem: str) -> str | None:
    """学校档案文件名（如 'UCL_University_College_London'）→ slug。"""
    low = stem.lower()
    # 精确前缀优先（长别名先匹配，避免 'uw' 抢走 'uw_madison'）
    cands = sorted(_BY_ALIAS.items(), key=lambda kv: -len(kv[0]))
    for alias, slug in cands:
        if low == alias or low.startswith(alias + "_"):
            return slug
    for slug, en, *_ in CANON:
        if en.lower().replace(" ", "_") in low:
            return slug
    return None
