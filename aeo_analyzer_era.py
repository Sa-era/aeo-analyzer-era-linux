#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║          AEO ANALYZER ERA  —  by Keyword Era              ║
║     SEO · AEO · Crawl · Rank Prediction Engine            ║
║          Designed for Kali Linux Terminal                  ║
╚═══════════════════════════════════════════════════════════╝
"""

import re
import json
import sys
import time
import os
import urllib.parse
from collections import Counter
from datetime import datetime

# ── Dependency check & graceful imports ─────────────────────────────────────

try:
    import requests
except ImportError:
    print("[!] requests not found. Run: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] beautifulsoup4 not found. Run: pip install beautifulsoup4 lxml")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.text import Text
    from rich.columns import Columns
    from rich.rule import Rule
    from rich.prompt import Prompt, FloatPrompt
    from rich import box
    from rich.align import Align
    from rich.live import Live
    from rich.layout import Layout
except ImportError:
    print("[!] rich not found. Run: pip install rich")
    sys.exit(1)

try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    HAS_SPACY = True
except Exception:
    HAS_SPACY = False

# ── Console ──────────────────────────────────────────────────────────────────
console = Console()

# ── Color Palette ────────────────────────────────────────────────────────────
C = {
    "banner":   "bold bright_cyan",
    "accent":   "bold cyan",
    "good":     "bold bright_green",
    "warn":     "bold yellow",
    "bad":      "bold bright_red",
    "info":     "bold bright_blue",
    "muted":    "dim white",
    "label":    "bold white",
    "heading":  "bold magenta",
    "score_hi": "bright_green",
    "score_md": "yellow",
    "score_lo": "bright_red",
    "border":   "cyan",
}


# ═══════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════

def print_banner():
    console.clear()
    banner = r"""
    ___   ______ ____      ___                __
   /   | / ____// __ \    /   |  ____  ____ _/ /_  ______  ___  _____
  / /| |/ __/  / / / /   / /| | / __ \/ __ `/ / / / /_  / / _ \/ ___/
 / ___ / /___ / /_/ /   / ___ |/ / / / /_/ / / /_/ / / /_/  __/ /
/_/  |_/_____/\____/   /_/  |_/_/ /_/\__,_/_/\__, / /___/\___/_/
                                             /____/
           ███████╗██████╗  █████╗
           ██╔════╝██╔══██╗██╔══██╗
           █████╗  ██████╔╝███████║
           ██╔══╝  ██╔══██╗██╔══██║
           ███████╗██║  ██║██║  ██║
           ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝  ANALYZER ERA
    """
    console.print(Panel(
        Align.center(Text(banner, style=C["banner"])),
        border_style=C["border"],
        padding=(0, 2),
    ))
    console.print(Align.center(
        Text("[ SEO · AEO · Crawl · Rank Prediction · EEAT · NLP ]",
             style=C["muted"])
    ))
    console.print(Align.center(
        Text(f"  Version 1.0  |  {datetime.now().strftime('%d %b %Y')}  |  Kali Linux Edition  ",
             style="dim cyan")
    ))
    console.print()


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def score_color(v: int) -> str:
    if v >= 75: return C["score_hi"]
    if v >= 45: return C["score_md"]
    return C["score_lo"]

def score_bar(v: int, width: int = 20) -> str:
    filled = int((v / 100) * width)
    empty  = width - filled
    color  = score_color(v)
    bar    = "█" * filled + "░" * empty
    return f"[{color}]{bar}[/{color}]"

def rank_style(pred: str):
    if "HIGH"   in pred: return C["good"],   "🟢"
    if "MEDIUM" in pred: return C["warn"],   "🟡"
    return C["bad"], "🔴"

def section(title: str):
    console.print()
    console.print(Rule(f"[{C['heading']}]  {title}  [{C['heading']}]",
                       style=C["border"]))
    console.print()


# ═══════════════════════════════════════════════════════════════
# LAYER 1 — CRAWL
# ═══════════════════════════════════════════════════════════════

def crawl_page(url: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    t0 = time.time()
    resp = requests.get(url, headers=headers, timeout=20)
    load_time = round(time.time() - t0, 2)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    base = urllib.parse.urlparse(url)

    title_tag  = soup.find("title")
    title      = title_tag.get_text(strip=True) if title_tag else ""

    meta_tag   = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    meta_desc  = meta_tag.get("content", "").strip() if meta_tag else ""

    headings = {}
    for lv in ["h1", "h2", "h3", "h4"]:
        headings[lv] = [h.get_text(strip=True) for h in soup.find_all(lv)]

    paragraphs = [
        p.get_text(strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 40
    ]

    faq_re = re.compile(r"(frequently asked|faq|common questions|people also ask)", re.I)
    faqs = []
    for sec in soup.find_all(["section", "div", "article"]):
        h = sec.find(re.compile(r"^h[1-6]$"))
        if h and faq_re.search(h.get_text()):
            for q in sec.find_all(["dt", "h3", "h4", "strong", "b"]):
                t = q.get_text(strip=True)
                if t.endswith("?") or len(t.split()) < 20:
                    faqs.append(t)

    internal_links, external_links = [], []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue
        full   = urllib.parse.urljoin(url, href)
        parsed = urllib.parse.urlparse(full)
        entry  = {"href": full, "text": a.get_text(strip=True)}
        if parsed.netloc == base.netloc:
            internal_links.append(entry)
        else:
            external_links.append(entry)

    images = []
    for img in soup.find_all("img"):
        images.append({
            "src":    img.get("src", ""),
            "alt":    img.get("alt", ""),
            "width":  img.get("width", ""),
            "height": img.get("height", ""),
        })

    schemas = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            schemas.append(json.loads(script.string or "{}"))
        except Exception:
            pass

    body      = soup.find("body")
    full_text = body.get_text(separator=" ", strip=True) if body else ""

    return {
        "url":             url,
        "status_code":     resp.status_code,
        "load_time_sec":   load_time,
        "title":           title,
        "meta_description": meta_desc,
        "headings":        headings,
        "paragraphs":      paragraphs,
        "faqs":            faqs,
        "internal_links":  internal_links,
        "external_links":  external_links,
        "images":          images,
        "schemas":         schemas,
        "full_text":       full_text,
        "word_count":      len(full_text.split()),
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 2 — SEO ANALYZER
# ═══════════════════════════════════════════════════════════════

def analyze_seo(data: dict, target_keyword: str = "") -> dict:
    title     = data["title"]
    meta      = data["meta_description"]
    full_text = data["full_text"]
    words     = full_text.lower().split()
    scores    = {}
    issues    = []
    recommendations = []

    tl = len(title)
    if 50 <= tl <= 60:     scores["title_length"] = 100
    elif 40 <= tl <= 70:   scores["title_length"] = 70;  issues.append(f"Title is {tl} chars (ideal 50–60)")
    else:                  scores["title_length"] = 30;  issues.append(f"Title length {tl} — too {'short' if tl < 40 else 'long'}")

    ml = len(meta)
    if 140 <= ml <= 160:   scores["meta_description"] = 100
    elif meta == "":       scores["meta_description"] = 0;  issues.append("Missing meta description")
    elif ml < 140:         scores["meta_description"] = 50; issues.append(f"Meta too short ({ml} chars, ideal 140–160)")
    else:                  scores["meta_description"] = 60; issues.append(f"Meta too long ({ml} chars)")

    density = 0.0
    if target_keyword:
        kw_lower  = target_keyword.lower()
        kw_count  = sum(1 for w in words if kw_lower in w)
        density   = round((kw_count / max(len(words), 1)) * 100, 2)
        if 1.0 <= density <= 2.5:  scores["keyword_density"] = 100
        elif density < 1.0:        scores["keyword_density"] = 40; issues.append(f"Keyword density {density}% low (target 1–2.5%)")
        else:                      scores["keyword_density"] = 50; issues.append(f"Keyword density {density}% — possible stuffing")
    else:
        scores["keyword_density"] = 50

    il_count = len(data["internal_links"])
    if il_count >= 5:     scores["internal_links"] = 100
    elif il_count >= 3:   scores["internal_links"] = 70
    elif il_count >= 1:   scores["internal_links"] = 40;  recommendations.append("Add more internal links (aim for 5+)")
    else:                 scores["internal_links"] = 0;   issues.append("No internal links found")

    imgs = data["images"]
    if imgs:
        with_alt = sum(1 for i in imgs if i["alt"].strip())
        ratio    = with_alt / len(imgs)
        scores["image_alt"] = round(ratio * 100)
        if ratio < 1.0:
            issues.append(f"{len(imgs)-with_alt} image(s) missing alt tags")
    else:
        scores["image_alt"] = 100

    h1 = data["headings"].get("h1", [])
    h2 = data["headings"].get("h2", [])
    if len(h1) == 1:     scores["heading_structure"] = 100 if h2 else 60
    elif len(h1) == 0:   scores["heading_structure"] = 0;  issues.append("No H1 tag found")
    else:                scores["heading_structure"] = 40; issues.append(f"Multiple H1 tags ({len(h1)}) — use only one")

    flesch = None
    if HAS_TEXTSTAT and full_text:
        flesch = textstat.flesch_reading_ease(full_text)
        if flesch >= 60:    scores["readability"] = 100
        elif flesch >= 40:  scores["readability"] = 70
        else:               scores["readability"] = 40; issues.append(f"Low readability ({flesch:.0f}) — simplify language")
    else:
        scores["readability"] = 60

    schema_types = [s.get("@type", "Unknown") for s in data["schemas"]]
    if data["schemas"]:
        sc = 40
        if any("FAQ"       in str(t) for t in schema_types): sc += 30
        if any("Article"   in str(t) or "BlogPosting" in str(t) for t in schema_types): sc += 30
        scores["schema"] = min(100, sc)
    else:
        scores["schema"] = 0
        recommendations.append("Add JSON-LD structured data (Article, FAQ, BreadcrumbList)")

    seo_score = round(sum(scores.values()) / len(scores))

    return {
        "scores":             scores,
        "seo_score":          seo_score,
        "flesch_score":       flesch,
        "keyword_density":    density,
        "internal_link_count": il_count,
        "image_count":        len(imgs),
        "issues":             issues,
        "recommendations":    recommendations,
        "schema_types":       schema_types,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 3 — AEO ANALYZER
# ═══════════════════════════════════════════════════════════════

def analyze_aeo(data: dict) -> dict:
    full_text    = data["full_text"]
    headings_all = []
    for lv in ["h1", "h2", "h3"]:
        headings_all.extend(data["headings"].get(lv, []))

    scores  = {}
    signals = {}
    issues  = []

    q_heads = [h for h in headings_all if "?" in h or
               re.match(r"^(what|how|why|when|where|who|which|can|is|are|does|do)\b", h, re.I)]
    q_ratio = len(q_heads) / max(len(headings_all), 1)
    scores["question_headings"]   = min(100, round(q_ratio * 200))
    signals["question_headings"]  = f"{len(q_heads)}/{len(headings_all)} are question-style"

    has_faq = len(data["faqs"]) > 0 or any(
        re.search(r"faq|frequently asked|people also ask", h, re.I) for h in headings_all)
    scores["faq_section"]  = 100 if has_faq else 0
    signals["faq_section"] = f"{'✓ Found' if has_faq else '✗ Not found'} — {len(data['faqs'])} items"
    if not has_faq:
        issues.append("No FAQ section — add Q&A blocks to capture People Also Ask")

    short_ans = [p for p in data["paragraphs"] if len(p.split()) <= 50]
    sa_ratio  = len(short_ans) / max(len(data["paragraphs"]), 1)
    scores["short_direct_answers"]  = min(100, round(sa_ratio * 150))
    signals["short_direct_answers"] = f"{len(short_ans)} short paragraphs (≤50 words)"

    top_entities = []
    if HAS_SPACY and full_text:
        doc          = nlp(full_text[:50000])
        ents         = Counter([(e.text, e.label_) for e in doc.ents])
        top_entities = ents.most_common(10)
        entity_count = len(set(e.text for e in doc.ents))
        scores["semantic_entities"]  = min(100, entity_count * 3)
        signals["semantic_entities"] = f"{entity_count} unique named entities found"
    else:
        scores["semantic_entities"]  = 50
        signals["semantic_entities"] = "spaCy unavailable — install for NLP analysis"

    common = Counter(
        w.lower() for w in full_text.split() if len(w) > 4 and w.isalpha()
    ).most_common(20)
    scores["nlp_relevance"]  = 80 if len(common) >= 10 else 40
    signals["nlp_relevance"] = "Top terms: " + ", ".join([w for w, _ in common[:5]])

    schema_types = [s.get("@type", "Unknown") for s in data["schemas"]]
    sc = 0
    if data["schemas"]:                                           sc += 40
    if any("FAQ"       in str(t) for t in schema_types):         sc += 30
    if any("Article"   in str(t) or "BlogPosting" in str(t) for t in schema_types): sc += 30
    scores["structured_data"]  = min(100, sc)
    signals["structured_data"] = f"Types: {schema_types if schema_types else 'None'}"

    citable = [p for p in data["paragraphs"] if 80 <= len(p.split()) <= 300]
    scores["citable_paragraphs"]  = min(100, len(citable) * 15)
    signals["citable_paragraphs"] = f"{len(citable)} paragraphs in 80–300 word range"

    eeat = {
        "author byline":      bool(re.search(r"by\s+[A-Z][a-z]+\s+[A-Z][a-z]+|written by|author:", full_text[:3000], re.I)),
        "publication date":   bool(re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}", full_text[:3000], re.I)),
        "citations/references": bool(re.search(r"(according to|research shows|study|cited|reference|source)", full_text, re.I)),
        "expertise language": bool(re.search(r"(expert|professional|certified|licensed|specialist|years of experience)", full_text, re.I)),
    }
    scores["eeat_signals"]  = sum(eeat.values()) * 25
    signals["eeat_signals"] = f"{sum(eeat.values())}/4 signals: {', '.join(k for k,v in eeat.items() if v)}"

    aeo_score = round(sum(scores.values()) / len(scores))

    return {
        "scores":       scores,
        "aeo_score":    aeo_score,
        "signals":      signals,
        "top_entities": top_entities,
        "eeat_detail":  eeat,
        "issues":       issues,
    }


# ═══════════════════════════════════════════════════════════════
# LAYER 5 — RANKING PROBABILITY ENGINE
# ═══════════════════════════════════════════════════════════════

def rank_probability(seo_score, aeo_score, word_count, internal_links,
                     backlink_score=50.0) -> dict:
    if   word_count >= 2000: depth = 100
    elif word_count >= 1000: depth = 70
    elif word_count >= 500:  depth = 40
    else:                    depth = 15
    depth = min(100, depth + min(20, internal_links * 2))

    rank_score = round(
        seo_score      * 0.35 +
        aeo_score      * 0.35 +
        backlink_score * 0.15 +
        depth          * 0.15, 1
    )

    if   rank_score >= 90: prediction, confidence = "🟢 HIGH — Strong ranking potential",    "High"
    elif rank_score >= 70: prediction, confidence = "🟡 MEDIUM — Moderate ranking potential", "Medium"
    else:                  prediction, confidence = "🔴 LOW — Significant improvements needed","Low"

    return {
        "rank_score":  rank_score,
        "prediction":  prediction,
        "confidence":  confidence,
        "depth_score": depth,
        "components":  {
            "SEO Score":           seo_score,
            "AEO Score":           aeo_score,
            "Backlink Score":      backlink_score,
            "Content Depth Score": depth,
        },
    }


# ═══════════════════════════════════════════════════════════════
# DISPLAY — RICH OUTPUT
# ═══════════════════════════════════════════════════════════════

def display_crawl(raw: dict):
    section("LAYER 1 — PAGE CRAWL")

    t = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    t.add_column("Field", style=C["label"],  width=22)
    t.add_column("Value", style="white",     width=70)

    title_disp = raw["title"][:80] + ("…" if len(raw["title"]) > 80 else "")
    meta_disp  = raw["meta_description"][:100] + ("…" if len(raw["meta_description"]) > 100 else "")

    t.add_row("URL",              f"[{C['accent']}]{raw['url']}[/{C['accent']}]")
    t.add_row("HTTP Status",      f"[{C['good']}]{raw['status_code']} OK[/{C['good']}]")
    t.add_row("Load Time",        f"{raw['load_time_sec']}s")
    t.add_row("Title",            title_disp)
    t.add_row("Title Length",     f"{len(raw['title'])} chars")
    t.add_row("Meta Description", meta_disp)
    t.add_row("Meta Length",      f"{len(raw['meta_description'])} chars")
    t.add_row("Word Count",       f"[{C['info']}]{raw['word_count']:,}[/{C['info']}]")
    t.add_row("H1 Tags",          str(raw["headings"].get("h1", [])))
    t.add_row("H2 Tags",          f"{len(raw['headings'].get('h2', []))} found")
    t.add_row("H3 Tags",          f"{len(raw['headings'].get('h3', []))} found")
    t.add_row("Internal Links",   f"{len(raw['internal_links'])}")
    t.add_row("External Links",   f"{len(raw['external_links'])}")
    t.add_row("Images",           f"{len(raw['images'])} total")
    t.add_row("FAQs Found",       f"{len(raw['faqs'])}")
    t.add_row("Paragraphs",       f"{len(raw['paragraphs'])}")

    schema_types = [s.get("@type", "?") for s in raw["schemas"]]
    t.add_row("Schema Types",     ", ".join(schema_types) if schema_types else "[dim]None[/dim]")

    console.print(Panel(t, border_style=C["border"], title="[bold cyan]Crawl Results[/bold cyan]"))

    if raw["faqs"]:
        console.print(f"\n  [{C['info']}]FAQ items detected:[/{C['info']}]")
        for faq in raw["faqs"][:5]:
            console.print(f"    [dim]•[/dim] {faq[:100]}")


def display_seo(seo: dict):
    section("LAYER 2 — SEO ANALYSIS")

    names = {
        "title_length":      "Title Length (50–60 chars)",
        "meta_description":  "Meta Description (140–160 chars)",
        "keyword_density":   "Keyword Density (1–2.5%)",
        "internal_links":    "Internal Links (5+ ideal)",
        "image_alt":         "Image Alt Tags (100% coverage)",
        "heading_structure": "Heading Structure (H1→H2)",
        "readability":       "Readability (Flesch score)",
        "schema":            "Schema / JSON-LD",
    }

    t = Table(box=box.SIMPLE_HEAD, border_style=C["border"], show_header=True)
    t.add_column("Signal",    style=C["label"],   width=32)
    t.add_column("Score",     justify="center",   width=8)
    t.add_column("Bar",       no_wrap=True,       width=24)
    t.add_column("Status",    justify="center",   width=10)

    for key, label in names.items():
        v      = seo["scores"].get(key, 0)
        col    = score_color(v)
        status = "✓ Good" if v >= 75 else ("△ Fair" if v >= 45 else "✗ Weak")
        sc     = "good"   if v >= 75 else ("warn"   if v >= 45 else "bad")
        t.add_row(
            label,
            f"[{col}]{v}[/{col}]",
            score_bar(v),
            f"[{C[sc]}]{status}[/{C[sc]}]",
        )

    console.print(Panel(t, border_style=C["border"], title=f"[bold cyan]SEO Score: {seo['seo_score']}/100[/bold cyan]"))

    # Stats row
    stats = [
        Panel(f"[{C['accent']}]{seo['seo_score']}[/{C['accent']}]\n[dim]SEO Score[/dim]",        border_style="cyan",  expand=True),
        Panel(f"[{C['info']}]{seo['internal_link_count']}[/{C['info']}]\n[dim]Internal Links[/dim]", border_style="blue",  expand=True),
        Panel(f"[{C['info']}]{seo['image_count']}[/{C['info']}]\n[dim]Images[/dim]",              border_style="blue",  expand=True),
        Panel(f"[white]{seo['keyword_density']:.1f}%[/white]\n[dim]Keyword Density[/dim]",        border_style="white", expand=True),
    ]
    if seo["flesch_score"] is not None:
        stats.append(Panel(f"[white]{seo['flesch_score']:.0f}[/white]\n[dim]Flesch Score[/dim]", border_style="white", expand=True))
    console.print(Columns(stats, equal=True, expand=True))

    if seo["issues"]:
        console.print(f"\n  [{C['bad']}]⚠ Issues:[/{C['bad']}]")
        for i in seo["issues"]:
            console.print(f"    [{C['warn']}]•[/{C['warn']}] {i}")
    if seo["recommendations"]:
        console.print(f"\n  [{C['good']}]💡 Recommendations:[/{C['good']}]")
        for r in seo["recommendations"]:
            console.print(f"    [{C['good']}]→[/{C['good']}] {r}")


def display_aeo(aeo: dict):
    section("LAYER 3 — AEO ANALYSIS (AI-Answer Friendliness)")

    names = {
        "question_headings":   "Question-Based Headings",
        "faq_section":         "FAQ Section Present",
        "short_direct_answers":"Short Direct Answers (≤50w)",
        "semantic_entities":   "Semantic Entities (NLP)",
        "nlp_relevance":       "NLP Topic Relevance",
        "structured_data":     "Structured Data (Schema)",
        "citable_paragraphs":  "Citable Paragraphs",
        "eeat_signals":        "E-E-A-T Signals",
    }
    importance = {
        "question_headings":   "HIGH",
        "faq_section":         "HIGH",
        "short_direct_answers":"HIGH",
        "semantic_entities":   "HIGH",
        "nlp_relevance":       "HIGH",
        "structured_data":     "HIGH",
        "citable_paragraphs":  "HIGH",
        "eeat_signals":        "HIGH",
    }

    t = Table(box=box.SIMPLE_HEAD, border_style=C["border"], show_header=True)
    t.add_column("AEO Signal",   style=C["label"],  width=30)
    t.add_column("Score",        justify="center",  width=8)
    t.add_column("Bar",          no_wrap=True,      width=22)
    t.add_column("Importance",   justify="center",  width=10)
    t.add_column("Detail",       style="dim white", width=35)

    for key, label in names.items():
        v      = aeo["scores"].get(key, 0)
        col    = score_color(v)
        imp    = importance.get(key, "MED")
        detail = str(aeo["signals"].get(key, ""))[:40]
        t.add_row(
            label,
            f"[{col}]{v}[/{col}]",
            score_bar(v),
            f"[{C['bad']}]{imp}[/{C['bad']}]",
            detail,
        )

    console.print(Panel(t, border_style=C["border"], title=f"[bold cyan]AEO Score: {aeo['aeo_score']}/100[/bold cyan]"))

    # EEAT detail
    eeat = aeo.get("eeat_detail", {})
    if eeat:
        console.print(f"\n  [{C['heading']}]E-E-A-T Signal Detail:[/{C['heading']}]")
        for k, v in eeat.items():
            icon  = f"[{C['good']}]✓[/{C['good']}]" if v else f"[{C['bad']}]✗[/{C['bad']}]"
            color = C["good"] if v else C["muted"]
            console.print(f"    {icon} [{color}]{k}[/{color}]")

    # Top entities
    if aeo.get("top_entities"):
        console.print(f"\n  [{C['info']}]Top Named Entities (NLP):[/{C['info']}]")
        for (ent, label), count in aeo["top_entities"][:8]:
            console.print(f"    [{C['accent']}]{ent}[/{C['accent']}] [{C['muted']}]({label} ×{count})[/{C['muted']}]")

    if aeo["issues"]:
        console.print(f"\n  [{C['bad']}]⚠ AEO Issues:[/{C['bad']}]")
        for i in aeo["issues"]:
            console.print(f"    [{C['warn']}]•[/{C['warn']}] {i}")


def display_rank(rank: dict, seo: dict, aeo: dict, raw: dict):
    section("LAYER 5 — RANKING PROBABILITY ENGINE")

    style, icon = rank_style(rank["prediction"])

    formula = (
        f"[{C['accent']}]rank_score[/{C['accent']}] = "
        f"SEO({seo['seo_score']})×0.35 + "
        f"AEO({aeo['aeo_score']})×0.35 + "
        f"Backlinks({rank['components']['Backlink Score']:.0f})×0.15 + "
        f"Depth({rank['components']['Content Depth Score']:.0f})×0.15"
    )
    console.print(f"  Formula: {formula}")
    console.print()

    # Score breakdown table
    t = Table(box=box.SIMPLE_HEAD, border_style=C["border"])
    t.add_column("Component",    style=C["label"],  width=24)
    t.add_column("Score",        justify="center",  width=8)
    t.add_column("Weight",       justify="center",  width=8)
    t.add_column("Contribution", justify="center",  width=14)
    t.add_column("Bar",          no_wrap=True,      width=20)

    comps   = rank["components"]
    weights = {"SEO Score": 0.35, "AEO Score": 0.35, "Backlink Score": 0.15, "Content Depth Score": 0.15}
    for name, val in comps.items():
        w    = weights.get(name, 0)
        cont = round(val * w, 1)
        col  = score_color(int(val))
        t.add_row(
            name,
            f"[{col}]{val:.0f}[/{col}]",
            f"{int(w*100)}%",
            f"[{col}]{cont}[/{col}]",
            score_bar(int(val)),
        )
    console.print(t)

    # Final verdict box
    verdict_text = (
        f"\n  {icon}  FINAL RANK SCORE:  [{style}]{rank['rank_score']}/100[/{style}]\n\n"
        f"     [{style}]{rank['prediction']}[/{style}]\n\n"
        f"     Confidence: [{C['label']}]{rank['confidence']}[/{C['label']}]\n"
        f"     Words: [{C['info']}]{raw['word_count']:,}[/{C['info']}]   "
        f"Internal Links: [{C['info']}]{seo['internal_link_count']}[/{C['info']}]   "
        f"Schemas: [{C['info']}]{len(raw['schemas'])}[/{C['info']}]\n"
    )
    console.print(Panel(verdict_text, border_style=style, padding=(1, 4),
                        title=f"[{style}]  Ranking Prediction  [/{style}]"))

    # Priority actions
    console.print(f"\n  [{C['heading']}]Priority Actions:[/{C['heading']}]")
    actions = []
    if seo["seo_score"] < 70:  actions.append(f"[{C['bad']}]→[/{C['bad']}] SEO score {seo['seo_score']}/100 — fix issues above")
    if aeo["aeo_score"] < 70:  actions.append(f"[{C['bad']}]→[/{C['bad']}] AEO score {aeo['aeo_score']}/100 — add FAQ + question headings")
    if not raw["schemas"]:     actions.append(f"[{C['warn']}]→[/{C['warn']}] Add JSON-LD schema markup")
    if raw["word_count"] < 1000: actions.append(f"[{C['warn']}]→[/{C['warn']}] Content depth low ({raw['word_count']} words) — aim for 1500+")
    if seo["internal_link_count"] < 3: actions.append(f"[{C['warn']}]→[/{C['warn']}] Only {seo['internal_link_count']} internal links — add more")
    if not actions:
        actions.append(f"[{C['good']}]✓ All major signals look strong![/{C['good']}]")
    for a in actions:
        console.print(f"    {a}")


# ═══════════════════════════════════════════════════════════════
# SAVE REPORT
# ═══════════════════════════════════════════════════════════════

def save_report(raw: dict, seo: dict, aeo: dict, rank: dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"aeo_era_report_{timestamp}.json"
    payload   = {"raw": {**raw}, "seo": seo, "aeo": aeo, "rank": rank}
    payload["raw"].pop("full_text", None)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return filename


# ═══════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════

def run_analysis(url: str, keyword: str = "", backlink_score: float = 50.0):
    console.print()

    steps = [
        ("Crawling page & extracting signals",  lambda: crawl_page(url)),
        ("Running SEO analysis",                None),
        ("Running AEO analysis",                None),
        ("Computing ranking probability",       None),
    ]

    raw = seo = aeo = rank = None

    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold cyan"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=30, style="cyan", complete_style="bright_green"),
        TextColumn("[dim]{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Starting...", total=4)

        progress.update(task, description="[bold cyan]Layer 1 — Crawling page...[/bold cyan]")
        raw = crawl_page(url)
        progress.advance(task)

        progress.update(task, description="[bold cyan]Layer 2 — SEO analysis...[/bold cyan]")
        seo = analyze_seo(raw, target_keyword=keyword)
        progress.advance(task)

        progress.update(task, description="[bold cyan]Layer 3 — AEO analysis...[/bold cyan]")
        aeo = analyze_aeo(raw)
        progress.advance(task)

        progress.update(task, description="[bold cyan]Layer 5 — Ranking probability...[/bold cyan]")
        rank = rank_probability(
            seo["seo_score"], aeo["aeo_score"],
            raw["word_count"], seo["internal_link_count"],
            backlink_score
        )
        progress.advance(task)

    console.print(f"  [{C['good']}]✓ Analysis complete![/{C['good']}]  "
                  f"Crawled in [{C['accent']}]{raw['load_time_sec']}s[/{C['accent']}]  |  "
                  f"[{C['info']}]{raw['word_count']:,} words[/{C['info']}]")

    display_crawl(raw)
    display_seo(seo)
    display_aeo(aeo)
    display_rank(rank, seo, aeo, raw)

    # ── Save ───────────────────────────────────────
    section("REPORT SAVED")
    fname = save_report(raw, seo, aeo, rank)
    console.print(f"  [{C['good']}]💾 Report saved:[/{C['good']}] [{C['accent']}]{fname}[/{C['accent']}]")
    console.print()

    return raw, seo, aeo, rank


# ═══════════════════════════════════════════════════════════════
# INTERACTIVE MENU
# ═══════════════════════════════════════════════════════════════

def main_menu():
    print_banner()

    # Capability status
    caps = [
        ("requests",       True),
        ("beautifulsoup4", True),
        ("rich",           True),
        ("textstat",       HAS_TEXTSTAT),
        ("spaCy NLP",      HAS_SPACY),
    ]
    status_line = "  "
    for name, ok in caps:
        color = C["good"] if ok else C["bad"]
        icon  = "●" if ok else "○"
        status_line += f"[{color}]{icon} {name}[/{color}]   "
    console.print(status_line)
    console.print()

    if not HAS_TEXTSTAT:
        console.print(f"  [{C['warn']}]⚠ textstat not found — readability scoring limited[/{C['warn']}]")
    if not HAS_SPACY:
        console.print(f"  [{C['warn']}]⚠ spaCy not found — NLP entity analysis disabled[/{C['warn']}]")
    console.print()

    while True:
        console.print(Rule(style=C["border"]))
        console.print(f"\n  [{C['heading']}]MAIN MENU[/{C['heading']}]\n")
        console.print(f"  [{C['accent']}][1][/{C['accent']}] Analyze a URL")
        console.print(f"  [{C['accent']}][2][/{C['accent']}] Batch analyze (multiple URLs from file)")
        console.print(f"  [{C['accent']}][3][/{C['accent']}] About / Help")
        console.print(f"  [{C['accent']}][q][/{C['accent']}] Quit\n")

        choice = Prompt.ask(f"  [{C['label']}]Enter choice[/{C['label']}]",
                            choices=["1","2","3","q"], default="1")

        if choice == "1":
            console.print()
            url = Prompt.ask(f"  [{C['label']}]Enter URL[/{C['label']}]")
            if not url.startswith("http"):
                url = "https://" + url
            keyword       = Prompt.ask(f"  [{C['label']}]Target keyword[/{C['label']}] (press Enter to skip)", default="")
            backlink_score = FloatPrompt.ask(f"  [{C['label']}]Backlink score 0–100[/{C['label']}] (default 50)", default=50.0)
            try:
                run_analysis(url, keyword=keyword, backlink_score=backlink_score)
            except requests.exceptions.ConnectionError:
                console.print(f"\n  [{C['bad']}]✗ Connection error — check the URL and your network[/{C['bad']}]")
            except requests.exceptions.HTTPError as e:
                console.print(f"\n  [{C['bad']}]✗ HTTP error: {e}[/{C['bad']}]")
            except Exception as e:
                console.print(f"\n  [{C['bad']}]✗ Error: {e}[/{C['bad']}]")

            input("\n  Press Enter to return to menu...")
            print_banner()

        elif choice == "2":
            filepath = Prompt.ask(f"  [{C['label']}]Path to URL list file[/{C['label']}] (one URL per line)")
            keyword  = Prompt.ask(f"  [{C['label']}]Target keyword (same for all)[/{C['label']}]", default="")
            try:
                with open(filepath.strip()) as f:
                    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                console.print(f"\n  [{C['info']}]Found {len(urls)} URLs[/{C['info']}]\n")
                for i, u in enumerate(urls, 1):
                    console.print(Rule(f"[cyan]URL {i}/{len(urls)}: {u[:60]}[/cyan]", style="cyan"))
                    try:
                        run_analysis(u, keyword=keyword)
                    except Exception as e:
                        console.print(f"  [{C['bad']}]✗ Failed: {e}[/{C['bad']}]")
            except FileNotFoundError:
                console.print(f"  [{C['bad']}]✗ File not found: {filepath}[/{C['bad']}]")
            input("\n  Press Enter to return to menu...")
            print_banner()

        elif choice == "3":
            section("ABOUT AEO ANALYZER ERA")
            console.print("""
  [bold white]AEO Analyzer Era[/bold white] — [dim]by Keyword Era[/dim]

  A 5-layer SEO + AEO intelligence tool built for Kali Linux.

  [bold cyan]Layers:[/bold cyan]
    [cyan]Layer 1[/cyan]  Crawl — fetches live page, extracts all signals
    [cyan]Layer 2[/cyan]  SEO   — title, meta, density, links, alt tags, schema
    [cyan]Layer 3[/cyan]  AEO   — AI-answer friendliness, FAQ, EEAT, NLP, entities
    [cyan]Layer 5[/cyan]  Rank  — weighted score → HIGH / MEDIUM / LOW prediction

  [bold cyan]Formula:[/bold cyan]
    rank_score = SEO×0.35 + AEO×0.35 + Backlinks×0.15 + Depth×0.15

  [bold cyan]Dependencies:[/bold cyan]
    requests, beautifulsoup4, lxml, rich, textstat, spacy

  [bold cyan]Output:[/bold cyan]
    JSON report saved to current directory after each analysis.
            """)
            input("  Press Enter to go back...")
            print_banner()

        elif choice == "q":
            console.print(f"\n  [{C['accent']}]AEO Analyzer Era — by Keyword Era. Goodbye.[/{C['accent']}]\n")
            sys.exit(0)


# ═══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] not in ["-h", "--help", "menu"]:
        # Direct CLI mode: python aeo_analyzer_era.py <url> [keyword] [backlinks]
        print_banner()
        url     = sys.argv[1]
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        bl      = float(sys.argv[3]) if len(sys.argv) > 3 else 50.0
        run_analysis(url, keyword=keyword, backlink_score=bl)
    elif len(sys.argv) >= 2 and sys.argv[1] in ["-h", "--help"]:
        print(__doc__)
        print("Usage:")
        print("  python aeo_analyzer_era.py                         # interactive menu")
        print("  python aeo_analyzer_era.py <url> [keyword] [bl]    # direct CLI")
        print("  python aeo_analyzer_era.py menu                    # force menu mode")
    else:
        main_menu()
