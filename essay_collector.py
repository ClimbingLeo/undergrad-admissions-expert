#!/usr/bin/env python3
"""
Essay Collector & Pattern Analyzer
Collects publicly available admission essays and analyzes patterns
for a given school. Does NOT reproduce full essay text — outputs
structural and stylistic analysis only.

Sources (in priority order):
  1. School official "Essays That Worked" pages
  2. Reddit posts with shared essays (r/ApplyingToCollege, r/collegeresults)
  3. CollegeVine public essay examples
  4. Other public essay databases

Usage:
  python3 essay_collector.py --school "Johns Hopkins University"
  python3 essay_collector.py --school "University of Chicago"
  python3 essay_collector.py --school "MIT" --json
"""

import argparse
import json
import re
import sys
import time
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip3 install requests --break-system-packages")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Clawdbot/1.0; educational research)"
}

REQUEST_DELAY = 1.5  # seconds between requests

# ── Official "Essays That Worked" registry ────────────────────────────────────
# Schools that publish official essay examples. Verified as of 2024-25 cycle.

OFFICIAL_ESSAY_SOURCES = {
    "Johns Hopkins University": {
        "url": "https://apply.jhu.edu/apply/essays-that-worked/",
        "type": "official",
        "notes": "JHU publishes ~10 full essays per cycle with admitted student context",
    },
    "Tufts University": {
        "url": "https://admissions.tufts.edu/blogs/jumbo-talk/post/essays-that-worked/",
        "type": "official",
        "notes": "Tufts publishes supplemental essay examples",
    },
    "Hamilton College": {
        "url": "https://www.hamilton.edu/admission/essays-that-worked",
        "type": "official",
        "notes": "Full essays with brief admission committee commentary",
    },
    "Connecticut College": {
        "url": "https://www.conncoll.edu/admission/essays-that-worked/",
        "type": "official",
        "notes": "Supplement essays with themes noted",
    },
    "University of Pennsylvania": {
        "url": "https://admissions.upenn.edu/admissions-and-financial-aid/what-penn-looks-for/essays-that-worked",
        "type": "official",
        "notes": "Penn publishes ~8-12 essays per cycle",
    },
    "MIT": {
        "url": "https://mitadmissions.org/apply/process/essays/",
        "type": "official",
        "notes": "MIT publishes essay examples with context from admissions",
    },
    "Vanderbilt University": {
        "url": "https://admissions.vanderbilt.edu/vandybloggers/essays-that-rocked/",
        "type": "official",
        "notes": "Essays That Rocked series",
    },
    "University of Chicago": {
        "url": "https://collegeadmissions.uchicago.edu/apply/extended-essay",
        "type": "official_prompts",
        "notes": "UChicago publishes Extended Essay prompts; community discussions on r/UChicago",
        "supplemental": "https://www.reddit.com/r/ApplyingToCollege/search.json?q=UChicago+extended+essay+examples&restrict_sr=false&sort=top"
    },
    "Carnegie Mellon University": {
        "url": None,
        "type": "community",
        "notes": "CMU does not publish official examples; see Reddit and CollegeVine",
    },
    "Stanford University": {
        "url": None,
        "type": "community",
        "notes": "Stanford does not publish official examples; community sources below",
        "community_sources": [
            "https://www.collegeadvisor.com/essay-guides/stanford-essays-examples/",
            "https://blog.collegevine.com/stanford-essay-example",
            "https://www.acescollegeessaycoaching.com/blog/stanford-roommate-essay-guide",
            "https://www.shemmassianconsulting.com/blog/how-to-get-into-stanford",
        ],
    },
}

# Reddit search queries for essay examples per school type
ESSAY_REDDIT_QUERIES = [
    '"{school}" essay example accepted 2024 OR 2025',
    '"{school}" college essay worked admitted',
    '"{school}" supplement essay tips theme',
    '"{school}" extended essay successful',
]

# CollegeVine essay search (public, no login required for some)
COLLEGEVINE_SEARCH = "https://www.collegevine.com/essays?schoolName={query}"


# ── Fetching helpers ──────────────────────────────────────────────────────────

def safe_fetch(url: str, timeout: int = 15) -> str | None:
    """Fetch URL, return text or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  Warning: fetch failed for {url}: {e}", file=sys.stderr)
        return None


def reddit_search_essays(school_name: str, limit: int = 20) -> list[dict]:
    """Search Reddit for essay examples related to a school."""
    results = []
    seen_ids = set()

    subreddits = ["ApplyingToCollege", "collegeresults", "chanceme"]
    queries = [q.format(school=school_name) for q in ESSAY_REDDIT_QUERIES[:2]]

    for sub in subreddits:
        for query in queries:
            url = f"https://www.reddit.com/r/{sub}/search.json"
            params = {
                "q": query,
                "sort": "top",
                "t": "all",
                "limit": 15,
                "restrict_sr": "true",
            }
            try:
                resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
                resp.raise_for_status()
                posts = resp.json().get("data", {}).get("children", [])
                for p in posts:
                    d = p.get("data", {})
                    pid = d.get("id")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        results.append(d)
            except Exception as e:
                print(f"  Warning: Reddit search failed: {e}", file=sys.stderr)

            time.sleep(REQUEST_DELAY)

        if len(results) >= limit:
            break

    return results[:limit]


# ── Pattern analysis ──────────────────────────────────────────────────────────

def classify_essay_topic(text: str) -> str:
    """Classify essay into broad topic category."""
    text_lower = text.lower()

    topic_patterns = {
        "Intellectual curiosity / academic passion": [
            r'\b(research|lab|experiment|thesis|theory|discover|curious|fascinated)\b',
            r'\b(book|reading|math|science|philosophy|literature)\b',
        ],
        "Identity / cultural background": [
            r'\b(culture|heritage|immigrant|language|family background|tradition)\b',
            r'\b(identity|who i am|where i come from)\b',
        ],
        "Overcoming challenge / adversity": [
            r'\b(overcome|challenge|struggle|obstacle|failure|setback|resilience)\b',
            r'\b(difficult|hard time|dark period|depression|anxiety)\b',
        ],
        "Community / leadership / service": [
            r'\b(community|volunteer|leader|captain|founded|organized|impact)\b',
            r'\b(service|mentor|teach|coach|change)\b',
        ],
        "Creative pursuit / passion project": [
            r'\b(music|art|theater|film|write|create|design|build|code)\b',
            r'\b(passion|love for|years of|dedicated)\b',
        ],
        "Quirky / intellectual exercise (UChicago-style)": [
            r'\b(paradox|thought experiment|if you could|imagine|what if)\b',
            r'\b(unconventional|unusual|weird|eccentric)\b',
        ],
        "Person who influenced you": [
            r'\b(mentor|teacher|parent|grandparent|inspired me|changed my)\b',
        ],
        "Place / object / experience": [
            r'\b(place|object|moment|memory|childhood|grew up)\b',
        ],
    }

    scores = {}
    for topic, patterns in topic_patterns.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 1
        if score > 0:
            scores[topic] = score

    if not scores:
        return "Unclear / Generic"
    return max(scores, key=scores.get)


def extract_essay_length(text: str) -> int | None:
    """Estimate word count of an essay excerpt."""
    words = text.split()
    return len(words) if len(words) > 20 else None


def analyze_writing_style(text: str) -> list[str]:
    """Detect notable writing style features."""
    features = []
    text_lower = text.lower()

    if re.search(r'^(I |It |The |When |Every )', text[:50]):
        features.append("Opens with immediate scene or statement")
    if re.search(r'\b(anaphora|repetition)\b|\b(\w+)[.,]\s+\1\b', text_lower):
        features.append("Uses repetition/anaphora for emphasis")
    if text.count('"') >= 4:
        features.append("Heavy use of dialogue")
    if re.search(r'\.\s+[A-Z][a-z]', text) and len(text.split('.')) > 8:
        features.append("Short, punchy sentences")
    if any(c in text for c in ['—', '–', '…']):
        features.append("Uses em-dash or ellipsis for rhythm")
    if re.search(r'\b(however|nevertheless|although|despite|yet)\b', text_lower):
        features.append("Explicit contrast/reflection structure")
    if re.search(r'\b(now i know|i realized|i learned|i understand now)\b', text_lower):
        features.append("Explicit lesson/epiphany moment")

    return features


def parse_reddit_essay_post(post: dict, school_name: str) -> dict | None:
    """Extract essay metadata from a Reddit post."""
    title  = post.get("title", "")
    body   = post.get("selftext", "")
    full   = f"{title}\n{body}"
    post_id = post.get("id", "")
    url    = f"https://www.reddit.com{post.get('permalink', '')}"

    # Check school relevance
    if school_name.lower() not in full.lower():
        # Try aliases
        from collegeresults_scraper import school_variants
        variants = school_variants(school_name)
        if not any(v.lower() in full.lower() for v in variants):
            return None

    # Look for actual essay content markers
    has_essay = bool(re.search(
        r'(my essay|here is|here\'s|i wrote|word for word|essay:|essay below)',
        full.lower()
    ))

    topic = classify_essay_topic(full)
    style = analyze_writing_style(body)
    wc    = extract_essay_length(body)

    # Extract admission result if mentioned alongside essay
    result = None
    if re.search(r'\b(accepted|admitted|got in)\b', full.lower()):
        result = "Accepted"
    elif re.search(r'\b(rejected|denied)\b', full.lower()):
        result = "Rejected"

    return {
        "type":          "reddit",
        "url":           url,
        "platform":      f"Reddit r/{post.get('subreddit', '?')}",
        "title":         title,
        "has_full_essay": has_essay,
        "result":        result,
        "topic_category": topic,
        "style_features": style,
        "word_count_est": wc,
        "excerpt":       body[:300].replace("\n", " "),
        "school":        school_name,
    }


# ── Main collector ────────────────────────────────────────────────────────────

def collect_essays(school_name: str, verbose: bool = True) -> dict:
    """
    Main entry point. Returns structured essay analysis for a school.
    """
    result = {
        "school":           school_name,
        "official_source":  None,
        "essay_samples":    [],
        "pattern_analysis": {},
        "notes":            [],
    }

    # Step 1: Check official sources
    official = OFFICIAL_ESSAY_SOURCES.get(school_name)
    if official:
        result["official_source"] = official
        result["notes"].append(
            f"Official essay examples available at: {official['url']}" 
            if official["url"] else official["notes"]
        )
        if verbose:
            print(f"  Official source: {official.get('url', 'None')}")
    else:
        result["notes"].append(
            "No known official essay publication. Using community sources."
        )
        if verbose:
            print(f"  No official essay source registered for {school_name}")

    # Step 2: Reddit essay posts
    if verbose:
        print("  Searching Reddit for essay examples...")

    reddit_posts = reddit_search_essays(school_name, limit=25)
    parsed = []
    for post in reddit_posts:
        essay = parse_reddit_essay_post(post, school_name)
        if essay:
            parsed.append(essay)

    result["essay_samples"] = parsed
    if verbose:
        print(f"  Found {len(parsed)} relevant Reddit essay posts")

    # Step 3: Pattern analysis
    result["pattern_analysis"] = analyze_patterns(school_name, parsed, official)

    return result


def analyze_patterns(school_name: str, samples: list[dict],
                     official_info: dict | None) -> dict:
    """
    Analyze collected essay samples to extract patterns.
    """
    patterns = {
        "sample_count":         len(samples),
        "topic_distribution":   {},
        "style_signals":        [],
        "school_specific_tips": [],
        "avoid_patterns":       [],
    }

    # Topic distribution
    topic_counts = {}
    for s in samples:
        t = s.get("topic_category", "Unknown")
        topic_counts[t] = topic_counts.get(t, 0) + 1
    patterns["topic_distribution"] = dict(
        sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    )

    # Aggregate style features
    style_freq = {}
    for s in samples:
        for feat in s.get("style_features", []):
            style_freq[feat] = style_freq.get(feat, 0) + 1
    patterns["style_signals"] = [
        f for f, c in sorted(style_freq.items(), key=lambda x: x[1], reverse=True)
        if c >= 2  # only report if seen in 2+ samples
    ]

    # School-specific knowledge
    school_tips = {
        "University of Chicago": [
            "Extended Essay is the primary differentiator — creativity and intellectual depth required",
            "Prompt selection matters: choose the one that showcases genuine curiosity, not the 'easiest'",
            "Common trap: treating the prompt as a conventional personal statement",
            "Successful essays often subvert or interrogate the prompt itself",
            "Why UChicago essay: specificity required (name specific courses, professors, programs)",
        ],
        "MIT": [
            "Five Activity essays: show personality and range, not just achievement lists",
            "MIT essay 1 ('What do you do for fun?'): playful, genuine — not impressive-sounding",
            "Avoid lab report style writing; MIT wants to see a human, not a resume",
            "Challenge essay: how you solved a problem is more important than what problem",
        ],
        "Stanford University": [
            "2025-26 三篇 short essays: (1) Intellectual Vitality, (2) Roommate letter, (3) Distinctive contribution",
            "Intellectual Vitality: AO 内部有 IV score — 从一个具体小事切入，展示思维过程，而非'我爱CS'式的宏观叙述",
            "Roommate letter: 必须像一个真实的18岁学生写的，不能是personal statement语气；写生活习惯和怪癖而非成就",
            "Distinctive contribution: '我能给Stanford什么'，而非'Stanford能给我什么'；不要重复Common App内容",
            "短答（50字）: 避免抽象概念（'family', 'love'），用具体物件/时刻/地点",
            "Stanford不发布官方Essays That Worked，社区来源: collegeadvisor.com, collegevine.com, acescollegeessaycoaching.com",
        ],
        "Harvard University": [
            "No set supplement prompts; essays should complement, not repeat the application",
            "Unusual extracurricular essay: the point is the unusual activity, not the lesson",
        ],
        "Johns Hopkins University": [
            "JHU publishes Essays That Worked annually — read them before writing",
            "Why JHU: extremely specific (Krieger/Whiting school, specific research, specific profs)",
            "Intellectual interests essay: go deep on one thing, not broad overview",
        ],
        "Carnegie Mellon University": [
            "CMU essay should reflect understanding of the specific program, not generic STEM passion",
            "SCS applicants: show you've thought about CS beyond competitive programming",
            "Creative writing programs: portfolio matters more than essay style",
        ],
    }

    if school_name in school_tips:
        patterns["school_specific_tips"] = school_tips[school_name]

    # Universal avoid patterns
    patterns["avoid_patterns"] = [
        "Mission trip narrative without reflection on power dynamics",
        "'I want to help people' without specific mechanism",
        "Sports injury as primary challenge essay unless extraordinarily written",
        "First paragraph that is entirely scene-setting without a hook",
        "Listing accomplishments instead of revealing character",
        "Ending with 'and that's why I want to attend [school]'",
        "Using the word 'passionate' or 'passion' more than once",
    ]

    # Add school-specific avoids
    school_avoids = {
        "University of Chicago": [
            "Treating Extended Essay like a standard Why School essay",
            "Choosing the most obscure prompt to seem interesting, then writing generically",
        ],
        "MIT": [
            "Turning the 'fun' essay into a humble-brag about achievements",
            "Writing about AI/robots as your passion without specific technical depth",
        ],
        "Stanford University": [
            "Roommate letter that reads like a personal statement (最常见错误)",
            "Intellectual Vitality essay covering your entire academic journey — pick ONE thing",
            "Roommate letter 过度承诺'我们要成为最好的朋友'——实际上Stanford不提前告知室友信息",
            "Distinctive contribution 重复 Common App essay 已写过的内容",
            "短答用抽象词汇（'family', 'love', 'justice'）而不是具体物件或时刻",
        ],
    }

    if school_name in school_avoids:
        patterns["avoid_patterns"].extend(school_avoids[school_name])

    return patterns


# ── Output formatting ─────────────────────────────────────────────────────────

def format_essay_analysis(data: dict) -> str:
    """Format essay analysis for human-readable output."""
    school   = data["school"]
    official = data["official_source"]
    patterns = data["pattern_analysis"]
    samples  = data["essay_samples"]
    notes    = data["notes"]

    lines = []
    lines.append(f"\n{'═'*60}")
    lines.append(f"  文书风格分析：{school}")
    lines.append(f"  样本量：{patterns['sample_count']} 个社区帖子")
    lines.append(f"{'═'*60}")

    # Official source
    if official and official.get("url"):
        lines.append(f"\n【官方文书来源】")
        lines.append(f"  URL   : {official['url']}")
        lines.append(f"  说明  : {official.get('notes', '')}")
    elif official and official.get("community_sources"):
        lines.append(f"\n【社区文书来源（该校无官方发布）】")
        lines.append(f"  说明  : {official.get('notes', '')}")
        for src_url in official["community_sources"]:
            lines.append(f"  • {src_url}")

    # School-specific tips
    tips = patterns.get("school_specific_tips", [])
    if tips:
        lines.append(f"\n【该校文书特点】")
        for tip in tips:
            lines.append(f"  • {tip}")

    # Topic distribution
    topic_dist = patterns.get("topic_distribution", {})
    if topic_dist:
        lines.append(f"\n【话题分布（社区样本）】")
        for topic, count in list(topic_dist.items())[:6]:
            bar = "▓" * count
            lines.append(f"  {bar} ({count}) {topic}")

    # Style signals
    style = patterns.get("style_signals", [])
    if style:
        lines.append(f"\n【写作风格信号】")
        for s in style:
            lines.append(f"  • {s}")

    # Avoid patterns
    avoids = patterns.get("avoid_patterns", [])
    if avoids:
        lines.append(f"\n【应该避免的模式】")
        for a in avoids:
            lines.append(f"  ✗ {a}")

    # Sample URLs (no full text)
    full_essay_posts = [s for s in samples if s.get("has_full_essay")]
    if full_essay_posts:
        lines.append(f"\n【社区分享文书帖（含原文）: {len(full_essay_posts)} 个】")
        for s in full_essay_posts[:8]:
            result_tag = f"[{s['result']}] " if s.get("result") else ""
            lines.append(f"  {result_tag}{s['url']}")
            lines.append(f"    → 话题：{s['topic_category']}")

    # Notes
    if notes:
        lines.append(f"\n【备注】")
        for note in notes:
            lines.append(f"  {note}")

    lines.append(f"\n{'═'*60}\n")
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Collect and analyze admission essay patterns for a school"
    )
    parser.add_argument("--school", "-s", required=True,
                        help="School name (e.g. 'University of Chicago')")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output raw JSON")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress progress output")
    args = parser.parse_args()

    data = collect_essays(
        school_name=args.school,
        verbose=not args.quiet,
    )

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_essay_analysis(data))


if __name__ == "__main__":
    main()
